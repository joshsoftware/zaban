# app/services/diarization/service.py

from .pipeline import DiarizationPipeline
from .clustering import SpeakerClustering
from .segmenter import Segmenter


class DiarizationService:
    def __init__(self, distance_threshold=0.6, single_speaker_threshold=0.7):
        self.pipeline = DiarizationPipeline()
        self.clustering = SpeakerClustering(
            distance_threshold=distance_threshold,
            single_speaker_threshold=single_speaker_threshold
        )

    def diarize(self, audio_path: str):
        """
        Full diarization pipeline
        """

        # Step 1: VAD → segments
        segments = self.pipeline.get_speech_segments(audio_path)

        # Step 2: embeddings
        segments_with_embeddings = self.pipeline.extract_embeddings(
            audio_path, segments
        )

        # Step 3: clustering → assign speakers
        clustered = self.clustering.cluster(segments_with_embeddings)

        # Step 4: merge segments
        resolved = Segmenter.resolve_overlaps(clustered)
        merged = Segmenter.merge_segments(resolved)

        # Step 5: format output
        return Segmenter.format_output(merged)