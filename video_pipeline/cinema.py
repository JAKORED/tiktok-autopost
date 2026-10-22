"""Réalisateur « FactVibes Nocturne » (22/10/2026) — rendu storyboardé.

Différence fondamentale avec l'ancien `make_toon.render` :
  - l'ancien chemin avait UNE image plate, une caméra qui zoomait doucement et un
    titre jaune visible pendant toute la vidéo ;
  - ici chaque épisode est un **plan par plan** : plans (wide/med/close), mouvements
    de caméra (travelling, panoramique, poussée), parallaxe multicouche (sets_v2),
    transitions motivées (coupe, fondu, flash de révélation, balayage), effets
    atmosphériques (poussières, faisceaux, brouillard, grain, vignettage),
    typographie cinétique (titre révélé par masque puis évacué, sous-titres mot à
    mot avec accent, mot-clé « frappé » au moment de la révélation) et rig complet
    des personnages (tour de tête, regard, posture, gestes, entrée en scène).

Le contenu narratif reste dans `factory.py` (scénario + storyboard optionnel) ;
ce module ne fait que le METTRE EN SCÈNE. Un épisode sans `storyboard` obtient un
plan automatique déterministe (voir `_plan_automatique`), jamais le rendu plat.

Usage interne :
    import cinema
    cinema.render(ep, lines, total, wav, out_path)
"""
import math
import subprocess
import time

import cairo

import artdir as A
import sets_v2 as S2
import toon_engine as E

FPS = 24
W, H = A.W, A.H

# ------------------------------------------------------------------ storyboard
# Types de plan (cadrage) et mouvements de caméra gérés.
PLANS = ("wide", "med", "close")
MOUVES = ("static", "push", "pull", "pan", "drift", "whip")
TRANS = ("cut", "dip", "flash", "wipe")

GESTURES_PAR_EMO = {
    "angry": ("point", 1), "worried": ("crossed", 1), "happy": ("open", 1),
    "smug": ("crossed", 1), "neutral": ("auto", 1),
}


def _side_x(ep, who):
    return E.LEFT_X if who == ep["left"] else E.RIGHT_X


def _plan_automatique(ep, lines):
    """Planification déterministe d'un épisode sans storyboard explicite."""
    plans = []
    n = len(lines)
    for i, ln in enumerate(lines):
        emo = ln.get("emo", "neutral")
        if i == 0:
            kind, move = "wide", "push"
        elif ln.get("punch") or i == n - 1:
            kind, move = "close", "push"
        elif emo in ("angry", "worried"):
            kind, move = "close", "push" if i % 2 else "drift"
        elif emo in ("happy", "smug"):
            kind, move = "med", "drift"
        else:
            kind, move = "med", "push" if i % 2 else "drift"
        trans = "flash" if ln.get("punch") else ("dip" if i == 1 else "cut")
        plans.append(dict(kind=kind, move=move, transition=trans,
                          slam=("|".join(ln["text"].split()[-2:]).upper()
                                if ln.get("punch") else None)))
    return plans


def normaliser(ep, lines, total):
    """Construit la timeline complète : plans, cadrages, moods, cues.

    Chaque réplique = un plan. Les silences (trous > 0,55 s) deviennent des temps
    de respiration : la caméra tient sur le réacteur (plan med sur l'autre).
    """
    hints = ep.get("storyboard") or {}
    auto = _plan_automatique(ep, lines)
    plans = []
    for i, ln in enumerate(lines):
        h = dict(auto[i])
        h.update(hints.get(i, {}) or {})
        start = ln["start"]
        fin_ligne = ln["start"] + ln["dur"]
        suivante = lines[i + 1]["start"] if i + 1 < len(lines) else total
        end = min(suivante, fin_ligne + 0.9) if not ln.get("punch") else total
        if ln.get("punch"):
            end = total
        plans.append(dict(
            i=i, start=start, end=end, kind=h.get("kind", h.get("shot", "med")),
            move=h.get("move", "drift"), transition=h.get("transition", "cut"),
            slam=h.get("slam"), mood=h.get("mood", "tension" if ln.get("punch") else "curious"),
            who=ln["who"], emo=ln.get("emo", "neutral"), line=ln,
        ))
    # calage des bornes (aucun trou, aucun chevauchement) — le premier plan
    # couvre l'amorçage depuis t=0 (titre + entrée des personnages)
    for k, p in enumerate(plans):
        p["start"] = max(p["start"], plans[k - 1]["end"] if k else 0.0)
        if k == 0:
            p["start"] = 0.0
        if k + 1 < len(plans):
            p["end"] = min(p["end"], plans[k + 1]["start"])
    return dict(plans=plans, total=total, lines=lines,
                title_until=3.7, endcard_from=total - 1.9)


