#!/usr/bin/env python3
"""FactVibes — Orchestrateur de publication automatique 24/7.

Pourquoi ce fichier existe (09/10/2026)
--------------------------------------
Le compte est resté MUET 6 jours (dernière publication le 03/10 23:41 UTC). Deux
causes, toutes deux structurelles :

1. **Rien ne lançait le scheduler.** Aucun processus Python ne tournait, et il n'existe
   aucune tâche dans le Planificateur de tâches Windows (le HANDOFF affirmait le
   contraire). Un scheduler 24/7 qui n'est jamais démarré ne poste rien.
2. **Le scheduler ne rattrape pas la matinée.** `main.py run_scheduler` ne publie qu'un
   créneau si son horaire UTC est DÉJÀ dépassé. Or les créneaux sont 17:00-19:00 UTC :
   à 9h du matin, aucun n'est dépassé, donc rien ne part — même après plusieurs jours
   d'arrêt. Le rattrapage ne se déclenche qu'à partir de 17:00 UTC.

Ce script corrige les deux : boucle unique, relancement de Chrome, production du
tampon, publication au bon moment, et compte rendu quotidien. Il est pensé pour être
lancé par le Planificateur de tâches Windows (au démarrage + toutes les 15 min).

Le doublon reste impossible : toute la logique anti-doublon vit dans
`studio.publish_next` (signature de script, famille de scénario, empreinte visuelle,
vérification de la liste Contenu, intervalle minimum, verrou de publication). Ce
fichier ne fait que décider QUAND appeler cette fonction.

Usage :
  python auto_poster.py              # boucle 24/7 (mode normal)
  python auto_poster.py --once       # un seul tour puis on sort
  python auto_poster.py --post       # tente un post maintenant (respecte les gardes)
  python auto_poster.py --status     # état de la programmation
"""
import argparse
import json
import os
import subprocess
import sys
import time
import traceback
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "video_pipeline"))

# La console Windows est en cp1252 : le moindre caractère hors cp1252 (« → », « … »
# suivant la police) lève UnicodeEncodeError et tue le tour de publication EN COURS.
# On force l'UTF-8 avec remplacement sur tous les flux, ce qui couvre aussi les `print`
# de studio.py et publish_studio.py importés plus bas. Voir _console_safe() pour le journal.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

import studio  # noqa: E402

LOG_DIR = ROOT / "logs"
HEARTBEAT = LOG_DIR / "auto_poster_heartbeat.json"
INSTANCE_LOCK = ROOT / "videos" / ".autoposter.lock"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROFILE = ROOT / "config" / "chrome_tiktok_profile"
UPLOAD_URL = "https://www.tiktok.com/tiktokstudio/upload"

# Arrêt du programme si le patron l'a demandé (le watchdog Windows le vérifie).
STOP_FILE = ROOT / "videos" / ".stop_autoposter"


# ------------------------------------------------------------------ logs
def _console_safe(texte):
    """Version affichable en console Windows (cp1252) sans jamais lever.

    09/10/2026 — PIÈGE QUI A COÛTÉ 6 JOURS DE SILENCE. Un `log("→ publication")` a levé
    `UnicodeEncodeError: 'charmap' codec can't encode character '→'` : la console du
    processus (lancé par le superviseur, sans PYTHONIOENCODING) est en cp1252. L'exception
    partait DANS le tour, AVANT l'envoi, et le superviseur relançait aussitôt le process,
    qui plantait au même endroit — une boucle de crash toutes les 60 s, sans jamais poster.
    Le journal écrit ici ne doit donc jamais pouvoir tuer la publication.
    """
    return (texte
            .encode("cp1252", "replace").decode("cp1252")
            .encode("ascii", "replace").decode("ascii"))


