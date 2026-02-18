#!/usr/bin/env python3
"""
Système de chunking avancé pour guides de jeux vidéo.
Optimisé pour RAG avec Discord bot.
"""

import json
import re
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import hashlib

class GameGuideChunker:
    """Chunker intelligent pour guides de jeux vidéo."""
    
    def __init__(
        self,
        chunk_size: int = 512,  # Tokens approximatifs (meilleur pour RAG)
        overlap: int = 50,
        min_chunk_size: int = 100,
        max_chunk_size: int = 1000
    ):
        """
        Initialize le chunker.
        
        Args:
            chunk_size: Taille cible en tokens (~4 chars = 1 token)
            overlap: Chevauchement en tokens
            min_chunk_size: Taille minimum d'un chunk
            max_chunk_size: Taille maximum d'un chunk
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        
        # Patterns pour détecter les structures
        self.section_patterns = [
            r'^#{1,6}\s+(.+)$',  # Markdown headers
            r'^([A-Z][A-Z\s]{3,}):?\s*$',  # Headers en majuscules
            r'^\d+\.\s+([A-Z].+)$',  # Numérotation
            r'^[-=]{3,}$',  # Séparateurs
        ]
        
        # Patterns pour types de contenu spécifiques
        self.quest_pattern = r'(?:quest|mission|objective)[:.]?\s*(.+)'
        self.boss_pattern = r'(?:boss|enemy|fight)[:.]?\s*(.+)'
        self.item_pattern = r'(?:item|weapon|armor|equipment)[:.]?\s*(.+)'
        self.achievement_pattern = r'(?:achievement|trophy)[:.]?\s*(.+)'
    
    def clean_text(self, text: str) -> str:
        """
        Nettoie le texte du guide.
        
        Args:
            text: Texte brut
        
        Returns:
            Texte nettoyé
        """
        # Supprimer les balises Markdown
        # Headers (# ## ### etc.) - garder le texte seulement
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        
        # Gras et italique (**texte** ou *texte*)
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold**
        text = re.sub(r'\*([^*]+)\*', r'\1', text)      # *italic*
        text = re.sub(r'__([^_]+)__', r'\1', text)      # __bold__
        text = re.sub(r'_([^_]+)_', r'\1', text)        # _italic_
        
        # Code inline (`code`)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        
        # Liens [texte](url) - garder seulement le texte
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        
        # Blocs de code (```) - supprimer les délimiteurs
        text = re.sub(r'```[a-z]*\n', '', text)
        text = re.sub(r'```', '', text)
        
        # Listes (-, *, +) - garder le contenu
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
        
        # Listes numérotées (1. 2. etc.) - garder le contenu
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
        
        # Blockquotes (>) - garder le contenu
        text = re.sub(r'^\s*>\s+', '', text, flags=re.MULTILINE)
        
        # Lignes horizontales (---, ***, ___)
        text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
        
        # Supprimer les lignes vides multiples
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Supprimer les caractères de contrôle
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)
        
        # Normaliser les espaces
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Supprimer les lignes qui sont juste des caractères spéciaux
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            if line and not re.match(r'^[=\-_*#]+$', line):
                lines.append(line)
        
        text = '\n'.join(lines)
        
        # Normaliser les apostrophes et guillemets
        text = text.replace('\u2019', "'").replace('\u201c', '"').replace('\u201d', '"')
        
        return text.strip()
    
    def extract_metadata_from_text(self, text: str) -> Dict[str, any]:
        """
        Extrait des métadonnées du contenu.
        
        Args:
            text: Texte du chunk
        
        Returns:
            Métadonnées extraites
        """
        metadata = {
            'content_type': [],
            'keywords': [],
            'has_code': False,
            'has_table': False,
            'has_list': False
        }
        
        # Détecter le type de contenu
        if re.search(self.quest_pattern, text, re.IGNORECASE):
            metadata['content_type'].append('quest')
        if re.search(self.boss_pattern, text, re.IGNORECASE):
            metadata['content_type'].append('boss')
        if re.search(self.item_pattern, text, re.IGNORECASE):
            metadata['content_type'].append('item')
        if re.search(self.achievement_pattern, text, re.IGNORECASE):
            metadata['content_type'].append('achievement')
        
        # Détecter les structures
        if re.search(r'```|`[^`]+`', text):
            metadata['has_code'] = True
        if re.search(r'\|.+\|', text):
            metadata['has_table'] = True
        if re.search(r'^\s*[-*+]\s+', text, re.MULTILINE):
            metadata['has_list'] = True
        
        return metadata
    
    def detect_sections(self, text: str) -> List[Dict[str, any]]:
        """
        Détecte automatiquement les sections dans le texte.
        
        Args:
            text: Texte complet
        
        Returns:
            Liste de sections avec leurs positions
        """
        sections = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            for pattern in self.section_patterns:
                match = re.match(pattern, line.strip())
                if match:
                    # Calculer la position en caractères
                    pos = len('\n'.join(lines[:i]))
                    
                    # Extraire le titre
                    if match.groups():
                        title = match.group(1).strip()
                    else:
                        title = line.strip('#= -').strip()
                    
                    sections.append({
                        'title': title,
                        'line_number': i,
                        'char_position': pos,
                        'level': self._get_header_level(line)
                    })
                    break
        
        return sections
    
    def _get_header_level(self, line: str) -> int:
        """Détermine le niveau d'un header."""
        # Markdown headers
        if line.startswith('#'):
            return len(re.match(r'^#+', line).group(0))
        # ALL CAPS headers (niveau 2)
        elif re.match(r'^[A-Z][A-Z\s]{3,}:?\s*$', line):
            return 2
        # Numbered headers (niveau 3)
        elif re.match(r'^\d+\.\s+', line):
            return 3
        return 4
    
    def create_semantic_chunks(self, text: str, metadata: Dict) -> List[Dict]:
        """
        Crée des chunks en respectant la structure sémantique.
        
        Args:
            text: Texte à chunker
            metadata: Métadonnées du guide
        
        Returns:
            Liste de chunks intelligents
        """
        # Nettoyer le texte
        text = self.clean_text(text)
        
        # Détecter les sections
        sections = self.detect_sections(text)
        
        if not sections:
            # Pas de structure détectée, chunking simple
            return self._create_simple_chunks(text, metadata)
        
        # Chunking basé sur les sections
        chunks = []
        
        for i, section in enumerate(sections):
            # Déterminer le début et la fin de la section
            start_pos = section['char_position']
            
            if i < len(sections) - 1:
                end_pos = sections[i + 1]['char_position']
            else:
                end_pos = len(text)
            
            section_text = text[start_pos:end_pos].strip()
            
            # Si la section est trop grande, la subdiviser
            if len(section_text) > self.max_chunk_size * 4:  # ~4 chars per token
                sub_chunks = self._split_large_section(
                    section_text,
                    section['title'],
                    metadata
                )
                chunks.extend(sub_chunks)
            else:
                # Section de taille acceptable
                chunk = self._create_chunk(
                    section_text,
                    metadata,
                    section_title=section['title'],
                    section_level=section['level']
                )
                chunks.append(chunk)
        
        return chunks
    
    def _split_large_section(
        self,
        text: str,
        section_title: str,
        metadata: Dict
    ) -> List[Dict]:
        """Divise une grande section en chunks plus petits."""
        chunks = []
        
        # Essayer de diviser par paragraphes
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        current_chunk = ""
        chunk_num = 0
        
        for para in paragraphs:
            # Estimation de tokens (~4 chars = 1 token)
            current_tokens = len(current_chunk) // 4
            para_tokens = len(para) // 4
            
            if current_tokens + para_tokens <= self.chunk_size:
                # Ajouter au chunk actuel
                current_chunk += "\n\n" + para if current_chunk else para
            else:
                # Sauvegarder le chunk actuel
                if current_chunk:
                    chunk = self._create_chunk(
                        current_chunk,
                        metadata,
                        section_title=f"{section_title} (Part {chunk_num + 1})",
                        section_level=2
                    )
                    chunks.append(chunk)
                    chunk_num += 1
                
                # Commencer un nouveau chunk
                current_chunk = para
        
        # Ajouter le dernier chunk
        if current_chunk:
            chunk = self._create_chunk(
                current_chunk,
                metadata,
                section_title=f"{section_title} (Part {chunk_num + 1})" if chunk_num > 0 else section_title,
                section_level=2
            )
            chunks.append(chunk)
        
        return chunks
    
    def _create_simple_chunks(self, text: str, metadata: Dict) -> List[Dict]:
        """Crée des chunks simples avec chevauchement."""
        chunks = []
        words = text.split()
        
        # Approximation: ~1.3 mots = 1 token
        words_per_chunk = int(self.chunk_size * 1.3)
        words_overlap = int(self.overlap * 1.3)
        
        start = 0
        chunk_num = 0
        
        while start < len(words):
            end = min(start + words_per_chunk, len(words))
            chunk_text = ' '.join(words[start:end])
            
            chunk = self._create_chunk(
                chunk_text,
                metadata,
                chunk_number=chunk_num
            )
            chunks.append(chunk)
            
            start = end - words_overlap if end < len(words) else end
            chunk_num += 1
        
        return chunks
    
    def _create_chunk(
        self,
        text: str,
        metadata: Dict,
        section_title: Optional[str] = None,
        section_level: Optional[int] = None,
        chunk_number: Optional[int] = None
    ) -> Dict:
        """Crée un chunk avec toutes ses métadonnées."""
        
        # Générer un ID unique
        chunk_id = hashlib.md5(
            f"{metadata.get('game_name', '')}_{text[:100]}".encode()
        ).hexdigest()[:16]
        
        # Extraire les métadonnées du contenu
        content_metadata = self.extract_metadata_from_text(text)
        
        # Calculer les statistiques
        word_count = len(text.split())
        char_count = len(text)
        estimated_tokens = char_count // 4
        
        chunk = {
            'chunk_id': chunk_id,
            'text': text,
            'game_name': metadata.get('game_name', 'Unknown'),
            'source_url': metadata.get('source_url', ''),
            'section_title': section_title,
            'section_level': section_level,
            'chunk_number': chunk_number,
            'word_count': word_count,
            'char_count': char_count,
            'estimated_tokens': estimated_tokens,
            'content_type': content_metadata['content_type'],
            'has_code': content_metadata['has_code'],
            'has_table': content_metadata['has_table'],
            'has_list': content_metadata['has_list'],
        }
        
        return chunk
    
    def process_guide(
        self,
        guide_path: Path,
        metadata_path: Path,
        output_dir: Path
    ) -> Tuple[int, Path]:
        """
        Traite un guide complet.
        
        Args:
            guide_path: Chemin vers le guide .md
            metadata_path: Chemin vers le fichier metadata
            output_dir: Répertoire de sortie
        
        Returns:
            Tuple (nombre de chunks, fichier de sortie)
        """
        # Charger le guide et les métadonnées
        with open(guide_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Créer les chunks
        chunks = self.create_semantic_chunks(text, metadata)
        
        # Créer le fichier de sortie
        output_file = output_dir / f"{guide_path.stem}_chunks.json"
        
        output_data = {
            'guide_metadata': metadata,
            'chunking_config': {
                'chunk_size': self.chunk_size,
                'overlap': self.overlap,
                'min_chunk_size': self.min_chunk_size,
                'max_chunk_size': self.max_chunk_size,
                'method': 'semantic'
            },
            'processing_info': {
                'processed_at': datetime.now().isoformat(),
                'total_chunks': len(chunks),
                'original_length': len(text)
            },
            'chunks': chunks
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        return len(chunks), output_file


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="Chunker intelligent pour guides de jeux vidéo"
    )
    parser.add_argument(
        '-i', '--input',
        type=str,
        default='data/guides',
        help="Répertoire contenant les guides"
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='data/chunks',
        help="Répertoire de sortie"
    )
    parser.add_argument(
        '-s', '--chunk-size',
        type=int,
        default=512,
        help="Taille des chunks en tokens (défaut: 512)"
    )
    parser.add_argument(
        '--overlap',
        type=int,
        default=50,
        help="Chevauchement en tokens (défaut: 50)"
    )
    parser.add_argument(
        '--min-size',
        type=int,
        default=100,
        help="Taille minimum d'un chunk (défaut: 100)"
    )
    parser.add_argument(
        '--max-size',
        type=int,
        default=1000,
        help="Taille maximum d'un chunk (défaut: 1000)"
    )
    
    args = parser.parse_args()
    
    print("""
╔═══════════════════════════════════════════════════════════════╗
║        Chunker Intelligent - Gaming Guides                    ║
║        Optimisé pour RAG avec Discord Bot                     ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    
    if not input_dir.exists():
        print(f"❌ Répertoire d'entrée non trouvé: {args.input}")
        return
    
    # Créer le répertoire de sortie
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Trouver tous les guides
    md_files = list(input_dir.rglob("*.md"))
    
    if not md_files:
        print(f"❌ Aucun guide trouvé dans {args.input}")
        return
    
    print(f"\n📁 {len(md_files)} guides trouvés\n")
    
    # Configuration
    print("⚙️  Configuration:")
    print(f"  • Chunk size:     {args.chunk_size} tokens")
    print(f"  • Overlap:        {args.overlap} tokens")
    print(f"  • Min size:       {args.min_size} tokens")
    print(f"  • Max size:       {args.max_size} tokens")
    print(f"  • Output:         {output_dir}")
    
    # Confirmer
    print("\n" + "="*70)
    response = input("▶️  Commencer le chunking? [O/n]: ").strip().lower()
    if response and response not in ['o', 'oui', 'y', 'yes']:
        print("❌ Opération annulée.")
        return
    
    # Initialiser le chunker
    chunker = GameGuideChunker(
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        min_chunk_size=args.min_size,
        max_chunk_size=args.max_size
    )
    
    # Traiter chaque guide
    total_chunks = 0
    processed = 0
    failed = 0
    
    print("\n🚀 Chunking en cours...\n")
    
    for md_file in md_files:
        # Trouver le fichier de métadonnées correspondant
        metadata_file = md_file.parent / f"{md_file.stem}_metadata.json"
        
        if not metadata_file.exists():
            print(f"⚠️  Métadonnées manquantes pour: {md_file.name}")
            failed += 1
            continue
        
        try:
            chunks_count, output_file = chunker.process_guide(
                md_file,
                metadata_file,
                output_dir
            )
            
            total_chunks += chunks_count
            processed += 1
            print(f"✅ {md_file.name}: {chunks_count} chunks → {output_file.name}")
            
        except Exception as e:
            print(f"❌ Erreur pour {md_file.name}: {e}")
            failed += 1
    
    # Résumé
    print("\n" + "="*70)
    print("📊 RÉSUMÉ")
    print("="*70)
    print(f"  • Guides traités:     {processed}")
    print(f"  • Guides échoués:     {failed}")
    print(f"  • Total chunks:       {total_chunks}")
    
    if processed > 0:
        avg_chunks = total_chunks / processed
        print(f"  • Moyenne chunks:     {avg_chunks:.1f} par guide")
    
    print("="*70)
    print(f"\n📁 Fichiers chunks dans: {output_dir}/")
    print("\n💡 Prochaines étapes:")
    print("  1. Générer les embeddings pour chaque chunk")
    print("  2. Indexer dans votre base vectorielle (Pinecone, Chroma, etc.)")
    print("  3. Configurer votre Discord bot pour interroger les chunks")
    print("\n✅ Chunking terminé!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Opération interrompue.")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        raise
