"""Run as a stdio MCP regression script for the private full-page catalogue."""
import base64
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter

base = Path(__file__).resolve().parents[1]
catalogue = json.loads((base / "references/landing-page-catalog.json").read_text())
metrics = []

with subprocess.Popen([sys.executable, "-B", str(base / "scripts/server.py")],
                      stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True) as process:
    def rpc(method, params):
        started = perf_counter()
        process.stdin.write(json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}) + "\n")
        process.stdin.flush()
        line = process.stdout.readline()
        metrics.append({"method": params.get("name", method), "ms": round(1000 * (perf_counter() - started), 2),
                        "responseBytes": len(line.encode())})
        return json.loads(line)["result"]

    def call(name, error=None, **arguments):
        result = rpc("tools/call", {"name": name, "arguments": arguments})
        if error:
            assert result.get("isError") and error in result["content"][0]["text"], result
            return None
        assert not result.get("isError"), result
        return result

    def image(result):
        payload = base64.b64decode(result["content"][1]["data"], validate=True)
        assert payload.startswith(b"\xff\xd8") and payload.endswith(b"\xff\xd9")
        return payload

    assert rpc("initialize", {"protocolVersion": "2025-11-25"})["serverInfo"]["version"] == "2.5.0"
    assert len(rpc("tools/list", {})["tools"]) == 15
    assert len(catalogue) == len({row["sourceSha256"] for row in catalogue}) == 15
    catalogue_ids = []
    for offset in (0, 5, 10):
        page = call("search_patterns", query="landing page", fullPageOnly=True, offset=offset)["structuredContent"]
        assert page["nextOffset"] == (offset + 5 if offset < 10 else None)
        catalogue_ids.extend(row["id"] for row in page["matches"])
    assert set(catalogue_ids) == {row["id"] for row in catalogue}
    for page in catalogue:
        id = page["id"]
        results = call("search_patterns", query=id, category="Landing-page")["structuredContent"]
        assert results["matches"][0]["id"] == id, results
        assert results["matches"][0]["previewAvailable"]
        detail = call("read_pattern", id=id)
        assert detail["structuredContent"]["rights"].startswith("private-reference-only")
        image(detail)
        for section in page["sections"]:
            crop = call("read_pattern", id=id, sectionId=section["id"])
            assert crop["structuredContent"]["section"] == section
            image(crop)

    def plan(goal, **options):
        return call("plan_design", platform="web", stack="generic", goal=goal, audience="Teams",
                    priority="editorial", **options)["structuredContent"]

    landing = plan("Crée une landing page pour un outil de documentation destiné aux développeurs")
    assert landing["initialResearch"]["matches"][0]["id"] == "landing-mintlify", landing["initialResearch"]
    assert landing["landingResearch"]["requiredSections"] == ["hero", "features", "conversion"]
    assert landing["designContract"]["schemaVersion"] == 1
    workflow = landing["workflowId"]
    id = "landing-mintlify"
    call("read_pattern", id=id, workflowId=workflow, sectionId="hero", error="Open the full landing page")
    image(call("read_pattern", id=id, workflowId=workflow))
    sections = ["hero", "features", "conversion"]
    decisions = [{"id": id, "sectionId": section, "region": section, "visibleProperties": observation,
                  "adaptation": decision, "renderTarget": "#" + section, "productFeature": feature}
                 for section, observation, decision, feature in [
        ("hero", "Title left and product preview right", "Show a draft and its published result", "Instant preview"),
        ("features", "Feature tiles with individual demos", "Use one example per publishing workflow", "Versioned guides"),
        ("conversion", "Closing action first", "Link to a working example before setup", "Demo access")]]
    direction = {"workflowId": workflow, "direction": "Editorial and demonstration-led",
                 "productQuery": "developer documentation SaaS", "visualSignature": "Offset product preview",
                 "primaryAction": "Open demo", "copySample": "See your guide change as you type."}
    call("choose_design_direction", **direction, referenceDecisions=decisions, error="Open the landing section")
    for section in sections:
        image(call("read_pattern", id=id, workflowId=workflow, sectionId=section))
    call("choose_design_direction", **direction, referenceDecisions=decisions[:2], error="Use one opened full landing page")
    for skill in ("frontend-design", "ui-ux-pro-max", "taste-skill"):
        call("read_design_skill", workflowId=workflow, skill=skill)
    contract = call("choose_design_direction", **direction, referenceDecisions=decisions)["structuredContent"]["designContract"]
    assert [row["productFeature"] for row in contract["composition"]] == ["Instant preview", "Versioned guides", "Demo access"]
    assert "colors" in call("get_design_assets", workflowId=workflow)["structuredContent"]["tokens"]
    assert plan("Retouche le CTA sur cette landing page", taskMode="edit")["landingResearch"] is None
    assert call("search_patterns", query="landing-mintlify", platform="ios")["structuredContent"]["status"] == "empty"
    call("plan_design", error="Style memory is disabled", reuseProjectStyle=True, platform="web", goal="Example",
         audience="Teams", priority="editorial")
    assert "animateSequence" in call("get_design_workflow", task="motion", platform="web")["structuredContent"]["motionExample"]["content"]
    assert "motionExample" not in call("get_design_workflow", task="motion", platform="ios")["structuredContent"]
    process.stdin.close()
    assert process.wait(timeout=10) == 0

if len(sys.argv) == 2:
    Path(sys.argv[1]).write_text(json.dumps(metrics, indent=2) + "\n")
print(f"PASS: 15 ranked pages, 60 JPEG responses, direction gate, component and motion contracts ({len(metrics)} MCP calls)")
