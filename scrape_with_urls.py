#!/usr/bin/env python3
"""
Script pour scraper des jeux en utilisant leurs URLs directes.
Solution de contournement pour l'erreur 403.
"""

from scraper import GameFAQsScraper
import time

# ========================================================================
# 📝 CONFIGUREZ VOS JEUX ICI
# ========================================================================
# Pour trouver l'URL d'un jeu:
# 1. Allez sur https://gamefaqs.gamespot.com
# 2. Cherchez le jeu
# 3. Copiez l'URL (ex: https://gamefaqs.gamespot.com/pc/200179-red-dead-redemption-2)
# ========================================================================

GAMES = [
    {
        "name": "Red Dead Redemption 2",
        "url": "https://gamefaqs.gamespot.com/pc/200179-red-dead-redemption-2",
        "max_guides": 3
    },
    {
        "name": "Elden Ring",
        "url": "https://gamefaqs.gamespot.com/pc/259372-elden-ring",
        "max_guides": 5
    },
    {
        "name": "Dark Souls 3",
        "url": "https://gamefaqs.gamespot.com/pc/168566-dark-souls-iii",
        "max_guides": 5
    },
    {
        "name": "The Witcher 3",
        "url": "https://gamefaqs.gamespot.com/pc/699808-the-witcher-3-wild-hunt",
        "max_guides": 5
    },
    {
        "name": "Celeste",
        "url": "https://gamefaqs.gamespot.com/pc/225251-celeste",
        "max_guides": 3
    },
    # Ajoutez vos jeux ici...
    # {
    #     "name": "Nom du Jeu",
    #     "url": "https://gamefaqs.gamespot.com/...",
    #     "max_guides": 5
    # },
]

# Configuration
OUTPUT_DIR = "data/guides"
DELAY_BETWEEN_REQUESTS = 3.0  # Secondes entre chaque requête
PAUSE_BETWEEN_GAMES = 10      # Secondes entre chaque jeu


def main():
    """Lance le scraping avec URLs directes."""
    
    print("""
╔═══════════════════════════════════════════════════════════════╗
║          Direct URL Scraper - GameFAQs Guides                 ║
║          Solution pour contourner l'erreur 403                ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    print(f"\n📋 {len(GAMES)} jeux configurés\n")
    
    # Afficher la liste
    for i, game in enumerate(GAMES, 1):
        print(f"  {i:2d}. {game['name']:40s} (max {game['max_guides']} guides)")
    
    # Configuration
    print("\n" + "="*70)
    print("⚙️  Configuration:")
    print(f"  • Délai entre requêtes:  {DELAY_BETWEEN_REQUESTS}s")
    print(f"  • Pause entre jeux:      {PAUSE_BETWEEN_GAMES}s")
    print(f"  • Répertoire de sortie:  {OUTPUT_DIR}")
    print("="*70)
    
    # Confirmation
    response = input("\n▶️  Commencer le scraping? [O/n]: ").strip().lower()
    if response and response not in ['o', 'oui', 'y', 'yes']:
        print("❌ Opération annulée.")
        return
    
    # Initialiser le scraper
    scraper = GameFAQsScraper(
        output_dir=OUTPUT_DIR,
        delay=DELAY_BETWEEN_REQUESTS
    )
    
    # Statistiques
    total = len(GAMES)
    success = 0
    failed = 0
    failed_games = []
    
    start_time = time.time()
    
    # Scraper chaque jeu
    for i, game in enumerate(GAMES, 1):
        print("\n\n" + "="*70)
        print(f"[{i}/{total}] 🎮 {game['name']}")
        print("="*70)
        
        try:
            saved_files = scraper.scrape_game_from_url(
                game_url=game['url'],
                game_name=game['name'],
                max_guides=game['max_guides']
            )
            
            if saved_files:
                print(f"✅ Succès: {len(saved_files)} guides sauvegardés")
                success += 1
            else:
                print(f"⚠️  Aucun guide récupéré")
                failed += 1
                failed_games.append(game['name'])
        
        except Exception as e:
            print(f"❌ Erreur: {e}")
            failed += 1
            failed_games.append(game['name'])
        
        # Pause entre jeux (sauf pour le dernier)
        if i < total:
            print(f"\n⏳ Pause de {PAUSE_BETWEEN_GAMES} secondes avant le prochain jeu...")
            time.sleep(PAUSE_BETWEEN_GAMES)
    
    # Résumé final
    elapsed = time.time() - start_time
    hours = int(elapsed // 3600)
    minutes = int((elapsed % 3600) // 60)
    seconds = int(elapsed % 60)
    
    print("\n\n" + "="*70)
    print("📊 RÉSUMÉ FINAL")
    print("="*70)
    print(f"  Total:        {total} jeux")
    print(f"  ✅ Succès:    {success}")
    print(f"  ❌ Échecs:    {failed}")
    
    if hours > 0:
        print(f"  ⏱️  Durée:     {hours}h {minutes}m {seconds}s")
    else:
        print(f"  ⏱️  Durée:     {minutes}m {seconds}s")
    
    print("="*70)
    
    if failed > 0:
        print("\n⚠️  Jeux échoués:")
        for game in failed_games:
            print(f"  • {game}")
    else:
        print("\n🎉 Tous les jeux ont été scrapés avec succès!")
    
    print(f"\n📁 Les guides sont dans: {OUTPUT_DIR}/")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Opération interrompue par l'utilisateur.")
        print("Les guides déjà récupérés sont sauvegardés.")
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        raise
