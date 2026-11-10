import argparse
import json
from pathlib import Path

from app.config import get_settings
from app.indexing import build_index


def parse_args() -> argparse.Namespace:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Build the OpsLens semantic index")
    parser.add_argument("--source-dir", type=Path, default=settings.source_dir)
    parser.add_argument("--index-path", type=Path, default=settings.index_path)
    parser.add_argument("--embedding-model", default=settings.embedding_model)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_index(args.source_dir, args.index_path, args.embedding_model)
    print(
        json.dumps(
            {
                "status": "ok",
                "index_path": str(args.index_path),
                "embedding_model": payload.embedding_model,
                **payload.metadata,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

