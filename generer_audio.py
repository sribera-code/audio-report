#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generer_audio.py
================
Transforme un fichier texte de narration en audio (.mp3) et/ou en vidéo
audio .mp4 (piste sonore + carte-titre fixe, donc lisible partout / uploadable).

Deux moteurs de synthèse vocale sont gérés :
  - piper   : voix neuronale, son naturel, hors-ligne, GRATUIT  (RECOMMANDÉ)
  - espeak  : voix robotique mais sans aucune configuration       (SECOURS)

------------------------------------------------------------------------------
INSTALLATION
------------------------------------------------------------------------------
ffmpeg est requis dans les deux cas :
    Windows       : winget install Gyan.FFmpeg
    Ubuntu/Debian : sudo apt-get install ffmpeg
    macOS (brew)  : brew install ffmpeg

Pour la voix NATURELLE (Piper) :
    pip install piper-tts
    # puis télécharger une voix française (≈ 60 Mo), une seule fois :
    python -m piper.download_voices fr_FR-siwis-medium
    # (autres voix possibles : fr_FR-upmc-medium, fr_FR-tom-medium, ...)

Pour la jolie carte-titre du MP4 (recommandé) :
    pip install pillow

------------------------------------------------------------------------------
UTILISATION
------------------------------------------------------------------------------
# Voix naturelle, sortie mp3 + mp4 :
    python generer_audio.py textes/mon-sujet.txt --engine piper \
        --voice fr_FR-siwis-medium --format both --output audio/mon-sujet

# Auto : prend Piper si dispo, sinon espeak :
    python generer_audio.py textes/mon-sujet.txt

Options principales :
    --engine    piper | espeak | auto   (défaut: auto)
    --voice     nom OU chemin du modèle Piper (défaut: fr_FR-siwis-medium)
    --format    mp3 | mp4 | both          (défaut: both)
    --output    nom de base de sortie     (défaut: <nom du texte>)
    --rate      vitesse espeak en mots/min (défaut: 155)
    --gap       silence entre paragraphes, en secondes (défaut: 0.6)
    --title     texte de la carte-titre du mp4 (défaut: 1re ligne du texte)
    --subtitle  sous-titre de la carte (défaut: aucun)
    --image     image de fond du mp4 (sinon une carte-titre est générée)
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import wave


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------

def need(binary):
    """Vérifie qu'un exécutable est présent dans le PATH, sinon arrête tout."""
    if shutil.which(binary) is None:
        sys.exit(f"[ERREUR] '{binary}' est introuvable. Voir la section INSTALLATION.")


def run(cmd):
    """Lance une commande en masquant la sortie ; remonte une erreur claire."""
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if res.returncode != 0:
        sys.exit(f"[ERREUR] Commande échouée : {' '.join(map(str, cmd))}\n"
                 f"{res.stderr.decode(errors='ignore')}")


def lire_paragraphes(chemin):
    """Découpe le texte en paragraphes (séparés par une ligne vide)."""
    with open(chemin, encoding="utf-8") as f:
        brut = f.read()
    blocs = re.split(r"\n\s*\n", brut.strip())
    return [re.sub(r"\s+", " ", b).strip() for b in blocs if b.strip()]


