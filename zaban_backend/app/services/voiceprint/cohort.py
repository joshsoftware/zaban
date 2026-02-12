"""Cohort management utilities."""

from typing import List, Optional

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.services.voiceprint.config import voiceprint_settings as settings


def vector_to_list(vec: np.ndarray) -> list:
    """Ensure a flat list of floats for Qdrant (avoids multi/regular mismatch)."""
    a = np.asarray(vec, dtype=np.float32).flatten()
    return a.tolist()


def get_top_k_cohort_vectors(
    qdrant_client: QdrantClient,
    query_emb: np.ndarray,
    k: int,
) -> List[np.ndarray]:
    """
    Get top-K nearest vectors from cohort collection.
    
    Args:
        qdrant_client: Qdrant client instance
        query_emb: Query embedding
        k: Number of nearest vectors to retrieve
        
    Returns:
        List of cohort embeddings as numpy arrays
    """
    res = qdrant_client.query_points(
        collection_name=settings.COHORT_COLLECTION,
        query=vector_to_list(query_emb),
        limit=k,
        with_vectors=True,
    )
    vecs = []
    for p in (res.points or []):
        if p.vector:
            vecs.append(np.array(p.vector, dtype=np.float32))
    return vecs


def ensure_collection_exists(
    qdrant_client: QdrantClient,
    collection_name: str,
    embedding_dim: int,
) -> None:
    """
    Ensure a Qdrant collection exists with correct dimensions.
    
    Args:
        qdrant_client: Qdrant client instance
        collection_name: Name of the collection
        embedding_dim: Expected embedding dimension
    """
    try:
        info = qdrant_client.get_collection(collection_name)
        params = info.config.params.vectors
        
        # Check dimension
        try:
            existing_size = params.size if hasattr(params, "size") else None
        except Exception:
            existing_size = None
            
        if existing_size is None or existing_size != embedding_dim:
            # Recreate with correct dimension
            qdrant_client.delete_collection(collection_name)
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=embedding_dim,
                    distance=Distance.COSINE,
                ),
            )
    except Exception:
        # Collection doesn't exist, create it
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=embedding_dim,
                distance=Distance.COSINE,
            ),
        )
