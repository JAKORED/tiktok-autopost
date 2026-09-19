"""Moteur de dessin animé 2D vectoriel (pycairo) — personnages parlants originaux.

Tout est dessiné par code (aucun asset externe, aucun personnage protégé) :
- 5 personnages : Kevin, Mme Fournier, le Ministre Promesse, Mamie Josette, Robo-Bob
- synchro labiale pilotée par l'amplitude réelle de la voix, clignements, respiration,
  gestes des bras, émotions (sourcils / bouche), petits effets (goutte de sueur, veine…)
- décors : bureau, estrade, usine, supermarché
- sous-titres animés mot par mot
"""
import math
import random

import cairo

W, H = 1080, 1920
LEFT_X, RIGHT_X, HEAD_Y, R = 290, 790, 800, 150
COUNTER_Y = 1270

CHARACTERS = {
    "kevin": dict(name="Kevin", skin=(255, 214, 170), hair="messy", hair_col=(74, 48, 32),
                  outfit="hoodie", outfit_col=(242, 132, 40), bags=True),
    "fournier": dict(name="Mme Fournier", skin=(250, 205, 170), hair="bun", hair_col=(60, 40, 40),
                     outfit="blazer", outfit_col=(28, 140, 150), glasses=True, lipstick=True),
    "ministre": dict(name="Le Ministre", skin=(245, 200, 165), hair="gray_side", hair_col=(170, 175, 185),
                     outfit="suit", outfit_col=(30, 44, 90), tie=(200, 40, 50), big_smile=True),
    "josette": dict(name="Mamie Josette", skin=(250, 210, 180), hair="curly_white", hair_col=(238, 238, 245),
                    outfit="cardigan", outfit_col=(140, 90, 170), glasses=True),
    "bob": dict(name="Robo-Bob", skin=(170, 185, 200), hair="robot", hair_col=(90, 100, 115),
                outfit="robot", outfit_col=(120, 135, 150), robot=True),
}


def rgb(c, a=1.0):
    return (c[0] / 255, c[1] / 255, c[2] / 255, a)


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


def ease_out_back(x):
    x = max(0.0, min(1.0, x))
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def ellipse(ctx, cx, cy, rx, ry):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(max(rx, 0.01), max(ry, 0.01))
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()


