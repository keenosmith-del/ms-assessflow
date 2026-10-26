import json
from pathlib import Path

from openapi_spec_validator import validate

for filename in ["docs/api/openapi.json", "copilot/tools/connector.swagger.json"]:
    validate(json.loads(Path(filename).read_text()))
    print(f"Valid contract: {filename}")
