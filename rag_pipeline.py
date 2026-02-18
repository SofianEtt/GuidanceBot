#!/usr/bin/env python3
"""
Pipeline RAG complet avec Mistral 7B et ChromaDB.
Recherche sémantique + Génération de réponse.
"""

import argparse
from typing import List, Dict, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch
except ImportError:
    print("❌ transformers ou torch n'est pas installé")
    print("\nInstallez avec:")
    print("  pip install transformers torch accelerate")
    exit(1)


class RAGPipeline:
    """Pipeline RAG complet pour guides de jeux vidéo."""
    
    def __init__(
        self,
        db_path: str = "data/chromadb",
        collection_name: str = "gaming_guides",
        embedding_model: str = "all-MiniLM-L6-v2",
        llm_model: str = "mistralai/Mistral-7B-Instruct-v0.2",
        device: str = "auto"
    ):
        """
        Initialize le pipeline RAG.
        
        Args:
            db_path: Chemin de la base ChromaDB
            collection_name: Nom de la collection
            embedding_model: Modèle pour les embeddings
            llm_model: Modèle LLM pour la génération
            device: Device (cuda, cpu, ou auto)
        """
        print("🚀 Initialisation du pipeline RAG...\n")
        
        # 1. Charger le modèle d'embeddings
        print(f"📦 Chargement du modèle d'embeddings: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)
        print(f"✓ Embeddings prêts\n")
        
        # 2. Connecter à ChromaDB
        print(f"📦 Connexion à ChromaDB: {db_path}")
        self.client = chromadb.PersistentClient(
            path=str(Path(db_path)),
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_collection(name=collection_name)
        print(f"✓ ChromaDB prêt ({self.collection.count()} documents)\n")
        
        # 3. Charger Mistral 7B
        print(f"📦 Chargement de Mistral 7B: {llm_model}")
        print("   ⏱️  Ceci peut prendre 1-2 minutes...")
        
        # Déterminer le device
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        print(f"   Device: {self.device}")
        
        # Charger le tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(llm_model)
        
        # Charger le modèle
        if self.device == "cuda":
            # Charger en float16 pour économiser VRAM
            self.llm = AutoModelForCausalLM.from_pretrained(
                llm_model,
                torch_dtype=torch.float16,
                device_map="auto",
                low_cpu_mem_usage=True
            )
        else:
            # CPU - charger normalement
            self.llm = AutoModelForCausalLM.from_pretrained(
                llm_model,
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True
            )
            self.llm.to(self.device)
        
        print(f"✓ Mistral 7B prêt\n")
        print("✅ Pipeline RAG initialisé!\n")
    
    def retrieve(
        self,
        question: str,
        n_results: int = 5,
        game_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Récupère les chunks pertinents pour une question.
        
        Args:
            question: Question de l'utilisateur
            n_results: Nombre de résultats
            game_filter: Filtrer par jeu
        
        Returns:
            Liste des chunks pertinents
        """
        # Générer l'embedding de la question
        query_embedding = self.embedding_model.encode(question).tolist()
        
        # Rechercher dans ChromaDB
        where = {"game_name": game_filter} if game_filter else None
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )
        
        # Formater les résultats
        chunks = []
        for i in range(len(results['ids'][0])):
            chunk = {
                'id': results['ids'][0][i],
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if 'distances' in results else None
            }
            chunks.append(chunk)
        
        return chunks
    
    def build_context(self, chunks: List[Dict]) -> str:
        """
        Construit le contexte à partir des chunks.
        
        Args:
            chunks: Chunks récupérés
        
        Returns:
            Contexte formaté
        """
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            game = chunk['metadata'].get('game_name', 'Unknown')
            section = chunk['metadata'].get('section_title', '')
            text = chunk['text']
            
            part = f"[Source {i} - {game}"
            if section:
                part += f" - {section}"
            part += f"]\n{text}"
            
            context_parts.append(part)
        
        return "\n\n".join(context_parts)
    
    def generate_answer(
        self,
        question: str,
        context: str,
        max_length: int = 512,
        temperature: float = 0.7
    ) -> str:
        """
        Génère une réponse avec Mistral 7B.
        
        Args:
            question: Question de l'utilisateur
            context: Contexte récupéré
            max_length: Longueur max de la réponse
            temperature: Température de génération
        
        Returns:
            Réponse générée
        """
        # Construire le prompt pour Mistral
        prompt = f"""<s>[INST] You are a helpful gaming guide assistant. Use the following context from gaming guides to answer the user's question. Be concise and helpful.

Context from guides:
{context}

Question: {question}

Provide a clear and helpful answer based on the context above. If the context doesn't contain relevant information, say so. [/INST]"""
        
        # Tokenizer
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        # Générer
        with torch.no_grad():
            outputs = self.llm.generate(
                **inputs,
                max_new_tokens=max_length,
                temperature=temperature,
                do_sample=True,
                top_p=0.95,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        # Décoder
        full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extraire seulement la réponse (après [/INST])
        if "[/INST]" in full_response:
            answer = full_response.split("[/INST]")[-1].strip()
        else:
            answer = full_response
        
        return answer
    
    def query(
        self,
        question: str,
        n_results: int = 5,
        game_filter: Optional[str] = None,
        max_length: int = 512,
        temperature: float = 0.7,
        show_sources: bool = True
    ) -> Dict:
        """
        Pipeline RAG complet: Retrieve + Generate.
        
        Args:
            question: Question de l'utilisateur
            n_results: Nombre de chunks à récupérer
            game_filter: Filtrer par jeu
            max_length: Longueur max de la réponse
            temperature: Température de génération
            show_sources: Inclure les sources dans la réponse
        
        Returns:
            Dictionnaire avec réponse et métadonnées
        """
        print(f"❓ Question: {question}\n")
        
        # 1. Retrieve
        print("🔍 Recherche des chunks pertinents...")
        chunks = self.retrieve(question, n_results, game_filter)
        print(f"✓ {len(chunks)} chunks trouvés\n")
        
        if not chunks:
            return {
                'answer': "Je n'ai pas trouvé d'informations pertinentes dans les guides.",
                'sources': [],
                'context': ''
            }
        
        # 2. Build context
        context = self.build_context(chunks)
        
        # 3. Generate
        print("🤖 Génération de la réponse avec Mistral 7B...")
        answer = self.generate_answer(question, context, max_length, temperature)
        print("✓ Réponse générée\n")
        
        # Formater les sources
        sources = []
        for chunk in chunks:
            sources.append({
                'game': chunk['metadata'].get('game_name', 'Unknown'),
                'section': chunk['metadata'].get('section_title', ''),
                'url': chunk['metadata'].get('source_url', '')
            })
        
        return {
            'answer': answer,
            'sources': sources,
            'context': context,
            'chunks_used': len(chunks)
        }


def interactive_mode(rag: RAGPipeline):
    """Mode interactif pour tester le RAG."""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║              Mode Interactif - RAG Pipeline                   ║
║              Posez vos questions sur les jeux!                ║
╚═══════════════════════════════════════════════════════════════╝

Commandes:
  • Tapez votre question normalement
  • 'quit' ou 'exit' pour quitter
  • 'game:NomDuJeu' pour filtrer par jeu
  
""")
    
    current_game_filter = None
    
    while True:
        try:
            # Afficher le filtre actuel
            if current_game_filter:
                print(f"[Filtre: {current_game_filter}]")
            
            question = input("❓ Votre question: ").strip()
            
            if not question:
                continue
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Au revoir!")
                break
            
            # Commande de filtre
            if question.lower().startswith('game:'):
                game_name = question[5:].strip()
                current_game_filter = game_name if game_name else None
                print(f"✓ Filtre {'activé' if current_game_filter else 'désactivé'}: {current_game_filter}\n")
                continue
            
            # Requête RAG
            print()
            result = rag.query(
                question,
                n_results=5,
                game_filter=current_game_filter
            )
            
            # Afficher la réponse
            print("="*70)
            print("💬 RÉPONSE")
            print("="*70)
            print(result['answer'])
            print()
            
            # Afficher les sources
            if result['sources']:
                print("📚 SOURCES")
                print("-"*70)
                for i, source in enumerate(result['sources'][:3], 1):
                    print(f"{i}. {source['game']}", end="")
                    if source['section']:
                        print(f" - {source['section']}", end="")
                    print()
                print()
            
            print("="*70)
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Au revoir!")
            break
        except Exception as e:
            print(f"\n❌ Erreur: {e}\n")


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="Pipeline RAG avec Mistral 7B"
    )
    parser.add_argument(
        '-d', '--db-path',
        type=str,
        default='data/chromadb',
        help="Chemin de la base ChromaDB"
    )
    parser.add_argument(
        '-c', '--collection',
        type=str,
        default='gaming_guides',
        help="Nom de la collection"
    )
    parser.add_argument(
        '-q', '--question',
        type=str,
        help="Question unique (mode non-interactif)"
    )
    parser.add_argument(
        '--game',
        type=str,
        help="Filtrer par jeu"
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        help="Mode interactif"
    )
    
    args = parser.parse_args()
    
    print("""
╔═══════════════════════════════════════════════════════════════╗
║          RAG Pipeline - Mistral 7B + ChromaDB                 ║
║          Réponses intelligentes sur guides de jeux            ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Initialiser le pipeline
    rag = RAGPipeline(
        db_path=args.db_path,
        collection_name=args.collection
    )
    
    # Mode interactif ou question unique
    if args.interactive or not args.question:
        interactive_mode(rag)
    else:
        # Question unique
        result = rag.query(
            args.question,
            game_filter=args.game
        )
        
        print("\n" + "="*70)
        print("💬 RÉPONSE")
        print("="*70)
        print(result['answer'])
        print("\n" + "="*70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Au revoir!")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        raise
