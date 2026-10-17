#!/usr/bin/env python3
"""Mořský svět — download the real animal photos from Wikimedia Commons (stdlib only).

Run once on a computer with internet access:

    python3 fetch_photos.py                # download what is missing
    python3 fetch_photos.py --force        # re-download everything
    python3 fetch_photos.py --only liska,bedla
    python3 fetch_photos.py --contact you@example.com   # contact in the User-Agent (Wikimedia asks for one)

Input:  photos/manifest.json  ({"photos": [{"id", "commonsFile", "alt"?, "verified"?, ...}]})
        data/species.json     (only for the last-resort fallback: Latin name -> English Wikipedia image)
Output: photos/<id>.jpg       (Commons thumbnail, 1000 px wide)
        photos/credits.json   ({id: {author, license, licenseUrl, sourcePage, ...}}) — from Commons extmetadata

Order of attempts per species: commonsFile -> alt (string or list) -> pageimage of the
English Wikipedia article for the species' Latin name (free-licence images only).
"""
from __future__ import annotations

import argparse
import html
import http.client
import html.parser
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
ENWIKI_API = "https://en.wikipedia.org/w/api.php"
DEFAULT_WIDTH = 1000
VERSION = "1.0"


def user_agent(contact: str | None = None) -> str:
    # https://meta.wikimedia.org/wiki/User-Agent_policy
    ua = f"MorskySvetFetchPhotos/{VERSION} (private offline children's game; one-off download"
    if contact:
        ua += f"; {contact}"
    return ua + f") Python-urllib/{sys.version_info.major}.{sys.version_info.minor}"


class FetchError(Exception):
    pass


def _retry_after(err, default: float) -> float:
    """Seconds from a Retry-After header; HTTP-date or garbage -> the default back-off."""
    value = err.headers.get("Retry-After") if getattr(err, "headers", None) else None
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        return default


class Fetcher:
    """The only place that touches the network. Tests replace it with a fake."""

    def __init__(self, contact: str | None = None, timeout: float = 30.0, retries: int = 3):
        self.ua = user_agent(contact)
        self.timeout = timeout
        self.retries = retries

    def _open(self, url: str) -> bytes:
        req = urllib.request.Request(url, headers={"User-Agent": self.ua, "Accept-Encoding": "identity"})
        delay = 2.0
        for attempt in range(1, self.retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    return resp.read()
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503, 504) and attempt < self.retries:
                    time.sleep(min(_retry_after(e, delay), 30.0))
                    delay *= 2
                    continue
                raise FetchError(f"HTTP {e.code} for {url}") from e
            except urllib.error.URLError as e:
                reason = str(getattr(e, "reason", e))
                if "CERTIFICATE_VERIFY_FAILED" in reason:
                    raise FetchError(
                        "SSL certificate check failed. On macOS with python.org Python run "
                        "'/Applications/Python 3.x/Install Certificates.command' once, or use /usr/bin/python3."
                    ) from e
                if attempt < self.retries:
                    time.sleep(delay)
                    delay *= 2
                    continue
                raise FetchError(f"network error for {url}: {reason}") from e
            except (OSError, http.client.HTTPException) as e:
                # TimeoutError, ConnectionResetError, IncompleteRead, RemoteDisconnected … — transient: retry
                if attempt < self.retries:
                    time.sleep(delay)
                    delay *= 2
                    continue
                raise FetchError(f"network error for {url}: {e.__class__.__name__}: {e}") from e
        raise FetchError(f"giving up on {url}")

    def get_json(self, url: str) -> dict:
        try:
            return json.loads(self._open(url).decode("utf-8"))
        except ValueError as e:
            raise FetchError(f"invalid JSON from {url}") from e

    def get_bytes(self, url: str) -> bytes:
        return self._open(url)


# ---------------------------------------------------------------- helpers

class _Stripper(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data):
        self.parts.append(data)


def strip_html(value) -> str:
    if value is None:
        return ""
    s = _Stripper()
    s.feed(str(value))
    s.close()
    text = html.unescape("".join(s.parts))
    return re.sub(r"\s+", " ", text).strip()


def normalize_file_title(name: str) -> str:
    """'Foo bar.jpg', 'File:Foo_bar.jpg', 'https://commons.wikimedia.org/wiki/File:Foo_bar.jpg' -> 'File:Foo bar.jpg'"""
    name = (name or "").strip()
    if "/wiki/" in name:
        name = name.split("/wiki/", 1)[1]
    name = urllib.parse.unquote(name.split("?", 1)[0].split("#", 1)[0])
    name = name.replace("_", " ").strip()
    if re.match(r"(?i)^(file|image|soubor):", name):
        name = name.split(":", 1)[1].strip()
    return "File:" + name if name else ""


