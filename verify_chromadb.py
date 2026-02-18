#!/usr/bin/env python3
"""Vérifier le contenu d'une collection ChromaDB.

Usage:
  python verify_chromadb.py --collection my_collection --sample 5

Ce script tente plusieurs méthodes de l'API Chroma pour lister/compter
et afficher un échantillon des documents et metadatas.
"""

import argparse
import json
import sys

import chromadb
from chromadb.config import Settings

def print_sample_from_get(result, n=5):
    # result peut contenir 'ids', 'documents', 'metadatas', 'embeddings'
    ids = result.get("ids") or result.get("_ids") or []
    docs = result.get("documents") or result.get("_documents") or []
    metas = result.get("metadatas") or result.get("_metadatas") or []

    count = len(ids)
    print(f" -> récupéré {count} items")
    limit = min(n, count)
    for i in range(limit):
        print(f"--- item {i+1}/{limit} ---")
        print("id:", ids[i])
        if i < len(metas):
            print("meta:", json.dumps(metas[i], ensure_ascii=False))
        if i < len(docs):
            text = docs[i]
            print("doc:", (text[:400] + '...') if isinstance(text, str) and len(text) > 400 else text)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--collection", help="Nom de la collection ChromaDB à vérifier")
    p.add_argument("--sample", type=int, default=5, help="Nombre d'exemples à afficher")
    p.add_argument("--list", action="store_true", help="Lister toutes les collections")
    args = p.parse_args()

    client = chromadb.PersistentClient("db")

    
    # mode: list collections
    if args.list:
        try:
            cols = client.list_collections()
            print(f"Collections disponibles ({len(cols)}):")
            for col in cols:
                name = col.get('name') if isinstance(col, dict) else (getattr(col, 'name', None) or str(col))
                print(f"  - {name}")
            return
        except Exception as e:
            print(f"Erreur listage: {e}")
            sys.exit(1)
    
    # mode: verify specific collection
    if not args.collection:
        print("Usage: python3 verify_chromadb.py --collection <name> [--sample N]")
        print("   or: python3 verify_chromadb.py --list")
        sys.exit(1)
    
    try:
        col = client.get_collection(name=args.collection)
    except Exception as e:
        print(f"Erreur: impossible d'ouvrir la collection '{args.collection}': {e}")
        print("\nCollections disponibles:")
        try:
            cols = client.list_collections()
            for c in cols:
                name = c.get('name') if isinstance(c, dict) else (getattr(c, 'name', None) or str(c))
                print(f"  - {name}")
        except Exception:
            pass
        sys.exit(1)

    print(f"Collection trouvée: {args.collection}")

    # 1) tenter .count()
    try:
        c = col.count()
        print(f"Nombre total (count): {c}")
    except Exception:
        print("Méthode .count() indisponible pour cette version de Chroma.")

    # 2) tenter get_all()
    try:
        all_data = col.get_all()
        print("get_all() OK")
        print_sample_from_get(all_data, n=args.sample)
        return
    except Exception:
        print("get_all() indisponible ou a échoué — tentative d'autres méthodes...")

    # 3) tenter get() sans ids (certains backends acceptent query vide)
    try:
        res = col.get(include=["ids", "documents", "metadatas"])
        print("get(include=...) OK")
        print_sample_from_get(res, n=args.sample)
        return
    except Exception:
        pass

    # 4) fallback: lister quelques ids connus (ex: lecture d'un fichier d'embed)
    print("Aucune méthode standard fonctionnelle. Vous pouvez: ")
    print(" - vérifier le fichier de base de données chroma (ex: chroma-data/chroma.sqlite3)")
    print(" - ou fournir des IDs explicites et utiliser col.get(ids=[...])")


if __name__ == "__main__":
    main()
