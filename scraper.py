import requests
from bs4 import BeautifulSoup
import string
import datetime
import html2text
import time
import logging
from pathlib import Path
from typing import List, Optional
import json
from urllib.parse import urljoin
import random
import cloudscraper

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GameFAQsScraper:
    """Scraper pour extraire les guides de jeux depuis GameFAQs."""
    
    BASE_URL = "https://gamefaqs.gamespot.com"
    
    def __init__(self, output_dir: str = "data/guides", delay: float = 2.0):
        """
        Initialize the scraper.
        
        Args:
            output_dir: Répertoire de sortie pour les guides
            delay: Délai entre les requêtes (en secondes) pour respecter le site
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.delay = delay
        self.last_request_time = 0
        
        self.session = cloudscraper.create_scraper(
            browser={
                "browser": "chrome",
                "platform": "windows",
                "mobile": False
            }
        )
        #self.session.headers["user-agent"] = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        # Headers plus réalistes et complets
        '''
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        })
        '''
        # Configuration HTML2Text
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = True
        self.html_converter.body_width = 0
    
    def _rate_limit(self):
        """Applique un délai entre les requêtes pour respecter le serveur."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self.last_request_time = time.time()
    '''
    def _make_request(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """
        Fait une requête HTTP avec gestion d'erreurs et retry.
        
        Args:
            url: URL à requêter
            retries: Nombre de tentatives
            
        Returns:
            BeautifulSoup object ou None en cas d'erreur
        """
        for attempt in range(retries):
            self._rate_limit()
            
            try:
                # Ajouter un délai aléatoire pour paraître plus humain
                if attempt > 0:
                    wait_time = random.uniform(3, 6)
                    logger.info(f"Tentative {attempt + 1}/{retries} après {wait_time:.1f}s...")
                    time.sleep(wait_time)
                
                response = self.session.get(url) #, timeout=30, allow_redirects=True
                
                # Si 403, essayer avec des headers différents
                if response.status_code == 403 and attempt < retries - 1:
                    logger.warning(f"403 Forbidden, changement de User-Agent...")
                    self._rotate_user_agent()
                    continue
                
                response.raise_for_status()
                return BeautifulSoup(response.text, 'html.parser')
                
            except requests.RequestException as e:
                logger.error(f"Erreur lors de la requête à {url}: {e}")
                if attempt == retries - 1:
                    return None
        
        return None

    '''
    def _make_request(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        
        #Fait une requête HTTP et réessaie indéfiniment tant que le serveur renvoie 403.
        #Les autres erreurs sont réessayées 3 fois avant abandon.

        max_other_errors = 3
        other_errors = 0

        while True:
            self._rate_limit()

            for attempt in range(retries):
                self._rate_limit()
                
                try:
                    # Ajouter un délai aléatoire pour paraître plus humain
                    if attempt > 0:
                        wait_time = random.uniform(3, 6)
                        logger.info(f"Tentative {attempt + 1}/{retries} après {wait_time:.1f}s...")
                        time.sleep(wait_time)
                    
                    response = self.session.get(url) #, timeout=30, allow_redirects=True
                    
                    # Si 403, essayer avec des headers différents
                    if response.status_code == 403 and attempt < retries - 1:
                        logger.warning(f"403 Forbidden, changement de User-Agent...")
                        self._rotate_user_agent()
                        continue
                    
                    response.raise_for_status()
                    return BeautifulSoup(response.text, 'html.parser')
                    
                except requests.RequestException as e:
                    logger.error(f"Erreur lors de la requête à {url}: {e}")
                    #if attempt == retries - 1:
                        #return None
            
        return None
    
    
    def _rotate_user_agent(self):
        """Change le User-Agent pour éviter les blocages."""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        self.session.headers["User-Agent"] = random.choice(user_agents)
        logger.debug(f"User-Agent changé")
    
    def search_game_by_name(self, name: str, platform: str = "pc") -> Optional[str]:
        """
        Recherche un jeu par son nom.
        
        Args:
            name: Nom du jeu
            platform: Plateforme (pc, ps5, xbox, switch, etc.)
            
        Returns:
            URL des FAQs du jeu ou None si non trouvé
        """
        # Déterminer la page de sitemap appropriée
        first_char = name[0].upper() if name and name[0].isalpha() else "00"
        sitemap_url = f"{self.BASE_URL}/sitemap/game/{platform}/{first_char}"
        
        logger.info(f"Recherche de '{name}' sur {sitemap_url}")
        soup = self._make_request(sitemap_url)
        
        if not soup:
            logger.error("Impossible d'accéder à la page de recherche")
            logger.info("Suggestion: Essayez de trouver l'URL directe du jeu sur GameFAQs et utilisez search_game_by_url()")
            return None
        
        # Rechercher le lien exact du jeu
        all_links = soup.find_all('a')
        for link in all_links:
            if link.get_text(strip=True).lower() == name.lower():
                game_url = link.get('href')
                if game_url:
                    faqs_url = urljoin(self.BASE_URL, game_url) + "/faqs"
                    logger.info(f"Jeu trouvé: {faqs_url}")
                    return faqs_url
        
        logger.warning(f"Jeu '{name}' non trouvé")
        return None
    
    def search_game_by_url(self, game_url: str) -> Optional[str]:
        """
        Utilise directement l'URL d'un jeu (contournement si la recherche échoue).
        
        Args:
            game_url: URL complète du jeu sur GameFAQs
            
        Returns:
            URL des FAQs du jeu
        """
        if not game_url.endswith("/faqs"):
            game_url = game_url.rstrip('/') + "/faqs"
        
        logger.info(f"Utilisation de l'URL directe: {game_url}")
        
        # Vérifier que l'URL est valide
        soup = self._make_request(game_url)
        if soup:
            return game_url
        return None
    
    def get_game_guides_urls(self, game_url: str) -> List[str]:
        """
        Récupère toutes les URLs des guides disponibles pour un jeu.
        
        Args:
            game_url: URL de la page FAQs du jeu
            
        Returns:
            Liste des URLs des guides
        """
        soup = self._make_request(game_url)
        if not soup:
            return []
        
        guide_urls = []
        ol_tag = soup.find("ol", class_="list flex col1 stripe guides gf_guides")
        
        if ol_tag:
            li_items = ol_tag.find_all("li")
            for li in li_items:
                link = li.find('a', class_="bold")
                if link and link.get('href'):
                    full_url = urljoin(self.BASE_URL, link.get('href'))
                    guide_urls.append(full_url)
                    logger.info(f"Guide trouvé: {link.get_text(strip=True)}")
        
        logger.info(f"Total de {len(guide_urls)} guides trouvés")
        return guide_urls
    
    def scrape_guide(self, guide_url: str) -> Optional[str]:
        """
        Scrape un guide complet (gère la pagination).
        
        Args:
            guide_url: URL du guide
            
        Returns:
            Contenu du guide en markdown ou None
        """
        logger.info(f"Scraping du guide: {guide_url}")
        
        soup = self._make_request(guide_url)
        if not soup:
            return None
        
        # Vérifier le type de guide (paginé ou texte brut)
        has_pagination = soup.find("ul", class_="paginate") is not None
        
        if has_pagination:
            return self._scrape_paginated_guide(guide_url)
        else:
            return self._scrape_text_guide(soup)
    
    def _scrape_paginated_guide(self, start_url: str) -> str:
        """Scrape un guide avec pagination."""
        all_content = []
        current_url = start_url
        page_num = 1
        
        while current_url:
            logger.info(f"Scraping page {page_num}: {current_url}")
            soup = self._make_request(current_url)
            
            if not soup:
                break
            
            # Extraire le contenu principal
            main_div = soup.find("div", class_="ffaq ffaqbody")
            if main_div:
                # Supprimer les images et table des matières
                for elem in main_div.find_all("img"):
                    elem.decompose()
                for elem in main_div.find_all("div", class_="ftoc"):
                    elem.decompose()
                
                # Convertir en markdown
                html_content = main_div.decode_contents()
                markdown = self.html_converter.handle(html_content)
                all_content.append(markdown)
            
            # Trouver la page suivante
            current_url = self._find_next_page(soup)
            page_num += 1
        
        return "\n\n".join(all_content)
    
    def _scrape_text_guide(self, soup: BeautifulSoup) -> str:
        """Scrape un guide en texte brut (balises <pre>)."""
        content = []
        pre_tags = soup.find_all("pre")
        
        for pre in pre_tags:
            content.append(pre.get_text())
        
        return "\n\n".join(content)
    
    def _find_next_page(self, soup: BeautifulSoup) -> Optional[str]:
        """Trouve l'URL de la page suivante dans la pagination."""
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
        """
        Sauvegarde un guide avec métadonnées.
        
        Args:
            content: Contenu du guide
            game_name: Nom du jeu
            guide_url: URL source du guide
            
        Returns:
            Chemin du fichier sauvegardé
        """
        timestamp = int(datetime.datetime.now().timestamp() * 1000)
        safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in game_name)
        safe_name = safe_name.replace(' ', '_')
        
        # Sauvegarder le contenu
        content_file = self.output_dir / f"{safe_name}_{timestamp}.md"
        with open(content_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Sauvegarder les métadonnées
        metadata = {
            "game_name": game_name,
            "source_url": guide_url,
            "scraped_at": datetime.datetime.now().isoformat(),
            "content_file": str(content_file)
        }
        
        metadata_file = self.output_dir / f"{safe_name}_{timestamp}_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Guide sauvegardé: {content_file}")
        return content_file
    
    def scrape_game(self, game_name: str, platform: str = "pc", max_guides: Optional[int] = None) -> List[Path]:
        """
        Scrape tous les guides d'un jeu.
        
        Args:
            game_name: Nom du jeu
            platform: Plateforme
            max_guides: Nombre maximum de guides à scraper (None = tous)
            
        Returns:
            Liste des fichiers créés
        """
        logger.info(f"Début du scraping pour '{game_name}' sur {platform}")
        
        # Trouver le jeu
        game_url = self.search_game_by_name(game_name, platform)
        if not game_url:
            logger.error(f"Impossible de trouver le jeu '{game_name}'")
            return []
        
        # Récupérer les URLs des guides
        guide_urls = self.get_game_guides_urls(game_url)
        if max_guides:
            guide_urls = guide_urls[:max_guides]
        
        # Scraper chaque guide
        saved_files = []
        for i, guide_url in enumerate(guide_urls, 1):
            logger.info(f"Traitement du guide {i}/{len(guide_urls)}")
            
            content = self.scrape_guide(guide_url)
            if content:
                file_path = self.save_guide(content, game_name, guide_url)
                saved_files.append(file_path)
            
            # Pause entre les guides
            if i < len(guide_urls):
                time.sleep(self.delay)
        
        logger.info(f"Scraping terminé: {len(saved_files)} guides sauvegardés")
        return saved_files
    
    def scrape_game_from_url(self, game_url: str, game_name: str, max_guides: Optional[int] = None) -> List[Path]:
        """
        Scrape tous les guides d'un jeu en utilisant directement son URL.
        
        Args:
            game_url: URL directe du jeu sur GameFAQs
            game_name: Nom du jeu (pour les fichiers)
            max_guides: Nombre maximum de guides à scraper
            
        Returns:
            Liste des fichiers créés
        """
        logger.info(f"Début du scraping pour '{game_name}' depuis URL directe")
        
        # Valider l'URL
        faqs_url = self.search_game_by_url(game_url)
        if not faqs_url:
            logger.error(f"URL invalide ou inaccessible: {game_url}")
            return []
        
        # Récupérer les URLs des guides
        guide_urls = self.get_game_guides_urls(faqs_url)
        if max_guides:
            guide_urls = guide_urls[:max_guides]
        
        # Scraper chaque guide
        saved_files = []
        for i, guide_url in enumerate(guide_urls, 1):
            logger.info(f"Traitement du guide {i}/{len(guide_urls)}")
            
            content = self.scrape_guide(guide_url)
            if content:
                file_path = self.save_guide(content, game_name, guide_url)
                saved_files.append(file_path)
            
            # Pause entre les guides
            if i < len(guide_urls):
                time.sleep(self.delay)
        
        logger.info(f"Scraping terminé: {len(saved_files)} guides sauvegardés")
        return saved_files


if __name__ == "__main__":
    # Exemple d'utilisation
    print("[EXEC]")
    scraper = GameFAQsScraper(output_dir="data/guides", delay=3.0)
    scraper.scrape_game("Red Dead Redemption 2", platform="pc")
    
    # Option 1: Recherche par nom (peut être bloqué)
    # scraper.scrape_game("Red Dead Redemption 2", platform="pc", max_guides=3)
    
    # Option 2: URL directe (plus fiable)
    # Trouvez l'URL sur gamefaqs.gamespot.com puis utilisez:
    # scraper.scrape_game_from_url(
    #     "https://gamefaqs.gamespot.com/pc/200179-red-dead-redemption-2",
    #     "Red Dead Redemption 2",
    #     max_guides=3
    # )
