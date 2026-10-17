#!/usr/bin/env python3
"""Headless-Chrome screenshot helper for comps and sheets (designer sight loop).
Usage: python3 design/shoot.py page.html out.png [width height scale]"""
import os
import subprocess
import sys

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def shoot(html, png, w=1024, h=768, scale=2):
    html = os.path.abspath(html)
    png = os.path.abspath(png)
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
           f"--window-size={w},{h}", f"--force-device-scale-factor={scale}", "--virtual-time-budget=3000",
           "--default-background-color=00000000", f"--screenshot={png}", "file://" + html]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
    return png


if __name__ == "__main__":
    a = sys.argv[1:]
    shoot(a[0], a[1], *(int(x) for x in a[2:5]))
