#!/usr/bin/env python3
"""
TikTok AutoPost - Orchestrateur Principal
Système automatisé pour la recherche, l'édition et la publication
de contenu viral sur TikTok, tous les jours.
"""

import os
import sys
import json
import time
import random
import logging
import signal
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "video_pipeline"))

from video_pipeline import studio
from agents.content_finder import ContentFinderAgent
from agents.downloader import DownloaderAgent
from agents.video_editor import VideoEditorAgent
from agents.tiktok_publisher import TikTokPublisherAgent
from agents.fallback_agent import FallbackAgent

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")

os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(
            os.path.join(LOG_DIR, f"autopost_{datetime.now():%Y%m%d}.log"),
            encoding="utf-8",
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("autopost")

# Résultat du dernier run, pour que le scheduler dise la vérité (« post réussi »,
# « plafond atteint », « file vide ») au lieu d'annoncer « Post réussi » dans tous
# les cas — ce qui masquait une file sèche pendant des heures.
LAST_RUN_RESULT: dict = {}

running = True


def signal_handler(sig, frame):
    global running
    logger.info("Shutdown signal received. Finishing current run...")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def run_pipeline(config: dict) -> bool:
    """
    Exécute le pipeline complet :
    0. Moteur par défaut = « toons » (dessins animés originaux, gratuit, sans quota).
    1. Recherche de contenu viral (stock) / banque locale (toons)
    2. Téléchargement / rendu
    3. Édition
    4. Publication
    """
    if config.get("production", {}).get("engine", "toons") == "toons":
        return run_toon_pipeline(config)

    fallback = FallbackAgent(config)
    today = datetime.now().strftime("%Y-%m-%d")
    logger.info(f"=== Pipeline run - {today} ===")

    # --- ÉTAPE 1 : Recherche ---
    logger.info("--- ÉTAPE 1 : Recherche de contenu viral ---")
    finder = ContentFinderAgent(config)

    def search_step():
        result = finder.search_viral_content()
        if result is None:
            raise Exception("Aucun contenu trouvé")
        return result

    video_info = fallback.run_with_retry(search_step, "content_finder")
    if video_info is None:
        logger.error("ÉCHEC: Pas de contenu trouvé après toutes les tentatives")
        return False

    # --- ÉTAPE 2 : Téléchargement ---
    logger.info("--- ÉTAPE 2 : Téléchargement ---")
    downloader = DownloaderAgent(config)

    def download_step():
        path = downloader.download_video(video_info)
        if not os.path.exists(path):
            raise Exception(f"Fichier non trouvé: {path}")
        return path

    raw_path = fallback.run_with_retry(download_step, "downloader")
    if raw_path is None:
        logger.error("ÉCHEC: Téléchargement impossible")
        return False

    # --- ÉTAPE 3 : Édition ---
    logger.info("--- ÉTAPE 3 : Édition vidéo ---")
    editor = VideoEditorAgent(config)
    output_path = downloader.get_output_path(video_info, suffix="final")
    hook_text = video_info.get("hook_text", "")

    def edit_step():
        result = editor.edit_video(
            input_path=raw_path,
            output_path=output_path,
            hook_text=hook_text,
            skip_editing=not editor._check_ffmpeg(),
        )
        if not os.path.exists(result):
            raise Exception(f"Fichier édité non trouvé: {result}")
        return result

    edited_path = fallback.run_with_retry(edit_step, "video_editor")
    if edited_path is None:
        logger.warning("Édition échouée, publication du fichier brut")
        edited_path = raw_path

    # --- ÉTAPE 4 : Publication ---
    logger.info("--- ÉTAPE 4 : Publication TikTok ---")
    publisher = TikTokPublisherAgent(config)

    caption = _generate_caption(video_info)

    def publish_step():
        success = publisher.publish(edited_path, caption)
        if not success:
            raise Exception("Publication échouée")
        return True

    result = fallback.run_with_retry(publish_step, "tiktok_publisher")
    if result is None:
        logger.error("ÉCHEC: Publication impossible")
        _save_unposted(video_info, edited_path, caption)
        return False

    logger.info("=== Pipeline terminé avec succès ===")
    _log_daily_stats(config)
    return True


def run_toon_pipeline(config: dict) -> bool:
    """
    Ligne « dessins animés » : garantit un tampon de vidéos prêtes (budget du jour
    respecté via le ledger) puis publie la plus ancienne via l'API TikTok (repli
    Studio navigateur). Aucun crédit externe consommé : le rendu est CPU local.
    """
    logger.info("=== Pipeline TOONS — dessin animé original gratuit ===")
    prod = config.get("production", {})
    try:
        new = studio.ensure_buffer(config)
        if new:
            logger.info(f"Tampon rechargé : {len(new)} épisode(s) rendu(s)")
    except Exception as e:
        logger.error(f"Production toons échouée: {e}")

    if not prod.get("auto_publish", False):
        logger.info("Publication automatique DÉSACTIVÉE par le patron : production OK, "
                    "post en attente (lancer `python main.py run` ou passer auto_publish=true)")
        return True
    try:
        res = studio.publish_next(config)
    except Exception as e:
        logger.error(f"Publication toons échouée: {e}")
        res = "failed"
    if res in ("published", "processing"):
        logger.info(f"=== Pipeline toons terminé avec succès ({res}) ===")
        _log_daily_stats(config)
        LAST_RUN_RESULT["toons"] = res
        return True
    if res == "failed":
        logger.error("Publication toons impossible")
        LAST_RUN_RESULT["toons"] = "failed"
        return False
    if res == "wait":
        logger.info("Publication différée : délai minimum entre posts non écoulé")
        LAST_RUN_RESULT["toons"] = "wait"
        return False
    # Rien à publier : soit le plafond du jour est atteint (normal, rien à réessayer),
    # soit la file est VIDE (il faut retenter après production). La nuance compte : on
    # disait « Post réussi » dans les deux cas, ce qui masquait une file sèche.
    queue = studio.load_queue()
    cap_day = int(config.get("posting_schedule", {}).get("posts_per_day", 5))
    aujourdhui = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    postes = sum(1 for e in queue if e.get("state") in ("PUBLISHED", "PUBLISHED_SUSPECT")
                 and str(e.get("published_at_utc") or "").startswith(aujourdhui))
    if postes >= cap_day:
        logger.info(f"Plafond journalier atteint ({postes}/{cap_day}) — rien à poster")
        LAST_RUN_RESULT["toons"] = "cap"
        return True
    logger.warning("File de publication VIDE (aucune vidéo prête) — nouvelle tentative dans 30 min")
    LAST_RUN_RESULT["toons"] = "empty"
    return False


def _generate_caption(video_info: dict) -> str:
    """Génère une légende TikTok optimale."""
    category = video_info.get("category", "")
    hook = video_info.get("hook_text", "")
    keyword = video_info.get("search_keyword", "")

    hashtags = {
        "nature": "#nature #beautiful #naturephotography #earth #viral",
        "satisfying": "#satisfying #oddlysatisfying #relaxing #viral #fyp",
        "motivation": "#motivation #inspiration #success #mindset #viral",
        "facts": "#facts #didyouknow #learning #science #viral #fyp",
        "tech": "#technology #future #ai #tech #viral #fyp",
        "food": "#food #cooking #foodie #yummy #viral #fyp",
        "travel": "#travel #wanderlust #explore #adventure #viral #fyp",
        "animals": "#animals #cute #animalslovers #pets #viral #fyp",
        "science": "#science #experiment #chemistry #physics #viral",
        "history": "#history #ancient #mystery #facts #viral #fyp",
    }

    tags = hashtags.get(category, "#viral #fyp #tiktok")
    caption = f"{hook}\n\n{tags}"
    return caption[:300]


def _save_unposted(video_info: dict, video_path: str, caption: str):
    """Sauvegarde les vidéos non postées pour publication ultérieure."""
    queue_path = os.path.join(LOG_DIR, "post_queue.json")
    queue = []
    if os.path.exists(queue_path):
        with open(queue_path, "r") as f:
            queue = json.load(f)
    queue.append(
        {
            "video_info": video_info,
            "video_path": video_path,
            "caption": caption,
            "queued_at": datetime.now().isoformat(),
            "status": "pending",
        }
    )
    with open(queue_path, "w") as f:
        json.dump(queue, f, indent=2)
    logger.info(f"Video added to queue: {queue_path}")


def _log_daily_stats(config: dict):
    """Log les statistiques journalières."""
    stats_path = os.path.join(LOG_DIR, "daily_stats.json")
    stats = {}
    if os.path.exists(stats_path):
        with open(stats_path, "r") as f:
            stats = json.load(f)

    today = datetime.now().strftime("%Y-%m-%d")
    if today not in stats:
        stats[today] = {"posts": 0, "errors": 0, "content_found": 0}

    publisher = TikTokPublisherAgent(config)
    posts_api = publisher.get_post_count_today()
    posts_queue = sum(
        1 for e in studio.load_queue()
        if e.get("state") == "PUBLISHED" and str(e.get("published_at_utc", "")).startswith(today)
    )
    stats[today]["posts"] = posts_api + posts_queue
    stats[today]["last_run"] = datetime.now().isoformat()

    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)


