"""Command-line entry point for extracting Plover events from raw text."""

import argparse
import json
import sys
from pathlib import Path

from .config import load_config
from .llm import OpenAICompatibleClient
from .models import ExtractionRequest
from .pipeline import extract_events


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract Plover events from raw text")
    parser.add_argument("--config", required=True, help="Path to pipeline YAML config")
    parser.add_argument("--doc-id", required=True)
    parser.add_argument("input", nargs="?", help="Raw-text file; stdin when omitted")
    args = parser.parse_args()
    raw_text = Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()
    config = load_config(args.config)
    request = ExtractionRequest(args.doc_id, raw_text)
    events = extract_events(request, config, OpenAICompatibleClient(config.llm))
    json.dump([event.to_dict() for event in events], sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
