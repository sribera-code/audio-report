#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_audio.py
=================
Transforme un fichier texte de narration en audio .mp3.

Deux moteurs de synthèse vocale sont gérés :
  - piper   : voix neuronale, son naturel, hors-ligne, GRATUIT      (RECOMMANDÉ)
  - espeak  : voix robotique mais sans aucune configuration            (SECOURS)

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

------------------------------------------------------------------------------
UTILISATION
------------------------------------------------------------------------------
# Voix naturelle :
    python generate_audio.py texts/2026_06_20/mon-sujet.txt --engine piper \
        --voice fr_FR-siwis-medium --output audio/2026_06_20/mon-sujet

# Auto : prend Piper si dispo, sinon espeak :
    python generate_audio.py texts/2026_06_20/mon-sujet.txt

Options principales :
    --engine    piper | espeak | auto   (défaut: auto)
    --voice     nom OU chemin du modèle Piper (défaut: fr_FR-siwis-medium)
    --output    nom de base de sortie     (défaut: <nom du texte>)
    --rate      vitesse espeak en mots/min (défaut: 155)
    --gap       silence entre paragraphes, en secondes (défaut: 0.6)
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import wave


PIPER_VOICE_DEFAULT = "fr_FR-siwis-medium"


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


def cmd_piper(voix, sortie_wav):
    """Construit la commande Piper, que ce soit l'exécutable ou le module Python."""
    if shutil.which("piper"):
        # piper.exe est aussi un programme Python : comme le module, il lit le
        # texte via sys.stdin en mode texte (encodage local cp1252 sous Windows).
        # Le passage en UTF-8 est assuré pour les deux branches par env_piper().
        return ["piper", "--model", voix, "--output_file", sortie_wav]
    # Repli : Piper installé comme module Python (python -m piper).
    # -X utf8 reste posé ici par ceinture et bretelles (il ne s'applique qu'au
    # module, pas à piper.exe ; c'est env_piper() qui couvre les deux cas).
    return [sys.executable, "-X", "utf8", "-m", "piper", "-m", voix, "-f", sortie_wav]


def env_piper():
    """Environnement forçant l'UTF-8 pour le sous-processus Piper.

    IMPÉRATIF : Piper (que ce soit piper.exe OU python -m piper) lit le texte
    via sys.stdin, qui sous Windows utilise par défaut l'encodage local cp1252.
    Nos accents, envoyés en UTF-8, y sont alors mal décodés et la voix prononce
    du mojibake (« é » devient « Ã© »), rendant l'audio incompréhensible et
    bien plus long. PYTHONUTF8=1 force le mode UTF-8 quelle que soit la branche.
    """
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def synth_piper(texte, sortie_wav, voix):
    """Synthèse via Piper (voix neuronale)."""
    # Piper lit le texte sur l'entrée standard et écrit un WAV.
    proc = subprocess.run(
        cmd_piper(voix, sortie_wav),
        input=texte.encode("utf-8"),
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        env=env_piper(),
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

    ap = argparse.ArgumentParser(description="Génère un audio .mp3 depuis un texte.")
    ap.add_argument("texte", help="Fichier texte de narration (paragraphes séparés par des lignes vides).")
    ap.add_argument("--engine", choices=["piper", "espeak", "auto"], default="auto")
    ap.add_argument("--voice", default=None,
                    help="Nom ou chemin du modèle Piper. Défaut : fr_FR-siwis-medium.")
    ap.add_argument("--output", default=None, help="Nom de base de sortie (sans extension).")
    ap.add_argument("--rate", type=int, default=155, help="Vitesse espeak (mots/min).")
    ap.add_argument("--gap", type=float, default=0.6, help="Silence entre paragraphes (s).")
    args = ap.parse_args()

    if not os.path.exists(args.texte):
        sys.exit(f"[ERREUR] Fichier introuvable : {args.texte}")

    need("ffmpeg")
    moteur = detecter_moteur() if args.engine == "auto" else args.engine
    print(f"Moteur de synthèse : {moteur}")

    if moteur == "espeak":
        need("espeak-ng" if shutil.which("espeak-ng") else "espeak")
    voix_piper = args.voice or PIPER_VOICE_DEFAULT

    paragraphes = lire_paragraphes(args.texte)
    if not paragraphes:
        sys.exit("[ERREUR] Le fichier texte est vide.")
    print(f"{len(paragraphes)} paragraphes à narrer.\n")

    base = args.output or os.path.splitext(os.path.basename(args.texte))[0]
    dossier = os.path.dirname(base)
    if dossier:
        os.makedirs(dossier, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        morceaux = construire_audio(paragraphes, moteur, voix_piper, args.rate, args.gap, tmp)
        wav_final = os.path.join(tmp, "final.wav")
        print("\nAssemblage de la piste audio...")
        concatener(morceaux, wav_final, tmp)

        mp3 = base + ".mp3"
        print(f"Encodage MP3 -> {mp3}")
        vers_mp3(wav_final, mp3)

    print("\nTermine.")


if __name__ == "__main__":
    main()
