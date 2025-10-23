from __future__ import annotations

from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from .models import RoutingDecision
from .services.executor import build_default_orchestrator
from .services.llm_client import ClaudeMessagesCallable, ClaudeMessagesError
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


app = FastAPI(title="DevoLight Router Demo")


def build_router_service() -> RouterService:
    session_repository = SessionRepository()
    try:
        llm_callable = ClaudeMessagesCallable.from_environment()
    except ClaudeMessagesError as exc:
        raise RuntimeError(f"无法初始化 Claude 客户端: {exc}") from exc
    orchestrator: ExecutionOrchestrator = build_default_orchestrator(llm_callable)
    meta_client = MetaRouterClient(llm_callable)
    service = RouterService(
        meta_client=meta_client,
        context_builder=ContextBuilder(),
        orchestrator=orchestrator,
        fallback_manager=FallbackManager(),
        session_repository=session_repository,
    )
    return service


def get_router_service(service=None) -> RouterService:
    # In production you might inject a singleton via dependency overrides.
    return service or build_router_service()


@app.post("/route", response_model=RouterResponseModel)
def route(session_id: str, payload: dict, service: RouterService = Depends(get_router_service)) -> RouterResponseModel:
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
