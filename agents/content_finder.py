import os
import json
import random
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class ContentFinderAgent:
    """
    Agent 1 : Recherche de contenu viral libre de droits.
    Interroge les APIs Pexels et Pixabay pour trouver des vidéos
    correspondant aux catégories et mots-clés tendance.
    """

    SOURCES = {
        "pexels": "https://api.pexels.com/videos/search",
        "pixabay": "https://pixabay.com/api/videos/",
    }

    def __init__(self, config: dict):
        self.config = config
        self.pexels_key = os.getenv("PEXELS_API_KEY", "")
        self.pixabay_key = os.getenv("PIXABAY_API_KEY", "")
        self.search_config = config.get("content_search", {})
        self.posted_log = self._load_posted_log()

    def _load_posted_log(self) -> list:
        log_path = os.path.join("logs", "posted_videos.json")
        if os.path.exists(log_path):
            with open(log_path, "r") as f:
                return json.load(f)
        return []

    def _save_posted_log(self):
        log_path = os.path.join("logs", "posted_videos.json")
        with open(log_path, "w") as f:
            json.dump(self.posted_log, f, indent=2)

    def _get_trending_category(self) -> str:
        categories = self.search_config.get("categories", ["nature"])
        base_weights = [10, 12, 8, 9, 7, 11, 10, 13, 6, 5]
        if len(categories) > len(base_weights):
            base_weights += [8] * (len(categories) - len(base_weights))
        weights = base_weights[: len(categories)]
        return random.choices(categories, weights=weights)[0]

    def _get_random_keyword(self, category: str) -> str:
        keywords = self.search_config.get("keywords_by_category", {}).get(
            category, ["viral video"]
        )
        return random.choice(keywords)

    def _get_random_hook(self) -> str:
        hooks = self.search_config.get("viral_hooks", ["Wait for it..."])
        hook = random.choice(hooks)
        day = random.randint(1, 365)
        return hook.replace("{number}", str(day))

    def _get_broader_queries(self) -> list:
        queries = []
        for kw_map in self.search_config.get("keywords_by_category", {}).values():
            if isinstance(kw_map, list):
                queries.extend(kw_map)
        if not queries:
            queries = ["nature", "city", "ocean", "sunset", "cute animals"]
        random.shuffle(queries)
        return queries[:5]

    def _search_pexels(self, query: str, per_page: int = 15) -> list:
        import requests

        if not self.pexels_key:
            logger.warning("Pexels API key not configured, skipping Pexels")
            return []

        try:
            headers = {"Authorization": self.pexels_key}
            params = {
                "query": query,
                "per_page": per_page,
                "orientation": "portrait",
                "size": "medium",
            }
            resp = requests.get(
                self.SOURCES["pexels"], headers=headers, params=params, timeout=15
            )
            resp.raise_for_status()
            data = resp.json()

            videos = []
            for video in data.get("videos", []):
                video_files = video.get("video_files", [])
                hd_files = [
                    f
                    for f in video_files
                    if f.get("quality") == "hd" and f.get("file_type") == "video/mp4"
                ]
                if not hd_files:
                    hd_files = [
                        f for f in video_files if f.get("file_type") == "video/mp4"
                    ]
                if hd_files:
                    portrait = [
                        f
                        for f in hd_files
                        if f.get("width") and f.get("height") and f["width"] < f["height"]
                    ]
                    candidates = portrait if portrait else hd_files
                    best = min(
                        candidates,
                        key=lambda x: abs(x.get("width", 0) - 720),
                    )
                    duration = video.get("duration", 0)
                    min_dur = self.search_config.get("min_video_duration_sec", 5)
                    max_dur = self.search_config.get("max_video_duration_sec", 60)
                    if min_dur <= duration <= max_dur:
                        videos.append(
                            {
                                "id": f"pexels_{video['id']}",
                                "source": "pexels",
                                "url": best["link"],
                                "width": best.get("width"),
                                "height": best.get("height"),
                                "duration": duration,
                                "thumbnail": video.get("image"),
                                "author": video.get("user", {}).get("name", "Unknown"),
                                "query": query,
                            }
                        )
            return videos
        except Exception as e:
            logger.error(f"Pexels search error: {e}")
            return []

    def _search_pixabay(self, query: str, per_page: int = 20) -> list:
        import requests

        if not self.pixabay_key:
            logger.warning("Pixabay API key not configured, skipping Pixabay")
            return []

        try:
            params = {
                "key": self.pixabay_key,
                "q": query,
                "video_type": "all",
                "per_page": per_page,
                "min_width": 720,
                "safesearch": "true",
            }
            resp = requests.get(
                self.SOURCES["pixabay"], params=params, timeout=15
            )
            resp.raise_for_status()
            data = resp.json()

            videos = []
            min_dur = self.search_config.get("min_video_duration_sec", 5)
            max_dur = self.search_config.get("max_video_duration_sec", 60)
            for hit in data.get("hits", []):
                duration = hit.get("duration", 0)
                if not (min_dur <= duration <= max_dur):
                    continue
                videos_dict = hit.get("videos", {})
                medium = videos_dict.get("medium", {})
                large = videos_dict.get("large", {})
                chosen = medium if medium.get("url") else large

                if chosen.get("url"):
                    videos.append(
                        {
                            "id": f"pixabay_{hit.get('id')}",
                            "source": "pixabay",
                            "url": chosen["url"],
                            "width": chosen.get("width"),
                            "height": chosen.get("height"),
                            "duration": duration,
                            "thumbnail": hit.get("picture_id"),
                            "author": hit.get("user", "Unknown"),
                            "query": query,
                            "tags": hit.get("tags", ""),
                        }
                    )
            return videos
        except Exception as e:
            logger.error(f"Pixabay search error: {e}")
            return []

    def search_viral_content(self) -> Optional[dict]:
        """
        Recherche du contenu viral. Retourne la meilleure vidéo trouvée
        avec un hook accrocheur.
        """
        category = self._get_trending_category()
        keyword = self._get_random_keyword(category)
        hook = self._get_random_hook()

        logger.info(
            f"Searching content - Category: {category}, Keyword: {keyword}"
        )

        all_videos = []

        pexels_results = self._search_pexels(keyword)
        all_videos.extend(pexels_results)
        logger.info(f"Pexels: {len(pexels_results)} results")

        pixabay_results = self._search_pixabay(keyword)
        all_videos.extend(pixabay_results)
        logger.info(f"Pixabay: {len(pixabay_results)} results")

        posted_ids = set(self.posted_log)
        new_videos = [v for v in all_videos if v["id"] not in posted_ids]

        if not new_videos:
            logger.warning("No new videos found, trying broader search")
            for kw in self._get_broader_queries():
                logger.info(f"Broader search keyword: {kw}")
                new_videos.extend(self._search_pexels(kw))
                new_videos.extend(self._search_pixabay(kw))
            new_videos = [v for v in new_videos if v["id"] not in posted_ids]

        if not new_videos:
            logger.error("No videos found from any source")
            return None

        chosen = random.choice(new_videos)

        chosen["hook_text"] = hook
        chosen["category"] = category
        chosen["search_keyword"] = keyword
        chosen["found_at"] = datetime.now().isoformat()

        self.posted_log.append(chosen["id"])
        self._save_posted_log()

        logger.info(
            f"Selected: {chosen['id']} from {chosen['source']} - {chosen['query']}"
        )
        return chosen


def find_content(config: dict) -> Optional[dict]:
    agent = ContentFinderAgent(config)
    return agent.search_viral_content()