def _post_dt(ts):
    """Parse un timestamp ISO en datetime aware (naïf = heure locale)."""
    try:
        dt = datetime.fromisoformat(ts)
    except (TypeError, ValueError):
        return None
    if dt.tzinfo is None:
        dt = dt.astimezone()
    return dt


def _last_post_date(config):
    """Dernière publication réussie (file toons + historique API), ou None."""
    best = None
    try:
        for e in studio.load_queue():
            if e.get("state") == "PUBLISHED" and e.get("published_at_utc"):
                dt = _post_dt(e["published_at_utc"])
                if dt and (best is None or dt > best):
                    best = dt
    except Exception:
        pass
    hist_path = os.path.join(LOG_DIR, "post_history.json")
    if os.path.exists(hist_path):
        try:
            with open(hist_path, encoding="utf-8") as f:
                hist = json.load(f)
            for p in hist:
                if p.get("status") == "success" and p.get("posted_at"):
                    dt = _post_dt(p["posted_at"])
                    if dt and (best is None or dt > best):
                        best = dt
        except Exception:
            pass
    return best


def _minutes_since_last_post(config):
    """Minutes écoulées depuis la dernière publication (None si aucune)."""
    last = _last_post_date(config)
    if last is None:
        return None
    return (datetime.now().astimezone() - last).total_seconds() / 60.0


