#!/usr/bin/env python3
"""Importer les embeddings JSON (dans data/embeddings) vers une collection ChromaDB.

Usage examples:
  python interactchromadb.py --collection my_collection
  python interactchromadb.py --collection guides --replace
"""

import os
import json
import argparse
from typing import List, Tuple


import chromadb
from chromadb.config import Settings

def find_embedding_files(dirpath: str) -> List[str]:
	files = []
	for fn in os.listdir(dirpath):
		if fn.endswith("_embeddings.json"):
			files.append(os.path.join(dirpath, fn))
	return sorted(files)


def load_file(file_path: str) -> Tuple[List[str], List[str], List[dict], List[List[float]]]:
	with open(file_path, "r", encoding="utf-8") as f:
		data = json.load(f)

	chunks = data.get("chunks", [])
	base = os.path.splitext(os.path.basename(file_path))[0]

	ids = []
	docs = []
	metas = []
	embs = []

	guide_meta = data.get("guide_metadata", {})

	seen_ids = set()
	for idx, c in enumerate(chunks):
		cid = c.get("chunk_id") or str(idx)
		candidate = f"{base}::{cid}"
		# assurer l'unicité locale des IDs (ajouter un suffixe si collision)
		if candidate in seen_ids:
			suffix = 1
			new_cand = f"{candidate}::{suffix}"
			while new_cand in seen_ids:
				suffix += 1
				new_cand = f"{candidate}::{suffix}"
			candidate = new_cand
		seen_ids.add(candidate)

		ids.append(candidate)
		docs.append(c.get("text", ""))
		meta = {
			"source_file": base,
			"chunk_id": cid,
			"game_name": guide_meta.get("game_name"),
			"source_url": guide_meta.get("source_url"),
		}
		metas.append(meta)
		embs.append(c.get("embedding"))

	return ids, docs, metas, embs


def chunked(iterable, size: int):
	for i in range(0, len(iterable), size):
		yield i, min(i + size, len(iterable))


def main():
	p = argparse.ArgumentParser(description="Import embeddings JSON into a ChromaDB collection")
	p.add_argument("--emb-dir", default="data/embeddings", help="Dossier contenant les fichiers d'embed JSON")
	p.add_argument("--collection", required=True, help="Nom de la collection ChromaDB à créer / utiliser")
	p.add_argument("--batch", type=int, default=500, help="Taille de lot pour l'insertion")
	p.add_argument("--replace", action="store_true", help="Supprimer la collection existante avant d'insérer")
	p.add_argument("--list-collections", action="store_true", help="Lister les collections et quitter")
	args = p.parse_args()

	client = chromadb.PersistentClient("db")
	
	# diagnostic: list existing collections
	if args.list_collections:
		try:
			cols = client.list_collections()
			print(f"Collections disponibles ({len(cols)}):")
			for col in cols:
				name = col.get('name') if isinstance(col, dict) else (getattr(col, 'name', None) or str(col))
				print(f"  - {name}")
			return
		except Exception as e:
			print(f"Erreur lors du listage: {e}")
			return

	# create / get collection
	if args.replace:
		try:
			client.delete_collection(name=args.collection)
			print(f"Collection '{args.collection}' supprimée (replace=True)")
		except Exception:
			pass

	try:
		collection = client.get_collection(name=args.collection)
		print(f"Utilisation de la collection existante: {args.collection}")
	except Exception:
		collection = client.create_collection(name=args.collection)
		print(f"Collection créée: {args.collection}")

	files = find_embedding_files(args.emb_dir)
	if not files:
		print(f"Aucun fichier d'embeddings trouvé dans {args.emb_dir}")
		return

	total_added = 0
	for fp in files:
		print(f"Traitement: {fp}")
		ids, docs, metas, embs = load_file(fp)
		if not ids:
			print("  Aucun chunk trouvé, saut.")
			continue

		# insert in batches
		for i, j in chunked(ids, args.batch):
			batch_ids = ids[i:j]
			batch_docs = docs[i:j]
			batch_metas = metas[i:j]
			batch_embs = embs[i:j]

			collection.add(
				ids=batch_ids,
				documents=batch_docs,
				metadatas=batch_metas,
				embeddings=batch_embs,
			)
			total_added += len(batch_ids)
			print(f"  Inséré {len(batch_ids)} items (total {total_added})")

	print(f"Terminé. Total inséré: {total_added} items dans la collection '{args.collection}'")


if __name__ == "__main__":
	main()