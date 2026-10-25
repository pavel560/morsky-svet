"""make_voice.py with fake service layers (the real services are not reachable from CI sandboxes)."""
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import make_voice as mv  # noqa: E402

MP3 = b"ID3" + b"\x00" * 12000          # big enough to pass the length check for the test texts
STUB = b"ID3" + b"\x00" * 1900          # the ~2 kB stub the service sometimes returns
LEGACY = b"ID3" + b"\x01" * 12000       # an old edge-tts recording (not licensed)

AZ_CFG = {"provider": "azure", "voice": "en-GB-MaisieNeural", "rate": "-8%", "licence": {"plan": "Azure AI Speech"}}
EL_CS = {"provider": "elevenlabs", "voice_name": "Candy - Young and Sweet", "model_id": "eleven_multilingual_v2",
         "language_code": "cs", "voice_settings": {"stability": 0.45, "similarity_boost": 0.8, "style": 0.35, "use_speaker_boost": True},
         "licence": {"plan": "ElevenLabs Starter", "since": "2026-10-12T15:15:00Z"}}


def said(ssml):
    return re.search(r"<prosody[^>]*>(.*)</prosody>", ssml).group(1)


class FakeAzure:
    """Mocked Azure REST layer: tts(ssml)."""

    def __init__(self, fail=None, stub=None, limited=0):
        self.calls = []
        self.fail = dict(fail or {})      # text -> number of failures before success
        self.stub = dict(stub or {})      # text -> number of tiny "successful" outputs before a good one
        self.limited = limited            # first N calls answer 429

    def check(self):
        pass

    def tts(self, ssml):
        self.calls.append(ssml)
        text = said(ssml)
        if self.limited > 0:
            self.limited -= 1
            raise mv.RateLimited(5.0, "Azure")
        if self.fail.get(text, 0) > 0:
            self.fail[text] -= 1
            raise ConnectionResetError("reset")
        if self.stub.get(text, 0) > 0:
            self.stub[text] -= 1
            return STUB
        return MP3

    def texts(self):
        return [said(s) for s in self.calls]


class FakeEleven:
    """Mocked ElevenLabs REST layer: voices(), subscription(), tts(voice_id, body)."""

    def __init__(self, used=0, limit=30000, voices=None, fail_on=None, tiny_on=None, reject_language=False):
        self.used, self.limit = used, limit
        self.voice_list = voices if voices is not None else [{"voice_id": "v-other", "name": "Somebody"}, {"voice_id": "v-candy", "name": "Candy - Young and Sweet"}]
        self.fail_on = set(fail_on or [])          # texts that fail permanently
        self.tiny_on = set(tiny_on or [])          # texts that come back as a 2 kB stub
        self.reject_language = reject_language
        self.calls = []

    def voices(self):
        return self.voice_list

    def subscription(self):
        return {"character_count": self.used, "character_limit": self.limit}

    def tts(self, voice_id, body):
        self.calls.append((voice_id, dict(body)))
        if self.reject_language and "language_code" in body:
            raise mv.LanguageCodeRejected("language_code not supported for this model")
        if body["text"] in self.fail_on:
            raise mv.TTSError("HTTP 500")
        self.used += len(body["text"])
        return STUB if body["text"] in self.tiny_on else MP3


