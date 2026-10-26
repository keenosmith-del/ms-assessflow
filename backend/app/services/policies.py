import hashlib
from datetime import date
from fastapi import HTTPException
from sqlalchemy import select, func
from app.models.entities import Policy, PolicyVersion
from app.core.config import settings
from app.integrations.microsoft.providers import PrivacyProvider, SearchProvider


def permitted(user, policy):
    return policy.department in {"all", user.department} or user.role == "admin"


def latest(db, policy_id):
    return db.scalar(
        select(PolicyVersion)
        .where(PolicyVersion.policy_id == policy_id)
        .order_by(PolicyVersion.version.desc())
        .limit(1)
    )


def retrieve(db, user, query="", application_id=None):
    if settings().assessflow_mode == "azure":
        # Filter Search results against canonical version and ACL again; stale index data is untrusted.
        hits = SearchProvider().search(query or "access", user.department, application_id)
        result = []
        for hit in hits:
            version = db.get(PolicyVersion, hit.get("version_id"))
            if not version:
                continue
            policy = db.get(Policy, version.policy_id)
            if not permitted(user, policy) or latest(db, policy.id).id != version.id:
                continue
            if application_id and policy.application_id != application_id:
                continue
            index = hit.get("chunk_index")
            if not isinstance(index, int) or not 0 <= index < len(version.chunks):
                continue
            result.append(evidence(policy, version, index))
        return result
    result = []
    words = set(query.lower().split())
    for policy in db.scalars(select(Policy)):
        if not permitted(user, policy) or (
            application_id and policy.application_id != application_id
        ):
            continue
        version = latest(db, policy.id)
        if not version:
            continue
        for index, chunk in enumerate(version.chunks):
            if not words or any(word in (chunk + policy.title).lower() for word in words):
                result.append(evidence(policy, version, index))
    return result[:8]


def evidence(policy, version, index):
    return {
        "policy_id": policy.id,
        "version_id": version.id,
        "chunk_index": index,
        "quote": version.chunks[index],
        "title": policy.title,
        "version": version.version,
        "expired": version.expires_at < date.today().isoformat(),
        "digest": version.digest,
    }


def ingest(db, payload):
    if payload.expires_at < date.today():
        raise HTTPException(422, "New policy must not be expired")
    text = payload.content
    if "\x00" in text:
        raise HTTPException(422, "Only UTF-8 plain text policy documents are supported")
    text = PrivacyProvider().redact(text).text
    policy = db.scalar(
        select(Policy).where(Policy.application_id == payload.application_id).with_for_update()
    )
    if policy and (policy.department != payload.department):
        raise HTTPException(409, "Policy ACL changes require a separate migration")
    if not policy:
        policy = Policy(
            application_id=payload.application_id,
            title=payload.title,
            department=payload.department,
        )
        db.add(policy)
        db.flush()
    else:
        policy.title = payload.title
    number = (
        db.scalar(
            select(func.max(PolicyVersion.version)).where(PolicyVersion.policy_id == policy.id)
        )
        or 0
    ) + 1
    chunks = [text[i : i + 1200] for i in range(0, len(text), 1000)]
    version = PolicyVersion(
        policy_id=policy.id,
        version=number,
        content=text,
        chunks=chunks,
        digest=hashlib.sha256(text.encode()).hexdigest(),
        expires_at=str(payload.expires_at),
    )
    db.add(version)
    db.flush()
    if settings().assessflow_mode == "azure":
        SearchProvider().index(
            [
                {
                    "id": f"{version.id}-{i}",
                    "version_id": version.id,
                    "application_id": policy.application_id,
                    "department": policy.department,
                    "chunk_index": i,
                    "content": chunk,
                }
                for i, chunk in enumerate(chunks)
            ]
        )
    return policy, version
