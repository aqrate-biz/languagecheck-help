#!/usr/bin/env python3
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "assets" / "javascripts" / "firebase-auth-overrides.js"

def js_string_or_null(value: str) -> str:
    if value is None or value == "":
        return "null"
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


config_map = {
    "apiKey": os.getenv("FIREBASE_API_KEY", ""),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", ""),
    "projectId": os.getenv("FIREBASE_PROJECT_ID", ""),
    "appId": os.getenv("FIREBASE_APP_ID", ""),
}

config_lines = []
for key, value in config_map.items():
    config_lines.append(f"  {key}: {js_string_or_null(value)},")

content = [
    "window.LANGUAGECHECK_FIREBASE_CONFIG_OVERRIDES = {",
    *config_lines,
    "};",
    "",
]

OUT.write_text("\n".join(content), encoding="utf-8")
print(f"Generated {OUT}")
