import re
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ---------------------------------------------------------
# FIXED CONFIG (CONSTANTS)
# ---------------------------------------------------------
DB_PATH = "./qa_keywords_doc_normalized"
COLLECTION_NAME = "bank_info"
EMBEDDING_MODEL = "mxbai-embed-large:335m"

ALPHA = 0.5
TOP_K = 5

# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------
def clean_question(text: str) -> str:
    return re.sub(r"^\s*\d+\s*-\s*", "", text).strip()

def detect_lang_fast(text: str) -> str:
    return "ar" if re.search(r'[\u0600-\u06FF]', text) else "en"


# ---------------------------------------------------------
# Hybrid Retriever
# ---------------------------------------------------------
from collections import defaultdict

class HybridWeightedRetriever:
    def __init__(self):
        self.embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        self.vector_store = Chroma(
            collection_name=COLLECTION_NAME,
            persist_directory=DB_PATH,
            embedding_function=self.embeddings
        )

        raw = self.vector_store._collection.get(
            include=["documents", "metadatas"]
        )

        self.docs_index = {}
        self.docs_for_tfidf = defaultdict(list)

        for text, meta in zip(raw["documents"], raw["metadatas"]):
            doc_id = meta.get("doc_id")
            if not doc_id or not text.strip():
                continue

            searchable = []

            if meta.get("qa_pair"):
                searchable.append(str(meta["qa_pair"]))

            searchable.append(text)

            if meta.get("keywords"):
                searchable.append(
                    " ".join(meta["keywords"])
                    if isinstance(meta["keywords"], list)
                    else str(meta["keywords"])
                )

            full_text = " ".join(searchable)
            full_text = re.sub(r"\\", "", full_text)
            full_text = " ".join(full_text.split())

            lang = meta.get("language", "en")

            self.docs_index[doc_id] = {
                "text": text,
                "meta": meta
            }

            self.docs_for_tfidf[lang].append({
                "id": doc_id,
                "text": full_text
            })

        # 🚀 Pre-fit TF-IDF per language
        self.tfidf_models = {}
        self.tfidf_matrices = {}
        self.tfidf_doc_ids = {}

        for lang, docs in self.docs_for_tfidf.items():
            corpus = [d["text"] for d in docs]
            ids = [d["id"] for d in docs]

            vectorizer = TfidfVectorizer(
                ngram_range=(1, 2),
                stop_words="english" if lang == "en" else None
            )

            matrix = vectorizer.fit_transform(corpus)

            self.tfidf_models[lang] = vectorizer
            self.tfidf_matrices[lang] = matrix
            self.tfidf_doc_ids[lang] = ids


    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def search(self, query: str):
        cleaned = clean_question(query)
        query_lang = detect_lang_fast(cleaned)

        if query_lang not in self.tfidf_models:
            return []

        # ---------- TF-IDF ----------
        vectorizer = self.tfidf_models[query_lang]
        matrix = self.tfidf_matrices[query_lang]
        doc_ids = self.tfidf_doc_ids[query_lang]

        query_vec = vectorizer.transform([cleaned])

        tfidf_scores = cosine_similarity(
            query_vec, matrix
        ).flatten()

        tfidf_map = {
            doc_ids[i]: float(score)
            for i, score in enumerate(tfidf_scores)
        }

        # ---------- Embeddings ----------
        emb_results = self.vector_store.similarity_search_with_score(
            cleaned,
            k=10,
            filter={"language": query_lang}
        )

        emb_scores = {}
        for doc, dist in emb_results:
            doc_id = doc.metadata.get("doc_id")
            if doc_id:
                similarity = 1.0 - (dist / 2.0)
                emb_scores[doc_id] = max(0.0, similarity)

        # ---------- Weighted Merge ----------
        combined = {}
        all_ids = set(tfidf_map) | set(emb_scores)

        for doc_id in all_ids:
            combined[doc_id] = (
                ALPHA * tfidf_map.get(doc_id, 0.0)
                + (1 - ALPHA) * emb_scores.get(doc_id, 0.0)
            )

        ranked = sorted(
            combined.items(),
            key=lambda x: x[1],
            reverse=True
        )[:TOP_K]

        results = []

        for rank, (doc_id, score) in enumerate(ranked, start=1):
            if doc_id not in self.docs_index:
                continue

            results.append({
                "document_rank": rank,
                "document_text": self.docs_index[doc_id]["text"]
            })

        return results


