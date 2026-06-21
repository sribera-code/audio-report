# audio-report

Mes **articles audio** perso : j'écris (ou je génère) un texte, le script le
transforme en MP3 avec une voix neuronale naturelle, et je l'écoute en faisant
autre chose.

## Organisation

```
audio-report/
├── generate_audio.py       # le script texte -> audio
├── texts/                  # un .txt par sujet, rangé par jour (la source à narrer)
│   └── AAAA_MM_JJ/         #   ex. texts/2026_06_20/mon-sujet.txt
├── audio/                  # les .mp3 générés, rangés par jour (ignorés par git)
│   └── AAAA_MM_JJ/         #   ex. audio/2026_06_20/mon-sujet.mp3
└── .vscode/tasks.json      # génération en un raccourci dans VS Code
```

## Moteurs de voix

| Moteur   | Qualité | Coût | Remarque |
|----------|---------|------|----------|
| `piper`  | naturelle, légère | gratuit, CPU | **moteur par défaut**, hors-ligne, rapide (voix **fr_FR-siwis-medium**) |
| `espeak` | robotique | gratuit, CPU | secours sans configuration |

Piper est le moteur recommandé : 100 % local, instantané, sans GPU. La voix par
défaut est **fr_FR-siwis-medium** (féminine, claire).

Les fichiers générés sont regroupés par jour dans un sous-dossier daté
`AAAA_MM_JJ`. Chaque `texts/<jour>/mon-sujet.txt` produit
`audio/<jour>/mon-sujet.mp3`. Les paragraphes sont séparés par une **ligne vide**.
(`audio` est invariable, `texts` prend un s.)

## Générer un audio (dans VS Code)

1. Ouvrir le fichier `texts/<jour>/<sujet>.txt`.
2. `Ctrl+Shift+B` → tâche **« Générer l'audio (fichier courant, voix Piper siwis-medium) »**.
3. Le MP3 apparaît dans `audio/` (à la racine ; pour le ranger dans le
   sous-dossier daté, utiliser la ligne de commande ci-dessous).

Ou en ligne de commande — voix Piper par défaut (fr_FR-siwis-medium) :

```powershell
python generate_audio.py texts/2026_06_20/mon-sujet.txt --engine piper `
    --voice "$env:USERPROFILE\.local\share\piper\voices\fr_FR-siwis-medium.onnx" `
    --output audio/2026_06_20/mon-sujet
```

Le plus court (auto-détection Piper/espeak, sortie à côté du texte) :

```powershell
python generate_audio.py texts/2026_06_20/mon-sujet.txt
```

## Pré-requis

| Outil      | Installation |
|------------|--------------|
| ffmpeg     | `winget install Gyan.FFmpeg` (ou build statique gyan.dev ajouté au PATH) |
| piper-tts  | `pip install piper-tts` |
| voix FR    | `python -m piper.download_voices fr_FR-siwis-medium` |

> Astuce ffmpeg sans `winget` : télécharger le build statique
> `ffmpeg-release-essentials.zip` depuis gyan.dev, le décompresser et ajouter son
> dossier `bin` au PATH. (Le paquet `imageio-ffmpeg` embarque aussi un binaire
> ffmpeg réutilisable.)

> Note réseau (voix Piper) : si le téléchargement échoue (SSL/proxy), récupérer
> les 2 fichiers à la main depuis HuggingFace (`rhasspy/piper-voices`, dossier
> `fr/fr_FR/siwis/medium/`) avec `curl.exe --ssl-no-revoke` et les placer dans
> `%USERPROFILE%\.local\share\piper\voices\`.

## Options du script

| Option       | Rôle | Défaut |
|--------------|------|--------|
| `--engine`   | `piper` (recommandé) / `espeak` / `auto` | `auto` |
| `--voice`    | nom ou chemin du modèle Piper | `fr_FR-siwis-medium` |
| `--output`   | nom de base de sortie | nom du texte |
| `--rate`     | vitesse espeak (mots/min) | `155` |
| `--gap`      | silence entre paragraphes (s) | `0.6` |

## Autres voix Piper à essayer

`fr_FR-tom-medium` (masculine), `fr_FR-upmc-medium`, `fr_FR-mls-medium` — les
télécharger comme ci-dessus (`python -m piper.download_voices <nom>`) puis passer
leur nom/chemin à `--voice`.
