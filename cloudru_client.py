"""Cloud.ru AI Client"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import base64

class GigaChatClient:
    def __init__(self):
        self.access_token = None
        
    async def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        # Mock implementation for testing
        return {
            "content": f"Mock response to: {prompt[:50]}...",
            "usage": {"tokens": 100},
            "model": "GigaChat-mock"
        }

class GigaChatEmbeddings:
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        return [[0.1] * 768 for _ in texts]