# ------------------------------------------------------------------ caméra
def _cam_target(ep, plan):
    """Cadrage cible (zoom + point de vue) d'un plan."""
    sx = _side_x(ep, plan["who"])
    kind = plan["kind"]
    z0, fx, fy = {
        "wide": (1.04, W / 2, 900.0),
        "med": (1.30, sx, 915.0),
        "close": (1.74, sx, 838.0),
    }[kind]
    dz = {"static": 0.0, "push": 0.20, "pull": -0.12, "pan": 0.06,
          "drift": 0.05, "whip": 0.30}[plan["move"]]
    if kind == "wide":
        dz *= 0.5
    return z0, z0 + max(dz, -0.3), fx, fy


def _cam_state(ep, plan, t):
    """Position caméra à l'instant t (easing + panoramique éventuel)."""
    z0, z1, fx, fy = _cam_target(ep, plan)
    k = A.clamp((t - plan["start"]) / max(0.2, plan["end"] - plan["start"]))
    z = A.lerp(z0, z1, A.ease_in_out(k))
    # panoramique : sur un plan « pan », le regard glisse de l'autre personnage
    if plan["move"] == "pan":
        autre = _side_x(ep, ep["right"] if plan["who"] == ep["left"] else ep["left"])
        fx = A.lerp(fx, autre, A.ease_in_out(k) * 0.75)
    # petit angle (dutch) sur les plans colère/révélémentation
    roll = math.radians(-1.4) if plan["emo"] == "angry" and plan["kind"] == "close" else 0.0
    # secousse courte à l'entrée d'un plan « whip »
    shake = 0.0
    if plan["move"] == "whip":
        d = t - plan["start"]
        if 0 <= d < 0.3:
            shake = (1 - d / 0.3) * 16
    return z, fx, fy, roll, shake


def _apply_cam(ctx, z, fx, fy, depth, roll=0.0, shake=0.0, sx_shake=0.0):
    """Transforme caméra pour un plan de profondeur `depth` (parallaxe)."""
    k = 1.0 + (z - 1.0) * depth
    ctx.save()
    ctx.translate(W / 2 + sx_shake, H / 2 + shake * 0.6)
    if roll:
        ctx.rotate(roll * (0.6 + 0.4 * depth))
    ctx.scale(k, k)
    ctx.translate(-fx, -fy)


