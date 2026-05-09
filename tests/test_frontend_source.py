#!/usr/bin/env python3

import pathlib
import unittest


class TestFrontendSource(unittest.TestCase):
    def test_effective_ranking_is_initialized_before_chart_memo(self):
        source = pathlib.Path("frontend/src/App.jsx").read_text()

        self.assertLess(
            source.index("const effectiveRanking = useMemo"),
            source.index("const filteredCharts = useMemo"),
        )


if __name__ == "__main__":
    unittest.main()
