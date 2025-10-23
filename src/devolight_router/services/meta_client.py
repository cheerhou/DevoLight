from __future__ import annotations

import json
import logging
from typing import Callable, Dict, Tuple

from pydantic import ValidationError

from ..models import RoutingContext, RoutingDecision
from ..prompts import load_prompt


class MetaRouterResponseError(RuntimeError):
    """Raised when the元调度者返回的数据无效。"""


LLMCallable = Callable[[str, Dict], str]


class MetaRouterClient:
    """Encapsulate interaction with the meta router prompt."""

    def __init__(self, llm_call: LLMCallable, *, prompt_name: str = "meta_router") -> None:
        self._llm_call = llm_call
        self._prompt_template = load_prompt(prompt_name)
        self._logger = logging.getLogger(__name__)

    def _prepare_payload(self, context: RoutingContext) -> Tuple[str, Dict]:
        user_payload: Dict = context.raw_payload or context.dict(exclude_none=True)
        warnings = context.requires_attention()
        if warnings:
            user_payload = {**user_payload, "system_warnings": warnings}
        return self._prompt_template, user_payload

    def route(self, context: RoutingContext) -> RoutingDecision:
        prompt, payload = self._prepare_payload(context)
        self._logger.info("MetaRouter prompt: %s", prompt)
        try:
            serialized_payload = json.dumps(payload, ensure_ascii=False)
        except (TypeError, ValueError):
            serialized_payload = str(payload)
        self._logger.info("MetaRouter payload: %s", serialized_payload)
        raw = self._llm_call(prompt, payload)
        self._logger.info("MetaRouter raw response: %s", raw)
        normalized = self._normalize_response(raw)
        if normalized != raw:
            self._logger.info("MetaRouter normalized response: %s", normalized)
        try:
            response = json.loads(normalized)
        except json.JSONDecodeError as exc:
            preview_source = normalized or raw
            preview = preview_source if len(preview_source) <= 500 else f"{preview_source[:500]}…"
            message = f"MetaRouter 返回值不是合法 JSON。原始响应：{preview}"
            raise MetaRouterResponseError(message) from exc
        try:
            decision = RoutingDecision.parse_obj(response)
        except ValidationError as exc:
            raise MetaRouterResponseError("MetaRouter 返回值未通过数据模型校验。") from exc
        return decision

    @staticmethod
    def _normalize_response(raw: str) -> str:
        if not raw:
            return raw
        text = raw.strip()
        if text.startswith("```"):
            text = text[3:]
            text = text.lstrip()
            if text.lower().startswith("json"):
                # remove optional json language hint
                newline_index = text.find("\n")
                if newline_index != -1:
                    text = text[newline_index + 1 :]
                else:
                    text = ""
            end_fence = text.rfind("```")
            if end_fence != -1:
                text = text[:end_fence]
        if text.endswith("```"):
            text = text[: -3]
        return text.strip()
