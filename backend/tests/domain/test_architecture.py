"""Dependency rule: the domain imports nothing from frameworks or outer layers."""

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
FORBIDDEN_IN_DOMAIN = (
    "fastapi",
    "starlette",
    "sqlalchemy",
    "pydantic",
    "itsdangerous",
    "src.api",
    "src.config",
    "src.infra",
)
FORBIDDEN_IN_INFRA = ("fastapi", "starlette", "src.api", "src.config.dependency")


def imports_of(path: Path) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def violations(layer: str, forbidden: tuple[str, ...]) -> list[str]:
    return [
        f"{f.relative_to(SRC)} imports {name}"
        for f in sorted((SRC / layer).rglob("*.py"))
        for name in imports_of(f)
        if any(name == p or name.startswith(p + ".") for p in forbidden)
    ]


@pytest.mark.parametrize(
    ("layer", "forbidden"),
    [("domain", FORBIDDEN_IN_DOMAIN), ("infra", FORBIDDEN_IN_INFRA)],
)
def test_layer_dependencies(layer: str, forbidden: tuple[str, ...]) -> None:
    assert violations(layer, forbidden) == []