# ------------------------------------------------------------------ personnages
def _rig(ep, plan, side, t, is_speaking, plans_index):
    """Valeurs du rig pour un personnage pendant un plan."""
    who = ep["left"] if side == "L" else ep["right"]
    vers_camera = -0.55 if side == "L" else 0.55      # tourner face caméra
    vers_partenaire = 0.5 if side == "L" else -0.5    # tourner vers l'autre
    r = dict(x=0.0, y=0.0, lean=0.0, yaw=0.0, pitch=0.0, gaze_x=0.0, gaze_y=0.0,
             scale=1.0, alpha=1.0, enter=1.0, gesture_kind="auto", shoulder=0.0,
             point_dir=1 if side == "L" else -1)
    # entrée en scène sur le tout premier plan
    if plan["i"] == 0:
        k = A.ramp(t, 0.05 if side == "L" else 0.22, 0.55, "out_expo")
        r["enter"] = k
        r["x"] = (-1.0 if side == "L" else 1.0) * (1 - k) * 300.0
    if is_speaking:
        gest, _ = GESTURES_PAR_EMO.get(plan["emo"], ("auto", 1))
        r["gesture_kind"] = gest
        r["lean"] = 0.055 + 0.03 * (plan["kind"] == "close")
        # émotion forte -> on s'adresse à la caméra (le spectateur), sinon à l'autre
        if plan["emo"] in ("angry",) or plan["line"].get("punch"):
            r["yaw"] = vers_camera * (1.0 if plan["line"].get("punch") else 0.7)
            r["gaze_x"] = 0.0
            r["gaze_y"] = -0.15 if plan["emo"] == "angry" else 0.0
        else:
            r["yaw"] = vers_partenaire * 0.35
            r["gaze_x"] = 0.25 * (1 if side == "L" else -1)
        if plan["emo"] == "worried":
            r["shoulder"] = 0.55
            r["lean"] = -0.02
            r["pitch"] = -0.2
        if plan["emo"] == "happy":
            r["pitch"] = 0.25
            r["gaze_y"] = 0.2
    else:
        # réacteur : il écoute, tourne la tête vers la voix, réagit aux émotions
        r["yaw"] = vers_partenaire
        r["gaze_x"] = -0.35 * (1 if side == "L" else -1)
        r["gesture_kind"] = "auto"
        r["lean"] = -0.025
        if plan["emo"] == "angry":
            r["shoulder"] = 0.6
            r["lean"] = -0.07
            r["yaw"] = vers_partenaire * 0.4
        if plan["emo"] == "happy":
            r["gesture_kind"] = "shrug"
        # le punch : l'autre met la main au front (ou hausse les épaules)
        if plan["line"].get("punch") and plan["i"] > 0:
            k = A.ramp(t, plan["start"], 0.45, "out_cubic")
            r["gesture_kind"] = "facepalm"
            r["shoulder"] = 0.45 * k
            r["pitch"] = -0.3 * k
    del plans_index
    return r


