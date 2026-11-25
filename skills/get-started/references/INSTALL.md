# Cosmos 2.4.1 local setup

Extract the plugin. Python 3.10+ runs the desktop stdio MCP and the bundled UI/UX Pro Max script. Set `COSMOS_PROJECT_ROOT` to the absolute path of the project to inspect. Change the setting when switching projects. The package includes 117 Grok Bot iOS references and 3,656 Pixlpin Web captures in 39 folders. The catalogue exposes app, product category (when identified), screen type, states and components. Use the platform counts returned from plan_design to discover categories. The Pixlpin manifest is incorporated into the index, and SHA-256 values for shipped bytes are stored separately from the source manifest hashes.

An example of manual MCP registration in a client configuration:

```json
{
  "mcpServers": {
    "cosmos": {
      "command": "python3",
      "args": ["/absolute/path/to/cosmos/skills/get-started/scripts/server.py"],
      "env": { "COSMOS_PROJECT_ROOT": "/absolute/path/to/your/project" }
    }
  }
}
```

Use the Cosmos plugin in the same conversation for the bundled skills. For a verification call, supply file paths relative to the configured project root. The server will check source and render files there. Run ID state lives in the MCP process. To use ChatGPT Web with the same tools requires a separate hosted MCP and platform-specific project evidence.

## Web audit

In the web project use Playwright and `@axe-core/playwright` as dev dependencies and an installed Chromium. If you use a system Chromium, set `COSMOS_CHROMIUM` to its executable. Start the local app and create a configuration, for example `.cosmos/audit.json`:

```json
{
  "url": "http://127.0.0.1:4173/",
  "shadcnButtons": "button[data-slot=button]",
  "designProbes": {
    "composition": {"selector":"h1","text":"Interview notes"},
    "copy": {"selector":"label[for=message]","text":"Ask about this interview"},
    "token": {"selector":".source-note","property":"color","token":"--cosmos-foreground"}
  },
  "referenceTargets": ["#message"],
  "steps": [
    {"action": "fill", "selector": "#message", "value": "Test the composer"},
    {"action": "press", "selector": "button[type=submit]", "value": "Enter"},
    {"action": "text", "selector": ".timeline li", "value": "Test the composer"}
  ]
}
```

From the project root run `node /absolute/path/to/cosmos/skills/get-started/scripts/audit-web.cjs .cosmos/audit.json`. Inspect the screenshots under `.cosmos/review/`. Open the mobile and desktop files with `open_design_render`. Submit `.cosmos/review/browser-report.json` with the final review. For a different product use selectors and assertions that match its primary user action. Automated axe results cover the selected checks and do not establish full accessibility conformance.

The research and rationale are in [RECHERCHE.md](RECHERCHE.md). The registry component and license are in [components/](components/).

Use the approved copySample in one of the two visible text probes. Compare the token with a real, visible element using the generated color. Put shadcnButtons on projects with registry buttons and choose a selector covering the actual actions.

In a web workflow with references, enter each approved renderTarget as an exact CSS selector in referenceTargets. Only visible elements count at the screenshot viewport. For native designs use an identifiable element and describe the visual match.


For `ios-agent-chat`, first approve distinct `componentRole` assignments with observations from two opened reference states when available. Supply one `skillPlan` application and verification per applicable skill. Copy the returned `auditAgentChat` selector map verbatim into `agentChat` in the audit config. Set `agentChatDraft` to an object with `selector` for the message input and `text` giving a realistic draft. Pair the browser's default mobile capture with the idle reference and `agent-draft-390.png` with the draft reference. Keep all approved selectors in `referenceTargets`. The tool checks layout and geometry. Use the paired images to judge icon style, copy and visual fidelity. Native projects use simulator evidence for these judgments.


## HeroUI and theSVG on web

Use Node, React 19 and Tailwind CSS 4. Get the exact HeroUI dependencies from get_design_assets, including @babel/parser for source checks. Import tailwindcss before @heroui/styles. Install dependencies in the target project. The source verifier checks the dependency versions and AST, while the browser audit measures the controls and verifies SVG bytes. These checks are evidence of the specified project workflow.

For user-provided PNG references, specify project-relative files in briefReferences and open the returned brief-NNN IDs. In plan_design, pass brandLogos such as ["figma","notion","vercel"], or use logoExclusion for a project that calls for no third-party marks. Place the exact SVG returned by read_brand_logo in public/cosmos-logos and add data-cosmos-logo to its img. In audit.json use "uiKit": {"heroui":true, "logoSlugs":["figma","notion","vercel"]}. Add {"action":"capture-ui"} after opening any modal to include that interactive state. For a documented logo exclusion set logoSlugs to [].

The bundled marks come from @thesvg/icons 4.0.16. The pinned component implementation is HeroUI 3.2.8. Use registered asset provenance and preserve third-party marks as provided.


### Skill review evidence

On a new HeroUI design, include a `renderCheck` in the two design entries
`frontend-design` and `impeccable`. Use `selector`, `property`, `operator`
and `value`. Use `min-px` with a numeric string for a size or `equals`
with a browser-computed value such as `rgb(255, 255, 255)`. Choose a visible,
approved reference target when references were selected.

For any web design, run the registered local app and call `run_design_audit`
before opening the final screenshots. The report must belong to this workflow.
Use a keyboard action followed by an assertion that changes from false to true,
such as opening a modal with Enter then asserting that it is visible.
Register source files before reporting skill evidence. General claims in a
separate JSON document are not evidence. These checks establish concrete effects,
while the paired images still need visual judgment.
