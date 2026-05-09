#!/usr/bin/env python3

import pathlib
import unittest


class TestWorkflows(unittest.TestCase):
    def test_benchmark_workflow_does_not_refetch_runner_ip_in_python(self):
        workflow = pathlib.Path(".github/workflows/benchmark.yml").read_text()

        self.assertNotIn("os.popen", workflow)
        self.assertIn('new_ip = os.environ["RUNNER_IP"]', workflow)

    def test_benchmark_summary_is_passed_through_env(self):
        workflow = pathlib.Path(".github/workflows/benchmark.yml").read_text()

        self.assertIn("BENCHMARK_SUMMARY:", workflow)
        self.assertIn("process.env.BENCHMARK_SUMMARY", workflow)
        self.assertNotIn(
            "const summary = `${{ needs.process.outputs.summary }}`", workflow
        )

    def test_benchmark_all_destroy_failures_are_not_suppressed(self):
        workflow = pathlib.Path(".github/workflows/benchmark-all.yml").read_text()

        self.assertNotIn(
            'allowed_ssh_ips=[\\"${{ steps.get_ip.outputs.ip }}/32\\"]" || true',
            workflow,
        )


if __name__ == "__main__":
    unittest.main()
