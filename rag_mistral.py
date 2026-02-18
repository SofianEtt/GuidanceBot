import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline


# ============================
# 1. Embeddings (MiniLM)
# ============================

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)


def embed_query(text: str):
    """Encode une requête utilisateur en embedding."""
    return embedder.encode(text).tolist()


# ============================
# 2. ChromaDB (vecteurs)
# ============================

client = chromadb.PersistentClient(path="db")
collection = client.get_collection(name="guidancebot")


def retrieve_context(game_name: str, question: str, k: int = 5):
    """Recherche les chunks les plus pertinents dans Chroma."""
    query_embedding = embed_query(question)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        where={"game_name": game_name}
    )

    texts = results["documents"][0]
    metadatas = results["metadatas"][0]

    return texts, metadatas


# ============================
# 3. Mistral 7B (local)
# ============================

#MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.2"
#MODEL_NAME = "microsoft/phi-2"
MODEL_NAME = "microsoft/Phi-3-mini-4k-instruct
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)   
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    device_map="auto",
    torch_dtype="auto"
)

llm = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=512,
    temperature=0.2,
    top_p=0.9,
    do_sample=True
)


# ============================
# 4. Prompt RAG
# ============================

def build_prompt(game_name: str, question: str, contexts: list[str]) -> str:
    """Construit un prompt optimisé pour Mistral 7B."""
    context_block = "\n\n---\n\n".join(contexts)

    system = (
        "Tu es un expert en jeux vidéo. "
        "Tu réponds uniquement à partir du contexte fourni. "
        "Si l'information n'est pas dans le contexte, tu le dis clairement."
    )

    user = (
        f"Jeu : {game_name}\n\n"
        f"Question : {question}\n\n"
        f"Contexte :\n{context_block}\n\n"
        "Donne une réponse claire, structurée et utile pour un joueur."
    )

    prompt = f"<s>[INST] {system}\n\n{user} [/INST]"
    return prompt


def generate_answer(prompt: str) -> str:
    """Génère une réponse avec Mistral."""
    out = llm(prompt)[0]["generated_text"]
    return out


# ============================
# 5. Fonction principale RAG
# ============================

def answer_question(game_name: str, question: str, k: int = 5) -> str:
    """Pipeline complet : retrieve → prompt → generate."""
    contexts, metas = retrieve_context(game_name, question, k=k)

    if not contexts:
        return "Aucun guide pertinent n’a été trouvé pour cette question."

    prompt = build_prompt(game_name, question, contexts)
    answer = generate_answer(prompt)

    return answer


# ============================
# 6. Exemple d’utilisation
# ============================

if __name__ == "__main__":
    game = "Death Stranding"
    question = "C'est quoi les DOOMS et comment ça fonctionne dans le gameplay ?"

    print("\n=== RÉPONSE RAG ===\n")
    print(answer_question(game, question, k=3))
