"""Shape rotation checks in validate_proposal.check. Run: python3 -m unittest discover scripts"""

import unittest
from datetime import date

from common import load_config
from validate_proposal import check

CFG = load_config()
PILLARS = ["P1", "P2", "P3", "P4", "P5", "P6"]
LENSES = ["L1", "L2", "L3", "L4", "L5", "L6"]
TODAY = date(2026, 11, 10)


def sheet(posted_shapes):
    """Posted rows on the Saturdays before TODAY, oldest first; '' means no shape."""
    days = ["2026-10-17", "2026-10-24", "2026-10-31", "2026-11-07"][-len(posted_shapes):] if posted_shapes else []
    rows = [{"row": 22 + i, "date": d, "pillar": PILLARS[i], "lens": LENSES[i], "topic": f"old {i}",
             "status": CFG["status"]["posted"], "rationale": "", "source": "Me", "url": "", "shape": s}
            for i, (d, s) in enumerate(zip(days, posted_shapes))]
    return {"pillars": PILLARS, "lenses": LENSES, "schedule": rows}


def queue(shapes):
    days = ["2026-11-14", "2026-11-21", "2026-11-28"]
    return {"queue": [{"date": d, "pillar": PILLARS[4 + i % 2], "lens": LENSES[4 + i % 2], "topic": f"new idea {i}",
                       "shape": s, "rationale": "r", "test": "t", "origin_row": None}
                      for i, (d, s) in enumerate(zip(days, shapes))], "drops": []}


def shape_errors(posted, shapes):
    errors, _ = check(sheet(posted), queue(shapes), CFG, TODAY)
    return [e for e in errors if "shape" in e]


class ShapeRules(unittest.TestCase):
    def test_varied_shapes_pass(self):
        self.assertEqual(shape_errors(["E", "D", "A"], ["C", "B", "E"]), [])

    def test_missing_or_unknown_shape(self):
        self.assertEqual(len(shape_errors([], ["F", None])), 2)

    def test_back_to_back_after_posted(self):
        self.assertIn("2026-11-07 and 2026-11-14: shape A on back-to-back Saturdays", shape_errors(["A"], ["A"]))

    def test_three_in_four_saturdays(self):
        errs = shape_errors(["E", "", "E"], ["C", "E"])
        self.assertTrue(any("shape 'E' appears 3 times in a 6-Saturday window" in e for e in errs), errs)

    def test_old_posts_without_shape_are_ignored(self):
        self.assertEqual(shape_errors(["", "", ""], ["A", "B", "C"]), [])


if __name__ == "__main__":
    unittest.main()