class Base(unittest.TestCase):
    PHRASES = {"cs": {"ui.say.greeting": "Ahoj!", "sp.liska.name": "Liška obecná.", "ui.vyprava.wait": "Počkej, něco tu je!"},
               "en": {"ui.say.greeting": "Hello!", "sp.liska.name": "Red fox."}}

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="game-voice-")
        self.vdir = os.path.join(self.root, "voice")
        os.makedirs(self.vdir)
        self.dump("phrases.json", self.PHRASES)
        self.dump("config.json", {"cs": EL_CS, "en": AZ_CFG})
        self.out = io.StringIO()
        self.sleep = mock.patch("time.sleep", lambda s: None)
        self.sleep.start()

    def tearDown(self):
        self.sleep.stop()
        shutil.rmtree(self.root, ignore_errors=True)

    def dump(self, name, obj):
        with open(os.path.join(self.vdir, name), "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False)

    def index(self):
        with open(os.path.join(self.vdir, "index.json"), encoding="utf-8") as f:
            return json.load(f)

    def read_mp3(self, lang, pid):
        with open(os.path.join(self.vdir, lang, f"{pid}.mp3"), "rb") as f:
            return f.read()

    def seed_legacy(self, langs=("cs", "en")):
        """The state before this change: every line recorded by edge-tts (Vlasta / Maisie), as the old index wrote it."""
        idx = {}
        for lang in langs:
            os.makedirs(os.path.join(self.vdir, lang), exist_ok=True)
            for pid, text in self.PHRASES[lang].items():
                with open(os.path.join(self.vdir, lang, f"{pid}.mp3"), "wb") as f:
                    f.write(LEGACY)
                idx.setdefault(lang, {})[pid] = {"text": text, "sha1": "legacy", "file": f"{lang}/{pid}.mp3", "bytes": len(LEGACY),
                                                 "voice": "en-GB-MaisieNeural" if lang == "en" else "cs-CZ-VlastaNeural", "provider": "edge"}
        self.dump("index.json", idx)

    def run_mv(self, eleven=None, azure=None, **kw):
        return mv.run(self.root, pause=0, out=self.out, eleven=eleven or FakeEleven(), azure=azure or FakeAzure(), **kw)

    def audit(self):
        buf = io.StringIO()
        code = mv.audit(self.root, out=buf)
        return code, buf.getvalue()


class TestRecording(Base):
    def test_records_all_with_right_voices_and_index(self):
        az, el = FakeAzure(), FakeEleven()
        self.assertEqual(self.run_mv(el, az), 0)
        self.assertEqual(len(az.calls), 2)
        self.assertEqual(len(el.calls), 3)
        self.assertIn('<voice name="en-GB-MaisieNeural"><prosody rate="-8%">Hello!</prosody></voice>', az.calls[0] + az.calls[1])
        self.assertIn('xml:lang="en-GB"', az.calls[0])
        idx = self.index()
        e = idx["en"]["sp.liska.name"]
        self.assertEqual((e["file"], e["text"], e["provider"], e["voice"], e["licence"]), ("en/sp.liska.name.mp3", "Red fox.", "azure", "en-GB-MaisieNeural", "Azure AI Speech"))
        self.assertRegex(e["recorded"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
        self.assertEqual(idx["cs"]["ui.say.greeting"]["licence"], "ElevenLabs Starter")
        self.assertTrue(os.path.isfile(os.path.join(self.vdir, "en", "sp.liska.name.mp3")))
        self.assertIn("[1/2] en sp.liska.name … nahrávám … hotovo 12 kB", self.out.getvalue())

    def test_second_run_records_nothing(self):
        self.run_mv()
        az, el = FakeAzure(), FakeEleven()
        self.assertEqual(self.run_mv(el, az), 0)
        self.assertEqual((az.calls, el.calls), ([], []))
        self.assertIn("vše nahráno, beze změny", self.out.getvalue())

    def test_changed_text_rerecorded_removed_text_pruned(self):
        self.run_mv()
        self.dump("phrases.json", {"cs": self.PHRASES["cs"], "en": {"ui.say.greeting": "Hello, friend!"}})
        az = FakeAzure()
        self.run_mv(azure=az)
        self.assertEqual(az.texts(), ["Hello, friend!"])
        self.assertNotIn("sp.liska.name", self.index()["en"])
        self.assertFalse(os.path.exists(os.path.join(self.vdir, "en", "sp.liska.name.mp3")))

    def test_transient_failure_is_retried(self):
        az = FakeAzure(fail={"Hello!": 2})
        self.assertEqual(self.run_mv(azure=az, langs=["en"]), 0)
        self.assertEqual(az.texts().count("Hello!"), 3)

    def test_rate_limit_is_waited_out_without_using_retries(self):
        az = FakeAzure(limited=4)
        waits = []
        with mock.patch("time.sleep", lambda s: waits.append(s)):
            self.assertEqual(self.run_mv(azure=az, langs=["en"], retries=1), 0)
        self.assertEqual(waits.count(5.0), 4)

    def test_permanent_failure_keeps_the_old_recordings(self):
        self.seed_legacy()
        az = FakeAzure(fail={"Hello!": 99})
        self.assertEqual(self.run_mv(azure=az, langs=["en"], retries=2), 1)
        self.assertEqual(self.index()["en"]["sp.liska.name"]["provider"], "edge")       # nothing switched
        self.assertEqual(self.read_mp3("en", "sp.liska.name"), LEGACY)
        self.assertFalse(os.path.exists(os.path.join(self.vdir, ".staging-en")))
        self.assertIn("PŘEPNUTÍ HLASU ZRUŠENO", self.out.getvalue())

    def test_empty_audio_is_rejected(self):
        class Empty(FakeAzure):
            def tts(self, ssml):
                return b""
        self.assertEqual(self.run_mv(azure=Empty(), langs=["en"], retries=1), 1)

    def test_tiny_output_is_retried(self):
        az = FakeAzure(stub={"Hello!": 2})
        self.assertEqual(self.run_mv(azure=az, langs=["en"]), 0)
        self.assertEqual(az.texts().count("Hello!"), 3)
        self.assertGreater(os.path.getsize(os.path.join(self.vdir, "en", "ui.say.greeting.mp3")), 4000)

    def test_cached_tiny_file_is_regenerated(self):
        self.run_mv()
        stub_path = os.path.join(self.vdir, "en", "sp.liska.name.mp3")
        with open(stub_path, "wb") as f:                     # a 2 kB stub with a matching hash
            f.write(STUB)
        az = FakeAzure()
        self.assertEqual(self.run_mv(azure=az), 0)
        self.assertEqual(az.texts(), ["Red fox."])
        self.assertGreater(os.path.getsize(stub_path), 4000)
        self.assertIn("podezřelé 1 (opraveno 1)", self.out.getvalue())

    def test_min_bytes_scales_with_text(self):
        self.assertEqual(mv.min_bytes("Ahoj!"), 4000)
        self.assertEqual(mv.min_bytes("x" * 100), 20000)

    def test_missing_phrases(self):
        os.remove(os.path.join(self.vdir, "phrases.json"))
        self.assertEqual(self.run_mv(), 2)
        self.assertEqual(mv.audit(self.root, out=io.StringIO()), 2)

    def test_force(self):
        self.run_mv()
        az, el = FakeAzure(), FakeEleven()
        self.run_mv(el, az, force=True)
        self.assertEqual((len(az.calls), len(el.calls)), (2, 3))

    def test_ssml_is_escaped(self):
        p = mv.AzureProvider(AZ_CFG, FakeAzure())
        s = p.ssml('Tom & Jerry <3 "hi"')
        self.assertIn("Tom &amp; Jerry &lt;3", s)
        self.assertNotIn("<3", s)


class TestLicensing(Base):
    def test_edge_recordings_are_replaced_by_the_licensed_voice(self):
        self.seed_legacy(("en",))
        az = FakeAzure()
        self.assertEqual(self.run_mv(azure=az, langs=["en"]), 0)
        self.assertEqual(sorted(az.texts()), ["Hello!", "Red fox."])
        self.assertTrue(all(e["provider"] == "azure" for e in self.index()["en"].values()))
        self.assertEqual(self.read_mp3("en", "sp.liska.name"), MP3)

    def test_edge_is_refused_as_a_provider(self):
        self.seed_legacy(("en",))
        self.dump("config.json", {"cs": EL_CS, "en": {"provider": "edge", "voice": "en-GB-MaisieNeural", "rate": "-8%"}})
        az = FakeAzure()
        self.assertEqual(self.run_mv(azure=az, langs=["en"]), 1)
        self.assertEqual(az.calls, [])
        self.assertIn("není licencovaná pro komerční nahrávky", self.out.getvalue())
        self.assertEqual(self.read_mp3("en", "sp.liska.name"), LEGACY)

    def test_language_without_config_is_an_error(self):
        self.dump("config.json", {"cs": EL_CS})
        self.assertEqual(self.run_mv(langs=["en"]), 1)
        self.assertIn("nemá hlas pro tento jazyk", self.out.getvalue())

    def test_missing_azure_key_records_nothing(self):
        self.seed_legacy(("en",))
        with mock.patch.dict(os.environ, {"AZURE_SPEECH_KEY": "", "AZURE_SPEECH_REGION": ""}):
            code = mv.run(self.root, pause=0, out=self.out, eleven=FakeEleven(), azure=mv.AzureSpeechAPI(), langs=["en"])
        self.assertEqual(code, 1)
        self.assertIn("NIC SE NENAHRÁVÁ — chybí AZURE_SPEECH_KEY a AZURE_SPEECH_REGION", self.out.getvalue())
        self.assertEqual(self.read_mp3("en", "sp.liska.name"), LEGACY)

    def test_audit_passes_after_licensed_recording(self):
        self.run_mv()
        code, text = self.audit()
        self.assertEqual(code, 0, text)
        self.assertIn("cs: v pořádku — 3/3 vět, ElevenLabs Starter (licence od 2026-10-12T15:15:00Z)", text)
        self.assertIn("en: v pořádku — 2/2 vět, Azure AI Speech", text)

    def test_audit_flags_edge_recordings_with_the_cost(self):
        self.run_mv(langs=["cs"])
        self.seed_legacy(("en",))
        idx = self.index()
        code, text = self.audit()
        self.assertEqual(code, 1)
        self.assertIn("en: K PŘENAHRÁNÍ 2/2 vět, 14 znaků", text)
        self.assertIn("2× nahráno službou bez komerční licence (edge-tts)", text)
        self.assertEqual(idx, self.index())                   # the audit never writes

    def test_audit_flags_recordings_from_before_the_licence(self):
        self.run_mv()
        idx = self.index()
        idx["cs"]["ui.say.greeting"]["recorded"] = "2026-10-12T15:01:58Z"   # recorded on the free plan
        self.dump("index.json", idx)
        code, text = self.audit()
        self.assertEqual(code, 1)
        self.assertIn("cs: K PŘENAHRÁNÍ 1/3 vět, 5 znaků", text)
        self.assertIn("nahráno před začátkem licence", text)

    def test_audit_flags_a_voice_that_no_longer_matches_the_config(self):
        self.run_mv()
        self.dump("config.json", {"cs": EL_CS, "en": {**AZ_CFG, "voice": "en-GB-LibbyNeural"}})
        code, text = self.audit()
        self.assertEqual(code, 1)
        self.assertIn("2× nahráno jiným hlasem", text)

    def test_licence_metadata_does_not_change_the_hash(self):
        """Adding or editing the licence note must not re-record (and so re-bill) a whole language."""
        base = {k: v for k, v in EL_CS.items() if k != "licence"}
        self.assertEqual(mv.line_hash("Ahoj!", base), mv.line_hash("Ahoj!", EL_CS))

    def test_hash_changes_with_voice_model_or_settings(self):
        h = mv.line_hash("Ahoj!", EL_CS)
        for change in ({"voice_name": "Other"}, {"model_id": "eleven_v3"}, {"voice_settings": {**EL_CS["voice_settings"], "style": 0.5}},
                       {"provider": "azure", "voice": "x"}):
            self.assertNotEqual(h, mv.line_hash("Ahoj!", {**EL_CS, **change}), change)
        a = mv.line_hash("Hi", AZ_CFG)
        for change in ({"voice": "en-GB-LibbyNeural"}, {"rate": "0%"}, {"style": "cheerful"}):
            self.assertNotEqual(a, mv.line_hash("Hi", {**AZ_CFG, **change}), change)

    def test_elevenlabs_hash_format_is_unchanged(self):
        """The Czech recordings committed before this change must stay valid (no re-recording, no new credits)."""
        parts = {k: EL_CS.get(k) for k in ("provider", "voice_name", "voice_id", "model_id", "language_code", "voice_settings")}
        legacy = "elevenlabs|" + json.dumps(parts, sort_keys=True, ensure_ascii=False)
        import hashlib
        self.assertEqual(mv.line_hash("Ahoj!", EL_CS), hashlib.sha1(f"{legacy}|Ahoj!".encode("utf-8")).hexdigest())

    def test_azure_http_layer_maps_errors(self):
        import urllib.error
        api = mv.AzureSpeechAPI(key="k", region="westeurope")

        def boom(code):
            def f(req, timeout=None):
                raise urllib.error.HTTPError("https://x", code, "err", {"Retry-After": "3"}, io.BytesIO(b"{}"))
            return f
        for code, exc in ((401, mv.FatalTTSError), (403, mv.FatalTTSError), (429, mv.RateLimited), (500, mv.TTSError)):
            with self.subTest(code=code), mock.patch("urllib.request.urlopen", boom(code)):
                with self.assertRaises(exc):
                    api.tts("<speak/>")
        seen = {}

        class Resp(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self, *a): return False

        def ok(req, timeout=None):
            seen.update(url=req.full_url, headers=dict(req.headers))
            return Resp(MP3)
        with mock.patch("urllib.request.urlopen", ok):
            self.assertEqual(api.tts("<speak/>"), MP3)
        self.assertEqual(seen["url"], "https://westeurope.tts.speech.microsoft.com/cognitiveservices/v1")
        self.assertEqual(seen["headers"]["X-microsoft-outputformat"], "audio-24khz-48kbitrate-mono-mp3")


class TestElevenLabs(Base):
    def setUp(self):
        super().setUp()
        self.seed_legacy()                     # Czech still in the old edge-tts voice
        self.vlasta = self.read_mp3("cs", "sp.liska.name")

    def run_el(self, api, **kw):
        return self.run_mv(eleven=api, langs=["cs"], **kw)

    def test_success_switches_whole_language_atomically(self):
        api = FakeEleven()
        self.assertEqual(self.run_el(api), 0)
        self.assertEqual(len(api.calls), 3)                                   # every Czech line, Candy's voice id
        self.assertTrue(all(c[0] == "v-candy" for c in api.calls))
        body = api.calls[0][1]
        self.assertEqual((body["model_id"], body["language_code"], body["voice_settings"]["stability"]), ("eleven_multilingual_v2", "cs", 0.45))
        idx = self.index()
        self.assertTrue(all(e["provider"] == "elevenlabs" and e["voice"] == "Candy - Young and Sweet" for e in idx["cs"].values()))
        self.assertEqual(idx["en"]["ui.say.greeting"]["provider"], "edge")  # English untouched (not asked for)
        self.assertFalse(os.path.exists(os.path.join(self.vdir, ".staging-cs")))
        self.assertIn("hlas přepnut — 3 vět", self.out.getvalue())
        api2 = FakeEleven()
        self.assertEqual(self.run_el(api2), 0)
        self.assertEqual(api2.calls, [])

    def test_partial_failure_keeps_the_old_voice(self):
        before = self.index()
        self.assertEqual(self.run_el(FakeEleven(fail_on={"Počkej, něco tu je!"}), retries=2), 1)
        self.assertEqual(self.index()["cs"], before["cs"])
        self.assertEqual(self.read_mp3("cs", "sp.liska.name"), self.vlasta)
        self.assertFalse(os.path.exists(os.path.join(self.vdir, ".staging-cs")))
        self.assertIn("PŘEPNUTÍ HLASU ZRUŠENO", self.out.getvalue())

    def test_tiny_output_counts_as_failure_and_blocks_the_switch(self):
        before = self.index()
        self.assertEqual(self.run_el(FakeEleven(tiny_on={"Ahoj!"}), retries=2), 1)
        self.assertEqual(self.index()["cs"], before["cs"])

    def test_quota_guard_refuses_before_spending(self):
        need = sum(len(t) for t in self.PHRASES["cs"].values())
        api = FakeEleven(used=30000 - need + 1, limit=30000)
        self.assertEqual(self.run_el(api), 1)
        self.assertEqual(api.calls, [])
        self.assertIn(f"potřeba {need} znaků, ale v ElevenLabs zbývá jen {need - 1}", self.out.getvalue())
        self.assertEqual(self.index()["cs"]["sp.liska.name"]["provider"], "edge")

    def test_quota_exactly_enough_records(self):
        need = sum(len(t) for t in self.PHRASES["cs"].values())
        self.assertEqual(self.run_el(FakeEleven(used=30000 - need, limit=30000)), 0)

    def test_key_without_user_read_still_records(self):
        class NoUserRead(FakeEleven):
            def subscription(self): raise mv.PermissionMissing("missing_permissions user_read")
        api = NoUserRead()
        self.assertEqual(self.run_el(api), 0)
        self.assertEqual(len(api.calls), 3)
        self.assertIn("stav kreditů nelze ověřit", self.out.getvalue())

    def test_voice_not_in_my_voices(self):
        api = FakeEleven(voices=[{"voice_id": "x", "name": "Somebody"}])
        self.assertEqual(self.run_el(api), 1)
        self.assertEqual(api.calls, [])
        self.assertIn("není v „My voices“", self.out.getvalue())

    def test_bad_key_or_plan_is_reported_cleanly(self):
        class NoPlan(FakeEleven):
            def tts(self, voice_id, body):
                raise mv.QuotaError("ElevenLabs: došly kredity nebo je potřeba placený plán (402)")
        self.assertEqual(self.run_el(NoPlan(), retries=3), 1)
        self.assertIn("placený plán", self.out.getvalue())
        self.assertEqual(self.read_mp3("cs", "sp.liska.name"), self.vlasta)

    def test_language_code_rejected_is_retried_without_it(self):
        api = FakeEleven(reject_language=True)
        self.assertEqual(self.run_el(api), 0)
        self.assertTrue(all("language_code" not in c[1] for c in api.calls[1:]))

    def test_committed_recordings_need_no_service(self):
        """With every recording committed and licensed, a run makes no network call at all, even without keys."""
        self.run_mv()

        class NoNetwork(FakeEleven):
            def voices(self): raise AssertionError("network")
            def subscription(self): raise AssertionError("network")
            def tts(self, voice_id, body): raise AssertionError("network")

        class NoAzure(FakeAzure):
            def tts(self, ssml): raise AssertionError("network")
        with mock.patch.dict(os.environ, {"ELEVENLABS_API_KEY": "", "AZURE_SPEECH_KEY": ""}):
            self.assertEqual(mv.run(self.root, pause=0, out=self.out), 0)
            self.assertEqual(mv.run(self.root, pause=0, out=self.out, eleven=NoNetwork(), azure=NoAzure()), 0)

    def test_config_change_rerecords_that_language(self):
        self.run_el(FakeEleven())
        cfg = json.loads(json.dumps(EL_CS)); cfg["voice_settings"]["style"] = 0.6
        self.dump("config.json", {"cs": cfg, "en": AZ_CFG})
        api = FakeEleven()
        self.assertEqual(self.run_el(api), 0)
        self.assertEqual(len(api.calls), 3)

    def test_http_layer_maps_errors(self):
        import urllib.error
        api = mv.ElevenLabsAPI(key="k")

        def boom(code, body=b"{}"):
            def f(req, timeout=None):
                raise urllib.error.HTTPError("https://x", code, "err", {"Retry-After": "3"}, io.BytesIO(body))
            return f
        for code, exc in ((401, mv.FatalTTSError), (402, mv.QuotaError), (429, mv.RateLimited), (500, mv.TTSError)):
            with self.subTest(code=code), mock.patch("urllib.request.urlopen", boom(code)):
                with self.assertRaises(exc):
                    api.tts("v", {"text": "x"})
        with mock.patch("urllib.request.urlopen", boom(400, b'{"detail":"language_code unsupported"}')):
            with self.assertRaises(mv.LanguageCodeRejected):
                api.tts("v", {"text": "x"})
        with mock.patch.dict(os.environ, {"ELEVENLABS_API_KEY": ""}):
            with self.assertRaises(mv.FatalTTSError):
                mv.ElevenLabsAPI(key="").voices()


if __name__ == "__main__":
    unittest.main()
