#!/usr/bin/env python3
"""
Script pour corriger automatiquement les chunks avec valeurs None.
Corrige les fichiers existants sans avoir à tout re-chunker.
"""

import json
import argparse
from pathlib import Path
from typing import Dict, Any
import shutil

def fix_chunk(chunk: Dict[str, Any]) -> Dict[str, Any]:
    """
    Corrige un chunk en remplaçant les None par des valeurs par défaut.
    
    Args:
        chunk: Chunk à corriger
    
    Returns:
        Chunk corrigé
    """
    # Copier le chunk pour ne pas modifier l'original
    fixed = chunk.copy()
    
    # Corrections des champs textuels
    if fixed.get('game_name') is None:
        fixed['game_name'] = 'Unknown'
    
    if fixed.get('source_url') is None:
        fixed['source_url'] = ''
    
    if fixed.get('section_title') is None:
        fixed['section_title'] = ''
    
    # Corrections des champs numériques
    if fixed.get('section_level') is None:
        fixed['section_level'] = 0
    
    if fixed.get('chunk_number') is None:
        fixed['chunk_number'] = 0
    
    if fixed.get('word_count') is None:
        fixed['word_count'] = len(fixed.get('text', '').split())
    
    if fixed.get('estimated_tokens') is None:
        fixed['estimated_tokens'] = len(fixed.get('text', '')) // 4
    
    # Corrections des listes
    if fixed.get('content_type') is None:
        fixed['content_type'] = []
    elif not isinstance(fixed.get('content_type'), list):
        fixed['content_type'] = []
    
    # Corrections des booléens
    if fixed.get('has_code') is None:
        fixed['has_code'] = False
    
    if fixed.get('has_table') is None:
        fixed['has_table'] = False
    
    if fixed.get('has_list') is None:
        fixed['has_list'] = False
    
    # S'assurer que les types sont corrects
    fixed['has_code'] = bool(fixed['has_code'])
    fixed['has_table'] = bool(fixed['has_table'])
    fixed['has_list'] = bool(fixed['has_list'])
    
    # S'assurer que section_level est un int
    if fixed['section_level'] is not None:
        try:
            fixed['section_level'] = int(fixed['section_level'])
        except (ValueError, TypeError):
            fixed['section_level'] = 0
    
    return fixed


