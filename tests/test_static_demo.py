"""Public export boundaries: recorded data only, with live functionality disabled."""

import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

from countertrace import model
from scripts.build_static_demo import recorded_status, tracked_files


class StaticDemoTest(unittest.TestCase):
    def test_status_never_loads_model_credentials_or_private_usage(self):
        with mock.patch.object(model, "config", side_effect=AssertionError("private config read")), \
                mock.patch.object(model, "spend_summary", side_effect=AssertionError("private usage read")):
            state = recorded_status()
        self.assertFalse(state["deployment"]["live_available"])
        self.assertFalse(state["model"]["configured"])
        self.assertFalse(state["verifier"]["image_built"])
        self.assertFalse(state["uploads_enabled"])
        self.assertIsNone(state["model"]["spend"]["estimated_cost_usd"])

    def test_untracked_private_files_are_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / "recorded").mkdir()
            (root / "recorded" / "public.json").write_text(json.dumps({"recorded": True}))
            subprocess.run(["git", "-C", str(root), "add", "recorded/public.json"], check=True)
            (root / "recorded" / "private.txt").write_text("must not be published")
            self.assertEqual(tracked_files(root, "recorded"), [Path("recorded/public.json")])

    def test_tracked_symlinks_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / "recorded").mkdir()
            (root / "private.txt").write_text("must not be published")
            (root / "recorded" / "link.txt").symlink_to(root / "private.txt")
            subprocess.run(["git", "-C", str(root), "add", "recorded/link.txt"], check=True)
            with self.assertRaisesRegex(ValueError, "regular tracked file"):
                tracked_files(root, "recorded")