def silence_wav(chemin, secondes, framerate=22050):
    """Génère un petit fichier WAV de silence (mono 16 bits)."""
    n = int(secondes * framerate)
    with wave.open(chemin, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(framerate)
        w.writeframes(b"\x00\x00" * n)


# ---------------------------------------------------------------------------
# Moteurs de synthèse vocale
# ---------------------------------------------------------------------------

def detecter_moteur():
    """Choisit automatiquement le meilleur moteur disponible."""
    if shutil.which("piper"):
        return "piper"
    if shutil.which("espeak-ng") or shutil.which("espeak"):
        return "espeak"
    sys.exit("[ERREUR] Aucun moteur TTS trouvé. Installe 'piper-tts' ou 'espeak-ng'.")


def synth_piper(texte, sortie_wav, voix):
    """Synthèse via Piper (voix neuronale)."""
    # Piper lit le texte sur l'entrée standard et écrit un WAV.
    proc = subprocess.run(
        ["piper", "--model", voix, "--output_file", sortie_wav],
        input=texte.encode("utf-8"),
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        sys.exit("[ERREUR] Piper a échoué. La voix est-elle téléchargée ?\n"
                 "  python -m piper.download_voices " + voix + "\n"
                 + proc.stderr.decode(errors="ignore"))


def synth_espeak(texte, sortie_wav, rate):
    """Synthèse via espeak-ng (voix robotique de secours)."""
    exe = "espeak-ng" if shutil.which("espeak-ng") else "espeak"
    run([exe, "-v", "fr", "-s", str(rate), "-p", "40", "-w", sortie_wav, texte])


# ---------------------------------------------------------------------------
# Assemblage audio
# ---------------------------------------------------------------------------

def construire_audio(paragraphes, moteur, voix, rate, gap, tmp):
    """Synthétise chaque paragraphe, insère des silences, renvoie la liste de WAV."""
    morceaux = []
    sil = os.path.join(tmp, "silence.wav")
    silence_wav(sil, gap)

    total = len(paragraphes)
    for i, para in enumerate(paragraphes, 1):
        wav = os.path.join(tmp, f"p{i:03d}.wav")
        print(f"  [{i:>3}/{total}] synthese... ({len(para)} caracteres)")
        if moteur == "piper":
            synth_piper(para, wav, voix)
        else:
            synth_espeak(para, wav, rate)
        morceaux.append(wav)
        morceaux.append(sil)          # un silence après chaque paragraphe
    return morceaux


def concatener(morceaux, sortie_wav, tmp):
    """Concatène des WAV avec ffmpeg (ré-encodage pour homogénéiser les formats)."""
    liste = os.path.join(tmp, "liste.txt")
    with open(liste, "w", encoding="utf-8") as f:
        for m in morceaux:
            f.write(f"file '{os.path.abspath(m)}'\n")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", liste,
         "-ar", "22050", "-ac", "1", sortie_wav])


def vers_mp3(wav, mp3):
    run(["ffmpeg", "-y", "-i", wav, "-codec:a", "libmp3lame", "-qscale:a", "2", mp3])


# ---------------------------------------------------------------------------
# Carte-titre (via Pillow : rendu propre et UTF-8 natif, multi-plateforme)
# ---------------------------------------------------------------------------

def _trouver_police(gras=False):
    """Renvoie le chemin d'une police TrueType selon le système, ou None."""
    if sys.platform == "win32":
        base = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
        noms = (["arialbd.ttf", "segoeuib.ttf"] if gras
                else ["arial.ttf", "segoeui.ttf"])
        candidats = [os.path.join(base, n) for n in noms]
    elif sys.platform == "darwin":
        candidats = (["/Library/Fonts/Arial Bold.ttf",
                      "/System/Library/Fonts/Helvetica.ttc"] if gras
                     else ["/Library/Fonts/Arial.ttf",
                           "/System/Library/Fonts/Helvetica.ttc"])
    else:
        d = "/usr/share/fonts/truetype/dejavu"
        candidats = ([f"{d}/DejaVuSans-Bold.ttf"] if gras
                     else [f"{d}/DejaVuSans.ttf"])
    for c in candidats:
        if os.path.exists(c):
            return c
    return None


def _wrap(draw, texte, font, largeur_max):
    """Découpe un texte en lignes qui tiennent dans largeur_max pixels."""
    lignes, courante = [], ""
    for mot in texte.split():
        essai = (courante + " " + mot).strip()
        if draw.textlength(essai, font=font) <= largeur_max or not courante:
            courante = essai
        else:
            lignes.append(courante)
            courante = mot
    if courante:
        lignes.append(courante)
    return lignes


