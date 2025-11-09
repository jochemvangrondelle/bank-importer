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

"""Pytest configuration for profiling tests.

This module provides pytest fixtures and hooks for profiling test execution.
It integrates with cProfile, pyinstrument, and other profiling tools.

Usage:
    # Profile all tests
    pytest --profile

    # Profile specific test file
    pytest tests/banks/test_krungsri_pdf.py --profile

    # Profile with pyinstrument (flamegraph)
    pytest --profile --profile-tool=pyinstrument

    # Profile with cProfile
    pytest --profile --profile-tool=cprofile
"""

import cProfile
import pstats
from pathlib import Path
from typing import Any

import pytest


def pytest_addoption(parser: Any) -> None:
    """Add profiling command-line options."""
    parser.addoption(
        "--profile",
        action="store_true",
        default=False,
        help="Enable profiling for tests",
    )
    parser.addoption(
        "--profile-tool",
        action="store",
        default="cprofile",
        choices=["cprofile", "pyinstrument"],
        help="Profiling tool to use (default: cprofile)",
    )
    parser.addoption(
        "--profile-output-dir",
        action="store",
        default="profiles",
        help="Directory for profile output files (default: profiles)",
    )
    parser.addoption(
        "--profile-top-n",
        action="store",
        type=int,
        default=50,
        help="Number of top functions to show in reports (default: 50)",
    )


@pytest.fixture(scope="session", autouse=True)
def setup_profiling(pytestconfig: Any) -> None:
    """Set up profiling infrastructure."""
    if not pytestconfig.getoption("--profile"):
        return

    output_dir = Path(pytestconfig.getoption("--profile-output-dir"))
    output_dir.mkdir(exist_ok=True)
    pytestconfig.profile_output_dir = output_dir  # type: ignore[attr-defined]
    pytestconfig.profile_tool = pytestconfig.getoption("--profile-tool")  # type: ignore[attr-defined]


@pytest.fixture(autouse=True)
def profile_test(request: Any, pytestconfig: Any) -> Any:
    """Profile individual test execution."""
    if not pytestconfig.getoption("--profile"):
        yield
        return

    tool = pytestconfig.getoption("--profile-tool")
    output_dir: Path = pytestconfig.profile_output_dir  # type: ignore[attr-defined]

    # Generate profile filename from test name
    test_name = request.node.name
    test_file = Path(request.node.fspath).stem  # type: ignore[attr-defined]
    profile_file = output_dir / f"{test_file}_{test_name}.prof"

    if tool == "cprofile":
        profiler = cProfile.Profile()
        profiler.enable()
        yield
        profiler.disable()
        profiler.dump_stats(str(profile_file))
    elif tool == "pyinstrument":
        try:
            from pyinstrument import Profiler

            profiler = Profiler()
            profiler.start()
            yield
            profiler.stop()
            html_file = profile_file.with_suffix(".html")
            profiler.output_html(open(html_file, "w"))
        except ImportError:
            pytest.skip("pyinstrument not installed. Run: uv sync --group profiling")
    else:
        yield


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session: Any) -> None:
    """Generate summary report after all tests."""
    if not session.config.getoption("--profile"):
        return

    output_dir: Path = session.config.profile_output_dir  # type: ignore[attr-defined]
    top_n = session.config.getoption("--profile-top-n")

    # Collect all profile files
    profile_files = list(output_dir.glob("*.prof"))
    if not profile_files:
        return

    # Aggregate statistics
    combined_stats = pstats.Stats(str(profile_files[0]))
    for prof_file in profile_files[1:]:
        combined_stats.add(str(prof_file))

    # Generate combined report
    summary_file = output_dir / "summary.txt"
    with summary_file.open("w") as f:
        combined_stats.sort_stats("cumulative")
        combined_stats.print_stats(top_n, file=f)

    combined_stats.sort_stats("cumulative")
    combined_stats.print_stats(top_n)

    # Generate HTML with snakeviz if available
    try:
        import snakeviz

        combined_prof = output_dir / "combined.prof"
        combined_stats.dump_stats(str(combined_prof))
    except ImportError:
        pass
