"""Guard the experimental contrast: diagnostics must not leak into the control."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('feedback_experiment', ROOT / 'scripts/compare_check_feedback.py')
experiment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(experiment)


class FeedbackComparisonTests(unittest.TestCase):
    def test_arms_share_everything_except_diagnostic_suffix(self):
        for module_id in experiment.SEEDS:
            seed = experiment.seed_record(module_id)
            detailed = experiment.prompt(module_id, 'detailed')
            control = experiment.prompt(module_id, 'rejection_only')
            self.assertTrue(detailed.endswith(seed['feedback']))
            self.assertTrue(control.endswith(experiment.CONTROL))
            self.assertEqual(detailed[:-len(seed['feedback'])], control[:-len(experiment.CONTROL)])
            self.assertNotIn(seed['feedback'], control)

    def test_selected_seeds_are_real_rejections_and_no_golden_source_is_sent(self):
        for module_id in experiment.SEEDS:
            seed = experiment.seed_record(module_id)
            self.assertFalse(seed['gate']['passed'])
            self.assertEqual(seed['gate']['stage'], 'golden')
            self.assertTrue(seed['gate_full']['trace'])
            golden = experiment.modules.load(module_id).golden
            for arm in ['detailed', 'rejection_only']:
                self.assertNotIn(golden, experiment.prompt(module_id,arm))


if __name__ == '__main__':
    unittest.main()
