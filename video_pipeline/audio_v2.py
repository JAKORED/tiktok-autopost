"""Design sonore « FactVibes Nocturne » (22/10/2026).

Ce module complète `make_toon` pour les épisodes storyboardés :
  - banque d'effets sonores **entièrement synthétisés par code** (aucun fichier
    tiers, aucun droit à payer, aucun asset inventé : tout est généré ici) :
    riser, whoosh, stab de révélation, hit de mot-clé, tick de réplique,
    shimmer de fin ;
  - musiques par HUMEUR (curious / tension / light / reveal) qui suivent le
    scénario au lieu d'une boucle identique à chaque épisode ;
  - ambiances discrètes par décor (bourdon de bureau, drone d'usine, néon de
    supermarché, air de salle) ;
  - gestion des SILENCES : les temps de respiration entre deux répliques
    étouffent la musique (la tension vient du vide, pas du bruit) ;
  - mixage : voix 1.0, sfx 0.7, musique duckée sous la voix, ambiance en fond.
    Le niveau final est normalisé par ffmpeg `loudnorm` dans make_toon (inchangé).

L'ancien chemin (`make_toon.mix_audio`) reste intact pour les épisodes sans
storyboard.
"""
import numpy as np

SR = 24000


# ------------------------------------------------------------------ utilitaires
def _n(dur):
    return max(1, int(dur * SR))


def _tt(dur):
    return np.arange(_n(dur)) / SR


def _lowpass(a, fc):
    """Filtre passe-bas un pôle (bruit -> nappe d'ambiance)."""
    x = np.exp(-2 * np.pi * fc / SR)
    out = np.empty_like(a)
    acc = 0.0
    for i in range(len(a)):
        acc = acc * x + a[i] * (1 - x)
        out[i] = acc
    return out


def _fade(a, fin=0.02, fout=0.05):
    n = len(a)
    i, j = int(fin * SR), int(fout * SR)
    if i > 0:
        a[:i] *= np.linspace(0, 1, i)
    if j > 0 and j < n:
        a[-j:] *= np.linspace(1, 0, j)
    return a


def _add(buf, sig, at):
    """Ajoute `sig` dans `buf` à la position `at` (sec), sans débordement."""
    s = int(at * SR)
    if s >= len(buf) or s < -len(sig):
        return
    if s < 0:
        sig = sig[-s:]
        s = 0
    e = min(len(buf), s + len(sig))
    buf[s:e] += sig[: e - s]


# ------------------------------------------------------------------ effets
def riser(dur=1.25):
    """Montée de tension (ouverture, avant une chute)."""
    t = _tt(dur)
    k = (t / dur) ** 2.0
    bruit = np.random.default_rng(7).standard_normal(len(t)).astype(np.float32)
    bruit = _lowpass(bruit, 400 + 5200 * float(k.mean()))
    bruit *= (0.25 + 0.75 * k)
    souffle = np.random.default_rng(8).standard_normal(len(t)).astype(np.float32)
    souffle = _lowpass(souffle, 900) * k * 0.5
    return _fade((bruit * 0.20 + souffle * 0.12).astype(np.float32), 0.05, 0.02)


def whoosh(dur=0.5):
    """Passage rapide (changement de plan, arrivée d'une réplique clé)."""
    t = _tt(dur)
    bruit = np.random.default_rng(3).standard_normal(len(t)).astype(np.float32)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.6
    f = 300 + 2600 * np.sin(np.pi * t / dur)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return _fade((bruit * env * 0.16 + np.sin(ph) * env * 0.05).astype(np.float32), 0.02, 0.06)


def stab(dur=1.0):
    """Impact de révélation : sub + transient, le « moment » du scénario."""
    t = _tt(dur)
    f = 130 * np.exp(-t * 9) + 38
    corps = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4.2) * 0.55
    clic = np.random.default_rng(11).standard_normal(min(len(t), int(0.06 * SR))).astype(np.float32)
    clic *= np.exp(-np.arange(len(clic)) / SR * 60) * 0.35
    out = corps.astype(np.float32)
    out[: len(clic)] += clic
    return _fade(out, 0.001, 0.25)


def hit(dur=0.35):
    """Frappe sèche : mot-clé tapé à l'écran."""
    t = _tt(dur)
    f = 220 * np.exp(-t * 22) + 70
    a = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 13) * 0.4
    bruit = np.random.default_rng(5).standard_normal(len(t)).astype(np.float32)
    bruit *= np.exp(-t * 55) * 0.18
    return _fade((a + bruit).astype(np.float32), 0.001, 0.06)


