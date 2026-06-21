# audio-report — consignes de travail

## Workflow par défaut : c'est Claude qui rédige les textes

Quand l'utilisateur demande un sujet (« génère-moi un rapport audio sur X »),
**je rédige moi-même** le fichier texte source dans
`texts/<AAAA_MM_JJ>/<sujet>.txt`. Ne pas demander à l'utilisateur de fournir le
texte.

Le texte doit être :
- **en français** ;
- **complet et exhaustif** sur le sujet (un vrai rapport de fond, pas un résumé) ;
- **adapté à l'écoute audio** : prose en paragraphes, phrases complètes et fluides,
  transitions parlées (« premièrement », « pour comprendre cela », etc.).

Contraintes de format imposées par `generate_audio.py` :
- **paragraphes séparés par une ligne vide** (c'est le séparateur de découpe) ;
- **pas de Markdown** (`#`, `*`, listes, tableaux) ni de symboles : ils seraient lus
  littéralement par la synthèse vocale. Écrire les sigles de façon prononçable et
  les expliciter à la première occurrence.

Rangement par jour : les fichiers générés sont regroupés dans un sous-dossier
daté `AAAA_MM_JJ` (la date du jour). Un texte donne donc
`texts/<AAAA_MM_JJ>/<sujet>.txt` et l'audio correspondant
`audio/<AAAA_MM_JJ>/<sujet>.mp3` (voir README). Le nom de sujet reste en
kebab-case. (`audio` reste au singulier : nom indénombrable ; `texts` au pluriel.)

Après avoir écrit le texte, **lancer directement la génération audio** (l'utilisateur
veut le MP3, pas seulement le texte). Créer le sous-dossier audio daté au besoin
(le script le fait via `--output`). Commande type par défaut — moteur **Piper**,
voix **fr_FR-siwis-medium** (naturelle, légère, 100 % locale, sans GPU) — en
remplaçant `<AAAA_MM_JJ>` par la date du jour :

```powershell
python generate_audio.py texts/<AAAA_MM_JJ>/<sujet>.txt --engine piper `
    --voice "$env:USERPROFILE\.local\share\piper\voices\fr_FR-siwis-medium.onnx" `
    --output audio/<AAAA_MM_JJ>/<sujet>
```

Piper lit le texte par paragraphes (séparés par une ligne vide) ; il n'a pas la
limite de longueur de phrase de XTTS. ffmpeg est requis (assemblage/encodage MP3) ;
il est installé dans le PATH. Voir README pour les prérequis et les autres voix
françaises disponibles.

Versionnage : `texts/` et `audio/` sont **entièrement ignorés par git** (seuls les
`.gitkeep` suivent les dossiers racines). Les textes sont régénérables via un prompt
et l'audio via le script — rien à versionner ni à ajouter à `.gitignore` à la
création (les sous-dossiers datés sont couverts par `texts/*` et `audio/*`).
