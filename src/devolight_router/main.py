from __future__ import annotations

from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from .models import RoutingDecision
from .services.executor import build_default_orchestrator
from .services.meta_client import MetaRouterClient
from .services.router import (
    ContextBuilder,
    ExecutionOrchestrator,
    FallbackManager,
    RouterResult,
    RouterService,
    SessionRepository,
)


class RoleOutputModel(BaseModel):
    role_name: str
    content: str


class RouterResponseModel(BaseModel):
    decision: RoutingDecision
    role_outputs: List[RoleOutputModel]
    warnings: List[str]


class SimpleLLMStub:
    """A deterministic stub that imitates the meta router JSON response."""

    def __call__(self, prompt: str, payload: dict) -> str:
        warnings = payload.get("system_warnings", [])
        scripture = payload.get("scripture")
        if warnings and "缺少经文章节" in warnings[0]:
            return self._halt_response(warnings)

        roles = []
        question = (payload.get("user_question") or "").lower()
        intents = set(payload.get("intents", []))
        if "历史" in question or "背景" in question or "history" in intents:
            roles.append(
                self._role("LukeScribe", 0.86, "用户关心经文的历史背景。", "请提供历史与地理背景概述。")
            )
        if "应用" in question or "生活" in question or "application" in intents:
            roles.append(
                self._role("MarthaMentor", 0.81, "用户想知道生活应用与实践。", "结合用户画像给出三到五个应用。")
            )
        if not roles:
            roles.append(
                self._role("AntiochTeacher", 0.9, "需要先建立神学脉络。", "最终输出")
            )
        mode = "single" if len(roles) == 1 else "smart"
        rationale = f"根据用户提问与会话阶段，建议调用 {', '.join(r['name'] for r in roles)}。"
        response = {
            "mode": mode,
            "selected_roles": roles,
            "overall_rationale": rationale,
            "fallback_plan": "若回应不符需求，请改为顺序流程或提示用户补充问题。",
            "warnings": warnings,
        }
        return json_dumps(response)

    @staticmethod
    def _halt_response(warnings: list) -> str:
        response = {
            "mode": "halt",
            "selected_roles": [],
            "overall_rationale": "关键信息缺失，需要用户补充后再继续。",
            "fallback_plan": "请提示用户提供经文章节等必要输入。",
            "warnings": warnings,
        }
        return json_dumps(response)

    @staticmethod
    def _role(name: str, score: float, reason: str, note: str) -> dict:
        return {
            "name": name,
            "score": score,
            "reason": reason,
            "handoff_note": note,
        }


def json_dumps(data: dict) -> str:
    """Ensure consistent JSON serialization with ensure_ascii=False."""
    import json

    return json.dumps(data, ensure_ascii=False)


app = FastAPI(title="DevoLight Router Demo")


def build_router_service() -> RouterService:
    session_repository = SessionRepository()
    orchestrator: ExecutionOrchestrator = build_default_orchestrator()
    meta_client = MetaRouterClient(SimpleLLMStub())
    service = RouterService(
        meta_client=meta_client,
        context_builder=ContextBuilder(),
        orchestrator=orchestrator,
        fallback_manager=FallbackManager(),
        session_repository=session_repository,
    )
    return service


def get_router_service(service: Optional[RouterService] = None) -> RouterService:
    # In production you might inject a singleton via dependency overrides.
    return service or build_router_service()


@app.post("/route", response_model=RouterResponseModel)
def route(session_id: str, payload: dict, service: RouterService = Depends(get_router_service)):
    """Route a single request through the meta router."""
    try:
        result = service.route(session_id=session_id, raw_payload=payload)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return RouterResponseModel(
        decision=result.decision,
        role_outputs=[
            RoleOutputModel(role_name=output.role_name, content=output.content)
            for output in result.role_outputs
        ],
        warnings=result.warnings,
    )

