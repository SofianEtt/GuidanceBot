#!/usr/bin/env python3
"""
Script pour scraper des jeux à partir d'un fichier de configuration.
Permet de gérer facilement une grande liste de jeux.
"""

import subprocess
import time
import argparse
from pathlib import Path
from typing import List, Tuple

def parse_config_file(config_path: str) -> List[Tuple[str, str, int]]:
    """
    Parse le fichier de configuration.
    
    Args:
        config_path: Chemin vers le fichier de configuration
    
    Returns:
        Liste de tuples (nom_jeu, plateforme, max_guides)
    """
    games = []
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Ignorer les lignes vides et commentaires
                if not line or line.startswith('#'):
                    continue
                
                # Parser la ligne
                parts = line.split('|')
                if len(parts) != 3:
                    print(f"⚠️  Ligne {line_num} invalide (ignorée): {line}")
                    continue
                
                game_name = parts[0].strip()
                platform = parts[1].strip()
                try:
                    max_guides = int(parts[2].strip())
                except ValueError:
                    print(f"⚠️  Ligne {line_num}: nombre de guides invalide (ignorée)")
                    continue
                
                games.append((game_name, platform, max_guides))
        
        return games
    
    except FileNotFoundError:
        print(f"❌ Fichier de configuration non trouvé: {config_path}")
        return []
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du fichier: {e}")
        return []


def scrape_game(game_name: str, platform: str, max_guides: int, output_base: str, delay: float) -> bool:
    """
    Scrape un jeu spécifique.
    
    Args:
        game_name: Nom du jeu
        platform: Plateforme
        max_guides: Nombre maximum de guides
        output_base: Répertoire de base pour la sortie
        delay: Délai entre requêtes
    
    Returns:
        True si succès, False sinon
    """
    print("\n" + "="*70)
    print(f"🎮 Scraping: {game_name} ({platform})")
    print(f"📊 Max guides: {max_guides}")
    print("="*70)
    
    try:
        # Créer un sous-dossier propre pour chaque jeu
        safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in game_name)
        safe_name = safe_name.replace(' ', '_').lower()
        output_dir = f"{output_base}/{safe_name}"
        
        # Construire la commande
        cmd = [
            "python", "cli_scraper.py",
            "-g", game_name,
            "-p", platform,
            "-m", str(max_guides),
            "-o", output_dir,
            "-d", str(delay)
        ]
        
        # Exécuter la commande
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800  # 15 minutes max par jeu
        )
        
        if result.returncode == 0:
            print(f"✅ {game_name} - Succès!")
            return True
        else:
            print(f"❌ {game_name} - Échec")
            if result.stderr:
                print(f"Erreur: {result.stderr[:200]}")  # Limiter la sortie d'erreur
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏱️  {game_name} - Timeout (>15 minutes)")
        return False
    except Exception as e:
        print(f"❌ {game_name} - Erreur: {e}")
        return False


def main():
    """Lance le scraping depuis le fichier de configuration."""
    parser = argparse.ArgumentParser(
        description="Scraper de guides en batch depuis un fichier de configuration"
    )
    parser.add_argument(
        '-c', '--config',
        type=str,
        default='games_config.txt',
        help="Fichier de configuration (défaut: games_config.txt)"
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='data/guides',
        help="Répertoire de sortie de base (défaut: data/guides)"
    )
    parser.add_argument(
        '-d', '--delay',
        type=float,
        default=2.0,
        help="Délai entre requêtes (défaut: 2.0)"
    )
    parser.add_argument(
        '--pause',
        type=int,
        default=5,
        help="Pause entre jeux en secondes (défaut: 5)"
    )
    parser.add_argument(
        '--skip',
        type=int,
        default=0,
        help="Ignorer les N premiers jeux (pour reprendre)"
    )
    parser.add_argument(
        '--limit',
        type=int,
        help="Limiter au N premiers jeux"
    )
    
    args = parser.parse_args()
    
    print("""
╔═══════════════════════════════════════════════════════════════╗
║        Config-Based Batch Scraper - GameFAQs Guides           ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Charger la configuration
    print(f"📄 Chargement de la configuration: {args.config}")
    games = parse_config_file(args.config)
    
    if not games:
        print("❌ Aucun jeu trouvé dans la configuration.")
        return
    
    print(f"✅ {len(games)} jeux chargés depuis la configuration\n")
    
    # Appliquer les filtres
    if args.skip > 0:
        games = games[args.skip:]
        print(f"⏭️  Ignorés: {args.skip} premiers jeux")
    
    if args.limit:
        games = games[:args.limit]
        print(f"🔢 Limité à: {args.limit} jeux")
    
    # Afficher la liste
    print("\n📋 Jeux à scraper:")
    print("-" * 70)
    for i, (game, platform, max_guides) in enumerate(games, 1):
        print(f"  {i:2d}. {game:40s} ({platform}, max {max_guides})")
    print("-" * 70)
    
    # Configuration
    print(f"\n⚙️  Configuration:")
    print(f"  Output:        {args.output}")
    print(f"  Délai:         {args.delay}s entre requêtes")
    print(f"  Pause:         {args.pause}s entre jeux")
    
    # Confirmation
    print("\n" + "="*70)
    response = input("▶️  Commencer le scraping? [O/n]: ").strip().lower()
    if response and response not in ['o', 'oui', 'y', 'yes']:
        print("❌ Opération annulée.")
        return
    
    # Créer le répertoire de sortie
    Path(args.output).mkdir(parents=True, exist_ok=True)
    
    # Statistiques
    total = len(games)
    success = 0
    failed = 0
    failed_games = []
    
    start_time = time.time()
    
    # Scraper chaque jeu
    for i, (game, platform, max_guides) in enumerate(games, 1):
        print(f"\n\n[{i}/{total}] ", end="")
        
        if scrape_game(game, platform, max_guides, args.output, args.delay):
            success += 1
        else:
            failed += 1
            failed_games.append(game)
        
        # Pause entre les jeux (sauf pour le dernier)
        if i < total:
            print(f"\n⏳ Pause de {args.pause} secondes avant le prochain jeu...")
            time.sleep(args.pause)
    
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
        print("\nVous pouvez relancer le script avec --skip pour reprendre.")
    else:
        print("\n🎉 Tous les jeux ont été scrapés avec succès!")
    
    print(f"\n📁 Les guides sont dans: {args.output}/")
    print("\n💡 Prochaines étapes:")
    print("  1. Vérifiez les guides générés")
    print("  2. Préparez le chunking pour le RAG")
    print("  3. Créez les embeddings")
    print("  4. Indexez dans votre base vectorielle")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Opération interrompue par l'utilisateur.")
        print("Les guides déjà récupérés sont sauvegardés.")
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        raise
