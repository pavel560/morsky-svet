"""serve.py: MIME types, cache headers, no directory listing."""
import os
import sys
import threading
import unittest
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import serve  # noqa: E402


class TestServe(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = serve.make_server("127.0.0.1", 0, ROOT, quiet=True)
        cls.port = cls.httpd.server_address[1]
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def get(self, path):
        return urllib.request.urlopen(f"http://127.0.0.1:{self.port}{path}", timeout=5)

    def test_mime_and_cache(self):
        cases = {
            "/manifest.webmanifest": ("application/manifest+json", "no-cache"),
            "/sw.js": ("text/javascript", "no-cache"),
            "/js/speech.js": ("text/javascript", "no-cache"),
            "/index.html": ("text/html", "no-cache"),
            "/fonts/andika-latin-ext-400-normal.woff2": ("font/woff2", "max-age"),
            "/icons/icon-192.png": ("image/png", "max-age"),
        }
        for path, (ctype, cache) in cases.items():
            with self.subTest(path=path), self.get(path) as r:
                self.assertTrue(r.headers["Content-Type"].startswith(ctype), r.headers["Content-Type"])
                self.assertIn(cache, r.headers["Cache-Control"])

    def test_root_serves_index(self):
        with self.get("/") as r:
            self.assertIn("text/html", r.headers["Content-Type"])
            self.assertEqual(r.headers["Cache-Control"], "no-cache")

    def test_no_directory_listing(self):
        with self.assertRaises(urllib.error.HTTPError) as cm:
            self.get("/tests/")
        self.assertEqual(cm.exception.code, 404)

    def test_svg_mime(self):
        self.assertEqual(serve.Handler.extensions_map[".svg"], "image/svg+xml")
        self.assertTrue(serve.Handler.extensions_map[".mjs"].startswith("text/javascript"))

    def test_byte_range(self):
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}/manifest.webmanifest", headers={"Range": "bytes=2-11"})
        with urllib.request.urlopen(req, timeout=5) as r:
            body = r.read()
            self.assertEqual(r.status, 206)
            self.assertEqual(len(body), 10)
            self.assertTrue(r.headers["Content-Range"].startswith("bytes 2-11/"))
        with open(os.path.join(ROOT, "manifest.webmanifest"), "rb") as fh:
            self.assertEqual(body, fh.read()[2:12])
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}/manifest.webmanifest", headers={"Range": "bytes=99999-"})
        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(req, timeout=5)
        self.assertEqual(cm.exception.code, 416)

    def test_many_parallel_requests(self):
        """60 simultaneous requests all succeed (listen backlog ≫ 5)."""
        import concurrent.futures
        def one(_):
            with self.get("/js/app.js") as r:
                return r.status
        with concurrent.futures.ThreadPoolExecutor(max_workers=60) as ex:
            codes = list(ex.map(one, range(60)))
        self.assertEqual(codes, [200] * 60)
        self.assertGreaterEqual(self.httpd.request_queue_size, 64)

    def test_lan_addresses_is_list(self):
        self.assertIsInstance(serve.lan_addresses(), list)


if __name__ == "__main__":
    unittest.main()
