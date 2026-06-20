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

Les fichiers générés sont regroupés par jour dans un sous-dossier daté
`AAAA_MM_JJ`. Chaque `texts/<jour>/mon-sujet.txt` produit
`audio/<jour>/mon-sujet.mp3`. Les paragraphes sont séparés par une **ligne vide**.
(`audio` est invariable, `texts` prend un s.)

## Générer un audio (dans VS Code)

1. Ouvrir le fichier `texts/<jour>/<sujet>.txt`.
2. `Ctrl+Shift+B` → tâche **« Générer l'audio (fichier courant, voix Piper) »**.
3. Le MP3 apparaît dans `audio/` (à la racine ; pour le ranger dans le
   sous-dossier daté, utiliser la ligne de commande ci-dessous).

Ou en ligne de commande :

```powershell
python generate_audio.py texts/2026_06_20/mon-sujet.txt --engine piper `
    --voice "$env:USERPROFILE\.local\share\piper\voices\fr_FR-siwis-medium.onnx" `
    --output audio/2026_06_20/mon-sujet
```

Le plus court (auto-détection du moteur, sortie à côté du texte) :

```powershell
python generate_audio.py texts/2026_06_20/mon-sujet.txt
```

## Pré-requis (déjà installés sur cette machine)

| Outil      | Installation |
|------------|--------------|
| ffmpeg     | `winget install Gyan.FFmpeg` |
| piper-tts  | `pip install piper-tts` |
| voix FR    | `python -m piper.download_voices fr_FR-siwis-medium` |

> Astuce ffmpeg (si `'ffmpeg' est introuvable` et que `winget` n'est pas
> disponible) : le paquet Python `imageio-ffmpeg` (souvent déjà présent) embarque
> un binaire ffmpeg complet. On le réutilise en le copiant sous le nom `ffmpeg.exe`
> dans un dossier ajouté au PATH :
>
> ```powershell
> $bin = "$env:USERPROFILE\.local\bin"
> New-Item -ItemType Directory -Force $bin | Out-Null
> $exe = python -c "import imageio_ffmpeg, sys; sys.stdout.write(imageio_ffmpeg.get_ffmpeg_exe())"
> Copy-Item $exe (Join-Path $bin "ffmpeg.exe")
> $env:PATH = "$bin;$env:PATH"   # session courante uniquement
> ```
>
> Pour rendre l'astuce permanente, ajouter `%USERPROFILE%\.local\bin` au PATH
> utilisateur de Windows (sinon, refaire la dernière ligne à chaque nouveau
> terminal). `imageio-ffmpeg` s'installe au besoin avec `pip install imageio-ffmpeg`.

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
