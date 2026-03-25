import json
import logging
from pathlib import Path
from typing import Iterator, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_jsonl_files(folder_path: str) -> Iterator[Dict[str, Any]]:
    """
    Reads all JSON/JSONL files from a specified folder and yields one JSON object at a time.
    Safely handles both strict JSON arrays (beautifully formatted) and raw JSONL formats.
    """
    path = Path(folder_path)
    if not path.exists() or not path.is_dir():
        logger.error(f"Directory {folder_path} does not exist.")
        return

    all_files = list(path.rglob("*.json*"))
    
    def sort_key(f):
        fp = str(f).lower()
        if 'partner' in fp or 'customer' in fp: return 0
        if 'product' in fp or 'material' in fp: return 1
        if 'sales_order' in fp: return 2
        if 'delivery' in fp: return 3
        if 'billing' in fp: return 4
        if 'journal' in fp or 'payment' in fp or 'accounting' in fp: return 5
        return 99

    all_files.sort(key=sort_key)

    for file_path in all_files: 
        logger.info(f"Processing file into ingestion queue: {file_path}")
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read().strip()
                if not content:
                    continue
                
                try:
                    # Try parsing entire file as a single JSON (array or dict)
                    dataset = json.loads(content)
                    if isinstance(dataset, list):
                        for item in dataset:
                            yield item
                    else:
                        yield dataset
                except json.JSONDecodeError:
                    # Otherwise, fallback to strict JSONL
                    for line_number, line in enumerate(content.splitlines(), 1):
                        line = line.strip()
                        if not line or line == '[' or line == ']':
                            continue
                        if line.endswith(','):
                            line = line[:-1]
                            
                        try:
                            record = json.loads(line)
                            yield record
                        except json.JSONDecodeError as e:
                            logger.warning(f"Malformed JSON in {file_path} at line {line_number}. Skipping record. Error: {e}")
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
