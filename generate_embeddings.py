#!/usr/bin/env python3
"""
Générateur d'embeddings pour chunks de guides de jeux.
Utilise sentence-transformers (all-MiniLM-L6-v2) - GRATUIT et LOCAL.
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import numpy as np
from tqdm import tqdm

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("❌ sentence-transformers n'est pas installé")
    print("\nInstallez avec:")
    print("  pip install sentence-transformers")
    exit(1)


class EmbeddingGenerator:
    """Générateur d'embeddings pour RAG."""
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        batch_size: int = 32,
        show_progress: bool = True
    ):
        """
        Initialize le générateur.
        
        Args:
            model_name: Nom du modèle sentence-transformers
            batch_size: Taille des batchs pour traitement
            show_progress: Afficher la barre de progression
        """
        self.model_name = model_name
        self.batch_size = batch_size
        self.show_progress = show_progress
        
        print(f"📦 Chargement du modèle: {model_name}")
        self.model = SentenceTransformer(model_name)
        print(f"✓ Modèle chargé ({self.model.get_sentence_embedding_dimension()} dimensions)\n")
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Génère les embeddings pour une liste de textes.
        
        Args:
            texts: Liste de textes
        
        Returns:
            Array numpy des embeddings
        """
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=self.show_progress,
            convert_to_numpy=True
        )
        return embeddings
    
    def process_chunks_file(
        self,
        chunks_file: Path,
        output_dir: Path
    ) -> tuple[int, Path]:
        """
        Traite un fichier de chunks et génère les embeddings.
        
        Args:
            chunks_file: Fichier JSON contenant les chunks
            output_dir: Répertoire de sortie
        
        Returns:
            Tuple (nombre de chunks traités, fichier de sortie)
        """
        # Charger les chunks
        with open(chunks_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        chunks = data['chunks']
        
        if not chunks:
            print(f"⚠️  Aucun chunk dans {chunks_file.name}")
            return 0, None
        
        # Extraire les textes
        texts = [chunk['text'] for chunk in chunks]
        
        # Générer les embeddings
        print(f"  Génération de {len(texts)} embeddings...")
        embeddings = self.generate_embeddings(texts)
        
        # Ajouter les embeddings aux chunks
        for i, chunk in enumerate(chunks):
            chunk['embedding'] = embeddings[i].tolist()
        
        # Préparer les données de sortie
        output_data = {
            'guide_metadata': data.get('guide_metadata', {}),
            'chunking_config': data.get('chunking_config', {}),
            'embedding_config': {
                'model': self.model_name,
                'dimensions': self.model.get_sentence_embedding_dimension(),
                'generated_at': datetime.now().isoformat()
            },
            'processing_info': data.get('processing_info', {}),
            'chunks': chunks
        }
        
        # Sauvegarder
        output_file = output_dir / f"{chunks_file.stem}_embeddings.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        return len(chunks), output_file
    
    def process_all_chunks(
        self,
        input_dir: Path,
        output_dir: Path
    ) -> Dict[str, int]:
        """
        Traite tous les fichiers de chunks d'un répertoire.
        
        Args:
            input_dir: Répertoire contenant les chunks
            output_dir: Répertoire de sortie
        
        Returns:
            Statistiques de traitement
        """
        # Trouver tous les fichiers de chunks
        chunk_files = list(input_dir.glob("*_chunks.json"))
        
        if not chunk_files:
            print(f"❌ Aucun fichier chunks trouvé dans {input_dir}")
            return {}
        
        print(f"📁 {len(chunk_files)} fichiers de chunks trouvés\n")
        
        # Créer le répertoire de sortie
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Traiter chaque fichier
        total_chunks = 0
        processed_files = 0
        failed_files = 0
        
        for chunks_file in tqdm(chunk_files, desc="📊 Traitement des fichiers"):
            try:
                count, output_file = self.process_chunks_file(chunks_file, output_dir)
                
                if count > 0:
                    total_chunks += count
                    processed_files += 1
                    tqdm.write(f"  ✓ {chunks_file.name}: {count} embeddings → {output_file.name}")
                else:
                    failed_files += 1
                    
            except Exception as e:
                tqdm.write(f"  ❌ Erreur pour {chunks_file.name}: {e}")
                failed_files += 1
        
        return {
            'total_files': len(chunk_files),
            'processed': processed_files,
            'failed': failed_files,
            'total_chunks': total_chunks
        }


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="Générateur d'embeddings pour chunks de guides"
    )
    parser.add_argument(
        '-i', '--input',
        type=str,
        default='data/chunks',
        help="Répertoire contenant les chunks (défaut: data/chunks)"
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='data/embeddings',
        help="Répertoire de sortie (défaut: data/embeddings)"
    )
    parser.add_argument(
        '-m', '--model',
        type=str,
        default='all-MiniLM-L6-v2',
        help="Modèle sentence-transformers (défaut: all-MiniLM-L6-v2)"
    )
    parser.add_argument(
        '-b', '--batch-size',
        type=int,
        default=32,
        help="Taille des batchs (défaut: 32)"
    )
    parser.add_argument(
        '--no-progress',
        action='store_true',
        help="Désactiver la barre de progression"
    )
    
    args = parser.parse_args()
    
    print("""
╔═══════════════════════════════════════════════════════════════╗
║        Embedding Generator - Gaming Guides                    ║
║        Modèle Local: sentence-transformers                    ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    
    if not input_dir.exists():
        print(f"❌ Répertoire d'entrée non trouvé: {args.input}")
        return
    
    # Configuration
    print("⚙️  Configuration:")
    print(f"  • Modèle:         {args.model}")
    print(f"  • Batch size:     {args.batch_size}")
    print(f"  • Input:          {input_dir}")
    print(f"  • Output:         {output_dir}")
    
    # Confirmer
    print("\n" + "="*70)
    response = input("▶️  Commencer la génération des embeddings? [O/n]: ").strip().lower()
    if response and response not in ['o', 'oui', 'y', 'yes']:
        print("❌ Opération annulée.")
        return
    
    print("\n")
    
    # Initialiser le générateur
    generator = EmbeddingGenerator(
        model_name=args.model,
        batch_size=args.batch_size,
        show_progress=not args.no_progress
    )
    
    # Traiter tous les chunks
    import time
    start_time = time.time()
    
    stats = generator.process_all_chunks(input_dir, output_dir)
    
    elapsed = time.time() - start_time
    
    # Résumé
    print("\n" + "="*70)
    print("📊 RÉSUMÉ")
    print("="*70)
    print(f"  • Fichiers traités:   {stats.get('processed', 0)}")
    print(f"  • Fichiers échoués:   {stats.get('failed', 0)}")
    print(f"  • Total embeddings:   {stats.get('total_chunks', 0)}")
    print(f"  • Temps écoulé:       {elapsed:.1f}s")
    
    if stats.get('total_chunks', 0) > 0:
        avg_time = elapsed / stats['total_chunks']
        print(f"  • Temps moyen:        {avg_time*1000:.1f}ms par chunk")
    
    print("="*70)
    print(f"\n📁 Embeddings sauvegardés dans: {output_dir}/")
    print("\n💡 Prochaines étapes:")
    print("  1. Indexer les embeddings dans une base vectorielle (Chroma, FAISS)")
    print("  2. Créer votre Discord bot")
    print("  3. Implémenter la recherche sémantique")
    print("\n✅ Génération terminée!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Opération interrompue.")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        raise
