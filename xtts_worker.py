#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xtts_worker.py
==============
Synthèse vocale XTTS-v2 (voix neuronale très naturelle) pour un texte de
narration. Ce script n'est PAS lancé directement : c'est `generate_audio.py`
qui l'appelle, via le Python du venv dédié (voir README), parce que XTTS exige
PyTorch + coqui-tts dans un environnement Python 3.11 séparé.

Logique identique à generate_audio.py : découpe en paragraphes (ligne vide),
synthèse de chaque paragraphe (XTTS découpe lui-même en phrases), silences
entre paragraphes, concaténation puis encodage MP3 via ffmpeg.

Usage (depuis le venv XTTS) :
    python xtts_worker.py texts/<jour>/sujet.txt --voice "Sofia Hellen" \
        --output audio/<jour>/sujet --gap 0.5
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import wave

# XTTS télécharge le modèle au 1er run ; on accepte sa licence sans interaction.
os.environ.setdefault("COQUI_TOS_AGREED", "1")

import torch
from TTS.api import TTS

MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"


def lire_paragraphes(chemin):
    """Découpe le texte en paragraphes (séparés par une ligne vide)."""
    brut = open(chemin, encoding="utf-8").read().strip()
    blocs = re.split(r"\n\s*\n", brut)
    return [re.sub(r"\s+", " ", b).strip() for b in blocs if b.strip()]


def silence_wav(chemin, secondes, framerate):
    """Génère un petit WAV de silence (mono 16 bits) au bon échantillonnage."""
    n = int(secondes * framerate)
    with wave.open(chemin, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(framerate)
        w.writeframes(b"\x00\x00" * n)


def main():
    ap = argparse.ArgumentParser(description="Synthèse XTTS-v2 d'un texte -> MP3.")
    ap.add_argument("texte", help="Fichier texte (paragraphes séparés par des lignes vides).")
    ap.add_argument("--voice", default="Aaron Dreschner", help="Nom de la voix XTTS intégrée.")
    ap.add_argument("--output", default=None, help="Nom de base de sortie (sans extension).")
    ap.add_argument("--gap", type=float, default=0.5, help="Silence entre paragraphes (s).")
    args = ap.parse_args()

    if not os.path.exists(args.texte):
        sys.exit(f"[ERREUR] Fichier introuvable : {args.texte}")

    ff = shutil.which("ffmpeg")
    if ff is None:
        sys.exit("[ERREUR] ffmpeg introuvable dans le PATH (requis pour l'assemblage).")

    paragraphes = lire_paragraphes(args.texte)
    if not paragraphes:
        sys.exit("[ERREUR] Le fichier texte est vide.")
    print(f"{len(paragraphes)} paragraphes a narrer, voix={args.voice}.", flush=True)

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Chargement du modele XTTS-v2 (device={dev})...", flush=True)
    tts = TTS(MODEL).to(dev)
    sr = tts.synthesizer.output_sample_rate

    speakers = set(tts.synthesizer.tts_model.speaker_manager.speakers.keys())
    if args.voice not in speakers:
        sys.exit(f"[ERREUR] Voix inconnue : {args.voice}\n"
                 f"Voix disponibles : {', '.join(sorted(speakers))}")

    base = args.output or os.path.splitext(args.texte)[0]
    dossier = os.path.dirname(base)
    if dossier:
        os.makedirs(dossier, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        sil = os.path.join(tmp, "silence.wav")
        silence_wav(sil, args.gap, sr)

        morceaux = []
        total = len(paragraphes)
        for i, para in enumerate(paragraphes, 1):
            wav = os.path.join(tmp, f"p{i:03d}.wav")
            print(f"  [{i:>3}/{total}] synthese... ({len(para)} caracteres)", flush=True)
            tts.tts_to_file(text=para, file_path=wav, language="fr",
                            speaker=args.voice, split_sentences=True)
            morceaux.append(wav)
            morceaux.append(sil)          # un silence après chaque paragraphe

        liste = os.path.join(tmp, "liste.txt")
        with open(liste, "w", encoding="utf-8") as f:
            for m in morceaux:
                f.write(f"file '{os.path.abspath(m)}'\n")

        print("\nAssemblage de la piste audio...", flush=True)
        wav_final = os.path.join(tmp, "final.wav")
        subprocess.run([ff, "-y", "-f", "concat", "-safe", "0", "-i", liste,
                        "-ar", str(sr), "-ac", "1", wav_final],
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)

        mp3 = base + ".mp3"
        print(f"Encodage MP3 -> {mp3}", flush=True)
        subprocess.run([ff, "-y", "-i", wav_final, "-codec:a", "libmp3lame",
                        "-qscale:a", "2", mp3],
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)

    print("\nTermine.", flush=True)


if __name__ == "__main__":
    main()
