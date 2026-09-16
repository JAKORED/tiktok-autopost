import os
import json
import time
import base64
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class TikTokPublisherAgent:
    """
    Agent 4 : Publication automatique sur TikTok.
    Supporte deux méthodes :
    - API TikTok officielle (recommandé, nécessite approbation développeur)
    - Selenium/Playwright (automatisation navigateur)
    """

    TIKTOK_API_BASE = "https://open.tiktokapis.com/v2"

    def __init__(self, config: dict):
        self.config = config
        self.tiktok_config = config.get("tiktok", {})
        self.client_key = os.getenv("TIKTOK_CLIENT_KEY", "")
        self.client_secret = os.getenv("TIKTOK_CLIENT_SECRET", "")
        self.access_token = os.getenv("TIKTOK_ACCESS_TOKEN", "")
        self.refresh_token = os.getenv("TIKTOK_REFRESH_TOKEN", "")
        self.post_history = self._load_post_history()

    def _load_post_history(self) -> list:
        log_path = os.path.join("logs", "post_history.json")
        if os.path.exists(log_path):
            with open(log_path, "r") as f:
                return json.load(f)
        return []

    def _save_post_history(self):
        log_path = os.path.join("logs", "post_history.json")
        with open(log_path, "w") as f:
            json.dump(self.post_history, f, indent=2)

    def _refresh_access_token(self) -> bool:
        """Rafraîchit le token d'accès TikTok."""
        import requests

        if not self.refresh_token:
            logger.error("No refresh token available")
            return False

        try:
            resp = requests.post(
                f"{self.TIKTOK_API_BASE}/oauth2/token/",
                data={
                    "client_key": self.client_key,
                    "client_secret": self.client_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token,
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json().get("data", {})
            self.access_token = data.get("access_token", "")
            self.refresh_token = data.get("refresh_token", self.refresh_token)
            logger.info("Access token refreshed successfully")
            return True
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            return False

    def _upload_video_api(self, video_path: str) -> Optional[str]:
        """Upload une vidéo via l'API TikTok Content Posting."""
        import requests

        if not self.access_token:
            logger.error("No access token. TikTok API not configured.")
            return None

        file_size = os.path.getsize(video_path)
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "multipart/form-data",
        }

        try:
            init_resp = requests.post(
                f"{self.TIKTOK_API_BASE}/post/publish/inbox/video/init/",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "post_info": {
                        "title": "",
                        "privacy_level": self.tiktok_config.get(
                            "privacy_level", "PUBLIC_TO_EVERYONE"
                        ),
                        "disable_duet": not self.tiktok_config.get(
                            "allow_duet", False
                        ),
                        "disable_comment": not self.tiktok_config.get(
                            "allow_comments", True
                        ),
                        "disable_stitch": not self.tiktok_config.get(
                            "allow_stitch", False
                        ),
                    },
                    "source_info": {
                        "source": "FILE_UPLOAD",
                        "video_size": file_size,
                    },
                },
                timeout=15,
            )
            init_resp.raise_for_status()
            init_data = init_resp.json().get("data", {})

            upload_url = init_data.get("upload_url")
            publish_id = init_data.get("publish_id")

            if not upload_url:
                logger.error("No upload URL returned from TikTok")
                return None

            with open(video_path, "rb") as f:
                upload_resp = requests.put(
                    upload_url,
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "video/mp4",
                        "Content-Range": f"bytes 0-{file_size - 1}/{file_size}",
                    },
                    data=f,
                    timeout=300,
                )
                upload_resp.raise_for_status()

            logger.info(f"Video uploaded. Publish ID: {publish_id}")
            return publish_id

        except Exception as e:
            logger.error(f"API upload failed: {e}")
            if "access_token" in str(e).lower() or "unauthorized" in str(e).lower():
                logger.info("Attempting token refresh...")
                if self._refresh_access_token():
                    return self._upload_video_api(video_path)
            return None

    def _publish_via_selenium(self, video_path: str, caption: str) -> bool:
        """Publication via Selenium (automatisation navigateur)."""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            import glob

            cookies_path = os.path.join("config", "tiktok_cookies.json")
            if not os.path.exists(cookies_path):
                logger.error(
                    "No TikTok cookies found. Run 'python setup_browser.py' first."
                )
                return False

            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--window-size=1920,1080")

            driver = webdriver.Chrome(options=options)
            try:
                driver.get("https://www.tiktok.com/creator#/upload?scene=creator_center")
                time.sleep(3)

                with open(cookies_path, "r") as f:
                    cookies = json.load(f)
                for cookie in cookies:
                    driver.add_cookie(cookie)

                driver.refresh()
                time.sleep(5)

                upload_input = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'input[type="file"]')
                    )
                )
                upload_input.send_keys(os.path.abspath(video_path))
                time.sleep(10)

                caption_field = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, '[data-e2e="post_caption"]')
                    )
                )
                caption_field.clear()
                caption_field.send_keys(caption)
                time.sleep(2)

                post_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, '[data-e2e="post_btn"]')
                    )
                )
                post_btn.click()
                time.sleep(5)

                logger.info("Video posted via Selenium successfully!")
                return True

            finally:
                driver.quit()

        except ImportError:
            logger.error("Selenium not installed. Run: pip install selenium")
            return False
        except Exception as e:
            logger.error(f"Selenium posting failed: {e}")
            return False

    def publish(self, video_path: str, caption: str = "") -> bool:
        """
        Publie une vidéo sur TikTok.
        Essaie d'abord l'API, puis Selenium en fallback.
        """
        logger.info(f"Publishing to TikTok: {video_path}")

        method = "api"
        success = False

        if self.access_token:
            logger.info("Trying TikTok API...")
            publish_id = self._upload_video_api(video_path)
            if publish_id:
                success = True
                method = "api"
            else:
                logger.warning("API failed, trying Selenium fallback...")
                method = "selenium"
                success = self._publish_via_selenium(video_path, caption)
        else:
            logger.info("No API token, using Selenium...")
            method = "selenium"
            success = self._publish_via_selenium(video_path, caption)

        if success:
            self.post_history.append(
                {
                    "video_path": video_path,
                    "caption": caption,
                    "method": method,
                    "posted_at": datetime.now().isoformat(),
                    "status": "success",
                }
            )
            self._save_post_history()
            logger.info(f"Successfully posted via {method}")
        else:
            self.post_history.append(
                {
                    "video_path": video_path,
                    "caption": caption,
                    "method": method,
                    "posted_at": datetime.now().isoformat(),
                    "status": "failed",
                }
            )
            self._save_post_history()
            logger.error("Failed to post video")

        return success

    def get_post_count_today(self) -> int:
        today = datetime.now().strftime("%Y-%m-%d")
        return sum(
            1
            for p in self.post_history
            if p.get("posted_at", "").startswith(today)
            and p.get("status") == "success"
        )


def publish(video_path: str, caption: str, config: dict) -> bool:
    agent = TikTokPublisherAgent(config)
    return agent.publish(video_path, caption)
