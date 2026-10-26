"""Fail-closed GitHub staging release gates; no Azure calls or writes."""

import json
import os
import re
import subprocess
import sys

ENVIRONMENT = "azure-staging"


def github(path):
    return json.loads(subprocess.check_output(["gh", "api", path], text=True))


def validate_environment(environment, branches):
    reviewers = [
        x
        for x in environment.get("protection_rules", [])
        if x["type"] == "required_reviewers"
    ]
    if not any(
        x.get("reviewers") and x.get("prevent_self_review") is True for x in reviewers
    ):
        raise ValueError(
            "azure-staging requires reviewers and prevention of self-review"
        )
    if (environment.get("deployment_branch_policy") or {}).get(
        "custom_branch_policies"
    ) is not True:
        raise ValueError("Environment must use selected deployment branches")
    rules = branches.get("branch_policies", [])
    if (
        branches.get("total_count") != 1
        or len(rules) != 1
        or rules[0].get("name") != "main"
        or rules[0].get("type") != "branch"
    ):
        raise ValueError("Only the main branch may deploy")


def validate_approval(reviews, actor):
    if not any(
        x.get("state") == "approved"
        and x.get("user", {}).get("login", "").lower() not in {"", actor.lower()}
        and any(
            e.get("name", "").lower() == ENVIRONMENT for e in x.get("environments", [])
        )
        for x in reviews
    ):
        raise ValueError(
            "A recorded independent environment approval is required; bypass is insufficient"
        )


def validate_ci(runs, sha):
    if not any(
        x.get("head_sha") == sha
        and x.get("head_branch") == "main"
        and x.get("event") == "push"
        and x.get("status") == "completed"
        and x.get("conclusion") == "success"
        for x in runs.get("workflow_runs", [])
    ):
        raise ValueError(
            "The exact release commit needs a successful Verify AssessFlow push run on main"
        )


def main():
    repo = os.environ["GITHUB_REPOSITORY"]
    sha = os.environ["RELEASE_SHA"]
    if (
        os.environ.get("GITHUB_REF") != "refs/heads/main"
        or os.environ.get("GITHUB_EVENT_NAME") != "workflow_dispatch"
    ):
        raise ValueError("Only manual dispatch from main is permitted")
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("release_sha must be a full lowercase commit SHA")
    if (
        os.environ.get("CONFIRMATION") != "DEPLOY STAGING"
        or os.environ.get("SCHEMA_COMPATIBLE") != "true"
    ):
        raise ValueError(
            "Explicit staging and schema compatibility confirmations required"
        )
    subprocess.run(["git", "merge-base", "--is-ancestor", sha, "HEAD"], check=True)
    environment = github(f"repos/{repo}/environments/{ENVIRONMENT}")
    branches = github(
        f"repos/{repo}/environments/{ENVIRONMENT}/deployment-branch-policies?per_page=100"
    )
    validate_environment(environment, branches)
    validate_ci(
        github(
            f"repos/{repo}/actions/workflows/verify.yml/runs?head_sha={sha}&event=push&status=completed&per_page=100"
        ),
        sha,
    )
    if len(sys.argv) > 1 and sys.argv[1] == "approved":
        validate_approval(
            github(
                f"repos/{repo}/actions/runs/{os.environ['GITHUB_RUN_ID']}/approvals"
            ),
            os.environ["GITHUB_ACTOR"],
        )
    print("Release SHA, successful CI and environment protection gates passed.")


if __name__ == "__main__":
    main()
