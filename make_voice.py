#!/usr/bin/env python3
"""Mořský svět — pre-record every spoken line (voice/<lang>/<id>.mp3 + voice/index.json).

    node dev/export_phrases.mjs        # → voice/phrases.json (all lines, stable ids)
    python3 make_voice.py              # record only new/changed lines
    python3 make_voice.py --force      # re-record everything
    python3 make_voice.py --lang cs

Voices per language come from voice/config.json (optional; without it: Microsoft edge-tts, Vlasta / Maisie):
  {"cs": {"provider": "elevenlabs", "voice_name": "…", "model_id": "…", "language_code": "cs", "voice_settings": {…}},
   "en": {"provider": "edge", "voice": "en-GB-MaisieNeural", "rate": "-8%"}}
  edge        pip install edge-tts (free, no key)
  elevenlabs  REST API, key in env ELEVENLABS_API_KEY; the voice must be in the account's "My voices"

voice/index.json keeps the text + a hash of (provider, voice, model/settings, text) per phrase: a changed line or a
changed voice re-records. An ElevenLabs language is switched ATOMICALLY: all needed lines are recorded into a
staging folder first and only moved in when every one succeeded, so the game never mixes two voices. Before
recording, the characters are checked against the remaining ElevenLabs quota (nothing is spent if it would not fit).
Python 3.9+.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
import sys
import shutil
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
VOICES = {"cs": "cs-CZ-VlastaNeural", "en": "en-GB-MaisieNeural"}
RATE = "-8%"
DEFAULT_CONFIG = {lang: {"provider": "edge", "voice": v, "rate": RATE} for lang, v in VOICES.items()}
EL_API = "https://api.elevenlabs.io/v1/"
EL_FORMAT = "mp3_44100_64"
ID_RE = re.compile(r"^[A-Za-z0-9.-]+$")


class TTSError(Exception):
    pass


class EdgeTTS:
    """The only place that talks to the TTS service. Tests replace it with a fake."""

    def synth(self, text: str, voice: str, rate: str, path: str) -> None:
        try:
            import edge_tts  # noqa: PLC0415 — optional dependency, only needed for real recording
        except ImportError as e:
            raise TTSError("edge-tts is not installed: pip install edge-tts") from e

        async def _save():
            await edge_tts.Communicate(text, voice, rate=rate).save(path)

        asyncio.run(_save())


def text_hash(text: str, voice: str, rate: str) -> str:
    """Hash of an edge-tts line (kept exactly as before, so existing recordings stay valid)."""
    return hashlib.sha1(f"{voice}|{rate}|{text}".encode("utf-8")).hexdigest()


def voice_key(cfg: dict) -> str:
    """What identifies a voice: changing any part re-records every line of that language."""
    if cfg.get("provider", "edge") == "edge":
        return f"{cfg.get('voice')}|{cfg.get('rate', RATE)}"          # legacy form (edge provider)
    parts = {k: cfg.get(k) for k in ("provider", "voice_name", "voice_id", "model_id", "language_code", "voice_settings")}
    return "elevenlabs|" + json.dumps(parts, sort_keys=True, ensure_ascii=False)


def line_hash(text: str, cfg: dict) -> str:
    return hashlib.sha1(f"{voice_key(cfg)}|{text}".encode("utf-8")).hexdigest()


def load_config(vdir: str) -> dict:
    cfg = {lang: dict(c) for lang, c in DEFAULT_CONFIG.items()}
    user = load_json(os.path.join(vdir, "config.json"), {}) or {}
    for lang, c in user.items():
        if isinstance(c, dict):
            cfg[lang] = dict(c)
    return cfg


class QuotaError(TTSError):
    pass


class PermissionMissing(TTSError):
    """401 missing_permissions — the key works, it just may not call this endpoint."""


class FatalTTSError(TTSError):
    """Not worth retrying (bad key, plan, missing voice)."""


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


class RateLimited(TTSError):
    def __init__(self, wait: float | None):
        super().__init__("ElevenLabs: příliš mnoho požadavků (429)")
        self.wait = wait


class LanguageCodeRejected(TTSError):
    pass


def _retry_after(err) -> float | None:
    try:
        return float(err.headers.get("Retry-After"))
    except (TypeError, ValueError, AttributeError):
        return None


class EdgeProvider:
    def __init__(self, cfg: dict, tts=None):
        self.cfg = cfg; self.tts = tts or EdgeTTS()
        self.label = f"edge {cfg.get('voice')}"

    def synth(self, text: str, path: str) -> None:
        self.tts.synth(text, self.cfg.get("voice"), self.cfg.get("rate", RATE), path)


class ElevenLabsProvider:
    def __init__(self, cfg: dict, api):
        self.cfg = cfg; self.api = api
        self.label = f"ElevenLabs „{cfg.get('voice_name') or cfg.get('voice_id')}“ ({cfg.get('model_id')})"
        self.voice_id = cfg.get("voice_id")
        self.send_language = bool(cfg.get("language_code"))

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
    for attempt in range(1, retries + 1):
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
        except Exception as e:  # network, service throttling, empty audio — all transient here
            last = e
            if os.path.exists(tmp):
                os.remove(tmp)
            if attempt < retries:
                time.sleep(min(60.0, e.wait) if isinstance(e, RateLimited) and e.wait else wait)
                wait *= 2
    raise TTSError(f"{last.__class__.__name__}: {last}")


def _needed(lang, phrases, index, cfg, vdir, force):
    """[(pid, text, hash, why)] lines of a language that need recording ('new', 'changed', 'suspect')."""
    out = []
    for pid, text in sorted(phrases.items()):
        if not ID_RE.match(pid) or not isinstance(text, str) or not text.strip():
            continue
        h = text_hash(text, cfg.get("voice"), cfg.get("rate", RATE)) if cfg.get("provider", "edge") == "edge" else line_hash(text, cfg)
        entry = index.get(lang, {}).get(pid)
        dest = os.path.join(vdir, lang, f"{pid}.mp3")
        if force or not entry or entry.get("sha1") != h or not os.path.exists(dest):
            out.append((pid, text, h, "new" if not entry else "changed"))
        else:
            problem = audio_problem(dest, text)          # re-validate cached files: heals stubs kept by the CI cache
            if problem:
                out.append((pid, text, h, f"suspect: {problem}"))
    return out


def run(root: str = HERE, tts=None, force: bool = False, langs=None, retries: int = 3, delay: float = 2.0,
        pause: float = 0.2, out=sys.stdout, eleven=None) -> int:
    vdir = os.path.join(root, "voice")
    phrases = load_json(os.path.join(vdir, "phrases.json"))
    if not isinstance(phrases, dict) or not phrases:
        print("Chybí voice/phrases.json — nejdřív spusťte: node dev/export_phrases.mjs", file=out)
        return 2
    config = load_config(vdir)
    index_path = os.path.join(vdir, "index.json")
    index = load_json(index_path, {}) or {}
    langs = [lang for lang in (langs or phrases.keys()) if lang in config and lang in phrases]
    totals = {"made": 0, "skipped": 0, "failed": 0, "suspect": 0, "healed": 0, "removed": 0}
    bad = [(lang, pid) for lang in langs for pid, text in phrases[lang].items()
           if not ID_RE.match(pid) or not isinstance(text, str) or not text.strip()]
    for lang, pid in bad:
        print(f"{lang} {pid}: CHYBA: neplatné id nebo prázdný text", file=out, flush=True)
    totals["failed"] += len(bad)
    for lang in langs:
        cfg = config[lang]
        need = _needed(lang, phrases[lang], index, cfg, vdir, force)
        totals["skipped"] += sum(1 for pid, text in phrases[lang].items() if ID_RE.match(pid) and isinstance(text, str) and text.strip()) - len(need)
        if cfg.get("provider", "edge") == "elevenlabs":
            _run_elevenlabs(lang, cfg, need, phrases[lang], index, index_path, vdir, eleven, retries, delay, pause, out, totals)
        else:
            _run_edge(lang, cfg, need, index, index_path, vdir, tts, retries, delay, pause, out, totals)
        totals["removed"] += _prune(lang, phrases.get(lang, {}), index, vdir)
    write_json_atomic(index_path, index)
    t = totals
    print(f"\nNahráno {t['made']}, beze změny {t['skipped']}, odstraněno {t['removed']}, podezřelé {t['suspect']} (opraveno {t['healed']}), chyb {t['failed']}.",
          file=out, flush=True)
    if t["failed"]:
        print("Věty s chybou hra řekne hlasem prohlížeče. Skript lze spustit znovu, dodělá jen chybějící.", file=out)
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


def _run_edge(lang, cfg, need, index, index_path, vdir, tts, retries, delay, pause, out, t):
    """edge-tts: line by line (same voice, so partial progress is fine)."""
    provider = EdgeProvider(cfg, tts)
    os.makedirs(os.path.join(vdir, lang), exist_ok=True)
    print(f"{lang}: {provider.label} — nahrávám {len(need)} vět, ostatní přeskočeno (beze změny) …", file=out, flush=True)
    for i, (pid, text, h, why) in enumerate(need, 1):
        prefix = f"[{i}/{len(need)}] {lang} {pid} …"
        dest = os.path.join(vdir, lang, f"{pid}.mp3")
        suspect = why.startswith("suspect")
        if suspect:
            t["suspect"] += 1
            print(f"{prefix} podezřelé ({why[9:]}), nahrávám znovu … ", end="", file=out, flush=True)
        else:
            print(f"{prefix} nahrávám … ", end="", file=out, flush=True)
        try:
            size = record(provider, text, dest, retries, delay)
        except TTSError as e:
            t["failed"] += 1
            # never keep a bad or outdated recording: the app then says this line with the browser voice
            if os.path.isfile(dest):
                os.remove(dest)
            if index.get(lang, {}).pop(pid, None) is not None:
                write_json_atomic(index_path, index)
            print(f"CHYBA: {e} (smazáno, hra použije hlas prohlížeče)", file=out, flush=True)
            continue
        if suspect:
            t["healed"] += 1
        index.setdefault(lang, {})[pid] = {"text": text, "sha1": h, "file": f"{lang}/{pid}.mp3", "bytes": size,
                                           "voice": cfg.get("voice"), "provider": "edge"}
        write_json_atomic(index_path, index)
        t["made"] += 1
        print(f"hotovo {round(size / 1024)} kB", file=out, flush=True)
        if pause:
            time.sleep(pause)


def _run_elevenlabs(lang, cfg, need, phrases, index, index_path, vdir, api, retries, delay, pause, out, t):
    """ElevenLabs: quota check, then record everything into a staging folder; switch only if ALL lines succeeded."""
    if not need:
        print(f"{lang}: ElevenLabs — vše nahráno, beze změny.", file=out, flush=True)
        return
    provider = ElevenLabsProvider(cfg, api or ElevenLabsAPI())
    chars = sum(len(text) for _, text, _, _ in need)
    print(f"{lang}: {provider.label} — potřeba {len(need)} vět, {chars} znaků.", file=out, flush=True)
    try:
        try:
            sub = provider.api.subscription()
        except PermissionMissing:
            sub = None
            print(f"{lang}: stav kreditů nelze ověřit (klíč nemá oprávnění user_read) — pokračuji; "
                  f"když kredity dojdou, přepnutí se zruší a stávající nahrávky zůstanou.", file=out, flush=True)
        remaining = (int(sub.get("character_limit", 0)) - int(sub.get("character_count", 0))) if sub else chars
        if chars > remaining:
            t["failed"] += len(need)
            print(f"{lang}: NIC SE NENAHRÁVÁ — potřeba {chars} znaků, ale v ElevenLabs zbývá jen {max(0, remaining)} "
                  f"(limit {sub.get('character_limit')}, použito {sub.get('character_count')}). Stávající nahrávky zůstávají.",
                  file=out, flush=True)
            return
        if sub:
            print(f"{lang}: kredity v pořádku (zbývá {remaining} znaků, po nahrání {remaining - chars}).", file=out, flush=True)
        provider.resolve()
    except TTSError as e:
        t["failed"] += len(need)
        print(f"{lang}: NIC SE NENAHRÁVÁ — {e}. Stávající nahrávky zůstávají.", file=out, flush=True)
        return
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
            done.append((pid, text, h, why, size))
            print(f"hotovo {round(size / 1024)} kB", file=out, flush=True)
            if pause:
                time.sleep(pause)
        # all succeeded: move in and update the index in one go
        os.makedirs(os.path.join(vdir, lang), exist_ok=True)
        for pid, text, h, why, size in done:
            os.replace(os.path.join(stage, f"{pid}.mp3"), os.path.join(vdir, lang, f"{pid}.mp3"))
            index.setdefault(lang, {})[pid] = {"text": text, "sha1": h, "file": f"{lang}/{pid}.mp3", "bytes": size,
                                               "voice": cfg.get("voice_name") or cfg.get("voice_id"), "provider": "elevenlabs",
                                               "model": cfg.get("model_id")}
            t["made"] += 1
            if why.startswith("suspect"):
                t["suspect"] += 1
                t["healed"] += 1
        write_json_atomic(index_path, index)
        print(f"{lang}: hlas přepnut — {len(done)} vět nahráno ({provider.label}).", file=out, flush=True)
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Record Mořský svět voice lines (voice/config.json: edge-tts or ElevenLabs)")
    ap.add_argument("--force", action="store_true", help="re-record everything")
    ap.add_argument("--lang", help="only one language (e.g. cs)")
    args = ap.parse_args(argv)
    return run(HERE, force=args.force, langs=[args.lang] if args.lang else None)


if __name__ == "__main__":
    sys.exit(main())
