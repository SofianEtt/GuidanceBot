#!/usr/bin/env python3
"""
Indexeur de base vectorielle avec ChromaDB.
Charge les embeddings et les indexe pour la recherche sémantique.
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Optional
from tqdm import tqdm
import chromadb
from chromadb.config import Settings

class VectorDBIndexer:
    """Indexeur pour ChromaDB."""
    
    def __init__(
        self,
        db_path: str = "data/chromadb",
        collection_name: str = "gaming_guides"
    ):
        """
        Initialize l'indexeur.
        
        Args:
            db_path: Chemin de la base de données ChromaDB
            collection_name: Nom de la collection
        """
        self.db_path = Path(db_path)
        self.collection_name = collection_name
        
        # Créer le répertoire si nécessaire
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        # Initialiser ChromaDB
        print(f"📦 Initialisation de ChromaDB...")
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Créer ou récupérer la collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            print(f"✓ Collection '{collection_name}' chargée ({self.collection.count()} documents)")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "Gaming guides embeddings for RAG"}
            )
            print(f"✓ Collection '{collection_name}' créée")
    
    def load_embeddings_file(self, embeddings_file: Path) -> Dict:
        """
        Charge un fichier d'embeddings.
        
        Args:
            embeddings_file: Fichier JSON des embeddings
        
        Returns:
            Données des embeddings
        """
        with open(embeddings_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def index_chunks(
        self,
        embeddings_file: Path,
        batch_size: int = 100
    ) -> int:
        """
        Indexe les chunks d'un fichier dans ChromaDB.
        
        Args:
            embeddings_file: Fichier contenant les embeddings
            batch_size: Taille des batchs pour l'indexation
        
        Returns:
            Nombre de chunks indexés
        """
        # Charger les données
        data = self.load_embeddings_file(embeddings_file)
        chunks = data.get('chunks', [])
        
        if not chunks:
            print(f"⚠️  Aucun chunk dans {embeddings_file.name}")
            return 0
        
        # Préparer les données pour ChromaDB
        ids = []
        embeddings = []
        documents = []
        metadatas = []
        
        for chunk in chunks:
            # ID unique
            ids.append(chunk['chunk_id'])
            
            # Embedding
            embeddings.append(chunk['embedding'])
            
            # Document (texte)
            documents.append(chunk['text'])
            
            # Métadonnées (tout sauf embedding et texte)
            # ChromaDB n'accepte pas les None - filtrer ou remplacer
            metadata = {
                'game_name': chunk.get('game_name') or 'Unknown',
                'source_url': chunk.get('source_url') or '',
                'section_title': chunk.get('section_title') or '',
                'section_level': chunk.get('section_level') if chunk.get('section_level') is not None else 0,
                'chunk_number': chunk.get('chunk_number') if chunk.get('chunk_number') is not None else 0,
                'word_count': chunk.get('word_count') or 0,
                'estimated_tokens': chunk.get('estimated_tokens') or 0,
                'content_type': ','.join(chunk.get('content_type', [])) or 'general',
                'has_code': bool(chunk.get('has_code', False)),
                'has_table': bool(chunk.get('has_table', False)),
                'has_list': bool(chunk.get('has_list', False)),
            }
            
            # Supprimer les None restants (sécurité supplémentaire)
            metadata = {k: v for k, v in metadata.items() if v is not None}
            
            metadatas.append(metadata)
        
        # Indexer par batchs
        total_indexed = 0
        
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i+batch_size]
            batch_embeddings = embeddings[i:i+batch_size]
            batch_documents = documents[i:i+batch_size]
            batch_metadatas = metadatas[i:i+batch_size]
            
            self.collection.add(
                ids=batch_ids,
                embeddings=batch_embeddings,
                documents=batch_documents,
                metadatas=batch_metadatas
            )
            
            total_indexed += len(batch_ids)
        
        return total_indexed
    
    def index_all_embeddings(
        self,
        embeddings_dir: Path,
        batch_size: int = 100
    ) -> Dict[str, int]:
        """
        Indexe tous les fichiers d'embeddings d'un répertoire.
        
        Args:
            embeddings_dir: Répertoire contenant les embeddings
            batch_size: Taille des batchs
        
        Returns:
            Statistiques d'indexation
        """
        # Trouver tous les fichiers d'embeddings
        embedding_files = list(embeddings_dir.glob("*_embeddings.json"))
        
        if not embedding_files:
            print(f"❌ Aucun fichier embeddings trouvé dans {embeddings_dir}")
            return {}
        
        print(f"📁 {len(embedding_files)} fichiers d'embeddings trouvés\n")
        
        total_chunks = 0
        processed_files = 0
        failed_files = 0
        
        for embeddings_file in tqdm(embedding_files, desc="📊 Indexation"):
            try:
                count = self.index_chunks(embeddings_file, batch_size)
                
                if count > 0:
                    total_chunks += count
                    processed_files += 1
                    tqdm.write(f"  ✓ {embeddings_file.name}: {count} chunks indexés")
                else:
                    failed_files += 1
                    
            except Exception as e:
                tqdm.write(f"  ❌ Erreur pour {embeddings_file.name}: {e}")
                failed_files += 1
        
        return {
            'total_files': len(embedding_files),
            'processed': processed_files,
            'failed': failed_files,
            'total_chunks': total_chunks
        }
    
    def search(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        game_filter: Optional[str] = None,
        content_type_filter: Optional[str] = None
    ) -> Dict:
        """
        Recherche sémantique dans la base vectorielle.
        
        Args:
            query_embedding: Embedding de la question
            n_results: Nombre de résultats à retourner
            game_filter: Filtrer par jeu (optionnel)
            content_type_filter: Filtrer par type (boss, quest, etc.)
        
        Returns:
            Résultats de la recherche
        """
        # Construire le filtre
        where = {}
        if game_filter:
            where['game_name'] = game_filter
        if content_type_filter:
            where['content_type'] = {"$contains": content_type_filter}
        
        # Rechercher
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where if where else None
        )
        
        return results
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques de la collection."""
        total_docs = self.collection.count()
        
        # Compter par jeu
        # Note: ChromaDB ne supporte pas les agrégations facilement
        # On fait une approximation
        
        return {
            'total_documents': total_docs,
            'collection_name': self.collection_name,
            'db_path': str(self.db_path)
        }


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="Indexer les embeddings dans ChromaDB"
    )
    parser.add_argument(
        '-i', '--input',
        type=str,
        default='data/embeddings',
        help="Répertoire contenant les embeddings (défaut: data/embeddings)"
    )
    parser.add_argument(
        '-d', '--db-path',
        type=str,
        default='data/chromadb',
        help="Chemin de la base ChromaDB (défaut: data/chromadb)"
    )
    parser.add_argument(
        '-c', '--collection',
        type=str,
        default='gaming_guides',
        help="Nom de la collection (défaut: gaming_guides)"
    )
    parser.add_argument(
        '-b', '--batch-size',
        type=int,
        default=100,
        help="Taille des batchs (défaut: 100)"
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help="Réinitialiser la collection (supprime les données existantes)"
    )
    
    args = parser.parse_args()
    
    print("""
╔═══════════════════════════════════════════════════════════════╗
║        Vector Database Indexer - ChromaDB                     ║
║        Indexation pour RAG avec recherche sémantique          ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    embeddings_dir = Path(args.input)
    
    if not embeddings_dir.exists():
        print(f"❌ Répertoire d'embeddings non trouvé: {args.input}")
        return
    
    # Configuration
    print("⚙️  Configuration:")
    print(f"  • Embeddings:     {embeddings_dir}")
    print(f"  • Base de données: {args.db_path}")
    print(f"  • Collection:     {args.collection}")
    print(f"  • Batch size:     {args.batch_size}")
    
    if args.reset:
        print(f"  • ⚠️  Mode reset:   Oui (supprime les données existantes)")
    
    # Confirmer
    print("\n" + "="*70)
    response = input("▶️  Commencer l'indexation? [O/n]: ").strip().lower()
    if response and response not in ['o', 'oui', 'y', 'yes']:
        print("❌ Opération annulée.")
        return
    
    print("\n")
    
    # Initialiser l'indexeur
    indexer = VectorDBIndexer(
        db_path=args.db_path,
        collection_name=args.collection
    )
    
    # Reset si demandé
    if args.reset:
        print("🗑️  Suppression de la collection existante...")
        indexer.client.delete_collection(name=args.collection)
        indexer.collection = indexer.client.create_collection(
            name=args.collection,
            metadata={"description": "Gaming guides embeddings for RAG"}
        )
        print("✓ Collection réinitialisée\n")
    
    # Indexer tous les embeddings
    import time
    start_time = time.time()
    
    stats = indexer.index_all_embeddings(embeddings_dir, args.batch_size)
    
    elapsed = time.time() - start_time
    
    # Résumé
    print("\n" + "="*70)
    print("📊 RÉSUMÉ")
    print("="*70)
    print(f"  • Fichiers traités:   {stats.get('processed', 0)}")
    print(f"  • Fichiers échoués:   {stats.get('failed', 0)}")
    print(f"  • Total indexé:       {stats.get('total_chunks', 0)} chunks")
    print(f"  • Temps écoulé:       {elapsed:.1f}s")
    print("="*70)
    
    # Stats de la collection
    collection_stats = indexer.get_stats()
    print(f"\n📚 Collection '{collection_stats['collection_name']}':")
    print(f"  • Documents totaux:   {collection_stats['total_documents']}")
    print(f"  • Base de données:    {collection_stats['db_path']}")
    
    print("\n💡 Prochaines étapes:")
    print("  1. Tester la recherche sémantique")
    print("  2. Créer le pipeline RAG avec Mistral 7B")
    print("  3. Intégrer dans le Discord bot")
    print("\n✅ Indexation terminée!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Opération interrompue.")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        raise
