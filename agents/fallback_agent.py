import os
import json
import time
import logging
import traceback
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

AGENT_MODULES = [
    ("content_finder", "ContentFinderAgent"),
    ("downloader", "DownloaderAgent"),
    ("video_editor", "VideoEditorAgent"),
    ("tiktok_publisher", "TikTokPublisherAgent"),
]


class FallbackAgent:
    """
    Agent 5 : Système de secours et redondance.
    Gère les erreurs, relance les agents en cas d'échec,
    et assure la continuité du pipeline.
    """

    def __init__(self, config: dict):
        self.config = config
        self.agents_config = config.get("agents", {})
        self.max_retries = self.agents_config.get("max_retries", 3)
        self.health_log_path = os.path.join("logs", "agent_health.json")
        self._load_health()

    def _load_health(self):
        if os.path.exists(self.health_log_path):
            with open(self.health_log_path, "r") as f:
                self.health = json.load(f)
        else:
            self.health = {}

    def _save_health(self):
        with open(self.health_log_path, "w") as f:
            json.dump(self.health, f, indent=2)

    def _update_agent_health(self, agent_name: str, success: bool):
        if agent_name not in self.health:
            self.health[agent_name] = {
                "total_runs": 0,
                "successes": 0,
                "failures": 0,
                "last_run": None,
                "last_error": None,
                "consecutive_failures": 0,
            }
        stats = self.health[agent_name]
        stats["total_runs"] += 1
        stats["last_run"] = datetime.now().isoformat()
        if success:
            stats["successes"] += 1
            stats["consecutive_failures"] = 0
        else:
            stats["failures"] += 1
            stats["consecutive_failures"] += 1
        self._save_health()

    def is_agent_healthy(self, agent_name: str) -> bool:
        stats = self.health.get(agent_name, {})
        consecutive = stats.get("consecutive_failures", 0)
        if consecutive >= self.max_retries:
            logger.warning(
                f"Agent {agent_name} has {consecutive} consecutive failures. "
                f"Checking if it recovered..."
            )
        return consecutive < self.max_retries

    def reset_agent_health(self, agent_name: str):
        if agent_name in self.health:
            self.health[agent_name]["consecutive_failures"] = 0
            self._save_health()

    def run_with_retry(self, func, agent_name: str, *args, **kwargs):
        """Exécute une fonction avec retry automatique."""
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    f"[{agent_name}] Attempt {attempt}/{self.max_retries}"
                )
                result = func(*args, **kwargs)
                self._update_agent_health(agent_name, True)
                return result
            except Exception as e:
                logger.error(
                    f"[{agent_name}] Attempt {attempt} failed: {e}"
                )
                logger.debug(traceback.format_exc())
                self._update_agent_health(agent_name, False)
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt * 10
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
        logger.error(f"[{agent_name}] All {self.max_retries} attempts failed")
        return None

    def get_health_report(self) -> dict:
        report = {
            "timestamp": datetime.now().isoformat(),
            "agents": {},
            "overall_status": "healthy",
        }
        for name, stats in self.health.items():
            success_rate = 0
            if stats["total_runs"] > 0:
                success_rate = (
                    stats["successes"] / stats["total_runs"]
                ) * 100
            report["agents"][name] = {
                **stats,
                "success_rate_pct": round(success_rate, 1),
            }
            if stats.get("consecutive_failures", 0) >= self.max_retries:
                report["overall_status"] = "degraded"
        return report


def get_fallback_agent(config: dict) -> FallbackAgent:
    return FallbackAgent(config)
