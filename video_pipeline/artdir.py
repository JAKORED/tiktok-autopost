"""Direction artistique « FactVibes Nocturne » — système graphique commun.

Objectif du 22/10/2026 : sortir du « plat pastel » (fond uni + 2 personnages + titre
jaune permanent) pour une image **cinématographique** : palette limitée et
reconnaissable, lumière clé + contre-jour, profondeur (parallaxe), texture (grain,
poussières), typographie expressive et lisible sur mobile.

Tout est procédural (aucun asset externe, aucun droit à payer) et déterministe
(même graine = même image) pour rester compatible avec le pipeline automatisé.

Usage :
    import artdir as A
    A.key_light(ctx, A.PALETTES["office"]["key"], t)   # lumière clé
    A.dust(ctx, t, seed=3)                              # poussières en suspension
    A.vignette(ctx, 0.55)                               # vignettage
"""
import math

import cairo

W, H = 1080, 1920
TAU = 2 * math.pi


# ------------------------------------------------------------------ utilitaires
def clamp(x, a=0.0, b=1.0):
    return a if x < a else (b if x > b else x)


def lerp(a, b, k):
    return a + (b - a) * k


def mix(c1, c2, k):
    return tuple(int(round(lerp(c1[i], c2[i], clamp(k)))) for i in range(3))


def rgb(c, a=1.0):
    return (c[0] / 255, c[1] / 255, c[2] / 255, a)


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


# ------------------------------------------------------------------ easing
def linear(k):
    return clamp(k)


def ease_in(k):
    k = clamp(k)
    return k * k


def ease_out(k):
    k = clamp(k)
    return 1 - (1 - k) ** 2


def ease_in_out(k):
    k = clamp(k)
    return 2 * k * k if k < 0.5 else 1 - (-2 * k + 2) ** 2 / 2


def ease_out_cubic(k):
    k = clamp(k)
    return 1 - (1 - k) ** 3


def ease_out_expo(k):
    k = clamp(k)
    return 1.0 if k >= 1 else 1 - 2 ** (-10 * k)


def ease_in_cubic(k):
    k = clamp(k)
    return k ** 3


def spring(k, freq=4.2, damp=5.5):
    """Petit ressort : dépassement contrôlé (~5 %) pour le « rebound », jamais de
    tremblement. borné à [0 .. 1.06] pour rester prévisible sur les échelles."""
    k = clamp(k)
    if k >= 1:
        return 1.0
    return min(1.06, 1 - math.exp(-damp * k) * math.cos(freq * math.pi * k))


def ease(k, name):
    fn = {
        "linear": linear, "in": ease_in, "out": ease_out, "in_out": ease_in_out,
        "out_cubic": ease_out_cubic, "out_expo": ease_out_expo, "in_cubic": ease_in_cubic,
        "spring": spring,
    }.get(name, ease_out_cubic)
    return fn(k)


def ramp(t, start, dur, curve="out_cubic"):
    """Progression 0->1 entre `start` et `start+dur` (sec), avec easing nommé."""
    if dur <= 0:
        return 1.0 if t >= start else 0.0
    return ease((t - start) / dur, curve)


def pulse(t, start, dur=0.5, curve="out_cubic"):
    """Impulsion 0 -> 1 -> 0 (clignement d'accent, frappe, révélation)."""
    k = ramp(t, start, dur, curve)
    if k <= 0 or t > start + dur:
        return 0.0
    return math.sin(k * math.pi) ** 1.4