def process_queue(config: dict):
    """Traite les vidéos en attente de publication (1 max, délai min respecté)."""
    queue_path = os.path.join(LOG_DIR, "post_queue.json")
    if not os.path.exists(queue_path):
        return

    with open(queue_path, "r") as f:
        queue = json.load(f)

    pending = [item for item in queue if item["status"] == "pending"]
    if not pending:
        return

    min_gap = int(config.get("posting_schedule", {}).get("min_minutes_between_posts", 30))
    logger.info(f"Processing {len(pending)} queued videos...")
    publisher = TikTokPublisherAgent(config)

    for item in pending[:3]:
        elapsed = _minutes_since_last_post(config)
        if elapsed is not None and elapsed < min_gap:
            logger.info(f"File en attente : {min_gap - elapsed:.0f} min restantes "
                        f"avant le prochain post (délai min {min_gap} min)")
            break
        try:
            if os.path.exists(item["video_path"]):
                success = publisher.publish(item["video_path"], item["caption"])
                if success:
                    item["status"] = "posted"
                    item["posted_at"] = datetime.now().isoformat()
                else:
                    item["status"] = "failed"
                    item["retries"] = item.get("retries", 0) + 1
            else:
                item["status"] = "file_missing"
        except Exception as e:
            logger.error(f"Queue processing error: {e}")
            item["status"] = "error"
            item["error"] = str(e)

    with open(queue_path, "w") as f:
        json.dump(queue, f, indent=2)


