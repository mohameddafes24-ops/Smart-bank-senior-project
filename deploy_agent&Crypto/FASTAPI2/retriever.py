from hybrid_retriever import HybridWeightedRetriever

# ---------------------------------------------------------
# GLOBAL SINGLETON
# ---------------------------------------------------------
_RETRIEVER = None
_INITIALIZED = False


# ---------------------------------------------------------
# Initialization (called once from system_init)
# ---------------------------------------------------------
def retrievalINIT():
    """
    Initialize the retriever ONCE.
    This loads:
    - Chroma
    - Embeddings
    - Pre-fitted TF-IDF
    """
    global _RETRIEVER, _INITIALIZED

    if _INITIALIZED:
        return

    _RETRIEVER = HybridWeightedRetriever()
    _INITIALIZED = True


# ---------------------------------------------------------
# Public API
# ---------------------------------------------------------
def retrieve(query: str):
    """
    Production-safe retrieval API.
    Returns ONLY rank + text.
    """
    if not _INITIALIZED or _RETRIEVER is None:
        raise RuntimeError(
            "Retriever not initialized. Call system_init() first."
        )

    return _RETRIEVER.search(query)
