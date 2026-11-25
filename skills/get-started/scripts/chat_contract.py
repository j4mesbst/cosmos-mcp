"""Reference-based checks for a full iOS-style agent conversation."""
import json
import math

from patterns import REFERENCES


PROFILE = json.loads((REFERENCES / "ios-agent-chat.json").read_text())


def validate_direction(decisions, opened):
    inventory = [item for item in decisions if item.get("componentRole")]
    roles = {item["componentRole"]: item["renderTarget"] for item in inventory}
    if (set(roles) != PROFILE["regions"].keys() or len(roles) != len(inventory)
            or len(set(roles.values())) != len(roles)):
        raise ValueError("Inventory every required chat component with its own render target and reference.")
    used = {item["id"] for item in decisions if item.get("componentRole")}
    if len(opened) > 1 and len(used) < 2:
        raise ValueError("Use at least two opened reference states for the chat inventory.")
    return roles


def failures(report, roles):
    if not isinstance(report, dict) or report.get("roles") != roles:
        return ["inventory"]
    sampled = report.get("measurements")
    if not isinstance(sampled, dict):
        return ["measurements"]
    try:
        box = sampled["box"]
        canvas, back, agent, avatar, computer, messages, composer, add, send = (box[role] for role in roles_order)
        for rect in (*box.values(), sampled["bubble"]):
            if not isinstance(rect, dict) or any(
                type(rect.get(key)) not in {int, float} or not math.isfinite(rect[key])
                for key in ("left","right","top","bottom","width","height")
            ):
                return ["geometry"]
        bubble = sampled["bubble"]
        checks = {
            "white-canvas": sampled["color"] == "rgb(255, 255, 255)",
            "header-without-divider": sampled["divider"] == 0,
            "header-order": back["right"] <= agent["left"] and agent["right"] < computer["left"]
                            and abs(back["top"] - computer["top"]) <= 12 and agent["top"] < canvas["top"] + 135,
            "agent-avatar": sampled["agentContainsAvatar"] is True and 18 <= avatar["width"] <= 45
                            and avatar["left"] < agent["left"] + 16 and avatar["width"] < agent["width"],
            "touch-targets": all(item["height"] >= 44 and item["width"] >= 44 for item in (back, computer, add))
                             and send["width"] >= 36 and send["height"] >= 36,
            "composer-position": composer["bottom"] >= min(canvas["bottom"], sampled["viewportHeight"]) - 55
                                 and sampled["composerRadius"] >= composer["height"] * 0.35,
            "send-inside": sampled["composerContainsSend"] is True and send["left"] >= composer["left"]
                           and send["right"] <= composer["right"] + 1 and send["top"] >= composer["top"]
                           and send["bottom"] <= composer["bottom"] + 1
                           and composer["right"] - send["right"] <= 16,
            "auxiliary-outside": sampled["composerContainsAdd"] is False and add["right"] <= composer["left"]
                                 and abs(add["width"] - add["height"]) <= 2 and sampled["addRadius"] >= add["height"] * 0.45,
            "message-bubble": bubble["left"] - messages["left"] <= 16 and bubble["width"] <= messages["width"] * 0.92
                              and bubble["radius"] >= 12 and bubble["top"] > canvas["top"] + canvas["height"] * 0.42
                              and bubble["bottom"] < composer["top"],
        }
    except (KeyError, TypeError, ValueError):
        return ["measurements"]
    return [name for name, passed in checks.items() if not passed]


roles_order = ("canvas", "back", "agent", "avatar", "computer", "messages", "composer", "add", "send")
