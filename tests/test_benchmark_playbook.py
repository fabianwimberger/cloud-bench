#!/usr/bin/env python3
"""Tests for benchmark playbook wiring."""

import pathlib
import unittest

import yaml


class TestBenchmarkPlaybook(unittest.TestCase):
    def test_pipefail_shell_tasks_use_bash(self):
        playbook_path = (
            pathlib.Path(__file__).resolve().parents[1]
            / "ansible"
            / "playbooks"
            / "benchmark.yml"
        )
        plays = yaml.safe_load(playbook_path.read_text())
        tasks = plays[0]["tasks"][0]["block"]

        pipefail_tasks = [
            task
            for task in tasks
            if "shell" in task and "pipefail" in str(task.get("shell", ""))
        ]

        self.assertGreater(len(pipefail_tasks), 0)
        for task in pipefail_tasks:
            self.assertEqual(task.get("args", {}).get("executable"), "/bin/bash")


if __name__ == "__main__":
    unittest.main()