def rrect(ctx, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()


# ------------------------------------------------------------------ personnages
class Toon:
    def __init__(self, key, cx, seed):
        self.k = key
        self.p = CHARACTERS[key]
        self.cx = cx
        rnd = random.Random(seed)
        t, blinks = rnd.uniform(1.0, 2.5), []
        while t < 90:
            blinks.append(t)
            t += rnd.uniform(2.0, 4.2)
        self.blinks = blinks
        self.gest_phase = rnd.uniform(0, 6)
        self.mouth = 0.0      # 0..1 lissé
        self.gesture = 0.0    # 0..1 lissé
        self.brow_smooth = 0.0

    def blink_amount(self, t):
        for b in self.blinks:
            d = t - b
            if 0 <= d < 0.16:
                return math.sin(d / 0.16 * math.pi)
        return 0.0

    def update(self, energy, dt):
        target = min(1.0, energy * 2.2)
        k = 1 - math.exp(-dt * 30)
        self.mouth += (target - self.mouth) * k
        g_target = 1.0 if energy > 0.04 else 0.0
        self.gesture += (g_target - self.gesture) * (1 - math.exp(-dt * 6))

    # ---- dessin
    def draw(self, ctx, t, speaking, emotion, look_dir, pop=1.0, reacting=False):
        p = self.p
        bob = math.sin(t * 2.2 + self.cx) * 5
        talk_bob = math.sin(t * 9 + self.gest_phase) * 6 * self.mouth if speaking else 0
        tilt = (math.sin(t * 2.0 + self.gest_phase) * 0.018 +
                (math.sin(t * 5.0) * 0.02 * self.mouth if speaking else 0))
        if reacting:
            tilt += math.sin(t * 4.0) * 0.012
        ctx.save()
        ctx.translate(self.cx, HEAD_Y + bob + talk_bob)
        ctx.scale(pop, pop)
        self._torso_and_arms(ctx, t, speaking)
        ctx.rotate(tilt)
        if p.get("robot"):
            self._robot_head(ctx, t, emotion, look_dir)
        else:
            self._head(ctx, t, emotion, look_dir)
        ctx.restore()

    def _torso_and_arms(self, ctx, t, speaking):
        p = self.p
        oc = p["outfit_col"]
        dark = shade(oc, 0.72)
        # bras (derrière le buste)
        for side in (-1, 1):
            sx, sy = side * 0.95 * R, 1.35 * R
            rest = (side * 1.15 * R, 2.45 * R)
            active = (side == 1) and self.gesture > 0.01
            if active:
                sw = math.sin(t * 5 + self.gest_phase)
                gest = (side * 1.05 * R + sw * 0.18 * R, 0.95 * R + math.sin(t * 3.1) * 0.22 * R)
                g = self.gesture
                hx, hy = rest[0] + (gest[0] - rest[0]) * g, rest[1] + (gest[1] - rest[1]) * g
            else:
                hx, hy = rest
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.set_line_width(0.34 * R)
            ctx.set_source_rgba(*rgb(dark))
            ctx.move_to(sx, sy)
            ctx.curve_to(sx + side * 0.3 * R, sy + 0.3 * R, hx, hy - 0.5 * R, hx, hy)
            ctx.stroke()
            ctx.set_source_rgba(*rgb(p["skin"]))
            ctx.arc(hx, hy, 0.24 * R, 0, 2 * math.pi)
            ctx.fill()
            ctx.set_source_rgba(0, 0, 0, 0.55)
            ctx.set_line_width(4)
            ctx.arc(hx, hy, 0.24 * R, 0, 2 * math.pi)
            ctx.stroke()
        # buste
        ctx.set_source_rgba(*rgb(oc))
        rrect(ctx, -1.15 * R, 1.05 * R, 2.3 * R, 3.2 * R, 0.55 * R)
        ctx.fill_preserve()
        ctx.set_source_rgba(0, 0, 0, 0.5)
        ctx.set_line_width(5)
        ctx.stroke()
        kind = p["outfit"]
        if kind == "hoodie":
            ctx.set_source_rgba(*rgb(shade(oc, 0.85)))
            ellipse(ctx, 0, 1.12 * R, 0.62 * R, 0.28 * R)
            ctx.fill()
            ctx.set_source_rgba(1, 1, 1, 0.9)
            ctx.set_line_width(7)
            ctx.move_to(-0.22 * R, 1.3 * R); ctx.line_to(-0.25 * R, 1.95 * R); ctx.stroke()
            ctx.move_to(0.22 * R, 1.3 * R); ctx.line_to(0.25 * R, 1.95 * R); ctx.stroke()
        elif kind in ("blazer", "suit"):
            ctx.set_source_rgba(1, 1, 1, 1)
            ctx.move_to(-0.42 * R, 1.06 * R); ctx.line_to(0.42 * R, 1.06 * R); ctx.line_to(0, 2.35 * R); ctx.close_path()
            ctx.fill()
            ctx.set_source_rgba(*rgb(shade(oc, 0.8)))
            ctx.move_to(-0.42 * R, 1.06 * R); ctx.line_to(-0.85 * R, 1.5 * R); ctx.line_to(-0.1 * R, 1.75 * R); ctx.close_path(); ctx.fill()
            ctx.move_to(0.42 * R, 1.06 * R); ctx.line_to(0.85 * R, 1.5 * R); ctx.line_to(0.1 * R, 1.75 * R); ctx.close_path(); ctx.fill()
            if p.get("tie"):
                ctx.set_source_rgba(*rgb(p["tie"]))
                ctx.move_to(-0.12 * R, 1.08 * R); ctx.line_to(0.12 * R, 1.08 * R); ctx.line_to(0.2 * R, 2.2 * R)
                ctx.line_to(0, 2.4 * R); ctx.line_to(-0.2 * R, 2.2 * R); ctx.close_path(); ctx.fill()
        elif kind == "cardigan":
            ctx.set_source_rgba(*rgb((250, 240, 235)))
            ctx.move_to(-0.5 * R, 1.06 * R); ctx.line_to(0.5 * R, 1.06 * R); ctx.line_to(0.4 * R, 2.5 * R); ctx.line_to(-0.4 * R, 2.5 * R); ctx.close_path(); ctx.fill()
            ctx.set_source_rgba(*rgb(shade(oc, 0.6)))
            for i in range(4):
                ctx.arc(0, (1.55 + 0.32 * i) * R, 0.07 * R, 0, 2 * math.pi); ctx.fill()
        elif kind == "robot":
            ctx.set_source_rgba(*rgb(shade(oc, 0.8)))
            rrect(ctx, -0.7 * R, 1.4 * R, 1.4 * R, 1.3 * R, 0.15 * R); ctx.fill()
            for i, col in enumerate([(60, 220, 120), (255, 200, 60), (240, 80, 80)]):
                ctx.set_source_rgba(*rgb(col))
                ctx.arc(-0.35 * R + i * 0.35 * R, 1.75 * R, 0.1 * R, 0, 2 * math.pi); ctx.fill()
            ctx.set_source_rgba(0.1, 0.1, 0.12, 1)
            for i in range(3):
                rrect(ctx, -0.5 * R, (2.05 + 0.18 * i) * R, 1.0 * R, 0.09 * R, 0.04 * R); ctx.fill()
        # cou
        if not p.get("robot"):
            ctx.set_source_rgba(*rgb(shade(p["skin"], 0.9)))
            rrect(ctx, -0.22 * R, 0.85 * R, 0.44 * R, 0.4 * R, 0.1 * R)
            ctx.fill()

    def _hair_back(self, ctx):
        p = self.p
        hc = p["hair_col"]
        if p["hair"] == "curly_white":
            ctx.set_source_rgba(*rgb(hc))
            for a in range(-185, 5, 16):
                ang = math.radians(a)
                ctx.arc(math.cos(ang) * R * 0.98, math.sin(ang) * R * 0.98, 0.27 * R, 0, 2 * math.pi)
                ctx.fill()
            ctx.arc(-R * 1.0, 0.1 * R, 0.25 * R, 0, 2 * math.pi); ctx.fill()
            ctx.arc(R * 1.0, 0.1 * R, 0.25 * R, 0, 2 * math.pi); ctx.fill()
        elif p["hair"] == "bun":
            ctx.set_source_rgba(*rgb(hc))
            ctx.arc(0, -1.05 * R, 0.34 * R, 0, 2 * math.pi); ctx.fill()

    def _hair_front(self, ctx):
        p = self.p
        hc = p["hair_col"]
        ctx.set_source_rgba(*rgb(hc))
        kind = p["hair"]
        if kind in ("messy", "bun", "gray_side"):
            ctx.save()
            ctx.arc(0, 0, R * 1.0, 0, 2 * math.pi)
            ctx.clip()
            ctx.new_path()
            ctx.move_to(-R * 1.1, -R * 1.1)
            ctx.line_to(R * 1.1, -R * 1.1)
            ctx.line_to(R * 1.1, -0.28 * R)
            if kind == "gray_side":
                ctx.curve_to(0.6 * R, -0.55 * R, -0.2 * R, -0.15 * R, -R * 1.1, -0.5 * R)
            elif kind == "bun":
                ctx.curve_to(0.5 * R, -0.62 * R, -0.3 * R, -0.62 * R, -R * 1.1, -0.28 * R)
            else:
                pts = 7
                for i in range(pts):
                    x0 = R * 1.1 - (2.2 * R) * i / pts
                    x1 = R * 1.1 - (2.2 * R) * (i + 1) / pts
                    ctx.curve_to(x0 - 0.05 * R, -0.05 * R, x1 + 0.05 * R, -0.05 * R, x1, -0.3 * R)
            ctx.close_path()
            ctx.fill()
            ctx.restore()
            if kind == "messy":
                for (bx, by, br) in [(-0.55, -0.98, 0.26), (-0.2, -1.08, 0.28), (0.2, -1.06, 0.28), (0.58, -0.94, 0.26)]:
                    ctx.arc(bx * R, by * R, br * R, 0, 2 * math.pi); ctx.fill()
            if kind == "gray_side":
                for sx in (-1, 1):
                    ellipse(ctx, sx * 0.98 * R, -0.05 * R, 0.09 * R, 0.3 * R); ctx.fill()
        elif kind == "curly_white":
            for (bx, by) in [(-0.6, -0.72), (-0.2, -0.86), (0.2, -0.86), (0.6, -0.72)]:
                ctx.arc(bx * R, by * R, 0.26 * R, 0, 2 * math.pi); ctx.fill()

    def _head(self, ctx, t, emotion, look_dir):
        p = self.p
        skin = p["skin"]
        self._hair_back(ctx)
        # oreilles
        ctx.set_source_rgba(*rgb(shade(skin, 0.95)))
        for sx in (-1, 1):
            ctx.arc(sx * 0.98 * R, 0.08 * R, 0.17 * R, 0, 2 * math.pi); ctx.fill()
        # tête
        ctx.set_source_rgba(*rgb(skin))
        ctx.arc(0, 0, R, 0, 2 * math.pi)
        ctx.fill_preserve()
        ctx.set_source_rgba(0, 0, 0, 0.55)
        ctx.set_line_width(6)
        ctx.stroke()
        # reflet
        ctx.set_source_rgba(1, 1, 1, 0.16)
        ellipse(ctx, -0.35 * R, -0.45 * R, 0.32 * R, 0.2 * R)
        ctx.fill()
        self._hair_front(ctx)
        if emotion in ("happy", "smug") or p.get("big_smile"):
            ctx.set_source_rgba(1, 0.45, 0.5, 0.35)
            for sx in (-1, 1):
                ellipse(ctx, sx * 0.62 * R, 0.28 * R, 0.16 * R, 0.09 * R); ctx.fill()
        self._eyes(ctx, t, emotion, look_dir, dark_bags=p.get("bags"))
        # nez
        ctx.set_source_rgba(*rgb(shade(skin, 0.82)))
        ellipse(ctx, 0, 0.2 * R, 0.1 * R, 0.08 * R)
        ctx.fill()
        self._mouth(ctx, emotion)
        if p.get("glasses"):
            ctx.set_source_rgba(0.1, 0.1, 0.15, 1)
            ctx.set_line_width(7)
            for sx in (-1, 1):
                ellipse(ctx, sx * 0.36 * R, -0.05 * R, 0.33 * R, 0.29 * R)
                ctx.stroke()
            ctx.move_to(-0.03 * R, -0.07 * R); ctx.line_to(0.03 * R, -0.07 * R); ctx.stroke()
        self._effects(ctx, t, emotion)

    def _eyes(self, ctx, t, emotion, look_dir, dark_bags=False):
        bl = self.blink_amount(t)
        ry = 0.29 * R * (1 - 0.92 * bl)
        for sx in (-1, 1):
            ex, ey = sx * 0.36 * R, -0.05 * R
            if dark_bags:
                ctx.set_source_rgba(0.45, 0.3, 0.45, 0.35)
                ellipse(ctx, ex, ey + 0.34 * R, 0.24 * R, 0.07 * R); ctx.fill()
            ctx.set_source_rgba(1, 1, 1, 1)
            ellipse(ctx, ex, ey, 0.25 * R, ry); ctx.fill_preserve()
            ctx.set_source_rgba(0, 0, 0, 0.7); ctx.set_line_width(4); ctx.stroke()
            if bl < 0.7:
                ctx.set_source_rgba(0.08, 0.08, 0.12, 1)
                pr = 0.11 * R * (1.25 if emotion == "worried" else 1.0)
                ellipse(ctx, ex + look_dir * 0.1 * R, ey + (0.03 * R if emotion == "smug" else 0), pr, pr * min(1, ry / (0.29 * R) + 0.1))
                ctx.fill()
                ctx.set_source_rgba(1, 1, 1, 0.9)
                ctx.arc(ex + look_dir * 0.1 * R - 0.03 * R, ey - 0.04 * R, 0.03 * R, 0, 2 * math.pi); ctx.fill()
            if emotion == "neutral" and dark_bags:  # paupière lourde (fatigué)
                ctx.set_source_rgba(*rgb(shade(self.p["skin"], 0.98)))
                ctx.save(); ellipse(ctx, ex, ey, 0.26 * R, 0.3 * R); ctx.clip()
                ctx.rectangle(ex - 0.3 * R, ey - 0.35 * R, 0.6 * R, 0.33 * R); ctx.fill(); ctx.restore()
        # sourcils
        ctx.set_source_rgba(*rgb(shade(self.p["hair_col"], 0.85)))
        ctx.set_line_width(0.075 * R)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for sx in (-1, 1):
            bx, by = sx * 0.36 * R, -0.5 * R
            inner, outer = 0.0, 0.0
            if emotion == "angry":
                inner, outer = 0.16 * R, -0.05 * R
            elif emotion == "worried":
                inner, outer = -0.16 * R, 0.08 * R
            elif emotion == "happy":
                inner, outer = -0.06 * R, -0.06 * R
            elif emotion == "smug":
                inner, outer = (0.06 * R, 0) if sx == -1 else (-0.16 * R, -0.08 * R)
            ctx.move_to(bx - sx * 0.24 * R, by + inner * (1 if sx else 0))
            ctx.line_to(bx + sx * 0.24 * R, by + outer)
            ctx.stroke()

    def _mouth(self, ctx, emotion):
        m = self.mouth
        my = 0.5 * R
        curve = {"happy": 0.22, "smug": 0.12, "worried": -0.14, "angry": -0.2, "neutral": 0.04}.get(emotion, 0.04)
        if self.p.get("big_smile"):
            curve = max(curve, 0.16)
        if m < 0.12:
            ctx.set_source_rgba(0.25, 0.08, 0.1, 1)
            ctx.set_line_width(0.07 * R)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.move_to(-0.3 * R, my)
            ctx.curve_to(-0.15 * R, my + curve * R * 1.6, 0.15 * R, my + curve * R * 1.6, 0.3 * R, my + (-0.05 * R if emotion == "smug" else 0))
            ctx.stroke()
            return
        rx = 0.27 * R * (0.85 + 0.25 * m)
        ry = 0.05 * R + m * 0.2 * R
        ctx.save()
        ellipse(ctx, 0, my + ry * 0.4, rx, ry)
        ctx.clip_preserve()
        ctx.set_source_rgba(0.28, 0.05, 0.1, 1)
        ctx.fill_preserve()
        ctx.set_source_rgba(0.95, 0.4, 0.45, 1)  # langue
        ellipse(ctx, 0, my + ry * 1.55, rx * 0.55, ry * 0.38); ctx.fill()
        if m > 0.35:  # dents
            ctx.set_source_rgba(1, 1, 1, 1)
            ctx.rectangle(-rx, my + ry * 0.4 - ry, rx * 2, ry * 0.42); ctx.fill()
        ctx.restore()
        ellipse(ctx, 0, my + ry * 0.4, rx, ry)
        ctx.set_source_rgba(0.15, 0.03, 0.05, 1); ctx.set_line_width(5); ctx.stroke()
        if self.p.get("lipstick"):
            ellipse(ctx, 0, my + ry * 0.4, rx, ry)
            ctx.set_source_rgba(0.85, 0.1, 0.25, 1); ctx.set_line_width(6); ctx.stroke()

    def _effects(self, ctx, t, emotion):
        if emotion == "worried":  # goutte de sueur
            drop = (t * 0.9) % 1.0
            ctx.set_source_rgba(0.45, 0.75, 1, 0.9)
            ellipse(ctx, 0.95 * R, -0.5 * R + drop * 0.35 * R, 0.09 * R, 0.14 * R); ctx.fill()
        elif emotion == "angry":  # veine
            s = 1 + 0.08 * math.sin(t * 14)
            ctx.set_source_rgba(0.85, 0.1, 0.1, 1)
            ctx.set_line_width(8)
            cx, cy = 0.72 * R, -0.85 * R
            for dx, dy in [(1, 1), (-1, 1), (1, -1), (-1, -1)]:
                ctx.move_to(cx, cy); ctx.curve_to(cx + dx * 0.15 * R * s, cy, cx, cy + dy * 0.15 * R * s, cx + dx * 0.16 * R * s, cy + dy * 0.16 * R * s)
                ctx.stroke()

    def _robot_head(self, ctx, t, emotion, look_dir):
        p = self.p
        metal = p["skin"]
        # antenne
        ctx.set_source_rgba(*rgb(shade(metal, 0.6)))
        ctx.set_line_width(9)
        ctx.move_to(0, -0.95 * R); ctx.line_to(0, -1.35 * R); ctx.stroke()
        blink_led = 0.5 + 0.5 * math.sin(t * 6)
        ctx.set_source_rgba(1, 0.3 + 0.4 * blink_led, 0.3, 1)
        ctx.arc(0, -1.4 * R, 0.13 * R, 0, 2 * math.pi); ctx.fill()
        # boulons d'oreille
        for sx in (-1, 1):
            ctx.set_source_rgba(*rgb(shade(metal, 0.7)))
            rrect(ctx, sx * 1.02 * R - 0.09 * R, -0.2 * R, 0.18 * R, 0.4 * R, 0.05 * R); ctx.fill()
        rrect(ctx, -1.0 * R, -0.95 * R, 2.0 * R, 1.9 * R, 0.35 * R)
        ctx.set_source_rgba(*rgb(metal)); ctx.fill_preserve()
        ctx.set_source_rgba(0, 0, 0, 0.6); ctx.set_line_width(6); ctx.stroke()
        ctx.set_source_rgba(1, 1, 1, 0.14)
        rrect(ctx, -0.85 * R, -0.85 * R, 1.2 * R, 0.25 * R, 0.1 * R); ctx.fill()
        # visage écran
        ctx.set_source_rgba(0.06, 0.09, 0.14, 1)
        rrect(ctx, -0.78 * R, -0.6 * R, 1.56 * R, 1.25 * R, 0.22 * R); ctx.fill()
        bl = self.blink_amount(t)
        eye_h = 0.26 * R * (1 - 0.9 * bl)
        col = {"angry": (255, 80, 80), "worried": (255, 210, 80)}.get(emotion, (80, 230, 255))
        for sx in (-1, 1):
            ex, ey = sx * 0.36 * R, -0.22 * R
            ctx.set_source_rgba(*rgb(col, 0.25))
            ellipse(ctx, ex, ey, 0.3 * R, eye_h + 0.06 * R); ctx.fill()
            ctx.set_source_rgba(*rgb(col))
            ellipse(ctx, ex + look_dir * 0.06 * R, ey, 0.2 * R, eye_h); ctx.fill()
        # sourcils LED
        ctx.set_source_rgba(*rgb(col)); ctx.set_line_width(0.06 * R); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for sx in (-1, 1):
            tilt = {"angry": 0.14, "worried": -0.14}.get(emotion, 0.0)
            ctx.move_to(sx * 0.36 * R - sx * 0.2 * R, -0.52 * R + tilt * R)
            ctx.line_to(sx * 0.36 * R + sx * 0.2 * R, -0.52 * R - tilt * R); ctx.stroke()
        # bouche LED : segments selon l'ouverture
        segs, m = 7, self.mouth
        for i in range(segs):
            h = (0.06 + 0.22 * m * (1 - abs(i - 3) / 4.0)) * R
            ctx.set_source_rgba(*rgb(col, 0.95 if m > 0.1 or i in (2, 3, 4) else 0.5))
            rrect(ctx, (-0.55 + i * 0.16) * R, 0.32 * R - h / 2, 0.12 * R, max(h, 0.05 * R), 0.03 * R); ctx.fill()


# ------------------------------------------------------------------ décors
def _gradient(ctx, top, bottom, y0=0, y1=H):
    g = cairo.LinearGradient(0, y0, 0, y1)
    g.add_color_stop_rgba(0, *rgb(top))
    g.add_color_stop_rgba(1, *rgb(bottom))
    ctx.set_source(g)
    ctx.rectangle(0, y0, W, y1 - y0)
    ctx.fill()


def draw_set(ctx, kind):
    if kind == "office":
        _gradient(ctx, (188, 214, 236), (222, 232, 242))
        ctx.set_source_rgba(*rgb((150, 190, 225)))
        rrect(ctx, 90, 240, 420, 520, 12); ctx.fill()
        ctx.set_source_rgba(*rgb((110, 140, 175)))
        for i, (x, h) in enumerate([(110, 260), (190, 340), (270, 220), (340, 380), (430, 300)]):
            ctx.rectangle(x, 740 - h, 60, h); ctx.fill()
        ctx.set_source_rgba(1, 1, 1, 0.9); ctx.set_line_width(10)
        rrect(ctx, 90, 240, 420, 520, 12); ctx.stroke()
        ctx.move_to(300, 240); ctx.line_to(300, 760); ctx.stroke()
        ctx.set_source_rgba(1, 1, 1, 1); ctx.arc(830, 300, 80, 0, 2 * math.pi); ctx.fill()
        ctx.set_source_rgba(0.2, 0.2, 0.25, 1); ctx.set_line_width(8)
        ctx.arc(830, 300, 80, 0, 2 * math.pi); ctx.stroke()
        ctx.move_to(830, 300); ctx.line_to(830, 250); ctx.move_to(830, 300); ctx.line_to(865, 315); ctx.stroke()
        ctx.set_source_rgba(*rgb((70, 150, 90)))  # plante
        ellipse(ctx, 990, 1140, 46, 70); ctx.fill(); ellipse(ctx, 940, 1090, 40, 62); ctx.fill()
        ctx.set_source_rgba(*rgb((170, 100, 70))); rrect(ctx, 950, 1160, 80, 100, 10); ctx.fill()
        counter = ((150, 110, 80), (120, 85, 60))
    elif kind == "stage":
        _gradient(ctx, (36, 44, 96), (18, 22, 56))
        for i in range(7):  # rideau
            ctx.set_source_rgba(*rgb((150, 30, 50) if i % 2 == 0 else (125, 22, 42)))
            ctx.rectangle(i * 155, 0, 155, 1000); ctx.fill()
        for i in range(9):  # étoiles / spots
            ctx.set_source_rgba(1, 0.9, 0.5, 0.9)
            ctx.arc(60 + i * 120, 90 + (i % 2) * 40, 12, 0, 2 * math.pi); ctx.fill()
        ctx.set_source_rgba(1, 0.95, 0.7, 0.10)
        ctx.move_to(540, 60); ctx.line_to(180, 1250); ctx.line_to(900, 1250); ctx.close_path(); ctx.fill()
        counter = ((90, 60, 40), (66, 44, 30))
    elif kind == "factory":
        _gradient(ctx, (92, 104, 118), (58, 66, 78))
        ctx.set_source_rgba(1, 1, 1, 0.07)
        for i in range(0, W, 120):
            ctx.rectangle(i, 0, 6, 1300); ctx.fill()
        for (gx, gy, gr) in [(150, 330, 110), (330, 260, 70), (900, 380, 130)]:  # engrenages
            ctx.set_source_rgba(*rgb((130, 140, 150)))
            for k in range(10):
                a = k * math.pi / 5
                ctx.save(); ctx.translate(gx, gy); ctx.rotate(a)
                ctx.rectangle(-gr * 0.16, -gr * 1.15, gr * 0.32, gr * 0.3); ctx.fill(); ctx.restore()
            ctx.arc(gx, gy, gr, 0, 2 * math.pi); ctx.fill()
            ctx.set_source_rgba(*rgb((80, 90, 100))); ctx.arc(gx, gy, gr * 0.4, 0, 2 * math.pi); ctx.fill()
        for i in range(14):  # bandes danger
            ctx.set_source_rgba(*rgb((240, 200, 40) if i % 2 == 0 else (30, 30, 34)))
            ctx.rectangle(i * 80, 1240, 80, 30); ctx.fill()
        counter = ((70, 78, 90), (48, 54, 64))
    else:  # supermarket
        _gradient(ctx, (248, 240, 220), (232, 218, 190))
        cols = [(230, 80, 70), (250, 190, 60), (90, 170, 100), (90, 140, 210), (200, 110, 190)]
        for row in range(3):
            y = 260 + row * 250
            ctx.set_source_rgba(*rgb((160, 130, 100))); ctx.rectangle(0, y + 150, W, 22); ctx.fill()
            for i in range(13):
                ctx.set_source_rgba(*rgb(cols[(i + row * 2) % 5]))
                rrect(ctx, 14 + i * 82, y + 40 + (i * 7 % 3) * 8, 62, 110 - (i * 7 % 3) * 8, 8); ctx.fill()
        counter = ((120, 120, 130), (86, 86, 96))
    return counter


def draw_counter(ctx, colors):
    top, bottom = colors
    g = cairo.LinearGradient(0, COUNTER_Y, 0, H)
    g.add_color_stop_rgba(0, *rgb(top)); g.add_color_stop_rgba(1, *rgb(bottom))
    ctx.set_source(g)
    ctx.rectangle(0, COUNTER_Y, W, H - COUNTER_Y); ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 0.22)
    ctx.rectangle(0, COUNTER_Y, W, 14); ctx.fill()