def commons_url(title: str, width: int) -> str:
    params = {
        "action": "query", "format": "json", "formatversion": "2", "redirects": "1",
        "prop": "imageinfo", "iiprop": "url|extmetadata", "iiurlwidth": str(width),
        "titles": title,
    }
    return COMMONS_API + "?" + urllib.parse.urlencode(params)


def wikipedia_url(latin: str) -> str:
    params = {
        "action": "query", "format": "json", "formatversion": "2", "redirects": "1",
        "prop": "pageimages", "piprop": "name|original", "pilicense": "free",
        "titles": latin,
    }
    return ENWIKI_API + "?" + urllib.parse.urlencode(params)


def image_kind(data: bytes) -> str | None:
    if data[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def commons_info(fetcher, title: str, width: int) -> dict:
    data = fetcher.get_json(commons_url(title, width))
    if "error" in data:
        raise FetchError(f"Commons API error: {data['error'].get('info', data['error'])}")
    pages = (data.get("query") or {}).get("pages") or []
    if not pages:
        raise FetchError(f"no page for {title}")
    page = pages[0]
    if page.get("missing") or page.get("invalid") or not page.get("imageinfo"):
        raise FetchError(f"{title} not found on Commons")
    ii = page["imageinfo"][0]
    meta = ii.get("extmetadata") or {}

    def m(key):
        return strip_html((meta.get(key) or {}).get("value"))

    license_name = m("LicenseShortName") or m("UsageTerms") or m("License")
    author = m("Artist") or m("Credit")
    return {
        "title": page.get("title", title),
        "thumbUrl": ii.get("thumburl") or ii.get("url"),
        "width": ii.get("thumbwidth") or ii.get("width"),
        "height": ii.get("thumbheight") or ii.get("height"),
        "author": author,
        "license": license_name,
        "licenseUrl": m("LicenseUrl"),
        "sourcePage": ii.get("descriptionurl") or "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(page.get("title", title).replace(" ", "_")),
        "attributionRequired": m("AttributionRequired").lower() != "false",
        "credit": m("Credit"),
    }


def wikipedia_file(fetcher, latin: str) -> str:
    data = fetcher.get_json(wikipedia_url(latin))
    pages = (data.get("query") or {}).get("pages") or []
    for page in pages:
        if page.get("pageimage"):
            return normalize_file_title(page["pageimage"])
    raise FetchError(f"no free page image on en.wikipedia for '{latin}'")


def load_json(path: str, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def write_json_atomic(path: str, obj) -> None:
    tmp = path + ".part"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)


def candidates(entry: dict, latin: str | None) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if entry.get("commonsFile"):
        out.append(("commonsFile", entry["commonsFile"]))
    alt = entry.get("alt")
    for a in ([alt] if isinstance(alt, str) else (alt or [])):
        if a:
            out.append(("alt", a))
    if latin:
        out.append(("wikipedia", latin))
    return out


# ---------------------------------------------------------------- main logic

def fetch_one(fetcher, entry: dict, latin: str | None, dest: str, width: int, need_image: bool, delay: float) -> dict:
    errors = []
    for via, value in candidates(entry, latin):
        try:
            title = wikipedia_file(fetcher, value) if via == "wikipedia" else normalize_file_title(value)
            if not title:
                raise FetchError("empty file name")
            info = commons_info(fetcher, title, width)
            if need_image:
                if not info["thumbUrl"]:
                    raise FetchError(f"no image URL for {title}")
                if delay:
                    time.sleep(delay)
                data = fetcher.get_bytes(info["thumbUrl"])
                kind = image_kind(data)
                if not kind:
                    raise FetchError(f"{title}: download is not an image")
                tmp = dest + ".part"
                with open(tmp, "wb") as f:
                    f.write(data)
                os.replace(tmp, dest)
                info["format"] = kind
                info["bytes"] = len(data)
            info["via"] = via
            info["errors"] = errors
            return info
        except FetchError as e:
            errors.append(f"{via}: {e}")
        if delay:
            time.sleep(delay)
    raise FetchError("; ".join(errors) or "no candidates (no commonsFile, alt or Latin name)")


def run(root: str = HERE, fetcher=None, force: bool = False, only: set[str] | None = None,
        width: int = DEFAULT_WIDTH, delay: float = 0.5, out=sys.stdout) -> int:
    fetcher = fetcher or Fetcher()
    photos_dir = os.path.join(root, "photos")
    manifest = load_json(os.path.join(photos_dir, "manifest.json"))
    if not manifest or not isinstance(manifest.get("photos"), list):
        print("Chybí nebo je neplatný photos/manifest.json — nic ke stažení.", file=out)
        return 2
    species = load_json(os.path.join(root, "data", "species.json"), {}) or {}
    sp_list = species if isinstance(species, list) else species.get("species", [])  # data/species.json: bare array (BRIEF §6) or {"species": [...]}
    latin_by_id = {s.get("id"): s.get("latin") for s in sp_list if isinstance(s, dict) and s.get("id")}

    credits_path = os.path.join(photos_dir, "credits.json")
    credits = load_json(credits_path, {}) or {}
    rows = []
    entries = [e for e in manifest["photos"] if not only or e.get("id") in only]
    total = len(entries)
    print(f"Stahuji fotky z Wikimedia Commons ({total} druhů)…", file=out, flush=True)
    for i, entry in enumerate(entries, 1):
        pid = entry.get("id")
        prefix = f"[{i}/{total}] {pid} …"
        if not pid or not re.fullmatch(r"[a-z0-9-]+", str(pid)):
            rows.append((str(pid), "FAILED", "", "invalid id"))
            print(f"{prefix} CHYBA: neplatné id", file=out, flush=True)
            continue
        dest = os.path.join(photos_dir, f"{pid}.jpg")
        need_image = force or not os.path.exists(dest)
        need_meta = force or pid not in credits
        if not need_image and not need_meta:
            rows.append((pid, "skipped", credits[pid].get("via", ""), "already downloaded"))
            print(f"{prefix} přeskočeno (už staženo)", file=out, flush=True)
            continue
        print(f"{prefix} stahuji … ", end="", file=out, flush=True)
        try:
            info = fetch_one(fetcher, entry, latin_by_id.get(pid), dest, width, need_image, delay)
        except FetchError as e:
            rows.append((pid, "FAILED", "", str(e)))
            print("CHYBA (podrobnosti v přehledu na konci)", file=out, flush=True)
            continue
        if need_image:
            print(f"hotovo {round((info.get('bytes') or 0) / 1024)} kB" + ("" if info["via"] == "commonsFile" else f" (náhradní zdroj: {info['via']})"), file=out, flush=True)
        else:
            print("hotovo (jen údaje o licenci)", file=out, flush=True)
        credits[pid] = {
            "author": info["author"],
            "license": info["license"],
            "licenseUrl": info["licenseUrl"],
            "sourcePage": info["sourcePage"],
            "file": info["title"],
            "via": info["via"],
            "verified": entry.get("verified", None) if info["via"] == "commonsFile" else False,
            "width": info["width"],
            "height": info["height"],
        }
        notes = []
        if info["via"] != "commonsFile":
            notes.append(f"fallback ({info['via']}): {info['title']}")
        if entry.get("verified") is False:
            notes.append("manifest says verified=false — check the photo")
        if info.get("format") and info["format"] != "jpeg":
            notes.append(f"image is {info['format']}, saved as .jpg")
        if entry.get("license") and info["license"] and entry["license"].lower() != info["license"].lower():
            notes.append(f"licence differs from manifest ({entry['license']} vs {info['license']})")
        rows.append((pid, "downloaded" if need_image else "metadata", info["via"], "; ".join(notes) or info["license"]))
        write_json_atomic(credits_path, credits)  # save progress after each photo
        if delay:
            time.sleep(delay)

    width_id = max([len(r[0]) for r in rows] + [2])
    print("\nFotky z Wikimedia Commons:", file=out)
    for pid, status, via, note in rows:
        print(f"  {pid:<{width_id}}  {status:<10}  {via:<11}  {note}", file=out)
    n = {s: sum(1 for r in rows if r[1] == s) for s in ("downloaded", "metadata", "skipped", "FAILED")}
    print(f"\nStaženo {n['downloaded']}, jen metadata {n['metadata']}, přeskočeno {n['skipped']}, chyb {n['FAILED']}.", file=out)
    if n["FAILED"]:
        print("Chybějící fotky doplní výzkumník do photos/manifest.json (pole commonsFile/alt); pak skript spusťte znovu.", file=out)
    return 1 if n["FAILED"] else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Download Mořský svět photos from Wikimedia Commons")
    ap.add_argument("--force", action="store_true", help="re-download even if the photo exists")
    ap.add_argument("--only", help="comma-separated species ids")
    ap.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    ap.add_argument("--delay", type=float, default=0.5, help="pause between requests (s)")
    ap.add_argument("--contact", default=os.environ.get("MORSKY_SVET_CONTACT"),
                    help="e-mail or URL put in the User-Agent (Wikimedia policy)")
    args = ap.parse_args(argv)
    only = {s.strip() for s in args.only.split(",")} if args.only else None
    return run(HERE, Fetcher(contact=args.contact), force=args.force, only=only,
               width=args.width, delay=args.delay)


if __name__ == "__main__":
    sys.exit(main())
