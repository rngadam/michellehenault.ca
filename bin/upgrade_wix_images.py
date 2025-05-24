#!/usr/bin/env python3
import os
import re
import requests

WIX_STATIC_URL = "https://static.wixstatic.com/media/"
HEX_IMG_PATTERN = re.compile(r"^[0-9a-f]{6}_[0-9a-f]{32}~mv2.*\.(jpg|jpeg|png|gif)$", re.IGNORECASE)

# Taille seuil en octets (10 Ko)
SIZE_THRESHOLD = 10 * 1024

def try_fetch_highres_img(img_path):
    fname = os.path.basename(img_path)
    url = WIX_STATIC_URL + fname
    try:
        resp = requests.get(url, timeout=10)
        if resp.ok and len(resp.content) > SIZE_THRESHOLD:
            print(f"[UPGRADE] {fname}: {os.path.getsize(img_path)} -> {len(resp.content)} octets (remplacement)")
            with open(img_path, "wb") as f:
                f.write(resp.content)
            return True
        else:
            print(f"[NO UPGRADE] {fname}: rien de mieux trouvé ({len(resp.content)} octets)")
    except Exception as e:
        print(f"[ERROR] {fname}: {e}")
    return False

def process_dir(root):
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            if HEX_IMG_PATTERN.match(fname):
                fpath = os.path.join(dirpath, fname)
                if os.path.getsize(fpath) < SIZE_THRESHOLD:
                    try_fetch_highres_img(fpath)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python upgrade_wix_images.py <dossier racine>")
        exit(1)
    process_dir(sys.argv[1])
