from __future__ import annotations

import json
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

    def _prepare_payload(self, context: RoutingContext) -> Tuple[str, Dict]:
        user_payload: Dict = context.raw_payload or context.dict(exclude_none=True)
        warnings = context.requires_attention()
        if warnings:
            user_payload = {**user_payload, "system_warnings": warnings}
        return self._prompt_template, user_payload

    def route(self, context: RoutingContext) -> RoutingDecision:
        prompt, payload = self._prepare_payload(context)
        raw = self._llm_call(prompt, payload)
        try:
            response = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise MetaRouterResponseError("MetaRouter 返回值不是合法 JSON。") from exc
        try:
            decision = RoutingDecision.parse_obj(response)
        except ValidationError as exc:
            raise MetaRouterResponseError("MetaRouter 返回值未通过数据模型校验。") from exc
        return decision

