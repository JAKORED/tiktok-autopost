"""Décors en couches parallaxe — FactVibes Nocturne (22/10/2026).

Chaque décor est découpé en 3 plans rendus séparément, déplacés à des vitesses
différentes par la caméra de `cinema.py` :

    far   (depth 0.55)  ciel, ville derrière la fenêtre, brume lointaine
    mid   (depth 0.90)  mur, fenêtre, étagères, engrenages, produits, horloge
    near  (depth 1.35)  comptoir / bureau en avant-plan + éléments qui passent devant

Les personnages sont insérés entre `mid` et `near` : ils sont donc DERRIÈRE le plan
avant-plan, ce qui donne instantanément de la profondeur (l'ancien moteur n'avait
qu'un seul plan plein cadre).

Les palettes viennent de `artdir.PALETTES` (décor nocturne = identité de la chaîne).
"""
import math

import cairo

import artdir as A

W, H = A.W, A.H
TAU = math.tau

# profondeur de chaque plan (multiplie le zoom caméra)
DEPTH = {"far": 0.55, "mid": 0.90, "near": 1.35}


def _surface():
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    c = cairo.Context(s)
    c.set_antialias(cairo.ANTIALIAS_BEST)
    return s, c


def _grad(ctx, top, bottom, y0=0, y1=H):
    g = cairo.LinearGradient(0, y0, 0, y1)
    g.add_color_stop_rgba(0, *A.rgb(top))
    g.add_color_stop_rgba(1, *A.rgb(bottom))
    ctx.set_source(g)
    ctx.rectangle(0, y0, W, y1 - y0)
    ctx.fill()


