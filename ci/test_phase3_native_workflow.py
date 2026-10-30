"""Codemagic regression: the install step must not use an unbound CI_PYTHON.

The installer writes CI_PYTHON to CM_ENV for *later* steps, not into the
currently running shell. A same-step command must export the path explicitly.
"""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class Phase3NativeWorkflowTest(unittest.TestCase):
    def test_install_step_exports_python_before_invoking_it(self):
        yaml = (ROOT / "codemagic.yaml").read_text(encoding="utf-8")
        workflow = yaml.split("  dual-strategy-phase3-native-research:", 1)[1]
        install = workflow.split("      - name: Install pinned CPU Freqtrade and FreqAI runtime", 1)[1]
        install = install.split("      - name:", 1)[0]
        setup = 'bash ci/setup-python.sh requirements-freqai.txt requirements-market-data.txt'
        command = '"$CI_PYTHON" -m freqtrade --version'
        self.assertIn(setup, install)
        self.assertIn(command, install)
        self.assertIn('export CI_PYTHON="$CM_BUILD_DIR/.ci-tools/python-venv/bin/python"', install)
        self.assertLess(install.index(setup), install.index("export CI_PYTHON="))
        self.assertLess(install.index("export CI_PYTHON="), install.index(command))
        self.assertIn('test -x "$CI_PYTHON"', install)

    def test_installer_persists_python_for_following_steps(self):
        setup = (ROOT / "ci/setup-python.sh").read_text(encoding="utf-8")
        self.assertIn("printf 'CI_PYTHON=%s\\n' \"$ci_python\" >> \"$CM_ENV\"", setup)


if __name__ == "__main__":
    unittest.main()
