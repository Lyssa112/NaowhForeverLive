"""Tests for Tools/build/rxp_contract.py, offline, against folders made here. From the repo root:

    python -m unittest discover -s Tools/tests
"""
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import paths  # noqa: E402,F401
import rxp_contract  # noqa: E402

SWITCH = "the V2 switch (IsEnabled, or IsGuideWindowEnabled before 4.11.38)"
LINK = "comms.OpenLink (or the RXP_Link popup before it)"
ITEMS = "the Active Items window (activeItemWindow, or activeItemFrame before 4.11.39)"
TARGETS = "the Active Targets window (activeTargetWindow, or activeTargetFrame before 4.11.39)"
RESTYLE = "UpdateTheme of a window (or its UpdateVisuals before 4.11.39)"
ARROW = "the arrow's redraw (UpdateTheme, or UpdateVisuals before 4.11.39)"


def found(source):
    return {name: ok for _, name, ok in rxp_contract.check(source)}


class ContractTest(unittest.TestCase):
    def folder(self, files):
        root = tempfile.TemporaryDirectory()
        self.addCleanup(root.cleanup)
        for name, text in files.items():
            path = Path(root.name) / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        return root.name

    def test_every_entry_is_whole_and_unique(self):
        names = [name for _, name, _ in rxp_contract.CONTRACT]
        self.assertEqual(len(names), len(set(names)))
        for what, name, pattern in rxp_contract.CONTRACT:
            self.assertTrue(what and name and pattern)
            rxp_contract.re.compile(pattern)

    def test_nothing_is_found_in_nothing(self):
        self.assertFalse(any(found("").values()))

    def test_a_name_is_found_where_it_is_written(self):
        got = found("function addon.GetGuideProgress()\nend\nfunction RXPFrame:DropDownMenu(menu)\nend")
        self.assertTrue(got["GetGuideProgress"])
        self.assertTrue(got["RXPFrame.DropDownMenu"])
        self.assertFalse(got["GetGuideName"])
        self.assertFalse(got["SetStep"])

    def test_the_v2_switch_is_either_name(self):
        self.assertTrue(found("function addon.v2:IsEnabled()\nend")[SWITCH])
        self.assertTrue(found("function addon.v2:IsGuideWindowEnabled()\nend")[SWITCH])
        self.assertFalse(found("function addon.v2:IsSomethingElse()\nend")[SWITCH])
        self.assertFalse(found("function addon.v2:UpdateGuideWindow()\nend")[SWITCH])

    def test_a_link_is_the_function_or_the_older_popup(self):
        self.assertTrue(found("function addon.comms.OpenLink(url)\nend")[LINK])
        self.assertTrue(found('_G.StaticPopupDialogs["RXP_Link"] = {}')[LINK])
        self.assertFalse(found("function addon.comms.OpenSupport()\nend")[LINK])

    def test_the_windows_are_widgets_or_the_older_frames(self):
        self.assertTrue(found("self.activeItemWindow = window")[ITEMS])
        self.assertTrue(found("addon.activeItemFrame = CreateFrame()")[ITEMS])
        self.assertFalse(found("self.activeItemList = {}")[ITEMS])
        self.assertTrue(found("self.activeTargetWindow = window")[TARGETS])
        self.assertTrue(found("targeting.activeTargetFrame = CreateFrame()")[TARGETS])
        self.assertFalse(found("self.activeTargetCount = 0")[TARGETS])
        self.assertTrue(found('["UpdateTheme"] = updateTheme')[RESTYLE])
        self.assertTrue(found("function frame:UpdateVisuals()\nend")[RESTYLE])
        self.assertFalse(found("function frame:UpdateScale()\nend")[RESTYLE])

    def test_the_arrow_is_redrawn_by_either_name(self):
        self.assertTrue(found("af.UpdateTheme = addon.ui.v2.UpdateTheme")[ARROW])
        self.assertTrue(found("function af:UpdateVisuals()\nend")[ARROW])
        self.assertFalse(found("function af:UpdateSubTheme()\nend")[ARROW])

    def test_libraries_translations_and_scripts_are_not_read(self):
        root = self.folder({
            "libs/Ace/Ace.lua": "function addon.GetGuideProgress() end",
            "Libs/Other.lua": "function addon.GetGuideName() end",
            "locale/enUS.lua": "function addon.SetStep() end",
            "Scripts/new_locale.lua": "function addon.UpdateMap() end",
            "UI/V2/Core.lua": "function addon.v2:BuildGuideStepsSnapshot() end",
            "GuideWindow.lua": "function addon.ReplaceNpcIds() end",
        })
        got = found(rxp_contract.read_source(root))
        self.assertTrue(got["v2:BuildGuideStepsSnapshot"])
        self.assertTrue(got["ReplaceNpcIds"])
        for name in ("GetGuideProgress", "GetGuideName", "SetStep", "UpdateMap"):
            self.assertFalse(got[name], name)

    def test_a_file_is_read_whatever_its_line_endings(self):
        root = self.folder({"a.lua": "function addon.GetGuideProgress()\r\nend\r\n"})
        self.assertTrue(found(rxp_contract.read_source(root))["GetGuideProgress"])

    def run_main(self, root):
        out = io.StringIO()
        with redirect_stdout(out):
            status = rxp_contract.main(["rxp_contract.py", root])
        return status, out.getvalue()

    def test_the_status_is_1_with_something_missing_and_it_is_listed(self):
        root = self.folder({"a.lua": "function addon.GetGuideProgress()\nend"})
        with mock.patch.object(rxp_contract, "CONTRACT", [
                ("guide", "GetGuideProgress", r"function addon\.GetGuideProgress"),
                ("guide", "SetStep", r"function addon\.SetStep")]):
            status, text = self.run_main(root)
        self.assertEqual(status, 1)
        self.assertIn("MISSING guide   SetStep", text)
        self.assertIn("ok      guide   GetGuideProgress", text)
        self.assertIn("1 of 2 found, 1 missing", text)

    def test_the_status_is_0_with_everything_there(self):
        root = self.folder({"a.lua": "function addon.SetStep()\nend"})
        with mock.patch.object(rxp_contract, "CONTRACT", [("guide", "SetStep", r"function addon\.SetStep")]):
            status, text = self.run_main(root)
        self.assertEqual(status, 0)
        self.assertIn("1 of 1 found", text)
        self.assertNotIn("MISSING", text)

    def test_a_folder_that_is_not_there_is_status_2(self):
        status, text = self.run_main(str(Path(tempfile.gettempdir()) / "no-such-rxpguides-folder"))
        self.assertEqual(status, 2)
        self.assertIn("No RestedXP folder", text)


if __name__ == "__main__":
    unittest.main()
