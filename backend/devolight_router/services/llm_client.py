from __future__ import annotations

import json
import os
from typing import Dict, Iterable, List, Optional

import httpx


class ClaudeMessagesError(RuntimeError):
    """Raised when the Claude messages API call fails."""


class ClaudeMessagesCallable:
    """Callable wrapper that invokes the Claude messages API."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        max_output_tokens: int = 1024,
        temperature: float = 0.0,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._max_output_tokens = max_output_tokens
        self._temperature = temperature
        self._timeout = timeout_seconds

    @classmethod
    def from_environment(cls) -> "ClaudeMessagesCallable":
        """Construct the callable using environment configuration."""
        api_key = os.getenv("DEVO_CLAUDE_API_KEY")
        if not api_key:
            raise ClaudeMessagesError("缺少环境变量 DEVO_CLAUDE_API_KEY，用于访问 Claude API。")
        base_url = os.getenv("DEVO_CLAUDE_BASE_URL", "https://dpapi.cn")
        model = os.getenv("DEVO_CLAUDE_MODEL", "claude-sonnet-4-20250514")
        max_tokens = int(os.getenv("DEVO_CLAUDE_MAX_TOKENS", "1024"))
        temperature = float(os.getenv("DEVO_CLAUDE_TEMPERATURE", "0.0"))
        timeout = float(os.getenv("DEVO_CLAUDE_TIMEOUT", "30.0"))
        return cls(
            api_key=api_key,
            base_url=base_url,
            model=model,
            max_output_tokens=max_tokens,
            temperature=temperature,
            timeout_seconds=timeout,
        )

    def __call__(self, prompt: str, payload: Dict) -> str:
        """Invoke the Claude API and return the textual response."""
        body = {
            "model": self._model,
            "max_tokens": self._max_output_tokens,
            "temperature": self._temperature,
            "system": prompt,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(payload, ensure_ascii=False),
                        }
                    ],
                }
            ],
        }
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
        }
        url = f"{self._base_url}/v1/messages"
        try:
            response = httpx.post(
                url,
                headers=headers,
                json=body,
                timeout=self._timeout,
            )
        except httpx.HTTPError as exc:
            raise ClaudeMessagesError(f"无法访问 Claude API: {exc}") from exc

        if response.status_code >= 400:
            raise ClaudeMessagesError(
                f"Claude API 返回错误状态码 {response.status_code}: {response.text}"
            )
        try:
            data = response.json()
        except ValueError as exc:
            raise ClaudeMessagesError("Claude API 返回值不是合法 JSON。") from exc
        content = self._extract_text(data.get("content", []))
        if not content:
            raise ClaudeMessagesError("Claude API 返回内容为空。")
        return content

    @staticmethod
    def _extract_text(chunks: Optional[Iterable[Dict]]) -> str:
        if not chunks:
            return ""
        texts: List[str] = []
        for chunk in chunks:
            if not isinstance(chunk, dict):
                continue
            if chunk.get("type") == "text":
                text = chunk.get("text")
                if isinstance(text, str):
                    texts.append(text)
        return "".join(texts)

