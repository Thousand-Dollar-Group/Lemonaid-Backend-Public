from typing import List
from src.core.models import History

# --- Render histories into readable text
def render_histories(items: List[History]) -> str:
  rendered = []
  for h in items:
    # Be defensive if fields are optional
    q = getattr(h, "query", "")
    fd = getattr(h, "file_description", "")
    res = getattr(h, "resources", []) or []
    r = getattr(h, "result", "")
    rendered.append(
      f"- Q: {q}\n  FileDesc: {fd}\n  Resources: {', '.join(res)}\n  Result: {r}"
    )
  return "\n".join(rendered)

