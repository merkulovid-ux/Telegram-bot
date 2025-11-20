"""Utility to request Cloud.ru (SberCloud) IAM tokens for service accounts.

Usage:
    python scripts/get_cloudru_token.py \
        --client-id <CLIENT_ID> \
        --client-secret <CLIENT_SECRET>

    # or rely on environment variables / .env
    export CLOUDRU_CLIENT_ID=...
    export CLOUDRU_CLIENT_SECRET=...
    python scripts/get_cloudru_token.py --json
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict

import httpx

DEFAULT_ENDPOINT = "https://auth.iam.sbercloud.ru/auth/system/openid/token"


def request_token(
    client_id: str,
    client_secret: str,
    endpoint: str = DEFAULT_ENDPOINT,
    timeout: float = 15.0,
) -> Dict[str, Any]:
    """Call Cloud.ru IAM endpoint and return parsed JSON response."""
    data = {
        "grant_type": "access_key",
        "client_id": client_id,
        "client_secret": client_secret,
    }
    with httpx.Client(timeout=timeout) as client:
        response = client.post(endpoint, data=data)
        response.raise_for_status()
        return response.json()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Request Cloud.ru IAM token for a service account."
    )
    parser.add_argument(
        "--client-id",
        default=os.getenv("CLOUDRU_CLIENT_ID"),
        help="Client ID (service account). Can also come from CLOUDRU_CLIENT_ID env.",
    )
    parser.add_argument(
        "--client-secret",
        default=os.getenv("CLOUDRU_CLIENT_SECRET"),
        help="Client secret for the service account. "
        "Can also come from CLOUDRU_CLIENT_SECRET env.",
    )
    parser.add_argument(
        "--endpoint",
        default=DEFAULT_ENDPOINT,
        help=f"IAM endpoint URL (default: {DEFAULT_ENDPOINT}).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print raw JSON response (pretty formatted). Otherwise, print tokens only.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.client_id or not args.client_secret:
        raise SystemExit(
            "client_id and client_secret are required. "
            "Pass via --client-id/--client-secret or set CLOUDRU_CLIENT_ID / CLOUDRU_CLIENT_SECRET."
        )

    token_payload = request_token(
        client_id=args.client_id,
        client_secret=args.client_secret,
        endpoint=args.endpoint,
    )

    if args.json:
        print(json.dumps(token_payload, indent=2))
        return

    access_token = token_payload.get("access_token")
    expires_in = token_payload.get("expires_in")
    print("access_token:", access_token)
    print("expires_in:", expires_in)


if __name__ == "__main__":
    main()

