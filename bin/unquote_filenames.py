#!/usr/bin/env python3
import os
from urllib.parse import unquote

def unquote_filenames_recursively(root_dir):
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for fname in filenames:
            unquoted = unquote(fname)
            if fname != unquoted:
                src = os.path.join(dirpath, fname)
                dst = os.path.join(dirpath, unquoted)
                # Si le fichier cible existe déjà, ne pas écraser
                if os.path.exists(dst):
                    print(f"[SKIP] {dst} existe déjà, {src} non renommé.")
                else:
                    print(f"[RENAME] {src} -> {dst}")
                    os.rename(src, dst)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python unquote_filenames.py <dossier racine>")
        exit(1)
    unquote_filenames_recursively(sys.argv[1])
