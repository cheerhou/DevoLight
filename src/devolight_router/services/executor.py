from __future__ import annotations

from typing import Dict

from ..models import RoutingContext, SelectedRole
from .router import ExecutionOrchestrator, RoleExecutionResult, RoleExecutor


def _create_stub_executor(prefix: str) -> RoleExecutor:
    def executor(context: RoutingContext, role: SelectedRole) -> str:
        scripture = context.scripture or "未知经文"
        return f"{prefix} 响应 {scripture}，意图评分 {role.score:.2f}。备注：{role.handoff_note}"

    return executor


def build_default_orchestrator() -> ExecutionOrchestrator:
    orchestrator = ExecutionOrchestrator()
    executors: Dict[str, RoleExecutor] = {
        "AntiochTeacher": _create_stub_executor("安提阿老师"),
        "LukeScribe": _create_stub_executor("路加笔者"),
        "MarthaMentor": _create_stub_executor("马大姊妹"),
        "BarnabasCompanion": _create_stub_executor("巴拿巴友伴"),
    }
    for name, executor in executors.items():
        orchestrator.register(name, executor)
    return orchestrator