def carte_titre(titre, png, sous_titre=None):
    """Génère une carte-titre 1280x720 via Pillow."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        sys.exit("[ERREUR] Pillow est requis pour la carte-titre du MP4.\n"
                 "  Installe-le (pip install pillow) ou fournis une image "
                 "avec --image.")

    W, H = 1280, 720
    BG = (26, 26, 46)
    BLANC = (245, 245, 250)
    GRIS = (184, 184, 208)
    ACCENT = (120, 130, 220)

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    pf, ps = _trouver_police(gras=True), _trouver_police(gras=False)
    f_titre = ImageFont.truetype(pf, 76) if pf else ImageFont.load_default()
    f_sous = ImageFont.truetype(ps, 32) if ps else ImageFont.load_default()

    lignes = _wrap(d, titre, f_titre, W - 200)
    h_ligne = (d.textbbox((0, 0), "Ap", font=f_titre)[3]) + 14
    h_titre = h_ligne * len(lignes)
    h_sous = (d.textbbox((0, 0), "Ap", font=f_sous)[3] + 24) if sous_titre else 0
    h_accent = 30
    y = (H - (h_titre + h_accent + h_sous)) / 2

    for ligne in lignes:
        w = d.textlength(ligne, font=f_titre)
        d.text(((W - w) / 2, y), ligne, font=f_titre, fill=BLANC)
        y += h_ligne

    y += 8
    d.rectangle([(W / 2 - 90, y), (W / 2 + 90, y + 4)], fill=ACCENT)
    y += h_accent

    if sous_titre:
        for ligne in _wrap(d, sous_titre, f_sous, W - 240):
            w = d.textlength(ligne, font=f_sous)
            d.text(((W - w) / 2, y), ligne, font=f_sous, fill=GRIS)
            y += d.textbbox((0, 0), "Ap", font=f_sous)[3] + 8

    img.save(png)


def vers_mp4(wav, mp4, titre, sous_titre, image, tmp):
    """Construit un mp4 = image fixe (carte-titre ou image fournie) + piste audio."""
    if image and os.path.exists(image):
        fond = image
    else:
        fond = os.path.join(tmp, "fond.png")
        carte_titre(titre, fond, sous_titre)
    run([
        "ffmpeg", "-y", "-loop", "1", "-i", fond, "-i", wav,
        "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-shortest", mp4,
    ])


# ---------------------------------------------------------------------------
# Programme principal
# ---------------------------------------------------------------------------

def main():
    # La console Windows est souvent en cp1252 : on force l'UTF-8 pour les prints
    # (le texte contient des flèches, accents, etc.).
    for flux in (sys.stdout, sys.stderr):
        try:
            flux.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    ap = argparse.ArgumentParser(description="Génère un audio (mp3/mp4) depuis un texte.")
    ap.add_argument("texte", help="Fichier texte de narration (paragraphes séparés par des lignes vides).")
    ap.add_argument("--engine", choices=["piper", "espeak", "auto"], default="auto")
    ap.add_argument("--voice", default="fr_FR-siwis-medium", help="Nom ou chemin du modèle Piper.")
    ap.add_argument("--format", choices=["mp3", "mp4", "both"], default="both")
    ap.add_argument("--output", default=None, help="Nom de base de sortie (sans extension).")
    ap.add_argument("--rate", type=int, default=155, help="Vitesse espeak (mots/min).")
    ap.add_argument("--gap", type=float, default=0.6, help="Silence entre paragraphes (s).")
    ap.add_argument("--title", default=None, help="Titre de la carte du mp4.")
    ap.add_argument("--subtitle", default=None, help="Sous-titre de la carte du mp4.")
    ap.add_argument("--image", default=None, help="Image de fond du mp4.")
    args = ap.parse_args()

    if not os.path.exists(args.texte):
        sys.exit(f"[ERREUR] Fichier introuvable : {args.texte}")

    need("ffmpeg")
    moteur = detecter_moteur() if args.engine == "auto" else args.engine
    if moteur == "espeak":
        need("espeak-ng" if shutil.which("espeak-ng") else "espeak")
    print(f"Moteur de synthèse : {moteur}")

    paragraphes = lire_paragraphes(args.texte)
    if not paragraphes:
        sys.exit("[ERREUR] Le fichier texte est vide.")
    print(f"{len(paragraphes)} paragraphes à narrer.\n")

    base = args.output or os.path.splitext(os.path.basename(args.texte))[0]
    dossier = os.path.dirname(base)
    if dossier:
        os.makedirs(dossier, exist_ok=True)
    titre = args.title or paragraphes[0][:80]

    with tempfile.TemporaryDirectory() as tmp:
        morceaux = construire_audio(paragraphes, moteur, args.voice, args.rate, args.gap, tmp)
        wav_final = os.path.join(tmp, "final.wav")
        print("\nAssemblage de la piste audio...")
        concatener(morceaux, wav_final, tmp)

        if args.format in ("mp3", "both"):
            mp3 = base + ".mp3"
            print(f"Encodage MP3 -> {mp3}")
            vers_mp3(wav_final, mp3)
        if args.format in ("mp4", "both"):
            mp4 = base + ".mp4"
            print(f"Encodage MP4 -> {mp4}")
            vers_mp4(wav_final, mp4, titre, args.subtitle, args.image, tmp)

    print("\nTermine.")


if __name__ == "__main__":
    main()
