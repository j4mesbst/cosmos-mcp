"""Run from any directory: python -B test_references.py [demo-output-path]."""
import base64
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else None
FLOW = ["grok-029", "grok-035", "grok-036", "grok-037"]

with TemporaryDirectory() as temp:
    project = Path(temp)
    # Keep dependency resolution local to the temporary browser fixture.
    if OUT:
        (project / "node_modules").symlink_to(Path(os.environ["COSMOS_NODE_MODULES"]).resolve(), target_is_directory=True)
    with subprocess.Popen([sys.executable, "-B", str(ROOT / "scripts/server.py")],
                          stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
                          env={**os.environ, "COSMOS_PROJECT_ROOT": temp}) as process:
        def call(name, *, error=None, **args):
            process.stdin.write(json.dumps({"jsonrpc":"2.0","method":"tools/call","id":1,
                                           "params":{"name":name,"arguments":args}}) + "\n")
            process.stdin.flush()
            result = json.loads(process.stdout.readline())["result"]
            if error:
                assert result.get("isError") and error in result["content"][0]["text"], result
                return None
            assert not result.get("isError"), result
            return result["structuredContent"], result["content"][1:]

        def plan(goal, platform="web", **options):
            options.setdefault("stack", "generic")
            return call("plan_design", goal=goal, platform=platform, audience="Équipe terrain",
                        priority="exploration", **options)[0]

        def guides(workflow, ids):
            for skill in ids:
                call("read_design_skill", workflowId=workflow, skill=skill)

        try:
            named = plan("Inspire-toi des écrans Grok Bot pour une première conversation", "ios")
            assert named["app"] == "Grok Bot" and named["relatedPatterns"][0] == "grok-029"
            assert FLOW == named["initialResearch"]["flows"][0]["ids"]
            unnamed = plan("Crée une interface iOS d’agent IA", "ios")
            assert unnamed["category"] == "Agent IA" and unnamed["screenType"] == "Chat"
            assert unnamed["initialResearch"]["matches"][0]["productCategory"] == "Agent IA"
            cross = plan("Crée en HTML une interface d’agent IA au style iOS")
            assert (cross["platform"], cross["referencePlatform"], cross["allowCrossPlatform"]) == ("web", "ios", True)
            assert cross["relatedPatterns"]
            workflow = cross["workflowId"]
            empty = plan("xjzqvplmok")
            assert empty["initialResearch"]["status"] == "empty"
            assert sum(cross["catalog"]["categoriesByPlatform"]["web"].values()) == 3656
            assert cross["catalog"]["categoriesByPlatform"]["web"]["Autres"] == 52
            landing = call("search_patterns", query="page de destination", platform="web", app="apple-web", screenType="Landing-page")[0]
            assert landing["matches"] and all(row["category"] == "Landing-page" for row in landing["matches"])
            call("read_pattern", id=landing["matches"][0]["id"])
            fields = call("search_patterns", query="champ de saisie", platform="ios", component="input")[0]
            assert fields["matches"]
            assert unnamed["designProfile"]["id"] == cross["designProfile"]["id"] == "ios-agent-chat"
            inventory = [
                ("029","canvas","Fond blanc, sans séparation au-dessous du header","Fond blanc sans titre produit","#chat"),
                ("029","back","Chevron simple dans un cercle côté gauche","Retour réel vers les discussions","#back"),
                ("029","agent","Nom court et avatar regroupés à gauche","Afficher le nom de l’agent Sillage","#agent"),
                ("029","avatar","Petit pictogramme clair dans une forme sombre","Créer une marque topographique bleu ardoise","#avatar"),
                ("029","computer","Moniteur isolé en haut à droite","Ouvrir l’espace local des repères","#computer"),
                ("029","messages","Bulles entrantes grises en bas sous une grande zone libre","Deux messages courts, fond gris presque blanc","#messages"),
                ("035","composer","Capsule blanche en bas, à droite du bouton plus","Regrouper le champ et la validation","#composer"),
                ("035","add","Bouton plus séparé, rond et clair","Préremplir un repère de terrain","#add"),
                ("035","send","Flèche montante dans un petit disque sombre à droite à l’intérieur de la capsule","Envoyer et afficher une bulle sombre à droite","#send"),
            ]
            decisions = [{"id":"grok-"+id, "componentRole":role, "region":role,
                          "visibleProperties":properties, "adaptation":adaptation, "renderTarget":target}
                         for id, role, properties, adaptation, target in inventory]
            application = {
                "frontend-design": ("Zone libre au-dessus de la conversation", "Contrôle de la position verticale des bulles"),
                "taste-skill": ("Nom de l’agent et texte d’accueil liés au contexte terrain", "Contrôle des textes visibles dans Chromium"),
                "ui-ux-pro-max": ("Couleur sémantique appliquée au nom de l’agent", "Comparaison du style calculé et du jeton produit"),
                "web-accessibility": ("Nom accessible du bouton d’envoi et attribut disabled", "Test axe et envoi au clavier"),
                "web-design-guidelines": ("Toute la navigation reste accessible sur mobile", "Retour, repère, envoi, ordinateur à 390, 768, 1440"),
                "impeccable": ("Supprimer le titre produit, le trait et la toile beige du prototype précédent", "Comparer le rendu et les mesures"),
                "superpowers": ("Rétablir la position interne de la flèche et rejouer le défaut", "Détection de l’envoi hors capsule"),
            }
            skill_plan = [{"skill":key,"application":value[0],"verification":value[1]}
                          for key,value in application.items()]
            approval = dict(direction="Discussion claire, identité terrain", productQuery="AI chat productivity",
                            visualSignature="Icône topographique et contrôles compacts", primaryAction="Envoyer",
                            copySample="Sillage")
            call("choose_design_direction", workflowId=workflow, referenceDecisions=decisions, error="Open an offered image", **approval)
            # Simulate unavailable previews in this server by using a temporary moved file, restored immediately.
            unavailable = ROOT / "references/grok/previews/grok-029.jpg"
            backup = unavailable.rename(unavailable.with_suffix(".test-missing"))
            try:
                partial, images = call("open_reference_flow", workflowId=workflow, flow="first-conversation")
                assert partial["status"] == "partial" and partial["openedIds"] == FLOW[1:] and len(images) == 3
                call("choose_design_direction", workflowId=workflow, referenceDecisions=decisions, error="whose image bytes", **approval)
            finally:
                backup.rename(unavailable)
            frames, images = call("open_reference_flow", workflowId=workflow, flow="first-conversation")
            assert frames["openedIds"] == FLOW and len(images) == 4
            ref_image = base64.b64decode(images[0]["data"])
            only = plan("xjzqvplmok")
            single = only["workflowId"]
            call("search_patterns", query="grok-029", workflowId=single, platform="ios", allowCrossPlatform=True)
            backup = unavailable.rename(unavailable.with_suffix(".test-missing"))
            try:
                failure, blocks = call("read_pattern", workflowId=single, id="grok-029")
                assert failure["status"] == "unavailable" and not blocks
                guides(single, only["requiredSkills"])
                assert call("choose_design_direction", workflowId=single, referenceDecisions=[],
                            noReferenceReason="grok-029 est illisible.", **approval)[0]["noReferenceReason"]
            finally:
                backup.rename(unavailable)
            guides(empty["workflowId"], empty["requiredSkills"])
            assert call("choose_design_direction", workflowId=empty["workflowId"], referenceDecisions=[],
                        noReferenceReason="Aucune capture pour xjzqvplmok.", **approval)[0]["noReferenceReason"]
            call("plan_design", platform="ios", goal="Copie fidèle", audience="Équipe", priority="exploration",
                 designMode="faithful", error="authorization")
            guides(workflow, cross["requiredSkills"])
            call("choose_design_direction", workflowId=workflow, referenceDecisions=decisions[:2],
                 skillPlan=skill_plan, error="Inventory", **approval)
            call("choose_design_direction", workflowId=workflow, referenceDecisions=decisions,
                 skillPlan=skill_plan[:-1], error="distinct application", **approval)
            approved = call("choose_design_direction", workflowId=workflow, referenceDecisions=decisions,
                            skillPlan=skill_plan, **approval)[0]
            assert len(approved["referenceDecisions"]) == 9
            assets = call("get_design_assets", workflowId=workflow)[0]
            if OUT:
                shutil.copytree(ROOT / "tests/fixture", project, dirs_exist_ok=True)
                token = assets["tokens"]["file"]
                file = project / token["path"]
                file.parent.mkdir()
                file.write_text(token["content"])
                source = ["index.html", token["path"]]
                call("record_design_implementation", workflowId=workflow, artifacts=source,
                     entry="index.html", implementation="Capsule et ajout de repère dans un carnet original.")
                with subprocess.Popen([sys.executable, "-m", "http.server", "4191", "--bind", "127.0.0.1"],
                                      cwd=project, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) as web:
                    try:
                        for attempt in range(50):
                            try:
                                with urlopen("http://127.0.0.1:4191/", timeout=0.3):
                                    break
                            except OSError:
                                time.sleep(0.1)
                        else:
                            raise RuntimeError("Browser fixture could not start")
                        call("run_design_audit", workflowId=workflow, auditConfig="audit.json")
                        subprocess.run(["node", str(ROOT / "tests/agent_chat_regressions.cjs")], cwd=project, check=True)
                        sys.path.insert(0, str(ROOT / "scripts"))
                        from chat_contract import failures
                        regression = json.loads((project / ".cosmos/review/regressions.json").read_text())
                        assert not failures(regression["restored"], approved["auditAgentChat"])
                        for key, report in regression.items():
                            if key != "restored":
                                assert key in failures(report, approved["auditAgentChat"]), (key, report)
                    finally:
                        web.terminate()
                        web.wait(timeout=5)
                mobile, desktop = [f".cosmos/review/render-{width}.png" for width in (390, 1440)]
                draft_screen = ".cosmos/review/agent-draft-390.png"
                captures = [mobile, desktop, draft_screen]
                excerpts = {
                    "frontend-design": ("index.html", "justify-content: flex-end"),
                    "taste-skill": ("index.html", "Un itinéraire à préparer ou un repère à retrouver"),
                    "ui-ux-pro-max": ("index.html", "color: var(--cosmos-foreground)"),
                    "web-accessibility": ("index.html", 'aria-label="Envoyer le message" disabled'),
                    "web-design-guidelines": ("index.html", 'aria-label="Retour aux discussions"'),
                    "impeccable": ("index.html", "margin: 0; background: #fff"),
                    "superpowers": (".cosmos/review/browser-report.json", '"keyboardTransition": true'),
                }
                proof = [{"skill": skill, "path": excerpts[skill][0], "excerpt": excerpts[skill][1],
                          "decision": application[skill][0]} for skill in cross["requiredSkills"]]
                review = dict(workflowId=workflow, renderEvidence="Capture Chromium",
                              visualCorrection="Comparaison des trois régions", browserReport=".cosmos/review/browser-report.json",
                              skillEvidence=proof,
                              checks=[{"check":name, "status":"pass","evidence":"Chromium fixture audit"}
                                      for name in ("render","responsive","keyboard","primary-flow","reduced-motion")])
                verdicts = [{"decisionIndex":index,"screenshot":mobile if index <= 6 else draft_screen,
                             "status":"pass","observation": item["adaptation"]}
                            for index,item in enumerate(decisions,1)]
                call("open_design_render", workflowId=workflow, screenshots=captures)
                assert "reference-decision-1" in call("record_design_review", visualResults=verdicts, **review)[0]["pendingChecks"]
                call("open_design_render", workflowId=workflow, screenshots=captures, error="aspect ratios",
                     comparisonPairs=[{"id":"grok-029","screenshot":desktop}])
                comparison, blocks = call("open_design_render", workflowId=workflow, screenshots=captures,
                                          comparisonPairs=[{"id":FLOW[0],"screenshot":mobile},{"id":FLOW[1],"screenshot":draft_screen}])
                assert comparison["comparisons"][0]["decisionIndices"] == [1,2,3,4,5,6] and len(blocks) == 7
                assert "reference-decision-3" in call("record_design_review", visualResults=verdicts[:2], **review)[0]["pendingChecks"]
                report_path = project / review["browserReport"]
                report_bytes = report_path.read_bytes()
                try:
                    report_path.write_bytes(report_bytes + b" ")
                    call("record_design_review", workflowId=workflow,
                         visualResults=verdicts, error="browser report changed",
                         **{key:value for key,value in review.items() if key != "workflowId"})
                finally:
                    report_path.write_bytes(report_bytes)
                duplicate = [{**item, "path":"index.html","excerpt":"<main"} for item in proof]
                call("record_design_review", visualResults=verdicts,
                     **{**review, "skillEvidence":duplicate}, error="distinct source")
                completed = call("record_design_review", visualResults=verdicts, **review)[0]
                assert completed["stage"] == "complete"
                OUT.mkdir(parents=True, exist_ok=True)
                (OUT / "reference.jpg").write_bytes(ref_image)
                shutil.copyfile(project / mobile, OUT / "render.png")
                shutil.copyfile(project / draft_screen, OUT / "active.png")
                shutil.copyfile(project / ".cosmos/review/regressions.json", OUT / "regressions.json")
                shutil.copyfile(project / "index.html", OUT / "index.html")
                (OUT / "cosmos-tokens.css").write_text(token["content"])
                shutil.copyfile(project / review["browserReport"], OUT / "browser-report.json")
                (OUT / "workflow.json").write_text(json.dumps(
                    {"brief":cross["brief"],"initial":cross["initialResearch"],"opened":FLOW,
                     "decisions":decisions,"comparison":completed["comparisons"],"review":completed["visualResults"],
                     "skills":completed["skillEvidence"],"skillPlan":completed["skillPlan"]},
                    ensure_ascii=False, indent=2))
            print("Cosmos reference tests passed")
        finally:
            process.stdin.close()
