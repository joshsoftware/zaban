"""Cohort management utilities."""
from __future__ import annotations  # Defer type annotation evaluation to avoid SQLAlchemy conflicts

from typing import List, Optional
import importlib

import numpy as np

# Lazy import qdrant_client to avoid type annotation conflicts with SQLAlchemy
_QDRANT_CLASSES = None

def _get_qdrant_classes():
    """Lazy import qdrant_client classes to avoid type annotation conflicts."""
    global _QDRANT_CLASSES
    if _QDRANT_CLASSES is None:
        try:
            qdrant_client = importlib.import_module("qdrant_client")
            qdrant_models = importlib.import_module("qdrant_client.models")
            _QDRANT_CLASSES = (
                qdrant_client.QdrantClient,
                qdrant_models.Distance,
                qdrant_models.PointStruct,
                qdrant_models.VectorParams,
            )
        except (TypeError, AttributeError) as e:
            error_str = str(e)
            if "EnumTypeWrapper" in error_str or ("|" in error_str and "NoneType" in error_str):
                # Use exec to import in isolated namespace to bypass type annotation evaluation
                namespace = {}
                exec("""
import importlib
qdrant_client = importlib.import_module("qdrant_client")
qdrant_models = importlib.import_module("qdrant_client.models")
QdrantClient = qdrant_client.QdrantClient
Distance = qdrant_models.Distance
PointStruct = qdrant_models.PointStruct
VectorParams = qdrant_models.VectorParams
""", {"importlib": importlib}, namespace)
                _QDRANT_CLASSES = (
                    namespace["QdrantClient"],
                    namespace["Distance"],
                    namespace["PointStruct"],
                    namespace["VectorParams"],
                )
            else:
                raise
    return _QDRANT_CLASSES

from app.services.voiceprint.config import voiceprint_settings as settings


def vector_to_list(vec: np.ndarray) -> list:
    """Ensure a flat list of floats for Qdrant (avoids multi/regular mismatch)."""
    a = np.asarray(vec, dtype=np.float32).flatten()
    return a.tolist()


async def get_top_k_cohort_vectors(
    qdrant_client,  # QdrantClient type (lazy import)
    query_emb: np.ndarray,
    k: int,
) -> List[np.ndarray]:
    """
    Get top-K nearest vectors from cohort collection.
    
    Args:
        qdrant_client: Qdrant client instance (AsyncQdrantClient)
        query_emb: Query embedding
        k: Number of nearest vectors to retrieve
        
    Returns:
        List of cohort embeddings as numpy arrays
    """
    res = await qdrant_client.query_points(
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
    qdrant_client,  # QdrantClient type (lazy import)
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
            _, Distance, _, VectorParams = _get_qdrant_classes()
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
        _, Distance, _, VectorParams = _get_qdrant_classes()
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=embedding_dim,
                distance=Distance.COSINE,
            ),
        )
