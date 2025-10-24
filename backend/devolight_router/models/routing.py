from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class RoutingMode(str, Enum):
    SINGLE = "single"
    SEQUENCE = "sequence"
    SMART = "smart"
    HALT = "halt"


class UserProfile(BaseModel):
    age_group: Optional[str] = None
    profession: Optional[str] = None
    spiritual_state: Optional[str] = None
    concerns: List[str] = Field(default_factory=list)


class RoutingContext(BaseModel):
    scripture: Optional[str] = None
    text: Optional[str] = None
    user_question: Optional[str] = None
    user_profile: Optional[UserProfile] = None
    spiritual_state: Optional[str] = None
    session_stage: Optional[str] = None
    history_summary: Optional[str] = None
    last_role: Optional[str] = None
    raw_payload: dict = Field(default_factory=dict)

    def requires_attention(self) -> List[str]:
        """Return a list of missing critical fields."""
        warnings: List[str] = []
        if not self.scripture:
            warnings.append("缺少经文章节字段 scripture。")
        return warnings


class SelectedRole(BaseModel):
    name: str
    score: float = Field(ge=0.0, le=1.0)
    reason: str
    handoff_note: str

    @validator("name")
    def validate_role_name(cls, value: str) -> str:
        allowed = {
            "AntiochTeacher",
            "LukeScribe",
            "MarthaMentor",
            "BarnabasCompanion",
        }
        if value not in allowed:
            raise ValueError(f"未知角色 {value}")
        return value


class RoutingDecision(BaseModel):
    mode: RoutingMode
    selected_roles: List[SelectedRole] = Field(default_factory=list)
    overall_rationale: str
    fallback_plan: str
    warnings: List[str] = Field(default_factory=list)

    @validator("selected_roles", always=True)
    def validate_roles_for_mode(
        cls, roles: List[SelectedRole], values
    ) -> List[SelectedRole]:
        mode: RoutingMode = values.get("mode", RoutingMode.HALT)
        if mode == RoutingMode.HALT and roles:
            raise ValueError("mode 为 halt 时 selected_roles 必须为空。")
        if mode in (RoutingMode.SINGLE, RoutingMode.SEQUENCE, RoutingMode.SMART) and not roles:
            raise ValueError(f"mode 为 {mode.value} 时必须至少选择一个角色。")
        if mode == RoutingMode.SINGLE and len(roles) != 1:
            raise ValueError("mode 为 single 时 selected_roles 必须仅包含一个角色。")
        return roles