def log(msg, level="INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    try:
        print(_console_safe(line), flush=True)
    except Exception:
        pass
    try:
        LOG_DIR.mkdir(exist_ok=True)
        path = LOG_DIR / f"auto_poster_{datetime.now():%Y%m%d}.log"
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def heartbeat(state, detail=""):
    HB = {
        "last_beat": datetime.now().isoformat(),
        "state": state,
        "detail": str(detail)[:300],
        "pid": os.getpid(),
    }
    try:
        HEARTBEAT.write_text(json.dumps(HB, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass


def config():
    return json.loads((ROOT / "config.json").read_text(encoding="utf-8"))


# ------------------------------------------------------------------ Chrome
def chrome_vif():
    """Le port de debug 9222 répond-il vraiment ?

    Le 09/10/2026 le piège : `netstat` annonçait 9222 en LISTENING, mais toute
    connexion était REFUSÉE — un Chrome lancé le 30/09 était figé. C'est pour ça
    qu'on teste une VRAIE requête HTTP et pas la simple présence du port.
    """
    try:
        with urllib.request.urlopen("http://127.0.0.1:9222/json/version", timeout=5) as r:
            return r.status == 200
    except Exception:
        return False


def relancer_chrome():
    """(Re)lance Chrome de debug avec le profil TikTok et attend le port."""
    if not os.path.exists(CHROME):
        log(f"Chrome introuvable : {CHROME}", "ERROR")
        return False
    log("Chrome de debug injoignable -> relancement avec le profil TikTok", "WARN")
    try:
        subprocess.Popen(
            [CHROME, "--remote-debugging-port=9222", f"--user-data-dir={PROFILE}",
             "--window-size=1250,980", "--no-first-run", "--no-default-browser-check",
             UPLOAD_URL],
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except Exception as exc:
        log(f"relancement Chrome impossible : {exc}", "ERROR")
        return False
    for _ in range(45):                      # 90 s : Chrome met 15-25 s à ouvrir 9222
        if chrome_vif():
            log("Chrome relancé, port 9222 répond")
            return True
        time.sleep(2)
    log("Chrome toujours muet sur 9222 après 90 s", "ERROR")
    return False


def chrome_sur_la_bonne_page():
    """Ouvre l'onglet d'upload si aucun onglet TikTok Studio n'est ouvert.

    Un formulaire d'upload laissé ouvert peut partir tout seul (02/10/2026, auto_049
    publiée sans aucun clic). On remet donc toujours la page dans un état connu.
    """
    try:
        with urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=5) as r:
            onglets = json.loads(r.read().decode("utf-8"))
    except Exception:
        return
    for t in onglets:
        if t.get("type") == "page" and "tiktokstudio" in (t.get("url") or ""):
            return
    log("Aucun onglet TikTok Studio ouvert -> ouverture de la page d'upload")
    try:
        import publish_studio
        publish_studio.ensure_chrome()
    except Exception as exc:
        log(f"ouverture de la page TikTok Studio impossible : {exc}", "WARN")


# ------------------------------------------------------------------ file
def compte_rendu_jour(cfg):
    q = studio.load_queue()
    auj = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    postes = [e for e in q if e.get("state") in ("PUBLISHED", "PUBLISHED_SUSPECT")
              and str(e.get("published_at_utc") or "").startswith(auj)]
    ready = sum(1 for e in q if e["state"] == "READY")
    dernier = studio.last_published_dt(q)
    return {
        "posts_aujourdhui": len(postes),
        "ready": ready,
        "dernier_post_utc": dernier.isoformat() if dernier else None,
        "heures_depuis_dernier_post": (
            round((datetime.now(timezone.utc) - dernier).total_seconds() / 3600.0, 1)
            if dernier else None),
    }


def produire_si_besoin(cfg, min_ready=3):
    """Complète le tampon si la file de publication s'assèche.

    Plafonné par le ledger quotidien (daily_render_cap) : le rendu est CPU local,
    gratuit, mais on ne veut pas non plus remplir le disque la nuit.
    """
    q = studio.load_queue()
    ready = sum(1 for e in q if e["state"] == "READY")
    if ready >= min_ready:
        return []
    cap = int(cfg.get("production", {}).get("daily_render_cap", 5))
    reste = max(0, cap - studio.used_today("renders"))
    if reste <= 0:
        log(f"tampon à {ready} vidéos, budget de rendu du jour épuisé ({cap})", "WARN")
        return []
    log(f"tampon bas ({ready} prêtes) -> production de {reste} épisode(s)")
    try:
        faits = studio.ensure_buffer(cfg, target=min_ready + reste)
        if faits:
            log(f"produit : {faits}")
        else:
            log("aucun épisode neuf disponible : la BANQUE est épuisée "
                "(il faut ajouter des scénarios dans video_pipeline/factory.py)", "WARN")
        return faits
    except Exception as exc:
        log(f"production échouée : {exc}", "ERROR")
        return []


# ------------------------------------------------------------------ décision
def creneaux_utc(cfg):
    sch = cfg.get("posting_schedule", {})
    return list(sch.get("post_times_utc", ["17:00", "17:30", "18:00", "18:30", "19:00"]))


def garanties_horaires(cfg):
    """[(heure locale, nb de posts minimum attendus à cette heure-là)]."""
    return [(h, int(n)) for h, n in
            cfg.get("recovery", {}).get("min_posts_by_hour_local", [])]


def a_il_faut_publier(cfg):
    """Décide s'il est temps de poster. Renvoie (boolien, raison).

    Quatre règles, dans l'ordre :

    * **plafond** — jamais plus de `posts_per_day` par jour (jour UTC) ;
    * **garantie horaire** — le patron exige un minimum de posts à une heure donnée
      (`min_posts_by_hour_local`). Ordre du 09/10/2026 : « aujourd'hui tu dois poster
      au moins trois ». Sans ça, la première publication de la journée ne pouvait
      partir qu'à 17:00 UTC ;
    * **rattrapage** — le compte est muet depuis plus de `recovery_after_hours` et rien
      n'est parti aujourd'hui : on relance tout de suite. C'est le trou du 03→09/10,
      où un scheduler en attente de 17:00 laissait un compte mort de silence repartir
      pour 6 jours de plus ;
    * **créneau dépassé** — rattrapage normal si la machine a redémarré après un créneau.

    Dans tous les cas l'intervalle minimum entre deux posts reste appliqué par
    `studio.publish_next` : la cadence de 30 minutes du patron est intangible.
    """
    sch = cfg.get("posting_schedule", {})
    cap = int(sch.get("posts_per_day", 5))
    etat = compte_rendu_jour(cfg)
    faits = etat["posts_aujourdhui"]
    if faits >= cap:
        return False, f"plafond du jour atteint ({faits}/{cap})"

    now = datetime.now().astimezone()
    now_utc = now.astimezone(timezone.utc)

    # 1. Garantie horaire du patron : « au moins N posts à telle heure ».
    for heure, mini in garanties_horaires(cfg):
        h, m = (int(x) for x in heure.split(":"))
        if now >= now.replace(hour=h, minute=m, second=0, microsecond=0) and faits < mini:
            return True, (f"GARANTIE HORAIRE : {faits} post(s) à {heure} alors que le "
                          f"minimum attendu est {mini}")

    # 2. Rattrapage : le compte est-il mort de silence ?
    heures = etat["heures_depuis_dernier_post"]
    if faits == 0 and heures is not None:
        seuil = float(cfg.get("recovery", {}).get("recovery_after_hours", 20))
        if heures >= seuil:
            return True, (f"RATTRAPAGE : {heures} h sans publication "
                          f"(seuil {seuil:.0f} h) -> on relance tout de suite")

    # 3. Créneau planifié déjà dépassé ?
    for pt in creneaux_utc(cfg):
        h, m = (int(x) for x in pt.split(":"))
        slot = now_utc.replace(hour=h, minute=m, second=0, microsecond=0)
        if slot <= now_utc:
            return True, f"créneau {pt} UTC dépassé et le jour n'est pas à quota"
    return False, (f"prochain créneau {creneaux_utc(cfg)[0]} UTC "
                   f"(pas de post en attente aujourd'hui)")


def poster(cfg):
    """Un envoi, encadré par tous les gardes anti-doublon de `studio`."""
    try:
        res = studio.publish_next(cfg)
    except SystemExit as exc:
        log(f"publication interrompue : {exc}", "ERROR")
        return "failed"
    except Exception as exc:
        log(f"publication en erreur : {exc.__class__.__name__}: {exc}", "ERROR")
        log(traceback.format_exc(), "ERROR")
        return "failed"
    libelle = {
        "published": "PUBLIÉE", "already": "déjà en ligne (aucun envoi)",
        "processing": "en traitement", "wait": "intervalle minimum non écoulé",
        "busy": "autre publication en cours", "failed": "ÉCHEC",
        None: "rien à publier (file vide ou tout bloqué par les anti-doublons)",
    }.get(res, str(res))
    log(f"résultat de l'envoi : {libelle}")
    return res


# ------------------------------------------------------------------ boucle
def _pid_vivant(pid):
    """Le processus existe-t-il encore ? (sans jamais le tuer).

    `os.kill(pid, 0)` est INTERDIT ici : sous Windows, CPython traduit tout signal autre
    que CTRL_C/CTRL_BREAK par `TerminateProcess`. On interroge l'API Win32.
    """
    try:
        import ctypes
        from ctypes import wintypes
    except ImportError:
        return True
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    STILL_ACTIVE = 259
    k32 = ctypes.windll.kernel32
    h = k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))
    if not h:
        return False
    code = wintypes.DWORD()
    ok = k32.GetExitCodeProcess(h, ctypes.byref(code))
    k32.CloseHandle(h)
    return bool(ok) and code.value == STILL_ACTIVE


def _pid_dans_verrou():
    """PID écrit dans le verrou, ou None."""
    try:
        return int(INSTANCE_LOCK.read_text(encoding="utf-8").split("pid=")[1].split()[0])
    except Exception:
        return None


def instance_unique():
    """Une seule instance à la fois : deux orchestrateurs se marcheraient dessus.

    Le Planificateur de tâches / le superviseur relancent ce script alors que la boucle
    précédente tourne déjà. On ne se fie donc PAS à l'âge du verrou seul : un processus
    tué laisse un verrou neuf, et le relanceur repartait jamais (vu le 09/10/2026).
    On exige que le PID inscrit soit ENCORE VIVANT.
    """
    pid = _pid_dans_verrou()
    if pid is not None and _pid_vivant(pid):
        return False
    INSTANCE_LOCK.unlink(missing_ok=True)     # verrou orphelin : on prend la place
    try:
        fd = os.open(str(INSTANCE_LOCK), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False                        # une autre instance a gagné la course
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(f"pid={os.getpid()} debut={datetime.now().isoformat()}")
    return True


def rafraichir_verrou():
    """Garde le verrou « frais » pour que le watchdog ne prenne pas la place."""
    try:
        os.utime(str(INSTANCE_LOCK), None)
    except OSError:
        pass


def reconcilier_une_fois_par_jour(cfg):
    """Aligne la base sur le compte TikTok, une fois par jour.

    09/10/2026 — la base et le compte se étaient désynchronisés (auto_069 réellement en
    ligne mais notée FAILED, auto_070 notée PUBLISHED alors que c'était elle qui manquait).
    Cette désynchronisation est la cause historique des doublons : une vidéo en ligne
    reste relancée parce que la base la croit partie, une vidéo jamais partie est
    Declaree publiée et ne le sera jamais.

    On ne le fait qu'une fois par jour, et seulement s'il reste une vidéo prête : la
    lecture de Contenu coûte uneMinute de navigateur.
    """
    jour = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    marqueur = LOG_DIR / f"reconcilie_{jour}.flag"
    if marqueur.exists():
        return []
    q = studio.load_queue()
    if not any(e["state"] == "READY" for e in q):
        return []                      # rien à poster : inutile de solliciter TikTok
    log("réconciliation quotidienne base <-> compte TikTok")
    try:
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "reconcilier.py"),
                            "--appliquer"], cwd=str(ROOT), capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=300)
        for ligne in (r.stdout or "").splitlines():
            if "écrit" in ligne or "identifiée" in ligne or "Aucune correction" in ligne:
                log(f"[reconciliation] {ligne.strip()}")
        if r.returncode != 0:
            log(f"réconciliation en échec (code {r.returncode}) : {(r.stderr or '')[:200]}",
                "WARN")
            return []
    except Exception as exc:
        log(f"réconciliation impossible : {exc}", "WARN")
        return []
    marqueur.write_text(datetime.now().isoformat(), encoding="utf-8")
    return []


