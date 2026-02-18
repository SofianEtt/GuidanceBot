#!/usr/bin/env python3
"""
Analyseur de qualité pour chunks de guides.
Vérifie que le chunking est optimal pour le RAG.
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Dict, List
import statistics

class ChunkAnalyzer:
    """Analyse la qualité des chunks créés."""
    
    def __init__(self, chunks_dir: str):
        """
        Initialize l'analyseur.
        
        Args:
            chunks_dir: Répertoire contenant les fichiers chunks
        """
        self.chunks_dir = Path(chunks_dir)
        self.all_chunks = []
        self.stats = defaultdict(list)
    
    def load_all_chunks(self):
        """Charge tous les fichiers de chunks."""
        json_files = list(self.chunks_dir.glob("*_chunks.json"))
        
        if not json_files:
            print(f"❌ Aucun fichier chunks trouvé dans {self.chunks_dir}")
            return False
        
        print(f"📁 {len(json_files)} fichiers chunks trouvés")
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.all_chunks.extend(data['chunks'])
            except Exception as e:
                print(f"⚠️  Erreur lors du chargement de {json_file.name}: {e}")
        
        print(f"✓ {len(self.all_chunks)} chunks chargés au total\n")
        return True
    
    def analyze_sizes(self):
        """Analyse la distribution des tailles."""
        print("="*70)
        print("📏 ANALYSE DES TAILLES")
        print("="*70)
        
        sizes = [c['estimated_tokens'] for c in self.all_chunks]
        
        if not sizes:
            print("❌ Aucune donnée de taille")
            return
        
        print(f"\n📊 Statistiques (en tokens):")
        print(f"  • Total chunks:       {len(sizes)}")
        print(f"  • Moyenne:            {statistics.mean(sizes):.1f}")
        print(f"  • Médiane:            {statistics.median(sizes):.1f}")
        print(f"  • Min:                {min(sizes)}")
        print(f"  • Max:                {max(sizes)}")
        print(f"  • Écart-type:         {statistics.stdev(sizes):.1f}")
        
        # Distribution par ranges
        ranges = {
            "< 100": 0,
            "100-256": 0,
            "256-512": 0,
            "512-1024": 0,
            "> 1024": 0
        }
        
        for size in sizes:
            if size < 100:
                ranges["< 100"] += 1
            elif size < 256:
                ranges["100-256"] += 1
            elif size < 512:
                ranges["256-512"] += 1
            elif size < 1024:
                ranges["512-1024"] += 1
            else:
                ranges["> 1024"] += 1
        
        print(f"\n📊 Distribution:")
        for range_name, count in ranges.items():
            percentage = (count / len(sizes)) * 100
            bar = "█" * int(percentage / 2)
            print(f"  {range_name:12s}: {count:4d} ({percentage:5.1f}%) {bar}")
        
        # Recommandations
        print(f"\n💡 Recommandations:")
        avg = statistics.mean(sizes)
        if avg < 256:
            print("  ⚠️  Chunks trop petits (< 256) - Considérez augmenter chunk_size")
        elif avg > 1024:
            print("  ⚠️  Chunks trop grands (> 1024) - Considérez réduire chunk_size")
        else:
            print("  ✅ Taille moyenne optimale pour RAG")
    
    def analyze_content_types(self):
        """Analyse les types de contenu."""
        print("\n" + "="*70)
        print("🏷️  ANALYSE DES TYPES DE CONTENU")
        print("="*70)
        
        type_counts = defaultdict(int)
        
        for chunk in self.all_chunks:
            content_types = chunk.get('content_type', [])
            if not content_types:
                type_counts['generic'] += 1
            else:
                for ct in content_types:
                    type_counts[ct] += 1
        
        if not type_counts:
            print("❌ Aucun type de contenu détecté")
            return
        
        print(f"\n📊 Types détectés:")
        sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
        
        for content_type, count in sorted_types:
            percentage = (count / len(self.all_chunks)) * 100
            print(f"  • {content_type:15s}: {count:4d} chunks ({percentage:5.1f}%)")
    
    def analyze_structure(self):
        """Analyse la structure (headers, listes, tableaux)."""
        print("\n" + "="*70)
        print("📐 ANALYSE DE LA STRUCTURE")
        print("="*70)
        
        structure_stats = {
            'has_code': 0,
            'has_table': 0,
            'has_list': 0,
            'has_section_title': 0
        }
        
        section_levels = defaultdict(int)
        
        for chunk in self.all_chunks:
            if chunk.get('has_code'):
                structure_stats['has_code'] += 1
            if chunk.get('has_table'):
                structure_stats['has_table'] += 1
            if chunk.get('has_list'):
                structure_stats['has_list'] += 1
            if chunk.get('section_title'):
                structure_stats['has_section_title'] += 1
                level = chunk.get('section_level', 0)
                if level:
                    section_levels[f"Level {level}"] += 1
        
        print(f"\n📊 Éléments structurels:")
        for elem, count in structure_stats.items():
            percentage = (count / len(self.all_chunks)) * 100
            print(f"  • {elem:20s}: {count:4d} ({percentage:5.1f}%)")
        
        if section_levels:
            print(f"\n📊 Niveaux de sections:")
            for level, count in sorted(section_levels.items()):
                print(f"  • {level:10s}: {count:4d}")
    
    def analyze_by_game(self):
        """Analyse par jeu."""
        print("\n" + "="*70)
        print("🎮 ANALYSE PAR JEU")
        print("="*70)
        
        game_stats = defaultdict(lambda: {
            'chunks': 0,
            'total_tokens': 0,
            'content_types': defaultdict(int)
        })
        
        for chunk in self.all_chunks:
            game = chunk.get('game_name', 'Unknown')
            game_stats[game]['chunks'] += 1
            game_stats[game]['total_tokens'] += chunk.get('estimated_tokens', 0)
            
            for ct in chunk.get('content_type', []):
                game_stats[game]['content_types'][ct] += 1
        
        print(f"\n📊 {len(game_stats)} jeux détectés:")
        
        for game, stats in sorted(game_stats.items(), key=lambda x: x[1]['chunks'], reverse=True):
            avg_tokens = stats['total_tokens'] / stats['chunks'] if stats['chunks'] > 0 else 0
            print(f"\n🎮 {game}")
            print(f"  • Chunks:         {stats['chunks']}")
            print(f"  • Tokens moyens:  {avg_tokens:.0f}")
            
            if stats['content_types']:
                types_str = ", ".join([f"{ct}({n})" for ct, n in list(stats['content_types'].items())[:3]])
                print(f"  • Types:          {types_str}")
    
    def check_quality(self):
        """Vérifie la qualité globale et donne des recommendations."""
        print("\n" + "="*70)
        print("✅ VÉRIFICATION DE QUALITÉ")
        print("="*70)
        
        issues = []
        warnings = []
        good_points = []
        
        # Vérifier les tailles
        sizes = [c['estimated_tokens'] for c in self.all_chunks]
        avg_size = statistics.mean(sizes)
        
        if avg_size < 200:
            issues.append("Chunks trop petits (moyenne < 200 tokens)")
        elif avg_size > 1200:
            issues.append("Chunks trop grands (moyenne > 1200 tokens)")
        elif 400 <= avg_size <= 600:
            good_points.append(f"Taille moyenne optimale: {avg_size:.0f} tokens")
        else:
            good_points.append(f"Taille moyenne acceptable: {avg_size:.0f} tokens")
        
        # Vérifier la variance
        if statistics.stdev(sizes) > 500:
            warnings.append("Forte variance dans les tailles de chunks")
        else:
            good_points.append("Tailles de chunks homogènes")
        
        # Vérifier les métadonnées
        chunks_with_sections = sum(1 for c in self.all_chunks if c.get('section_title'))
        section_ratio = chunks_with_sections / len(self.all_chunks)
        
        if section_ratio > 0.7:
            good_points.append(f"{section_ratio*100:.0f}% des chunks ont une section identifiée")
        elif section_ratio < 0.3:
            warnings.append("Peu de chunks avec sections identifiées - structure faible?")
        
        # Vérifier les types de contenu
        chunks_with_types = sum(1 for c in self.all_chunks if c.get('content_type'))
        type_ratio = chunks_with_types / len(self.all_chunks)
        
        if type_ratio > 0.5:
            good_points.append(f"{type_ratio*100:.0f}% des chunks ont un type identifié")
        elif type_ratio < 0.2:
            warnings.append("Peu de chunks typés - détection faible?")
        
        # Afficher les résultats
        if good_points:
            print(f"\n✅ Points forts ({len(good_points)}):")
            for point in good_points:
                print(f"  • {point}")
        
        if warnings:
            print(f"\n⚠️  Avertissements ({len(warnings)}):")
            for warning in warnings:
                print(f"  • {warning}")
        
        if issues:
            print(f"\n❌ Problèmes ({len(issues)}):")
            for issue in issues:
                print(f"  • {issue}")
        
        # Score global
        score = len(good_points) * 2 - len(warnings) - len(issues) * 2
        max_score = 10
        
        print(f"\n📊 Score de qualité: {max(0, score)}/{max_score}")
        
        if score >= 8:
            print("🎉 Excellente qualité de chunking!")
        elif score >= 5:
            print("👍 Bonne qualité de chunking")
        elif score >= 2:
            print("⚠️  Qualité acceptable, améliorations possibles")
        else:
            print("❌ Qualité faible, reconsidérez les paramètres de chunking")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        
        if avg_size < 400:
            print("  • Augmentez --chunk-size à 512 ou 768")
        elif avg_size > 800:
            print("  • Réduisez --chunk-size à 512")
        
        if statistics.stdev(sizes) > 500:
            print("  • Ajustez --min-size et --max-size pour plus de consistance")
        
        if section_ratio < 0.3:
            print("  • Vérifiez que vos guides ont une structure claire (headers markdown)")
        
        if type_ratio < 0.2:
            print("  • Les patterns de détection peuvent être améliorés")
    
    def generate_report(self, output_file: str = None):
        """Génère un rapport complet."""
        self.analyze_sizes()
        self.analyze_content_types()
        self.analyze_structure()
        self.analyze_by_game()
        self.check_quality()
        
        print("\n" + "="*70)
        print("✅ Analyse terminée!")
        print("="*70)


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="Analyser la qualité des chunks créés"
    )
    parser.add_argument(
        '-d', '--directory',
        type=str,
        default='data/chunks',
        help="Répertoire contenant les chunks (défaut: data/chunks)"
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        help="Fichier de sortie pour le rapport (optionnel)"
    )
    
    args = parser.parse_args()
    
    print("""
╔═══════════════════════════════════════════════════════════════╗
║          Chunk Quality Analyzer                               ║
║          Vérification de la qualité du chunking               ║
╚═══════════════════════════════════════════════════════════════╝
""")
    
    analyzer = ChunkAnalyzer(args.directory)
    
    if not analyzer.load_all_chunks():
        return
    
    analyzer.generate_report(args.output)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Analyse interrompue.")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        raise