def run_scheduler(config: dict):
    """Boucle principale du scheduler - tourne 24/7, produit et publie 4-5 vidéos/jour."""
    schedule = config.get("posting_schedule", {})
    posts_per_day = int(schedule.get("posts_per_day", 5))
    post_times = schedule.get("post_times_utc", ["11:00", "14:00", "17:00", "19:30", "22:00"])
    prod = config.get("production", {})
    engine = prod.get("engine", "toons")
    logger.info("=== FactVibes Scheduler démarré ===")
    logger.info(f"Posts par jour: {posts_per_day} ({len(post_times)} créneaux)")
    logger.info(f"Moteur de contenu: {engine}")

    last_prod_date = None
    posted_slots_today = set()
    retry_until = None

    while running:
        now = datetime.now()
        now_utc = now.astimezone(timezone.utc)
        today = now.strftime("%Y-%m-%d")

        if retry_until is not None:
            if now < retry_until:
                for _ in range(60):
                    if not running:
                        return
                    time.sleep(1)
                continue
            retry_until = None

        # Une production par jour : remplir le tampon dans la limite du budget quotidien
        if last_prod_date != today:
            if engine == "toons":
                try:
                    new = studio.ensure_buffer(config)
                    logger.info(f"Production quotidienne: {len(new)} épisode(s) rendu(s)")
                except Exception as e:
                    logger.error(f"Production quotidienne échouée: {e}")
            posted_slots_today = set()
            last_prod_date = today

        # Publication aux créneaux planifiés — post_times_utc sont des HEURES UTC.
        # On convertit chaque créneau en datetime aware UTC, puis on compare à now_utc.
        targets = []
        for pt in post_times[:max(posts_per_day, len(post_times))]:
            h, m = map(int, pt.split(":"))
            slot = now_utc.replace(hour=h, minute=m, second=0, microsecond=0)
            targets.append((pt, slot))
        done_today = len(posted_slots_today)

        min_gap = int(schedule.get("min_minutes_between_posts", 30))

        for pt, t in sorted(targets, key=lambda x: x[1]):
            if done_today >= posts_per_day or pt in posted_slots_today:
                continue
            if t > now_utc:
                break
            elapsed = _minutes_since_last_post(config)
            if elapsed is not None and elapsed < min_gap:
                wait_min = min_gap - elapsed
                logger.info(f"Créneau {pt} reporté : {wait_min:.0f} min restantes "
                            f"avant le prochain post (délai min {min_gap} min)")
                retry_until = now + timedelta(minutes=max(1, int(wait_min) + 1))
                break
            logger.info(f"C'est l'heure de poster ! (créneau {pt})")
            process_queue(config)
            LAST_RUN_RESULT.clear()
            if run_pipeline(config):
                quoi = LAST_RUN_RESULT.get("toons", "published")
                if quoi in ("published", "processing"):
                    logger.info("Post réussi (vidéo en ligne)")
                else:
                    logger.info(f"Créneau {pt} clos sans publication ({quoi})")
            else:
                logger.warning("Post en échec ou reporté, nouvelle tentative dans 30 min")
                posted_slots_today.discard(pt)
                retry_until = now + timedelta(minutes=30)
                break
            posted_slots_today.add(pt)
            done_today += 1

        for _ in range(60):
            if not running:
                return
            time.sleep(1)


def main():
    """Point d'entrée principal."""
    config = load_config()

    privacy_override = os.getenv("TIKTOK_PRIVACY_LEVEL", "").strip()
    if privacy_override:
        config.setdefault("tiktok", {})["privacy_level"] = privacy_override

    if len(sys.argv) > 1:
        command = sys.argv[1]
        extra = sys.argv[2:]
        if command == "run":
            if "--private" in extra or "--draft" in extra:
                logger.info("Mode privé/draft: privacy -> SELF_ONLY")
                config.setdefault("tiktok", {})["privacy_level"] = "SELF_ONLY"
            logger.info("Manual single run")
            ok = run_pipeline(config)
            sys.exit(0 if ok else 1)
        elif command == "queue":
            process_queue(config)
        elif command == "produce":
            if extra and extra[0].isdigit():
                done = studio.render_new(config, count=int(extra[0]))
            elif extra:
                done = studio.render_new(config, ep_ids=extra)
            else:
                done = studio.render_new(config)
            print(f"{len(done)} épisode(s) rendu(s): {done}")
        elif command == "bank":
            studio.bank_report()
        elif command == "verify":
            studio.verify_all(config)
        elif command == "status":
            studio.status()
        elif command == "health":
            fallback = FallbackAgent(config)
            report = fallback.get_health_report()
            print(json.dumps(report, indent=2))
        elif command == "stats":
            stats_path = os.path.join(LOG_DIR, "daily_stats.json")
            if os.path.exists(stats_path):
                with open(stats_path, "r") as f:
                    print(json.dumps(json.load(f), indent=2))
            else:
                print("No stats yet.")
        elif command == "test":
            logger.info("=== MODE TEST ===")
            logger.info("Testing content search...")
            finder = ContentFinderAgent(config)
            result = finder.search_viral_content()
            if result:
                print(f"Found: {result['id']} from {result['source']}")
                print(f"Hook: {result.get('hook_text', 'N/A')}")
                print(f"Category: {result.get('category', 'N/A')}")
                print(f"URL: {result.get('url', 'N/A')}")
            else:
                print("No content found. Check your API keys.")
        else:
            print(f"Unknown command: {command}")
            print("Usage: python main.py [run|queue|health|stats|test]")
            sys.exit(1)
    else:
        run_scheduler(config)


if __name__ == "__main__":
    main()