def tour(cfg, cycle=0):
    """Un tour complet : santé Chrome, réconciliation, production, publication."""
    rafraichir_verrou()
    if STOP_FILE.exists():
        log("fichier d'arrêt présent -> l'orchestrateur s'arrête")
        STOP_FILE.unlink(missing_ok=True)
        return False

    if not chrome_vif():
        if not relancer_chrome():
            log("pas de Chrome : publication impossible ce tour", "ERROR")
            heartbeat("no_chrome", "port 9222 muet")
            return True
    chrome_sur_la_bonne_page()

    if cycle <= 2:                       # les premiers tours : base alignée sur le compte
        reconcilier_une_fois_par_jour(cfg)

    produire_si_besoin(cfg)

    publier, raison = a_il_faut_publier(cfg)
    if publier:
        log(f"→ publication ({raison})")
        res = poster(cfg)
        etat = compte_rendu_jour(cfg)
        heartbeat("post_" + str(res),
                  f"{raison} | posts aujourd'hui: {etat['posts_aujourdhui']}")
        log(f"état du jour : {json.dumps(etat, ensure_ascii=False)}")
        if res in ("failed", None):
            time.sleep(120)                  # on laisse respirer TikTok avant de réessayer
    else:
        etat = compte_rendu_jour(cfg)
        heartbeat("attente", f"{raison} | posts aujourd'hui: {etat['posts_aujourdhui']}")
        if cycle % 10 == 0:
            log(f"en attente — {raison} | posts aujourd'hui: {etat['posts_aujourdhui']} "
                f"| tampon: {etat['ready']}")
    return True


