"""Minimal Gemini client — one call returns a sticker grid image.

Same shape as the live Gemini image API, with an injectable base_url so tests
point at a local fake server (no key, no network):

    POST {base_url}/{model}:generateContent?key={api_key}

Prereq concept: this is the same call taught in gemini-image-starter. Here we
ask for a green-screen grid of poses in ONE call, then split + cut it locally.
"""
from __future__ import annotations

import base64

import httpx

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_MODEL = "gemini-2.5-flash-image"


def build_request_body(prompt: str) -> dict:
    return {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }


def extract_image(result: dict) -> bytes:
    candidates = result.get("candidates", [])
    if candidates:
        for part in candidates[0].get("content", {}).get("parts", []):
            data = part.get("inlineData", {}).get("data")
            if data:
                return base64.b64decode(data)
    raise ValueError("no image found in response")


def generate_grid(
    prompt: str,
    api_key: str,
    *,
    model: str = DEFAULT_MODEL,
    base_url: str = GEMINI_BASE,
    timeout: float = 60.0,
) -> bytes:
    """Ask Gemini for one grid image (PNG bytes). Use a green background so the
    local cut-out step has a clean key to remove."""
    url = f"{base_url}/{model}:generateContent?key={api_key}"
    resp = httpx.post(url, json=build_request_body(prompt), timeout=timeout)
    resp.raise_for_status()
    return extract_image(resp.json())
