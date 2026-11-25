"""Cosmos development MCP over stdio. Uses local reference data, bundled scripts, and read-only project verification."""

import base64
import hashlib
import json
import os
import subprocess
import re
import sys
from dataclasses import dataclass, field
from uuid import uuid4
from pathlib import Path

from design_assets import project_file, component_assets, design_tokens, inspect_browser_report, inspect_implementation, inspect_render
from project_style import load_style, save_style

from brand_assets import find_logos, hero_assets, logo_asset, project_ui, verify_brand_assets, verify_heroui_source
from chat_contract import PROFILE, failures as chat_failures, validate_direction as validate_chat_direction
from patterns import REFERENCES, CATALOG, PATTERNS, COUNTS, find, infer_app, normalize, tokens

PROTOCOLS = {"2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05"}

TEXT = {"type": "string", "minLength": 1, "maxLength": 600}
PLATFORM = {"type": "string", "enum": ["web", "ios"]}
COUNT = {"type": "integer", "minimum": 0, "maximum": 1000000}
WORKFLOW_ID = {"type": "string", "maxLength": 32}
REFERENCE_ID = {"type": "string", "pattern": "^(grok-[0-9]{3}|brief-[0-9]{3}|pixlpin-[a-z0-9-]+_[0-9]+|landing-[a-z0-9-]+)$", "maxLength": 96}
LANDING_SECTION = {"type": "string", "enum": ["hero", "features", "conversion"]}
TASK_MODE = {"type": "string", "enum": ["create", "edit", "audit", "motion"]}
REVIEW_CHECKS = {
    "web": ["render", "responsive", "keyboard", "primary-flow", "reduced-motion"],
    "ios": ["render", "build", "voiceover", "dynamic-type", "primary-flow", "reduced-motion"],
}

@dataclass
class DesignSession:
    platform: str
    stack: str
    stage: str = "research"
    reference_platform: str | None = None
    design_mode: str = "inspiration"
    design_profile: str | None = None
    chat_roles: dict = field(default_factory=dict)
    skill_plan: dict = field(default_factory=dict)
    skill_visuals: list = field(default_factory=list)
    audit_sha: str | None = None
    brief_references: dict = field(default_factory=dict)
    brand_slugs: tuple = ()
    logos: dict = field(default_factory=dict)
    logo_exclusion: str | None = None
    decisions: list = field(default_factory=list)
    failed: dict = field(default_factory=dict)
    rejected_renders: dict = field(default_factory=dict)
    comparisons: list = field(default_factory=list)
    reference_limit: str | None = None
    search_count: int = 0
    offered: set = field(default_factory=set)
    opened: set = field(default_factory=set)
    delivered_skills: dict = field(default_factory=dict)
    references: list = field(default_factory=list)
    tokens: dict | None = None
    assets_delivered: bool = False
    copy_sample: str = ""
    implementation: dict | None = None
    reviewed_images: list = field(default_factory=list)
    opened_sections: set = field(default_factory=set)
    landing_candidates: set = field(default_factory=set)
    contract: dict = field(default_factory=dict)


SESSIONS = {}
MAX_SESSIONS = 128


def session(workflow_id, stage=None):
    current = SESSIONS.get(workflow_id)
    if current is None:
        raise ValueError("Unknown workflowId. Call plan_design in this MCP session.")
    if stage is not None and current.stage != stage:
        raise ValueError(f"This action requires stage {stage}. Your workflow is at {current.stage}.")
    return current


def array_of(items, maximum, minimum=0):
    return {"type": "array", "items": items, "minItems": minimum, "maxItems": maximum}


def record(properties):
    return {"type": "object", "properties": properties, "required": list(properties),
            "additionalProperties": False}


FLOW_IDS = {
    "first-conversation": {"title": "Draft a message and wait for a reply", "ids": ["grok-029", "grok-035", "grok-036", "grok-037"]},
    "mention-agent": {"title": "Find, select and use an agent mention", "ids": ["grok-038", "grok-039", "grok-040"]},
    "choose-tools": {"title": "Select tools and reach notification permission", "ids": ["grok-021", "grok-022", "grok-023"]},
}

WORKFLOWS = {
    "design": ["frontend-design", "ui-ux-pro-max", "taste-skill"],
    "implementation": ["ui-ux-pro-max", "web-accessibility", "superpowers"],
    "audit": ["web-design-guidelines", "web-accessibility", "impeccable", "superpowers"],
    "motion": ["impeccable", "taste-skill", "superpowers"],
}

PLAYBOOKS = json.loads((REFERENCES / "skill-playbooks.json").read_text(encoding="utf-8"))
STACK = {"type": "string", "enum": ["generic", "shadcn", "heroui"]}
EXECUTION = (
    "Apply the selected skill instructions in the implementation or review. "
    "When files can be edited, implement the requested artifact. Verify what changed and "
    "report the evidence or the exact check that was unavailable."
)

WEB_REVIEW_ACTIONS = {
    "focusInvisible": "Restore a visible keyboard focus indicator for each affected control and retest with Tab.",
    "contrastFailures": "Increase foreground/background contrast; rerun contrast checks on the affected text and states.",
    "smallTargets": "Increase the hit area or provide sufficient separation; verify pointer use on narrow viewports.",
    "unlabeledFields": "Give each affected field an associated visible label, then verify its accessible name.",
    "missingPageLanguage": "Set a valid lang attribute on the root HTML element and verify the document language.",
    "missingMainLandmark": "Wrap the primary content in a single main landmark and confirm it in the accessibility tree.",
}


