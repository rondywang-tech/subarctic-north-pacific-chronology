#!/usr/bin/env python3
import hashlib
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from output_discovery import OutputDiscoveryError, discover_expected_scientific_out


cases = []
with tempfile.TemporaryDirectory(prefix="appledouble_smoke_") as td:
    root = Path(td)
    def reset(names):
        for p in root.iterdir():
            p.unlink()
        for name in names:
            (root / name).write_bytes(b"test\n")

    reset(["foo.out", "._foo.out"])
    out, sidecars = discover_expected_scientific_out(root, "foo.out")
    cases.append(("case1_real_plus_sidecar", out.name == "foo.out" and len(sidecars) == 1,
                  "one scientific output; sidecar classified as filesystem metadata"))

    reset(["._foo.out"])
    try:
        discover_expected_scientific_out(root, "foo.out")
        ok = False
    except OutputDiscoveryError as exc:
        ok = "missing expected" in str(exc)
    cases.append(("case2_sidecar_only", ok, "missing scientific output raises STOP"))

    reset(["foo.out", "bar.out", "._foo.out"])
    try:
        discover_expected_scientific_out(root, "foo.out")
        ok = False
    except OutputDiscoveryError as exc:
        ok = "additional real" in str(exc)
    cases.append(("case3_extra_real_output", ok, "additional non-sidecar output raises STOP"))

    reset(["foo.out", ".DS_Store", "._foo.out"])
    out, sidecars = discover_expected_scientific_out(root, "foo.out")
    cases.append(("case4_metadata_files", out.name == "foo.out" and len(sidecars) == 1,
                  "expected output identified; metadata excluded"))

if not all(x[1] for x in cases):
    raise SystemExit("OUTPUT_DISCOVERY_SMOKE_TEST_FAIL")

ts = datetime.now(timezone.utc).isoformat()
lines = ["# AppleDouble output-discovery smoke test — 2026-08-12", "",
         f"**Timestamp:** {ts}  ", "**Bacon calls:** 0  ",
         "`APPLEDOUBLE_OUTPUT_DISCOVERY_SMOKE_TEST = PASS`", "",
         "| Case | Result | Evidence |", "|---|---|---|"]
for name, ok, note in cases:
    lines.append(f"| {name} | {'PASS' if ok else 'FAIL'} | {note} |")
lines += ["", "The test uses manifest-expected output discovery. Dot-prefixed AppleDouble files and `.DS_Store` are non-scientific metadata; a second real `.out` remains a hard stop.", ""]
Path("APPLEDOUBLE_OUTPUT_DISCOVERY_SMOKE_TEST_2026-08-12.md").write_text("\n".join(lines), encoding="utf-8")
print("OUTPUT_DISCOVERY_SMOKE_TEST_PASS")
