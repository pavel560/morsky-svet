#!/usr/bin/env python3
"""Mořský svět — pre-record every spoken line (voice/<lang>/<id>.mp3 + voice/index.json).

    node dev/export_phrases.mjs        # → voice/phrases.json (all lines, stable ids)
    python3 make_voice.py              # record only new/changed lines (and lines whose recording is not licensed)
    python3 make_voice.py --force      # re-record everything
    python3 make_voice.py --lang cs
    python3 make_voice.py --audit      # licence check only: every line recorded by a paid, licensed service? (exit 1 if not)

Voices per language come from voice/config.json (required). Only licensed services are used for recordings:
  {"cs": {"provider": "elevenlabs", "voice_name": "…", "model_id": "…", "language_code": "cs", "voice_settings": {…},
          "licence": {"plan": "ElevenLabs Starter", "since": "2026-10-12T15:15:00Z"}},
   "en": {"provider": "azure", "voice": "en-GB-MaisieNeural", "rate": "-8%", "licence": {"plan": "Azure AI Speech"}}}
  elevenlabs  REST API, key in env ELEVENLABS_API_KEY; the voice must be in the account's "My voices"; paid plan only
  azure       Azure AI Speech REST API, key in env AZURE_SPEECH_KEY, region in env AZURE_SPEECH_REGION (e.g. westeurope)
The free Microsoft Edge "Read Aloud" voices (edge-tts) are not licensed for commercial use and are never used here;
lines recorded with them earlier are reported by --audit and re-recorded on the next run.

voice/index.json keeps per phrase the text, a hash of (provider, voice, model/settings, text), the service, the licence
and the recording time (UTC): a changed line or a changed voice re-records. A language is switched ATOMICALLY: all
needed lines are recorded into a staging folder first and only moved in when every one succeeded, so the game never
mixes two voices. Before recording with ElevenLabs, the characters are checked against the remaining quota (nothing is
spent if it would not fit). Python 3.9+.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
import shutil
import time
import urllib.error
import urllib.request
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
LICENSED = ("elevenlabs", "azure")      # services whose recordings may be used commercially (paid plan / Azure terms)
RATE = "-8%"
EL_API = "https://api.elevenlabs.io/v1/"
EL_FORMAT = "mp3_44100_64"
AZ_FORMAT = "audio-24khz-48kbitrate-mono-mp3"
ID_RE = re.compile(r"^[A-Za-z0-9.-]+$")


class TTSError(Exception):
    pass


def voice_key(cfg: dict) -> str:
    """What identifies a voice: changing any part re-records every line of that language."""
    provider = cfg.get("provider")
    if provider == "azure":
        parts = {k: cfg.get(k) for k in ("provider", "voice", "rate", "style")}
        return "azure|" + json.dumps(parts, sort_keys=True, ensure_ascii=False)
    if provider == "elevenlabs":
        parts = {k: cfg.get(k) for k in ("provider", "voice_name", "voice_id", "model_id", "language_code", "voice_settings")}
        return "elevenlabs|" + json.dumps(parts, sort_keys=True, ensure_ascii=False)
    return f"{provider}|{cfg.get('voice')}"     # unsupported (e.g. the old edge-tts): never matches a licensed recording


def line_hash(text: str, cfg: dict) -> str:
    return hashlib.sha1(f"{voice_key(cfg)}|{text}".encode("utf-8")).hexdigest()


def load_config(vdir: str) -> dict:
    user = load_json(os.path.join(vdir, "config.json"), {}) or {}
    return {lang: dict(c) for lang, c in user.items() if isinstance(c, dict)}


def utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


class QuotaError(TTSError):
    pass


class PermissionMissing(TTSError):
    """401 missing_permissions — the key works, it just may not call this endpoint."""


class FatalTTSError(TTSError):
    """Not worth retrying (bad key, plan, missing voice)."""


class RateLimited(TTSError):
    def __init__(self, wait: float | None, service: str = "ElevenLabs"):
        super().__init__(f"{service}: příliš mnoho požadavků (429)")
        self.wait = wait


class LanguageCodeRejected(TTSError):
    pass


def _retry_after(err) -> float | None:
    try:
        return float(err.headers.get("Retry-After"))
    except (TypeError, ValueError, AttributeError):
        return None


class ElevenLabsAPI:
    """The only place that talks to ElevenLabs. Tests replace it with a fake with the same three methods."""

    def __init__(self, key: str | None = None, timeout: float = 60.0):
        self.key = key or os.environ.get("ELEVENLABS_API_KEY", "")
        self.timeout = timeout

    def _call(self, path: str, body=None) -> bytes:
        if not self.key:
            raise FatalTTSError("chybí ELEVENLABS_API_KEY")
        req = urllib.request.Request(EL_API + path, data=json.dumps(body).encode("utf-8") if body is not None else None,
                                     headers={"xi-api-key": self.key, "Content-Type": "application/json", "Accept": "*/*"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300] if hasattr(e, "read") else ""
            if e.code == 401 and "missing_permissions" in detail:
                raise PermissionMissing(f"ElevenLabs: klíči chybí oprávnění ({detail})") from e
            if e.code == 401:
                raise FatalTTSError(f"ElevenLabs: neplatný API klíč (401): {detail}") from e
            if e.code == 402 or "quota" in detail.lower() or "paid" in detail.lower():
                raise QuotaError(f"ElevenLabs: došly kredity nebo je potřeba placený plán ({e.code}): {detail}") from e
            if e.code == 429:
                raise RateLimited(_retry_after(e)) from e
            if e.code == 400 and "language" in detail.lower():
                raise LanguageCodeRejected(detail) from e
            raise TTSError(f"ElevenLabs HTTP {e.code}: {detail}") from e
        except (OSError, urllib.error.URLError) as e:
            raise TTSError(f"ElevenLabs: síť: {e}") from e

    def voices(self) -> list:
        return json.loads(self._call("voices").decode("utf-8")).get("voices", [])

    def subscription(self) -> dict:
        return json.loads(self._call("user/subscription").decode("utf-8"))

    def tts(self, voice_id: str, body: dict) -> bytes:
        return self._call(f"text-to-speech/{voice_id}?output_format={EL_FORMAT}", body)


class AzureSpeechAPI:
    """The only place that talks to Azure AI Speech. Tests replace it with a fake with the same method."""

    def __init__(self, key: str | None = None, region: str | None = None, timeout: float = 60.0):
        self.key = key or os.environ.get("AZURE_SPEECH_KEY", "")
        self.region = (region or os.environ.get("AZURE_SPEECH_REGION", "")).strip()
        self.timeout = timeout

    def check(self) -> None:
        missing = [n for n, v in (("AZURE_SPEECH_KEY", self.key), ("AZURE_SPEECH_REGION", self.region)) if not v]
        if missing:
            raise FatalTTSError("chybí " + " a ".join(missing))

    def tts(self, ssml: str) -> bytes:
        self.check()
        req = urllib.request.Request(f"https://{self.region}.tts.speech.microsoft.com/cognitiveservices/v1",
                                     data=ssml.encode("utf-8"),
                                     headers={"Ocp-Apim-Subscription-Key": self.key, "Content-Type": "application/ssml+xml",
                                              "X-Microsoft-OutputFormat": AZ_FORMAT, "User-Agent": "game-voice-recorder"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300] if hasattr(e, "read") else ""
            if e.code in (401, 403):
                raise FatalTTSError(f"Azure: neplatný klíč nebo oblast ({e.code}): {detail}") from e
            if e.code == 429:
                raise RateLimited(_retry_after(e), "Azure") from e
            raise TTSError(f"Azure HTTP {e.code}: {detail}") from e
        except (OSError, urllib.error.URLError) as e:
            raise TTSError(f"Azure: síť: {e}") from e


class ElevenLabsProvider:
    name = "elevenlabs"

    def __init__(self, cfg: dict, api):
        self.cfg = cfg; self.api = api
        self.label = f"ElevenLabs „{cfg.get('voice_name') or cfg.get('voice_id')}“ ({cfg.get('model_id')})"
        self.voice_id = cfg.get("voice_id")
        self.send_language = bool(cfg.get("language_code"))

    def prepare(self, lang: str, chars: int, out) -> None:
        """Quota check (raises if the lines would not fit), then find the voice. Spends nothing."""
        try:
            sub = self.api.subscription()
        except PermissionMissing:
            sub = None
            print(f"{lang}: stav kreditů nelze ověřit (klíč nemá oprávnění user_read) — pokračuji; "
                  f"když kredity dojdou, přepnutí se zruší a stávající nahrávky zůstanou.", file=out, flush=True)
        if sub:
            remaining = int(sub.get("character_limit", 0)) - int(sub.get("character_count", 0))
            if chars > remaining:
                raise QuotaError(f"potřeba {chars} znaků, ale v ElevenLabs zbývá jen {max(0, remaining)} "
                                 f"(limit {sub.get('character_limit')}, použito {sub.get('character_count')})")
            print(f"{lang}: kredity v pořádku (zbývá {remaining} znaků, po nahrání {remaining - chars}).", file=out, flush=True)
        self.resolve()

    def resolve(self) -> str:
        if self.voice_id:
            return self.voice_id
        want = (self.cfg.get("voice_name") or "").strip().lower()
        for v in self.api.voices():
            if (v.get("name") or "").strip().lower() == want:
                self.voice_id = v.get("voice_id")
                return self.voice_id
        raise FatalTTSError(f"hlas „{self.cfg.get('voice_name')}“ není v „My voices“ účtu ElevenLabs (přidejte ho z Voice Library)")

    def synth(self, text: str, path: str) -> None:
        body = {"text": text, "model_id": self.cfg.get("model_id", "eleven_multilingual_v2")}
        if self.send_language:
            body["language_code"] = self.cfg["language_code"]
        if self.cfg.get("voice_settings"):
            body["voice_settings"] = self.cfg["voice_settings"]
        try:
            audio = self.api.tts(self.resolve(), body)
        except LanguageCodeRejected:
            self.send_language = False          # some models do not take language_code: retry without it, once per run
            body.pop("language_code", None)
            audio = self.api.tts(self.resolve(), body)
        with open(path, "wb") as f:
            f.write(audio)

    def entry(self) -> dict:
        return {"voice": self.cfg.get("voice_name") or self.cfg.get("voice_id"), "model": self.cfg.get("model_id")}


class AzureProvider:
    name = "azure"

    def __init__(self, cfg: dict, api):
        self.cfg = cfg; self.api = api
        self.label = f"Azure „{cfg.get('voice')}“"

    def prepare(self, lang: str, chars: int, out) -> None:
        if not self.cfg.get("voice"):
            raise FatalTTSError("v voice/config.json chybí „voice“ (např. en-GB-MaisieNeural)")
        if hasattr(self.api, "check"):
            self.api.check()

    def ssml(self, text: str) -> str:
        voice = self.cfg["voice"]
        xml_lang = "-".join(voice.split("-")[:2])                     # en-GB-MaisieNeural → en-GB
        inner = f"<prosody rate=\"{escape(self.cfg.get('rate', RATE))}\">{escape(text)}</prosody>"
        if self.cfg.get("style"):
            inner = f"<mstts:express-as style=\"{escape(self.cfg['style'])}\">{inner}</mstts:express-as>"
        return (f"<speak version=\"1.0\" xmlns=\"http://www.w3.org/2001/10/synthesis\" "
                f"xmlns:mstts=\"https://www.w3.org/2001/mstts\" xml:lang=\"{xml_lang}\">"
                f"<voice name=\"{escape(voice)}\">{inner}</voice></speak>")

    def synth(self, text: str, path: str) -> None:
        audio = self.api.tts(self.ssml(text))
        with open(path, "wb") as f:
            f.write(audio)

    def entry(self) -> dict:
        return {"voice": self.cfg.get("voice")}


def make_provider(cfg: dict, eleven=None, azure=None):
    provider = cfg.get("provider")
    if provider == "elevenlabs":
        return ElevenLabsProvider(cfg, eleven or ElevenLabsAPI())
    if provider == "azure":
        return AzureProvider(cfg, azure or AzureSpeechAPI())
    raise FatalTTSError(f"služba „{provider}“ není licencovaná pro komerční nahrávky (povolené: {', '.join(LICENSED)})")


def load_json(path: str, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def write_json_atomic(path: str, obj) -> None:
    tmp = path + ".part"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)


def looks_like_mp3(path: str) -> bool:
    try:
        with open(path, "rb") as f:
            head = f.read(3)
    except OSError:
        return False
    return head[:3] == b"ID3" or (len(head) >= 2 and head[0] == 0xFF and (head[1] & 0xE0) == 0xE0)


# A real recording is ≈ 6 kB per second of speech (48 kbit/s). The service sometimes returns a ~2 kB stub
# (a fragment or silence) without an error; such files are treated as failures, never as done.
MIN_BYTES = 4000              # shortest real line („Srnka!“) is ≈ 9 kB
MIN_BYTES_PER_CHAR = 200      # long lines: a truncated recording is far below this
MAX_RATE_LIMIT_WAITS = 10     # 429 answers are waited out; they do not use up the normal retries


def min_bytes(text: str) -> int:
    return max(MIN_BYTES, MIN_BYTES_PER_CHAR * len(text.strip()))


def audio_problem(path: str, text: str):
    """None if the file looks like a complete recording of `text`, else a short reason."""
    try:
        size = os.path.getsize(path)
    except OSError:
        return "soubor chybí"
    if not looks_like_mp3(path):
        return "není to MP3"
    if size < min_bytes(text):
        return f"podezřele krátká nahrávka ({size} B, čekáno ≥ {min_bytes(text)} B)"
    return None


def record(provider, text: str, dest: str, retries: int, delay: float) -> int:
    tmp = dest + ".part.mp3"
    wait = delay
    last = None
    attempt = limited = 0
    while attempt < retries:
        try:
            provider.synth(text, tmp)
            problem = audio_problem(tmp, text)
            if problem:
                raise TTSError(problem)
            os.replace(tmp, dest)
            return os.path.getsize(dest)
        except (FatalTTSError, QuotaError):
            if os.path.exists(tmp):
                os.remove(tmp)
            raise                                     # bad key / plan / quota / missing voice: retrying cannot help
        except RateLimited as e:                      # the service asks us to slow down: wait, do not count an attempt
            last = e
            limited += 1
            if limited > MAX_RATE_LIMIT_WAITS:
                break
            time.sleep(min(60.0, e.wait) if e.wait else min(60.0, delay * 2 ** limited))
        except Exception as e:  # network, service throttling, empty audio — all transient here
            last = e
            attempt += 1
            if os.path.exists(tmp):
                os.remove(tmp)
            if attempt < retries:
                time.sleep(wait)
                wait *= 2
    raise TTSError(f"{last.__class__.__name__}: {last}")


def _needed(lang, phrases, index, cfg, vdir, force):
    """[(pid, text, hash, why)] lines of a language that need recording ('new', 'changed', 'suspect')."""
    out = []
    for pid, text in sorted(phrases.items()):
        if not ID_RE.match(pid) or not isinstance(text, str) or not text.strip():
            continue
        h = line_hash(text, cfg)
        entry = index.get(lang, {}).get(pid)
        dest = os.path.join(vdir, lang, f"{pid}.mp3")
        if force or not entry or entry.get("sha1") != h or not os.path.exists(dest):
            out.append((pid, text, h, "new" if not entry else "changed"))
        else:
            problem = audio_problem(dest, text)          # re-validate committed files: heals stubs
            if problem:
                out.append((pid, text, h, f"suspect: {problem}"))
    return out


def run(root: str = HERE, force: bool = False, langs=None, retries: int = 3, delay: float = 2.0,
        pause: float = 0.2, out=sys.stdout, eleven=None, azure=None) -> int:
    vdir = os.path.join(root, "voice")
    phrases = load_json(os.path.join(vdir, "phrases.json"))
    if not isinstance(phrases, dict) or not phrases:
        print("Chybí voice/phrases.json — nejdřív spusťte: node dev/export_phrases.mjs", file=out)
        return 2
    config = load_config(vdir)
    index_path = os.path.join(vdir, "index.json")
    index = load_json(index_path, {}) or {}
    langs = [lang for lang in (langs or phrases.keys()) if lang in phrases]
    totals = {"made": 0, "skipped": 0, "failed": 0, "suspect": 0, "healed": 0, "removed": 0}
    bad = [(lang, pid) for lang in langs for pid, text in phrases[lang].items()
           if not ID_RE.match(pid) or not isinstance(text, str) or not text.strip()]
    for lang, pid in bad:
        print(f"{lang} {pid}: CHYBA: neplatné id nebo prázdný text", file=out, flush=True)
    totals["failed"] += len(bad)
    for lang in langs:
        cfg = config.get(lang)
        if not cfg:
            print(f"{lang}: CHYBA: voice/config.json nemá hlas pro tento jazyk — nic se nenahrává.", file=out, flush=True)
            totals["failed"] += len(phrases[lang])
            continue
        need = _needed(lang, phrases[lang], index, cfg, vdir, force)
        totals["skipped"] += sum(1 for pid, text in phrases[lang].items() if ID_RE.match(pid) and isinstance(text, str) and text.strip()) - len(need)
        _record_language(lang, cfg, need, index, index_path, vdir, eleven, azure, retries, delay, pause, out, totals)
        totals["removed"] += _prune(lang, phrases.get(lang, {}), index, vdir)
    write_json_atomic(index_path, index)
    t = totals
    print(f"\nNahráno {t['made']}, beze změny {t['skipped']}, odstraněno {t['removed']}, podezřelé {t['suspect']} (opraveno {t['healed']}), chyb {t['failed']}.",
          file=out, flush=True)
    if t["failed"]:
        print("Věty s chybou zůstávají ve starší nahrávce nebo je hra řekne hlasem prohlížeče. Skript lze spustit znovu, dodělá jen chybějící.", file=out)
    return 1 if t["failed"] else 0


def _prune(lang, phrases, index, vdir) -> int:
    removed = 0
    for pid in list(index.get(lang, {})):
        if pid not in phrases:
            f = os.path.join(vdir, index[lang][pid].get("file", ""))
            if os.path.isfile(f) and os.path.dirname(os.path.abspath(f)).startswith(os.path.abspath(vdir)):
                os.remove(f)
            del index[lang][pid]
            removed += 1
    return removed


def _record_language(lang, cfg, need, index, index_path, vdir, eleven, azure, retries, delay, pause, out, t):
    """Preflight, then record everything into a staging folder; switch only if ALL lines succeeded."""
    if not need:
        print(f"{lang}: {cfg.get('provider')} — vše nahráno, beze změny.", file=out, flush=True)
        return
    chars = sum(len(text) for _, text, _, _ in need)
    try:
        provider = make_provider(cfg, eleven, azure)
        print(f"{lang}: {provider.label} — potřeba {len(need)} vět, {chars} znaků.", file=out, flush=True)
        provider.prepare(lang, chars, out)
    except TTSError as e:
        t["failed"] += len(need)
        print(f"{lang}: NIC SE NENAHRÁVÁ — {e}. Stávající nahrávky zůstávají.", file=out, flush=True)
        return
    licence = (cfg.get("licence") or {}).get("plan")
    stage = os.path.join(vdir, f".staging-{lang}")
    shutil.rmtree(stage, ignore_errors=True)
    os.makedirs(stage)
    done = []
    try:
        for i, (pid, text, h, why) in enumerate(need, 1):
            print(f"[{i}/{len(need)}] {lang} {pid} … nahrávám … ", end="", file=out, flush=True)
            try:
                size = record(provider, text, os.path.join(stage, f"{pid}.mp3"), retries, delay)
            except TTSError as e:
                t["failed"] += len(need) - len(done)
                print(f"CHYBA: {e}", file=out, flush=True)
                print(f"{lang}: PŘEPNUTÍ HLASU ZRUŠENO — {len(done)} z {len(need)} vět nahráno, ale nahrávky se nepoužijí, "
                      "aby hra nemíchala dva hlasy. Stávající nahrávky zůstávají beze změny.", file=out, flush=True)
                return
            done.append((pid, text, h, why, size, utc_now()))
            print(f"hotovo {round(size / 1024)} kB", file=out, flush=True)
            if pause:
                time.sleep(pause)
        # all succeeded: move in and update the index in one go
        os.makedirs(os.path.join(vdir, lang), exist_ok=True)
        for pid, text, h, why, size, when in done:
            os.replace(os.path.join(stage, f"{pid}.mp3"), os.path.join(vdir, lang, f"{pid}.mp3"))
            entry = {"text": text, "sha1": h, "file": f"{lang}/{pid}.mp3", "bytes": size, "provider": provider.name,
                     "recorded": when, **provider.entry()}
            if licence:
                entry["licence"] = licence
            index.setdefault(lang, {})[pid] = entry
            t["made"] += 1
            if why.startswith("suspect"):
                t["suspect"] += 1
                t["healed"] += 1
        write_json_atomic(index_path, index)
        print(f"{lang}: hlas přepnut — {len(done)} vět nahráno ({provider.label}).", file=out, flush=True)
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def audit(root: str = HERE, out=sys.stdout) -> int:
    """Licence check of the committed recordings: every line recorded with the configured voice by a licensed service,
    inside the licence window. Prints what would have to be re-recorded (lines, characters). Exit 1 if anything is off."""
    vdir = os.path.join(root, "voice")
    phrases = load_json(os.path.join(vdir, "phrases.json"))
    if not isinstance(phrases, dict) or not phrases:
        print("Chybí voice/phrases.json — nejdřív spusťte: node dev/export_phrases.mjs", file=out)
        return 2
    config = load_config(vdir)
    index = load_json(os.path.join(vdir, "index.json"), {}) or {}
    problems = 0
    for lang in sorted(phrases):
        cfg = config.get(lang) or {}
        lic = cfg.get("licence") or {}
        since = lic.get("since")
        why = {}
        for pid, text in sorted(phrases[lang].items()):
            e = index.get(lang, {}).get(pid)
            if not e or not os.path.isfile(os.path.join(vdir, e.get("file", ""))):
                why[pid] = "chybí nahrávka"
            elif e.get("provider") not in LICENSED:
                why[pid] = f"nahráno službou bez komerční licence ({'edge-tts' if e.get('provider') in (None, 'edge') else e['provider']})"
            elif not cfg or e.get("sha1") != line_hash(text, cfg):
                why[pid] = "nahráno jiným hlasem, než určuje voice/config.json"
            elif not e.get("recorded"):
                why[pid] = "chybí čas nahrání"
            elif since and e["recorded"] < since:
                why[pid] = f"nahráno před začátkem licence ({e['recorded']} < {since})"
        n = len(phrases[lang])
        ok = n - len(why)
        plan = lic.get("plan") or cfg.get("provider") or "?"
        if not why:
            print(f"{lang}: v pořádku — {ok}/{n} vět, {plan}" + (f" (licence od {since})" if since else ""), file=out)
            continue
        problems += len(why)
        chars = sum(len(phrases[lang][p]) for p in why)
        print(f"{lang}: K PŘENAHRÁNÍ {len(why)}/{n} vět, {chars} znaků (licencováno {ok}); hlas podle config: {plan}", file=out)
        for reason in sorted(set(why.values())):
            k = sum(1 for r in why.values() if r == reason)
            print(f"    {k}× {reason}", file=out)
    return 1 if problems else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Record Mořský svět voice lines (voice/config.json: ElevenLabs or Azure AI Speech)")
    ap.add_argument("--force", action="store_true", help="re-record everything")
    ap.add_argument("--lang", help="only one language (e.g. cs)")
    ap.add_argument("--audit", action="store_true", help="only check that every recording is licensed (exit 1 if not)")
    args = ap.parse_args(argv)
    if args.audit:
        return audit(HERE)
    return run(HERE, force=args.force, langs=[args.lang] if args.lang else None)


if __name__ == "__main__":
    sys.exit(main())
