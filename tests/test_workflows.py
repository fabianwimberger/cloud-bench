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

    def test_benchmark_workflows_pass_instance_selection_via_var_file(self):
        for workflow_path in (
            ".github/workflows/benchmark.yml",
            ".github/workflows/benchmark-all.yml",
        ):
            workflow = pathlib.Path(workflow_path).read_text()

            self.assertNotIn('-var="enabled_instances=', workflow)
            self.assertIn("runtime.auto.tfvars.json", workflow)
            self.assertIn("-var-file=runtime.auto.tfvars.json", workflow)

    def test_benchmark_cleanup_handles_missing_state_artifact(self):
        workflow = pathlib.Path(".github/workflows/benchmark.yml").read_text()

        self.assertIn("if-no-files-found: ignore", workflow)
        self.assertIn("continue-on-error: true", workflow)
        self.assertIn("hashFiles('terraform/terraform.tfstate')", workflow)


if __name__ == "__main__":
    unittest.main()
