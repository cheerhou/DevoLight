from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from ..models import (
    RoleCallRecord,
    RoutingContext,
    RoutingDecision,
    RoutingMode,
    SelectedRole,
    SessionState,
)
from .meta_client import MetaRouterClient, MetaRouterResponseError

RoleExecutor = Callable[[RoutingContext, SelectedRole], str]


@dataclass
class RoleExecutionResult:
    role_name: str
    content: str


@dataclass
class RouterResult:
    decision: RoutingDecision
    role_outputs: List[RoleExecutionResult]
    warnings: List[str]


class ContextBuilder:
    """Builds routing context from raw payload and session state."""

    def build(self, raw_payload: Dict, session: Optional[SessionState]) -> RoutingContext:
        context = RoutingContext(
            scripture=raw_payload.get("scripture"),
            text=raw_payload.get("text"),
            user_question=raw_payload.get("user_question"),
            user_profile=raw_payload.get("user_profile"),
            spiritual_state=raw_payload.get("spiritual_state"),
            session_stage=raw_payload.get("session_stage"),
            history_summary=raw_payload.get("history_summary")
            or (session.summary if session else None),
            last_role=(session.last_role() if session else None),
            raw_payload=raw_payload,
        )
        if not raw_payload.get("spiritual_state") and session:
            context.spiritual_state = session.last_known_spiritual_state
        return context


class ExecutionOrchestrator:
    """Executes the selected roles sequentially."""

    def __init__(self, role_callers: Optional[Dict[str, RoleExecutor]] = None) -> None:
        self._role_callers = role_callers or {}

    def register(self, role_name: str, executor: RoleExecutor) -> None:
        self._role_callers[role_name] = executor

    def run(self, context: RoutingContext, decision: RoutingDecision) -> List[RoleExecutionResult]:
        results: List[RoleExecutionResult] = []
        for selected in decision.selected_roles:
            executor = self._role_callers.get(selected.name)
            if executor is None:
                raise KeyError(f"未注册角色执行器: {selected.name}")
            content = executor(context, selected)
            results.append(RoleExecutionResult(role_name=selected.name, content=content))
        return results


class FallbackManager:
    """Handles meta router failures or blocking warnings."""

    def handle_failure(
        self, error: Exception, context: RoutingContext
    ) -> RouterResult:
        pseudo_decision = RoutingDecision(
            mode=RoutingMode.HALT,
            selected_roles=[],
            overall_rationale="MetaRouter 调度失败，已触发兜底策略。",
            fallback_plan="提示用户检查输入或稍后重试。",
            warnings=[str(error), *context.requires_attention()],
        )
        return RouterResult(decision=pseudo_decision, role_outputs=[], warnings=pseudo_decision.warnings)


class RouterService:
    """High-level orchestration entry point."""

    def __init__(
        self,
        meta_client: MetaRouterClient,
        context_builder: Optional[ContextBuilder] = None,
        orchestrator: Optional[ExecutionOrchestrator] = None,
        fallback_manager: Optional[FallbackManager] = None,
        session_repository: Optional["SessionRepository"] = None,
    ) -> None:
        self._meta_client = meta_client
        self._context_builder = context_builder or ContextBuilder()
        self._orchestrator = orchestrator or ExecutionOrchestrator()
        self._fallback_manager = fallback_manager or FallbackManager()
        self._session_repository = session_repository

    def route(self, session_id: str, raw_payload: Dict) -> RouterResult:
        session = self._load_session(session_id)
        context = self._context_builder.build(raw_payload, session)
        try:
            decision = self._meta_client.route(context)
        except MetaRouterResponseError as error:
            return self._fallback_manager.handle_failure(error, context)
        if decision.mode == RoutingMode.HALT:
            return RouterResult(decision=decision, role_outputs=[], warnings=decision.warnings)
        try:
            outputs = self._orchestrator.run(context, decision)
        except Exception as error:  # noqa: BLE001
            return self._fallback_manager.handle_failure(error, context)
        self._persist_session(session_id, session, decision, outputs, context)
        warnings = [*decision.warnings, *context.requires_attention()]
        return RouterResult(decision=decision, role_outputs=outputs, warnings=warnings)

    def _load_session(self, session_id: str) -> Optional[SessionState]:
        if not self._session_repository:
            return None
        return self._session_repository.get(session_id)

    def _persist_session(
        self,
        session_id: str,
        session: Optional[SessionState],
        decision: RoutingDecision,
        outputs: List[RoleExecutionResult],
        context: RoutingContext,
    ) -> None:
        if not self._session_repository:
            return
        state = session or SessionState(session_id=session_id)
        for result in outputs:
            state.recent_calls.append(RoleCallRecord(role_name=result.role_name))
        state.summary = decision.overall_rationale
        if context.spiritual_state:
            state.last_known_spiritual_state = context.spiritual_state
        self._session_repository.save(state)


class SessionRepository:
    """Simple in-memory session repository for demonstration."""

    def __init__(self) -> None:
        self._store: Dict[str, SessionState] = {}

    def get(self, session_id: str) -> Optional[SessionState]:
        return self._store.get(session_id)

    def save(self, state: SessionState) -> None:
        self._store[state.session_id] = state

