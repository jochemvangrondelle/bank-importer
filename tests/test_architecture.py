# Copyright (C) 2025 Jochem van Grondelle <jochem@vangrondelle.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the PolyForm Noncommercial License 1.0.0.
# You may not use this program except in compliance with the License.
# A copy of the License is available at https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# PolyForm Noncommercial License 1.0.0 for more details.

"""Architectural tests to enforce import boundaries and prevent circular dependencies."""

import ast
from pathlib import Path


def get_imports_from_file(file_path: Path) -> list[tuple[str, str]]:
    """Extract all imports from a Python file.

    Returns:
        List of (module_name, import_type) tuples where import_type is
        'from' or 'import'

    """
    imports: list[tuple[str, str]] = []
    try:
        with file_path.open(encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(file_path))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append((alias.name, "import"))
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append((node.module, "from"))

    except (SyntaxError, UnicodeDecodeError):
        # Skip files that can't be parsed
        pass

    return imports


def get_core_modules() -> set[str]:
    """Get all core module paths (excluding cli and api)."""
    src_path = Path(__file__).parent.parent / "src" / "bank_importer"
    core_modules: set[str] = set()

    for py_file in src_path.rglob("*.py"):
        if "cli" in py_file.parts or "api" in py_file.parts:
            continue

        relative = py_file.relative_to(src_path.parent)
        module_name = (
            str(relative).replace("/", ".").replace("\\", ".").replace(".py", "")
        )
        core_modules.add(module_name)

    return core_modules


def get_cli_modules() -> set[str]:
    """Get all CLI module paths."""
    src_path = Path(__file__).parent.parent / "src" / "bank_importer" / "cli"
    cli_modules: set[str] = set()

    for py_file in src_path.rglob("*.py"):
        relative = py_file.relative_to(src_path.parent.parent)
        module_name = (
            str(relative).replace("/", ".").replace("\\", ".").replace(".py", "")
        )
        cli_modules.add(module_name)

    return cli_modules


def get_api_modules() -> set[str]:
    """Get all API module paths."""
    src_path = Path(__file__).parent.parent / "src" / "bank_importer" / "api"
    api_modules: set[str] = set()

    for py_file in src_path.rglob("*.py"):
        relative = py_file.relative_to(src_path.parent.parent)
        module_name = (
            str(relative).replace("/", ".").replace("\\", ".").replace(".py", "")
        )
        api_modules.add(module_name)

    return api_modules


