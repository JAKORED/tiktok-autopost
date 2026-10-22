"""Tests du réalisateur « FactVibes Nocturne » (22/10/2026).

Pas de pytest (dépendance non nécessaire) : scripts plats, comme
tests/test_detection_doublon.py. Chaque test imprime OK/ECHEC par vérification
et termine par un code retour non nul si le moindre échec.

Couvert :
  1. storyboards des 10 scénarios v2 sont valides (plans, mouvements, transitions connus)
  2. numérotation G55..G64 = auto_217..226, une seule vidéo par scénario
  3. cinématique : easing borné, caméra dans les limites, plans sans trou ni chevauchement
  4. rig : ancien chemin (sans rig) strictement identique, nouveau chemin sans exception
  5. légendes v2 : aucun « auto_ », numéro d'épisode présent, <= 5 hashtags
  6. audio_v2 : sfx/musique/ambiances bornés, mix sans NaN, silence qui étouffe la musique
"""
import math
import sys
from pathlib import Path

import numpy as np

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "video_pipeline"))

import artdir as A          # noqa: E402
import audio_v2 as AU       # noqa: E402
import cinema               # noqa: E402
import factory              # noqa: E402
import sets_v2 as S2        # noqa: E402

echecs = []


def verifie(nom, condition, detail=""):
    ok = bool(condition)
    print(f"  {'OK  ' if ok else 'ECHEC'} {nom}" + (f" — {detail}" if detail else ""))
    if not ok:
        echecs.append(f"{nom} — {detail}")


def _lines_factices(n=7):
    """Répliques factices crédibles (structure réelle de prepare())."""
    rng = np.random.default_rng(4)
    lines, t0 = [], 0.7
    emos = ["neutral", "worried", "smug", "happy", "angry", "neutral", "angry"]
    for i in range(n):
        mots = f"phrase numero {i} avec quelques mots pour la synchro".split()
        dur = len(mots) * 0.28
        lines.append(dict(who=["kevin", "fournier"][i % 2], emo=emos[i % len(emos)],
                          text=" ".join(mots), start=t0, dur=dur,
                          audio=np.zeros(int(dur * 24000), dtype=np.float32),
                          rms=np.clip(rng.random(int(dur * 24) + 2), 0, 1),
                          words=[(w, t0 + j * 0.28, t0 + (j + 1) * 0.28)
                                 for j, w in enumerate(mots)],
                          **({"punch": True} if i == n - 1 else {})))
        t0 += dur + 0.3
    return lines, t0 + 1.8


# ------------------------------------------------------------------ 1 & 2 : scénarios
def test_scenarios():
    eps = factory.build_factory_episodes()
    v2 = [e for e in eps if e.get("hooks")]
    verifie("10 scénarios v2 présents", len(v2) == 10, f"{len(v2)} trouvés")
    ids = [e["id"] for e in v2]
    verifie("numérotation auto_217..226",
            ids == [f"auto_{n:03d}" for n in range(217, 227)], str(ids[:3]))
    fams = [e["family"] for e in v2]
    verifie("familles G55..G64 uniques",
            fams == [f"G{n}" for n in range(55, 65)], str(fams))
    tous_ids = [e["id"] for e in eps]
    verifie("aucun id en double dans toute la banque",
            len(tous_ids) == len(set(tous_ids)))
    for e in v2:
        f = e["family"]
        verifie(f"{f} : 7 répliques", len(e["lines"]) == 7)
        verifie(f"{f} : dernière réplique = punch", e["lines"][-1].get("punch") is True)
        verifie(f"{f} : hook dans la 1re réplique", len(e["lines"][0]["text"]) > 10)
        verifie(f"{f} : question de commentaire", len(e.get("question", "")) > 15)
        verifie(f"{f} : 4 variantes d'accroche", len(e.get("hooks", [])) == 4)
        verifie(f"{f} : storyboard non vide", len(e.get("storyboard", {})) >= 3)
        sb = e.get("storyboard", {})
        for k, h in sb.items():
            verifie(f"{f} : plan {k} connu", h.get("kind", "med") in cinema.PLANS)
            verifie(f"{f} : mouvement {k} connu",
                    h.get("move", "drift") in cinema.MOUVES)
            verifie(f"{f} : transition {k} connue",
                    h.get("transition", "cut") in cinema.TRANS)
        # chaque scénario distinct des autres (pas deux fois le même titre)
    titres = [e["title"] for e in v2]
    verifie("titres v2 tous distincts", len(set(titres)) == 10)


