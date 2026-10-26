"""Explicit operator-only Search schema/index repair utility. Never runs at startup."""

import argparse
from sqlalchemy import select
from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchFieldDataType,
)
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.entities import Policy
from app.services.policies import latest
from app.integrations.microsoft.providers import SearchProvider


def configure(apply=False, reindex=False):
    cfg = settings()
    if cfg.assessflow_mode != "azure":
        raise ValueError("Search administration requires explicit Azure mode")
    if not apply:
        print(
            "Plan: create/update keyword schema and optionally reindex current policies. Add --apply to execute."
        )
        return
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SimpleField(name="version_id", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="application_id", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="department", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="chunk_index", type=SearchFieldDataType.Int32),
        SearchableField(name="content", type=SearchFieldDataType.String),
    ]
    with DefaultAzureCredential() as credential:
        with SearchIndexClient(cfg.azure_search_endpoint, credential) as client:
            client.create_or_update_index(SearchIndex(name=cfg.azure_search_index, fields=fields))
    if reindex:
        with SessionLocal() as db:
            for policy in db.scalars(select(Policy)):
                version = latest(db, policy.id)
                if version:
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
                            for i, chunk in enumerate(version.chunks)
                        ]
                    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--reindex", action="store_true")
    args = parser.parse_args()
    configure(args.apply, args.reindex)
