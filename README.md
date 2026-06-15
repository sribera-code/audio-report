# audio-report

Mes **articles audio** perso : j'écris (ou je génère) un texte, le script le
transforme en MP3 avec une voix neuronale naturelle, et je l'écoute en faisant
autre chose.

## Organisation

```
audio-report/
├── generate_audio.py       # le script texte -> audio
├── textes/                 # un .txt par sujet (la source à narrer)
├── audio/                  # les .mp3 générés (ignorés par git)
└── .vscode/tasks.json      # génération en un raccourci dans VS Code
```

Chaque fichier `textes/mon-sujet.txt` produit `audio/mon-sujet.mp3`.
Les paragraphes sont séparés par une **ligne vide**.

## Générer un audio (dans VS Code)

1. Ouvrir le fichier `textes/<sujet>.txt`.
2. `Ctrl+Shift+B` → tâche **« Générer l'audio (fichier courant, voix Piper) »**.
3. Le MP3 apparaît dans `audio/`.

Ou en ligne de commande :

```powershell
python generate_audio.py textes/mon-sujet.txt --engine piper `
    --voice "$env:USERPROFILE\.local\share\piper\voices\fr_FR-siwis-medium.onnx" `
    --output audio/mon-sujet
```

Le plus court (auto-détection du moteur, sortie à côté du texte) :

```powershell
python generate_audio.py textes/mon-sujet.txt
```

## Pré-requis (déjà installés sur cette machine)

| Outil      | Installation |
|------------|--------------|
| ffmpeg     | `winget install Gyan.FFmpeg` |
| piper-tts  | `pip install piper-tts` |
| voix FR    | `python -m piper.download_voices fr_FR-siwis-medium` |

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
| `--output`   | nom de base de sortie | nom du texte |
| `--rate`     | vitesse espeak (mots/min) | `155` |
| `--gap`      | silence entre paragraphes (s) | `0.6` |

## Autres voix Piper à essayer

`fr_FR-tom-medium`, `fr_FR-upmc-medium` — les télécharger comme ci-dessus puis
passer leur nom/chemin à `--voice`.
