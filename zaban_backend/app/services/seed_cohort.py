"""
Populate indian_cohort_ecapa from IndicVoices parquet file(s) or pre-extracted NPZ.

This script supports two modes:
  1. NPZ mode (default, fast): Load pre-extracted embeddings from an .npz file.
  2. Parquet mode (--from-parquet): Extract ECAPA embeddings from raw audio in parquet files.

Usage:
    # From pre-extracted embeddings (fast, no model loading):
    python -m app.services.seed_cohort

    # From parquet audio (slower, extracts embeddings live):
    python -m app.services.seed_cohort --from-parquet app/data/hindi-train-*.parquet --max-per-file 500

    # Custom Qdrant host/port:
    python -m app.services.seed_cohort --host localhost --port 6333

    # Force re-seed (recreate collection):
    python -m app.services.seed_cohort --force
"""
from pathlib import Path
import sys
import argparse

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.services.voiceprint.config import voiceprint_settings as settings
from app.services.voiceprint.cohort import vector_to_list, ensure_collection_exists
from app.services.voiceprint.utils.embeddings import ECAPAEmbedder

# Default data directory (app/data/)
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_NPZ = DATA_DIR / "embeddings_plda.npz"
DEFAULT_PARQUET = DATA_DIR / "hindi-train-00000-of-00064.parquet"

BATCH_SIZE = 100


def seed_from_npz(
    client: QdrantClient,
    collection: str,
    npz_path: Path,
    max_vectors: int = None,
) -> int:
    """Load pre-extracted embeddings from NPZ and upsert into Qdrant."""
    print(f"📂 Loading embeddings from: {npz_path}")
    data = np.load(str(npz_path), allow_pickle=False)
    embeddings = data["embeddings"]  # shape: (N, 1, 192)
    print(f"   Found {embeddings.shape[0]} embeddings, shape={embeddings.shape}")

    # Squeeze to (N, 192)
    if embeddings.ndim == 3:
        embeddings = embeddings.squeeze(1)

    if max_vectors is not None:
        embeddings = embeddings[:max_vectors]
        print(f"   Limited to {embeddings.shape[0]} embeddings (--max {max_vectors})")

    # L2-normalize
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1e-8
    embeddings = embeddings / norms

    # Upsert in batches
    total = len(embeddings)
    inserted = 0
    for start in range(0, total, BATCH_SIZE):
        end = min(start + BATCH_SIZE, total)
        batch = embeddings[start:end]
        points = [
            PointStruct(
                id=start + i,
                vector=vector_to_list(batch[i]),
                payload={"source": "embeddings_plda.npz", "index": start + i},
            )
            for i in range(len(batch))
        ]
        client.upsert(collection_name=collection, points=points)
        inserted += len(points)
        if inserted % 500 == 0 or inserted == total:
            print(f"   {inserted}/{total} inserted...")

    return inserted


def seed_from_parquet(
    client: QdrantClient,
    collection: str,
    parquet_paths: list,
    max_per_file: int = None,
    verbose: bool = False,
) -> int:
    """Extract ECAPA embeddings from parquet audio and upsert into Qdrant."""
    # Lazy imports — only needed for parquet mode
    import pandas as pd
    from tqdm import tqdm
    from app.services.voiceprint.utils.audio import decode_audio_from_bytes, to_16k_mono

    print("🔧 Loading ECAPA embedder...")
    embedder = ECAPAEmbedder()

    total = 0
    err_count = 0
    first_error = None

    for parquet_path in parquet_paths:
        p = Path(parquet_path).resolve()
        if not p.exists():
            if verbose:
                print(f"   Skip (not found): {p}")
            continue

        print(f"📂 Reading parquet: {p.name}")
        df = pd.read_parquet(p)
        if "audio_filepath" not in df.columns:
            if verbose:
                print(f"   Skip (no audio_filepath column): {p}")
            continue

        rows = list(df.iterrows())
        if max_per_file:
            rows = rows[:max_per_file]

        for idx, row in tqdm(rows, desc=p.name, leave=False):
            try:
                audio_data = row["audio_filepath"]
                if not isinstance(audio_data, dict) or audio_data.get("bytes") is None:
                    continue
                audio_array, sr = decode_audio_from_bytes(audio_data["bytes"])
                audio_16k = to_16k_mono(audio_array, sr)
                # Synchronous embedding extraction (returns numpy array, not coroutine)
                emb = embedder.extract_embedding(audio_16k, sample_rate=16000)
                point_id = abs(hash(f"{parquet_path}_{idx}")) % (2**63)
                client.upsert(
                    collection_name=collection,
                    points=[
                        PointStruct(
                            id=point_id,
                            vector=vector_to_list(emb),
                            payload={
                                "source": str(p.name),
                                "index": int(idx),
                                "speaker_id": row.get("speaker_id", ""),
                            },
                        )
                    ],
                )
                total += 1
            except Exception as e:
                err_count += 1
                if first_error is None:
                    first_error = (str(p), idx, e)
                if verbose and err_count <= 5:
                    import traceback
                    print(f"   Error at {p.name} idx={idx}: {e}")
                    traceback.print_exc()
                continue

    if total == 0 and first_error is not None:
        path_, idx_, ex_ = first_error
        print(
            f"⚠️  0 vectors added. First error at {path_} idx={idx_}: {ex_}",
            file=sys.stderr,
        )

    if err_count > 0:
        print(f"   ⚠️  {err_count} errors encountered")

    return total


