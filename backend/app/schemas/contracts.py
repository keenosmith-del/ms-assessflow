from typing import Literal
from datetime import date
from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RequestInput(StrictModel):
    application_id: str = Field(min_length=1, max_length=80)
    access_level: str = Field(min_length=1, max_length=50)
    justification: str = Field(default="", max_length=4000)


class Clarification(StrictModel):
    justification: str = Field(min_length=20, max_length=4000)


class DecisionInput(StrictModel):
    decision: Literal["approved", "rejected"]
    reason: str = Field(min_length=10, max_length=2000)


class CommentInput(StrictModel):
    body: str = Field(min_length=1, max_length=2000)


class FulfilInput(StrictModel):
    reference: str = Field(min_length=5, max_length=200)


class PolicyInput(StrictModel):
    application_id: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=5, max_length=180)
    department: Literal["all", "finance", "it", "sales"]
    content: str = Field(min_length=40, max_length=100000)
    expires_at: date


class Citation(StrictModel):
    version_id: str
    chunk_index: int = Field(ge=0)
    quote: str


class AssessmentOutput(StrictModel):
    recommendation: Literal["approve", "deny", "manual_review"]
    explanation: str
    missing_fields: list[str]
    uncertainty: str
    citations: list[Citation]


class CallbackInput(StrictModel):
    event_id: str = Field(min_length=8, max_length=80)
    request_id: str
    actor_id: str
    decision: Literal["approved", "rejected"]
    reason: str = Field(min_length=10, max_length=2000)


class ToolRequestResult(StrictModel):
    id: str
    status: str


class ToolStatusResult(ToolRequestResult):
    next_step: str
    missing_fields: list[str]


class PolicyEvidence(StrictModel):
    policy_id: str
    version_id: str
    chunk_index: int
    quote: str
    title: str
    version: int
    expired: bool
    digest: str


class ToolSearchResult(StrictModel):
    items: list[PolicyEvidence]