# ------------------------------------------------------------------ palettes
# Palette limitée par décor : ciel, lumière clé (position + couleur), contre-jour,
# ombre portée, brouillard, poussière, accent typographique. Une seule famille de
# teintes par décor = une identité reconnaissable image par image.
PALETTES = {
    # Bureau de nuit : bleu nuit + lampe de bureau ambre (le décor signature).
    "office": dict(
        sky_top=(16, 24, 44), sky_bottom=(34, 48, 78),
        wall=(28, 38, 62), floor=(20, 26, 40),
        key=dict(x=760, y=560, r=1250, col=(255, 186, 96), inten=0.55),
        rim=(120, 190, 255), shadow=(6, 8, 18), fog=(70, 96, 150),
        accent=(255, 196, 74), dust=(255, 214, 160), window=(90, 140, 210),
    ),
    # Estrade du ministre : rideau grenat + projecteur froid.
    "stage": dict(
        sky_top=(26, 12, 26), sky_bottom=(58, 18, 34),
        wall=(66, 16, 34), floor=(24, 10, 20),
        key=dict(x=540, y=380, r=1400, col=(255, 226, 178), inten=0.6),
        rim=(255, 120, 110), shadow=(12, 4, 12), fog=(120, 40, 60),
        accent=(255, 124, 96), dust=(255, 220, 200), window=(255, 160, 120),
    ),
    # Usine : gris acier + halo sodium.
    "factory": dict(
        sky_top=(12, 18, 24), sky_bottom=(30, 40, 50),
        wall=(30, 40, 50), floor=(16, 22, 28),
        key=dict(x=300, y=420, r=1150, col=(190, 240, 255), inten=0.45),
        rim=(120, 220, 255), shadow=(6, 10, 14), fog=(60, 80, 96),
        accent=(94, 226, 255), dust=(170, 210, 230), window=(120, 190, 220),
    ),
    # Supermarché de nuit : vert-caisse + néon rose.
    "supermarket": dict(
        sky_top=(18, 22, 30), sky_bottom=(38, 44, 56),
        wall=(34, 40, 52), floor=(18, 20, 28),
        key=dict(x=820, y=600, r=1200, col=(255, 190, 210), inten=0.42),
        rim=(140, 255, 210), shadow=(8, 8, 14), fog=(70, 80, 100),
        accent=(255, 120, 180), dust=(220, 230, 255), window=(120, 220, 190),
    ),
    # Version « jour » très claire (compatibilité avec les anciens décors).
    "office_day": dict(
        sky_top=(188, 214, 236), sky_bottom=(222, 232, 242),
        wall=(206, 222, 238), floor=(168, 140, 110),
        key=dict(x=700, y=480, r=1300, col=(255, 240, 200), inten=0.35),
        rim=(255, 255, 255), shadow=(90, 100, 120), fog=(220, 232, 245),
        accent=(255, 214, 64), dust=(255, 255, 255), window=(150, 190, 225),
    ),
    "stage_day": dict(
        sky_top=(36, 44, 96), sky_bottom=(18, 22, 56),
        wall=(60, 24, 60), floor=(24, 20, 40),
        key=dict(x=540, y=420, r=1350, col=(255, 236, 190), inten=0.45),
        rim=(255, 190, 160), shadow=(12, 8, 24), fog=(90, 70, 130),
        accent=(255, 120, 100), dust=(255, 230, 210), window=(180, 150, 220),
    ),
    "factory_day": dict(
        sky_top=(92, 104, 118), sky_bottom=(58, 66, 78),
        wall=(56, 64, 76), floor=(40, 46, 56),
        key=dict(x=340, y=400, r=1200, col=(255, 226, 170), inten=0.38),
        rim=(180, 210, 230), shadow=(20, 24, 30), fog=(110, 120, 135),
        accent=(94, 226, 255), dust=(210, 220, 230), window=(150, 175, 195),
    ),
    "supermarket_day": dict(
        sky_top=(248, 240, 220), sky_bottom=(232, 218, 190),
        wall=(226, 212, 186), floor=(190, 176, 152),
        key=dict(x=800, y=520, r=1250, col=(255, 246, 220), inten=0.32),
        rim=(255, 255, 255), shadow=(120, 110, 96), fog=(244, 236, 220),
        accent=(255, 150, 90), dust=(255, 250, 235), window=(140, 200, 170),
    ),
}

SET_TO_PAL = {"office": "office_day", "stage": "stage_day",
              "factory": "factory_day", "supermarket": "supermarket_day"}


def palette_for(set_kind, mood="night"):
    """Palette d'un décor. `mood` : 'night' (nouvelle direction) ou 'day' (ancien)."""
    if mood == "night":
        return PALETTES.get(set_kind, PALETTES["office"])
    return PALETTES[SET_TO_PAL.get(set_kind, set_kind)]


# ------------------------------------------------------------------ lumière
def key_light(ctx, light, t=None, drift=0.0):
    """Lumière clé radiale (additive). `drift` = léger balancement pour la respirer."""
    dx = math.sin(t * 0.7) * drift if t is not None else 0.0
    g = cairo.RadialGradient(light["x"] + dx, light["y"], light["r"] * 0.12,
                             light["x"] + dx, light["y"], light["r"])
    c = light["col"]
    g.add_color_stop_rgba(0, c[0] / 255, c[1] / 255, c[2] / 255, light["inten"])
    g.add_color_stop_rgba(0.55, c[0] / 255, c[1] / 255, c[2] / 255, light["inten"] * 0.28)
    g.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.set_source(g)
    ctx.paint()


