"""make_voice.py with a fake TTS layer (the real service is not reachable from CI sandboxes)."""
import io
import json
import os
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


class FakeTTS:
    def __init__(self, fail=None, stub=None):
        self.calls = []
        self.fail = dict(fail or {})      # text -> number of failures before success
        self.stub = dict(stub or {})      # text -> number of tiny "successful" outputs before a good one

    def synth(self, text, voice, rate, path):
        self.calls.append((text, voice, rate))
        if self.fail.get(text, 0) > 0:
            self.fail[text] -= 1
            raise ConnectionResetError("reset")
        data = MP3
        if self.stub.get(text, 0) > 0:
            self.stub[text] -= 1
            data = STUB
        with open(path, "wb") as f:
            f.write(data)


class TestMakeVoice(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="houbicky-voice-")
        os.makedirs(os.path.join(self.root, "voice"))
        self.write({"cs": {"ui.say.greeting": "Ahoj!", "sp.liska.name": "Liška obecná."}, "en": {"ui.say.greeting": "Hello!"}})
        self.out = io.StringIO()
        self.sleep = mock.patch("time.sleep", lambda s: None)
        self.sleep.start()

    def tearDown(self):
        self.sleep.stop()
        shutil.rmtree(self.root, ignore_errors=True)

    def write(self, phrases):
        with open(os.path.join(self.root, "voice", "phrases.json"), "w", encoding="utf-8") as f:
            json.dump(phrases, f, ensure_ascii=False)

    def index(self):
        with open(os.path.join(self.root, "voice", "index.json"), encoding="utf-8") as f:
            return json.load(f)

    def run_mv(self, tts, **kw):
        return mv.run(self.root, tts, pause=0, out=self.out, **kw)

    def test_records_all_with_right_voices_and_index(self):
        tts = FakeTTS()
        self.assertEqual(self.run_mv(tts), 0)
        self.assertEqual(len(tts.calls), 3)
        self.assertIn(("Ahoj!", "cs-CZ-VlastaNeural", "-8%"), tts.calls)
        self.assertIn(("Hello!", "en-GB-MaisieNeural", "-8%"), tts.calls)
        idx = self.index()
        self.assertEqual(idx["cs"]["sp.liska.name"]["file"], "cs/sp.liska.name.mp3")
        self.assertEqual(idx["cs"]["sp.liska.name"]["text"], "Liška obecná.")
        self.assertTrue(os.path.isfile(os.path.join(self.root, "voice", "cs", "sp.liska.name.mp3")))
        self.assertIn("[1/2] cs sp.liska.name … nahrávám … hotovo 12 kB", self.out.getvalue())

    def test_second_run_records_nothing(self):
        self.run_mv(FakeTTS())
        tts = FakeTTS()
        self.assertEqual(self.run_mv(tts), 0)
        self.assertEqual(tts.calls, [])
        self.assertIn("přeskočeno (beze změny)", self.out.getvalue())

    def test_changed_text_rerecorded_removed_text_pruned(self):
        self.run_mv(FakeTTS())
        self.write({"cs": {"ui.say.greeting": "Ahoj, kamarádko!"}, "en": {"ui.say.greeting": "Hello!"}})
        tts = FakeTTS()
        self.run_mv(tts)
        self.assertEqual([c[0] for c in tts.calls], ["Ahoj, kamarádko!"])
        idx = self.index()
        self.assertNotIn("sp.liska.name", idx["cs"])
        self.assertFalse(os.path.exists(os.path.join(self.root, "voice", "cs", "sp.liska.name.mp3")))

    def test_transient_failure_is_retried(self):
        tts = FakeTTS(fail={"Ahoj!": 2})
        self.assertEqual(self.run_mv(tts, langs=["cs"]), 0)
        self.assertEqual(sum(1 for c in tts.calls if c[0] == "Ahoj!"), 3)

    def test_permanent_failure_reported_and_others_continue(self):
        tts = FakeTTS(fail={"Ahoj!": 99})
        self.assertEqual(self.run_mv(tts, langs=["cs"], retries=2), 1)
        idx = self.index()
        self.assertNotIn("ui.say.greeting", idx.get("cs", {}))
        self.assertIn("sp.liska.name", idx["cs"])
        self.assertFalse([p for p in os.listdir(os.path.join(self.root, "voice", "cs")) if ".part" in p])

    def test_empty_audio_is_rejected(self):
        class Empty(FakeTTS):
            def synth(self, text, voice, rate, path):
                open(path, "wb").close()
        self.assertEqual(self.run_mv(Empty(), langs=["en"], retries=1), 1)

    def test_tiny_output_is_retried(self):
        tts = FakeTTS(stub={"Ahoj!": 2})
        self.assertEqual(self.run_mv(tts, langs=["cs"]), 0)
        self.assertEqual(sum(1 for c in tts.calls if c[0] == "Ahoj!"), 3)
        self.assertGreater(os.path.getsize(os.path.join(self.root, "voice", "cs", "ui.say.greeting.mp3")), 4000)

    def test_persistent_tiny_output_is_deleted_and_dropped(self):
        self.run_mv(FakeTTS())                               # a good recording exists first
        self.write({"cs": {"ui.say.greeting": "Ahoj, kamarádko!", "sp.liska.name": "Liška obecná."}, "en": {"ui.say.greeting": "Hello!"}})
        tts = FakeTTS(stub={"Ahoj, kamarádko!": 99})
        self.assertEqual(self.run_mv(tts, langs=["cs"], retries=3), 1)
        self.assertEqual(sum(1 for c in tts.calls if c[0] == "Ahoj, kamarádko!"), 3)
        self.assertNotIn("ui.say.greeting", self.index()["cs"])
        self.assertFalse(os.path.exists(os.path.join(self.root, "voice", "cs", "ui.say.greeting.mp3")))
        self.assertIn("chyb 1", self.out.getvalue())

    def test_cached_tiny_file_is_regenerated(self):
        self.run_mv(FakeTTS())
        stub_path = os.path.join(self.root, "voice", "cs", "sp.liska.name.mp3")
        with open(stub_path, "wb") as f:                     # the CI cache kept a 2 kB stub with a matching hash
            f.write(STUB)
        tts = FakeTTS()
        self.assertEqual(self.run_mv(tts), 0)
        self.assertEqual([c[0] for c in tts.calls], ["Liška obecná."])
        self.assertGreater(os.path.getsize(stub_path), 4000)
        out = self.out.getvalue()
        self.assertIn("podezřelé (podezřele krátká nahrávka", out)
        self.assertIn("podezřelé 1 (opraveno 1)", out)

    def test_min_bytes_scales_with_text(self):
        self.assertEqual(mv.min_bytes("Ahoj!"), 4000)
        self.assertEqual(mv.min_bytes("x" * 100), 20000)

    def test_missing_phrases(self):
        os.remove(os.path.join(self.root, "voice", "phrases.json"))
        self.assertEqual(self.run_mv(FakeTTS()), 2)

    def test_force(self):
        self.run_mv(FakeTTS())
        tts = FakeTTS()
        self.run_mv(tts, force=True)
        self.assertEqual(len(tts.calls), 3)


