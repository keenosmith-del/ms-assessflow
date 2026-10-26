"""Small repository-specific accidental secret check, not a comprehensive scanner."""

import re
import subprocess
from pathlib import Path

patterns = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(r"sk-[A-Za-z0-9]{32,}"),
]
violations = []
for name in subprocess.check_output(["git", "ls-files"], text=True).splitlines():
    path = Path(name)
    if path.name.startswith(".env") and path.name != ".env.example":
        violations.append(name)
    if path.is_file():
        text = path.read_text(errors="ignore")
        if any(pattern.search(text) for pattern in patterns):
            violations.append(name)
if violations:
    raise SystemExit("Potential secrets in: " + ", ".join(sorted(set(violations))))
print("Tracked-file accidental secret scan passed (limited patterns).")