# ------------------------------------------------------------------ texte
def stroked_text(ctx, text, x, y, size, fill, outline=(0, 0, 0), ow=12, family="Impact", center=True):
    ctx.select_font_face(family, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    ext = ctx.text_extents(text)
    px = x - ext.width / 2 - ext.x_bearing if center else x
    ctx.new_path()
    ctx.move_to(px, y)
    ctx.text_path(text)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgba(*rgb(outline)); ctx.set_line_width(ow); ctx.stroke_preserve()
    ctx.set_source_rgba(*rgb(fill)); ctx.fill()


def text_width(ctx, text, size, family="Impact"):
    ctx.select_font_face(family, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    return ctx.text_extents(text).x_advance


def draw_caption(ctx, words, idx_now, t, accent):
    """words : liste [(texte, début, fin)] du groupe affiché ; idx_now : mot actif (ou -1)."""
    size = 92
    space = 44
    line_words = [w[0].upper() for w in words]
    widths = [text_width(ctx, w, size) for w in line_words]
    total = sum(widths) + space * (len(widths) - 1)
    # 2 lignes si trop large
    lines = [list(range(len(words)))]
    if total > W - 140:
        half = (len(words) + 1) // 2
        lines = [list(range(half)), list(range(half, len(words)))]
    y0 = 1400 if len(lines) == 1 else 1350
    for li, idxs in enumerate(lines):
        lw = sum(widths[i] for i in idxs) + space * (len(idxs) - 1)
        x = (W - lw) / 2
        y = y0 + li * 120
        for i in idxs:
            active = (i == idx_now)
            start = words[i][1]
            grow = 1.0 + (0.16 * ease_out_back((t - start) / 0.18) if active else 0)
            ctx.save()
            ctx.translate(x + widths[i] / 2, y - size * 0.3)
            ctx.scale(grow, grow)
            stroked_text(ctx, line_words[i], -widths[i] / 2, size * 0.3, size,
                         accent if active else (255, 255, 255), ow=14, center=False)
            ctx.restore()
            x += widths[i] + space


def draw_headline(ctx, text, sub, accent, t):
    pop = ease_out_back(t / 0.45)
    ctx.save()
    ctx.translate(W / 2, 315)
    ctx.scale(pop, pop)
    lines = text.upper().split("|")
    for i, ln in enumerate(lines):
        stroked_text(ctx, ln, 0, i * 105, 96, accent, ow=16)
    ctx.restore()
    if sub:
        stroked_text(ctx, sub, W / 2, 315 + len(lines) * 105 + 30, 40, (255, 255, 255), ow=8, family="Arial Black")
