"""
ECAPA-TDNN + PLDA (Indic) + AS-Norm speaker verification.

Detailed voice verifier module that handles:
- User enrollment with multiple audio samples
- Speaker verification using PLDA scoring and AS-Norm normalization
- Cohort management for score normalization
"""

import hashlib
import pickle
import time
from typing import Dict, List, Optional, Union
import asyncio
import concurrent.futures
import numpy as np
from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.models import PointStruct

from app.services.voiceprint.config import voiceprint_settings as settings
from app.services.voiceprint.cohort import (
    ensure_collection_exists,
    get_top_k_cohort_vectors,
    vector_to_list,
)
from app.services.voiceprint.plda import (
    compute_as_norm_score,
    compute_cohort_plda_scores,
    plda_score,
)
from app.services.voiceprint.utils.audio import load_audio
from app.services.voiceprint.utils.embeddings import ECAPAEmbedder


class VoiceVerifierECAPA:
    """Speaker verification: ECAPA-TDNN + PLDA (Indic) + AS-Norm (Indic cohort)."""

    def __init__(
        self,
        plda_path: Optional[str] = None,
        qdrant_host: Optional[str] = None,
        qdrant_port: Optional[int] = None,
        threshold: Optional[float] = None,
        cohort_top_k: Optional[int] = None,
        device: Optional[str] = None,
        ecapa_savedir: Optional[str] = None,
    ):
        """
        Initialize the voice verifier.
        """
        # Use settings defaults if not provided
        self.threshold = threshold or settings.VERIFICATION_THRESHOLD
        self.cohort_top_k = cohort_top_k or settings.COHORT_TOP_K
        
        # Load PLDA model
        plda_path = plda_path or settings.PLDA_MODEL_PATH
        with open(plda_path, "rb") as f:
            self._plda = pickle.load(f)
        
        # Initialize ECAPA embedder
        self._embedder = ECAPAEmbedder(savedir=ecapa_savedir, device=device)
        self.embedding_dim = self._embedder.embedding_dim
        
        # Initialize Qdrant client
        qdrant_host = qdrant_host or settings.QDRANT_HOST
        qdrant_port = qdrant_port or settings.QDRANT_PORT
        print(f"📡 Connecting to Qdrant at {qdrant_host}:{qdrant_port}...")
        
        # Keep sync client for initialization/management if needed, 
        # but primarily we use async client for operations.
        self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.async_client = AsyncQdrantClient(host=qdrant_host, port=qdrant_port)
        
        # Executor for CPU-bound tasks
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        
        # Ensure collections exist (sync is fine for startup)
        try:
            self._init_collections()
        except Exception as e:
            print(f"⚠️  Failed to initialize Qdrant collections: {e}")
            pass

    def _init_collections(self) -> None:
        """Initialize Qdrant collections for enrolled users and cohort."""
        for name in [settings.ENROLLED_COLLECTION, settings.COHORT_COLLECTION]:
            try:
                ensure_collection_exists(self.qdrant_client, name, self.embedding_dim)
            except Exception as e:
                print(f"⚠️  Error ensuring collection '{name}' exists: {e}")
                raise

    async def extract_embedding(self, audio_path: Union[str, np.ndarray, dict]) -> np.ndarray:
        """
        Extract embedding from audio (runs in thread pool).
        """
        start = time.time()
        loop = asyncio.get_running_loop()
        
        def _extract():
            t0 = time.time()
            audio = load_audio(audio_path)
            t1 = time.time()
            emb = self._embedder.extract_embedding(audio, sample_rate=settings.TARGET_SAMPLE_RATE)
            t2 = time.time()
            print(f" [Extract] Load: {t1-t0:.3f}s, Inference: {t2-t1:.3f}s")
            return emb
            
        res = await loop.run_in_executor(self._executor, _extract)
        print(f" [Extract] Total (queued+run): {time.time()-start:.3f}s")
        return res

    async def enroll_user(
        self,
        audio_paths: List[Union[str, np.ndarray, dict]],
        customer_id: str,
    ) -> Dict:
        """
        Enroll a user with multiple audio samples.
        """
        if len(audio_paths) < settings.MIN_ENROLLMENT_SAMPLES:
            raise ValueError(
                f"At least {settings.MIN_ENROLLMENT_SAMPLES} audio samples required for enrollment"
            )
        if len(audio_paths) > settings.MAX_ENROLLMENT_SAMPLES:
            raise ValueError(
                f"Maximum {settings.MAX_ENROLLMENT_SAMPLES} samples allowed"
            )
        
        # Extract embeddings for all samples concurrently
        embs = await asyncio.gather(*[self.extract_embedding(p) for p in audio_paths])
        
        # Compute centroid (mean) and normalize
        centroid = np.mean(embs, axis=0).astype(np.float32)
        norm = np.linalg.norm(centroid)
        if norm > 0:
            centroid = centroid / norm
        
        # Generate point ID from customer_id
        point_id = int(hashlib.sha256(customer_id.encode()).hexdigest()[:15], 16) % (2**63)
        
        # Upsert to Qdrant
        await self.async_client.upsert(
            collection_name=settings.ENROLLED_COLLECTION,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector_to_list(centroid),
                    payload={"customer_id": customer_id, "num_samples": len(audio_paths)},
                )
            ],
        )
        
        return {
            "status": "success",
            "customer_id": customer_id,
            "point_id": point_id,
            "message": f"User enrolled successfully with {len(audio_paths)} samples",
        }

    async def get_user_embedding(self, customer_id: str) -> Optional[np.ndarray]:
        """
        Retrieve enrolled user's centroid embedding.
        """
        point_id = int(hashlib.sha256(customer_id.encode()).hexdigest()[:15], 16) % (2**63)
        try:
            out = await self.async_client.retrieve(
                collection_name=settings.ENROLLED_COLLECTION,
                ids=[point_id],
                with_vectors=True,
            )
            if out and out[0].vector:
                return np.array(out[0].vector, dtype=np.float32)
        except Exception:
            pass
        return None

    async def verify_speaker(
        self,
        audio_path: Union[str, np.ndarray, dict],
        customer_id: str,
    ) -> Dict:
        """
        Verify if the audio belongs to the enrolled user.
        """
        total_start = time.time()
        print(f" [Verify] Starting verification for {customer_id}")

        # Extract test embedding
        t0 = time.time()
        test_emb = await self.extract_embedding(audio_path)
        print(f" [Verify] Extract Test Embedding: {time.time()-t0:.3f}s")
        
        # Get enrolled user embedding
        t0 = time.time()
        user_emb = await self.get_user_embedding(customer_id)
        print(f" [Verify] Get User Embedding (Qdrant): {time.time()-t0:.3f}s")

        if user_emb is None:
            return {
                "verified": False,
                "error": f"Customer {customer_id} not found",
                "score": None,
                "raw_score": None,
            }
        
        loop = asyncio.get_running_loop()
        
        # Compute raw PLDA score (CPU bound)
        t0 = time.time()
        raw_score = await loop.run_in_executor(
            self._executor, 
            plda_score, 
            user_emb, test_emb, self._plda
        )
        print(f" [Verify] Raw PLDA Score: {time.time()-t0:.3f}s")
        
        # Get cohort vectors for AS-Norm (Async Qdrant)
        print(f" [Verify] FetchingCohort (k={self.cohort_top_k})...")
        t0 = time.time()
        # Run both queries concurrently
        cohort_enroll_task = get_top_k_cohort_vectors(
            self.async_client, user_emb, self.cohort_top_k
        )
        cohort_test_task = get_top_k_cohort_vectors(
            self.async_client, test_emb, self.cohort_top_k
        )
        
        cohort_enroll, cohort_test = await asyncio.gather(cohort_enroll_task, cohort_test_task)
        print("[Verify] Cohort Fetched: ", time.time()-t0)
        
        if not cohort_enroll or not cohort_test:
            return {
                "verified": False,
                "error": "Cohort empty. Populate cohort collection first.",
                "score": None,
                "raw_score": raw_score,
            }
        
        # Compute cohort PLDA scores (CPU bound)
        t0 = time.time()
        scores_enroll = await loop.run_in_executor(
            self._executor,
            compute_cohort_plda_scores,
            user_emb, cohort_enroll, self._plda
        )
        scores_test = await loop.run_in_executor(
            self._executor,
            compute_cohort_plda_scores,
            test_emb, cohort_test, self._plda
        )
        print("[Verify] Cohort Scores Computed: ", time.time()-t0)
        
        # Compute AS-Norm score
        mu_e = np.mean(scores_enroll)
        sigma_e = np.std(scores_enroll) or 1e-8
        mu_t = np.mean(scores_test)
        sigma_t = np.std(scores_test) or 1e-8
        
        s_norm = compute_as_norm_score(raw_score, scores_enroll, scores_test)
        
        verified = s_norm > self.threshold
        
        

        return {
            "verified": verified,
            "score": float(s_norm),
            "raw_score": float(raw_score),
            "threshold": self.threshold,
            "enrollment_cohort_mean": float(mu_e),
            "enrollment_cohort_std": float(sigma_e),
            "test_cohort_mean": float(mu_t),
            "test_cohort_std": float(sigma_t),
            "cohort_size": self.cohort_top_k,
        }

    async def delete_user(self, customer_id: str) -> Dict:
        """
        Delete an enrolled user from vector store.
        """
        point_id = int(hashlib.sha256(customer_id.encode()).hexdigest()[:15], 16) % (2**63)
        try:
            await self.async_client.delete(
                collection_name=settings.ENROLLED_COLLECTION,
                points_selector=[point_id],
            )
            return {"status": "success", "message": f"Customer {customer_id} deleted"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def list_enrolled_users(self, limit: int = 100) -> List[Dict]:
        """
        List all enrolled users in vector store.
        """
        try:
            result = await self.async_client.scroll(
                collection_name=settings.ENROLLED_COLLECTION,
                limit=limit,
                with_payload=True,
                with_vectors=False,
            )
            users = []
            for point in result[0]:
                users.append({
                    "customer_id": point.payload.get("customer_id"),
                    "num_samples": point.payload.get("num_samples"),
                })
            return users
        except Exception:
            return []
