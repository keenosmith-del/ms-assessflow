"""Explicit operator CLI for authorised tenant identity onboarding; no directory writes."""

import argparse
from uuid import UUID
from app.db.session import SessionLocal
from app.models.entities import User, Role, Department, Application


def onboard(db, object_id, name, role, department, manager_id=None):
    UUID(object_id)
    if manager_id:
        UUID(manager_id)
        if not db.get(User, manager_id):
            raise ValueError("Onboard manager before employees")
    for value in ["employee", "approver", "operator", "admin"]:
        if not db.get(Role, value):
            db.add(Role(id=value))
    for value in ["finance", "it", "sales"]:
        if not db.get(Department, value):
            db.add(Department(id=value, name=value.title()))
    db.flush()
    for app_id, app_name, levels in [
        ("finance-reports", "Financial Reporting", ["reader", "analyst"]),
        ("service-desk", "Service Desk", ["reader"]),
    ]:
        if not db.get(Application, app_id):
            db.add(Application(id=app_id, name=app_name, levels=levels))
    if db.get(User, object_id):
        raise ValueError("Identity exists; role changes require a separate reviewed operation")
    db.add(User(id=object_id, name=name, role=role, department=department, manager_id=manager_id))
    db.flush()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--object-id", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument(
        "--role", choices=["employee", "approver", "operator", "admin"], required=True
    )
    parser.add_argument("--department", choices=["finance", "it", "sales"], required=True)
    parser.add_argument("--manager")
    args = parser.parse_args()
    with SessionLocal.begin() as db:
        onboard(db, args.object_id, args.name, args.role, args.department, args.manager)
    print("Authorised application identity onboarded. No Entra permissions changed.")
