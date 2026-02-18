#!/usr/bin/env python3
"""Faire une requête de test sur une collection ChromaDB.

Usage:
  python3 query_collection.py --collection guidancebot --query "boss fight strategy"
  python3 query_collection.py --collection guidancebot --query "combat" --top 10
"""

import argparse
import json
import sys
from typing import List

import chromadb


def query_collection(collection_name: str, query_text: str, n_results: int = 5):
    """Query a ChromaDB collection using semantic search."""
    client = chromadb.PersistentClient("db")
    
    try:
        col = client.get_collection(name=collection_name)
    except Exception as e:
        print(f"❌ Erreur: impossible d'ouvrir la collection '{collection_name}': {e}")
        print("\nCollections disponibles:")
        try:
            cols = client.list_collections()
            for c in cols:
                name = c.get('name') if isinstance(c, dict) else (getattr(c, 'name', None) or str(c))
                print(f"  - {name}")
        except Exception:
            pass
        sys.exit(1)
    
    # Get count
    try:
        count = col.count()
        print(f"✓ Collection trouvée: {collection_name} ({count} documents)")
    except Exception:
        print(f"✓ Collection trouvée: {collection_name}")
    
    # Query
    print(f"\n📝 Requête: \"{query_text}\"")
    print(f"📊 Top {n_results} résultats:\n")
    
    try:
        results = col.query(
            query_texts=[query_text],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        if not results or not results.get("ids") or not results["ids"][0]:
            print("⚠️  Aucun résultat trouvé")
            return
        
        ids = results["ids"][0]
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        
        for i, (id_val, doc, meta, dist) in enumerate(zip(ids, docs, metas, distances)):
            similarity = 1 - (dist / 2) if dist else 0  # rough conversion
            print(f"--- Résultat {i+1} (similarité: {similarity:.2%}) ---")
            print(f"ID: {id_val}")
            if meta:
                print(f"Métadonnées: {json.dumps(meta, ensure_ascii=False)}")
            if doc:
                preview = (doc[:300] + "...") if len(doc) > 300 else doc
                print(f"Contenu:\n{preview}")
            print()
            
    except Exception as e:
        print(f"❌ Erreur requête: {e}")
        sys.exit(1)


def main():
    p = argparse.ArgumentParser(description="Query a ChromaDB collection with semantic search")
    p.add_argument("--collection", required=True, help="Collection name")
    p.add_argument("--query", required=True, help="Query text to search for")
    p.add_argument("--top", type=int, default=5, help="Number of results to return")
    args = p.parse_args()
    
    query_collection(args.collection, args.query, args.top)


if __name__ == "__main__":
    main()
