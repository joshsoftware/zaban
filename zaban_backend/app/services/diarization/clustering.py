# app/services/diarization/clustering.py

from sklearn.cluster import AgglomerativeClustering
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def is_single_speaker(embeddings, threshold=0.75):
    """
    Check if all embeddings are similar → single speaker
    """
    if len(embeddings) < 2:
        return True

    sims = cosine_similarity(embeddings)

    # ignore diagonal
    avg_sim = (np.sum(sims) - len(sims)) / (len(sims)**2 - len(sims))

    return avg_sim > threshold

class SpeakerClustering:
    def __init__(self, distance_threshold=0.6, single_speaker_threshold=0.7):
        """
        distance_threshold: For AgglomerativeClustering (1 - cosine_similarity)
        single_speaker_threshold: Cosine similarity threshold for Pre-Diarization Decision Layer
        """
        self.distance_threshold = distance_threshold
        self.single_speaker_threshold = single_speaker_threshold

    def cluster(self, segments):
        """
        segments: [{start, end, embedding}]
        """
        if not segments:
            return []

        embeddings = np.array([s["embedding"] for s in segments])
        
        # Normalize embeddings for cosine distance
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0  # avoid division by zero
        embeddings = embeddings / norms

        # Pre-Diarization Decision Layer
        if is_single_speaker(embeddings, threshold=self.single_speaker_threshold):
            print(f"Single speaker detected (sim > {self.single_speaker_threshold}). Skipping clustering.")
            for seg in segments:
                seg["speaker"] = "speaker_0"
            return segments

        # Clustering for multiple speakers
        try:
            clustering = AgglomerativeClustering(
                n_clusters=None,
                distance_threshold=self.distance_threshold,
                metric="cosine",
                linkage="average"
            )
            labels = clustering.fit_predict(embeddings)
        except Exception as e:
            print(f"Clustering failed: {e}. Falling back to single speaker.")
            for seg in segments:
                seg["speaker"] = "speaker_0"
            return segments

        for seg, label in zip(segments, labels):
            seg["speaker"] = f"speaker_{label}"

        return segments