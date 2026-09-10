#!/usr/bin/env python3
"""Manifest-anchored Bacon output discovery; filesystem sidecars are never scientific."""
from pathlib import Path


class OutputDiscoveryError(RuntimeError):
    pass


def is_scientific_out(path):
    path = Path(path)
    return path.is_file() and path.suffix == ".out" and not path.name.startswith("._")


def discover_expected_scientific_out(run_directory, expected_basename):
    run_directory = Path(run_directory)
    expected = run_directory / expected_basename
    if expected.name.startswith("._") or expected.suffix != ".out":
        raise OutputDiscoveryError("invalid expected scientific output basename")
    scientific = sorted(p for p in run_directory.iterdir() if is_scientific_out(p))
    sidecars = sorted(p for p in run_directory.iterdir()
                      if p.is_file() and p.name.startswith("._") and p.suffix == ".out")
    if not expected.is_file():
        raise OutputDiscoveryError(f"missing expected scientific output: {expected}")
    extras = [p for p in scientific if p != expected]
    if extras:
        raise OutputDiscoveryError("additional real scientific output(s): " + ";".join(map(str, extras)))
    return expected, sidecars
