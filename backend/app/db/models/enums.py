from __future__ import annotations

from enum import Enum


class RoleName(str, Enum):
    admin = "admin"
    department_admin = "department_admin"
    user = "user"
    finance = "finance"


class ApprovalStatus(str, Enum):
    approved = "approved"
    pending = "pending"
    rejected = "rejected"


class VisibilityScope(str, Enum):
    company = "company"
    department = "department"
    personal = "personal"


class DocumentStatus(str, Enum):
    pending = "pending"
    parsing = "parsing"
    chunking = "chunking"
    embedding = "embedding"
    ready = "ready"
    failed = "failed"


class BlockType(str, Enum):
    text = "text"
    table = "table"
    image = "image"


class ChunkMethod(str, Enum):
    sentence = "sentence"
    token = "token"


class MessageRole(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


class AgentRunStatus(str, Enum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"


class AgentStepStatus(str, Enum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    skipped = "skipped"


class ExpenseStatus(str, Enum):
    draft = "draft"
    submitted = "submitted"
    need_supplement = "need_supplement"
    finance_review = "finance_review"
    approved = "approved"
    rejected = "rejected"


class AuditResult(str, Enum):
    pass_ = "pass"
    attention = "attention"
    risk = "risk"


class AttachmentType(str, Enum):
    invoice = "invoice"
    payment = "payment"
    approval = "approval"
    other = "other"


class ExpenseApprovalAction(str, Enum):
    submit = "submit"
    resubmit = "resubmit"
    approve = "approve"
    reject = "reject"
    request_supplement = "request_supplement"


class SettingValueType(str, Enum):
    string = "string"
    number = "number"
    boolean = "boolean"
    json = "json"
    secret = "secret"


class SubjectType(str, Enum):
    user = "user"
    role = "role"
    org = "org"
