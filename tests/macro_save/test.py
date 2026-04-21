"""Test runner for macro_save feature. Zero external dependencies."""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

# Ensure project root is on sys.path for absolute imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from vditto.macro_save import detect_macro, make_filename, save_markdown, split_text

TEST_DIR = Path(__file__).resolve().parent


def load_json(filename: str) -> dict:
    with open(TEST_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)


def setup_env(config: dict) -> dict[str, Path]:
    """Create temp directories from test_env_config.json."""
    env = {}
    tmp_root = tempfile.mkdtemp(prefix="vditto_test_")
    env["_root"] = Path(tmp_root)

    for name, cfg in config.get("temp_dirs", {}).items():
        if cfg.get("auto_create", False):
            p = env["_root"] / name
            p.mkdir(parents=True, exist_ok=True)
            env[name] = p
        elif cfg.get("base") and cfg.get("subpath"):
            # Don't create - test should trigger auto-create
            env[name] = env["_root"] / name / cfg["subpath"]

    return env


def teardown_env(env: dict) -> None:
    """Remove all temp directories."""
    root = env.get("_root")
    if root and root.exists():
        shutil.rmtree(root, ignore_errors=True)


# ── Test runners per function group ──────────────────────────────────

def run_detect_macro(tc: dict, tc_name: str) -> tuple[bool, str]:
    text = tc["input"]["text"]
    mode, name, clean = detect_macro(text)
    expected = tc["expected_output"]["result"]

    if tc["expected_output"].get("should_reject"):
        return False, f"Expected rejection but got mode={mode}, name={name}, clean={clean!r}"

    ok = True
    msgs = []

    # Check mode
    exp_mode = expected.get("mode", "O")  # Default to O for backward compatibility
    if mode != exp_mode:
        ok = False
        msgs.append(f"mode: expected {exp_mode!r}, got {mode!r}")

    # Check name
    exp_name = expected["name"]
    if name != exp_name:
        ok = False
        msgs.append(f"name: expected {exp_name!r}, got {name!r}")

    # Check clean_text
    exp_clean = expected["clean_text"]
    if clean != exp_clean:
        ok = False
        msgs.append(f"clean_text: expected {exp_clean!r}, got {clean!r}")

    return ok, "; ".join(msgs)


def run_make_filename(tc: dict, tc_name: str) -> tuple[bool, str]:
    name_input = tc["input"]["name"]
    result = make_filename(name_input)
    expected = tc["expected_output"]["result"]

    if "matches_pattern" in expected:
        pattern = expected["matches_pattern"]
        if re.match(pattern, result):
            return True, f"matches pattern: {result}"
        return False, f"filename {result!r} does not match pattern {pattern!r}"

    exp_filename = expected["filename"]
    if result == exp_filename:
        return True, f"filename: {result}"
    return False, f"expected {exp_filename!r}, got {result!r}"


def run_save_markdown(tc: dict, tc_name: str, env: dict) -> tuple[bool, str]:
    text = tc["input"]["text"]
    name = tc["input"]["name"]
    dir_key = tc["input"].get("save_dir_env", "temp_dir")
    mode = tc["input"].get("mode", "A")  # Default to append mode

    save_dir = env.get(dir_key)
    if save_dir is None:
        return False, f"env key {dir_key!r} not found"

    # Pre-create file if testing overwrite or append
    pre_content = tc["input"].get("pre_existing_content")
    if pre_content:
        save_dir.mkdir(parents=True, exist_ok=True)
        if mode == "C":
            # For collection mode, pre-create in the collection directory
            collection_dir = save_dir / (name or "unnamed")
            collection_dir.mkdir(parents=True, exist_ok=True)
            # Create a pre-existing file in the collection
            pre_file = collection_dir / "20240101-120000.md"
            pre_file.write_text(pre_content, encoding="utf-8")
        else:
            (save_dir / f"{name}.md").write_text(pre_content, encoding="utf-8")

    try:
        saved_path = save_markdown(text, name, save_dir, mode)
    except Exception as e:
        if tc["expected_output"].get("should_reject"):
            return True, f"correctly rejected: {e}"
        return False, f"unexpected exception: {e}"

    expected = tc["expected_output"]["result"]

    # For collection mode, check parent directory and filename pattern
    if mode == "C":
        # Check parent directory name
        exp_parent = expected.get("parent_dirname", name or "unnamed")
        if saved_path.parent.name != exp_parent:
            return False, f"parent dir: expected {exp_parent!r}, got {saved_path.parent.name!r}"

        # Check filename pattern
        pattern = expected.get("matches_pattern", r"^\d{8}-\d{6}\.md$")
        if not re.match(pattern, saved_path.name):
            return False, f"filename {saved_path.name!r} does not match pattern {pattern!r}"
    else:
        # For non-collection modes, check exact filename
        exp_filename = expected["filename"]
        if saved_path.name != exp_filename:
            return False, f"filename: expected {exp_filename!r}, got {saved_path.name!r}"

    # Verify content
    actual = saved_path.read_text(encoding="utf-8")
    if actual != expected["file_content"]:
        return False, f"content: expected {expected['file_content']!r}, got {actual!r}"

    return True, f"saved to {saved_path}"


def run_split_text(tc: dict, tc_name: str) -> tuple[bool, str]:
    text = tc["input"]["text"]
    max_len = tc["input"].get("max_len", 20000)
    result = split_text(text, max_len)
    expected = tc["expected_output"]["result"]

    if "chunk_count" in expected:
        if len(result) == expected["chunk_count"]:
            # Also verify no chunk exceeds max_len
            over = [i for i, c in enumerate(result) if len(c) > max_len]
            if over:
                return False, f"chunks {over} exceed max_len={max_len}"
            return True, f"{len(result)} chunks, all <= {max_len}"
        return False, f"expected {expected['chunk_count']} chunks, got {len(result)}"

    if "chunks" in expected:
        if result == expected["chunks"]:
            return True, f"{len(result)} chunks match"
        return False, f"expected {expected['chunks']!r}, got {result!r}"

    return False, "No valid expected output field"


# ── Main runner ──────────────────────────────────────────────────────

def main() -> None:
    cases = load_json("test_cases.json")
    env_config = load_json("test_env_config.json")

    total, passed, failed = 0, 0, 0
    failures: list[str] = []

    for tc_name, tc in cases.items():
        total += 1

        # Route to correct test runner
        if tc_name.startswith("detect_macro"):
            ok, msg = run_detect_macro(tc, tc_name)
        elif tc_name.startswith("make_filename"):
            ok, msg = run_make_filename(tc, tc_name)
        elif tc_name.startswith("save_markdown"):
            env = setup_env(env_config)
            try:
                ok, msg = run_save_markdown(tc, tc_name, env)
            finally:
                teardown_env(env)
        elif tc_name.startswith("split_text"):
            ok, msg = run_split_text(tc, tc_name)
        else:
            ok, msg = False, "Unknown test prefix"

        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {tc_name}: {msg}")

        if ok:
            passed += 1
        else:
            failed += 1
            failures.append(tc_name)

    print(f"\n{'='*50}")
    print(f"Total: {total}, Passed: {passed}, Failed: {failed}")
    if failures:
        print(f"Failed cases: {', '.join(failures)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