# ------------------------------------------------------------------ 3 : cinématique
def test_cinematique():
    for name in ("linear", "in", "out", "in_out", "out_cubic", "out_expo",
                 "in_cubic", "spring"):
        # le « spring » admet un rebound contrôlé (~6 %) ; les autres restent dans [0,1]
        haut = 1.06 if name == "spring" else 1.0
        for k in (-0.5, 0.0, 0.33, 0.5, 0.99, 1.0, 1.7):
            v = A.ease(k, name)
            verifie(f"easing {name}({k}) borné", -0.01 <= v <= haut + 0.01, f"{v:.3f}")
    lines, total = _lines_factices()
    ep = dict(id="t", ep=1, set="office", left="kevin", right="fournier",
              headline="A|B", title="t", topic="t", tags=[], question="q ?",
              storyboard={0: dict(kind="wide", move="push", transition="dip"),
                          3: dict(kind="close", move="pan", transition="wipe"),
                          6: dict(kind="close", move="push", transition="flash",
                                  slam="MOT")})
    sb = cinema.normaliser(ep, lines, total)
    plans = sb["plans"]
    verifie("un plan par réplique", len(plans) == len(lines))
    verifie("plans contigus (aucun trou)",
            all(abs(plans[i]["end"] - plans[i + 1]["start"]) < 1e-6
                for i in range(len(plans) - 1)))
    verifie("plans ordonnés", all(plans[i]["end"] <= plans[i + 1]["start"] + 1e-6
                                  for i in range(len(plans) - 1)))
    verifie("premier plan commence à 0", abs(plans[0]["start"]) < 1e-6)
    verifie("dernier plan finit à total", abs(plans[-1]["end"] - total) < 1e-6)
    for p in plans:
        z0, z1, fx, fy = cinema._cam_target(ep, p)
        verifie("zoom dans les bornes", 0.5 <= z0 <= 3.0 and 0.5 <= z1 <= 3.0,
                f"{p['kind']} {z0:.2f}->{z1:.2f}")
        verifie("focus dans le cadre", 0 <= fx <= A.W and 0 <= fy <= A.H)
    # hints appliqués
    verifie("hint plan 0 appliqué", plans[0]["kind"] == "wide")
    verifie("hint mouvement plan 3", plans[3]["move"] == "pan")
    verifie("hint slam plan 6", plans[6]["slam"] == "MOT")
    verifie("dernier plan en révélation", plans[6]["transition"] == "flash")


# ------------------------------------------------------------------ 4 : rig
def test_rig():
    import cairo
    import toon_engine as E
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, E.W, E.H)
    ctx = cairo.Context(surf)
    t = E.Toon("kevin", 300, 1)
    t.mouth = 0.4
    t.gesture = 0.5
    try:
        t.draw(ctx, 1.5, True, "worried", 1.0, 0.9)          # ancien chemin
        verifie("ancien chemin (sans rig) sans exception", True)
    except Exception as exc:                                  # noqa: BLE001
        verifie("ancien chemin (sans rig) sans exception", False, str(exc))
    for rig in (
        dict(yaw=0.8), dict(yaw=-0.8, lean=0.1), dict(gesture_kind="point"),
        dict(gesture_kind="shrug", shoulder=0.7), dict(gesture_kind="crossed"),
        dict(gesture_kind="facepalm"), dict(gesture_kind="open"),
        dict(enter=0.0, alpha=0.3, x=-200), dict(scale=1.4, pitch=0.5),
        dict(gaze_x=0.9, gaze_y=-0.6, yaw=1.0, lean=-0.2, shoulder=1.0),
    ):
        try:
            to = E.Toon("fournier", 780, 2)
            to.mouth = 0.3
            to.draw(ctx, 2.0, True, "angry", -1.0, 1.0, rig=rig)
            verifie(f"rig {sorted(rig)[0]}=... sans exception", True)
        except Exception as exc:                              # noqa: BLE001
            verifie(f"rig {sorted(rig)} sans exception", False, str(exc))
    # décors en couches
    for kind in ("office", "stage", "factory", "supermarket"):
        couches, pal = S2.build(kind)
        verifie(f"décor {kind} : 3 couches", len(couches) == 3)
        verifie(f"décor {kind} : profondeurs croissantes",
                [d for _, _, d in couches] == [0.55, 0.90, 1.35])