# ------------------------------------------------------------------ rendu
def render(ep, lines, total, wav, out_path, png_at=None, seconds=None):
    sb = normaliser(ep, lines, total)
    plans = sb["plans"]
    couches, pal = S2.build(ep["set"])
    chars = {"L": E.Toon(ep["left"], E.LEFT_X, 1), "R": E.Toon(ep["right"], E.RIGHT_X, 2)}
    side_of = {ep["left"]: "L", ep["right"]: "R"}

    from make_toon import build_caption_groups   # import paresseux (pas de cycle)
    groups = build_caption_groups(lines)
    mots_cles = {m.lower() for m in (ep.get("slam_mots_cles") or [])}

    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    ctx.set_antialias(cairo.ANTIALIAS_BEST)

    def _couche(surface):
        """Peint un plan avec filtrage bilinéaire (net sous zoom caméra)."""
        ctx.set_source_surface(surface, 0, 0)
        ctx.get_source().set_filter(cairo.FILTER_GOOD)
        ctx.paint()

    n_frames = int((seconds if seconds else total) * FPS)
    ff = None
    if png_at is None:
        ff = subprocess.Popen(
            ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra",
             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(wav),
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
             "-af", "loudnorm=I=-15:TP=-1.5:LRA=9", "-c:a", "aac", "-b:a", "160k",
             "-t", f"{n_frames / FPS:.3f}", "-movflags", "+faststart", str(out_path)],
            stdin=subprocess.PIPE)

    frames = [int(png_at * FPS)] if png_at is not None else range(n_frames)
    t_start = time.time()
    prev_t = 0.0
    cam = dict(z=1.0, fx=W / 2, fy=900.0)
    for f in frames:
        t = f / FPS
        dt = max(t - prev_t, 1 / FPS)
        prev_t = t
        plan = plans[-1]
        for p in plans:
            if p["start"] <= t < p["end"]:
                plan = p
                break
        speaker = plan["line"] if plan["start"] <= t < plan["start"] + plan["line"]["dur"] + 0.12 else None

        # énergies de bouche (amplitude réelle de la voix)
        energy = {"L": 0.0, "R": 0.0}
        if speaker:
            idx = min(int((t - speaker["start"]) * FPS), len(speaker["rms"]) - 1)
            energy[side_of[speaker["who"]]] = float(speaker["rms"][max(idx, 0)])
        for s in "LR":
            chars[s].update(energy[s], dt)

        z, fx, fy, roll, shake = _cam_state(ep, plan, t)
        kk = 1 - math.exp(-dt * 7)
        cam["z"] += (z - cam["z"]) * kk
        cam["fx"] += (fx - cam["fx"]) * kk
        cam["fy"] += (fy - cam["fy"]) * kk
        z, fx, fy = cam["z"], cam["fx"], cam["fy"]

        # ---- fond + couches parallaxe
        ctx.set_source_rgba(0, 0, 0, 1)
        ctx.paint()
        for nom, couche, depth in couches:
            _apply_cam(ctx, z, fx, fy, depth, roll, shake, shake * 0.5)
            _couche(couche)
            if nom == "mid" and ep["set"] == "office":
                S2.draw_clock_hands(ctx, t)
            ctx.restore()

        # ---- personnages (plan médian, profondeur 1.0)
        _apply_cam(ctx, z, fx, fy, 1.0, roll, shake, shake * 0.5)
        ordre = ["L", "R"]
        if speaker:
            ordre = [s for s in "LR" if s != side_of[speaker["who"]]] + [side_of[speaker["who"]]]
        for s in ordre:
            ch = chars[s]
            is_spk = bool(speaker and side_of[speaker["who"]] == s)
            rig = _rig(ep, plan, s, t, is_spk, 0)
            emo = (plan["emo"] if is_spk else
                   ("worried" if plan["emo"] == "angry" else "neutral"))
            if not is_spk and plan["emo"] == "happy":
                emo = "neutral"
            ch.draw(ctx, t, is_spk, emo, +1 if s == "L" else -1,
                    pop=1.0, reacting=not is_spk, rig=rig)
        ctx.restore()

        # ---- plan avant-plan (profondeur 1.35) : les personnages sont dedans
        _apply_cam(ctx, z, fx, fy, 1.35, roll, shake, shake * 0.5)
        _couche(couches[2][1])
        ctx.restore()

        # ---- atmosphère (écran, hors caméra : la brume respire)
        A.light_shafts(ctx, pal, t, x=W * 0.78, n=3, a=0.13 if ep["set"] != "supermarket" else 0.08)
        A.atmosphere(ctx, pal, t, 0.6)
        A.dust(ctx, t, seed=hash(ep["id"]) % 997, n=22, col=pal["dust"], speed=1.0)
        A.key_light(ctx, pal["key"], t, drift=26)
        A.vignette(ctx, 0.62 if plan["kind"] == "close" else 0.5)
        A.top_gradient(ctx, pal["shadow"], 0.5, 360)
        A.grain(ctx, t, 0.045)
        # fin : le cadre s'assombrit pour que la question lise par-dessus
        if t >= sb["endcard_from"]:
            k = A.ramp(t, sb["endcard_from"], 0.5, "out_cubic")
            ctx.set_source_rgba(0.02, 0.02, 0.05, 0.62 * k)
            ctx.paint()

        # ---- transitions motivées
        d = t - plan["start"]
        if plan["transition"] == "flash" and 0 <= d < 0.22:
            A.flash(ctx, (1 - d / 0.22) ** 1.5 * 0.85)
        elif plan["transition"] == "dip" and 0 <= d < 0.30:
            A.flash(ctx, (1 - d / 0.30) * 0.75, (0, 0, 0))
        elif plan["transition"] == "wipe" and 0 <= d < 0.38:
            k = A.ease_out_expo(d / 0.38)
            ctx.set_source_rgba(*A.rgb(pal["shadow"]))
            ctx.rectangle(W * k, 0, W, H)
            ctx.fill()

        # ---- typographie
        # marque discrète (traçabilité épisode, jamais d'identifiant interne)
        A.outline_text(ctx, f"FACTVIBES TOONS  •  ÉPISODE {ep['ep']}", W / 2, 132, 30,
                       (235, 240, 255), outline=pal["shadow"], ow=8, family="Arial Black",
                       alpha=0.85)
        # titre : révélé par masque puis évacué (ne vole plus le cadre pendant 25 s)
        A.title_card(ctx, ep["headline"], t, A.mix(pal["accent"], (255, 255, 255), 0.25),
                     pal, start=0.30)
        # sous-titres synchronisés (mot actif accentué)
        for g in groups:
            g_start, g_end = g[0][1], g[-1][2] + 0.12
            if g_start - 0.02 <= t < g_end:
                now = -1
                for i, w in enumerate(g):
                    if w[1] <= t:
                        now = i
                A.subtitle_block(ctx, [(w[0], w[1], w[2]) for w in g], t,
                                 A.mix(pal["accent"], (255, 255, 255), 0.15),
                                 idx_now=now, mots_cles=mots_cles)
                break
        # mot-clé frappé au moment de la révélation
        if plan.get("slam"):
            slam_t = None
            if speaker:
                for (w, ws, we) in speaker["words"]:
                    if w.strip(".,!?«»").upper() == plan["slam"].split("|")[0]:
                        slam_t = ws
                        break
            if slam_t is None:
                slam_t = plan["start"] + 0.25
            A.keyword_slam(ctx, plan["slam"].replace("|", " "), t, slam_t,
                           A.mix(pal["accent"], (255, 90, 80), 0.35))
        # barres cinémascope sur l'ouverture et la fermeture
        lb = 0.0
        if t < 1.1:
            lb = A.ramp(t, 0.0, 0.5, "out_cubic")
        elif t > sb["endcard_from"]:
            lb = A.ramp(t, sb["endcard_from"], 0.5, "out_cubic")
        A.letterbox(ctx, lb * 0.55)

        # ---- fin : la question du scénario + appel à suivre (dans la zone sûre)
        if t >= sb["endcard_from"]:
            k = A.ramp(t, sb["endcard_from"], 0.45, "out_expo")
            ctx.save()
            ctx.translate(W / 2, 0)
            q = (ep.get("question") or "Tu en penses quoi, toi ?").upper()
            A.outline_text(ctx, q, 0, 860, A.fit_size(ctx, q, W - 200, 74, 40),
                           (255, 255, 255), outline=pal["shadow"], ow=13, alpha=k)
            p2 = 1 + 0.04 * math.sin(t * 7)
            ctx.save()
            ctx.translate(0, 980)
            ctx.scale(p2, p2)
            A.outline_text(ctx, "SUIS POUR LA SUITE", 0, 0, 58,
                           A.mix(pal["accent"], (255, 255, 255), 0.2),
                           outline=pal["shadow"], ow=11, alpha=k)
            ctx.restore()
            ctx.restore()

        if png_at is not None:
            surf.write_to_png(str(out_path))
            return out_path
        ff.stdin.write(surf.get_data())
        if f % 96 == 0:
            el = time.time() - t_start
            print(f"  {ep['id']} image {f}/{n_frames} ({el:.0f}s écoulées)", flush=True)
    ff.stdin.close()
    if ff.wait() != 0:
        raise RuntimeError("ffmpeg a échoué à l'encodage")
    return out_path