def tick(dur=0.07):
    """Petit clic discret au début d'une réplique (remplace le pop gratuit)."""
    t = _tt(dur)
    a = np.sin(2 * np.pi * 1750 * t) * np.exp(-t * 90) * 0.10
    return _fade(a.astype(np.float32), 0.001, 0.02)


def shimmer(dur=1.8):
    """Carillon de fin : appelle à rester / à répondre."""
    out = np.zeros(_n(dur), dtype=np.float32)
    for i, f in enumerate((880.0, 1174.7, 1567.98)):
        t = _tt(dur)
        a = np.sin(2 * np.pi * f * t) * np.exp(-t * (2.2 + i * 0.8)) * 0.06
        _add(out, _fade(a.astype(np.float32), 0.005, 0.4), i * 0.11)
    return out


def sub_drop(dur=1.4):
    """Chute de grave sous la révélation (vide soudain)."""
    t = _tt(dur)
    f = 90 * np.exp(-t * 3.0) + 26
    return _fade((np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.4) * 0.30).astype(np.float32),
                 0.01, 0.3)


# ------------------------------------------------------------------ musiques
# Accords (fréquences fondamentales) par humeur. Même logique « par mesures » que
# l'ancienne musique, mais l'humeur suit le scénario.
CHORDS = {
    "curious": [(220.0, 261.6, 329.6), (174.6, 220.0, 261.6), (261.6, 329.6, 392.0), (196.0, 246.9, 293.7)],
    "tension": [(146.8, 220.0, 277.2), (130.8, 196.0, 261.6), (164.8, 246.9, 311.1), (123.5, 185.0, 246.9)],
    "light": [(261.6, 329.6, 392.0), (196.0, 246.9, 293.7), (220.0, 261.6, 329.6), (174.6, 220.0, 261.6)],
    "reveal": [(110.0, 164.8, 220.0), (98.0, 146.8, 196.0), (110.0, 164.8, 220.0), (87.3, 130.8, 174.6)],
}
DRUMS = {"curious": 0.55, "tension": 0.25, "light": 0.8, "reveal": 0.12}


def make_music(dur, mood_at=None, bpm=92):
    """Musique continue dont l'humeur change avec le récit (`mood_at(t)`)."""
    mood_at = mood_at or (lambda t: "curious")
    n = _n(dur)
    t = np.arange(n) / SR
    beat = 60.0 / bpm
    bar = beat * 4
    out = np.zeros(n, dtype=np.float32)
    nbars = int(dur / bar) + 1
    for i in range(nbars):
        s, e = int(i * bar * SR), min(n, int((i + 1) * bar * SR))
        if s >= n:
            break
        mood = mood_at(i * bar)
        accords = CHORDS.get(mood, CHORDS["curious"])
        drums = DRUMS.get(mood, 0.5)
        tt = np.arange(e - s) / SR
        env = np.minimum(1, tt / 0.18) * np.exp(-tt * 0.45)
        for f in accords[i % 4]:
            out[s:e] += ((np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(2 * np.pi * 2 * f * tt))
                         * env * 0.055)
        if mood == "tension":       # pulsation basse qui « marche »
            for b in range(8):
                bs = s + int(b * beat / 2 * SR)
                bl = int(0.16 * SR)
                if bs + bl < n:
                    bt = np.arange(bl) / SR
                    out[bs:bs + bl] += np.sin(2 * np.pi * 55 * bt) * np.exp(-bt * 18) * 0.16 * drums
        if drums > 0.3:             # kick + charleston discrets
            for b in range(4):
                ks = s + int(b * beat * SR)
                kl = int(0.18 * SR)
                if ks + kl < n:
                    kt = np.arange(kl) / SR
                    out[ks:ks + kl] += (np.sin(2 * np.pi * (58 + 60 * np.exp(-kt * 30)) * kt)
                                        * np.exp(-kt * 16) * 0.17 * drums)
                hs = s + int((b + 0.5) * beat * SR)
                hl = int(0.04 * SR)
                if hs + hl < n:
                    rng = np.random.default_rng(b + i)
                    out[hs:hs + hl] += (rng.standard_normal(hl).astype(np.float32)
                                        * np.exp(-np.arange(hl) / SR * 90) * 0.028 * drums)
    return out


