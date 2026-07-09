"""Minimal functional tests for the pure instrument layer.

The model smoke test is the real integration gate. These tests cover the pure pieces the smoke test
does not isolate cleanly: nominal vs ordinal reducers, frame canonicalization/keying, readout names,
and packaged data integrity.
"""
from __future__ import annotations

import unittest

import numpy as np

from moralmaps.data import CONFIGS, CONDITIONS, load_vignettes
from moralmaps.instrument import (
    Instrument,
    canonicalize_to_forward,
    per_item_categorical,
    reduce_nominal,
    reduce_ordinal,
)
from moralmaps.readouts import expected_score, logit_contrast, logodds_agree


class InstrumentFlowTest(unittest.TestCase):
    def test_nominal_flow_reduces_answer_categories_to_profile(self) -> None:
        instr = Instrument(
            "mfv", "salience", "nominal",
            ["care", "fairness", "social"],
            ["Care", "Fairness", "SocialNorms"],
            items=[],
            prefill='This is wrong because {"violation": "',
            answer_to_dim={"care": "Care", "fairness": "Fairness", "social": "SocialNorms"},
        )
        rows = [
            {"id": "a", "frame": "forward", "lp": np.log([0.80, 0.15, 0.05]),
             "p": np.array([0.80, 0.15, 0.05]), "pmass_allowed": 0.95,
             "dimension": None, "sign": 1, "human_label": None},
            {"id": "b", "frame": "forward", "lp": np.log([0.20, 0.50, 0.30]),
             "p": np.array([0.20, 0.50, 0.30]), "pmass_allowed": 0.90,
             "dimension": None, "sign": 1, "human_label": None},
        ]

        items = per_item_categorical(rows, instr.kind)

        self.assertTrue(np.allclose(reduce_nominal(items, instr), [0.50, 0.325, 0.175]))
        self.assertAlmostEqual(items["a"]["pmass"], 0.95)
        self.assertEqual(items["a"]["n_frames"], 1)

    def test_ordinal_flow_canonicalizes_frames_then_keys_profile(self) -> None:
        instr = Instrument(
            "likert", "endorsement", "ordinal",
            ["1", "2", "3", "4", "5"],
            ["care", "authority"],
            items=[],
            prefill="(",
        )
        onehot = {d: np.eye(5)[d - 1] for d in range(1, 6)}
        rows = [
            {"id": "care", "frame": "forward", "lp": np.log(onehot[4] + 1e-9),
             "p": onehot[4], "pmass_allowed": 1.0,
             "dimension": "care", "sign": 1, "human_label": None},
            {"id": "authority", "frame": "inverted", "lp": np.log(onehot[5] + 1e-9),
             "p": onehot[5], "pmass_allowed": 1.0,
             "dimension": "authority", "sign": -1, "human_label": None},
        ]

        items = per_item_categorical(rows, instr.kind)
        profile = reduce_ordinal(items, instr)

        self.assertTrue(np.array_equal(canonicalize_to_forward(onehot[5], "inverted", "ordinal"), onehot[1]))
        self.assertAlmostEqual(expected_score(items["care"]["p"], 5), 4.0)
        self.assertAlmostEqual(profile[0], 4.0)
        self.assertAlmostEqual(profile[1], 5.0)
        self.assertAlmostEqual(
            logit_contrast(items["care"]["lp"] + 100.0, 5),
            logit_contrast(items["care"]["lp"], 5),
        )
        self.assertTrue(np.isfinite(logodds_agree(items["care"]["lp"], 5)))

    def test_packaged_vignettes_have_aligned_conditions_and_labels(self) -> None:
        required_human = {
            "human_Care", "human_Fairness", "human_Loyalty", "human_Authority",
            "human_Sanctity", "human_Liberty", "human_SocialNorms",
        }
        for cfg in CONFIGS:
            rows = load_vignettes(cfg)
            self.assertGreaterEqual(len(rows), 100)
            self.assertEqual({r["set"] for r in rows}, {cfg})
            for row in rows:
                self.assertTrue({"id", "foundation", "foundation_coarse", *CONDITIONS} <= set(row))
                self.assertTrue(required_human <= set(row))
                self.assertGreater(sum(float(row[k]) for k in required_human), 0.0)


if __name__ == "__main__":
    unittest.main()
