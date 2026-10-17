"""Unit tests for fetch_photos.py — network replaced by a fake Fetcher fed from tests/fixtures/."""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
import urllib.parse
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import fetch_photos as fp  # noqa: E402

FIX = os.path.join(ROOT, "tests", "fixtures")
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def fixture(name):
    with open(os.path.join(FIX, name), encoding="utf-8") as f:
        return json.load(f)


class FakeFetcher:
    """Routes API URLs by their 'titles' parameter; records every call."""

    def __init__(self, commons=None, wikipedia=None, blobs=None):
        self.commons = commons or {}
        self.wikipedia = wikipedia or {}
        self.blobs = blobs or {}
        self.calls = []

    def get_json(self, url):
        self.calls.append(url)
        q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        title = q["titles"][0]
        if url.startswith(fp.COMMONS_API):
            return self.commons.get(title, fixture("commons_missing.json"))
        if url.startswith(fp.ENWIKI_API):
            return self.wikipedia.get(title, {"query": {"pages": [{"title": title, "missing": True}]}})
        raise AssertionError("unexpected URL " + url)

    def get_bytes(self, url):
        self.calls.append(url)
        return self.blobs.get(url, JPEG)


def make_fetcher():
    ok = fixture("commons_ok.json")
    return FakeFetcher(
        commons={
            "File:Boletus edulis EtgHollande 041031 091.jpg": ok,
            "File:Cantharellus cibarius.jpg": fixture("commons_ok_pd.json"),
            "File:Macrolepiota procera (Parasol mushroom).jpg": ok,
            "File:Leccinum scabrum.jpg": ok,
        },
        wikipedia={"Macrolepiota procera": fixture("wikipedia_pageimage.json")},
    )


class Base(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="houbicky-test-")
        os.makedirs(os.path.join(self.root, "photos"))
        os.makedirs(os.path.join(self.root, "data"))
        shutil.copy(os.path.join(FIX, "manifest.json"), os.path.join(self.root, "photos", "manifest.json"))
        shutil.copy(os.path.join(FIX, "species.json"), os.path.join(self.root, "data", "species.json"))
        self.out = io.StringIO()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def run_fetch(self, fetcher, **kw):
        return fp.run(self.root, fetcher, delay=0, out=self.out, **kw)

    def credits(self):
        with open(os.path.join(self.root, "photos", "credits.json"), encoding="utf-8") as f:
            return json.load(f)

    def photo(self, pid):
        return os.path.join(self.root, "photos", f"{pid}.jpg")


