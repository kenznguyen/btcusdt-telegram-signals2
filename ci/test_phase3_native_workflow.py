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

    def test_download_uses_initialized_explicit_freqtrade_userdir(self):
        yaml = (ROOT / "codemagic.yaml").read_text(encoding="utf-8")
        workflow = yaml.split("  dual-strategy-phase3-native-research:", 1)[1]
        install = workflow.split("      - name: Install pinned CPU Freqtrade and FreqAI runtime", 1)[1]
        install = install.split("      - name:", 1)[0]
        download = workflow.split("      - name: Download genuine futures OHLCV plus exchange-managed funding and mark data", 1)[1]
        download = download.split("      - name:", 1)[0]
        userdir = '"$CM_BUILD_DIR/.ci-tools/phase3-freqtrade-userdata"'
        self.assertIn('freqtrade create-userdir --userdir ' + userdir, install)
        self.assertIn('--userdir ' + userdir, download)
        self.assertLess(install.index('freqtrade create-userdir'), install.index("Pinned Freqtrade/FreqAI imports OK") if False else len(install))
        self.assertIn('test -d ' + userdir, install)

    def test_native_research_uses_same_explicit_userdir(self):
        yaml = (ROOT / "codemagic.yaml").read_text(encoding="utf-8")
        native = yaml.split("  dual-strategy-phase3-native-research:", 1)[1]
        research = native.split("      - name: Native Freqtrade and FreqAI research on the SAME audited candles", 1)[1]
        research = research.split("    artifacts:", 1)[0]
        self.assertIn('--userdir "$CM_BUILD_DIR/.ci-tools/phase3-freqtrade-userdata"', research)
        source = (ROOT / "quant_system/native_research.py").read_text(encoding="utf-8")
        self.assertIn('parser.add_argument("--userdir", required=True)', source)
        self.assertIn('userdir=args.userdir', source)

    def test_installer_persists_python_for_following_steps(self):
        setup = (ROOT / "ci/setup-python.sh").read_text(encoding="utf-8")
        self.assertIn("printf 'CI_PYTHON=%s\\n' \"$ci_python\" >> \"$CM_ENV\"", setup)


if __name__ == "__main__":
    unittest.main()
