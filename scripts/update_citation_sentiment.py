#!/usr/bin/env python3
"""Update index.json with author feedback sentiment for cited Substack links."""

import argparse
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.analysis.citation_sentiment import update_index_with_citation_sentiment
from src.web.index_generator import IndexGenerator


def main():
    parser = argparse.ArgumentParser(
        description="Analyze saved post HTML and add citation sentiment to data/index.json."
    )
    parser.add_argument(
        "--index",
        default="data/index.json",
        help="Path to index.json (default: data/index.json)",
    )
    parser.add_argument(
        "--skip-html",
        action="store_true",
        help="Do not regenerate data/index.html after updating sentiment fields.",
    )
    args = parser.parse_args()

    index_path = Path(args.index)
    if not index_path.is_absolute():
        index_path = project_root / index_path

    if not index_path.exists():
        print(f"Error: {index_path} does not exist. Generate index.json first.")
        return 1

    metadata = update_index_with_citation_sentiment(index_path)
    print("Citation sentiment analysis complete:")
    print(f"  analyzed_posts: {metadata['analyzed_posts']}")
    print(f"  posts_with_citations: {metadata['posts_with_citations']}")
    print(f"  total_citations: {metadata['total_citations']}")

    if not args.skip_html:
        generator = IndexGenerator(index_path.parent)
        generator.create_index_html()
        print("Regenerated data/index.html with citation sentiment badges.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

