#!/usr/bin/env python3
"""
Script CLI pour scraper des guides de jeux depuis GameFAQs.
Utilise le scraper.py pour récupérer les guides de manière interactive.
"""

import argparse
import sys
from pathlib import Path
from gamefaqs_selenium_scraper import GameFAQsSeleniumScraper
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_banner():
    """Affiche une bannière de bienvenue."""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║         GameFAQs Guide Scraper - CLI Tool                 ║
║         Récupérez des guides de jeux facilement           ║
╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def list_supported_platforms():
    """Liste les plateformes supportées."""
    platforms = {
        "pc": "PC",
        "ps5": "PlayStation 5",
        "ps4": "PlayStation 4",
        "ps3": "PlayStation 3",
        "ps2": "PlayStation 2",
        "ps1": "PlayStation",
        "xbox-series-x": "Xbox Series X/S",
        "xbox-one": "Xbox One",
        "xbox360": "Xbox 360",
        "switch": "Nintendo Switch",
        "wii-u": "Wii U",
        "wii": "Wii",
        "3ds": "Nintendo 3DS",
        "ds": "Nintendo DS",
        "android": "Android",
        "ios": "iOS"
    }
    
    print("\n📱 Plateformes supportées:")
    print("-" * 50)
    for code, name in platforms.items():
        print(f"  • {code:20s} -> {name}")
    print("-" * 50)


def interactive_mode():
    """Mode interactif pour le scraping."""
    print_banner()
    print("\n🎮 Mode Interactif\n")
    
    # Demander le nom du jeu
    game_name = input("Entrez le nom du jeu: ").strip()
    if not game_name:
        print("❌ Nom de jeu invalide.")
        return
    
    # Demander la plateforme
    print("\n💡 Astuce: Tapez 'list' pour voir les plateformes disponibles")
    platform = input("Entrez la plateforme [pc]: ").strip().lower() or "pc"
    
    if platform == "list":
        list_supported_platforms()
        platform = input("\nEntrez la plateforme [pc]: ").strip().lower() or "pc"
    
    # Demander le nombre de guides
    max_guides_input = input("Nombre maximum de guides à scraper [tous]: ").strip()
    max_guides = None
    if max_guides_input.isdigit():
        max_guides = int(max_guides_input)
    
    # Demander le répertoire de sortie
    output_dir = input("Répertoire de sortie [data/guides]: ").strip() or "data/guides"
    
    # Demander le délai entre requêtes
    delay_input = input("Délai entre requêtes en secondes [2.0]: ").strip()
    delay = 2.0
    try:
        if delay_input:
            delay = float(delay_input)
    except ValueError:
        print("⚠️  Délai invalide, utilisation de 2.0 secondes par défaut")
    
    # Confirmation
    print("\n" + "="*60)
    print("📋 Résumé de la configuration:")
    print("="*60)
    print(f"  Jeu:              {game_name}")
    print(f"  Plateforme:       {platform}")
    print(f"  Max guides:       {max_guides if max_guides else 'Tous'}")
    print(f"  Répertoire:       {output_dir}")
    print(f"  Délai:            {delay}s")
    print("="*60)
    
    confirm = input("\n▶️  Continuer? [O/n]: ").strip().lower()
    if confirm and confirm not in ['o', 'oui', 'y', 'yes']:
        print("❌ Opération annulée.")
        return
    
    # Lancer le scraping
    print("\n🚀 Démarrage du scraping...\n")
    scraper = GameFAQsSeleniumScraper(output_dir=output_dir, delay=delay)
    
    try:
        saved_files = scraper.scrape_game(game_name, platform, max_guides)
        
        if saved_files:
            print("\n" + "="*60)
            print("✅ Scraping terminé avec succès!")
            print("="*60)
            print(f"\n📁 {len(saved_files)} guide(s) sauvegardé(s) dans: {output_dir}")
            print("\nFichiers créés:")
            for file_path in saved_files:
                print(f"  • {file_path.name}")
        else:
            print("\n⚠️  Aucun guide n'a été récupéré. Vérifiez le nom du jeu et la plateforme.")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Opération interrompue par l'utilisateur.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur lors du scraping: {e}")
        logger.exception("Erreur détaillée:")
        sys.exit(1)


def command_mode(args):
    """Mode commande avec arguments."""
    print_banner()
    
    print("\n🚀 Démarrage du scraping en mode commande...\n")
    print("="*60)
    print("📋 Configuration:")
    print("="*60)
    print(f"  Jeu:              {args.game}")
    print(f"  Plateforme:       {args.platform}")
    print(f"  Max guides:       {args.max_guides if args.max_guides else 'Tous'}")
    print(f"  Répertoire:       {args.output}")
    print(f"  Délai:            {args.delay}s")
    print("="*60 + "\n")
    
    scraper = GameFAQsSeleniumScraper(output_dir=args.output, delay=args.delay)
    
    try:
        saved_files = scraper.scrape_game(args.game, args.platform, args.max_guides)
        
        if saved_files:
            print("\n" + "="*60)
            print("✅ Scraping terminé avec succès!")
            print("="*60)
            print(f"\n📁 {len(saved_files)} guide(s) sauvegardé(s) dans: {args.output}")
            print("\nFichiers créés:")
            for file_path in saved_files:
                print(f"  • {file_path.name}")
        else:
            print("\n⚠️  Aucun guide n'a été récupéré. Vérifiez le nom du jeu et la plateforme.")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Opération interrompue par l'utilisateur.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur lors du scraping: {e}")
        logger.exception("Erreur détaillée:")
        sys.exit(1)


def main():
    """Point d'entrée principal du script."""
    parser = argparse.ArgumentParser(
        description="Scraper de guides de jeux depuis GameFAQs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  
  Mode interactif:
    python cli_scraper.py
  
  Mode commande:
    python cli_scraper.py -g "Red Dead Redemption 2" -p pc -m 3
    python cli_scraper.py --game "The Witcher 3" --platform ps4 --max-guides 5
    python cli_scraper.py -g "Elden Ring" -p pc -o guides/elden_ring
  
  Lister les plateformes:
    python cli_scraper.py --list-platforms
        """
    )
    
    parser.add_argument(
        '-g', '--game',
        type=str,
        help="Nom du jeu à scraper"
    )
    
    parser.add_argument(
        '-p', '--platform',
        type=str,
        default='pc',
        help="Plateforme du jeu (défaut: pc)"
    )
    
    parser.add_argument(
        '-m', '--max-guides',
        type=int,
        help="Nombre maximum de guides à scraper (défaut: tous)"
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='data/guides',
        help="Répertoire de sortie (défaut: data/guides)"
    )
    
    parser.add_argument(
        '-d', '--delay',
        type=float,
        default=2.0,
        help="Délai entre les requêtes en secondes (défaut: 2.0)"
    )
    
    parser.add_argument(
        '--list-platforms',
        action='store_true',
        help="Afficher la liste des plateformes supportées"
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help="Mode verbeux (plus de détails dans les logs)"
    )
    
    args = parser.parse_args()
    
    # Configuration du niveau de log
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Liste des plateformes
    if args.list_platforms:
        print_banner()
        list_supported_platforms()
        return
    
    # Mode interactif si aucun jeu n'est spécifié
    if not args.game:
        interactive_mode()
    else:
        command_mode(args)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Au revoir!")
        sys.exit(0)
