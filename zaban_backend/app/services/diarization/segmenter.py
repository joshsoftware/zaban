# app/services/diarization/segmenter.py

class Segmenter:
    @staticmethod
    def resolve_overlaps(segments):
        """
        Convert overlapping segments into timeline using majority voting
        """
        timeline = []

        for seg in segments:
            timeline.append((seg["start"], "start", seg["speaker"]))
            timeline.append((seg["end"], "end", seg["speaker"]))

        timeline.sort()

        active = []
        result = []

        last_time = None

        for time, typ, speaker in timeline:
            if last_time is not None and active:
                # pick most frequent speaker
                speaker_counts = {}
                for s in active:
                    speaker_counts[s] = speaker_counts.get(s, 0) + 1

                dominant = max(speaker_counts, key=speaker_counts.get)

                result.append({
                    "start": last_time,
                    "end": time,
                    "speaker": dominant
                })

            if typ == "start":
                active.append(speaker)
            else:
                if speaker in active:
                    active.remove(speaker)

            last_time = time

        return result
    
    @staticmethod
    def merge_segments(segments, gap_threshold=0.5):
        if not segments:
            return []

        segments = sorted(segments, key=lambda x: x["start"])
        merged = [segments[0]]

        for current in segments[1:]:
            last = merged[-1]

            if (
                current["speaker"] == last["speaker"]
                and (current["start"] - last["end"]) <= gap_threshold
            ):
                last["end"] = current["end"]
            else:
                merged.append(current)

        return merged

    @staticmethod
    def format_output(segments):
        return [
            {
                "start": s["start"],
                "end": s["end"],
                "speaker": s["speaker"]
            }
            for s in segments
        ]