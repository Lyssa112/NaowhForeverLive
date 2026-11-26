"""Check an installed RestedXP Guides for everything Naowh's RestedXP integration reaches into.

RestedXP renames and moves things between releases (4.11.38 renamed the V2 switch the window
asks first, and for a few days the Naowh window did not show). Run this after a RestedXP update:
every function, frame and field the integration uses (Core/Integrations/RestedXP) is looked for
in RestedXP's own Lua files, and what is not there is listed.

Usage: python Tools/build/rxp_contract.py [path to the RXPGuides folder]
       (without a path: the RXPGUIDES_PATH variable, else the Forever client's AddOns folder)

Exit status 1 when something is missing. An entry matching in the source only says the name is
still written there, not that it works the same: the window's tests are for that.
"""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import paths  # noqa: E402,F401

FOREVER = r"C:\Program Files (x86)\World of Warcraft\_forever_\Interface\AddOns\RXPGuides"
SKIPPED = {"libs", "locale", "scripts"}  # folders that carry no code the integration reaches

# (what, name, a regular expression that matches where RestedXP defines or makes it)
CONTRACT = [
    # the guide and its steps
    ("guide", "GetGuideProgress", r"function addon\.GetGuideProgress|addon\.GetGuideProgress\s*="),
    ("guide", "GetGuideName", r"function addon\.GetGuideName|addon\.GetGuideName\s*="),
    ("guide", "SetStep", r"function addon\.SetStep"),
    ("guide", "UpdateMap", r"function addon\.UpdateMap|addon\.UpdateMap\s*="),
    ("guide", "UpdateGotoSteps", r"function addon\.UpdateGotoSteps|addon\.UpdateGotoSteps\s*="),
    ("guide", "ReplaceNpcIds", r"function addon\.ReplaceNpcIds|addon\.ReplaceNpcIds\s*="),
    ("guide", "ActiveStepElementEventHandler",
     r"function addon\.ActiveStepElementEventHandler|addon\.ActiveStepElementEventHandler\s*="),
    ("guide", "RXPFrame.activeSteps", r"RXPFrame\.activeSteps"),
    ("guide", "questAccept", r"addon\.questAccept"),
    ("guide", "updateSteps", r"addon\.updateSteps"),
    ("guide", "UpdateItemFrame (the Active Items window)", r"function addon\.UpdateItemFrame"),
    # the V2 interface the window is for
    ("v2", "the V2 switch (IsEnabled, or IsGuideWindowEnabled before 4.11.38)",
     r"function addon\.v2[:.](IsEnabled|IsGuideWindowEnabled)"),
    ("v2", "v2:BuildGuideStepsSnapshot", r"function addon\.v2[:.]BuildGuideStepsSnapshot"),
    ("v2", "v2:UpdateGuideWindow", r"function addon\.v2[:.]UpdateGuideWindow"),
    ("v2", "v2:UpdateActiveStepsFrame", r"function addon\.v2[:.]UpdateActiveStepsFrame"),
    ("v2", "v2:UpdatePlayerActiveStepItem", r"function addon\.v2[:.]UpdatePlayerActiveStepItem"),
    ("v2", "v2:ShowGuideSelectionMenu", r"function addon\.v2[:.]ShowGuideSelectionMenu"),
    ("v2", "enableV2Interface (the setting behind the switch)", r"enableV2Interface"),
    ("v2", "enableBetaFeatures (the other setting behind it)", r"enableBetaFeatures"),
    # the menu and links
    ("menu", "RXPFrame.DropDownMenu", r"function RXPFrame[:.]DropDownMenu"),
    ("link", "comms.OpenLink (or the RXP_Link popup before it)",
     r"function addon\.comms\.OpenLink|StaticPopupDialogs\[\"RXP_Link\"\]"),
    # the windows RestedXP builds, which the window takes, skins or hangs another from
    ("frames", "RXPV2GuideWindow", r"RXPV2GuideWindow"),
    ("frames", "RXPActiveStepsFrame<player>", r"RXPActiveStepsFrame"),
    ("frames", "the Active Items window (activeItemWindow, or activeItemFrame before 4.11.39)",
     r"activeItemWindow\s*=|activeItemFrame\s*="),
    ("frames", "the Active Targets window (activeTargetWindow, or activeTargetFrame before 4.11.39)",
     r"activeTargetWindow\s*=|activeTargetFrame\s*="),
    ("frames", "UpdateTheme of a window (or its UpdateVisuals before 4.11.39)",
     r"\[\"UpdateTheme\"\]\s*=|UpdateVisuals"),
    ("frames", "buttonList (the Active Items window's buttons)", r"buttonList\s*="),
    ("frames", "UpdateTargetFrame", r"function addon\.targeting[:.]UpdateTargetFrame"),
    ("frames", "rxpBackground (what the skin recolors)", r"rxpBackground"),
    ("frames", "rxpBorder (and its border)", r"rxpBorder"),
    ("frames", ".textures (a border's pieces)", r"\.textures\b"),
    ("frames", ".placeholder (a target button's picture)", r"\.placeholder\b"),
    # the arrow and the themes
    ("theme", "RXPGuides_Themes", r"RXPGuides_Themes"),
    ("theme", "v2:GetTheme (the active theme, with the logo of its window)", r"function addon\.v2[:.]GetTheme"),
    ("theme", "guideWindow.logo (the logo of its V2 window)", r"theme\.guideWindow\.logo"),
    ("theme", "RegisterTheme", r"function addon[:.]RegisterTheme"),
    ("theme", "ReloadTheme", r"function addon[:.]ReloadTheme"),
    ("theme", "RXPG_ARROW", r"RXPG_ARROW"),
    ("theme", "addon.arrowFrame", r"addon\.arrowFrame\s*=|arrowFrame\s*=\s*CreateFrame"),
    ("theme", "the arrow's redraw (UpdateTheme, or UpdateVisuals before 4.11.39)",
     r"af\.UpdateTheme\s*=|af[:.]UpdateVisuals"),
    ("theme", "addon.hideArrow", r"addon\.hideArrow"),
    ("theme", "addon.activeWaypoints", r"addon\.activeWaypoints"),
    ("theme", "addon.icons", r"addon\.icons\s*="),
    ("theme", "addon.font", r"addon\.font\s*="),
    ("theme", "addon.locale", r"addon\.locale"),
]


def read_source(root):
    """All of RestedXP's Lua, but for the libraries and the translations, as one text."""
    root = Path(root)
    parts = []
    for path in sorted(root.rglob("*.lua")):
        if SKIPPED & {part.lower() for part in path.relative_to(root).parts[:-1]}:
            continue
        parts.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts)


def check(source):
    """(what, name, found) for each entry of the contract."""
    return [(what, name, re.search(pattern, source) is not None) for what, name, pattern in CONTRACT]


def missing(results):
    return [(what, name) for what, name, found in results if not found]


def report(results):
    lines = []
    for what, name, found in results:
        lines.append("{:<7} {:<7} {}".format("ok" if found else "MISSING", what, name))
    gone = missing(results)
    lines.append("")
    lines.append("{} of {} found{}".format(len(results) - len(gone), len(results),
                                           "" if not gone else ", {} missing".format(len(gone))))
    return "\n".join(lines)


def main(argv):
    given = argv[1] if len(argv) > 1 else os.environ.get("RXPGUIDES_PATH") or FOREVER
    root = Path(given)
    if not root.is_dir():
        print("No RestedXP folder at {}. Pass the path to its RXPGuides folder.".format(root))
        return 2
    results = check(read_source(root))
    print(report(results))
    return 1 if missing(results) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
