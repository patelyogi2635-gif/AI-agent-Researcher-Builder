# api/schemas.py
from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class RunMode(str, Enum):
    AUTO     = "auto"
    RESEARCH = "research"
    BUILDER  = "builder"
    BOTH     = "both"


class AgentRequest(BaseModel):
    query:      str       = Field(..., min_length=3, max_length=500)
    mode:       RunMode   = RunMode.AUTO
    max_steps:  Optional[int] = Field(None, ge=1, le=20)


class SSEEvent(BaseModel):
    event:   str
    graph:   str
    node:    str
    message: str
    data:    Optional[dict] = None


class ReportResponse(BaseModel):
    step_id:   int
    topic:     str
    summary:   str
    findings:  str
    sources:   list[str]


class PageResponse(BaseModel):
    step_id:     int
    description: str
    html:        str
    css_lines:   int
    js_lines:    int


class AgentResponse(BaseModel):
    success:          bool
    mode:             str
    intent_summary:   str
    research_reports: list[ReportResponse]
    built_pages:      list[PageResponse]
    execution_steps:  int
    error:            Optional[str] = None