"""Local catalogue metadata and ranked, platform-scoped reference search."""
from collections import Counter
import json
from pathlib import Path
import re
import unicodedata

REFERENCES = Path(__file__).resolve().parents[1] / "references"
ALIASES = {
    "premiere conversation": "first conversation", "champ de saisie": "input",
    "agent ia": "ai agent", "assistant ia": "ai agent", "page d accueil": "home",
    "page de vente": "landing page", "page de destination": "landing page",
    "tableau de bord": "dashboard", "premiere utilisation": "onboarding",
    "etat vide": "empty state", "en attente": "loading", "mot de passe": "password",
    "parametres": "settings", "reglages": "settings", "connexion": "oauth",
    "bouton": "button", "clavier": "keyboard", "saisie": "input", "messagerie": "chat",
    "conversation": "chat", "conversations": "chat", "tarification": "pricing",
    "iphone": "ios", "grokbot": "grok bot", "erreur": "error",
}
STOP = set("a an the for of and or in to with de d un une du et en des au sur la le les i os ios web screen ecran interface application app cree creer create design style inspire toi inspirez screens html corresponds".split())


def normalize(value):
    plain = "".join(c for c in unicodedata.normalize("NFKD", value.casefold()) if not unicodedata.combining(c))
    return " ".join(re.findall(r"[a-z0-9]+", plain))


def tokens(value):
    plain = normalize(value)
    for phrase, replacement in ALIASES.items():
        plain = re.sub(r"\b" + phrase + r"\b", replacement, plain)
    return set(plain.split()) - STOP


def indexed_entries():
    for filename in ("catalog.json", "pixlpin-catalog.json", "landing-page-catalog.json"):
        for row in json.loads((REFERENCES / filename).read_text(encoding="utf-8")):
            label = tokens(row["structure"] + " " + row.get("classificationReason", ""))
            row.setdefault("app", row["collection"])
            if row["app"] == "Grok Bot":
                row["category"] = "Agent IA"
                row["screenType"] = "Chat" if label & {"chat","prompt","keyboard","message","bot"} else "Agent IA"
                if row["id"] == "grok-029":
                    label.update(("input", "composer", "button", "first", "chat"))
            row["productCategory"] = "Agent IA" if row["app"] in {
                "Grok Bot", "chatgpt-web", "claude-web", "cursor-web", "sana-web"
            } else row.get("productCategory")
            row["components"] = sorted(label & {
                "input","composer","button","keyboard","dialog","modal","sidebar","menu",
                "navigation","textarea","filter","search","card","chart","table","toggle"
            })
            row["states"] = sorted((label | tokens(row["screenType"])) & {
                "empty","loading","error","success","disabled","hover","focus","initial","first","keyboard"
            })
            yield row


CATALOG = list(indexed_entries())
PATTERNS = {row["id"]: row for row in CATALOG}
COUNTS = {platform: dict(sorted(Counter(row["category"] for row in CATALOG if row["platform"] == platform).items()))
          for platform in ("ios", "web")}
APPS = {row["app"] for row in CATALOG}
SEARCH_INDEX = [(row, tokens(" ".join([row["structure"], row["category"], row["screenType"],
                                       row["productCategory"] or "", *row.get("tags", []),
                                       *row["states"], *row["components"]]))) for row in CATALOG]


def infer_app(query):
    plain = " " + normalize(query) + " "
    for app in sorted(APPS, key=lambda name: (-len(normalize(name).removesuffix(" web")), name)):
        if app == "Cosmos" and "cosmos" != plain.strip() and not re.search(r"(?:inspir|reference|app|site|landing).{0,25}cosmos", plain):
            continue
        name = normalize(app).removesuffix(" web").split()
        if len(name) > 1 and re.fullmatch(r"[a-z0-9]{4}", name[-1]) and any(c.isdigit() for c in name[-1]):
            name.pop()
        if " " + " ".join(name) + " " in plain:
            return app
    if "grok" in tokens(query):
        return "Grok Bot"
    return None


def find(query, platform, kind, app=None, category=None, screen_type=None, state=None, component=None,
         full_page_only=False, offset=0, limit=5):
    terms = tokens(query)
    app = app or infer_app(query)
    if app:
        terms -= tokens(app)
    if any(value and not tokens(value) for value in (category, screen_type, state, component)):
        return [], False, None
    filters = [tokens(value) for value in (screen_type, state, component) if value]
    category_words = tokens(category or "")
    landing_intent = {"landing", "page"} <= (terms | tokens(screen_type or "") | category_words)
    narrow, related = [], []
    for row, words in SEARCH_INDEX:
        if full_page_only and not row.get("fullPage"):
            continue
        if (platform and row["platform"] != platform) or (kind and row["kind"] != kind):
            continue
        exact = query.strip().casefold() == row["id"]
        if app and not exact and not (normalize(row["app"]).startswith(normalize(app)) or
                                      normalize(app).startswith(normalize(row["app"]) + " web")):
            continue
        overlap = terms & words
        strict = all(group <= words for group in filters)
        category_match = not category_words or any(category_words <= tokens(label) for label in
                                                   (row["productCategory"] or "", row["category"]))
        if exact or (strict and category_match and (overlap or app or filters or category_words)):
            if terms and not (exact or overlap or category_words or (app and filters)):
                continue
            target = narrow
        elif (overlap or any(group & words for group in filters)) and not exact:
            target = related
        else:
            continue
        score = 1000 * exact + 5 * len(overlap) + 8 * len(terms & tokens(row["screenType"]))
        score += 20 * ("first" in terms and bool({"first","initial"} & words))
        if row["id"] == "grok-029" and (app == "Grok Bot" or category == "Agent IA"):
            score += 100 if "first" in terms else 12
        if row.get("fullPage") and landing_intent:
            score += 30 + 7 * len(terms & set(row["tags"]))
        target.append((-score, row["id"], row))
    expanded = len(narrow) < 2 and bool(related) and bool(category_words or filters)
    ranked = sorted(narrow) + (sorted(related) if expanded else [])
    keys = ("id","title","kind","platform","app","category","productCategory","screenType","states","components","structure","adapt")
    results = []
    for _, _, row in ranked[offset:offset + limit]:
        entry = {key: row[key] for key in keys}
        entry["previewAvailable"] = (REFERENCES / row["preview"]).is_file()
        if row.get("fullPage"):
            entry.update(fullPage=True, sections=[s["id"] for s in row["sections"]],
                         matchReasons=sorted(terms & set(row["tags"])), rights=row["rights"])
        results.append(entry)
    next_offset = offset + limit if len(ranked) > offset + limit else None
    return results, expanded, next_offset
