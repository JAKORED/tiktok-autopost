"""Studio de production FactVibes — ligne « dessins animés » 4-5/jour, gratuit, sans quota.

Rôle : garantir QUE du contenu neuf tombe chaque jour et qu'il soit publié, sans jamais
dépasser la garde quotidienne de crédits (LEDGER). Le moteur local (pycairo + edge-tts +
ffmpeg) n'utilise AUCUN crédit externe : il peut tourner sans limite. Les appels externes
optionnels (décors IA, TTS de secours) sont eux plafonnés par jour dans le ledger.

Usage :
  python video_pipeline/studio.py bank            # inventaire (bank / ready / publié)
  python video_pipeline/studio.py produce [N]     # rend N épisodes neufs (défaut budget du jour)
  python video_pipeline/studio.py ensure [N]      # remplir le tampon à N vidéos prêtes
  python video_pipeline/studio.py publish [id]    # publie le plus ancien READY (API, puis Studio)
  python video_pipeline/studio.py publish --verify# reconfirme les SCHEDULED en attente
  python video_pipeline/studio.py status          # état de la file de publication
"""
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "video_pipeline"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

VIDEOS = ROOT / "videos"
READY_DIR = VIDEOS / "ready"
META_DIR = VIDEOS / "metadata"
QUEUE_FILE = VIDEOS / "queue.json"
LEDGER_FILE = ROOT / "logs" / "studio_ledger.json"

from toon_scripts import EPISODES, VOICES, GENERIC_TAGS  # noqa: E402

# Clusters de hashtags tournés (3-5 max, 3 couches : broad + format + niche, jamais
# #fyp/#viral/#pourtoi qui sont du poids mort — veille 20/09/2026). Le tag de série
# #FactVibesToons est ajouté par build_caption.
CAPTION_CLUSTERS = [
    ["#humour", "#dessinanime", "#cartoon"],
    ["#dessinanime", "#humourfrancais", "#storytime"],
    ["#humour", "#animation", "#quotidien"],
    ["#dessinanime", "#cartoon", "#pov"],
    ["#humour", "#animation2d", "#societe"],
]
BRAND_TAG = "#FactVibesToons"

# Comment-bait mesuré : une question en légende = +26 % de commentaires (Metricool 2026).
# Jamais de « like si ... » (−60 % de likes). Tournée selon l'épisode.
CAPTION_QUESTIONS = [
    "Qui a déjà vécu ça ?",
    "Vous en pensez quoi, vous ?",
    "T'es plutôt pour ou contre lui ?",
    "Ça vous arrive à vous aussi ?",
    "Et vous, vous auriez fait quoi ?",
]


def now_utc():
    return datetime.now(timezone.utc).isoformat()


def today_str():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ------------------------------------------------------------------ banque
def bank():
    """Tous les épisodes rendables : scripts originaux, sans décor IA externe."""
    return [e for e in EPISODES if e.get("id") and not e.get("bg_image")]


def produced_ids():
    ids, produced = set(), set()
    if META_DIR.exists():
        ids |= {p.stem for p in META_DIR.glob("*.json")}
    queue = load_queue()
    produced = {e["video_id"] for e in queue}
    return ids | produced


# ------------------------------------------------------------------ ledger
def load_ledger():
    if LEDGER_FILE.exists():
        return json.loads(LEDGER_FILE.read_text(encoding="utf-8"))
    return {}


def save_ledger(led):
    LEDGER_FILE.parent.mkdir(exist_ok=True)
    LEDGER_FILE.write_text(json.dumps(led, ensure_ascii=False, indent=2), encoding="utf-8")


def log_render(ep_id):
    led = load_ledger()
    day = led.setdefault(today_str(), {"renders": [], "bg_images": 0, "tts_calls": 0})
    if ep_id not in day["renders"]:
        day["renders"].append(ep_id)
    save_ledger(led)


def used_today(kind="renders"):
    return len(load_ledger().get(today_str(), {}).get(kind, []))


# ------------------------------------------------------------------ file
def load_queue():
    if QUEUE_FILE.exists():
        return json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
    return []


def save_queue(queue):
    QUEUE_FILE.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")


def find_in_queue(queue, video_id):
    return next((e for e in queue if e["video_id"] == video_id), None)


