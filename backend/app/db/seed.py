import hashlib
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.entities import Department, Role, User, Application, Policy, PolicyVersion


def seed(db):
    from app.core.config import settings

    if settings().assessflow_mode != "demo":
        raise ValueError("Synthetic fixtures require explicit demo mode")
    if db.scalar(select(User.id).limit(1)):
        return
    db.add_all([Department(id=x, name=x.title()) for x in ["finance", "it", "sales"]])
    db.add_all([Role(id=x) for x in ["employee", "approver", "admin", "operator"]])
    db.flush()
    db.add_all(
        [
            User(id="manager", name="Morgan Taylor", role="approver", department="finance"),
            User(id="admin", name="Alex Rivers", role="admin", department="it"),
            User(id="operator", name="Sam Chen", role="operator", department="it"),
        ]
    )
    db.flush()
    db.add_all(
        [
            User(
                id="employee",
                name="Jamie Ellis",
                role="employee",
                department="finance",
                manager_id="manager",
            ),
            User(
                id="other",
                name="Casey Jordan",
                role="employee",
                department="sales",
                manager_id="manager",
            ),
        ]
    )
    db.add_all(
        [
            Application(
                id="finance-reports", name="Financial Reporting", levels=["reader", "analyst"]
            ),
            Application(id="service-desk", name="Service Desk", levels=["reader"]),
        ]
    )
    db.flush()
    for pid, app, title, department, content in [
        (
            "finance-policy",
            "finance-reports",
            "Financial reporting access",
            "finance",
            "Finance reporting access is restricted to finance employees. A business justification of at least 20 characters is required. Reader and analyst access require manager approval. All exceptions require manual review. Never grant access without a human decision.",
        ),
        (
            "desk-policy",
            "service-desk",
            "Service desk access",
            "all",
            "Employees may request reader access to Service Desk with a business justification of at least 20 characters. Manager approval is mandatory. No automatic provisioning is permitted.",
        ),
    ]:
        db.add(Policy(id=pid, application_id=app, title=title, department=department))
        db.flush()
        db.add(
            PolicyVersion(
                policy_id=pid,
                version=1,
                content=content,
                chunks=[content],
                digest=hashlib.sha256(content.encode()).hexdigest(),
                expires_at="2030-12-31",
            )
        )
    db.flush()


if __name__ == "__main__":
    with SessionLocal.begin() as session:
        seed(session)
    print("Synthetic fixtures seeded (idempotent).")