def rapport(cfg):
    etat = compte_rendu_jour(cfg)
    cap = int(cfg.get("posting_schedule", {}).get("posts_per_day", 5))
    print("=== Programmation automatique FactVibes ===")
    print(f"Créneaux (UTC)   : {', '.join(creneaux_utc(cfg))}")
    print(f"Par jour         : {cap} (intervalle min "
          f"{cfg.get('posting_schedule', {}).get('min_minutes_between_posts', 30)} min)")
    print(f"Posts aujourd'hui: {etat['posts_aujourdhui']}/{cap}")
    print(f"Tampon READY     : {etat['ready']}")
    print(f"Dernier post     : {etat['dernier_post_utc']}")
    print(f"Chrome 9222      : {'OK' if chrome_vif() else 'MUET (sera relancé)'}")
    publier, raison = a_il_faut_publier(cfg)
    print(f"Décision         : {'PUBLIER' if publier else 'attendre'} — {raison}")
    if HEARTBEAT.exists():
        print(f"Cœur vivant      : {HEARTBEAT.read_text(encoding='utf-8').strip()[:160]}")


def main():
    ap = argparse.ArgumentParser(description="Publication automatique FactVibes")
    ap.add_argument("--once", action="store_true", help="un seul tour puis sortie")
    ap.add_argument("--post", action="store_true", help="tente un post maintenant")
    ap.add_argument("--status", action="store_true", help="état de la programmation")
    args = ap.parse_args()

    cfg = config()

    if args.status:
        rapport(cfg)
        return
    if args.post:
        if not chrome_vif():
            relancer_chrome()
        poster(cfg)
        rapport(cfg)
        return
    if args.once:
        tour(cfg, cycle=0)
        return

    if not instance_unique():
        log("une instance est DÉJÀ en cours -> on sort (pas de doublon de pilotage)")
        return
    log("=== FactVibes AutoPoster démarré (24/7) ===")
    log(f"Créneaux UTC : {', '.join(creneaux_utc(cfg))} | "
        f"{cfg.get('posting_schedule', {}).get('posts_per_day', 5)} posts/jour")
    cycle = 0
    try:
        while True:
            cycle += 1
            try:
                if not tour(cfg, cycle=cycle):
                    break
            except Exception as exc:            # aucun tour ne doit tuer l'orchestrateur
                log(f"erreur inattendue dans le tour : {exc}", "ERROR")
                log(traceback.format_exc(), "ERROR")
                heartbeat("erreur", str(exc))
            time.sleep(120)
    except KeyboardInterrupt:
        log("arrêt demandé")
    finally:
        INSTANCE_LOCK.unlink(missing_ok=True)
        heartbeat("arrete", "arrêt propre")


if __name__ == "__main__":
    main()