class TestHelpers(unittest.TestCase):
    def test_strip_html(self):
        self.assertEqual(fp.strip_html('<a href="x">Eric&nbsp;Steinert</a>\n'), "Eric Steinert")
        self.assertEqual(fp.strip_html("<bdi>Jan &amp; Petra</bdi>"), "Jan & Petra")
        self.assertEqual(fp.strip_html('<span lang="en">Own   work</span> <b>x</b>'), "Own work x")
        self.assertEqual(fp.strip_html(None), "")
        self.assertNotIn("<", fp.strip_html('<a href="x">Eric&nbsp;Steinert</a>'))

    def test_normalize_file_title(self):
        n = fp.normalize_file_title
        self.assertEqual(n("File:Foo_bar.jpg"), "File:Foo bar.jpg")
        self.assertEqual(n("Foo bar.jpg"), "File:Foo bar.jpg")
        self.assertEqual(n("Soubor:Foo.jpg"), "File:Foo.jpg")
        self.assertEqual(n("https://commons.wikimedia.org/wiki/File:Hřib_%C5%BElu%C4%8Dn%C3%ADk.jpg"), "File:Hřib žlučník.jpg")
        self.assertEqual(n(""), "")

    def test_commons_url_params(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(fp.commons_url("File:X.jpg", 1000)).query)
        self.assertEqual(q["action"], ["query"])
        self.assertEqual(q["prop"], ["imageinfo"])
        self.assertEqual(q["iiprop"], ["url|extmetadata"])
        self.assertEqual(q["iiurlwidth"], ["1000"])
        self.assertEqual(q["titles"], ["File:X.jpg"])

    def test_wikipedia_url_free_only(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(fp.wikipedia_url("Boletus edulis")).query)
        self.assertEqual(q["prop"], ["pageimages"])
        self.assertEqual(q["pilicense"], ["free"])

    def test_image_kind(self):
        self.assertEqual(fp.image_kind(JPEG), "jpeg")
        self.assertEqual(fp.image_kind(PNG), "png")
        self.assertIsNone(fp.image_kind(b"<!DOCTYPE html>"))

    def test_user_agent_sent(self):
        seen = {}

        class Resp(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def fake_urlopen(req, timeout=None):
            seen["ua"] = req.get_header("User-agent")
            return Resp(b'{"ok": 1}')

        with mock.patch("urllib.request.urlopen", fake_urlopen):
            self.assertEqual(fp.Fetcher(contact="someone@example.org").get_json("https://commons.wikimedia.org/w/api.php?x=1"), {"ok": 1})
        self.assertIn("MorskySvetFetchPhotos/", seen["ua"])
        self.assertIn("someone@example.org", seen["ua"])
        self.assertNotIn("contact", fp.user_agent(None).lower())


class TestRun(Base):
    def test_primary_alt_wikipedia_fallbacks(self):
        f = make_fetcher()
        rc = self.run_fetch(f)
        self.assertEqual(rc, 0, self.out.getvalue())
        c = self.credits()
        self.assertEqual(set(c), {"hrib-smrkovy", "liska", "bedla", "kozak"})
        # primary
        self.assertEqual(c["hrib-smrkovy"]["via"], "commonsFile")
        self.assertEqual(c["hrib-smrkovy"]["author"], "Eric Steinert")
        self.assertEqual(c["hrib-smrkovy"]["license"], "CC BY-SA 3.0")
        self.assertEqual(c["hrib-smrkovy"]["licenseUrl"], "https://creativecommons.org/licenses/by-sa/3.0")
        self.assertTrue(c["hrib-smrkovy"]["sourcePage"].startswith("https://commons.wikimedia.org/wiki/File:"))
        # alt (list, blank entry ignored, URL form accepted); licence from UsageTerms; HTML entities decoded
        self.assertEqual(c["liska"]["via"], "alt")
        self.assertEqual(c["liska"]["author"], "Jan & Petra Nováková")
        self.assertEqual(c["liska"]["license"], "Public domain")
        # wikipedia pageimage by Latin name
        self.assertEqual(c["bedla"]["via"], "wikipedia")
        requested = [urllib.parse.parse_qs(urllib.parse.urlparse(u).query)["titles"][0] for u in f.calls if u.startswith(fp.COMMONS_API)]
        self.assertIn("File:Macrolepiota procera (Parasol mushroom).jpg", requested)
        self.assertFalse(c["bedla"]["verified"])
        # no "File:" prefix in manifest still works; verified=false is surfaced
        self.assertEqual(c["kozak"]["via"], "commonsFile")
        self.assertIn("verified=false", self.out.getvalue())
        for pid in c:
            with open(self.photo(pid), "rb") as fh:
                self.assertEqual(fh.read(), JPEG)
        self.assertFalse([p for p in os.listdir(os.path.join(self.root, "photos")) if p.endswith(".part")])
        thumbs = [u for u in f.calls if "upload.wikimedia.org" in u]
        self.assertTrue(all("1000px" in u for u in thumbs), thumbs)

    def test_idempotent_second_run_makes_no_requests(self):
        self.run_fetch(make_fetcher())
        f2 = make_fetcher()
        rc = self.run_fetch(f2)
        self.assertEqual(rc, 0)
        self.assertEqual(f2.calls, [])
        self.assertIn("přeskočeno 4", self.out.getvalue())

    def test_force_redownloads(self):
        self.run_fetch(make_fetcher())
        f2 = make_fetcher()
        self.run_fetch(f2, force=True)
        self.assertEqual(sum(1 for u in f2.calls if "upload.wikimedia.org" in u), 4)

    def test_missing_image_with_credits_redownloads_only_that_one(self):
        self.run_fetch(make_fetcher())
        os.remove(self.photo("liska"))
        f2 = make_fetcher()
        self.run_fetch(f2)
        self.assertEqual([u for u in f2.calls if "upload.wikimedia.org" in u], ["https://upload.wikimedia.org/thumb/Cantharellus.jpg/1000px-Cantharellus.jpg"])

    def test_only_filter(self):
        f = make_fetcher()
        self.run_fetch(f, only={"liska"})
        self.assertEqual(set(self.credits()), {"liska"})

    def test_total_failure_reports_and_exit_code(self):
        f = FakeFetcher()  # every lookup missing
        rc = self.run_fetch(f, only={"bedla"})
        self.assertEqual(rc, 1)
        self.assertIn("FAILED", self.out.getvalue())
        self.assertFalse(os.path.exists(self.photo("bedla")))

    def test_non_image_download_rejected(self):
        f = make_fetcher()
        f.blobs["https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Boletus.jpg/1000px-Boletus.jpg"] = b"<html>error</html>"
        rc = self.run_fetch(f, only={"hrib-smrkovy"})
        self.assertEqual(rc, 1)
        self.assertFalse(os.path.exists(self.photo("hrib-smrkovy")))

    def test_png_saved_with_warning(self):
        f = make_fetcher()
        f.blobs["https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Boletus.jpg/1000px-Boletus.jpg"] = PNG
        self.assertEqual(self.run_fetch(f, only={"hrib-smrkovy"}), 0)
        self.assertIn("image is png", self.out.getvalue())

    def test_missing_manifest(self):
        os.remove(os.path.join(self.root, "photos", "manifest.json"))
        self.assertEqual(self.run_fetch(FakeFetcher()), 2)

    def test_missing_species_json_skips_wikipedia_fallback(self):
        os.remove(os.path.join(self.root, "data", "species.json"))
        f = make_fetcher()
        rc = self.run_fetch(f, only={"bedla"})
        self.assertEqual(rc, 1)
        self.assertFalse(any(u.startswith(fp.ENWIKI_API) for u in f.calls))

    def test_invalid_id_rejected(self):
        with open(os.path.join(self.root, "photos", "manifest.json"), "w") as fh:
            json.dump({"photos": [{"id": "../evil", "commonsFile": "File:X.jpg"}]}, fh)
        self.assertEqual(self.run_fetch(make_fetcher()), 1)
        self.assertFalse(os.path.exists(os.path.join(self.root, "evil.jpg")))


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class TestRetries(unittest.TestCase):
    def _run(self, failures, sleeps):
        calls = {"n": 0}

        def fake_urlopen(req, timeout=None):
            calls["n"] += 1
            if failures:
                raise failures.pop(0)
            return _Resp(b'{"ok": 1}')

        with mock.patch("urllib.request.urlopen", fake_urlopen), mock.patch("time.sleep", lambda t: sleeps.append(t)):
            return fp.Fetcher().get_json("https://commons.wikimedia.org/w/api.php?x=1"), calls["n"]

    def test_transient_errors_are_retried(self):
        import http.client
        for err in (TimeoutError("timed out"), ConnectionResetError("reset"), http.client.IncompleteRead(b"x", 10)):
            with self.subTest(err=type(err).__name__):
                sleeps = []
                data, n = self._run([err], sleeps)
                self.assertEqual(data, {"ok": 1})
                self.assertEqual(n, 2)

    def test_gives_up_after_retries_with_fetcherror(self):
        sleeps = []
        with self.assertRaises(fp.FetchError):
            self._run([TimeoutError("t")] * 3, sleeps)

    def test_non_numeric_retry_after_falls_back_to_delay(self):
        import urllib.error
        err = urllib.error.HTTPError("https://x", 503, "busy", {"Retry-After": "Wed, 21 Oct 2015 07:28:00 GMT"}, None)
        sleeps = []
        data, n = self._run([err], sleeps)
        self.assertEqual(data, {"ok": 1})
        self.assertEqual(sleeps, [2.0])

    def test_numeric_retry_after_is_honoured(self):
        import urllib.error
        err = urllib.error.HTTPError("https://x", 429, "slow down", {"Retry-After": "5"}, None)
        sleeps = []
        self._run([err], sleeps)
        self.assertEqual(sleeps, [5.0])


class TestProgress(Base):
    def test_progress_line_per_species(self):
        self.run_fetch(make_fetcher())
        out = self.out.getvalue()
        self.assertIn("[1/4] hrib-smrkovy … stahuji … hotovo 0 kB", out)
        self.assertIn("[4/4] kozak …", out)
        self.out = io.StringIO()
        self.run_fetch(make_fetcher())
        self.assertIn("[2/4] liska … přeskočeno (už staženo)", self.out.getvalue())


if __name__ == "__main__":
    unittest.main()


class TestBareArraySpecies(unittest.TestCase):
    """Mořský svět: data/species.json is a bare array (BRIEF §6), not {"species": [...]}."""

    def test_run_accepts_bare_array(self):
        import json, tempfile
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "photos")); os.makedirs(os.path.join(d, "data"))
            json.dump([{"id": "klaun", "latin": "Amphiprion ocellaris"}], open(os.path.join(d, "data", "species.json"), "w"))
            json.dump({"photos": []}, open(os.path.join(d, "photos", "manifest.json"), "w"))
            out = io.StringIO()
            fp.run(d, fp.Fetcher(), out=out)   # must not raise on the list shape
