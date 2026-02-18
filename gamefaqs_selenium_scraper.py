import time
import logging
from pathlib import Path
from typing import List, Optional
import datetime
import json
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import html2text
from selenium.webdriver.chrome.service import Service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class GameFAQsSeleniumScraper:
    BASE_URL = "https://gamefaqs.gamespot.com"

    def __init__(self, output_dir="data/guides_selenium", delay=2.0, headless=False):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.delay = delay
        self.headless = headless

        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = True
        self.html_converter.body_width = 0

        self.driver = None

    # ---------------- Selenium lifecycle ----------------

    def _start(self):
        if self.driver is not None:
            return

        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        if self.headless:
            chrome_options.add_argument("--headless=new")

        service = Service(ChromeDriverManager().install()) 
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def _stop(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

    def _get_soup(self, url: str, wait: float = 2.0) -> Optional[BeautifulSoup]:
        self._start()
        logger.info(f"[NAVIGATE] {url}")

        try:
            self.driver.get(url)
            time.sleep(wait)  # laisser Cloudflare faire son challenge
            html = self.driver.page_source
            return BeautifulSoup(html, "html.parser")
        except Exception as e:
            logger.error(f"Erreur lors du chargement de {url}: {e}")
            return None

    # ---------------- High-level API ----------------

    def search_game_by_name(self, name: str, platform="pc") -> Optional[str]:
        first_char = name[0].upper() if name and name[0].isalpha() else "00"
        sitemap_url = f"{self.BASE_URL}/sitemap/game/{platform}/{first_char}"

        logger.info(f"Recherche de '{name}' sur {sitemap_url}")
        soup = self._get_soup(sitemap_url)
        if not soup:
            return None

        for link in soup.find_all("a"):
            if link.get_text(strip=True).lower() == name.lower():
                game_url = link.get("href")
                if game_url:
                    return urljoin(self.BASE_URL, game_url) + "/faqs"

        logger.warning(f"Jeu '{name}' non trouvé")
        return None

    def get_game_guides_urls(self, game_url: str) -> List[str]:
        soup = self._get_soup(game_url)
        if not soup:
            return []

        guide_urls = []
        ol_tag = soup.find("ol", class_="list flex col1 stripe guides gf_guides")
        if ol_tag:
            for li in ol_tag.find_all("li"):
                link = li.find("a", class_="bold")
                if link and link.get("href"):
                    full_url = urljoin(self.BASE_URL, link.get("href"))
                    guide_urls.append(full_url)
                    logger.info(f"Guide trouvé: {link.get_text(strip=True)}")

        return guide_urls

    def scrape_guide(self, guide_url: str) -> Optional[str]:
        soup = self._get_soup(guide_url)
        if not soup:
            return None

        has_pagination = soup.find("ul", class_="paginate") is not None
        if has_pagination:
            return self._scrape_paginated_guide(guide_url)
        else:
            return self._scrape_text_guide(soup)

    def _scrape_paginated_guide(self, start_url: str) -> str:
        all_content = []
        current_url = start_url
        page_num = 1

        while current_url:
            logger.info(f"Scraping page {page_num}: {current_url}")
            soup = self._get_soup(current_url)
            if not soup:
                break

            main_div = soup.find("div", class_="ffaq ffaqbody")
            if main_div:
                for elem in main_div.find_all("img"):
                    elem.decompose()
                for elem in main_div.find_all("div", class_="ftoc"):
                    elem.decompose()

                html_content = main_div.decode_contents()
                markdown = self.html_converter.handle(html_content)
                all_content.append(markdown)

            next_page = self._find_next_page(soup)
            current_url = next_page
            page_num += 1
            time.sleep(self.delay)

        return "\n\n".join(all_content)

    def _scrape_text_guide(self, soup: BeautifulSoup) -> str:
        content = []
        for pre in soup.find_all("pre"):
            content.append(pre.get_text())
        return "\n\n".join(content)

    def _find_next_page(self, soup: BeautifulSoup) -> Optional[str]:
        pagination = soup.find("ul", class_="paginate")
        if not pagination:
            return None

        for link in pagination.find_all("a"):
            if "Next" in link.text:
                href = link.get("href")
                if href:
                    return urljoin(self.BASE_URL, href)

        return None

    def save_guide(self, content: str, game_name: str, guide_url: str) -> Path:
        timestamp = int(datetime.datetime.now().timestamp() * 1000)
        safe_name = "".join(
            c if c.isalnum() or c in (" ", "-", "_") else "_" for c in game_name
        ).replace(" ", "_")

        content_file = self.output_dir / f"{safe_name}_{timestamp}.md"
        with open(content_file, "w", encoding="utf-8") as f:
            f.write(content)

        metadata = {
            "game_name": game_name,
            "source_url": guide_url,
            "scraped_at": datetime.datetime.now().isoformat(),
            "content_file": str(content_file),
        }

        metadata_file = self.output_dir / f"{safe_name}_{timestamp}_metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Guide sauvegardé: {content_file}")
        return content_file

    def scrape_game(self, game_name: str, platform="pc", max_guides=None) -> List[Path]:
        logger.info(f"Début du scraping pour '{game_name}' sur {platform}")
        try:
            game_url = self.search_game_by_name(game_name, platform)
            if not game_url:
                return []

            guide_urls = self.get_game_guides_urls(game_url)
            if max_guides:
                guide_urls = guide_urls[:max_guides]

            saved_files = []
            for i, guide_url in enumerate(guide_urls, 1):
                logger.info(f"Traitement du guide {i}/{len(guide_urls)}")
                content = self.scrape_guide(guide_url)
                if content:
                    saved_files.append(self.save_guide(content, game_name, guide_url))
                time.sleep(self.delay)

            return saved_files
        finally:
            self._stop()


if __name__ == "__main__":
    scraper = GameFAQsSeleniumScraper(headless=False)
    scraper.scrape_game("Red Dead Redemption 2", platform="pc")