def rim_light(ctx, col, x, y, r, a=0.35):
    """Contre-jour : halo froid derrière la silhouette (sépare le sujet du fond)."""
    g = cairo.RadialGradient(x, y, r * 0.35, x, y, r)
    g.add_color_stop_rgba(0, col[0] / 255, col[1] / 255, col[2] / 255, a)
    g.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.set_source(g)
    ctx.paint()


def atmosphere(ctx, pal, t, strength=0.5):
    """Brume en bas de cadre : fait respirer la profondeur, masque le décor plat."""
    g = cairo.LinearGradient(0, H * 0.45, 0, H)
    c = pal["fog"]
    k = 0.5 + 0.5 * math.sin(t * 0.35)
    g.add_color_stop_rgba(0, c[0] / 255, c[1] / 255, c[2] / 255, 0)
    g.add_color_stop_rgba(1, c[0] / 255, c[1] / 255, c[2] / 255, 0.30 * strength * (0.75 + 0.25 * k))
    ctx.set_source(g)
    ctx.paint()


def vignette(ctx, strength=0.5, cx=None, cy=None):
    cx = W / 2 if cx is None else cx
    cy = H / 2 if cy is None else cy
    g = cairo.RadialGradient(cx, cy, H * 0.30, cx, cy, H * 0.74)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, 0.62 * strength)
    ctx.set_source(g)
    ctx.paint()


def top_gradient(ctx, col, a=0.45, h=430):
    """Assombrissement haut de cadre : les sous-titres et le titre restent lisibles."""
    g = cairo.LinearGradient(0, 0, 0, h)
    g.add_color_stop_rgba(0, col[0] / 255, col[1] / 255, col[2] / 255, a)
    g.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.set_source(g)
    ctx.paint()


def bottom_scrim(ctx, y0, col=(0, 0, 0), a=0.55, h=430):
    g = cairo.LinearGradient(0, y0, 0, y0 + h)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, col[0] / 255, col[1] / 255, col[2] / 255, a)
    ctx.set_source(g)
    ctx.paint()


# ------------------------------------------------------------------ particules
def dust(ctx, t, seed=0, n=26, col=(255, 220, 170), speed=1.0, area=None):
    """Poussières en suspension (mouvement lent, jamais de scintillement rapide)."""
    x0, y0, x1, y1 = area or (0, 0, W, H)
    for i in range(n):
        g = (i * 2654435761 + seed * 97) % 10007 / 10007.0
        g2 = (i * 40503 + seed * 613) % 99991 / 99991.0
        px = x0 + (x1 - x0) * g
        py = y0 + (y1 - y0) * g2
        vitesse = (0.25 + 0.55 * g2) * speed
        py = y0 + ((py - y0 + t * 26 * vitesse) % max(1.0, (y1 - y0)))
        px += math.sin(t * (0.35 + 0.5 * g) + i) * (14 + 22 * g2)
        r = 2.0 + 5.5 * g
        a = (0.10 + 0.26 * g2) * (0.55 + 0.45 * math.sin(t * 0.8 + i * 1.7))
        if a <= 0.01:
            continue
        ctx.set_source_rgba(col[0] / 255, col[1] / 255, col[2] / 255, a)
        ctx.arc(px, py, r, 0, TAU)
        ctx.fill()


def light_shafts(ctx, pal, t, x=None, n=3, a=0.16):
    """Faisceaux lumineux inclinés (fenêtre hors champ) — profondeur immédiate."""
    x = W * 0.72 if x is None else x
    c = pal["key"]["col"]
    ctx.save()
    ctx.translate(x, -200)
    ctx.rotate(math.radians(16))
    for i in range(n):
        décalage = math.sin(t * 0.25 + i) * 18
        g = cairo.LinearGradient(0, 0, 0, H * 1.15)
        g.add_color_stop_rgba(0, c[0] / 255, c[1] / 255, c[2] / 255, a * (1 - i * 0.22))
        g.add_color_stop_rgba(1, 0, 0, 0, 0)
        ctx.set_source(g)
        ctx.rectangle(-260 - i * 190 + décalage, 0, 170 - i * 22, H * 1.3)
        ctx.fill()
    ctx.restore()


def grain(ctx, t, strength=0.05, cell=7):
    """Grain argentique très léger : casse le « vectoriel plat » sans salir l'image."""
    n = 24
    for i in range(n):
        gr = (i * 7919 + int(t * 24) * 104729) % 1000003 / 1000003.0
        gr2 = (i * 65537 + int(t * 24) * 7919) % 999983 / 999983.0
        a = strength * (0.35 + 0.65 * gr)
        val = 1.0 if gr2 > 0.5 else 0.0
        ctx.set_source_rgba(val, val, val, a)
        ctx.arc(gr * W, gr2 * H, cell, 0, TAU)
        ctx.fill()


