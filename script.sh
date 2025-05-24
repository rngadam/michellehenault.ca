#!/bin/bash

# Script d'extraction d'images et de texte depuis des fichiers HTML
# Usage : $0 -d <répertoire> [--dry-run]"

TARGET_DIR=""
DRY_RUN=0
DEBUG=0

# Gestion des paramètres avec getopts
while getopts ":d:-:" opt; do
  case $opt in
    d)
      TARGET_DIR="$OPTARG"
      ;;
    -)
      case $OPTARG in
        dry-run)
          DRY_RUN=1
          ;;
        debug)
          DEBUG=1
          ;;
        *)
          echo "Option inconnue --$OPTARG" >&2
          exit 1
          ;;
      esac
      ;;
    \?)
      echo "Option invalide : -$OPTARG" >&2
      exit 1
      ;;
    :)
      echo "L'option -$OPTARG requiert un argument." >&2
      exit 1
      ;;
  esac
done

if [[ -z "$TARGET_DIR" ]]; then
  echo "Erreur : le répertoire à traiter est obligatoire."
  echo "Usage : $0 -d <répertoire> [--dry-run]"
  exit 1
fi

if [[ $DRY_RUN -eq 1 ]]; then
  echo "Mode --dry-run activé : aucune modification ne sera faite sur le système de fichiers."
fi
if [[ $DEBUG -eq 1 ]]; then
  echo "Mode --debug activé : toutes les actions seront affichées."
fi

