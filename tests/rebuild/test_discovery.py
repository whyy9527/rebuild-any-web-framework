import tempfile
from pathlib import Path
import unittest

from capabilities.rebuild.discovery import frontier


class DiscoveryFrontier(unittest.TestCase):
    def test_new_menu_actions_remain_pending_and_unavailable_is_not_completion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'observation.txt').write_text('Real observation placeholder for mechanism test')
            history = {'states': [
                {'id': 'home', 'evidence': 'observation.txt', 'actions': [{'id': 'hover-more'}]},
                {'id': 'menu', 'evidence': 'observation.txt', 'actions': [{'id': 'settings'}, {'id': 'help'}]}],
                'transitions': [{'from': 'home', 'action': 'hover-more', 'outcome': 'observed', 'to': 'menu', 'evidence': 'observation.txt'},
                                {'from': 'menu', 'action': 'settings', 'outcome': 'unavailable', 'evidence': 'observation.txt'}]}
            result = frontier(root, history)
            self.assertEqual([row['action']['id'] for row in result['pending']], ['help', 'settings'])
            self.assertEqual(result['resolved_actions'], 1)
            history['transitions'][0]['action'] = 'invented-action'
            with self.assertRaises(ValueError):
                frontier(root, history)

    def test_hover_does_not_complete_click_or_keyboard_exploration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory);(root / 'observed.txt').write_text('Mechanism counterexample, not source product evidence')
            history = {'states': [{'id':'home','evidence':'observed.txt','actions':[{'id':'hearts','operations':['hover','click','Enter']}]}, {'id':'panel','evidence':'observed.txt','actions':[]}],
                'transitions':[{'from':'home','to':'panel','action':'hearts','operation':'hover','outcome':'observed','evidence':'observed.txt'}, {'from':'home','action':'hearts','operation':'Enter','outcome':'unavailable','evidence':'observed.txt'}]}
            result = frontier(root, history)
            self.assertEqual([(r['operation'],r['attempts']) for r in result['pending']], [('click',0),('Enter',1)])
            self.assertEqual(result['resolved_actions'],1)
            history['transitions'][0]['operation']='drag'
            with self.assertRaises(ValueError):frontier(root,history)
