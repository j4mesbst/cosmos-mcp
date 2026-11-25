"""Replay the packaged plugin against a locally running Trait d’Union benchmark."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
app = Path(sys.argv[1]).resolve()
audit_config = Path(sys.argv[2]).resolve()
out = Path(sys.argv[3]).resolve()
proc = subprocess.Popen(
    [sys.executable, "-B", str(root / "scripts/server.py")],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
    env={**os.environ, "COSMOS_PROJECT_ROOT": str(app)},
)

def rpc(method, params):
    proc.stdin.write(json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}) + "\n")
    proc.stdin.flush()
    return json.loads(proc.stdout.readline())["result"]

def call(name, error=None, **arguments):
    blocks = rpc("tools/call", {"name":name,"arguments":arguments})
    if error:
        assert blocks.get("isError") and error in blocks["content"][0]["text"], blocks["content"][0]["text"][:500]
        return None
    assert not blocks.get("isError"), blocks["content"][0]["text"][:900]
    return blocks["structuredContent"]

def evidence(skills):
    properties = {
        "frontend-design": ("Composed the title and a blue selection on a grid.", "src/main.jsx", 'className="selected-text"'),
        "taste-skill": ("Use a specific positioning line and direct action.", "src/main.jsx", "Sites et outils numériques pour les marques indépendantes."),
        "ui-ux-pro-max": ("Apply a generated primary color token.", "src/cosmos-tokens.css", "--cosmos-primary:"),
        "heroui": ("Render the selected components from HeroUI.", "src/main.jsx", "from '@heroui/react'"),
        "thesvg": ("Render locally verified brand assets.", "src/main.jsx", "data-cosmos-logo"),
        "web-accessibility": ("Label the modal close action.", "src/main.jsx", "Fermer le projet"),
        "web-design-guidelines": ("Provide a skip link.", "src/main.jsx", "Aller au contenu"),
        "impeccable": ("Keep the collaboration fragment distinct from real integrations.", "src/main.jsx", 'data-fragment="collaboration"'),
        "superpowers": ("Audit the full keyboard flow.", ".cosmos/review/browser-report.json", '"primaryFlow": true'),
    }
    return [{"skill":skill,"path":properties[skill][1],"excerpt":properties[skill][2],"decision":properties[skill][0]}
            for skill in skills]

def run():
    identity = rpc("initialize", {"protocolVersion":"2025-11-25"})["serverInfo"]
    assert identity["version"] == "2.4.1", identity
    slugs = ["figma","notion","vercel"]
    assert call("search_brand_logos",query="Figma")["matches"][0]["slug"] == "figma"
    project_plan = {
        "goal":"Landing page Trait d’Union, studio de design web indépendant",
        "audience":"marques indépendantes","priority":"editorial","platform":"web","screenType":"Landing-page",
        "brandLogos":slugs,"briefReferences":[".cosmos/brief/reference-1.png",".cosmos/brief/reference-2.png"],
    }
    plan = call("plan_design", **project_plan)
    assert plan["stack"] == "heroui"
    workflow = {"workflowId":plan["workflowId"]}
    skills = plan["requiredSkills"]
    assert "heroui" in skills and "thesvg" in skills and "shadcn" not in skills
    source_notes = [
        {"id":"brief-001","region":"Central selected title","visibleProperties":"Large black headline over pale blue selection with handles.",
         "adaptation":"Use the original two-line Trait d’Union headline with selected blue second line.","renderTarget":".selected-text"},
        {"id":"brief-002","region":"Work-in-progress canvas","visibleProperties":"Quiet dotted grid with small detached work fragments.",
         "adaptation":"Place original studio notes, tooling and a wireframe on the perimeter of the canvas.","renderTarget":"[data-fragment=collaboration]"},
    ]
    skill_proof = evidence(skills)
    skill_plan = [{"skill":item["skill"],"application":item["decision"],
                   "verification":f'Check the rendered result and {item["path"]}.'} for item in skill_proof]
    visual_rules = {
        "frontend-design":{"selector":".selected-text","property":"font-size","operator":"min-px","value":"40"},
        "impeccable":{"selector":".selected-text","property":"background-color","operator":"equals","value":"rgba(203, 224, 255, 0.72)"},
    }
    for row in skill_plan:
        if row["skill"] in visual_rules:
            row["renderCheck"] = visual_rules[row["skill"]]
    request = {"direction":"Atelier web français sur fond blanc et quadrillage fin",
               "productQuery":"creative web design studio","visualSignature":"Grand texte sélectionné en bleu",
               "primaryAction":"Voir les projets","copySample":"Studio web indépendant",
               "referenceDecisions":source_notes,"skillPlan":skill_plan}
    call("choose_design_direction",error="Open an offered image",**workflow,**request)
    for item in plan["briefReferences"]:
        opened = call("read_pattern",id=item["id"],**workflow)
        assert opened["status"] == "opened"
    call("choose_design_direction",error="Read the full instructions",**workflow,**request)
    guides = [call("read_design_skill",skill=skill,**workflow) for skill in skills]
    call("choose_design_direction",error="distinct application",**workflow,**{**request,"skillPlan":skill_plan[:-1]})
    no_measurement = [{key:value for key,value in item.items() if key != "renderCheck"} for item in skill_plan]
    call("choose_design_direction",error="measurable renderCheck",**workflow,**{**request,"skillPlan":no_measurement})
    direction = call("choose_design_direction",**workflow,**request)
    config = call("get_design_assets",**workflow)
    assert config["component"]["version"] == "3.2.8"
    (app / config["tokens"]["file"]["path"]).write_text(config["tokens"]["file"]["content"])
    paths = ["package.json", "index.html", *(
        str(file.relative_to(app)) for file in sorted((app / "src").rglob("*"))
        if file.is_file() and file.suffix in {".js",".jsx",".ts",".tsx",".css",".mjs"}
    )]
    implementation = {"artifacts":paths,"entry":"src/main.jsx",
                      "implementation":"HeroUI controls and cards, plus three local theSVG marks."}
    call("record_design_implementation",error="Retrieve every brand logo",**workflow,**implementation)
    logos = {}
    for slug in slugs:
        asset = call("read_brand_logo",slug=slug,**workflow)
        path = app / asset["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(asset["svg"].encode())
        assert hashlib.sha256(path.read_bytes()).hexdigest() == asset["sha256"]
        logos[slug] = asset["sha256"]
    path = app / "src/main.jsx"
    original = path.read_bytes()
    try:
        path.write_bytes(original + b"\nconst raw = () => <button>Native</button>;\n")
        call("record_design_implementation",error="Use HeroUI for <button>",**workflow,**implementation)
    finally:
        path.write_bytes(original)
    path = app / "public/cosmos-logos/figma.svg"
    original = path.read_bytes()
    try:
        path.write_bytes(original + b"\n")
        call("record_design_implementation",error="exact theSVG bytes",**workflow,**implementation)
    finally:
        path.write_bytes(original)
    source_proof = call("record_design_implementation",**workflow,**implementation)["sourceVerification"]
    assert source_proof["theSVG"] == logos
    scoped_config = app / ".cosmos/benchmark-audit.json"
    scoped_config.write_bytes(audit_config.read_bytes())
    audit_args = {**workflow,"auditConfig":str(scoped_config.relative_to(app))}
    config_data = json.loads(scoped_config.read_bytes())
    dummy = app / ".cosmos/benchmark-checklist-only.json"
    dummy.write_text(json.dumps({**config_data,"steps":[{"action":"visible","selector":"h1"}]}))
    try:
        call("run_design_audit",error="no proven keyboard transition",
             **{**audit_args,"auditConfig":str(dummy.relative_to(app))})
    finally:
        dummy.unlink()
    css = next((app / "dist/assets").glob("*.css"))
    css_bytes = css.read_bytes()
    try:
        css.write_bytes(css_bytes + b"\n.selected-text { background-color: transparent !important; }\n")
        call("run_design_audit",error="impeccable background-color",**audit_args)
    finally:
        css.write_bytes(css_bytes)
    audit = call("run_design_audit",**audit_args)
    mobile = ".cosmos/review/render-390.png"
    desktop = ".cosmos/review/render-1440.png"
    linked = call("open_design_render", screenshots=[mobile,desktop], **workflow,
                  comparisonPairs=[{"id":row["id"],"screenshot":desktop} for row in source_notes])
    browser_report = ".cosmos/review/browser-report.json"
    review = {**workflow, "browserReport":browser_report,
              "renderEvidence":"Chromium 390, 768, 1440 plus paired brief references.",
              "visualCorrection":"Kept decorative elements at the perimeter of the central headline.",
              "checks":[{"check":key,"status":"pass","evidence":"Executed browser audit."}
                        for key in ("render","responsive","keyboard","primary-flow","reduced-motion")],
              "visualResults":[{"decisionIndex":index,"screenshot":desktop,"status":"pass",
                                "observation":row["adaptation"]} for index,row in enumerate(source_notes,1)],
              "skillEvidence":skill_proof}
    report_path = app / browser_report
    original = report_path.read_bytes()
    assert hashlib.sha256(original).hexdigest() == audit["sha256"]
    try:
        report_path.write_bytes(original + b" ")
        call("record_design_review",error="browser report changed",**review)
    finally:
        report_path.write_bytes(original)
    fake = app / ".cosmos/proof-with-no-design.json"
    examples = [{"skill":item["skill"],"path":".cosmos/proof-with-no-design.json",
                 "decision":f"Generic claim {index}", "excerpt":f"Claim {index} without evidence"}
                for index,item in enumerate(skill_proof,1)]
    fake.write_text(json.dumps([row["excerpt"] for row in examples]))
    try:
        call("record_design_review",error="registered implementation source",**{**review,"skillEvidence":examples})
    finally:
        fake.unlink()
    completed = call("record_design_review",**review)
    assert completed["stage"] == "complete" and completed["referenceStatus"] == "compared"
    out.write_text(json.dumps({"server":identity,"direction":direction,"review":completed,
                               "skills":[{"skill":guide["skill"],"sha256":guide["sha256"]} for guide in guides],
                               "pairs":linked["comparisons"],
                               "negativeChecks":["missing references","missing skills","incomplete plan","unretrieved marks",
                                                 "native button","modified SVG bytes","missing visual measurements","no interaction",
                                                 "removed visual styling","tampered browser report","fabricated skill claims"]},
                              ensure_ascii=False,indent=2))
    print("Cosmos HeroUI + theSVG benchmark passed")

try:
    run()
finally:
    proc.stdin.close()
    proc.wait(timeout=10)