def sync_ready_to_queue():
    """Ajoute à la file toute vidéo prête sans entrée (fruit de make_toon/build)."""
    queue = load_queue()
    changed = False
    for meta_path in sorted(META_DIR.glob("*.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        vid = meta.get("video_id")
        if not vid or find_in_queue(queue, vid) or not (READY_DIR / f"{vid}.mp4").exists():
            continue
        queue.append({
            "video_id": vid, "state": "READY", "file": f"ready/{vid}.mp4",
            "caption": meta.get("caption", ""), "hashtags": meta.get("hashtags", []),
            "created_utc": now_utc(), "scheduled_for_utc": None, "publish_id": None,
            "published_at_utc": None, "published_evidence": None, "error": None,
        })
        changed = True
    if changed:
        save_queue(queue)
    return queue


# ------------------------------------------------------------------ captions
def build_caption(ep):
    """Légende 2026 : hook + titre + identifiant + QUESTION (comment-bait) + hashtags.

    L'identifiant du fichier est dans la légende à dessein : c'est la seule trace fiable
    qui relie une publication TikTok à SON fichier. Le 01/10/2026 on ne pouvait plus dire
    quelle des vidéos en ligne était un doublon ; avec « auto_041 » dans le texte, la
    lecture de la liste Contenu tranche sans ambiguïté.
    """
    cluster = CAPTION_CLUSTERS[ep["ep"] % len(CAPTION_CLUSTERS)]
    question = CAPTION_QUESTIONS[ep["ep"] % len(CAPTION_QUESTIONS)]
    hook = ep["headline"].replace("|", " ")
    vid = ep.get("id") or ""
    text = (f"{hook} — {ep['title']} (épisode {ep['ep']}"
            f"{' · ' + vid if vid else ''}). "
            f"{question} {' '.join(cluster)} {BRAND_TAG}")
    return text.strip()


# ------------------------------------------------------------------ production
def render_new(config, count=None, ep_ids=None):
    """Rend des épisodes neufs, dans la limite du budget journalier (ledger).

    - ep_ids : commande explicite du patron (ex. tests) : ids exacts rendus, budget ignoré,
      mais chaque rendu reste journalisé dans le ledger.
    - count  : nombre souhaité, plafonné par daily_render_cap - déjà_rendus_du_jour.
    """
    prod = config.get("production", {})
    cap = int(prod.get("daily_render_cap", 5))
    if ep_ids:
        wanted = [e for e in bank() if e["id"] in ep_ids and e["id"] not in produced_ids()]
    else:
        if count is None:
            count = cap
        allowed = max(0, min(count, cap - used_today("renders")))
        wanted = [e for e in bank() if e["id"] not in produced_ids()][:allowed]
    os.makedirs(READY_DIR, exist_ok=True)
    done = []
    import make_toon
    for ep in wanted:
        print(f"[studio] rendu {ep['id']} (budget jour {used_today('renders')}/{cap})", flush=True)
        try:
            make_toon.build(ep["id"])
        except Exception as exc:
            print(f"[studio] ÉCHEC {ep['id']}: {exc}", flush=True)
            continue
        log_render(ep["id"])
        done.append(ep["id"])
    sync_ready_to_queue()
    return done


def ensure_buffer(config, target=None):
    """Remplit le tampon de vidéos prêtes (READY) à `target` (défaut config.min_buffer)."""
    prod = config.get("production", {})
    target = int(target if target is not None else prod.get("min_buffer", 8))
    sync_ready_to_queue()
    queue = load_queue()
    ready = sum(1 for e in queue if e["state"] == "READY" or e.get("publish_id"))
    want = max(0, target - ready)
    if want == 0:
        return []
    cap = int(prod.get("daily_render_cap", 5))
    return render_new(config, count=min(want, cap))


# ------------------------------------------------------------------ publication
def _agent(config):
    from agents.tiktok_publisher import TikTokPublisherAgent
    return TikTokPublisherAgent(config)


def signature(ep):
    """Empreinte d'un scénario = texte normalisé des répliques (détection de doublon)."""
    return "|".join(l["text"].strip().lower() for l in ep["lines"])


def family_key(ep):
    """Identifiant du SCÉNARIO (et non de la variante).

    La factory produit 4 variantes par scénario : même `headline`, même décor, mêmes
    6 répliques sur 7 — visuellement c'est la MÊME vidéo. Le 30/09/2026 auto_025 puis
    auto_026 sont partis ainsi (« même vidéo publiée une demi-heure après »). On compare
    donc le headline, qui est commun aux 4 variantes.
    """
    h = (ep.get("headline") or "").strip().lower()
    if h:
        return h
    t = (ep.get("title") or "").split("(")[0]
    return t.strip().lower()


def already_published_scripts(queue):
    """Signatures des épisodes déjà sortis (PUBLISHED) ou marqués doublon."""
    sigs = set()
    for e in queue:
        if e.get("state") not in ("PUBLISHED", "FAILED", "SCHEDULED"):
            continue
        mp = META_DIR / f"{e['video_id']}.json"
        if mp.exists():
            lines = json.loads(mp.read_text(encoding="utf-8")).get("lines", [])
            sigs.add("|".join(l["text"].strip().lower() for l in lines))
    return sigs


# Seuil de « doublon visuel » : même décor + mêmes personnages + mêmes répliques
# donnent 0.000-0.01 de distance d'empreinte, alors que deux épisodes réellement
# différents les plus proches mesurés sont à 0.0703 (auto_002 / auto_049). On place
# le seuil entre les deux (0.035) : large marge des deux côtés.
VISUAL_DUP_THRESHOLD = 0.035


def _mp4_of(video_id):
    for sub in ("published", "ready"):
        p = VIDEOS / sub / f"{video_id}.mp4"
        if p.exists():
            return p
    return None


def deja_publie_sur_tiktok(video_id, caption=None):
    """Interroge la liste Contenu du compte : cette vidéo y est-elle déjà ?

    Retourne (True, extrait) si on la trouve, (False, "") sinon. Tout échec technique
    (Chrome fermé, page lente) renvoie False : on n'empêche jamais une publication
    parce que la vérification est indisponible — le garde de scénario et d'empreinte
    restent, eux, hors ligne et fiables.
    """
    try:
        import publish_studio
    except Exception:
        return False, ""
    try:
        trouve, extrait = publish_studio.present_dans_contenu(video_id, caption)
    except Exception as exc:
        print(f"[publier] vérification Contenu impossible ({exc.__class__.__name__}) "
              f"— on continue", flush=True)
        return False, ""
    if trouve:
        print(f"[publier] {video_id} retrouvé dans Contenu : {extrait[:70]}", flush=True)
    return trouve, extrait


def visual_duplicate_of(video_id, against_ids, threshold=VISUAL_DUP_THRESHOLD):
    """Cherche une vidéo VISUELLEMENT identique à `video_id` parmi `against_ids`.

    Le contrôle par scénario (`family_key`) ne suffit pas : auto_001 et auto_002 ont été
    publiés alors que leurs rendus sont indiscernables (distance 0.0078) — deux scénarios
    différents qui se rendent pareil. C'est le doublon que le patron voit. On compare donc
    les images, pas le texte.
    """
    import fingerprint

    src = _mp4_of(video_id)
    if src is None:
        return None
    h_src = fingerprint.cached_hash(src)
    if not h_src:
        return None  # fichier illisible : on ne bloque pas (le nom du scénario protege)
    for other in against_ids:
        if other == video_id:
            continue
        p = _mp4_of(other)
        if p is None:
            continue
        dist = fingerprint.distance(h_src, fingerprint.cached_hash(p))
        if dist < threshold:
            return other, dist
    return None


def already_published_families(queue):
    """Scénarios déjà sortis : un même scénario ne doit JAMAIS repartir (ORDRE G)."""
    eps = {e["id"]: e for e in bank()}
    fams = set()
    for e in queue:
        if e.get("state") not in ("PUBLISHED", "SCHEDULED", "PUBLISHED_SUSPECT"):
            continue
        ep = eps.get(e["video_id"])
        if ep:
            fams.add(family_key(ep))
    return fams


def _api_status(agent, publish_id):
    import requests
    r = requests.post(
        f"{agent.TIKTOK_API_BASE}/post/publish/status/fetch/",
        headers={"Authorization": f"Bearer {agent.access_token}",
                 "Content-Type": "application/json; charset=UTF-8"},
        json={"publish_id": publish_id}, timeout=15)
    return r.json().get("data", {}) if r.ok else {}


def last_published_dt(queue=None):
    """Date/heure (UTC aware) de la dernière publication, ou None.

    Les états PUBLISHED_SUSPECT comptent aussi : le clic « Publier » a été fait, donc
    la vidéo est peut-être en ligne. Ignorer ces cas ferait partir deux posts à 5 min
    d'intervalle — exactement le doublon que le patron a signalé.
    """
    if queue is None:
        queue = load_queue()
    times = []
    for e in queue:
        ts = e.get("published_at_utc")
        if e.get("state") in ("PUBLISHED", "PUBLISHED_SUSPECT") and ts:
            try:
                times.append(datetime.fromisoformat(ts))
            except ValueError:
                pass
    return max(times) if times else None


def publish_next(config, video_id=None, allow_studio=None, force=False):
    """Publie le plus ancien READY via TikTok Studio navigateur (QR) ou API.

    Garde-fous :
    - jamais de doublon (signature de script comparée aux vidéos déjà sorties) ;
    - délai minimum entre deux publications (posting_schedule.min_minutes_between_posts) ;
    - méthode configurable (config.production.publish_method : "studio" ou "api").
    """
    prod = config.get("production", {})
    method = prod.get("publish_method", "studio")
    if allow_studio is None:
        allow_studio = True
    queue = load_queue()

    # ---- garde d'intervalle : au moins X minutes entre deux posts (aucun spam)
    min_gap = int(config.get("posting_schedule", {}).get("min_minutes_between_posts", 30))
    if min_gap > 0 and not force:
        last = last_published_dt(queue)
        if last is not None:
            elapsed_min = (datetime.now(timezone.utc) - last).total_seconds() / 60.0
            if elapsed_min < min_gap:
                reste = min_gap - elapsed_min
                print(f"[publier] délai minimum non écoulé : encore ~{reste:.0f} min "
                      f"avant le prochain post ({min_gap} min entre chaque vidéo)", flush=True)
                return "wait"

    done_sigs = already_published_scripts(queue)
    candidates = [e for e in queue if e["state"] == "READY"]
    if video_id:
        candidates = [e for e in candidates if e["video_id"] == video_id]
    if not candidates:
        print("[publier] file vide (aucun READY)")
        return None

    # Mix virals / toons : publier une catégorie différente de la dernière sortie
    # (jamais deux « via_* » ou deux « toon_* » d'affilée si on a le choix).
    def _cat(vid):
        return vid.split("_", 1)[0]

    published = [e for e in queue if e.get("state") == "PUBLISHED"]
    last_cat = _cat(published[-1]["video_id"]) if published else None
    if last_cat and len(candidates) > 1:
        autre = [e for e in candidates if _cat(e["video_id"]) != last_cat]
        if autre:
            candidates = autre

    # Plafond journalier : jamais plus de posts_per_day publiés dans la journée (UTC).
    cap_day = int(config.get("posting_schedule", {}).get("posts_per_day", 5))
    posted_today = sum(1 for e in queue
                       if e.get("state") in ("PUBLISHED", "PUBLISHED_SUSPECT")
                       and str(e.get("published_at_utc", "")).startswith(now_utc()[:10]))
    if posted_today >= cap_day:
        print(f"[publier] plafond journalier atteint ({posted_today}/{cap_day}) — rien à poster", flush=True)
        return None

    # ---- garde anti-doublon : on écarte et on marque tout doublon détecté
    kept = []
    for e in candidates:
        mp = META_DIR / f"{e['video_id']}.json"
        sig = None
        if mp.exists():
            lines = json.loads(mp.read_text(encoding="utf-8")).get("lines", [])
            sig = "|".join(l["text"].strip().lower() for l in lines)
        if sig and sig in done_sigs:
            e.update(state="FAILED", error="doublon d'un script déjà publié (bloqué par le studio)")
            print(f"[publier] DOUBLON bloqué : {e['video_id']} (script déjà sorti)", flush=True)
            save_queue(queue)
            continue
        if sig:
            done_sigs.add(sig)
        kept.append(e)
    candidates = kept

    # ---- gardeanti-doublon de SCÉNARIO : les 4 variantes d'un même scénario sont
    # visuellement identiques (même décor, mêmes répliques). Une fois le scénario sorti,
    # ses variantes sont bloquées (30/09/2026 : auto_025 puis auto_026, même vidéo).
    if len(candidates) > 1 or not already_published_families(queue):
        eps_by_id = {x["id"]: x for x in bank()}
        done_fams = already_published_families(queue)
        kept2 = []
        for e in candidates:
            ep = eps_by_id.get(e["video_id"])
            fam = family_key(ep) if ep else None
            if fam and fam in done_fams:
                e.update(state="FAILED",
                         error=f"doublon de scénario (variante de « {fam} » déjà publié)")
                print(f"[publier] DOUBLON DE SCÉNARIO bloqué : {e['video_id']} "
                      f"(« {fam} » déjà publié)", flush=True)
                save_queue(queue)
                continue
            if fam:
                done_fams.add(fam)
            kept2.append(e)
        candidates = kept2

    # ---- garde anti-doublon VISUEL (empreinte des images) : attrape ce que le contrôle
    # de scénario laisse passer (auto_001 / auto_002 publiés, distance 0.0078 = même vidéo
    # aux yeux du spectateur). On avance candidat par candidat jusqu'à trouver une vidéo
    # publiable : calculer une empreinte coûte 5-13 s (ffmpeg), donc on ne contrôle que
    # la première qui passe — les suivantes seront contrôlées à leur tour.
    if candidates:
        sorties = [e["video_id"] for e in queue
                   if e.get("state") in ("PUBLISHED", "SCHEDULED", "DELETED",
                                         "PUBLISHED_SUSPECT")]
        restants = []
        for e in candidates:
            if e["video_id"] in sorties:
                restants.append(e)
                continue
            t0 = time.time()
            dup = visual_duplicate_of(e["video_id"], sorties)
            if dup:
                autre, dist = dup
                e.update(state="FAILED",
                         error=f"doublon visuel de {autre} (empreinte {dist:.4f} < "
                               f"{VISUAL_DUP_THRESHOLD}) — vidéo indiscernable, bloquée")
                print(f"[publier] DOUBLON VISUEL bloqué : {e['video_id']} "
                      f"= {autre} (distance {dist:.4f})", flush=True)
                sorties.append(e["video_id"])
                save_queue(queue)
                continue
            print(f"[publier] contrôle visuel {e['video_id']} : distinct "
                  f"({time.time() - t0:.0f} s)", flush=True)
            restants.append(e)
            break            # le premier vidéo valide est publié : inutile de tester la suite
        candidates = restants

    if not candidates:
        return None

    e = candidates[0]
    path = VIDEOS / e["file"]
    if not path.exists():
        e.update(state="FAILED", error="fichier absent")
        save_queue(queue)
        return None
    # Légende 2026 (hook + mots-clés + hashtags tournés)
    ep = next((x for x in bank() if x["id"] == e["video_id"]), None)
    if ep:
        e.update(caption=build_caption(ep))
    save_queue(queue)

    # ---- dernier verrou : cette vidéo est-elle DÉJÀ en ligne ? Le 01/10/2026 un run
    # « échoué » avait pourtant publié auto_037 (légende cassée) : l'état FAILED de la base
    # ne prouvait rien. On interroge la liste Contenu du compte avant tout envoi.
    if not force:
        # ATTENTION : on décompose le retour, un tuple non vide étant toujours vrai.
        trouve, extrait = deja_publie_sur_tiktok(e["video_id"], e.get("caption"))
        if trouve:
            e.update(state="PUBLISHED", error=None, published_at_utc=now_utc(),
                     published_evidence={"method": "reconciliation TikTok Studio",
                                         "confirmation": "déjà présent dans Contenu avant envoi",
                                         "carte": extrait[:120]})
            (VIDEOS / "published").mkdir(exist_ok=True)
            if path.exists():
                shutil.copy2(path, VIDEOS / "published" / path.name)
            save_queue(queue)
            print(f"[publier] {e['video_id']} était DÉJÀ en ligne — aucun envoi fait", flush=True)
            return "already"

    def try_api():
        agent = _agent(config)
        if not agent.access_token or not prod.get("api_allowed", True):
            return None
        print(f"[publier] envoi {e['video_id']} (API)...", flush=True)
        try:
            publish_id = agent._upload_video_api(str(path))
        except Exception as exc:
            print(f"[publier] API erreur: {exc}", flush=True)
            return None
        if not publish_id:
            print("[publier] API refusé (403 ?) -> repli Studio navigateur", flush=True)
            return None
        e.update(state="SCHEDULED", publish_id=publish_id, error=None)
        save_queue(queue)
        for _ in range(12):
            time.sleep(12)
            data = _api_status(agent, publish_id)
            st = data.get("status")
            if st == "PUBLISH_COMPLETE":
                e.update(state="PUBLISHED", published_at_utc=now_utc(),
                         published_evidence={"status": st, "publish_id": publish_id,
                                             "post_ids": data.get("publicaly_available_post_id")})
                (VIDEOS / "published").mkdir(exist_ok=True)
                shutil.copy2(path, VIDEOS / "published" / path.name)
                save_queue(queue)
                print(f"[publier] {e['video_id']} PUBLISHED (API)", flush=True)
                return "published"
            if st == "FAILED":
                e.update(state="FAILED", error=data.get("fail_reason", "FAILED"))
                save_queue(queue)
                return "failed"
        print(f"[publier] {e['video_id']} en traitement (SCHEDULED)", flush=True)
        return "processing"

    def try_studio():
        if not allow_studio:
            return "failed"
        import publish_studio
        try:
            # La bonne légende (hook + question + ≤5 hashtags) prime sur les métadonnées.
            publish_studio.publish(e["video_id"], caption=e.get("caption") or None)
            return "published"
        except SystemExit as exc:
            e.update(state="FAILED", error=str(exc))
            save_queue(queue)
            return "failed"

    order = ["studio", "api"] if method == "studio" else ["api", "studio"]
    for m in order:
        res = try_api() if m == "api" else try_studio()
        if res is not None:
            return res
    return None


def verify_all(config):
    queue = load_queue()
    agent = _agent(config)
    changed = False
    for e in queue:
        if e["state"] != "SCHEDULED" or not e.get("publish_id"):
            continue
        data = _api_status(agent, e["publish_id"])
        st = data.get("status")
        path = VIDEOS / e["file"]
        if st == "PUBLISH_COMPLETE":
            e.update(state="PUBLISHED", published_at_utc=now_utc(),
                     published_evidence={"status": st, "publish_id": e["publish_id"],
                                         "post_ids": data.get("publicaly_available_post_id")})
            (VIDEOS / "published").mkdir(exist_ok=True)
            shutil.copy2(path, VIDEOS / "published" / path.name)
            changed = True
            print(f"[verify] {e['video_id']} PUBLISHED", flush=True)
        elif st == "FAILED":
            e.update(state="FAILED", error=data.get("fail_reason", "FAILED"))
            changed = True
            print(f"[verify] {e['video_id']} FAILED : {data.get('fail_reason')}", flush=True)
    if changed:
        save_queue(queue)


# ------------------------------------------------------------------ etat
def status():
    queue = sync_ready_to_queue()
    bank_ids = [e["id"] for e in bank()]
    done = {e["video_id"] for e in queue}
    nb_bank = len(bank_ids)
    nb_prod = len(done)
    counts = {}
    for e in queue:
        counts[e["state"]] = counts.get(e["state"], 0) + 1
    print(f"Banque d'épisodes : {nb_bank}")
    print(f"Déjà produites    : {nb_prod} (dont {counts.get('PUBLISHED', 0)} publiées)")
    print(f"READY (tampon)    : {counts.get('READY', 0)}")
    print(f"SCHEDULED/upload  : {counts.get('SCHEDULED', 0)}")
    print(f"FAILED            : {counts.get('FAILED', 0)}")
    led = load_ledger().get(today_str(), {})
    print(f"Budget du jour    : {len(led.get('renders', []))} rendus | {led.get('bg_images', 0)} fonds IA")
    return queue


def bank_report():
    ep_ids = produced_ids()
    for e in bank():
        mark = "FAIT" if e["id"] in ep_ids else "    "
        print(f"{mark} {e['id']:9} {e['title']}")


def main():
    a = sys.argv[1:]
    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    if not a or a[0] == "status":
        status()
    elif a[0] == "bank":
        bank_report()
    elif a[0] == "produce":
        n = int(a[1]) if len(a) > 1 and a[1].isdigit() else None
        done = render_new(config, count=n)
        print(f"[studio] {len(done)} épisodes rendus : {done}")
    elif a[0] == "ensure":
        t = int(a[1]) if len(a) > 1 and a[1].isdigit() else None
        done = ensure_buffer(config, target=t)
        print(f"[studio] {len(done)} épisodes rendus pour tampon : {done}")
    elif a[0] == "publish":
        if "--verify" in a:
            verify_all(config)
        else:
            vid = a[1] if len(a) > 1 and not a[1].startswith("-") else None
            publish_next(config, video_id=vid, force="--force" in a)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()