def _rrect(ctx, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()


def _ellipse(ctx, cx, cy, rx, ry):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(max(rx, .01), max(ry, .01))
    ctx.arc(0, 0, 1, 0, TAU)
    ctx.restore()


# ------------------------------------------------------------------ bureau
def office(pal):
    """Bureau de nuit : fenêtre sur la ville, lampe de bureau, plante, horloge."""
    far, c = _surface()
    _grad(c, pal["sky_top"], pal["sky_bottom"])
    # ville derrière la fenêtre (blobs lumineux, très lointain)
    rnd = [(60, .35), (150, .5), (240, .28), (330, .6), (420, .4), (700, .45),
           (790, .3), (880, .55), (970, .35)]
    for i, (x, hgt) in enumerate(rnd):
        h = 260 + hgt * 620
        c.set_source_rgba(*A.rgb(A.shade(pal["wall"], 0.55), 0.95))
        c.rectangle(x, 780 - h, 78, h)
        c.fill()
        for wy in range(int(780 - h) + 40, 760, 62):
            for wx in range(x + 12, x + 66, 26):
                if (wx + wy + i) % 5 < 2:
                    c.set_source_rgba(1, 0.86, 0.55, 0.55)
                    c.rectangle(wx, wy, 13, 20)
                    c.fill()
    A.dust(c, 0.0, seed=1, n=10, col=pal["fog"], speed=0.4)

    mid, c = _surface()
    _grad(c, A.shade(pal["wall"], 0.92), pal["wall"])
    # fenêtre : VRAIE ouverture (couche transparente) — la planure « far » est
    # vue à travers, à sa propre profondeur : la parallaxe est donc réelle.
    c.save()
    c.set_operator(cairo.OPERATOR_CLEAR)
    _rrect(c, 88, 228, 434, 524, 10)
    c.fill()
    c.restore()
    # encadrement + meneau (tracés, pas de remplissage : le trou reste ouvert)
    c.set_source_rgba(*A.rgb(A.shade(pal["wall"], 0.7)))
    c.set_line_width(20)
    _rrect(c, 88, 228, 434, 524, 10)
    c.stroke()
    c.set_source_rgba(*A.rgb(pal["rim"], 0.30))
    c.set_line_width(9)
    _rrect(c, 88, 228, 434, 524, 10)
    c.stroke()
    c.move_to(305, 228); c.line_to(305, 752); c.stroke()
    # horloge (les aiguilles avancent : temps réel dans la scène)
    c.set_source_rgba(*A.rgb(A.shade(pal["rim"], 0.9), 0.9))
    c.arc(838, 300, 84, 0, TAU)
    c.fill()
    c.set_source_rgba(*A.rgb(pal["shadow"]))
    c.set_line_width(7)
    c.arc(838, 300, 84, 0, TAU)
    c.stroke()
    # étagère + dossiers
    c.set_source_rgba(*A.rgb(A.shade(pal["wall"], 1.18)))
    _rrect(c, 620, 640, 380, 22, 6)
    c.fill()
    for i, col in enumerate([(196, 96, 78), (92, 132, 196), (188, 160, 84), (104, 168, 132)]):
        c.set_source_rgba(*A.rgb(A.shade(col, 0.75)))
        _rrect(c, 640 + i * 88, 664 - 0, 66, 96, 6)
        c.fill()
    # plante
    c.set_source_rgba(*A.rgb(A.shade((84, 150, 108), 0.8)))
    _ellipse(c, 990, 1120, 48, 74); c.fill()
    _ellipse(c, 936, 1064, 40, 62); c.fill()
    c.set_source_rgba(*A.rgb(A.shade((150, 96, 70), 0.8)))
    _rrect(c, 946, 1146, 88, 104, 12); c.fill()

    near, c = _surface()
    # bureau en avant-plan (bord haut du bureau, lampadaire ambre)
    g = cairo.LinearGradient(0, 1250, 0, H)
    g.add_color_stop_rgba(0, *A.rgb(A.shade(pal["floor"], 1.25)))
    g.add_color_stop_rgba(1, *A.rgb(pal["shadow"]))
    c.set_source(g)
    c.rectangle(0, 1250, W, H - 1250)
    c.fill()
    c.set_source_rgba(1, 0.9, 0.7, 0.10)
    c.rectangle(0, 1250, W, 12)
    c.fill()
    return [("far", far), ("mid", mid), ("near", near)]


# ------------------------------------------------------------------ estrade
def stage(pal):
    far, c = _surface()
    _grad(c, pal["sky_top"], pal["sky_bottom"])
    for i in range(9):  # guirlande de projecteurs lointains
        x = 60 + i * 118
        c.set_source_rgba(1, 0.85, 0.5, 0.30 + 0.12 * (i % 2))
        c.arc(x, 120 + (i % 2) * 36, 13, 0, TAU)
        c.fill()
    A.dust(c, 0.0, seed=5, n=12, col=pal["dust"], speed=0.35)

    mid, c = _surface()
    for i in range(8):  # rideau
        c.set_source_rgba(*A.rgb(A.shade(pal["wall"], 0.78 if i % 2 else 0.95)))
        c.rectangle(i * 138, 0, 138, 1120)
        c.fill()
    # faisceau du projecteur
    g = cairo.LinearGradient(540, 60, 540, 1260)
    g.add_color_stop_rgba(0, 1, 0.94, 0.75, 0.20)
    g.add_color_stop_rgba(1, 1, 0.9, 0.7, 0)
    c.set_source(g)
    c.move_to(540, 40); c.line_to(150, 1260); c.line_to(930, 1260)
    c.close_path(); c.fill()

    near, c = _surface()
    g = cairo.LinearGradient(0, 1230, 0, H)
    g.add_color_stop_rgba(0, *A.rgb(A.shade(pal["floor"], 1.5)))
    g.add_color_stop_rgba(1, *A.rgb(pal["shadow"]))
    c.set_source(g)
    c.rectangle(0, 1230, W, H - 1230)
    c.fill()
    c.set_source_rgba(1, 0.95, 0.85, 0.12)
    c.rectangle(0, 1230, W, 10)
    c.fill()
    return [("far", far), ("mid", mid), ("near", near)]


# ------------------------------------------------------------------ usine
def factory(pal):
    far, c = _surface()
    _grad(c, pal["sky_top"], pal["sky_bottom"])
    for i in range(6):  # cheminées / silos
        x = 60 + i * 180
        c.set_source_rgba(*A.rgb(A.shade(pal["wall"], 0.6)))
        _rrect(c, x, 380 + (i % 3) * 60, 110, 460, 10)
        c.fill()
    A.dust(c, 0.0, seed=9, n=10, col=pal["fog"], speed=0.3)

    mid, c = _surface()
    _grad(c, A.shade(pal["wall"], 1.05), A.shade(pal["wall"], 0.75))
    for i in range(0, W, 132):  # poutres
        c.set_source_rgba(*A.rgb(A.shade(pal["wall"], 0.72)))
        c.rectangle(i, 0, 9, 1180)
        c.fill()
    # engrenages (rotation lente)
    for (gx, gy, gr, sens) in [(170, 330, 112, 1), (352, 252, 72, -1), (905, 386, 132, 1)]:
        c.set_source_rgba(*A.rgb(A.shade(pal["wall"], 1.25)))
        for k in range(10):
            c.save(); c.translate(gx, gy); c.rotate(k * math.pi / 5)
            c.rectangle(-gr * 0.16, -gr * 1.15, gr * 0.32, gr * 0.3)
            c.fill(); c.restore()
        c.arc(gx, gy, gr, 0, TAU); c.fill()
        c.set_source_rgba(*A.rgb(A.shade(pal["wall"], 0.6)))
        c.arc(gx, gy, gr * 0.4, 0, TAU); c.fill()
        c.set_source_rgba(*A.rgb(pal["rim"], 0.5))
        c.arc(gx, gy, gr * 0.12, 0, TAU); c.fill()
        del sens
    # bande de danger
    for i in range(15):
        c.set_source_rgba(*A.rgb(pal["accent"] if i % 2 == 0 else A.shade(pal["wall"], 0.4)))
        c.rectangle(i * 76, 1180, 76, 30)
        c.fill()

    near, c = _surface()
    g = cairo.LinearGradient(0, 1255, 0, H)
    g.add_color_stop_rgba(0, *A.rgb(A.shade(pal["floor"], 1.35)))
    g.add_color_stop_rgba(1, *A.rgb(pal["shadow"]))
    c.set_source(g)
    c.rectangle(0, 1255, W, H - 1255)
    c.fill()
    return [("far", far), ("mid", mid), ("near", near)]


# ------------------------------------------------------------------ supermarché
def supermarket(pal):
    far, c = _surface()
    _grad(c, pal["sky_top"], pal["sky_bottom"])
    A.dust(c, 0.0, seed=13, n=10, col=pal["fog"], speed=0.25)

    mid, c = _surface()
    _grad(c, A.shade(pal["wall"], 1.1), pal["wall"])
    cols = [(196, 78, 70), (214, 168, 62), (86, 148, 96), (84, 124, 178), (172, 96, 158)]
    for row in range(3):
        y = 250 + row * 250
        c.set_source_rgba(*A.rgb(A.shade(pal["wall"], 1.35)))
        c.rectangle(0, y + 152, W, 22)
        c.fill()
        for i in range(13):
            c.set_source_rgba(*A.rgb(A.shade(cols[(i + row * 2) % 5], 0.72)))
            _rrect(c, 14 + i * 82, y + 40 + (i * 7 % 3) * 8, 62, 112 - (i * 7 % 3) * 8, 8)
            c.fill()
    # néon rose de la caisse
    g = cairo.LinearGradient(0, 180, 0, 420)
    g.add_color_stop_rgba(0, *A.rgb(pal["accent"], 0.35))
    g.add_color_stop_rgba(1, 0, 0, 0, 0)
    c.set_source(g)
    c.rectangle(0, 180, W, 240)
    c.fill()

    near, c = _surface()
    g = cairo.LinearGradient(0, 1265, 0, H)
    g.add_color_stop_rgba(0, *A.rgb(A.shade(pal["floor"], 1.4)))
    g.add_color_stop_rgba(1, *A.rgb(pal["shadow"]))
    c.set_source(g)
    c.rectangle(0, 1265, W, H - 1265)
    c.fill()
    c.set_source_rgba(1, 1, 1, 0.10)
    c.rectangle(0, 1265, W, 10)
    c.fill()
    return [("far", far), ("mid", mid), ("near", near)]


BUILDERS = {"office": office, "stage": stage, "factory": factory,
            "supermarket": supermarket}


def build(set_kind, mood="night"):
    pal = A.palette_for(set_kind, mood)
    couches = BUILDERS.get(set_kind, office)(pal)
    return [(nom, surf, DEPTH[nom]) for (nom, surf) in couches], pal


def draw_clock_hands(ctx, t, x=838, y=300, r=84, col=(20, 24, 34)):
    """Aiguilles de l'horloge : temps d'écran réel, avance visible sur les longueurs."""
    ctx.set_source_rgba(*A.rgb(col))
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_width(9)
    ang_h = (t / 43200.0) * TAU - math.pi / 2
    ctx.move_to(x, y)
    ctx.line_to(x + math.cos(ang_h) * r * 0.5, y + math.sin(ang_h) * r * 0.5)
    ctx.stroke()
    ctx.set_line_width(6)
    ang_m = (t / 3600.0) * TAU - math.pi / 2
    ctx.move_to(x, y)
    ctx.line_to(x + math.cos(ang_m) * r * 0.75, y + math.sin(ang_m) * r * 0.75)
    ctx.stroke()
