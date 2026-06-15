# audio-report

Mes **articles audio** perso : j'écris (ou je génère) un texte, le script le
transforme en MP3/MP4 avec une voix neuronale naturelle, et je l'écoute en
faisant autre chose.

## Organisation

```
audio-report/
├── generer_audio.py        # le script texte -> audio
├── textes/                 # un .txt par sujet (la source à narrer)
├── audio/                  # les .mp3 / .mp4 générés (ignorés par git)
└── .vscode/tasks.json      # génération en un raccourci dans VS Code
```

Chaque fichier `textes/mon-sujet.txt` produit `audio/mon-sujet.mp3` (+ `.mp4`).
Les paragraphes sont séparés par une **ligne vide** ; la première ligne sert de
titre à la carte du MP4.

## Générer un audio (dans VS Code)

1. Ouvrir le fichier `textes/<sujet>.txt`.
2. `Ctrl+Shift+B` → tâche **« Générer l'audio (fichier courant, voix Piper) »**.
3. Le MP3 et le MP4 apparaissent dans `audio/`.

Ou en ligne de commande :

```powershell
python generer_audio.py textes/mon-sujet.txt --engine piper `
    --voice "$env:USERPROFILE\.local\share\piper\voices\fr_FR-siwis-medium.onnx" `
    --format both --output audio/mon-sujet
```

## Pré-requis (déjà installés sur cette machine)

| Outil      | Installation |
|------------|--------------|
| ffmpeg     | `winget install Gyan.FFmpeg` |
| piper-tts  | `pip install piper-tts` |
| voix FR    | `python -m piper.download_voices fr_FR-siwis-medium` |
| pillow     | `pip install pillow` (jolie carte-titre du MP4) |

> Note réseau : si le téléchargement de la voix échoue (vérification SSL/proxy),
> récupérer les 2 fichiers à la main depuis HuggingFace
> (`rhasspy/piper-voices`, dossier `fr/fr_FR/siwis/medium/`) avec
> `curl.exe --ssl-no-revoke` et les placer dans
> `%USERPROFILE%\.local\share\piper\voices\`.

## Options du script

| Option       | Rôle | Défaut |
|--------------|------|--------|
| `--engine`   | `piper` (naturel) / `espeak` (secours) / `auto` | `auto` |
| `--voice`    | nom ou chemin du modèle Piper | `fr_FR-siwis-medium` |
| `--format`   | `mp3` / `mp4` / `both` | `both` |
| `--output`   | nom de base de sortie | nom du texte |
| `--gap`      | silence entre paragraphes (s) | `0.6` |
| `--title`    | titre de la carte du MP4 | 1re ligne du texte |
| `--subtitle` | sous-titre de la carte | aucun |
| `--image`    | image de fond du MP4 (sinon carte-titre auto) | — |

## Autres voix Piper à essayer

`fr_FR-tom-medium`, `fr_FR-upmc-medium` — les télécharger comme ci-dessus puis
passer leur nom/chemin à `--voice`.