def fix_chunks_file(input_file: Path, output_file: Path = None, backup: bool = True) -> tuple[int, int]:
    """
    Corrige un fichier de chunks.
    
    Args:
        input_file: Fichier d'entrée
        output_file: Fichier de sortie (None = écraser l'original)
        backup: Créer une sauvegarde
    
    Returns:
        Tuple (chunks_total, chunks_fixed)
    """
    # Charger le fichier
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    chunks = data.get('chunks', [])
    
    if not chunks:
        return 0, 0
    
    # Compter les chunks avec problèmes
    chunks_with_issues = 0
    fixed_chunks = []
    
    for chunk in chunks:
        # Vérifier si le chunk a des None
        has_none = any(
            chunk.get(field) is None
            for field in ['game_name', 'source_url', 'section_title', 
                         'section_level', 'chunk_number', 'word_count',
                         'estimated_tokens', 'content_type',
                         'has_code', 'has_table', 'has_list']
        )
        
        if has_none:
            chunks_with_issues += 1
        
        # Corriger le chunk
        fixed_chunk = fix_chunk(chunk)
        fixed_chunks.append(fixed_chunk)
    
    # Mettre à jour les chunks dans data
    data['chunks'] = fixed_chunks
    
    # Déterminer le fichier de sortie
    if output_file is None:
        output_file = input_file
        
        # Créer une sauvegarde si demandé
        if backup:
            backup_file = input_file.parent / f"{input_file.stem}_backup{input_file.suffix}"
            shutil.copy2(input_file, backup_file)
            print(f"  💾 Backup: {backup_file.name}")
    
    # Sauvegarder le fichier corrigé
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return len(chunks), chunks_with_issues


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="Corriger automatiquement les chunks avec valeurs None"
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
        help="Répertoire de sortie (défaut: écrase les fichiers originaux)"
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help="Ne pas créer de backup (par défaut, un backup est créé)"
    )
    parser.add_argument(
        '--embeddings',
        action='store_true',
        help="Corriger les fichiers embeddings au lieu des chunks"
    )
    
    args = parser.parse_args()
    
    print("""
╔═══════════════════════════════════════════════════════════════╗
║          Chunk Fixer - Correction automatique                 ║
║          Corrige les valeurs None dans les chunks             ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    input_dir = Path(args.input)
    
    if not input_dir.exists():
        print(f"❌ Répertoire non trouvé: {args.input}")
        return
    
    # Déterminer le pattern de fichiers
    if args.embeddings:
        pattern = "*_embeddings.json"
        file_type = "embeddings"
    else:
        pattern = "*_chunks.json"
        file_type = "chunks"
    
    # Trouver tous les fichiers
    files = list(input_dir.glob(pattern))
    
    if not files:
        print(f"❌ Aucun fichier {file_type} trouvé dans {args.input}")
        return
    
    print(f"📁 {len(files)} fichiers trouvés\n")
    
    # Configuration
    print("⚙️  Configuration:")
    print(f"  • Type:           {file_type}")
    print(f"  • Input:          {input_dir}")
    print(f"  • Output:         {'Écrase originaux' if not args.output else args.output}")
    print(f"  • Backup:         {'Non' if args.no_backup else 'Oui'}")
    
    # Confirmer
    print("\n" + "="*70)
    response = input("▶️  Corriger les fichiers? [O/n]: ").strip().lower()
    if response and response not in ['o', 'oui', 'y', 'yes']:
        print("❌ Opération annulée.")
        return
    
    print("\n🔧 Correction en cours...\n")
    
    # Déterminer le répertoire de sortie
    if args.output:
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = None
    
    # Corriger chaque fichier
    total_chunks = 0
    total_fixed = 0
    processed_files = 0
    
    for file_path in files:
        output_file = output_dir / file_path.name if output_dir else None
        
        try:
            chunks_count, fixed_count = fix_chunks_file(
                file_path,
                output_file,
                backup=not args.no_backup and output_dir is None
            )
            
            total_chunks += chunks_count
            total_fixed += fixed_count
            processed_files += 1
            
            if fixed_count > 0:
                print(f"✅ {file_path.name}: {fixed_count}/{chunks_count} chunks corrigés")
            else:
                print(f"✓  {file_path.name}: Déjà OK ({chunks_count} chunks)")
            
        except Exception as e:
            print(f"❌ Erreur pour {file_path.name}: {e}")
    
    # Résumé
    print("\n" + "="*70)
    print("📊 RÉSUMÉ")
    print("="*70)
    print(f"  • Fichiers traités:       {processed_files}/{len(files)}")
    print(f"  • Total chunks:           {total_chunks}")
    print(f"  • Chunks corrigés:        {total_fixed}")
    print(f"  • Pourcentage corrigé:    {(total_fixed/total_chunks*100) if total_chunks > 0 else 0:.1f}%")
    print("="*70)
    
    if total_fixed > 0:
        print(f"\n✅ {total_fixed} chunks ont été corrigés!")
        
        if args.embeddings:
            print(f"\nVous pouvez maintenant indexer:")
            print(f"  python index_vectordb.py -i {args.input}")
        else:
            print(f"\nVous pouvez maintenant générer les embeddings:")
            print(f"  python generate_embeddings.py -i {args.input}")
    else:
        print(f"\n✓ Tous les chunks étaient déjà OK!")
    
    if not args.no_backup and output_dir is None:
        print(f"\n💾 Des backups ont été créés (fichiers *_backup.json)")
        print(f"   Vous pouvez les supprimer si tout fonctionne bien.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Opération interrompue.")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        raise