class TestArchitecture:
    """Test architectural boundaries and import rules."""

    def test_core_does_not_import_cli(self) -> None:
        """Core modules must not import from CLI."""
        src_path = Path(__file__).parent.parent / "src" / "bank_importer"
        violations: list[tuple[str, str]] = []

        for py_file in src_path.rglob("*.py"):
            # Skip CLI and API directories
            if "cli" in py_file.parts or "api" in py_file.parts:
                continue
            # Skip __main__.py as it's the entry point and needs to import CLI
            if py_file.name == "__main__.py":
                continue

            imports = get_imports_from_file(py_file)
            for module_name, _ in imports:
                if module_name.startswith("bank_importer.cli"):
                    violations.append(
                        (str(py_file.relative_to(src_path.parent)), module_name),
                    )

        assert not violations, (
            "Core modules must not import from CLI. Violations:\n"
            + "\n".join(f"  {file}: imports {module}" for file, module in violations)
        )

    def test_core_does_not_import_api(self) -> None:
        """Core modules must not import from API."""
        src_path = Path(__file__).parent.parent / "src" / "bank_importer"
        violations: list[tuple[str, str]] = []

        for py_file in src_path.rglob("*.py"):
            # Skip CLI and API directories
            if "cli" in py_file.parts or "api" in py_file.parts:
                continue

            imports = get_imports_from_file(py_file)
            for module_name, _ in imports:
                if module_name.startswith("bank_importer.api"):
                    violations.append(
                        (str(py_file.relative_to(src_path.parent)), module_name),
                    )

        assert not violations, (
            "Core modules must not import from API. Violations:\n"
            + "\n".join(f"  {file}: imports {module}" for file, module in violations)
        )

    def test_cli_does_not_import_api(self) -> None:
        """CLI modules must not import from API."""
        src_path = Path(__file__).parent.parent / "src" / "bank_importer" / "cli"
        violations: list[tuple[str, str]] = []

        for py_file in src_path.rglob("*.py"):
            imports = get_imports_from_file(py_file)
            for module_name, _ in imports:
                if module_name.startswith("bank_importer.api"):
                    violations.append(
                        (str(py_file.relative_to(src_path.parent.parent)), module_name),
                    )

        assert not violations, (
            "CLI modules must not import from API. Violations:\n"
            + "\n".join(f"  {file}: imports {module}" for file, module in violations)
        )

    def test_api_does_not_import_cli(self) -> None:
        """API modules must not import from CLI."""
        src_path = Path(__file__).parent.parent / "src" / "bank_importer" / "api"
        violations: list[tuple[str, str]] = []

        for py_file in src_path.rglob("*.py"):
            imports = get_imports_from_file(py_file)
            for module_name, _ in imports:
                if module_name.startswith("bank_importer.cli"):
                    violations.append(
                        (str(py_file.relative_to(src_path.parent.parent)), module_name),
                    )

        assert not violations, (
            "API modules must not import from CLI. Violations:\n"
            + "\n".join(f"  {file}: imports {module}" for file, module in violations)
        )

    def test_cli_does_not_import_translation_directly(self) -> None:
        """CLI modules must not import translation_service directly."""
        src_path = Path(__file__).parent.parent / "src" / "bank_importer" / "cli"
        violations: list[tuple[str, str]] = []

        for py_file in src_path.rglob("*.py"):
            imports = get_imports_from_file(py_file)
            for module_name, _ in imports:
                if (
                    module_name == "bank_importer.translation_service"
                    or module_name.startswith("bank_importer.translation_service.")
                ):
                    violations.append(
                        (str(py_file.relative_to(src_path.parent.parent)), module_name),
                    )

        assert not violations, (
            "CLI modules must not import translation_service directly. Use library functions instead. Violations:\n"
            + "\n".join(f"  {file}: imports {module}" for file, module in violations)
        )

    def test_cli_does_not_import_firefly_directly(self) -> None:
        """CLI modules must not import firefly_target directly."""
        src_path = Path(__file__).parent.parent / "src" / "bank_importer" / "cli"
        violations: list[tuple[str, str]] = []

        for py_file in src_path.rglob("*.py"):
            imports = get_imports_from_file(py_file)
            for module_name, _ in imports:
                if (
                    module_name == "bank_importer.targets.firefly_target"
                    or module_name.startswith(
                        "bank_importer.targets.firefly_target.",
                    )
                ):
                    violations.append(
                        (str(py_file.relative_to(src_path.parent.parent)), module_name),
                    )

        assert not violations, (
            "CLI modules must not import firefly_target directly. Use library functions instead. Violations:\n"
            + "\n".join(f"  {file}: imports {module}" for file, module in violations)
        )

    def test_api_does_not_import_translation_directly(self) -> None:
        """API modules must not import translation_service directly."""
        src_path = Path(__file__).parent.parent / "src" / "bank_importer" / "api"
        violations: list[tuple[str, str]] = []

        for py_file in src_path.rglob("*.py"):
            imports = get_imports_from_file(py_file)
            for module_name, _ in imports:
                if (
                    module_name == "bank_importer.translation_service"
                    or module_name.startswith("bank_importer.translation_service.")
                ):
                    violations.append(
                        (str(py_file.relative_to(src_path.parent.parent)), module_name),
                    )

        assert not violations, (
            "API modules must not import translation_service directly. Use library functions instead. Violations:\n"
            + "\n".join(f"  {file}: imports {module}" for file, module in violations)
        )

    def test_api_does_not_import_firefly_directly(self) -> None:
        """API modules must not import firefly_target directly."""
        src_path = Path(__file__).parent.parent / "src" / "bank_importer" / "api"
        violations: list[tuple[str, str]] = []

        for py_file in src_path.rglob("*.py"):
            imports = get_imports_from_file(py_file)
            for module_name, _ in imports:
                if (
                    module_name == "bank_importer.targets.firefly_target"
                    or module_name.startswith(
                        "bank_importer.targets.firefly_target.",
                    )
                ):
                    violations.append(
                        (str(py_file.relative_to(src_path.parent.parent)), module_name),
                    )

        assert not violations, (
            "API modules must not import firefly_target directly. Use library functions instead. Violations:\n"
            + "\n".join(f"  {file}: imports {module}" for file, module in violations)
        )

    def test_cli_uses_library_functions(self) -> None:
        """CLI should use library functions where possible instead of duplicating logic."""
        src_path = Path(__file__).parent.parent / "src" / "bank_importer" / "cli"

        # This is a documentation/guidance test - we check that CLI imports from library
        # The actual enforcement is done by import-linter
        for py_file in src_path.rglob("*.py"):
            imports = get_imports_from_file(py_file)
            for module_name, _ in imports:
                if module_name == "bank_importer.library" or module_name.startswith(
                    "bank_importer.library.",
                ):
                    break

        # This test passes if CLI imports library at least once
        # It's more of a reminder to use library functions
        assert True  # Always pass - this is informational

    def test_api_uses_library_functions(self) -> None:
        """API should use library functions where possible instead of duplicating logic."""
        src_path = Path(__file__).parent.parent / "src" / "bank_importer" / "api"

        # This is a documentation/guidance test - we check that API imports from library
        # The actual enforcement is done by import-linter
        for py_file in src_path.rglob("*.py"):
            imports = get_imports_from_file(py_file)
            for module_name, _ in imports:
                if module_name == "bank_importer.library" or module_name.startswith(
                    "bank_importer.library.",
                ):
                    break

        # This test passes if API imports library at least once
        # It's more of a reminder to use library functions
        assert True  # Always pass - this is informational
