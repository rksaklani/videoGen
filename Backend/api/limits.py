"""Generation limits loaded from Backend/config.yaml (single source of truth)."""
from pathlib import Path
import yaml

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"
with open(_CONFIG_PATH, encoding="utf-8") as _f:
    _INFER = yaml.safe_load(_f)["inference"]

# Upper bound for Form validation / OpenAPI (must match inference.max_duration_seconds)
MAX_DURATION_SECONDS = int(_INFER["max_duration_seconds"])

MAX_DURATION_HELP = (
    "Maximum length of the generated video in seconds. "
    "Use **0** to follow the **full input audio** duration (still capped by the server "
    f"maximum of **{MAX_DURATION_SECONDS}s** per job). "
    "If set > 0, output length is min(audio length, this value, server max)."
)

CHUNK_SECONDS = float(_INFER.get("chunk_duration_seconds", 5))
