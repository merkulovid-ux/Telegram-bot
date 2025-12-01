"""Cloud.ru GigaChat client (REST)."""

from __future__ import annotations

import asyncio
import os
import time
from typing import Any, Dict, List, Optional

import httpx

DEFAULT_TOKEN_ENDPOINT = "https://auth.iam.sbercloud.ru/auth/system/openid/token"
DEFAULT_GIGACHAT_ENDPOINT = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"


class CloudRuAuthError(RuntimeError):
    pass


class GigaChatClient:
    def __init__(
        self,
        *,
        token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        token_endpoint: str = DEFAULT_TOKEN_ENDPOINT,
        api_endpoint: str = DEFAULT_GIGACHAT_ENDPOINT,
        request_timeout: float = 30.0,
    ) -> None:
        self._token = token or os.getenv("CLOUDRU_TOKEN")
        self._client_id = client_id or os.getenv("CLOUDRU_CLIENT_ID")
        self._client_secret = client_secret or os.getenv("CLOUDRU_CLIENT_SECRET")
        self._token_endpoint = token_endpoint
        self._api_endpoint = api_endpoint
        self._timeout = request_timeout
        self._token_expiry: float | None = None

    async def _fetch_token(self) -> str:
        if not self._client_id or not self._client_secret:
            raise CloudRuAuthError("CLOUDRU_TOKEN or CLOUDRU_CLIENT_ID/SECRET is required")
        data = {
            "grant_type": "access_key",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(self._token_endpoint, data=data)
            resp.raise_for_status()
            payload = resp.json()
            token = payload.get("access_token")
            expires_in = payload.get("expires_in")
            if not token:
                raise CloudRuAuthError("No access_token in IAM response")
            if isinstance(expires_in, (int, float)):
                self._token_expiry = time.time() + float(expires_in) - 60
            self._token = token
            return token

    async def _get_token(self) -> str:
        if self._token and (self._token_expiry is None or time.time() < self._token_expiry):
            return self._token
        return await self._fetch_token()

    async def generate_text(self, prompt: str, *, model: str = "GigaChat", temperature: float = 0.3) -> Dict[str, Any]:
        token = await self._get_token()
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(self._api_endpoint, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            # GigaChat returns choices[0].message.content
            content = ""
            if isinstance(data, dict):
                if "choices" in data:
                    try:
                        content = data["choices"][0]["message"].get("content", "")  # type: ignore[index]
                    except Exception:
                        content = ""
            return {
                "content": content,
                "raw": data,
            }


class GigaChatEmbeddings:
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        # Placeholder: implement when embedding endpoint is available
        return [[0.0] * 768 for _ in texts]