def tool(name, description, properties, required, *, read_only=True):
    return {
        "name": name,
        "description": description,
        "inputSchema": {
            "type": "object", "properties": properties, "required": required,
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": read_only, "openWorldHint": False},
    }


REFERENCE_DECISION = record({
    "id": REFERENCE_ID, "region": TEXT, "visibleProperties": TEXT,
    "adaptation": TEXT, "renderTarget": TEXT,
})
REFERENCE_DECISION["properties"]["measurements"] = TEXT
REFERENCE_DECISION["properties"]["sectionId"] = LANDING_SECTION
REFERENCE_DECISION["properties"]["productFeature"] = TEXT
REFERENCE_DECISION["properties"]["componentRole"] = {"type":"string","enum":list(PROFILE["regions"])}
VISUAL_RESULT = record({
    "decisionIndex": {"type": "integer", "minimum": 1, "maximum": 12},
    "screenshot": TEXT, "observation": TEXT, "status": {"type":"string","enum":["pass","fail"]},
})
VISUAL_RESULT["properties"]["measurements"] = TEXT
COMPARISON_PAIR = record({"id":REFERENCE_ID,"screenshot":TEXT})
COMPARISON_PAIR["properties"]["sectionId"] = LANDING_SECTION
MODE = {"type":"string","enum":["inspiration","faithful"]}

SKILL_PLAN = record({"skill":{"type":"string","enum":sorted(PLAYBOOKS)},
                     "application":TEXT,"verification":TEXT})
SKILL_PLAN["properties"]["renderCheck"] = record({
    "selector":TEXT, "value":TEXT,
    "property":{"type":"string","enum":["font-size","font-weight","background-color","color","border-top-left-radius","letter-spacing","padding-top","gap","max-width","display","text-align","background-image"]},
    "operator":{"type":"string","enum":["equals","min-px"]},
})
VISUAL_SKILLS = {"frontend-design", "impeccable"}
AUDIT_PATH = ".cosmos/review/browser-report.json"

TOOLS = [
    tool("read_design_skill", "Read a complete bundled skill, then optionally request one of its listed Markdown guides. Use these instructions on the design. The server tracks main-file delivery for this workflow.", {
        "workflowId": WORKFLOW_ID, "skill": {"type":"string","enum":sorted(PLAYBOOKS)}, "guide": TEXT,
    }, ["workflowId", "skill"], read_only=False),
    tool("plan_design", "Start every Cosmos creation or redesign here. Returns workflowId and requires searching and opening visual references before design approval.", {
        "platform": PLATFORM, "goal": TEXT, "audience": TEXT, "constraints": TEXT, "stack": STACK,
        "referencePlatform": PLATFORM, "app": TEXT, "category": TEXT, "screenType": TEXT,
        "allowCrossPlatform": {"type":"boolean"}, "designMode": MODE, "reproductionAuthorized": {"type":"boolean"},
        "priority": {"type": "string", "enum": ["editorial", "transaction", "exploration"]},
        "brandLogos": array_of(TEXT, 12, 1), "logoExclusion": TEXT,
        "briefReferences": array_of(TEXT, 4, 1),
        "taskMode": TASK_MODE,
        "reuseProjectStyle": {"type": "boolean"},
    }, ["platform", "goal", "audience", "priority"], read_only=False),
    tool("search_patterns", "Find relevant visual patterns for design work, including full landing pages, Grok iOS and categorized Pixlpin screens. For substantial landing pages compare hero, product demonstrations and conversion. Open selected images with read_pattern. Skip for unrelated coding or minor edits.", {
        "query": TEXT, "platform": PLATFORM,
        "kind": {"type": "string", "enum": ["screenshot", "component", "animation", "pattern"]},
        "workflowId": WORKFLOW_ID, "allowCrossPlatform": {"type": "boolean"},
        "app": TEXT, "category": TEXT, "screenType": TEXT, "state": TEXT, "component": TEXT,
        "fullPageOnly": {"type": "boolean"},
        "offset": COUNT,
        "limit": {"type": "integer", "minimum": 1, "maximum": 12},
    }, ["query"], read_only=False),
    tool("search_brand_logos", "Look up the pinned local theSVG catalogue by brand name or slug before planning a web design.", {
        "query":TEXT,
    }, ["query"]),
    tool("read_brand_logo", "Return the exact local theSVG asset and its verified project path. Retrieve every slug declared in plan_design.", {
        "workflowId":WORKFLOW_ID,"slug":TEXT,
    }, ["workflowId","slug"], read_only=False),
    tool("read_pattern", "Open an actual image. A full landing page has three section IDs: hero, features and conversion. Open the full page first and then each detail with sectionId before approving a direction.", {
        "id": REFERENCE_ID, "workflowId": WORKFLOW_ID, "sectionId": LANDING_SECTION,
    }, ["id"], read_only=False),
    tool("open_reference_flow", "Open a curated sequence of related Grok Bot screens as ordered images. Counts opened frames as research evidence for the workflow.", {
        "workflowId": WORKFLOW_ID,
        "flow": {"type": "string", "enum": list(FLOW_IDS)},
    }, ["workflowId", "flow"], read_only=False),
    tool("choose_design_direction", "Approve a design direction only after searching the library and opening relevant screenshots. Record what the references visibly show and how the new design will use those observations.", {
        "workflowId": WORKFLOW_ID, "direction": TEXT,
        "productQuery": TEXT, "visualSignature": TEXT, "primaryAction": TEXT, "copySample": TEXT,
        "referenceDecisions": array_of(REFERENCE_DECISION, 12),
        "noReferenceReason": TEXT,
        "skillPlan": array_of(SKILL_PLAN, 12, 1),
    }, ["workflowId", "direction", "referenceDecisions", "productQuery", "visualSignature", "primaryAction", "copySample"], read_only=False),
    tool("get_design_assets", "Retrieve implementation tokens and the selected component stack. HeroUI projects receive pinned dependencies. Shadcn projects receive the Button registry source. Save/import the token file and use the real component before recording implementation.", {
        "workflowId": WORKFLOW_ID,
    }, ["workflowId"], read_only=False),
    tool("record_design_implementation", "After implementing the approved direction, register the actual code files and decisions embodied in them. Returns the platform checks needed to review the finished UI.", {
        "workflowId": WORKFLOW_ID, "artifacts": array_of(TEXT, 12, 1), "implementation": TEXT, "entry": TEXT,
    }, ["workflowId", "artifacts", "implementation", "entry"], read_only=False),
    tool("run_design_audit", "Run the packaged Chromium audit in the registered project. Start the project on localhost and provide your audit config path. Cosmos binds test output to this workflow.", {
        "workflowId":WORKFLOW_ID, "auditConfig":TEXT,
    }, ["workflowId", "auditConfig"], read_only=False),
    tool("open_design_render", "Load real PNG render files from the configured project. Use the images to critique the implemented UI and reopen after making a correction.", {
        "workflowId": WORKFLOW_ID, "screenshots": array_of(TEXT, 3, 1),
        "comparisonPairs": array_of(COMPARISON_PAIR, 6, 1),
    }, ["workflowId", "screenshots"], read_only=False),
    tool("record_design_review", "Finish a Cosmos workflow by recording an inspected render, one concrete visual correction and fresh verification. Pending or failed checks keep the workflow in review.", {
        "workflowId": WORKFLOW_ID, "renderEvidence": TEXT, "visualCorrection": TEXT, "browserReport": TEXT,
        "saveProjectStyle": {"type": "boolean"},
        "visualResults": array_of(VISUAL_RESULT, 12, 1),
        "skillEvidence": array_of(record({"skill":{"type":"string","enum":sorted(PLAYBOOKS)},"decision":TEXT,"path":TEXT,"excerpt":TEXT}), 12, 1),
        "checks": array_of(record({
            "check": {"type": "string", "enum": sorted(set(sum(REVIEW_CHECKS.values(), [])))},
            "status": {"type": "string", "enum": ["pass", "fail", "pending"]},
            "evidence": TEXT,
        }), 6, 1),
    }, ["workflowId", "renderEvidence", "visualCorrection", "checks"], read_only=False),
    tool("get_design_workflow", "Call before design, implementation, visual audit or motion work. Returns skill instructions to apply and verification checks even when skill files cannot be opened.", {
        "task": {"type": "string", "enum": list(WORKFLOWS)},
        "platform": PLATFORM,
        "stack": STACK,
    }, ["task", "platform"]),
    tool("review_evidence", "Convert measured render observations into prioritized fixes. Inspect captures separately for qualitative findings.", {
        "platform": PLATFORM, "viewport": TEXT,
        "overflowPx": COUNT, "consoleErrors": COUNT, "unlabeledControls": COUNT,
        "reducedMotionAnimations": COUNT, **dict.fromkeys(WEB_REVIEW_ACTIONS, COUNT), "iteration": {"type": "integer", "minimum": 1, "maximum": 2},
    }, ["platform", "viewport", "iteration"]),
]
SCHEMAS = {entry["name"]: entry["inputSchema"] for entry in TOOLS}

COMPOSITIONS = {
    "editorial": (
        "Build the first screen around a dominant headline and one image or illustration.",
        "Use a display scale for headings and a readable text face. Align the image with a clear text edge.",
    ),
    "transaction": (
        "Put the cost, next action and decision-critical constraints in one stable reading order.",
        "Use tabular numerals for changing values. Give action and status distinct roles.",
    ),
    "exploration": (
        "Show the object users can explore and expose the current location or selection.",
        "Use a consistent label scale. Reserve emphasis for the active selection.",
    ),
}


def search_patterns(query, platform=None, kind=None, workflowId=None, allowCrossPlatform=False,
                    app=None, category=None, screenType=None, state=None, component=None,
                    fullPageOnly=False, offset=0, limit=5):
    current = session(workflowId, "research") if workflowId else None
    target = platform or (current.reference_platform if current else None)
    if current and target != current.platform and not (allowCrossPlatform or target == current.reference_platform):
        raise ValueError("Use allowCrossPlatform to explicitly study interactions from another platform.")
    matches, expanded, next_offset = find(query, target, kind, app, category, screenType, state, component,
                                          fullPageOnly, offset, limit)
    matched = {entry["id"] for entry in matches}
    if current:
        current.search_count += 1
        current.offered.update(matched)
    return {
        "matches": matches, "count": len(matches), "workflowId": workflowId, "nextOffset": next_offset,
        "referencePlatform": target, "expandedToRelatedInteractions": expanded,
        "status": "found" if matches else "empty",
        "flows": [{"id": key, "title": flow["title"], "frames": len(flow["ids"]), "ids": flow["ids"]}
                  for key, flow in FLOW_IDS.items() if matched.intersection(flow["ids"])],
    }


def required_skills(current, tasks=("design", "implementation", "audit")):
    names = {name for task in tasks for name in WORKFLOWS[task] if current.platform in PLAYBOOKS[name]}
    if current.stack == "shadcn":
        names.add("shadcn")
    if current.stack == "heroui":
        names.update(("heroui", "thesvg"))
    elif current.brand_slugs:
        names.add("thesvg")
    return sorted(names)


def read_design_skill(workflowId, skill, guide="SKILL.md"):
    current = session(workflowId)
    if skill not in required_skills(current):
        raise ValueError("Skill does not apply to this workflow.")
    root = REFERENCES.parents[1] / skill
    guides = sorted(str(p.relative_to(root)) for p in root.rglob("*.md") if p.is_file() and not p.is_symlink())
    if guide not in guides:
        raise ValueError("Unknown guide. Read the main skill to list available guides.")
    content = (root / guide).read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    if guide == "SKILL.md":
        current.delivered_skills[skill] = digest
    return {"skill": skill, "guide":guide, "sha256":digest, "instructions":content.decode(), "guides":guides}


def require_delivery(current, tasks):
    missing = set(required_skills(current, tasks)) - current.delivered_skills.keys()
    if missing:
        raise ValueError("Read the full instructions with read_design_skill: " + ", ".join(sorted(missing)))


def skill_evidence(current, evidence):
    by_skill = {entry["skill"]: entry for entry in evidence}
    if len(by_skill) != len(evidence) or set(by_skill) != set(required_skills(current)):
        raise ValueError("Submit one skillEvidence entry per applicable skill.")
    if current.design_profile or current.stack == "heroui":
        excerpts = {(" ".join(item["excerpt"].split()), Path(item["path"]).as_posix()) for item in evidence}
        if len(excerpts) != len(evidence):
            raise ValueError("Provide distinct source or test excerpts for each skill.")
    checked = {}
    for name, item in by_skill.items():
        path, quote = item["path"], item["excerpt"]
        if Path(path).suffix.lower() not in {".css", ".scss", ".html", ".tsx", ".ts", ".jsx", ".js", ".cjs", ".mjs", ".vue", ".svelte", ".swift", ".py", ".json", ".kt", ".dart", ".astro"}:
            raise ValueError("Use an implementation, test or report file for " + name)
        if current.platform == "web":
            if name == "superpowers":
                if path != AUDIT_PATH:
                    raise ValueError("Superpowers evidence must cite the browser audit run for this workflow.")
            elif path not in current.implementation["artifacts"] or path.endswith(".json"):
                raise ValueError(f"Evidence for {name} must cite registered implementation source.")
        data = project_file(path)
        if quote.encode() not in data:
            raise ValueError("Missing evidence excerpt for " + name)
        checked[name] = {**item, "fileSha256":hashlib.sha256(data).hexdigest(), "instructionSha256":current.delivered_skills[name]}
    return checked


def plan_design(platform, goal, audience, priority, constraints=None, stack=None,
                referencePlatform=None, app=None, category=None, screenType=None,
                allowCrossPlatform=False, designMode="inspiration", reproductionAuthorized=False,
                brandLogos=None, logoExclusion=None, briefReferences=None, taskMode="create", reuseProjectStyle=False):
    brief = f"{goal} {constraints or ''}"
    words = set(normalize(brief).split())
    app = app or infer_app(brief)
    if words & {"html", "css"}:
        platform = "web"
        stack = stack or "generic"
    target = referencePlatform or ("ios" if words & {"ios", "iphone"} or app == "Grok Bot" else platform)
    if referencePlatform and target != platform and not allowCrossPlatform:
        raise ValueError("Set allowCrossPlatform for an explicitly different referencePlatform.")
    if designMode == "faithful" and not reproductionAuthorized:
        raise ValueError("Faithful reproduction requires the user's ownership or authorization.")
    terms = tokens(brief.strip())
    landing = {"landing", "page"} <= (terms | tokens(screenType or ""))
    category = category or ("Agent IA" if not landing and ({"ai","agent"} <= terms or app == "Grok Bot") else None)
    screenType = screenType or ("Landing-page" if {"landing","page"} <= terms else
                                "Chat" if {"chat","input"} & terms or category == "Agent IA" else None)
    project = project_ui() if platform == "web" else {"status": "native"}
    if stack is None:
        stack = "heroui" if platform == "web" and (
            project["status"] == "unavailable" or project.get("react") or project.get("herouiDeclared")
        ) else "generic"
        if platform == "web":
            try:
                project_file("components.json")
            except (ValueError, OSError):
                pass
            else:
                stack = "shadcn"
    if brandLogos and logoExclusion:
        raise ValueError("Declare brandLogos or logoExclusion, not both.")
    slugs = tuple(slug.strip().lower() for slug in brandLogos or [])
    if len(set(slugs)) != len(slugs):
        raise ValueError("Brand logo slugs must be unique.")
    for slug in slugs:
        logo_asset(slug)
    attachments = {}
    for index, (image, _) in enumerate(inspect_render(briefReferences or []), 1):
        id = f"brief-{index:03d}"
        attachments[id] = {**image, "id":id, "title":Path(image["path"]).name,
                           "size":f'{image["width"]}x{image["height"]}', "mimeType":"image/png",
                           "provenance":"User brief reference"}
    composition, typography = COMPOSITIONS[priority]
    requirements = {
        "web": ["Preserve keyboard flow and usable focus", "Inspect desktop, tablet and mobile captures"],
        "ios": ["Use native navigation and system text styles", "Check VoiceOver, Dynamic Type and Reduce Motion in Simulator"],
    }
    if platform == "ios":
        composition = "Use a native navigation hierarchy and keep the active task in the main content."
        typography = "Use semantic SwiftUI font styles and check large Dynamic Type sizes."
    workflow = get_design_workflow("motion" if taskMode == "motion" else "audit" if taskMode == "audit" else "design", platform, stack)
    workflow_id = uuid4().hex
    if len(SESSIONS) >= MAX_SESSIONS:
        SESSIONS.pop(next(iter(SESSIONS)))
    chat_profile = target == "ios" and category and {"ai", "agent"} <= tokens(category) and "chat" in tokens(screenType or "")
    current = SESSIONS[workflow_id] = DesignSession(
        platform, stack, reference_platform=target, design_mode=designMode,
        design_profile=PROFILE["id"] if chat_profile else None,
        brief_references=attachments, brand_slugs=slugs, logo_exclusion=logoExclusion,
    )
    initial = search_patterns(goal, target, workflowId=workflow_id, allowCrossPlatform=target != platform,
                              app=app, category=category, screenType=screenType)
    if taskMode == "create" and platform == target == "web" and not attachments:
        current.landing_candidates = {row["id"] for row in initial["matches"] if row.get("fullPage") and row["previewAvailable"]}
    current.contract = {
        "schemaVersion": 1, "workflowId": workflow_id, "mode": taskMode,
        "target": {"platform": platform, "stack": stack, "projectUI": project},
        "constraints": {"userSupplied": constraints, "referenceMode": designMode},
        "goal": goal, "audience": audience, "priority": priority,
        "acceptance": requirements[platform],
    }
    if reuseProjectStyle:
        current.contract["projectStyle"] = load_style()
    current.offered.update(attachments)
    return {
        "workflowId": workflow_id,
        "designContract": current.contract,
        "landingResearch": {
            "referenceIds": sorted(current.landing_candidates),
            "requiredSections": LANDING_SECTION["enum"],
            "instruction": "Open one relevant full page and its three section crops. Map each to a concrete product message, example or conversion goal in the new design. Use original branding, copy and assets.",
        } if current.landing_candidates else None,
        "stage": "research", "stack":stack, "briefReferences":list(attachments.values()),
        "brandLogos":slugs, "logoExclusion":logoExclusion,
        "nextLogoAction":"Call read_brand_logo for each declared slug." if slugs else
                         "Record logoExclusion when no real brand mark belongs to the design.",
        "requiredSkills": required_skills(SESSIONS[workflow_id]),
        "next": "Open the matching reference flow and read the applicable guides before approving a direction. If a designProfile is returned, inventory every region and plan each skill application before building.",
        "catalog": {"entries": len(CATALOG), "categoriesByPlatform": COUNTS},
        "platform": platform, "referencePlatform": target, "allowCrossPlatform": target != platform,
        "app": app, "category": category, "screenType": screenType, "designMode": designMode,
        "initialResearch": initial,
        "designProfile": PROFILE if chat_profile else None,
        "brief": {"goal": goal, "audience": audience, "constraints": constraints},
        "composition": composition, "typography": typography,
        "interaction": "Animate one meaningful change at a time. Provide a reduced-motion state.",
        "verification": requirements[platform],
        "relatedPatterns": [entry["id"] for entry in initial["matches"]],
        "workflow": workflow,
    }


@dataclass
class VisualReference:
    metadata: dict
    images: list


def reference_entry(current, id):
    if current and id in current.brief_references:
        return current.brief_references[id]
    return PATTERNS.get(id)


def landing_section(entry, section_id):
    section = next((item for item in entry.get("sections", []) if item["id"] == section_id), None)
    if section is None:
        raise ValueError(f"Unknown full-page section {section_id} for {entry['id']}.")
    return section


def preview(id, current=None, section_id=None):
    attachment = current.brief_references.get(id) if current else None
    if attachment:
        metadata, payload = inspect_render([attachment["path"]])[0]
        if metadata["sha256"] != attachment["sha256"]:
            raise ValueError("The attached reference changed after the brief was registered.")
        return payload
    entry = PATTERNS[id]
    path = REFERENCES / (landing_section(entry, section_id) if section_id else entry)["preview"]
    try:
        data = path.read_bytes()
        if not data.startswith(b"\xff\xd8") or not data.endswith(b"\xff\xd9"):
            raise ValueError("Invalid JPEG")
        return data
    except (OSError, ValueError) as error:
        raise ValueError(f"Cannot open reference image {id}.") from error


def read_pattern(id, workflowId=None, sectionId=None):
    current = session(workflowId, "research") if workflowId else None
    if not reference_entry(current, id):
        raise ValueError("Unknown reference ID. Search the library or register the attachment in the plan.")
    if current and id not in current.offered:
        raise ValueError("Open a result offered to this workflow.")
    if sectionId:
        section = landing_section(reference_entry(current, id), sectionId)
        if current and id not in current.opened:
            raise ValueError("Open the full landing page before asking for section details.")
        data = preview(id, current, sectionId)
        if current:
            current.opened_sections.add((id, sectionId))
        return VisualReference({"id": id, "workflowId": workflowId, "section": section,
                                "status": "opened"}, [("image/jpeg", data)])
    return open_frames([id], workflowId, current)


def read_brand_logo(workflowId, slug):
    current = session(workflowId)
    if current.stage not in {"research", "implementation"} or slug not in current.brand_slugs:
        raise ValueError("Request the logo declared in plan_design during research or implementation.")
    asset = logo_asset(slug)
    current.logos[slug] = {key:value for key,value in asset.items() if key != "svg"}
    return asset


def open_frames(ids, workflow_id, current, **metadata):
    frames, images, failures = [], [], []
    for id in ids:
        try:
            data = preview(id, current)
        except ValueError as error:
            failures.append({"id":id, "reason":str(error)})
            if current:
                current.failed[id] = str(error)
            continue
        entry = reference_entry(current, id)
        frames.append(entry)
        images.append((entry.get("mimeType", "image/jpeg"), data))
        if current:
            current.opened.add(id)
            current.failed.pop(id, None)
    if len(ids) == 1:
        metadata.update(reference_entry(current, ids[0]))
    return VisualReference({**metadata, "workflowId":workflow_id, "frames":frames,
                            "openedIds":[row["id"] for row in frames], "failures":failures,
                            "status":"partial" if failures and frames else "unavailable" if failures else "opened"}, images)


def open_reference_flow(workflowId, flow):
    current = session(workflowId, "research")
    info = FLOW_IDS[flow]
    if not current.offered.intersection(info["ids"]):
        raise ValueError("Search this workflow first and open a flow returned by that search.")
    current.offered.update(info["ids"])
    return open_frames(info["ids"], workflowId, current, flow=flow, title=info["title"])


def choose_design_direction(workflowId, direction, referenceDecisions, productQuery,
                            visualSignature, primaryAction, copySample, noReferenceReason=None, skillPlan=None):
    current = session(workflowId, "research")
    if not current.search_count:
        raise ValueError("Search the library with the workflowId before approving a direction.")
    ids = [decision["id"] for decision in referenceDecisions]
    if current.opened:
        if noReferenceReason or not ids or not set(ids) <= current.opened:
            raise ValueError("Use only reference IDs whose image bytes were opened in this workflow.")
        if len({(item["id"], normalize(item["region"])) for item in referenceDecisions}) != len(ids):
            raise ValueError("Record each observed region once per reference.")
        if current.design_mode == "faithful" and any(not item.get("measurements") for item in referenceDecisions):
            raise ValueError("Faithful reproduction requires measurements of proportions, spacing, radii and visible states.")
    elif not (current.contract["mode"] == "edit" and not current.brief_references and not ids) and (
        ids or not noReferenceReason or current.offered - current.failed.keys()
    ):
        raise ValueError("Open an offered image first, or attempt every offered image and report the verified limitation.")
    for id in current.brief_references:
        if id not in ids and id not in current.failed:
            raise ValueError(f"Use at least one concrete decision from the brief reference {id}.")
    landing_decisions = {}
    for item in referenceDecisions:
        id, section_id = item["id"], item.get("sectionId")
        if section_id:
            landing_section(reference_entry(current, id), section_id)
            if (id, section_id) not in current.opened_sections or not item.get("productFeature"):
                raise ValueError("Open the landing section and name the product feature or conversion goal it demonstrates.")
            landing_decisions.setdefault(id, set()).add(section_id)
    if current.landing_candidates - current.failed.keys() and not any(
        id in current.offered and set(LANDING_SECTION["enum"]) <= sections
        for id, sections in landing_decisions.items()
    ):
        raise ValueError("Use one opened full landing page for hero, features and conversion. Open each crop and supply sectionId and productFeature for each.")
    if current.stack == "heroui" and not (current.brand_slugs or current.logo_exclusion):
        raise ValueError("Declare brandLogos or explain logoExclusion in plan_design.")
    chat_roles, skill_plan = {}, {}
    skill_visuals = []
    if current.design_profile or current.stack == "heroui":
        if current.design_profile and current.opened:
            chat_roles = validate_chat_direction(referenceDecisions, current.opened)
        require_delivery(current, ("design", "implementation", "audit"))
        skill_plan = {row["skill"]: row for row in skillPlan or []}
        if (set(skill_plan) != set(required_skills(current)) or len(skill_plan) != len(skillPlan or [])
                or len({normalize(row["application"]) for row in skill_plan.values()}) != len(skill_plan)):
            raise ValueError("Plan one distinct application and verification per applicable skill before implementing.")
    else:
        require_delivery(current, ("design",))
    if current.stack == "heroui":
        approved_targets = {item["renderTarget"] for item in referenceDecisions}
        for name in sorted(VISUAL_SKILLS):
            check = skill_plan[name].get("renderCheck")
            if not check or (approved_targets and check["selector"] not in approved_targets):
                raise ValueError(f"{name} needs a measurable renderCheck on an approved reference target.")
            if check["operator"] == "min-px" and not re.fullmatch(r"\d+(?:\.\d+)?", check["value"]):
                raise ValueError("Use a numeric minimum for min-px.")
            skill_visuals.append({"skill":name, **check})
        if len({(check["selector"], check["property"]) for check in skill_visuals}) != len(skill_visuals):
            raise ValueError("Use distinct visual measurements for the two design skills.")
    current.tokens = design_tokens(productQuery, current.platform)
    current.reference_limit = noReferenceReason
    current.decisions = referenceDecisions
    current.chat_roles = chat_roles
    current.skill_plan = skill_plan
    current.skill_visuals = skill_visuals
    current.copy_sample = copySample
    current.references = list(dict.fromkeys(ids))
    current.contract.update(direction=direction, primaryAction=primaryAction, composition=referenceDecisions,
                            visualSignature=visualSignature)
    current.stage = "implementation"
    return {
        "workflowId": workflowId, "stage": current.stage, "direction": direction,
        "designContract": current.contract,
        "visualSignature": visualSignature, "primaryAction": primaryAction, "copySample": copySample,
        "tokenGenerator": current.tokens["generator"], "skillPlan":current.skill_plan, "auditAgentChat":chat_roles,
        "references": current.references, "referenceDecisions": referenceDecisions, "noReferenceReason": noReferenceReason,
        "workflow": get_design_workflow("implementation", current.platform, current.stack),
        "next": "Call get_design_assets for the generated files. Implement and then submit the actual entry, imported design files and component sources.",
    }


def get_design_assets(workflowId):
    current = session(workflowId, "implementation")
    component = component_assets() if current.stack == "shadcn" else None
    if current.stack == "heroui":
        component = hero_assets(current.contract["target"]["projectUI"])
    current.assets_delivered = True
    return {"workflowId": workflowId, "tokens": current.tokens, "component": component, "brandLogos":current.brand_slugs,
            "apply": "Use the generated tokens and approved component stack. Build the approved screen, then submit its source files and package metadata for verification."}



def verify_design_source(current, artifacts, entry):
    verified = inspect_implementation(current.platform, current.stack, current.tokens, artifacts, entry, current.copy_sample)
    if current.stack == "heroui":
        verified["heroui"] = verify_heroui_source(artifacts, entry)
    if current.brand_slugs:
        if current.logos.keys() != set(current.brand_slugs):
            raise ValueError("Retrieve every brand logo using read_brand_logo.")
        verified["theSVG"] = verify_brand_assets(current.logos)
    return verified


def verify_browser_kit(current, rows):
    for row in rows:
        proof = row.get("uiKit")
        if not isinstance(proof, dict):
            raise ValueError("Run audit-web with uiKit enabled for the declared stack and brands.")
        if current.stack == "heroui":
            controls = proof.get("controls", [])
            if not controls or any(control.get("status") != "heroui" or not control.get("slot") for control in controls):
                raise ValueError("A visible control does not come from HeroUI.")
            slots = set(proof.get("slots", []))
            expected = {"Button":"button","Link":"link","Card":"card","Switch":"switch","Modal":"modal-dialog"}
            for component in current.implementation["heroui"]["components"]:
                if component in expected and expected[component] not in slots:
                    raise ValueError(f"Render the HeroUI {component} in the initial or audited interaction state.")
        if current.brand_slugs:
            actual = {item["slug"]:item.get("sha256") for item in proof.get("logos", []) if item.get("status") == "loaded"}
            if actual != current.implementation["theSVG"]:
                raise ValueError("A declared theSVG mark is missing or its rendered bytes do not match.")


def record_design_implementation(workflowId, artifacts, implementation, entry):
    current = session(workflowId)
    if current.stage not in {"implementation", "review"}:
        raise ValueError("Approve a direction before verifying its implementation.")
    if not current.assets_delivered:
        raise ValueError("Retrieve get_design_assets before submitting implementation.")
    require_delivery(current, ("implementation",))
    verified = verify_design_source(current, artifacts, entry)
    if verified != current.implementation:
        current.reviewed_images.clear()
        current.comparisons.clear()
        current.audit_sha = None
    current.implementation = verified
    current.stage = "review"
    return {
        "workflowId": workflowId, "stage": current.stage, "artifacts": artifacts,
        "implementation": implementation, "sourceVerification": verified, "checksRequired": REVIEW_CHECKS[current.platform],
        "workflow": get_design_workflow("audit", current.platform, current.stack),
        "next": "For web, run run_design_audit against the live local site. Open the actual captures before record_design_review.",
    }



def run_design_audit(workflowId, auditConfig):
    current = session(workflowId, "review")
    if current.platform != "web":
        raise ValueError("This browser audit is only for web designs.")
    verified = current.implementation
    paths, entry = list(verified["artifacts"]), verified["entry"]
    if verify_design_source(current, paths, entry) != verified:
        raise ValueError("Register updated source before relaunching the audit.")
    try:
        config = json.loads(project_file(auditConfig))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("Provide a valid browser audit configuration.") from error
    if not isinstance(config, dict):
        raise ValueError("Provide a browser audit configuration object.")
    current.audit_sha = None
    config["requireKeyboardTransition"] = True
    config["skillVisuals"] = current.skill_visuals
    try:
        result = subprocess.run(
            ["node", str(Path(__file__).with_name("audit-web.cjs")), "-"],
            input=json.dumps(config), cwd=os.environ["COSMOS_PROJECT_ROOT"], text=True,
            capture_output=True, timeout=90, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ValueError("The Chromium audit could not run. Install the project test dependencies and confirm the local server is available.") from error
    if result.returncode:
        details = result.stderr.strip()[:500]
        try:
            rows = json.loads(result.stdout)["viewports"]
            failures = [
                f'{row["width"]}px: '
                + ", ".join([check["skill"] + " " + check["property"] + "=" + check["actual"]
                             for check in row["skillVisuals"] if not check["pass"]]
                            + (["no proven keyboard transition"] if not row["keyboardTransition"] else [])
                            + row["violations"])
                for row in rows
                if any(not check["pass"] for check in row["skillVisuals"]) or not row["keyboardTransition"] or row["violations"]
            ]
            if failures:
                details = "; ".join(failures)
        except (ValueError, KeyError, TypeError):
            pass
        raise ValueError("Chromium audit failed: " + (details or "Inspect the browser report and rerun."))
    if verify_design_source(current, paths, entry) != verified:
        raise ValueError("Source changed during the audit. Register and run it again.")
    report = project_file(AUDIT_PATH)
    current.audit_sha = hashlib.sha256(report).hexdigest()
    parsed = json.loads(report)
    return {"browserReport":AUDIT_PATH, "sha256":current.audit_sha,
            "screenshots":parsed["screenshots"], "skillVisuals":current.skill_visuals,
            "next":"Open the audit screenshots and compare them before completing review."}


def open_design_render(workflowId, screenshots, comparisonPairs=None):
    current = session(workflowId, "review")
    images = inspect_render(screenshots)
    comparisons, paired_images = [], []
    captures = [metadata for metadata, _ in images]
    by_path = {meta["path"]: (meta, data) for meta, data in images}
    for pair in comparisonPairs or []:
        id, path = pair["id"], pair["screenshot"]
        if id not in current.references or path not in by_path:
            raise ValueError("Pair an approved reference with a screenshot from this call.")
        meta, render = by_path[path]
        entry = reference_entry(current, id)
        section_id = pair.get("sectionId")
        reference_metadata = landing_section(entry, section_id) if section_id else entry
        width, height = map(int, reference_metadata["size"].split("x"))
        ratio = (meta["width"] / meta["height"]) / (width / height)
        comparable = 0.67 <= ratio <= 1.5
        if not comparable and (not entry.get("fullPage") or current.design_mode == "faithful"):
            raise ValueError("Capture a comparable viewport or crop the same region. The aspect ratios differ too much.")
        reference = preview(id, current, section_id)
        index = len(images) + len(paired_images) + 1
        paired_images.extend([(reference_entry(current, id).get("mimeType", "image/jpeg"), reference), ("image/png", render)])
        comparisons.append({**pair, "imageBlocks": [index, index + 1], "referenceSize": [width,height],
                            "renderSize":[meta["width"],meta["height"]], "referenceSha256":hashlib.sha256(reference).hexdigest(),
                            "comparableAspectRatio": comparable,
                            "renderSha256":meta["sha256"],
                            "decisionIndices":[i for i, item in enumerate(current.decisions, 1)
                                               if item["id"] == id and (not section_id or item.get("sectionId") == section_id)]})
    current.reviewed_images = captures
    current.comparisons = comparisons
    return VisualReference({"workflowId":workflowId, "captures":captures, "comparisons":comparisons,
                            "referenceLimit":current.reference_limit,
                            "next":"Inspect each pair in order (reference, render) at the same display width. Compare each numbered decision against its render target. Report visible differences and reopen after fixing them."},
                           [("image/png", data) for _, data in images] + paired_images)


def record_design_review(workflowId, renderEvidence, visualCorrection, checks, browserReport=None, skillEvidence=None,
                         visualResults=None, saveProjectStyle=False):
    current = session(workflowId, "review")
    required = set(REVIEW_CHECKS[current.platform])
    results = {item["check"]: item for item in checks}
    if len(results) != len(checks) or results.keys() - required:
        raise ValueError("Supply at most one result per platform review check.")
    pending = sorted(required - {name for name, item in results.items() if item["status"] == "pass"})
    screenshots = current.reviewed_images
    has_render = bool(screenshots)
    if current.platform == "web":
        widths = {entry["width"] for entry in screenshots}
        has_render = any(width <= 480 for width in widths) and any(width >= 1000 for width in widths)
    if not has_render:
        pending = sorted(set(pending) | {"render"})
    browser_verification = None
    if current.platform == "web":
        if browserReport and has_render:
            if browserReport != AUDIT_PATH or not current.audit_sha:
                raise ValueError("Call run_design_audit in this workflow before review.")
            if hashlib.sha256(project_file(browserReport)).hexdigest() != current.audit_sha:
                raise ValueError("The browser report changed after run_design_audit. Rerun the audit.")
            browser_verification = inspect_browser_report(
                browserReport, screenshots, current.copy_sample, current.tokens["colors"],
                current.stack == "shadcn" and current.implementation["shadcnButton"]["source"] == "bundled shadcn registry",
            )
            if not all(row.get("keyboardTransition") is True for row in browser_verification["viewports"]):
                raise ValueError("Exercise a real keyboard action that changes an asserted state.")
            if current.stack == "heroui" or current.brand_slugs:
                verify_browser_kit(current, browser_verification["viewports"])
        else:
            pending = sorted(set(pending) | {"browser-report"})
    evidence = {}
    if not skillEvidence:
        pending = sorted(set(pending) | {"skill-evidence"})
    else:
        require_delivery(current, ("design", "implementation", "audit"))
        evidence = skill_evidence(current, skillEvidence)
    if current.decisions:
        results_by_index = {row["decisionIndex"]: row for row in visualResults or []}
        if len(results_by_index) != len(visualResults or []) or set(results_by_index) - set(range(1, len(current.decisions) + 1)):
            raise ValueError("Submit at most one visual result per decision index.")
        browser_rows = {row.get("screenshot"): row for row in browser_verification["viewports"]} if browser_verification else {}
        for index, decision in enumerate(current.decisions, 1):
            result = results_by_index.get(index)
            pair = next((pair for pair in current.comparisons
                         if result and index in pair["decisionIndices"] and pair["screenshot"] == result["screenshot"]), None)
            if pair and result["status"] == "fail":
                current.rejected_renders[index] = pair["renderSha256"]
            if (not pair or result["status"] != "pass"
                    or current.rejected_renders.get(index) == pair["renderSha256"]
                    or current.platform == "web" and decision["renderTarget"] not in browser_rows.get(pair["screenshot"], {}).get("referenceTargets", [])
                    or current.design_mode == "faithful" and not result.get("measurements")):
                pending.append(f"reference-decision-{index}")
            if pair and current.chat_roles and current.platform == "web" and decision.get("componentRole") == "send":
                send_audit = browser_rows.get(pair["screenshot"], {}).get("agentChat") or {}
                if (send_audit.get("measurements") or {}).get("sendEnabled") is not True:
                    pending.append("agent-chat-send-draft-state")
    if current.chat_roles and current.platform == "web":
        for screenshot in {row["screenshot"] for row in visualResults or []}:
            report = browser_rows.get(screenshot, {}).get("agentChat")
            pending.extend(f"agent-chat-{issue}" for issue in chat_failures(report, current.chat_roles))
        if not visualResults:
            pending.append("agent-chat-audit")
    pending = sorted(set(pending))
    saved_style = None
    if not pending:
        if any(hashlib.sha256(preview(pair["id"], current, pair.get("sectionId"))).hexdigest() != pair["referenceSha256"]
               for pair in current.comparisons):
            raise ValueError("Reference image changed. Reopen the comparison.")
        verified = current.implementation
        if verify_design_source(current, list(verified["artifacts"]), verified["entry"]) != verified:
            raise ValueError("Source files changed. Record implementation again and open fresh render captures.")
        if [meta for meta, _ in inspect_render([entry["path"] for entry in screenshots])] != screenshots:
            raise ValueError("Screenshot files changed. Reopen them for visual review.")
        if saveProjectStyle:
            saved_style = save_style(current.contract, current.tokens)
        current.stage = "complete"
    return {
        "workflowId": workflowId, "stage": current.stage, "references": current.references,
        "savedProjectStyle": saved_style,
        "pendingChecks": pending, "renderEvidence": renderEvidence, "visualCorrection": visualCorrection,
        "checks": checks, "openedScreenshots": screenshots, "sourceVerification": current.implementation,
        "referenceLimit": current.reference_limit,
        "referenceStatus": "compared" if current.comparisons and not any(item.startswith("reference-decision-") for item in pending)
                           else "pending" if current.decisions else "unavailable" if current.failed else "empty",
        "referenceFailures": current.failed, "comparisons":current.comparisons,
        "visualResults":visualResults or [], "browserVerification": browser_verification, "skillEvidence": evidence,
        "skillPlan":current.skill_plan, "designProfile":current.design_profile,
        "auditReportSha256":current.audit_sha,
        "evidenceStatus": (
            "Cosmos ran Chromium and checked the registered implementation evidence. Visual fidelity also involves reviewer judgment."
            if browser_verification else "Source and PNG evidence are inspected. Visual judgments are supplied by the client."
        ),
    }


def get_design_workflow(task, platform, stack="generic"):
    if platform == "ios" and stack != "generic":
        raise ValueError("Use native components for iOS designs.")
    def guidance(names):
        return [
            {
                "id": name,
                "path": f"skills/{name}/SKILL.md",
                "apply": PLAYBOOKS[name]["apply"],
                "instructions": PLAYBOOKS[name][platform],
                "check": PLAYBOOKS[name]["check"],
            }
            for name in names if platform in PLAYBOOKS[name]
        ]

    active = WORKFLOWS[task].copy()
    if platform == "ios" and "superpowers" not in active:
        active.append("superpowers")
    if stack == "shadcn" and task in {"design", "implementation", "audit"}:
        active.insert(0, "shadcn")
    if stack == "heroui" and task in {"design", "implementation", "audit"}:
        active[:0] = ["heroui", "thesvg"]

    lead = guidance(active)
    shipping = guidance(WORKFLOWS["implementation"] + WORKFLOWS["audit"]) if task == "design" else []
    lead_ids = {skill["id"] for skill in lead}
    # Implementation and audit share accessibility and verification. Send each once.
    completion = {skill["id"]: skill for skill in shipping if skill["id"] not in lead_ids}
    return {
        "task": task,
        "platform": platform,
        "execute": EXECUTION,
        "skills": lead,
        "completionChecks": list(completion.values()),
        **({"motionExample": {"path": "src/cosmos-stagger.mjs",
                              "content": Path(__file__).with_name("cosmos-stagger.mjs").read_text(),
                              "apply": "Use animateSequence with ordered elements, per-item frames and an explicit staggerMs. Test the computed delays, playback rate and reduced-motion final state."}}
           if task == "motion" and platform == "web" else {}),
        "evidence": "Open the actual page and inspect mobile, tablet and desktop. Exercise the primary path using keyboard and pointer, record console and overflow checks, and retest after corrections." if platform == "web"
                    else "Compile and verify VoiceOver, Dynamic Type and Reduce Motion on an Apple target when available.",
    }

def review_evidence(platform, viewport, iteration, **observations):
    actions = {
        "overflowPx": "Find the first overwide element. Check min-width, grid tracks and unbreakable text.",
        "consoleErrors": "Open the first error stack and repair the originating handler or asset load.",
        "unlabeledControls": "Give each affected control a visible label or a platform accessibility label.",
        "reducedMotionAnimations": "Skip nonessential transforms when the system requests reduced motion.",
    }
    if platform == "web":
        actions.update(WEB_REVIEW_ACTIONS)
    elif observations.keys() & WEB_REVIEW_ACTIONS.keys():
        raise ValueError("Web-only measurements supplied for iOS")
    return {
        "platform": platform, "viewport": viewport,
        "fixes": [{"signal": key, "value": observations[key], "action": action}
                  for key, action in actions.items() if observations.get(key, 0) > 0],
        "missingMeasurements": sorted(actions.keys() - observations.keys()),
        "remainingRounds": 2 - iteration,
        "visualAssessment": "Requires inspecting the actual images or video.",
    }


HANDLERS = {
    "read_design_skill": read_design_skill,
    "plan_design": plan_design,
    "search_patterns": search_patterns,
    "open_reference_flow": open_reference_flow,
    "get_design_assets": get_design_assets,
    "open_design_render": open_design_render,
    "run_design_audit": run_design_audit,
    "choose_design_direction": choose_design_direction,
    "record_design_implementation": record_design_implementation,
    "record_design_review": record_design_review,
    "read_pattern": read_pattern,
    "read_brand_logo": read_brand_logo,
    "search_brand_logos": lambda query: {"matches":find_logos(query)},
    "review_evidence": review_evidence,
    "get_design_workflow": get_design_workflow,
}


def validate(value, spec, field):
    kind = spec["type"]
    if kind == "object":
        properties = spec["properties"]
        if not isinstance(value, dict) or value.keys() - properties.keys() or set(spec["required"]) - value.keys():
            raise ValueError(f"Missing required or unexpected fields in {field}")
        for name, child in value.items():
            validate(child, properties[name], f"{field}.{name}")
    elif kind == "array":
        if not isinstance(value, list) or not spec["minItems"] <= len(value) <= spec["maxItems"]:
            raise ValueError(f"Invalid list: {field}")
        for child in value:
            validate(child, spec["items"], field)
    elif kind == "string":
        if not isinstance(value, str) or not value.strip() or len(value) > spec.get("maxLength", 1000):
            raise ValueError(f"Invalid text field: {field}")
        if "pattern" in spec and not re.fullmatch(spec["pattern"], value):
            raise ValueError(f"Invalid format: {field}")
    elif kind == "boolean" and type(value) is not bool:
        raise ValueError(f"Invalid boolean field: {field}")
    elif kind == "integer":
        if type(value) is not int or not spec["minimum"] <= value <= spec["maximum"]:
            raise ValueError(f"Invalid integer field: {field}")
    if "enum" in spec and value not in spec["enum"]:
        raise ValueError(f"Unsupported value: {field}")


def call(params):
    if not isinstance(params, dict) or not isinstance(params.get("name"), str):
        raise ValueError("Expected a tool name")
    name = params["name"]
    if name not in SCHEMAS:
        raise ValueError("Unknown tool")
    args = params.get("arguments", {})
    validate(args, SCHEMAS[name], "arguments")
    return HANDLERS[name](**args)


def dispatch(message):
    if not isinstance(message, dict) or message.get("jsonrpc") != "2.0" or not isinstance(message.get("method"), str):
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid request"}}
    if "id" not in message:
        return None

    method = message["method"]
    params = message.get("params", {})
    response = {"jsonrpc": "2.0", "id": message["id"]}
    if method == "initialize" and isinstance(params, dict):
        requested = params.get("protocolVersion")
        version = requested if isinstance(requested, str) and requested in PROTOCOLS else "2025-03-26"
        result = {"protocolVersion": version, "capabilities": {"tools": {}},
                  "serverInfo": {"name": "cosmos-local", "version": "2.5.0"},
                  "instructions": "For substantial UI work start plan_design. For a landing page with landingResearch open a complete page and each required section, then map them to actual features and conversion goals. For a small edit preserve the rest. Skip Cosmos for unrelated questions. Build, open real captures and record verified evidence. Preserve the selected web or native platform."}
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        try:
            data = call(params)
        except ValueError as error:
            result = {"isError": True, "content": [{"type": "text", "text": str(error)}]}
        else:
            visual = data if isinstance(data, VisualReference) else None
            payload = visual.metadata if visual else data
            result = {"content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False, separators=(",", ":"))}]}
            if isinstance(payload, dict):
                result["structuredContent"] = payload
            if visual:
                result["content"].extend(
                    {"type": "image", "mimeType": mime, "data": base64.b64encode(data).decode("ascii")}
                    for mime, data in visual.images
                )
    else:
        response["error"] = {"code": -32601, "message": "Method not found"}
        return response
    response["result"] = result
    return response


if __name__ == "__main__":
    for line in sys.stdin.buffer:
        try:
            response = dispatch(json.loads(line))
        except (ValueError, RecursionError):
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
        if response is not None:
            print(json.dumps(response, ensure_ascii=False), flush=True)
