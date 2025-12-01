from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)

KB_DIR = Path("data_pdfs/knowledge_base")

@dataclass(frozen=True)
class CategoryTopics:
    name: str
    topics: List[str]

async def get_kb_structure(force_refresh: bool = False) -> List[CategoryTopics]:
    """
    Scans local directory data_pdfs/knowledge_base.
    Categories = subfolder names. Topics = file names (without extension).
    Files in root are category "General" (Общее).
    """
    if not KB_DIR.exists():
        logger.warning(f"Knowledge base directory not found: {KB_DIR}")
        return []

    categories: Dict[str, List[str]] = {}

    # Iterate over all files
    for item in KB_DIR.rglob("*"):
        if item.is_file() and item.suffix.lower() in {'.pdf', '.txt', '.md'}:
            try:
                # Determine category based on folder structure
                relative_path = item.relative_to(KB_DIR)
                if len(relative_path.parts) > 1:
                    # First folder name is the category
                    category = relative_path.parts[0]
                else:
                    category = "Общее"
                
                topic = item.stem  # Filename without extension
                
                if category not in categories:
                    categories[category] = []
                categories[category].append(topic)
            except Exception as e:
                logger.warning(f"Error processing file {item}: {e}")

    result: List[CategoryTopics] = []
    for cat in sorted(categories.keys()):
        topics = sorted(categories[cat])
        result.append(CategoryTopics(name=cat, topics=topics))
    
    return result