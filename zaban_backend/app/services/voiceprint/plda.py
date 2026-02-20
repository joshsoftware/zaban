"""PLDA scoring utilities."""

from typing import Dict, List

import numpy as np
from speechbrain.processing.PLDA_LDA import StatObject_SB, Ndx, fast_PLDA_scoring

STAT_TYPE = np.float64


def _stat_single(emb: np.ndarray, model_id: str, seg_id: str) -> StatObject_SB:
    """Create a StatObject_SB for a single embedding."""
    emb = np.asarray(emb, dtype=STAT_TYPE)
    if emb.ndim == 1:
        emb = emb.reshape(1, -1)
    return StatObject_SB(
        modelset=np.array([model_id], dtype=object),
        segset=np.array([seg_id], dtype=object),
        start=np.zeros(1, dtype=object),
        stop=np.zeros(1, dtype=object),
        stat0=np.ones((1, 1), dtype=STAT_TYPE),
        stat1=emb,
    )



def _stat_batch(embs: np.ndarray, model_ids: np.ndarray, seg_ids: np.ndarray) -> StatObject_SB:
    """Create a StatObject_SB for multiple embeddings."""
    embs = np.asarray(embs, dtype=STAT_TYPE)
    if embs.ndim == 1:
        embs = embs.reshape(1, -1)
        
    # stat0 must be (N, 1) where N is number of segments
    n_segments = embs.shape[0]
    
    return StatObject_SB(
        modelset=model_ids.astype(object),
        segset=seg_ids.astype(object),
        start=np.zeros(n_segments, dtype=object),
        stop=np.zeros(n_segments, dtype=object),
        stat0=np.ones((n_segments, 1), dtype=STAT_TYPE),
        stat1=embs,
    )


def plda_score(emb1: np.ndarray, emb2: np.ndarray, plda: Dict) -> float:
    """
    Compute PLDA score between two embeddings.
    
    Args:
        emb1: First embedding (enrollment)
        emb2: Second embedding (test)
        plda: PLDA model dictionary with keys: mean, F, Sigma, scaling_factor
        
    Returns:
        PLDA score as float
    """
    en = _stat_single(emb1, "enroll", "e1")
    te = _stat_single(emb2, "test", "t1")
    ndx = Ndx(
        ndx_file_name="",
        models=np.array(["enroll"], dtype=object),
        testsegs=np.array(["t1"], dtype=object),
    )
    scores = fast_PLDA_scoring(
        en, te, ndx,
        mu=plda["mean"],
        F=plda["F"],
        Sigma=plda["Sigma"],
        scaling_factor=plda.get("scaling_factor", 1.0),
        check_missing=False,
    )
    return float(scores.scoremat[0, 0])


def compute_cohort_plda_scores(
    reference_emb: np.ndarray, 
    cohort_vectors: List[np.ndarray], 
    plda: Dict
) -> List[float]:

    """
    Compute PLDA scores between a reference embedding and multiple cohort vectors (Vectorized).
    
    Args:
        reference_emb: Reference embedding (1, D)
        cohort_vectors: List of cohort embeddings [(D,), ...]
        plda: PLDA model dictionary
        
    Returns:
        List of PLDA scores
    """
    if not cohort_vectors:
        return []

    # Prepare enrollment (reference) - Single Model
    en_emb = np.asarray(reference_emb, dtype=STAT_TYPE)
    if en_emb.ndim == 1:
        en_emb = en_emb.reshape(1, -1)
    
    en_obj = _stat_single(en_emb, "enroll", "e1")
    
    # Prepare test segments (cohort) - Batch
    cohort_embs = np.array(cohort_vectors, dtype=STAT_TYPE) # (N, D)
    n_cohort = len(cohort_vectors)
    
    # Create unique segment IDs for each cohort vector
    seg_ids = np.array([f"c{i}" for i in range(n_cohort)], dtype=object)

    # Create Batch StatObject for cohort
    te_obj = _stat_batch(cohort_embs, seg_ids, seg_ids) 
    
    ndx = Ndx(
        ndx_file_name="",
        models=np.array(["enroll"], dtype=object),
        testsegs=seg_ids,
    )
    
    # Fast PLDA Scoring
    scores = fast_PLDA_scoring(
        en_obj, te_obj, ndx,
        mu=plda["mean"],
        F=plda["F"],
        Sigma=plda["Sigma"],
        scaling_factor=plda.get("scaling_factor", 1.0),
        check_missing=False,
    )
    
    # scores.scoremat dimensions: (n_models, n_testsegs) -> (1, N)
    # We want a list of scores corresponding to cohort_vectors
    return scores.scoremat[0, :].tolist()


def compute_as_norm_score(
    raw_score: float,
    enrollment_cohort_scores: List[float],
    test_cohort_scores: List[float],
) -> float:
    """
    Compute Adaptive S-Norm (AS-Norm) score.
    
    AS-Norm normalizes the raw PLDA score using statistics from cohort comparisons,
    making the score more robust across different speakers.
    
    Args:
        raw_score: Raw PLDA score between enrolled and test embeddings
        enrollment_cohort_scores: PLDA scores between enrolled embedding and cohort
        test_cohort_scores: PLDA scores between test embedding and cohort
        
    Returns:
        AS-Norm normalized score
    """
    mu_e = np.mean(enrollment_cohort_scores)
    sigma_e = np.std(enrollment_cohort_scores) or 1e-8
    mu_t = np.mean(test_cohort_scores)
    sigma_t = np.std(test_cohort_scores) or 1e-8
    
    # Symmetric AS-Norm
    s_norm = 0.5 * ((raw_score - mu_e) / sigma_e + (raw_score - mu_t) / sigma_t)
    
    return s_norm
