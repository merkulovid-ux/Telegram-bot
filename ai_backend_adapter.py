"""AI Backend Adapter"""

import asyncio
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

@dataclass
class AIResponse:
    text: str
    usage: Optional[Dict[str, Any]] = None
    citations: Optional[List[Dict[str, Any]]] = None
    model: str = "unknown"

class AIBackend(ABC):
    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs):
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        pass

class AIBackendManager:
    def __init__(self):
        self.backends = {}
        self.preferred_backend = "yandex"
    
    async def generate_text(self, prompt: str, backend: Optional[str] = None, **kwargs):
        return AIResponse(text="Mock response", model="test")

_ai_manager = None

def get_ai_manager():
    global _ai_manager
    if _ai_manager is None:
        _ai_manager = AIBackendManager()
    return _ai_manager

async def generate_text(prompt: str, backend: Optional[str] = None, **kwargs):
    manager = get_ai_manager()
    return await manager.generate_text(prompt, backend, **kwargs)

