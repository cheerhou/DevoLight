from __future__ import annotations

from typing import Dict, Optional

from ..prompts import load_prompt
from .llm_client import ClaudeMessagesCallable

from ..models import RoutingContext, SelectedRole
from .router import ExecutionOrchestrator, RoleExecutionResult, RoleExecutor


def _create_stub_executor(prefix: str) -> RoleExecutor:
    def executor(context: RoutingContext, role: SelectedRole) -> str:
        scripture = context.scripture or "未知经文"
        return f"{prefix} 响应 {scripture}，意图评分 {role.score:.2f}。备注：{role.handoff_note}"

    return executor


class PromptRoleExecutor:
    """Invoke a prompt-driven role via LLM callable."""

    def __init__(self, llm_call: ClaudeMessagesCallable, prompt_name: str) -> None:
        self._llm_call = llm_call
        self._prompt_template = load_prompt(prompt_name)

    def __call__(self, context: RoutingContext, role: SelectedRole) -> str:
        payload = self._build_payload(context, role)
        return self._llm_call(self._prompt_template, payload)

    @staticmethod
    def _build_payload(context: RoutingContext, role: SelectedRole) -> Dict:
        user_profile = (
            context.user_profile.dict(exclude_none=True) if context.user_profile else None
        )
        payload: Dict = {
            "scripture": context.scripture,
            "user_question": context.user_question,
            "user_profile": user_profile,
            "spiritual_state": context.spiritual_state,
            "session_stage": context.session_stage,
            "history_summary": context.history_summary,
            "handoff_note": role.handoff_note,
            "role_reason": role.reason,
            "role_score": role.score,
            "raw_payload": context.raw_payload,
            "warnings": context.requires_attention(),
        }
        return {key: value for key, value in payload.items() if value not in (None, {})}


def build_default_orchestrator(
    llm_call: Optional[ClaudeMessagesCallable] = None,
) -> ExecutionOrchestrator:
    orchestrator = ExecutionOrchestrator()
    if llm_call is None:
        executors: Dict[str, RoleExecutor] = {
            "AntiochTeacher": _create_stub_executor("安提阿老师"),
            "LukeScribe": _create_stub_executor("路加笔者"),
            "MarthaMentor": _create_stub_executor("马大姊妹"),
            "BarnabasCompanion": _create_stub_executor("巴拿巴友伴"),
        }
    else:
        executors = {
            "AntiochTeacher": PromptRoleExecutor(llm_call, "antioch_teacher"),
            "LukeScribe": PromptRoleExecutor(llm_call, "luke_scribe"),
            "MarthaMentor": PromptRoleExecutor(llm_call, "martha_mentor"),
            "BarnabasCompanion": PromptRoleExecutor(llm_call, "barnabas_companion"),
        }
    for name, executor in executors.items():
        orchestrator.register(name, executor)
    return orchestrator
