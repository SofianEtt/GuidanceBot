#!/usr/bin/env python3
"""
Script de diagnostic pour tester l'accès à GameFAQs.
"""

import requests
import sys

def test_basic_access():
    """Test d'accès basique à GameFAQs."""
    print("="*70)
    print("TEST 1: Accès basique à GameFAQs")
    print("="*70)
    
    url = "https://gamefaqs.gamespot.com"
    
    try:
        print(f"URL testée: {url}")
        print("Requête en cours...")
        
        response = requests.get(url, timeout=10)
        
        print(f"✓ Status Code: {response.status_code}")
        print(f"✓ Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"✓ Content-Length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            print("\n✅ SUCCÈS: Accès à GameFAQs OK")
            return True
        elif response.status_code == 403:
            print("\n❌ ERREUR 403: Accès refusé")
            print("\nVotre IP semble être bloquée par GameFAQs.")
            return False
        else:
            print(f"\n⚠️  Code {response.status_code}: Réponse inattendue")
            return False
            
    except requests.exceptions.Timeout:
        print("\n❌ TIMEOUT: Le serveur ne répond pas")
        return False
    except requests.exceptions.ConnectionError:
        print("\n❌ ERREUR DE CONNEXION: Impossible de joindre le serveur")
        print("Vérifiez votre connexion internet")
        return False
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        return False


def test_with_headers():
    """Test avec headers avancés."""
    print("\n" + "="*70)
    print("TEST 2: Accès avec headers de navigateur")
    print("="*70)
    
    url = "https://gamefaqs.gamespot.com"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    
    try:
        print(f"URL testée: {url}")
        print("Requête avec headers personnalisés...")
        
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"✓ Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("\n✅ SUCCÈS: Headers acceptés")
            return True
        elif response.status_code == 403:
            print("\n❌ ERREUR 403: Toujours bloqué même avec headers")
            return False
        else:
            print(f"\n⚠️  Code {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        return False


def test_specific_game():
    """Test d'accès à une page de jeu spécifique."""
    print("\n" + "="*70)
    print("TEST 3: Accès à une page de jeu (Celeste)")
    print("="*70)
    
    url = "https://gamefaqs.gamespot.com/pc/225251-celeste/faqs"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://gamefaqs.gamespot.com/",
    }
    
    try:
        print(f"URL testée: {url}")
        print("Requête en cours...")
        
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"✓ Status Code: {response.status_code}")
        
        if response.status_code == 200:
            # Vérifier qu'on a bien des guides
            if "FAQ" in response.text or "Guide" in response.text:
                print("✓ Page contient des guides")
                print("\n✅ SUCCÈS: Accès aux pages de jeux OK")
                return True
            else:
                print("⚠️  Page accessible mais structure inhabituelle")
                return False
        elif response.status_code == 403:
            print("\n❌ ERREUR 403: Bloqué sur les pages de jeux")
            return False
        else:
            print(f"\n⚠️  Code {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        return False


def print_diagnostic():
    """Affiche le diagnostic et les recommandations."""
    print("\n" + "="*70)
    print("DIAGNOSTIC ET RECOMMANDATIONS")
    print("="*70)
    
    results = {
        "basic": test_basic_access(),
        "headers": test_with_headers(),
        "game": test_specific_game()
    }
    
    print("\n" + "="*70)
    print("RÉSUMÉ DES TESTS")
    print("="*70)
    print(f"Test 1 (Accès basique):    {'✅ OK' if results['basic'] else '❌ ÉCHEC'}")
    print(f"Test 2 (Avec headers):     {'✅ OK' if results['headers'] else '❌ ÉCHEC'}")
    print(f"Test 3 (Page de jeu):      {'✅ OK' if results['game'] else '❌ ÉCHEC'}")
    
    print("\n" + "="*70)
    print("RECOMMANDATIONS")
    print("="*70)
    
    if all(results.values()):
        print("\n✅ Tous les tests sont OK!")
        print("\nLe scraper devrait fonctionner.")
        print("\nSi vous avez toujours des erreurs 403:")
        print("  1. Augmentez le délai à 5-10 secondes")
        print("  2. Ne scrapez qu'un guide à la fois (-m 1)")
        print("  3. Attendez entre chaque jeu (30s minimum)")
    
    elif not results['basic']:
        print("\n❌ PROBLÈME MAJEUR: Impossible d'accéder à GameFAQs")
        print("\nCauses possibles:")
        print("  • Votre IP est bloquée par GameFAQs")
        print("  • Problème de connexion internet")
        print("  • Firewall/antivirus bloque l'accès")
        print("\nSolutions:")
        print("  1. Utilisez un VPN (changez de serveur)")
        print("  2. Attendez 1-2 heures et réessayez")
        print("  3. Essayez depuis un autre réseau (4G, autre WiFi)")
        print("  4. Vérifiez votre firewall")
    
    elif not results['headers']:
        print("\n⚠️  Les headers ne suffisent pas")
        print("\nGameFAQs utilise probablement des mesures anti-bot avancées.")
        print("\nSolutions:")
        print("  1. Utilisez un VPN")
        print("  2. Attendez plusieurs heures")
        print("  3. Essayez depuis un autre appareil/réseau")
    
    else:
        print("\n⚠️  Accès partiel")
        print("\nGameFAQs vous laisse accéder mais limite certaines pages.")
        print("\nSolutions:")
        print("  1. Augmentez les délais (5-10s entre requêtes)")
        print("  2. Limitez le nombre de guides par session")
        print("  3. Espacez vos sessions de scraping (plusieurs heures)")
    
    print("\n" + "="*70)
    print("ALTERNATIVES SI RIEN NE FONCTIONNE")
    print("="*70)
    print("\n1. Scraping manuel:")
    print("   • Ouvrez GameFAQs dans votre navigateur")
    print("   • Copiez les guides manuellement")
    print("   • Sauvegardez en .txt ou .md")
    
    print("\n2. Sources alternatives:")
    print("   • IGN Guides: https://www.ign.com/wikis")
    print("   • Steam Community Guides")
    print("   • Reddit wikis (/r/NintendoSwitch, etc.)")
    print("   • YouTube (avec transcripts)")
    
    print("\n3. Datasets existants:")
    print("   • Kaggle datasets de guides de jeux")
    print("   • GitHub archives de guides")
    
    print("\n" + "="*70)


def main():
    """Point d'entrée."""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║          Diagnostic GameFAQs - Test de Connexion              ║
╚═══════════════════════════════════════════════════════════════╝
""")
    
    print("Ce script va tester votre accès à GameFAQs.\n")
    
    input("Appuyez sur Entrée pour commencer les tests...")
    
    print_diagnostic()
    
    print("\n✅ Tests terminés!")
    print("\nPour plus d'aide, consultez TROUBLESHOOTING_403.md\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrompu.")
        sys.exit(0)
