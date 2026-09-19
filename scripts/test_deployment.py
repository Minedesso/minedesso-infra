"""Offline tests: never contact Docker, SSH, sudo, or a real deployment directory."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


BASH = os.environ.get("TEST_BASH") or shutil.which("bash")
SCRIPTS = Path(__file__).resolve().parent


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.env = dict(os.environ)
        self.env["TEST_ROOT"] = self.root.as_posix()
        self.env["FAIL_COMMAND"] = ""
        self.root.joinpath(".env").write_text("LOBBY_VERSION=old\n")

    def run_script(self, name, *args):
        script = SCRIPTS.joinpath(name).read_text()
        script = script.replace("cd /opt/minecraft-dev", 'cd "$TEST_ROOT"')
        script = script.replace("/run/lock/minedesso-deploy.lock", '"$TEST_ROOT/lock"')
        # Bash functions replace all privileged/external deployment operations.
        mocks = r'''
docker() {
  printf '%s\n' "$*" >> "$TEST_ROOT/calls"
  if [[ -n $FAIL_COMMAND && " $* " == *" $FAIL_COMMAND "* ]]; then return 1; fi
}
flock() { :; }
mktemp() { printf '%s\n' '.candidate'; }
rm() { :; }
mv() { printf '%s\n' 'saved' >> "$TEST_ROOT/calls"; }
'''
        return subprocess.run(
            [BASH, "-c", mocks + "\n" + script, name, *args],
            env=self.env, capture_output=True, text=True,
        )

    def calls(self):
        path = self.root / "calls"
        return path.read_text().splitlines() if path.exists() else []

    def test_success_pulls_before_restart_and_saves_after_healthcheck(self):
        result = self.run_script("deploy-minecraft", "run-123-1")
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.calls()
        self.assertEqual(len(calls), 3)
        self.assertIn("pull lobby citybuild islewars", calls[0])
        self.assertIn("--force-recreate --wait --wait-timeout 300", calls[1])
        self.assertEqual(calls[2], "saved")
        self.assertEqual(self.root.joinpath(".candidate").read_text(),
                         "LOBBY_VERSION=run-123-1\nCITYBUILD_VERSION=run-123-1\nISLEWARS_VERSION=run-123-1\n")

    def test_pull_failure_never_restarts(self):
        self.env["FAIL_COMMAND"] = "pull"
        result = self.run_script("deploy-minecraft", "run-123-1")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(len(self.calls()), 1)

    def test_unhealthy_deployment_does_not_save_version(self):
        self.env["FAIL_COMMAND"] = "up"
        result = self.run_script("deploy-minecraft", "run-123-1")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(len(self.calls()), 2)

    def test_rejects_invalid_arguments_before_docker(self):
        for args in [(), ("latest",), ("run-1-1;id",), ("run-1-1", "extra")]:
            with self.subTest(args=args):
                result = self.run_script("deploy-minecraft", *args)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(self.calls(), [])

    def test_ssh_rejects_shell_and_injection(self):
        for command in ["", "sh", "deploy-minecraft latest", "deploy-minecraft run-1-1; id",
                        "deploy-minecraft run-1-1\nwhoami"]:
            with self.subTest(command=command):
                self.env["SSH_ORIGINAL_COMMAND"] = command
                result = self.run_script("minecraft-ssh")
                self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