def main():
    parser = argparse.ArgumentParser(
        description="Seed Qdrant indian_cohort_ecapa collection"
    )
    parser.add_argument(
        "--host", default=settings.QDRANT_HOST, help="Qdrant host (default: from .env)"
    )
    parser.add_argument(
        "--port", type=int, default=settings.QDRANT_PORT, help="Qdrant port"
    )
    parser.add_argument(
        "--collection", default=settings.COHORT_COLLECTION, help="Collection name"
    )
    parser.add_argument(
        "--max", type=int, default=None, help="Max embeddings to insert"
    )
    parser.add_argument(
        "--force", action="store_true", help="Recreate collection even if non-empty"
    )

    # Source selection
    parser.add_argument(
        "--from-parquet",
        nargs="+",
        metavar="FILE",
        help="Parquet file(s) to extract embeddings from (slower, uses ECAPA model)",
    )
    parser.add_argument(
        "--npz",
        default=str(DEFAULT_NPZ),
        help=f"Path to NPZ file (default: {DEFAULT_NPZ})",
    )
    parser.add_argument(
        "--max-per-file",
        type=int,
        default=None,
        help="Max utterances per parquet file (only for --from-parquet)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose error output"
    )
    args = parser.parse_args()

    # Connect to Qdrant
    print(f"📡 Connecting to Qdrant at {args.host}:{args.port}...")
    client = QdrantClient(host=args.host, port=args.port)

    # Check collection status
    embedding_dim = 192
    try:
        info = client.get_collection(args.collection)
        existing_count = info.points_count
        print(f"   Collection '{args.collection}' exists with {existing_count} points")

        if existing_count > 0 and not args.force:
            print(f"   ✅ Already populated. Use --force to re-seed.")
            return

        if args.force:
            print(f"   🔄 Recreating collection (--force)...")
            client.delete_collection(args.collection)
            raise Exception("recreate")
    except Exception:
        print(
            f"   Creating collection '{args.collection}' (dim={embedding_dim}, cosine)..."
        )
        client.create_collection(
            collection_name=args.collection,
            vectors_config=VectorParams(
                size=embedding_dim, distance=Distance.COSINE
            ),
        )

    # Seed
    if args.from_parquet:
        inserted = seed_from_parquet(
            client,
            args.collection,
            args.from_parquet,
            max_per_file=args.max_per_file,
            verbose=args.verbose,
        )
    else:
        npz_path = Path(args.npz)
        if not npz_path.exists():
            print(f"❌ NPZ file not found: {npz_path}", file=sys.stderr)
            print(
                f"   Expected at: {DEFAULT_NPZ}",
                file=sys.stderr,
            )
            sys.exit(1)
        inserted = seed_from_npz(client, args.collection, npz_path, args.max)

    # Verify
    info = client.get_collection(args.collection)
    print(f"\n✅ Done! Collection '{args.collection}' now has {info.points_count} points (added {inserted}).")


if __name__ == "__main__":
    main()
