"""Offline negative tests for R12 Stage 0; no network, paid APIs or deployment."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.r12_site_guard import (
    ROOT, build_public_site, is_public_path, production_state,
    release_eligible, verify_package,
)


class TestR12Safety(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.config = self.base / "production_control.json"

    def test_missing_state_fails_closed(self):
        self.assertEqual(production_state(self.config), "STOPPED")
        self.assertFalse(release_eligible(self.config))

    def test_invalid_json_fails_closed(self):
        self.config.write_text("{not JSON", encoding="utf-8")
        self.assertEqual(production_state(self.config), "STOPPED")

    def test_unknown_or_wrong_type_state_fails_closed(self):
        for state in ("enabled", None, True, "ACTIVE "):
            self.config.write_text(json.dumps({"production_state": state}), encoding="utf-8")
            self.assertEqual(production_state(self.config), "STOPPED")

    def test_active_is_not_release_approval(self):
        self.config.write_text('{"production_state":"ACTIVE"}', encoding="utf-8")
        self.assertFalse(release_eligible(self.config))
        self.assertFalse(release_eligible(self.config, founder_approved=True))
        self.assertFalse(release_eligible(self.config, environment_verified=True))
        self.assertTrue(release_eligible(self.config, founder_approved=True, environment_verified=True))

    def test_stopped_overrides_approval(self):
        self.config.write_text('{"production_state":"STOPPED"}', encoding="utf-8")
        self.assertFalse(release_eligible(self.config, founder_approved=True, environment_verified=True))

    def test_allowlist_excludes_private_files(self):
        for name in (".env", "data/secret.json", "control-room/index.html",
                     "dashboard/truth.json", "products/notes.md",
                     "creatives/DRAFT.html", "tests/test_governance.py"):
            self.assertFalse(is_public_path(name), name)
        for name in ("index.html", "products/example.html", "social/hero.png"):
            self.assertTrue(is_public_path(name), name)

    def _sample_source(self):
        src = self.base / "site"
        (src / "products").mkdir(parents=True)
        (src / "data").mkdir()
        (src / "control-room").mkdir()
        (src / "index.html").write_text("<h1>RIO</h1>", encoding="utf-8")
        (src / "products" / "product.html").write_text("<p>Product</p>", encoding="utf-8")
        (src / "products" / "draft.md").write_text("internal", encoding="utf-8")
        (src / "control-room" / "index.html").write_text("private", encoding="utf-8")
        (src / "data" / "secret.json").write_text("secret", encoding="utf-8")
        return src

    def test_public_package_is_selective(self):
        src = self._sample_source()
        out = self.base / "out"
        self.assertEqual(build_public_site(src, out), 2)
        self.assertTrue((out / "products" / "product.html").exists())
        self.assertFalse((out / "data").exists())
        self.assertFalse((out / "control-room").exists())
        self.assertFalse((out / "products" / "draft.md").exists())

    def test_output_injection_is_rejected(self):
        src = self._sample_source()
        out = self.base / "out"
        build_public_site(src, out)
        (out / "secrets.json").write_text("oops", encoding="utf-8")
        with self.assertRaises(ValueError):
            verify_package(out)

    def test_nonempty_destination_is_rejected(self):
        src = self._sample_source()
        out = self.base / "out"
        out.mkdir()
        (out / "legacy").write_text("do not overwrite", encoding="utf-8")
        with self.assertRaises(ValueError):
            build_public_site(src, out)

    def test_source_output_overlap_is_rejected(self):
        src = self._sample_source()
        with self.assertRaises(ValueError):
            build_public_site(src, src / "_public")

    def test_symlink_source_is_rejected(self):
        src = self._sample_source()
        (src / "products" / "shortcut.html").symlink_to(src / "index.html")
        with self.assertRaises(ValueError):
            build_public_site(src, self.base / "out")

    def test_existing_live_deployment_remains_unmodified(self):
        # Branch-level guard: workflow performs validation but cannot publish.
        workflow = (ROOT / ".github/workflows/deploy-pages.yml").read_text(encoding="utf-8")
        self.assertNotIn("actions/deploy-pages@", workflow)
        self.assertNotIn("actions/upload-pages-artifact@", workflow)
        self.assertNotIn("pages: write", workflow)
        self.assertNotIn("id-token: write", workflow)

    def test_legacy_flyer_cannot_push_to_main(self):
        workflow = (ROOT / ".github/workflows/hermes-rio-flyer-transport.yml").read_text(encoding="utf-8")
        self.assertNotIn("git push origin HEAD:main", workflow)
        self.assertNotIn("contents: write", workflow)
        self.assertIn("if: \${{ false }}", workflow)

    def test_development_control_is_stopped(self):
        self.assertEqual(production_state(ROOT / "data/production_control.json"), "STOPPED")


if __name__ == "__main__":
    unittest.main()
