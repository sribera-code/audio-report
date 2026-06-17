# audio-report — consignes de travail

## Workflow par défaut : c'est Claude qui rédige les textes

Quand l'utilisateur demande un sujet (« génère-moi un rapport audio sur X »),
**je rédige moi-même** le fichier texte source dans `textes/<sujet>.txt`. Ne pas
demander à l'utilisateur de fournir le texte.

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

Nommage : `textes/<sujet-en-kebab-case>.txt`. La sortie audio sera
`audio/<sujet>.mp3` (voir README).

Après avoir écrit le texte, **lancer directement la génération audio** (l'utilisateur
veut le MP3, pas seulement le texte). Commande type :

```powershell
python generate_audio.py textes/<sujet>.txt --engine piper `
    --voice "$env:USERPROFILE\.local\share\piper\voices\fr_FR-siwis-medium.onnx" `
    --output audio/<sujet>
```

Versionnage : `textes/` et `audio/` sont **entièrement ignorés par git** (seuls les
`.gitkeep` sont suivis). Les textes sont régénérables via un prompt et l'audio via
le script — rien à versionner ni à ajouter à `.gitignore` à la création.