def flash(ctx, k, col=(255, 255, 255)):
    """Flash de transition (révélation, retournement). k dans [0..1]."""
    if k <= 0:
        return
    ctx.set_source_rgba(col[0] / 255, col[1] / 255, col[2] / 255, clamp(k))
    ctx.paint()


def letterbox(ctx, k, col=(0, 0, 0)):
    """Barres cinémascope (k = 0 -> aucun, 1 -> plein cadre)."""
    k = clamp(k)
    if k <= 0:
        return
    h = int(H * 0.075 * k)
    ctx.set_source_rgba(*rgb(col))
    ctx.rectangle(0, 0, W, h)
    ctx.fill()
    ctx.rectangle(0, H - h, W, h)
    ctx.fill()


# ------------------------------------------------------------------ typographie
def select_font(ctx, family, weight=None):
    import sys
    import os
    if sys.platform.startswith("win"):
        # Impact n'a pas de vrai « bold » : Cairo fabriquerait un faux gras qui
        # épaissit les glyphes SANS élargir leur avance -> lettres fusionnées.
        # On prend la graisse normale : le contour donne le poids visuel.
        ctx.select_font_face(family, cairo.FONT_SLANT_NORMAL,
                             cairo.FONT_WEIGHT_NORMAL if weight is None else weight)
    else:
        ctx.select_font_face(os.environ.get("TOON_FONT", "DejaVu Sans"),
                             cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)


def text_w(ctx, text, size, family="Impact", tracking=0.0):
    select_font(ctx, family)
    ctx.set_font_size(size)
    return ctx.text_extents(text).x_advance + tracking * max(0, len(text) - 1)


def fit_size(ctx, text, max_w, base, min_size=38, family="Impact", tracking=0.0):
    """Réduit la taille jusqu'à tenir dans `max_w` : plus jamais de titre tronqué."""
    size = base
    while size > min_size and text_w(ctx, text, size, family, tracking) > max_w:
        size -= 2
    return size


def outline_text(ctx, text, x, y, size, fill, outline=(0, 0, 0), ow=None,
                 family="Impact", center=True, tracking=None, alpha=1.0):
    """Texte avec contour : lisible sur n'importe quel fond (règle mobile).

    L'interlettrage est PROPORTIONNEL à l'épaisseur du contour : Impact est très
    condensé, un contour épais refermerait autrement les lettres en un bloc illisible.
    Renvoie la largeur totale dessinée (contour + interlettrage compris).
    """
    select_font(ctx, family)
    ctx.set_font_size(size)
    ow = ow if ow is not None else max(4, int(size * 0.13))
    tracking = max(0.0, ow * 0.5) if tracking is None else tracking
    ext = ctx.text_extents(text)
    total = ext.x_advance + tracking * max(0, len(text) - 1)
    px = (x - total / 2) if center else x
    ctx.save()
    ctx.set_source_rgba(*rgb(outline, alpha))
    ctx.set_line_width(ow)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    pos = px
    for ch in text:
        ctx.new_path()
        ctx.move_to(pos, y)
        ctx.text_path(ch)
        ctx.stroke_preserve()
        ctx.set_source_rgba(*rgb(fill, alpha))
        ctx.fill()
        pos += ctx.text_extents(ch).x_advance + tracking
    ctx.restore()
    return total


def title_card(ctx, headline, t, accent, pal, start=0.15, duree_apparition=0.75,
               duree_affichee=2.2, duree_sortie=0.45, y=300):
    """Titre en révélation par masque (balayage) mot à mot, puis sortie par le haut.

    Règle du 22/10 : le titre disparaît après ~2,5 s (l'ancien restait visible en
    permanence et volait le tiers supérieur du cadre).
    """
    if t < start:
        return 1.0
    fin = start + duree_apparition + duree_affichee + duree_sortie
    if t > fin:
        return 0.0
    sort_k = clamp((t - (start + duree_apparition + duree_affichee)) / duree_sortie)
    ctx.save()
    ctx.translate(0, -ease_in_cubic(sort_k) * 190)
    alpha = 1.0 - ease_in(sort_k)
    lignes = [l for l in headline.upper().split("|") if l.strip()]
    ow = 12.0
    track = ow * 0.5
    for i, ln in enumerate(lignes):
        k = ramp(t, start + i * 0.11, duree_apparition, "out_expo")
        if k <= 0:
            continue
        size = fit_size(ctx, ln, W - 210, 92, 46, tracking=track)
        # masque de révélation : on n'affiche qu'une fraction de la largeur
        ctx.save()
        w = text_w(ctx, ln, size, tracking=track)
        ctx.rectangle(W / 2 - w / 2 - 16, y + i * 92 - size * 1.05,
                      w * k + 32, size * 1.45)
        ctx.clip()
        outline_text(ctx, ln, W / 2, y + i * 92, size, accent, ow=ow)
        ctx.restore()
        # soulignement d'accent qui suit la révélation
        if 0.35 < k < 1.0:
            ctx.set_source_rgba(*rgb(pal["rim"], 0.8 * (1 - k)))
            ctx.rectangle(W / 2 - w / 2, y + i * 92 + 14, w * k, 6)
            ctx.fill()
    ctx.restore()      # translation de sortie (save équilibré plus haut)


