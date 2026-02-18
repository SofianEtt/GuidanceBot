#!/usr/bin/env python3
"""
Vérification des embeddings avant indexation ChromaDB.
Détecte les problèmes potentiels (None, types incorrects, etc.)
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List

def check_embedding_file(file_path: Path) -> Dict:
    """
    Vérifie un fichier d'embeddings.
    
    Returns:
        Dictionnaire avec les problèmes trouvés
    """
    issues = {
        'file': file_path.name,
        'errors': [],
        'warnings': [],
        'chunks_checked': 0,
        'chunks_ok': 0
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        chunks = data.get('chunks', [])
        issues['chunks_checked'] = len(chunks)
        
        if not chunks:
            issues['errors'].append("Aucun chunk dans le fichier")
            return issues
        
        for i, chunk in enumerate(chunks):
            chunk_issues = []
            
            # Vérifier les champs requis
            if 'chunk_id' not in chunk:
                chunk_issues.append(f"Chunk {i}: Pas de chunk_id")
            
            if 'text' not in chunk or not chunk['text']:
                chunk_issues.append(f"Chunk {i}: Pas de texte")
            
            if 'embedding' not in chunk:
                chunk_issues.append(f"Chunk {i}: Pas d'embedding")
            elif not isinstance(chunk['embedding'], list):
                chunk_issues.append(f"Chunk {i}: Embedding n'est pas une liste")
            
            # Vérifier les métadonnées pour None
            metadata_fields = [
                'game_name', 'source_url', 'section_title',
                'section_level', 'chunk_number', 'word_count',
                'estimated_tokens', 'content_type',
                'has_code', 'has_table', 'has_list'
            ]
            
            for field in metadata_fields:
                value = chunk.get(field)
                
                # None est problématique pour ChromaDB
                if value is None:
                    chunk_issues.append(f"Chunk {i}: {field} est None")
                
                # Types incorrects
                if field in ['section_level', 'chunk_number', 'word_count', 'estimated_tokens']:
                    if value is not None and not isinstance(value, (int, float)):
                        chunk_issues.append(f"Chunk {i}: {field} n'est pas un nombre ({type(value).__name__})")
                
                if field in ['has_code', 'has_table', 'has_list']:
                    if value is not None and not isinstance(value, bool):
                        chunk_issues.append(f"Chunk {i}: {field} n'est pas un booléen ({type(value).__name__})")
            
            if chunk_issues:
                issues['errors'].extend(chunk_issues)
            else:
                issues['chunks_ok'] += 1
        
    except json.JSONDecodeError as e:
        issues['errors'].append(f"Erreur JSON: {e}")
    except Exception as e:
        issues['errors'].append(f"Erreur: {e}")
    
    return issues


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="Vérifier les embeddings avant indexation"
    )
    parser.add_argument(
        '-i', '--input',
        type=str,
        default='data/embeddings',
        help="Répertoire contenant les embeddings"
    )
    parser.add_argument(
        '--fix',
        action='store_true',
        help="Corriger automatiquement les problèmes (crée de nouveaux fichiers)"
    )
    
    args = parser.parse_args()
    
    print("""
╔═══════════════════════════════════════════════════════════════╗
║          Embeddings Validator - ChromaDB Ready                ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    embeddings_dir = Path(args.input)
    
    if not embeddings_dir.exists():
        print(f"❌ Répertoire non trouvé: {args.input}")
        return
    
    # Trouver tous les fichiers
    embedding_files = list(embeddings_dir.glob("*_embeddings.json"))
    
    if not embedding_files:
        print(f"❌ Aucun fichier embeddings trouvé")
        return
    
    print(f"📁 {len(embedding_files)} fichiers à vérifier\n")
    
    # Vérifier chaque fichier
    total_errors = 0
    total_warnings = 0
    files_with_errors = []
    
    for file_path in embedding_files:
        print(f"🔍 Vérification: {file_path.name}")
        
        issues = check_embedding_file(file_path)
        
        if issues['errors']:
            print(f"  ❌ {len(issues['errors'])} erreur(s)")
            for error in issues['errors'][:5]:  # Montrer max 5 erreurs
                print(f"     • {error}")
            if len(issues['errors']) > 5:
                print(f"     ... et {len(issues['errors']) - 5} autres erreurs")
            
            total_errors += len(issues['errors'])
            files_with_errors.append(file_path.name)
        else:
            print(f"  ✅ OK ({issues['chunks_ok']} chunks)")
        
        if issues['warnings']:
            print(f"  ⚠️  {len(issues['warnings'])} avertissement(s)")
            total_warnings += len(issues['warnings'])
        
        print()
    
    # Résumé
    print("="*70)
    print("📊 RÉSUMÉ")
    print("="*70)
    print(f"  • Fichiers vérifiés:      {len(embedding_files)}")
    print(f"  • Fichiers avec erreurs:  {len(files_with_errors)}")
    print(f"  • Total erreurs:          {total_errors}")
    print(f"  • Total avertissements:   {total_warnings}")
    print("="*70)
    
    if files_with_errors:
        print(f"\n⚠️  Fichiers problématiques:")
        for fname in files_with_errors:
            print(f"  • {fname}")
        
        print(f"\n💡 Solution:")
        print(f"  Le problème vient probablement du chunking.")
        print(f"  Re-chunkez vos guides avec le chunker corrigé:")
        print(f"    python chunker.py -i data/guides -o data/chunks")
        print(f"  Puis re-générez les embeddings:")
        print(f"    python generate_embeddings.py -i data/chunks -o data/embeddings")
    else:
        print(f"\n✅ Tous les fichiers sont prêts pour ChromaDB!")
        print(f"\nVous pouvez maintenant indexer:")
        print(f"  python index_vectordb.py -i {args.input}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Vérification interrompue.")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        raise