EL_CFG = {"cs": {"provider": "elevenlabs", "voice_name": "Candy - Young and Sweet", "model_id": "eleven_multilingual_v2",
                 "language_code": "cs", "voice_settings": {"stability": 0.45, "similarity_boost": 0.8, "style": 0.35, "use_speaker_boost": True}},
          "en": {"provider": "edge", "voice": "en-GB-MaisieNeural", "rate": "-8%"}}


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


class TestElevenLabs(unittest.TestCase):
    PHRASES = {"cs": {"ui.say.greeting": "Ahoj!", "sp.liska.name": "Liška obecná.", "ui.vyprava.wait": "Počkej, něco tu je!"},
               "en": {"ui.say.greeting": "Hello!"}}

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="houbicky-el-")
        self.vdir = os.path.join(self.root, "voice")
        os.makedirs(self.vdir)
        self.dump("phrases.json", self.PHRASES)
        self.out = io.StringIO()
        self.sleep = mock.patch("time.sleep", lambda s: None)
        self.sleep.start()
        # the current state: Czech recorded by edge-tts (Vlasta), English by Maisie
        mv.run(self.root, FakeTTS(), pause=0, out=io.StringIO())
        self.vlasta = self.read_mp3("cs", "sp.liska.name")

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

    def run_el(self, api, tts=None, **kw):
        return mv.run(self.root, tts or FakeTTS(), pause=0, out=self.out, eleven=api, **kw)

    def test_no_config_keeps_edge_and_records_nothing(self):
        tts = FakeTTS()
        self.assertEqual(mv.run(self.root, tts, pause=0, out=self.out), 0)
        self.assertEqual(tts.calls, [])

    def test_success_switches_whole_language_atomically(self):
        self.dump("config.json", EL_CFG)
        api = FakeEleven(); tts = FakeTTS()
        self.assertEqual(self.run_el(api, tts), 0)
        self.assertEqual(len(api.calls), 3)                                   # every Czech line, Candy's voice id
        self.assertTrue(all(c[0] == "v-candy" for c in api.calls))
        body = api.calls[0][1]
        self.assertEqual((body["model_id"], body["language_code"], body["voice_settings"]["stability"]), ("eleven_multilingual_v2", "cs", 0.45))
        idx = self.index()
        self.assertTrue(all(e["provider"] == "elevenlabs" and e["voice"] == "Candy - Young and Sweet" for e in idx["cs"].values()))
        self.assertEqual(idx["en"]["ui.say.greeting"]["provider"], "edge")  # English (Maisie) untouched
        self.assertEqual(tts.calls, [])
        self.assertFalse(os.path.exists(os.path.join(self.vdir, ".staging-cs")))
        self.assertIn("hlas přepnut — 3 vět", self.out.getvalue())
        # second run: nothing to do, no API calls at all
        api2 = FakeEleven()
        self.assertEqual(self.run_el(api2), 0)
        self.assertEqual(api2.calls, [])

    def test_partial_failure_keeps_the_old_voice(self):
        self.dump("config.json", EL_CFG)
        before = self.index()
        api = FakeEleven(fail_on={"Počkej, něco tu je!"})
        self.assertEqual(self.run_el(api, retries=2), 1)
        self.assertEqual(self.index()["cs"], before["cs"])                  # index untouched: still Vlasta everywhere
        self.assertEqual(self.read_mp3("cs", "sp.liska.name"), self.vlasta)   # files untouched
        self.assertFalse(os.path.exists(os.path.join(self.vdir, ".staging-cs")))
        self.assertIn("PŘEPNUTÍ HLASU ZRUŠENO", self.out.getvalue())

    def test_tiny_output_counts_as_failure_and_blocks_the_switch(self):
        self.dump("config.json", EL_CFG)
        before = self.index()
        api = FakeEleven(tiny_on={"Ahoj!"})
        self.assertEqual(self.run_el(api, retries=2), 1)
        self.assertEqual(self.index()["cs"], before["cs"])

    def test_quota_guard_refuses_before_spending(self):
        self.dump("config.json", EL_CFG)
        need = sum(len(t) for t in self.PHRASES["cs"].values())
        api = FakeEleven(used=30000 - need + 1, limit=30000)
        self.assertEqual(self.run_el(api), 1)
        self.assertEqual(api.calls, [])
        self.assertIn(f"potřeba {need} znaků, ale v ElevenLabs zbývá jen {need - 1}", self.out.getvalue())
        self.assertEqual(self.index()["cs"]["sp.liska.name"]["provider"], "edge")

    def test_quota_exactly_enough_records(self):
        self.dump("config.json", EL_CFG)
        need = sum(len(t) for t in self.PHRASES["cs"].values())
        self.assertEqual(self.run_el(FakeEleven(used=30000 - need, limit=30000)), 0)

    def test_key_without_user_read_still_records(self):
        self.dump("config.json", EL_CFG)
        class NoUserRead(FakeEleven):
            def subscription(self): raise mv.PermissionMissing("missing_permissions user_read")
        api = NoUserRead()
        self.assertEqual(self.run_el(api), 0)
        self.assertEqual(len(api.calls), 3)
        self.assertIn("stav kreditů nelze ověřit", self.out.getvalue())

    def test_voice_not_in_my_voices(self):
        self.dump("config.json", EL_CFG)
        api = FakeEleven(voices=[{"voice_id": "x", "name": "Somebody"}])
        self.assertEqual(self.run_el(api), 1)
        self.assertEqual(api.calls, [])
        self.assertIn("není v „My voices“", self.out.getvalue())

    def test_bad_key_or_plan_is_reported_cleanly(self):
        self.dump("config.json", EL_CFG)
        class NoPlan(FakeEleven):
            def tts(self, voice_id, body):
                raise mv.QuotaError("ElevenLabs: došly kredity nebo je potřeba placený plán (402)")
        api = NoPlan()
        self.assertEqual(self.run_el(api, retries=3), 1)
        self.assertIn("placený plán", self.out.getvalue())
        self.assertEqual(self.read_mp3("cs", "sp.liska.name"), self.vlasta)

    def test_language_code_rejected_is_retried_without_it(self):
        self.dump("config.json", EL_CFG)
        api = FakeEleven(reject_language=True)
        self.assertEqual(self.run_el(api), 0)
        self.assertTrue(all("language_code" not in c[1] for c in api.calls[1:]))

    def test_committed_recordings_need_no_service(self):
        """A deploy with recordings committed in git makes no network call at all, even without an API key."""
        self.dump("config.json", EL_CFG)
        self.run_el(FakeEleven())                       # recorded + committed (Candy for cs, Maisie for en)
        class NoNetwork(FakeEleven):
            def voices(self): raise AssertionError("network")
            def subscription(self): raise AssertionError("network")
            def tts(self, voice_id, body): raise AssertionError("network")
        class NoEdge(FakeTTS):
            def synth(self, *a): raise AssertionError("network")
        with mock.patch.dict(os.environ, {"ELEVENLABS_API_KEY": ""}):
            self.assertEqual(mv.run(self.root, NoEdge(), pause=0, out=self.out, eleven=None), 0)
            self.assertEqual(mv.run(self.root, NoEdge(), pause=0, out=self.out, eleven=NoNetwork()), 0)

    def test_hash_changes_with_voice_model_or_settings(self):
        base = EL_CFG["cs"]
        h = mv.line_hash("Ahoj!", base)
        for change in ({"voice_name": "Other"}, {"model_id": "eleven_v3"}, {"voice_settings": {**base["voice_settings"], "style": 0.5}}, {"provider": "edge", "voice": "x"}):
            self.assertNotEqual(h, mv.line_hash("Ahoj!", {**base, **change}), change)
        self.assertEqual(h, mv.line_hash("Ahoj!", dict(base)))
        # edge keeps the legacy hash, so existing Vlasta/Maisie recordings stay valid
        self.assertEqual(mv.line_hash("Ahoj!", {"provider": "edge", "voice": "cs-CZ-VlastaNeural", "rate": "-8%"}),
                         mv.text_hash("Ahoj!", "cs-CZ-VlastaNeural", "-8%"))

    def test_config_change_rerecords_that_language(self):
        self.dump("config.json", EL_CFG)
        self.run_el(FakeEleven())
        cfg = json.loads(json.dumps(EL_CFG)); cfg["cs"]["voice_settings"]["style"] = 0.6
        self.dump("config.json", cfg)
        api = FakeEleven()
        self.assertEqual(self.run_el(api), 0)
        self.assertEqual(len(api.calls), 3)

    def test_rate_limit_backs_off_and_retries(self):
        self.dump("config.json", EL_CFG)
        class Busy(FakeEleven):
            n = 0
            def tts(self, voice_id, body):
                Busy.n += 1
                if Busy.n == 1:
                    raise mv.RateLimited(7.0)
                return super().tts(voice_id, body)
        waits = []
        with mock.patch("time.sleep", lambda s: waits.append(s)):
            self.assertEqual(self.run_el(Busy()), 0)
        self.assertIn(7.0, waits)

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
        with self.assertRaises(mv.FatalTTSError):
            mv.ElevenLabsAPI(key="").voices() if not os.environ.get("ELEVENLABS_API_KEY") else (_ for _ in ()).throw(mv.FatalTTSError("x"))


if __name__ == "__main__":
    unittest.main()
