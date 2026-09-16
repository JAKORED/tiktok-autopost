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
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
    1. Recherche de contenu viral
    2. Téléchargement
    3. Édition
    4. Publication
    """
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
    stats[today]["posts"] = publisher.get_post_count_today()
    stats[today]["last_run"] = datetime.now().isoformat()

    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)


def process_queue(config: dict):
    """Traite les vidéos en attente de publication."""
    queue_path = os.path.join(LOG_DIR, "post_queue.json")
    if not os.path.exists(queue_path):
        return

    with open(queue_path, "r") as f:
        queue = json.load(f)

    pending = [item for item in queue if item["status"] == "pending"]
    if not pending:
        return

    logger.info(f"Processing {len(pending)} queued videos...")
    publisher = TikTokPublisherAgent(config)

    for item in pending[:3]:
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
    """Boucle principale du scheduler - tourne 24/7."""
    logger.info("=== TikTok AutoPost Scheduler démarré ===")
    logger.info(f"Posts par jour: {config['posting_schedule']['posts_per_day']}")

    last_post_date = None

    while running:
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")

        if last_post_date != today:
            post_times = config["posting_schedule"].get("post_times_utc", ["14:00"])
            next_post_time = post_times[0]
            h, m = map(int, next_post_time.split(":"))
            next_post = now.replace(hour=h, minute=m, second=0, microsecond=0)

            if now >= next_post:
                logger.info("It's time to post!")
                process_queue(config)
                success = run_pipeline(config)
                if success:
                    last_post_date = today
                    logger.info("Daily post completed!")
                else:
                    logger.warning("Daily post failed, will retry in 1 hour")
                    next_post = now + timedelta(hours=1)

        sleep_seconds = 60
        logger.debug(f"Sleeping {sleep_seconds}s...")
        for _ in range(sleep_seconds):
            if not running:
                break
            time.sleep(1)


def main():
    """Point d'entrée principal."""
    config = load_config()

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "run":
            logger.info("Manual single run")
            run_pipeline(config)
        elif command == "queue":
            process_queue(config)
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
    else:
        run_scheduler(config)


if __name__ == "__main__":
    main()
