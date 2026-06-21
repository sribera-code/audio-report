# audio-report

Mes **articles audio** perso : j'écris (ou je génère) un texte, le script le
transforme en MP3 avec une voix neuronale naturelle, et je l'écoute en faisant
autre chose.

## Organisation

```
audio-report/
├── generate_audio.py       # le script texte -> audio (orchestrateur)
├── xtts_worker.py          # moteur XTTS, exécuté dans le venv dédié
├── texts/                  # un .txt par sujet, rangé par jour (la source à narrer)
│   └── AAAA_MM_JJ/         #   ex. texts/2026_06_20/mon-sujet.txt
├── audio/                  # les .mp3 générés, rangés par jour (ignorés par git)
│   └── AAAA_MM_JJ/         #   ex. audio/2026_06_20/mon-sujet.mp3
└── .vscode/tasks.json      # génération en un raccourci dans VS Code
```

## Moteurs de voix

| Moteur   | Qualité | Coût | Remarque |
|----------|---------|------|----------|
| `xtts`   | la plus naturelle | gratuit, **GPU conseillé** | voix neuronale "LLM", venv Python 3.11 dédié (défaut : voix **Aaron Dreschner**) |
| `piper`  | naturelle, légère | gratuit, CPU | repli rapide sans GPU |
| `espeak` | robotique | gratuit, CPU | secours sans configuration |

XTTS est le moteur par défaut recommandé. Il tourne dans un environnement Python
3.11 séparé (PyTorch + coqui-tts) ; `generate_audio.py` lui délègue le travail
via `xtts_worker.py`. Le chemin du Python de ce venv est lu dans la variable
`XTTS_PYTHON`, sinon `~/tts-bench/venv-xtts/Scripts/python.exe`.

Les fichiers générés sont regroupés par jour dans un sous-dossier daté
`AAAA_MM_JJ`. Chaque `texts/<jour>/mon-sujet.txt` produit
`audio/<jour>/mon-sujet.mp3`. Les paragraphes sont séparés par une **ligne vide**.
(`audio` est invariable, `texts` prend un s.)

## Générer un audio (dans VS Code)

1. Ouvrir le fichier `texts/<jour>/<sujet>.txt`.
2. `Ctrl+Shift+B` → tâche **« Générer l'audio (fichier courant, voix Piper) »**.
3. Le MP3 apparaît dans `audio/` (à la racine ; pour le ranger dans le
   sous-dossier daté, utiliser la ligne de commande ci-dessous).

Ou en ligne de commande — voix XTTS naturelle (défaut Aaron Dreschner) :

```powershell
python generate_audio.py texts/2026_06_20/mon-sujet.txt --engine xtts `
    --voice "Aaron Dreschner" `
    --output audio/2026_06_20/mon-sujet
```

Repli léger Piper (sans GPU) :

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

**Moteur XTTS (recommandé)** : tout est géré par `setup_xtts.ps1` (voir la
section « Installer le moteur XTTS » ci-dessous) — uv, Python 3.11, venv,
PyTorch, coqui-tts et ffmpeg.

**Repli Piper (sans GPU)** — optionnel, seulement si tu utilises `--engine piper` :

| Outil      | Installation |
|------------|--------------|
| ffmpeg     | géré par `setup_xtts.ps1`, ou `winget install Gyan.FFmpeg` |
| piper-tts  | `pip install piper-tts` |
| voix FR    | `python -m piper.download_voices fr_FR-siwis-medium` |

> Astuce ffmpeg sans `winget` : `setup_xtts.ps1` télécharge un build statique et
> l'ajoute au PATH. À la main, le paquet `imageio-ffmpeg` embarque aussi un
> binaire ffmpeg réutilisable (le copier en `ffmpeg.exe` dans un dossier du PATH).

> Note réseau (voix Piper) : si le téléchargement échoue (SSL/proxy), récupérer
> les 2 fichiers à la main depuis HuggingFace (`rhasspy/piper-voices`, dossier
> `fr/fr_FR/siwis/medium/`) avec `curl.exe --ssl-no-revoke` et les placer dans
> `%USERPROFILE%\.local\share\piper\voices\`.

## Installer le moteur XTTS (une seule fois)

**Le plus simple — un seul script** installe tout (uv, Python 3.11 isolé, venv,
PyTorch CUDA, coqui-tts, et ffmpeg s'il manque) sans toucher au Python système :

```powershell
powershell -ExecutionPolicy Bypass -File .\setup_xtts.ps1
```

Sans GPU : `... -File .\setup_xtts.ps1 -CudaIndex cpu`. Le modèle (~1,8 Go) se
télécharge tout seul au premier `--engine xtts`. Si tu mets le venv ailleurs
(`-VenvDir`), pointe dessus avec la variable `XTTS_PYTHON` ou l'option
`--xtts-python`.

<details>
<summary>Étapes manuelles équivalentes (si tu préfères ne pas lancer le script)</summary>

```powershell
# uv (si absent) :
python -m pip install --user uv

# Python 3.11 isolé + venv dédié :
python -m uv python install 3.11
python -m uv venv --python 3.11 "$env:USERPROFILE\tts-bench\venv-xtts"

# PyTorch CUDA + coqui-tts dans ce venv :
$PY = "$env:USERPROFILE\tts-bench\venv-xtts\Scripts\python.exe"
python -m uv pip install --python $PY torch torchaudio --index-url https://download.pytorch.org/whl/cu124
python -m uv pip install --python $PY coqui-tts "transformers>=4.57,<5"
```

> `transformers` est épinglé `>=4.57,<5` : coqui-tts exige ≥4.57, mais la
> branche 5.x a retiré une fonction qu'il utilise encore (sinon : `ImportError`).
</details>

## Options du script

| Option           | Rôle | Défaut |
|------------------|------|--------|
| `--engine`       | `xtts` (le plus naturel) / `piper` / `espeak` / `auto` | `auto` |
| `--voice`        | nom de voix XTTS (ex. `Aaron Dreschner`) **ou** nom/chemin du modèle Piper | `Aaron Dreschner` (xtts), `fr_FR-siwis-medium` (piper) |
| `--output`       | nom de base de sortie | nom du texte |
| `--rate`         | vitesse espeak (mots/min) | `155` |
| `--gap`          | silence entre paragraphes (s) | `0.6` |
| `--xtts-python`  | Python du venv XTTS | `$XTTS_PYTHON` ou `~/tts-bench/venv-xtts` |

## Autres voix à essayer

- **XTTS** : 58 voix intégrées (ex. `Aaron Dreschner`, `Alison Dietlinde`,
  `Sofia Hellen`, `Ana Florence`, `Damien Black`…). Passer le nom exact à `--voice`.
- **Piper** : `fr_FR-tom-medium`, `fr_FR-upmc-medium` — les télécharger comme
  ci-dessus puis passer leur nom/chemin à `--voice`.
