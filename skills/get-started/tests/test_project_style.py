"""Check explicit activation, per-root isolation and safe local storage."""
from pathlib import Path
from tempfile import TemporaryDirectory
import os
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from project_style import load_style, save_style, STYLE_PATH

def must_fail(operation, expected):
    try:
        operation()
    except ValueError as error:
        assert expected in str(error), str(error)
    else:
        raise AssertionError("Expected failure")

contract = {"direction":"Restrained", "visualSignature":"Aligned product demos",
            "target":{"platform":"web","stack":"generic"}}
tokens = {"colors":{"primary":"#14533c"}}
with TemporaryDirectory() as first, TemporaryDirectory() as second:
    os.environ["COSMOS_PROJECT_ROOT"] = first
    os.environ.pop("COSMOS_ENABLE_STYLE_MEMORY", None)
    must_fail(load_style, "disabled")
    os.environ["COSMOS_ENABLE_STYLE_MEMORY"] = "1"
    assert load_style() is None
    assert save_style(contract, tokens) == STYLE_PATH
    assert load_style()["colors"] == tokens["colors"]
    os.environ["COSMOS_PROJECT_ROOT"] = second
    assert load_style() is None
    target = Path(second) / STYLE_PATH
    target.symlink_to(Path(first) / STYLE_PATH)
    must_fail(load_style, "regular local file")
    save_style({**contract, "direction":"Editorial"}, tokens)
    assert not target.is_symlink() and load_style()["direction"] == "Editorial"
    os.environ["COSMOS_PROJECT_ROOT"] = first
    assert load_style()["direction"] == "Restrained"
print("PASS: opt-in, project isolation, symlink refusal and atomic replacement")
