#!/usr/bin/env python3
import os
import re
import sys
import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

WIX_URL = "https://michellehenault.wixsite.com/michellehenault/"
TARGET_URL = "https://michellehenault.ca/michellehenault/"
IMG_EXTS = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg")

def download_image(url, dest, dry_run=False, debug=False):
    if debug:
        print(f"[DEBUG] Vérification de l'existence de l'image : {dest}")
    if os.path.exists(dest):
        if debug or dry_run:
            print(f"Image déjà présente : {dest}")
        return
    if dry_run:
        print(f"[DRY-RUN] Télécharger {url} dans {dest}")
        return
    if debug:
        print(f"Télécharger {url} dans {dest}")
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        with open(dest, "wb") as f:
            f.write(r.content)
        if debug:
            print(f"[DEBUG] Image téléchargée : {dest}")
    except Exception as e:
        print(f"Erreur téléchargement {url}: {e}")

def process_html_file(filepath, outdir, dry_run=False, debug=False):
    if debug:
        print(f"[DEBUG] Traitement du fichier : {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        raw_html = f.read()
    # Suppression des balises <!--$--> et <!--/$-->, et de tous les commentaires
    raw_html = re.sub(r'<!--\$-->|<!--/\$-->|<!--.*?-->', '', raw_html, flags=re.DOTALL)
    # Suppression des balises <style> et de leur contenu
    raw_html = re.sub(r'<style.*?>.*?</style>', '', raw_html, flags=re.DOTALL|re.IGNORECASE)
    raw_html = re.sub(r'<script.*?>.*?</script>', '', raw_html, flags=re.DOTALL|re.IGNORECASE)
    # Suppression de balises inutiles ou Wix avant traitement
    raw_html = re.sub(r'<meta[^>]+id="wixDesktopViewport"[^>]*>', '', raw_html, flags=re.IGNORECASE)
    raw_html = re.sub(r'<meta[^>]+http-equiv="X-UA-Compatible"[^>]*>', '', raw_html, flags=re.IGNORECASE)
    raw_html = re.sub(r'<meta[^>]+content="Wix\.com Website Builder"[^>]*name="generator"[^>]*>', '', raw_html, flags=re.IGNORECASE)
    raw_html = re.sub(r'<link[^>]+href="https://www\\.wix\\.com/favicon\\.ico"[^>]*>', '', raw_html, flags=re.IGNORECASE)
    raw_html = re.sub(r'<meta[^>]+http-equiv="X-Wix-Meta-Site-Id"[^>]*>', '', raw_html, flags=re.IGNORECASE)
    raw_html = re.sub(r'<meta[^>]+http-equiv="X-Wix-Application-Instance-Id"[^>]*>', '', raw_html, flags=re.IGNORECASE)
    raw_html = re.sub(r'<meta[^>]+http-equiv="X-Wix-Published-Version"[^>]*>', '', raw_html, flags=re.IGNORECASE)

    soup = BeautifulSoup(raw_html, "html.parser")
    if debug:
        print(f"[DEBUG] Extraction du <head> et des balises meta/title...")
    # HEAD: copy <title>, <meta name|property|...>, remove generator/http-equiv, substitute URLs, download images
    head = soup.head
    new_head = BeautifulSoup("<head></head>", "html.parser").head
    for tag in head.find_all(["title", "meta"]):
        if debug:
            indent = '  '
            print(f"[DEBUG] Analyse de la balise : {tag.name}")
        if tag.name == "meta":
            if tag.get("name") == "generator" or tag.get("http-equiv"):
                if debug:
                    print(f"[DEBUG] Ignoré (generator/http-equiv) : {tag.name}")
                continue
            # Substitution d''URL
            if tag.get("content"):
                content = tag["content"].replace(WIX_URL, TARGET_URL)
                if debug and content != tag["content"]:
                    print(f"[DEBUG] Substitution d'URL dans meta : {tag['content']} -> {content}")
                # Si c'est une image, download
                if re.match(r"https?://.*\.(jpg|jpeg|png|gif|webp|svg)$", content, re.I):
                    img_name = os.path.basename(urlparse(content).path)
                    img_dest = os.path.join(outdir, img_name)
                    download_image(content, img_dest, dry_run, debug)
                    tag["content"] = img_name
                else:
                    tag["content"] = content
        new_head.append(tag)
    if debug:
        print(f"[DEBUG] Construction du <head> terminé.")

    # BODY: on garde toute la structure, mais on ne conserve que les balises qui contiennent ou sont parents de wixui-rich-text__text ou img
    def filter_tag(tag):
        if getattr(tag, 'attrs', None) and 'class' in tag.attrs and 'wixui-rich-text__text' in tag['class']:
            return True
        if getattr(tag, 'name', None) == 'img':
            return True
        if any(child for child in tag.descendants if getattr(child, 'attrs', None) and 'class' in child.attrs and 'wixui-rich-text__text' in child['class']):
            return True
        if any(getattr(child, 'name', None) == 'img' for child in tag.descendants):
            return True
        return False
    body = soup.body
    if debug:
        print(f"[DEBUG] Prune du <body> pour ne garder que les branches pertinentes...")
    def prune(tag, depth=0):
        if not hasattr(tag, 'children'):
            return None
        if filter_tag(tag):
            if debug:
                print(f"[DEBUG] {'  '*depth}{tag.name}")
            new_tag = tag.__copy__() if hasattr(tag, '__copy__') else BeautifulSoup(str(tag), "html.parser").find()
            new_tag.clear()
            # Préserver le texte direct du tag si présent
            if tag.string and tag.string.strip():
                new_tag.append(tag.string)
            for child in tag.children:
                if hasattr(child, 'name'):
                    pruned = prune(child, depth+1)
                    if pruned:
                        new_tag.append(pruned)
                elif isinstance(child, str):
                    # Préserver le texte non balisé
                    if child.strip():
                        new_tag.append(child)
            return new_tag
        return None
    pruned_body = prune(body)
    if not pruned_body:
        pruned_body = BeautifulSoup("<body></body>", "html.parser").body

    # Suppression de tous les attributs sauf src et alt pour img, et preservation de 'string' si présent
    def clean_attrs(tag):
        if not hasattr(tag, 'attrs'):
            return
        if tag.name == 'img':
            src = tag.get('src')
            alt = tag.get('alt')
            string = tag.get('string')
            tag.attrs = {}
            if src:
                tag['src'] = src
            if alt is not None:
                tag['alt'] = alt
            if string is not None:
                tag['string'] = string
        else:
            # Préserver l'attribut 'string' si présent
            string = tag.get('string')
            tag.attrs = {}
            if string is not None:
                tag['string'] = string
        for child in tag.children:
            if hasattr(child, 'name'):
                clean_attrs(child)
    clean_attrs(pruned_body)

    # Déplacement des enfants hors des balises non-HTML5 standard
    HTML5_TAGS = set([
        'html', 'head', 'body', 'header', 'footer', 'main', 'section', 'article', 'nav', 'aside',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'a', 'img', 'ul', 'ol', 'li', 'div', 'span',
        'figure', 'figcaption', 'blockquote', 'pre', 'code', 'em', 'strong', 'table', 'thead', 'tbody', 'tr', 'td', 'th', 'br', 'hr'])
    def unwrap_non_html5(tag):
        # Ne traiter que les balises (pas les NavigableString)
        if not hasattr(tag, 'children'):
            return
        for child in list(tag.children):
            if hasattr(child, 'name'):
                unwrap_non_html5(child)
        if tag.name not in HTML5_TAGS and tag.name is not None:
            tag.unwrap()
    unwrap_non_html5(pruned_body)

    if debug:
        print(f"[DEBUG] Recherche et traitement des balises <img> dans le body...")
    # Images dans le body : download et remplacer src si besoin
    for img in pruned_body.find_all("img"):
        src = img.get("src")
        if src and re.match(r"https?://", src):
            img_name = os.path.basename(urlparse(src).path)
            img_dest = os.path.join(outdir, img_name)
            download_image(src, img_dest, dry_run, debug)
            img["src"] = img_name
    # Remplacement du bloc Instagram Social Icon par un lien réel vers Instagram avec icône (multilignes) après le traitement BeautifulSoup
    html_result = f"<!DOCTYPE html>\n<html lang=\"fr\">\n" + new_head.prettify() + pruned_body.prettify() + "\n</html>\n"
    html_result = re.sub(
        r'<ul>\s*<li>\s*<a>\s*<img alt="Instagram Social Icon"\s*/>\s*</a>\s*</li>\s*</ul>',
        '<a href="https://www.instagram.com/henault.michelle/?hl=en" target="_blank" rel="noopener noreferrer" style="display:inline-block;vertical-align:middle;"><img src="https://upload.wikimedia.org/wikipedia/commons/a/a5/Instagram_icon.png" alt="Instagram" style="width:32px;height:32px;border-radius:6px;vertical-align:middle;"/></a>',
        html_result, flags=re.DOTALL|re.MULTILINE)
    # Ajout des liens et icônes Facebook et LinkedIn à côté d'Instagram dans le header (après traitement BeautifulSoup)
    html_result = re.sub(
        r'(<a href="https://www.instagram.com/henault.michelle/\?hl=en"[^>]*><img [^>]+></a>)',
        r'\1<a href="https://www.facebook.com/michellehenaultartistepeintre" target="_blank" rel="noopener noreferrer" style="display:inline-block;vertical-align:middle;margin-right:8px;"><img src="https://upload.wikimedia.org/wikipedia/commons/5/51/Facebook_f_logo_%282019%29.svg" alt="Facebook" style="width:32px;height:32px;border-radius:6px;vertical-align:middle;background:#fff;"/></a><a href="https://www.linkedin.com/in/michelle-h%C3%A9nault" target="_blank" rel="noopener noreferrer" style="display:inline-block;vertical-align:middle;"><img src="https://upload.wikimedia.org/wikipedia/commons/c/ca/LinkedIn_logo_initials.png" alt="LinkedIn" style="width:32px;height:32px;border-radius:6px;vertical-align:middle;background:#fff;"/></a>',
        html_result, flags=re.DOTALL)
    # Écriture du fichier
    if not os.path.exists(outdir):
        if dry_run:
            print(f"[DRY-RUN] Créer le dossier : {outdir}")
        else:
            if debug:
                print(f"Créer le dossier : {outdir}")
            os.makedirs(outdir)
    outpath = os.path.join(outdir, "index.html")
    if dry_run:
        print(f"[DRY-RUN] Créer {outpath}")
    else:
        if debug:
            print(f"Créer {outpath}")
        with open(outpath, "w", encoding="utf-8") as f:
            f.write(html_result)
    return

def main():
    parser = argparse.ArgumentParser(description="Extraction HTML Michelle Henault")
    parser.add_argument("-d", "--directory", required=True, help="Répertoire à traiter")
    parser.add_argument("--dry-run", action="store_true", help="Simulation sans écriture")
    parser.add_argument("--debug", action="store_true", help="Affiche toutes les actions")
    args = parser.parse_args()

    for fname in os.listdir(args.directory):
        if fname.endswith(".html"):
            name = os.path.splitext(fname)[0]
            outdir = os.path.join(args.directory, name)
            process_html_file(os.path.join(args.directory, fname), outdir, args.dry_run, args.debug)

if __name__ == "__main__":
    main()
