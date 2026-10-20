import unittest
from capabilities.rebuild.coverage import coverage


class CoverageChecks(unittest.TestCase):
    def test_unmodeled_control_survives_all_existing_passes(self):
        inventory = {'states': {'home': [{'id': 'login'}, {'id': 'shop'}]},
                     'journeys': [{'id': 'open-login', 'from': 'home', 'action': 'login', 'states': ['login']}]}
        contract = {'requirements': [{'id': 'title', 'state': 'login'}, {'id': 'image', 'state': 'login'}]}
        result = coverage(inventory, contract, {'rows': [{'id': 'title', 'status': 'pass'}, {'id': 'image', 'status': 'fail'}]})
        self.assertEqual([r['status'] for r in result['rows']], ['fail', 'unmodeled'])
        result = coverage(inventory, contract, {'rows': [{'id': 'title', 'status': 'pass'}, {'id': 'image', 'status': 'pass'}]})
        self.assertEqual(result['counts']['unmodeled'], 1)

    def test_same_action_name_in_other_state_does_not_resolve_gap(self):
        inventory = {'states': {'home': [{'id': 'login'}], 'menu': [{'id': 'login'}]},
                     'journeys': [{'id': 'home-login', 'from': 'home', 'action': 'login', 'states': ['form']}]}
        result = coverage(inventory, {'requirements': [{'id': 'form-title', 'state': 'form'}]}, {'rows': []})
        self.assertEqual([r['status'] for r in result['rows']], ['not_run', 'unmodeled'])

    def test_ambiguous_inventory_rejected(self):
        with self.assertRaises(ValueError):
            coverage({'states': {'home': [{'id': 'x'}, {'id': 'x'}]}, 'journeys': []}, {'requirements': []}, {'rows': []})