shopt -s nullglob
for file in "$TARGET_DIR"/*.html; do
  filename=$(basename "$file")
  dir="$TARGET_DIR/${filename%.html}"
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "[DRY-RUN] Créer le dossier : $dir"
  else
    if [[ -d "$dir" ]]; then
      if [[ $DEBUG -eq 1 ]]; then
        echo "Le dossier existe déjà : $dir (aucune création)"
      fi
    else
      if [[ $DEBUG -eq 1 ]]; then
        echo "Créer le dossier : $dir"
      fi
      mkdir -p "$dir"
    fi
  fi

  # Extraction de l'en-tête (title, meta name, meta property et meta)
  head_tags=""
  while IFS= read -r meta_line; do
    # Supprimer les meta name=generator et meta http-equiv
    if echo "$meta_line" | grep -q '<meta'; then
      if echo "$meta_line" | grep -q 'name="generator"'; then
        continue
      fi
      if echo "$meta_line" | grep -q 'http-equiv'; then
        continue
      fi
    fi
    # Si c'est une balise <title>
    if echo "$meta_line" | grep -q '<title>'; then
      head_tags+="$meta_line\n"
    # Si c'est une balise <meta ... content=...>
    elif echo "$meta_line" | grep -q '<meta'; then
      # Extraire l'attribut content
      meta_content=$(echo "$meta_line" | grep -oP 'content="\K[^"]+')
      # Substitution d'URL dans le content si besoin
      meta_content_mod=$(echo "$meta_content" | sed 's|https://michellehenault.wixsite.com/michellehenault/|https://michellehenault.ca/michellehenault/|g')
      if [[ "$meta_content_mod" != "$meta_content" ]]; then
        meta_line=$(echo "$meta_line" | sed "s|$meta_content|$meta_content_mod|")
        meta_content="$meta_content_mod"
      fi
      # Si content est une URL d'image
      if [[ "$meta_content" =~ ^https?://.*\.(jpg|jpeg|png|gif|webp|svg)$ ]]; then
        img_name=$(basename "$meta_content")
        if [[ ! -f "$dir/$img_name" ]]; then
          if [[ $DRY_RUN -eq 1 ]]; then
            echo "[DRY-RUN] Télécharger $meta_content dans $dir/$img_name (depuis meta)"
          else
            if [[ $DEBUG -eq 1 ]]; then
              echo "Télécharger $meta_content dans $dir/$img_name (depuis meta)"
            fi
            wget -q -O "$dir/$img_name" "$meta_content"
          fi
        else
          if [[ $DRY_RUN -eq 1 ]]; then
            echo "[DRY-RUN] Image déjà présente : $dir/$img_name (depuis meta)"
          elif [[ $DEBUG -eq 1 ]]; then
            echo "Image déjà présente : $dir/$img_name (depuis meta)"
          fi
        fi
        # Remplacer l'URL par le nom de fichier local dans la balise meta
        meta_line=$(echo "$meta_line" | sed "s|$meta_content|$img_name|")
      fi
      head_tags+="$meta_line\n"
    fi
  done < <(grep -oP '(<title>.*?</title>|<meta[^>]+name="[^"]+"[^>]*>|<meta[^>]+property="[^"]+"[^>]*>|<meta[^>]+>)' "$file")

  # Extraction ordonnée texte/images (texte = balises wixui-rich-text__text)
  content=""
  while IFS= read -r line; do
    # Si c'est une balise avec la classe wixui-rich-text__text
    if echo "$line" | grep -q 'class="[^\"]*wixui-rich-text__text'; then
      text=$(echo "$line" | sed -E 's/<[^>]+>//g')
      content+="<p>$text</p>\n"
    # Si c'est une balise <img>
    elif echo "$line" | grep -q '<img'; then
      img_url=$(echo "$line" | grep -oP 'src="\K[^\"]+')
      img_alt=$(echo "$line" | grep -oP 'alt="\K[^\"]*')
      img_name=$(basename "$img_url")
      if [[ ! -f "$dir/$img_name" ]]; then
        if [[ $DRY_RUN -eq 1 ]]; then
          echo "[DRY-RUN] Télécharger $img_url dans $dir/$img_name"
        else
          if [[ $DEBUG -eq 1 ]]; then
            echo "Télécharger $img_url dans $dir/$img_name"
          fi
          if [[ "$img_url" =~ ^https?:// ]]; then
            wget -q -O "$dir/$img_name" "$img_url"
          elif [[ -f "$TARGET_DIR/$img_url" ]]; then
            cp "$TARGET_DIR/$img_url" "$dir/$img_name"
            if [[ $DEBUG -eq 1 ]]; then
              echo "Copier $TARGET_DIR/$img_url dans $dir/$img_name"
            fi
          elif [[ -f "$img_url" ]]; then
            cp "$img_url" "$dir/$img_name"
            if [[ $DEBUG -eq 1 ]]; then
              echo "Copier $img_url dans $dir/$img_name"
            fi
          fi
        fi
      else
        if [[ $DRY_RUN -eq 1 ]]; then
          echo "[DRY-RUN] Image déjà présente : $dir/$img_name"
        elif [[ $DEBUG -eq 1 ]]; then
          echo "Image déjà présente : $dir/$img_name"
        fi
      fi
      content+="<img src=\"$img_name\" alt=\"$img_alt\">\n"
    fi
  done < <(grep -oP '(<img[^>]+>|<[^>]*class="[^"]*wixui-rich-text__text[^"]*"[^>]*>.*?</[^>]+>)' "$file")

  if [[ $DRY_RUN -eq 1 ]]; then
    echo "[DRY-RUN] Créer $dir/index.html avec :"
    echo -e "<head>\n$head_tags\n</head>"
    echo -e "$content"
  else
    if [[ $DEBUG -eq 1 ]]; then
      echo "Créer $dir/index.html"
    fi
    # Utiliser printf pour interpréter les \n dans $head_tags et $content
    head_tags=$(printf "%s" "$head_tags" | sed 's/\\n/\n/g')
    content=$(printf "%s" "$content" | sed 's/\\n/\n/g')
    printf '<!DOCTYPE html>\n<html lang=\"fr\">\n<head>\n%s\n</head>\n<body>\n%s</body>\n</html>\n' "$head_tags" "$content" > "$dir/index.html"
  fi
done
shopt -u nullglob