# ------------------------------------------------------------------ sous-titres
def wrap_words(ctx, words, max_w, size, family="Impact", tracking=0.0):
    """Découpe des mots en 1 à 3 lignes qui tiennent dans la zone sûre mobile."""
    lignes, cur, curw = [], [], 0.0
    for w in words:
        ww = text_w(ctx, w, size, family, tracking)
        if cur and curw + ww + 18 > max_w:
            lignes.append(cur)
            cur, curw = [w], ww
        else:
            cur.append(w)
            curw += ww + 18
    if cur:
        lignes.append(cur)
    return lignes[:3]


def subtitle_block(ctx, mots, t, accent, idx_now=-1, y=1520, size=80,
                   mots_cles=(), scrim=True, alpha=1.0):
    """Sous-titres mobiles : lignes courtes, mot actif accentué, scrim de lisibilité.

    `mots` : [(texte, debut, fin)] — les temps viennent des WordBoundary edge-tts.
    """
    if alpha <= 0.01 or not mots:
        return
    if scrim:
        bottom_scrim(ctx, y - 190, (8, 10, 18), 0.62 * alpha, h=470)
    texte = [m[0].upper() for m in mots]
    OW, TRACK = 11.0, 9.0        # contour + interlettrage (cohérent avec outline_text)
    lignes = wrap_words(ctx, texte, W - 150, size, tracking=TRACK)
    hauteurs = []
    for li, ln in enumerate(lignes):
        lw = sum(text_w(ctx, w, size, tracking=TRACK) + 18 for w in ln) - 18
        hauteurs.append(lw)
    y0 = y - (len(lignes) - 1) * (size + 14) / 2
    cursor = 0
    for li, ln in enumerate(lignes):
        x = (W - hauteurs[li]) / 2
        for w in ln:
            gi = cursor
            actif = (gi == idx_now)
            debut = mots[gi][1]
            k = ramp(t, debut, 0.16, "out_expo")
            taille = size * (1.0 + (0.13 * math.sin(clamp(k) * math.pi) if actif else 0))
            couleur = accent if (actif or w.lower().strip(".,!?«»") in
                                 {m.lower() for m in mots_cles}) else (255, 255, 255)
            if k < 1:
                ctx.save()
                ctx.translate(x + text_w(ctx, w, taille, tracking=TRACK) / 2, y0)
                ctx.translate(0, (1 - ease_out_expo(k)) * 26)
                outline_text(ctx, w, 0, 0, taille, couleur, ow=OW, center=True,
                             tracking=TRACK, alpha=clamp(k * 1.6))
                ctx.restore()
            else:
                outline_text(ctx, w, x + text_w(ctx, w, taille, tracking=TRACK) / 2, y0,
                             taille, couleur, ow=OW, center=True, tracking=TRACK,
                             alpha=alpha)
            x += text_w(ctx, w, taille, tracking=TRACK) + 18
            cursor += 1
        y0 += size + 16


def keyword_slam(ctx, mot, t, start, accent, y=760, size=140):
    """Mot-clé qui « frappe » à l'écran au moment exact de la révélation."""
    k = ramp(t, start, 0.42, "out_expo")
    if k <= 0 or t > start + 1.5:
        return
    s = spring(min(1.0, (t - start) / 0.5))
    alpha = 1.0 if t < start + 1.05 else clamp(1.5 - (t - start))
    ctx.save()
    ctx.translate(W / 2, y)
    ctx.scale(0.35 + 0.65 * s, 0.35 + 0.65 * s)
    outline_text(ctx, mot.upper(), 0, 0, size, accent, ow=18, alpha=alpha)
    ctx.restore()
