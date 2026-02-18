#!/usr/bin/env python3
"""
Script de vérification GPU pour embeddings.
Teste si PyTorch détecte votre GPU et l'utilise correctement.
"""

import sys

print("""
╔═══════════════════════════════════════════════════════════════╗
║          GPU Detection & Verification                         ║
╚═══════════════════════════════════════════════════════════════╝
""")

# Test 1: PyTorch installé ?
print("="*70)
print("TEST 1: PyTorch Installation")
print("="*70)

try:
    import torch
    print(f"✅ PyTorch installé: version {torch.__version__}")
except ImportError:
    print("❌ PyTorch n'est pas installé!")
    print("\nInstallez avec:")
    print("  pip install torch")
    sys.exit(1)

# Test 2: CUDA disponible ?
print("\n" + "="*70)
print("TEST 2: CUDA Disponible")
print("="*70)

cuda_available = torch.cuda.is_available()
print(f"CUDA disponible: {'✅ OUI' if cuda_available else '❌ NON'}")

if cuda_available:
    print(f"Version CUDA: {torch.version.cuda}")
    print(f"Nombre de GPU: {torch.cuda.device_count()}")
    
    for i in range(torch.cuda.device_count()):
        print(f"\nGPU {i}:")
        print(f"  • Nom: {torch.cuda.get_device_name(i)}")
        print(f"  • Mémoire totale: {torch.cuda.get_device_properties(i).total_memory / 1e9:.2f} GB")
        print(f"  • Compute capability: {torch.cuda.get_device_properties(i).major}.{torch.cuda.get_device_properties(i).minor}")
else:
    print("\n⚠️  Pas de GPU détecté. Causes possibles:")
    print("  1. Vous n'avez pas de GPU NVIDIA")
    print("  2. Les drivers NVIDIA ne sont pas installés")
    print("  3. PyTorch CPU-only est installé")
    print("\nVous utiliserez le CPU (plus lent mais fonctionnel)")

# Test 3: Sentence-transformers installé ?
print("\n" + "="*70)
print("TEST 3: Sentence-Transformers Installation")
print("="*70)

try:
    from sentence_transformers import SentenceTransformer
    print("✅ sentence-transformers installé")
except ImportError:
    print("❌ sentence-transformers n'est pas installé!")
    print("\nInstallez avec:")
    print("  pip install sentence-transformers")
    sys.exit(1)

# Test 4: Chargement du modèle et test
print("\n" + "="*70)
print("TEST 4: Test de Performance GPU vs CPU")
print("="*70)

print("\n📦 Chargement du modèle all-MiniLM-L6-v2...")

try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Vérifier quel device est utilisé
    device = model.device
    print(f"✅ Modèle chargé sur: {device}")
    
    if cuda_available:
        print(f"\n🔍 Vérification de l'utilisation GPU...")
        
        # Tester avec quelques phrases
        test_sentences = [
            "How to beat the boss in Elden Ring?",
            "Where to find the best weapons?",
            "Quest guide for Dark Souls 3",
            "Achievement walkthrough complete"
        ] * 25  # 100 phrases
        
        import time
        
        # Test sur GPU
        print(f"\n⏱️  Test sur GPU...")
        start = time.time()
        embeddings_gpu = model.encode(test_sentences, show_progress_bar=False)
        gpu_time = time.time() - start
        print(f"  Temps GPU: {gpu_time:.3f}s pour 100 phrases")
        print(f"  Vitesse: {len(test_sentences)/gpu_time:.1f} phrases/sec")
        
        # Test sur CPU
        print(f"\n⏱️  Test sur CPU (pour comparaison)...")
        model_cpu = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
        start = time.time()
        embeddings_cpu = model_cpu.encode(test_sentences, show_progress_bar=False)
        cpu_time = time.time() - start
        print(f"  Temps CPU: {cpu_time:.3f}s pour 100 phrases")
        print(f"  Vitesse: {len(test_sentences)/cpu_time:.1f} phrases/sec")
        
        # Comparaison
        speedup = cpu_time / gpu_time
        print(f"\n🚀 Accélération GPU: {speedup:.1f}x plus rapide!")
        
        if speedup < 2:
            print(f"\n⚠️  Accélération faible. Vérifiez:")
            print("  • Les drivers NVIDIA sont à jour")
            print("  • CUDA est correctement installé")
            print("  • Pas d'autres programmes utilisant le GPU")
        else:
            print(f"\n✅ GPU fonctionne parfaitement!")
    else:
        # Test CPU uniquement
        print(f"\n⏱️  Test sur CPU...")
        test_sentences = ["Test sentence"] * 100
        
        import time
        start = time.time()
        embeddings = model.encode(test_sentences, show_progress_bar=False)
        cpu_time = time.time() - start
        
        print(f"  Temps: {cpu_time:.3f}s pour 100 phrases")
        print(f"  Vitesse: {len(test_sentences)/cpu_time:.1f} phrases/sec")
        print(f"\n💡 Avec un GPU, ce serait ~5-10x plus rapide!")

except Exception as e:
    print(f"❌ Erreur: {e}")
    sys.exit(1)

# Test 5: Estimation pour votre projet
print("\n" + "="*70)
print("TEST 5: Estimation pour Votre Projet")
print("="*70)

chunks_estimate = 12500  # Estimation
chunk_size = 500  # tokens moyens

if cuda_available:
    # Estimation GPU
    phrases_per_sec = len(test_sentences) / gpu_time
    total_time = chunks_estimate / phrases_per_sec
    
    minutes = int(total_time // 60)
    seconds = int(total_time % 60)
    
    print(f"\n📊 Pour ~{chunks_estimate} chunks:")
    print(f"  • Temps estimé (GPU): {minutes}m {seconds}s")
    print(f"  • Vitesse: {phrases_per_sec:.0f} chunks/sec")
else:
    # Estimation CPU
    phrases_per_sec = len(test_sentences) / cpu_time
    total_time = chunks_estimate / phrases_per_sec
    
    minutes = int(total_time // 60)
    seconds = int(total_time % 60)
    
    print(f"\n📊 Pour ~{chunks_estimate} chunks:")
    print(f"  • Temps estimé (CPU): {minutes}m {seconds}s")
    print(f"  • Vitesse: {phrases_per_sec:.0f} chunks/sec")

# Résumé final
print("\n" + "="*70)
print("RÉSUMÉ")
print("="*70)

if cuda_available:
    print("\n✅ Configuration GPU Détectée!")
    print(f"  • GPU: {torch.cuda.get_device_name(0)}")
    print(f"  • Mémoire: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    print(f"  • Accélération: ~{speedup:.1f}x vs CPU")
    print(f"\n💡 Le script generate_embeddings.py utilisera automatiquement le GPU!")
else:
    print("\n⚠️  Pas de GPU - Utilisation CPU")
    print(f"  • Vitesse: ~{phrases_per_sec:.0f} chunks/sec")
    print(f"  • Temps total estimé: ~{int(total_time//60)} minutes")
    print(f"\n💡 C'est OK! Le CPU fonctionne bien, juste plus lent.")

print("\n" + "="*70)
print("✅ Tests terminés!")
print("="*70)
