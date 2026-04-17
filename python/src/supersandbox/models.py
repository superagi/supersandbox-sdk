"""Pydantic models for the SuperSandbox API."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

_ALIASES = ConfigDict(populate_by_name=True)


# ── Image ────────────────────────────────────────────────────────────────────

class ImageAuth(BaseModel):
    username: str
    password: str


class ImageSpec(BaseModel):
    uri: str
    auth: Optional[ImageAuth] = None


# ── Resources ────────────────────────────────────────────────────────────────

ResourceLimits = Dict[str, str]


# ── Network policy ───────────────────────────────────────────────────────────

class NetworkRule(BaseModel):
    action: str
    target: str


class NetworkPolicy(BaseModel):
    model_config = _ALIASES
    default_action: Optional[str] = Field(None, alias="defaultAction")
    egress: List[NetworkRule] = Field(default_factory=list)


# ── Volumes ──────────────────────────────────────────────────────────────────

class PVC(BaseModel):
    model_config = _ALIASES
    claim_name: str = Field(..., alias="claimName")


class Host(BaseModel):
    path: str


class OSSFS(BaseModel):
    """Alibaba Cloud OSS mount backend via ossfs."""

    model_config = _ALIASES
    bucket: str
    endpoint: str
    version: Literal["1.0", "2.0"] = "2.0"
    options: Optional[List[str]] = None
    access_key_id: Optional[str] = Field(None, alias="accessKeyId")
    access_key_secret: Optional[str] = Field(None, alias="accessKeySecret")


class Volume(BaseModel):
    model_config = _ALIASES
    name: str
    host: Optional[Host] = None
    pvc: Optional[PVC] = None
    ossfs: Optional[OSSFS] = None
    mount_path: str = Field(..., alias="mountPath")
    read_only: bool = Field(False, alias="readOnly")
    sub_path: Optional[str] = Field(None, alias="subPath")


# ── Status ───────────────────────────────────────────────────────────────────

class SandboxStatus(BaseModel):
    model_config = _ALIASES
    state: str
    reason: Optional[str] = None
    message: Optional[str] = None
    last_transition_at: Optional[datetime] = Field(None, alias="lastTransitionAt")


# ── Sandbox ──────────────────────────────────────────────────────────────────

class Sandbox(BaseModel):
    model_config = _ALIASES
    id: str
    image: ImageSpec
    status: SandboxStatus
    metadata: Optional[Dict[str, str]] = None
    entrypoint: List[str]
    expires_at: Optional[datetime] = Field(None, alias="expiresAt")
    created_at: datetime = Field(..., alias="createdAt")
    last_activity_at: Optional[datetime] = Field(None, alias="lastActivityAt")


class CreateSandboxResponse(BaseModel):
    model_config = _ALIASES
    id: str
    status: SandboxStatus
    metadata: Optional[Dict[str, str]] = None
    expires_at: Optional[datetime] = Field(None, alias="expiresAt")
    created_at: datetime = Field(..., alias="createdAt")
    entrypoint: List[str]


# ── List ─────────────────────────────────────────────────────────────────────

class PaginationInfo(BaseModel):
    model_config = _ALIASES
    page: int
    page_size: int = Field(..., alias="pageSize")
    total_items: int = Field(..., alias="totalItems")
    total_pages: int = Field(..., alias="totalPages")
    has_next_page: bool = Field(..., alias="hasNextPage")


class ListSandboxesResponse(BaseModel):
    items: List[Sandbox]
    pagination: PaginationInfo


# ── Expiration ────────────────────────────────────────────────────────────────

class RenewExpirationResponse(BaseModel):
    model_config = _ALIASES
    expires_at: datetime = Field(..., alias="expiresAt")


# ── Resource limits ──────────────────────────────────────────────────────────

class UpdateResourceLimitsResponse(BaseModel):
    model_config = _ALIASES
    id: str
    status: SandboxStatus
    resource_limits: Dict[str, str] = Field(..., alias="resourceLimits")


# ── Endpoint ─────────────────────────────────────────────────────────────────

class Endpoint(BaseModel):
    endpoint: str
    headers: Optional[Dict[str, str]] = None


# ── Env ──────────────────────────────────────────────────────────────────────

class UpdateEnvResponse(BaseModel):
    id: str
    env: Dict[str, str]


# ── Tasks ─────────────────────────────────────────────────────────────────────

class Task(BaseModel):
    model_config = _ALIASES
    id: str = Field(..., validation_alias=AliasChoices("id", "taskId"))
    status: Optional[str] = None
    exit_code: Optional[int] = Field(None, alias="exitCode")
    started_at: Optional[datetime] = Field(None, alias="startedAt")
    finished_at: Optional[datetime] = Field(None, alias="finishedAt")


class TaskLogsResponse(BaseModel):
    logs: str
    next_cursor: Optional[int] = None
