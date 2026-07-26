import os
import hashlib
import pandas as pd

from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from Document_Normalizer import normalize_document

# -------------------------
# 1️⃣ Load CSV
# -------------------------
csv_file = "bank_data_split_qa.csv"
df = pd.read_csv(csv_file)

# -------------------------
# 2️⃣ Build documents (QA INCLUDED)
# -------------------------
documents = []
ids = []

for _, row in df.iterrows():
    content = row.get("content_chunk", "")
    if not content:
        continue

    qa_pair = row.get("qa_pair", "")
    keywords = row.get("keywords", "")

    # Normalize document content and QA
    normalized_content = normalize_document(content)
    normalized_qa = normalize_document(qa_pair)

    # Embedding text includes QA + content + keywords
    embedding_text = (
        f"Q&A:\n{normalized_qa}\n\n"
        f"Content:\n{normalized_content}\n\n"
        f"Keywords: {keywords}"
    )

    # Stable, content-based ID
    doc_id = hashlib.sha256(embedding_text.encode("utf-8")).hexdigest()

    # Include ID in metadata
    metadata = {
        "doc_id": doc_id,
        "title": row.get("title", ""),
        "language": row.get("language", ""),
        "section_type": row.get("section_type", ""),
        "keywords": keywords,
        "qa_pair": qa_pair,  # preserved verbatim for LLM use
    }

    documents.append(
        Document(
            page_content=embedding_text,
            metadata=metadata
        )
    )
    ids.append(doc_id)

print(f"Prepared {len(documents)} documents for ingestion.")

# -------------------------
# 3️⃣ Initialize Chroma
# -------------------------
embeddings = OllamaEmbeddings(model="mxbai-embed-large:335m")
db_location = "./qa_keywords_doc_normalized"

vector_store = Chroma(
    collection_name="bank_info",
    persist_directory=db_location,
    embedding_function=embeddings
)

# -------------------------
# 4️⃣ Add documents safely
# -------------------------
existing_count = vector_store._collection.count()

if existing_count == 0:
    vector_store.add_documents(documents=documents, ids=ids)
    print("Documents added to ChromaDB (QA included in embeddings, IDs in metadata).")
else:
    print(f"ChromaDB already contains {existing_count} documents. Skipping ingestion.")
