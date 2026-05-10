#!/usr/bin/env python3

import json
import subprocess
import unittest


class TestParseInstances(unittest.TestCase):
    def test_trims_spaces_around_commas(self):
        result = subprocess.run(
            [
                "scripts/parse-instances.sh",
                " Standard_B2ls_v2, Standard_B2s_v2 ,Standard_D2as_v7 ",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertEqual(
            json.loads(result.stdout),
            ["Standard_B2ls_v2", "Standard_B2s_v2", "Standard_D2as_v7"],
        )

    def test_rejects_internal_spaces(self):
        result = subprocess.run(
            ["scripts/parse-instances.sh", "Standard_B2 ls_v2"],
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
