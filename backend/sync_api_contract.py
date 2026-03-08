"""
Sync API contract from backend/api_endpoints.json to frontend and tests.

Usage:
    python backend/sync_api_contract.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "backend" / "api_endpoints.json"
FRONTEND_TARGET = ROOT / "frontend" / "js" / "api-contract.js"
TESTS_TARGET = ROOT / "tests" / "utils" / "api_contract.py"


def _normalize_key(method: str, endpoint: str) -> str:
    parts: List[str] = []
    for raw in endpoint.strip("/").split("/"):
        if not raw:
            continue
        if raw.startswith("{") and raw.endswith("}"):
            parts.extend(["BY", raw[1:-1]])
        else:
            parts.append(raw)

    return "_".join([method.upper(), *[p.replace("-", "_").upper() for p in parts]])


def _load_routes() -> Dict[str, str]:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    routes: Dict[str, str] = {}

    for category in data.get("categories", []):
        for item in category.get("endpoints", []):
            method = item.get("method", "GET")
            endpoint = item.get("endpoint", "")
            if not endpoint:
                continue
            routes[_normalize_key(method, endpoint)] = endpoint

    return dict(sorted(routes.items()))


def _render_frontend(routes: Dict[str, str]) -> str:
    lines = [
        "(function (window) {",
        "    const routes = {",
    ]

    for key, path in routes.items():
        lines.append(f"        {key}: '{path}',")

    lines.extend(
        [
            "    };",
            "",
            "    function buildRoute(routeKey, params) {",
            "        let template = routes[routeKey];",
            "        if (!template) {",
            "            throw new Error('Unknown API route key: ' + routeKey);",
            "        }",
            "",
            "        const values = params || {};",
            "        Object.keys(values).forEach(function (name) {",
            "            template = template.replace('{' + name + '}', String(values[name]));",
            "        });",
            "",
            "        return template;",
            "    }",
            "",
            "    window.SeedAIContract = {",
            "        routes: routes,",
            "        buildRoute: buildRoute",
            "    };",
            "})(window);",
            "",
        ]
    )

    return "\n".join(lines)


def _render_tests(routes: Dict[str, str]) -> str:
    lines = [
        '"""Auto-generated from backend/api_endpoints.json by backend/sync_api_contract.py."""',
        "",
        "API_ROUTES = {",
    ]

    for key, path in routes.items():
        lines.append(f"    '{key}': '{path}',")

    lines.extend(
        [
            "}",
            "",
            "",
            "def build_route(route_key: str, **params) -> str:",
            "    template = API_ROUTES[route_key]",
            "    for name, value in params.items():",
            "        template = template.replace('{' + name + '}', str(value))",
            "    return template",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    routes = _load_routes()

    FRONTEND_TARGET.write_text(_render_frontend(routes), encoding="utf-8")
    TESTS_TARGET.write_text(_render_tests(routes), encoding="utf-8")

    print(f"Synced {len(routes)} routes")
    print(f"- {FRONTEND_TARGET}")
    print(f"- {TESTS_TARGET}")


if __name__ == "__main__":
    main()