# ------------------------------------------------------------------ ambiances
def ambience(dur, set_kind):
    """Nappe de fond très discrète, différente par décor."""
    n = _n(dur)
    out = np.zeros(n, dtype=np.float32)
    rng = np.random.default_rng({"office": 21, "factory": 22, "supermarket": 23,
                                 "stage": 24}.get(set_kind, 25))
    bruit = _lowpass(rng.standard_normal(n).astype(np.float32),
                     {"office": 320, "factory": 200, "supermarket": 480, "stage": 260}
                     .get(set_kind, 300))
    out += bruit * 0.020
    t = np.arange(n) / SR
    if set_kind == "office":          # bourdon de néon + ventilateur
        out += np.sin(2 * np.pi * 100 * t) * 0.010
        out += np.sin(2 * np.pi * 50 * t) * 0.008
    elif set_kind == "factory":       # drone de machines
        out += np.sin(2 * np.pi * 42 * t) * 0.014
        out += np.sin(2 * np.pi * 63 * t + np.sin(t * 0.7)) * 0.006
    elif set_kind == "supermarket":   # néon + caisse lointaine
        out += np.sin(2 * np.pi * 120 * t) * 0.007
    elif set_kind == "stage":         # air de salle
        out += np.sin(2 * np.pi * 58 * t) * 0.005
    return out.astype(np.float32)


# ------------------------------------------------------------------ mixage
def _mood_at(lines, total):
    """Humeur musicale en fonction du scénario (déterministe)."""
    def f(t):
        courante = "curious"
        for ln in lines:
            if t < ln["start"]:
                break
            if ln["start"] <= t < ln["start"] + ln["dur"] + 0.4:
                if ln.get("punch"):
                    courante = "reveal"
                elif ln.get("emo") in ("angry", "worried"):
                    courante = "tension"
                elif ln.get("emo") == "happy":
                    courante = "light"
        if t >= total - 1.9:
            courante = "light"
        return courante
    return f


def _beats(lines, total):
    """Régions de silence (respiration) entre deux répliques."""
    zones = []
    for i in range(len(lines) - 1):
        fin = lines[i]["start"] + lines[i]["dur"]
        debut = lines[i + 1]["start"]
        if debut - fin >= 0.5:
            zones.append((fin, debut))
    return zones


def mix(lines, total, ep, work):
    """Mix complet d'un épisode storyboardé -> work/mix.wav (chemin)."""
    import cinema
    sb = cinema.normaliser(ep, lines, total)
    plans = sb["plans"]

    n = _n(total)
    voice = np.zeros(n, dtype=np.float32)
    sfx = np.zeros(n, dtype=np.float32)
    for ln in lines:
        s = int(ln["start"] * SR)
        voice[s:s + len(ln["audio"])] += ln["audio"][: n - s]
        _add(sfx, tick(), ln["start"])

    # cues liés au récit
    _add(sfx, riser(1.2), 0.05)
    for p in plans:
        if p["line"].get("punch"):
            _add(sfx, whoosh(0.55), max(0.0, p["start"] - 0.42))
            _add(sfx, stab(1.1), p["start"])
            _add(sfx, sub_drop(1.5), p["start"] + 0.05)
            # mot-clé frappé : même règle que le visuel (2 derniers mots)
            mots = p["line"]["text"].split()
            if len(mots) >= 2:
                cible = " ".join(mots[-2:]).strip(".,!?«»").upper()
                for (w, ws, _we) in p["line"]["words"]:
                    if w.strip(".,!?«»").upper() == cible.split()[0]:
                        _add(sfx, hit(0.4), ws)
                        break
    _add(sfx, shimmer(1.9), max(0.0, total - 2.0))

    mood_at = _mood_at(lines, total)
    music = make_music(total, mood_at)
    amb = ambience(total, ep.get("set", "office"))

    # ducking sous la voix + creusement des silences (la tension vient du vide)
    env = np.convolve(np.abs(voice), np.ones(int(0.12 * SR)) / int(0.12 * SR), mode="same")
    duck = 1 - 0.62 * np.clip(env * 9, 0, 1)
    for (a, b) in _beats(lines, total):
        s, e = int(a * SR), int(b * SR)
        marge_s, marge_e = int(0.10 * SR), int(0.18 * SR)
        s2, e2 = max(0, s - marge_s), min(n, e + marge_e)
        fondu = np.ones(e2 - s2, dtype=np.float32)
        lg = len(fondu)
        montee = min(marge_s, lg)
        descente = min(marge_e, lg)
        if montee > 0:
            fondu[:montee] = np.linspace(1, 0.32, montee)
        if descente > 0:
            fondu[-descente:] = np.linspace(0.32, 1, descente)
        if lg > montee + descente:
            fondu[montee:lg - descente] = 0.32
        duck[s2:e2] *= fondu

    fade = np.minimum(1, np.arange(n) / (SR * 0.4)) * np.minimum(1, (n - np.arange(n)) / (SR * 1.4))
    mixed = voice * 1.0 + sfx * 0.75 + (music * duck * 0.9 + amb * 0.5) * fade
    peak = np.max(np.abs(mixed))
    mixed = mixed / peak * 0.89 if peak > 0.89 else mixed

    import wave
    wav = work / "mix.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mixed * 32767).astype(np.int16).tobytes())
    return wav
