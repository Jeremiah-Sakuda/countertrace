"""The reference model must reproduce the specified timing fixtures exactly."""

import json
from pathlib import Path
import unittest

from countertrace.contract import Contract, Edge, ReferenceFifo, classify, reference_steps

TIMING = Path(__file__).resolve().parents[1] / "fixtures" / "timing"


def load(name: str):
    fixture = json.loads((TIMING / name).read_text())
    symbols = fixture["symbols"]
    value = lambda s: None if s is None else symbols[s]
    contract = Contract(depth=fixture["parameters"]["DEPTH"], width=fixture["parameters"]["WIDTH"])
    edges = [Edge(e["rst"], e["wr_en"], e["rd_en"], symbols[e["din"]]) for e in fixture["edges"]]
    return fixture, contract, edges, value


class TimingFixtureTest(unittest.TestCase):
    def check_fixture(self, name: str) -> None:
        fixture, contract, edges, value = load(name)
        steps = reference_steps(contract, edges)
        for spec, step in zip(fixture["edges"], steps, strict=True):
            with self.subTest(cycle=spec["cycle"]):
                self.assertEqual(step.cycle, spec["cycle"])
                pre = None if spec["pre"] is None else [value(s) for s in spec["pre"]]
                self.assertEqual(step.pre_queue, pre)
                self.assertEqual(step.row, spec["row"])
                accepted = (
                    "reset" if step.reset
                    else "both" if step.accepted_read and step.accepted_write
                    else "read" if step.accepted_read
                    else "write" if step.accepted_write
                    else "none"
                )
                self.assertEqual(accepted, spec["accepted"])
                self.assertEqual(step.post_queue, [value(s) for s in spec["post"]])
                self.assertEqual(step.expected_dout, value(spec["dout"]))
                self.assertEqual((step.expected_empty, step.expected_full), (bool(spec["empty"]), bool(spec["full"])))
                self.assertEqual(step.wraps, spec.get("wraps", []))

    def test_depth2_prd_sequence(self):
        self.check_fixture("depth2_prd_sequence.json")

    def test_depth4_wraparound(self):
        self.check_fixture("depth4_wraparound.json")


class ContractRulesTest(unittest.TestCase):
    def test_first_edge_must_reset(self):
        model = ReferenceFifo(Contract(depth=2))
        with self.assertRaises(ValueError):
            model.step(Edge(0, 1, 0, 1))

    def test_unsupported_parameters_rejected(self):
        for depth, width in ((3, 8), (8, 8), (2, 16)):
            with self.assertRaises(ValueError):
                Contract(depth=depth, width=width)

    def test_rows_use_reference_occupancy(self):
        self.assertEqual(classify(Edge(0, 1, 1, 0), 0, 4), "both_empty")
        self.assertEqual(classify(Edge(0, 1, 1, 0), 4, 4), "both_full")
        self.assertEqual(classify(Edge(0, 1, 1, 0), 2, 4), "both_mid")
        self.assertEqual(classify(Edge(1, 1, 1, 0), 4, 4), "reset")

    def test_digest_is_stable_and_parameter_specific(self):
        self.assertEqual(Contract(depth=2).digest(), Contract(depth=2).digest())
        self.assertNotEqual(Contract(depth=2).digest(), Contract(depth=4).digest())

    def test_data_masked_to_width(self):
        steps = reference_steps(Contract(depth=2), [Edge(1, 0, 0, 0), Edge(0, 1, 0, 0x1FF)])
        self.assertEqual(steps[1].post_queue, [0xFF])


if __name__ == "__main__":
    unittest.main()
