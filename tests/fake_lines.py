"""Lignes factices pour tester la MISE EN SCÈNE sans dépendre du TTS (réseau).

Reproduit exactement la structure que `make_toon.prepare` produit réellement :
  dict(who=, emo=, text=, start=, dur=, audio=np.float32, rms=np.float32[],
       words=[(mot, debut, fin)], punch=?)

Usage :
    from tests.fake_lines import lignes_factices
    ep, lines, total = lignes_factices("office")
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "video_pipeline"))

FPS = 24
SR = 24000


def lignes_factices(set_kind="office", duree_mot=0.30):
    """Épisode de test 4 répliques (dont 1 punch) + timings crédibles."""
    ep = dict(
        id="test_001", ep=999, set=set_kind, left="kevin", right="fournier",
        accent=(255, 214, 64), headline="LE TEST|DU REALISATEUR",
        title="Test du realisateur", topic="test", tags=["#test"],
        structure="v2-test", question="Ca te parle ?", storyboard={},
        lines=[
            dict(who="kevin", emo="worried",
                 text="Ceci est un test du nouveau realisateur."),
            dict(who="fournier", emo="smug",
                 text="Un seul test, et on jugera."),
            dict(who="kevin", emo="happy",
                 text="Le decor est en couches, le plafond respire."),
            dict(who="fournier", emo="angry",
                 text="Assez ! Le test est concluant.", punch=True),
        ],
    )
    lines, t0 = [], 0.7
    for ln in ep["lines"]:
        mots = ln["text"].split()
        dur = len(mots) * duree_mot
        n = int(dur * SR)
        t = np.arange(n) / SR
        # « voix » = enveloppe pseudo-parlée pour piloter la synchro labiale
        env = (0.5 + 0.5 * np.sin(2 * np.pi * 4.5 * t)) * np.clip(np.sin(np.pi * t / dur) * 3, 0, 1)
        rms_hop = SR // FPS
        rms = np.array([float(env[min(j, len(env) - 1)]) for j in range(0, n + rms_hop, rms_hop)])
        words = [(w, t0 + i * duree_mot, t0 + (i + 1) * duree_mot) for i, w in enumerate(mots)]
        lines.append(dict(**ln, start=t0, dur=dur,
                          audio=(env * 0.25).astype(np.float32),
                          rms=np.clip(rms, 0, 1), words=words))
        t0 += dur + 0.3
    total = lines[-1]["start"] + lines[-1]["dur"] + 1.8
    return ep, lines, total
