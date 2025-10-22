import json

import pytest

from src.devolight_router.models import RoutingContext, RoutingMode
from src.devolight_router.services.executor import build_default_orchestrator
from src.devolight_router.services.meta_client import MetaRouterClient, MetaRouterResponseError
from src.devolight_router.services.router import (
    ContextBuilder,
    FallbackManager,
    RouterService,
    SessionRepository,
)


def test_meta_router_client_parses_valid_json():
    raw_response = json.dumps(
        {
            "mode": "single",
            "selected_roles": [
                {
                    "name": "AntiochTeacher",
                    "score": 0.92,
                    "reason": "用户提出神学相关问题。",
                    "handoff_note": "最终输出",
                }
            ],
            "overall_rationale": "保持单角色回应即可。",
            "fallback_plan": "必要时切换至智能协作。",
            "warnings": [],
        },
        ensure_ascii=False,
    )
    client = MetaRouterClient(lambda prompt, payload: raw_response)
    context = RoutingContext(scripture="约3:16")

    decision = client.route(context)

    assert decision.mode is RoutingMode.SINGLE
    assert decision.selected_roles[0].name == "AntiochTeacher"


def test_meta_router_client_raises_on_invalid_json():
    client = MetaRouterClient(lambda prompt, payload: "{ invalid json }")
    context = RoutingContext(scripture="约3:16")

    with pytest.raises(MetaRouterResponseError):
        client.route(context)


def test_router_service_runs_with_stub_meta_router():
    def llm_call(prompt, payload):
        return json.dumps(
            {
                "mode": "smart",
                "selected_roles": [
                    {
                        "name": "AntiochTeacher",
                        "score": 0.9,
                        "reason": "先建立神学脉络。",
                        "handoff_note": "请交给马大姊妹延伸应用。",
                    },
                    {
                        "name": "MarthaMentor",
                        "score": 0.85,
                        "reason": "用户想要生活应用。",
                        "handoff_note": "最终输出",
                    },
                ],
                "overall_rationale": "组合神学和应用，提供层次化回应。",
                "fallback_plan": "若用户仍疑惑，追加历史背景。",
                "warnings": [],
            },
            ensure_ascii=False,
        )

    orchestrator = build_default_orchestrator()
    service = RouterService(
        meta_client=MetaRouterClient(llm_call),
        context_builder=ContextBuilder(),
        orchestrator=orchestrator,
        fallback_manager=FallbackManager(),
        session_repository=SessionRepository(),
    )

    result = service.route(
        session_id="session-1",
        raw_payload={
            "scripture": "约3:16",
            "user_question": "这段经文在生活中如何应用？",
        },
    )

    assert result.decision.mode is RoutingMode.SMART
    assert [output.role_name for output in result.role_outputs] == [
        "AntiochTeacher",
        "MarthaMentor",
    ]
    assert not result.warnings

