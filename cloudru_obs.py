"""Cloud.ru Object Storage Service"""

import asyncio
from typing import List, Dict, Any, Optional

class CloudRuOBS:
    async def upload_file(self, file_path: str, object_key: str) -> bool:
        return True  # Mock implementation
        
    async def download_file(self, object_key: str, file_path: str) -> bool:
        return True  # Mock implementation

def get_obs_client():
    return CloudRuOBS()