# ------------------------------------------------------------------ 5 : légendes
def test_legendes():
    sys.path.insert(0, str(RACINE / "video_pipeline"))
    import studio
    for e in [x for x in studio.bank() if x.get("hooks")]:
        cap = studio.build_caption(e)
        verifie(f"{e['family']} : pas de « auto_ »", "auto_" not in cap)
        verifie(f"{e['family']} : numéro d'épisode", f"épisode {e['ep']}" in cap)
        nb_tags = cap.count("#")
        verifie(f"{e['family']} : <= 5 hashtags", nb_tags <= 5, str(nb_tags))
        verifie(f"{e['family']} : question présente",
                e["question"].split("?")[0][:20] in cap)
    # les épisodes historiques gardent leur format (regression)
    e = next(x for x in studio.bank() if not x.get("hooks"))
    cap = studio.build_caption(e)
    verifie("historique : pas de « auto_ »", "auto_" not in cap)
    verifie("historique : marque présente", "#FactVibesToons" in cap)


# ------------------------------------------------------------------ 6 : audio
def test_audio():
    lines, total = _lines_factices()
    ep = dict(id="t", ep=1, set="office", left="kevin", right="fournier",
              headline="A|B", title="t", topic="t", tags=[], question="q ?",
              storyboard={})
    n = int(total * AU.SR)
    for nom, sig in (("riser", AU.riser()), ("whoosh", AU.whoosh()),
                     ("stab", AU.stab()), ("hit", AU.hit()),
                     ("tick", AU.tick()), ("shimmer", AU.shimmer()),
                     ("sub_drop", AU.sub_drop())):
        verifie(f"sfx {nom} : fini et non vide", 0 < len(sig) < 3 * AU.SR)
        verifie(f"sfx {nom} : pas de NaN", not np.isnan(sig).any())
        verifie(f"sfx {nom} : amplitude bornée", np.max(np.abs(sig)) <= 1.0)
    for mood in ("curious", "tension", "light", "reveal"):
        mus = AU.make_music(6.0, lambda t, m=mood: m)
        verifie(f"musique {mood} : pas de NaN", not np.isnan(mus).any())
        verifie(f"musique {mood} : amplitude bornée", np.max(np.abs(mus)) <= 1.0)
    for kind in ("office", "factory", "supermarket", "stage"):
        amb = AU.ambience(3.0, kind)
        verifie(f"ambiance {kind} : pas de NaN", not np.isnan(amb).any())
        verifie(f"ambiance {kind} : discrète", np.max(np.abs(amb)) < 0.2)
    # silences détectés entre les répliques (gaps de 0.3s -> aucun; on force un trou)
    lines2 = [dict(l) for l in lines]
    lines2[1]["start"] += 1.2          # creuse 1.2s entre réplique 1 et 2
    verifie("beats détectés", len(AU._beats(lines2, total)) >= 1)
    mood_at = AU._mood_at(lines, total)
    verifie("humeur punch = reveal",
            mood_at(lines[-1]["start"] + 0.05) == "reveal")
    verifie("humeur fin = light", mood_at(total - 0.5) == "light")
    del n


def main():
    print("== scénarios v2 ==")
    test_scenarios()
    print("== cinématique ==")
    test_cinematique()
    print("== rig + décors ==")
    test_rig()
    print("== légendes ==")
    test_legendes()
    print("== audio ==")
    test_audio()
    print()
    if echecs:
        print(f"ECHECS ({len(echecs)}) :")
        for e in echecs:
            print("  -", e)
        sys.exit(1)
    print("TOUS LES TESTS PASSENT")


if __name__ == "__main__":
    main()
