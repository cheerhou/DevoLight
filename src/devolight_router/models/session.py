from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class RoleCallRecord(BaseModel):
    role_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    highlights: Optional[str] = None
    feedback: Optional[str] = None


class SessionState(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    recent_calls: List[RoleCallRecord] = Field(default_factory=list)
    summary: Optional[str] = None
    last_known_spiritual_state: Optional[str] = None

    def last_role(self) -> Optional[str]:
        if not self.recent_calls:
            return None
        return self.recent_calls[-1].role_name

