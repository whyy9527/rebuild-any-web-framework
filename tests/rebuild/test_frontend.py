import tempfile
from pathlib import Path
import unittest

from capabilities.rebuild.frontend import compare


class FrontendRequirements(unittest.TestCase):
    def test_empty_input_requires_measured_string_and_detects_retained_value(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'reference.txt').write_text('Source page input clears after Enter')
            requirement = {'id': 'page-value', 'state': 'submitted', 'kind': 'element_value',
                           'element': 'page-input', 'value': '', 'evidence': ['reference.txt']}
            for value, expected in [('', 'pass'), ('0', 'fail'), (0, 'unavailable'), (None, 'unavailable')]:
                observed = {'states': {'submitted': {'elements': {'page-input': {'value': value}}}}}
                self.assertEqual(compare(root, {'requirements': [requirement]}, observed)['rows'][0]['status'], expected)
            missing = {'states': {'submitted': {'elements': {}}}}
            self.assertEqual(compare(root, {'requirements': [requirement]}, missing)['rows'][0]['status'], 'unavailable')
            with self.assertRaises(ValueError):
                compare(root, {'requirements': [{**requirement, 'value': None}]}, missing)

    def test_semantic_success_does_not_hide_frontend_mismatch_or_unvisited_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'reference.txt').write_text('Observed reference home and menu')
            contract = {'requirements': [
                {'id': 'unit', 'state': 'home', 'kind': 'accessible_text', 'text': 'Order at a café', 'evidence': ['reference.txt']},
                {'id': 'settings', 'state': 'more-open', 'kind': 'accessible_text', 'text': 'Settings', 'evidence': ['reference.txt']},
                {'id': 'visual', 'state': 'home', 'kind': 'pending', 'description': 'Unimplemented visual comparison', 'evidence': ['reference.txt']}]}
            observed = {'semantic_status': 'pass', 'states': {'home': {'accessible_text': ['Small beginnings']}}}
            result = compare(root, contract, observed)
            self.assertEqual(result['status'], 'fail')
            self.assertEqual([row['status'] for row in result['rows']], ['fail', 'not_run', 'not_run'])
            observed['states']['home']['accessible_text'] = ['Order at a café']
            observed['states']['more-open'] = {'accessible_text': ['Settings']}
            self.assertEqual(compare(root, contract, observed)['status'], 'fail')
            contract['requirements'].pop()
            self.assertEqual(compare(root, contract, observed)['status'], 'pass')

    def test_interaction_requires_observed_boolean_and_failed_action_stays_failed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'reference.txt').write_text('Hover opens, moving out dismisses')
            contract = {'requirements': [{'id': 'hover', 'state': 'home',
                'kind': 'interaction_boolean', 'field': 'opened', 'expected': True,
                'evidence': ['reference.txt']}]}
            for actual, expected in [(None, 'unavailable'), (1, 'unavailable'), (False, 'fail'), (True, 'pass')]:
                observed = {'states': {'home': {'interactions': {'opened': actual}}}}
                self.assertEqual(compare(root, contract, observed)['rows'][0]['status'], expected)

    def test_control_geometry_rejects_displacement_and_missing_measurement(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'reference.txt').write_text('Measured content-relative switch rectangle')
            contract = {'requirements': [{'id': 'switch', 'state': 'settings',
                'kind': 'element_geometry', 'element': 'sound', 'rect': [704, 174, 56, 32],
                'tolerance_points': 1, 'evidence': ['reference.txt']}]}
            for actual, expected in [([704, 174.5, 56, 32], 'pass'), ([704, 190, 56, 32], 'fail'), (None, 'unavailable')]:
                observed = {'states': {'settings': {'elements': {'sound': {'rect': actual}}}}}
                self.assertEqual(compare(root, contract, observed)['rows'][0]['status'], expected)

    def test_identical_copy_cannot_hide_wrong_radio_role_or_enabled_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'reference.txt').write_text('Source feedback: radio 2 checked and disabled')
            contract = {'requirements': [
                {'id': 'role', 'state': 'feedback', 'kind': 'element_role', 'element': 'option-1', 'role': 'radio', 'evidence': ['reference.txt']},
                {'id': 'disabled', 'state': 'feedback', 'kind': 'element_boolean', 'element': 'option-1', 'field': 'enabled', 'expected': False, 'evidence': ['reference.txt']}]}
            for role in ['radio', 'AXRadioButton']:
                observed = {'states': {'feedback': {'accessible_text': ['2'], 'elements': {'option-1': {'role': role, 'enabled': False}}}}}
                self.assertEqual(compare(root, contract, observed)['status'], 'pass')
            observed['states']['feedback']['elements']['option-1'] = {'role': 'AXButton', 'enabled': True}
            self.assertEqual([x['status'] for x in compare(root, contract, observed)['rows']], ['fail', 'fail'])
            observed['states']['feedback']['elements']['option-1'] = {'role': None, 'enabled': None}
            self.assertEqual([x['status'] for x in compare(root, contract, observed)['rows']], ['unavailable', 'unavailable'])

    def test_checked_state_requires_boolean_measurement_and_detects_wrong_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'reference.txt').write_text('Source radio 2 checked in accepted feedback')
            contract = {'requirements': [{'id': 'checked', 'state': 'feedback',
                'kind': 'element_boolean', 'element': 'option-1', 'field': 'checked',
                'expected': True, 'evidence': ['reference.txt']}]}
            for value, expected in [(True, 'pass'), (False, 'fail'), (1, 'unavailable'), (None, 'unavailable')]:
                observed = {'states': {'feedback': {'elements': {'option-1': {'checked': value}}}}}
                self.assertEqual(compare(root, contract, observed)['rows'][0]['status'], expected)

    def test_pixel_color_requires_rgb_measurement_and_rejects_wrong_feedback_color(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'reference.txt').write_text('Actual source correct-option background sampled from PNG')
            contract = {'requirements': [{'id': 'color', 'state': 'feedback', 'kind': 'pixel_color',
                'point': [850, 500], 'rgb': [215, 255, 184], 'evidence': ['reference.txt']}]}
            for rgb, expected in [([215, 255, 184], 'pass'), ([229, 247, 252], 'fail'),
                                  (True, 'unavailable'), ([215, True, 184], 'unavailable'), (None, 'unavailable')]:
                observed = {'states': {'feedback': {'pixel_color_space': 'sRGB', 'pixel_samples': {'850,500': rgb}}}}
                self.assertEqual(compare(root, contract, observed)['rows'][0]['status'], expected)

            observed['states']['feedback'] = {'pixel_samples': {'850,500': [215, 255, 184]}}
            self.assertEqual(compare(root, contract, observed)['rows'][0]['status'], 'unavailable')

    def test_image_requirement_reads_pixels_instead_of_driver_pass_flags(self):
        from capabilities.rebuild.images import compare_capture
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            try:
                from PIL import Image
            except ImportError:
                self.assertEqual(compare_capture(root, {}, {})['status'], 'unavailable')
                return
            Image.new('RGB', (4, 4), 'white').save(root / 'source.png')
            # A measured two-pixel titlebar must be cropped, not compared.
            candidate = Image.new('RGB', (4, 6), 'black')
            candidate.paste((255, 255, 255), (0, 2, 4, 6))
            candidate.save(root / 'candidate.png')
            contract = {'requirements': [{'id': 'pixels', 'state': 'page', 'kind': 'image_pixels',
                'reference_image': 'source.png', 'pixels': [4, 4], 'evidence': ['source.png']}]}
            state = {'status': 'pass', 'capture': {'path': 'candidate.png', 'content_rect_points': [0, 2, 4, 4],
                     'backing_scale': 1, 'window_points': [4, 6]}}
            observed = {'states': {'page': state}}
            self.assertEqual(compare(root, contract, observed)['status'], 'pass')
            candidate.putpixel((2, 3), (254, 255, 255)); candidate.save(root / 'candidate.png')
            result = compare(root, contract, observed)
            self.assertEqual(result['status'], 'fail')
            self.assertGreater(result['rows'][0]['mean_absolute_rgb_difference'][0], 0)
            state['capture']['path'] = 'missing.png'
            self.assertEqual(compare(root, contract, observed)['rows'][0]['status'], 'unavailable')
            state.pop('capture')
            self.assertEqual(compare(root, contract, observed)['rows'][0]['status'], 'unavailable')

    def test_image_geometry_and_workspace_boundary_cannot_be_bypassed(self):
        from capabilities.rebuild.images import compare_capture
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            try:
                from PIL import Image
            except ImportError:
                self.assertEqual(compare_capture(root, {}, {})['status'], 'unavailable')
                return
            Image.new('RGB', (4, 4), 'white').save(root / 'source.png')
            requirement = {'reference_image': 'source.png', 'pixels': [4, 4]}
            capture = {'path': 'source.png', 'content_rect_points': [0, 1, 4, 4], 'backing_scale': 1, 'window_points': [4, 4]}
            self.assertEqual(compare_capture(root, requirement, {'capture': capture})['status'], 'unavailable')
            capture['content_rect_points'] = [0, 0, 4, 4]
            capture['backing_scale'] = 2
            self.assertEqual(compare_capture(root, requirement, {'capture': capture})['status'], 'unavailable')
            capture['backing_scale'] = 1; capture['path'] = '../outside.png'
            with self.assertRaises(ValueError):
                compare_capture(root, requirement, {'capture': capture})

    def test_missing_image_dependency_is_unavailable_not_success(self):
        from unittest.mock import patch
        from capabilities.rebuild.images import compare_capture
        with patch.dict('sys.modules', {'PIL': None}):
            self.assertEqual(compare_capture(Path('.'), {}, {})['status'], 'unavailable')

    def test_relative_geometry_measures_actual_motion_not_a_driver_pass_flag(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'source.txt').write_text('Actual card mouse-down moves two points; mouse-up restores origin')
            requirement = {'id': 'down', 'state': 'pressed', 'relative_to_state': 'idle',
                'kind': 'element_geometry', 'element': 'card', 'rect': [0, 2, 0, 0],
                'tolerance_points': 0, 'evidence': ['source.txt']}
            observed = {'states': {'idle': {'elements': {'card': {'rect': [10, 20, 40, 68]}}},
                'pressed': {'status': 'pass', 'elements': {'card': {'rect': [10, 20, 40, 68]}}}}}
            contract = {'requirements': [requirement]}
            self.assertEqual(compare(root, contract, observed)['rows'][0]['status'], 'fail')
            observed['states']['pressed']['elements']['card']['rect'][1] = 22
            self.assertEqual(compare(root, contract, observed)['rows'][0]['status'], 'pass')
            observed['states']['idle']['elements']['card']['rect'][1] = True
            self.assertEqual(compare(root, contract, observed)['rows'][0]['status'], 'unavailable')
            observed['states'].pop('idle')
            self.assertEqual(compare(root, contract, observed)['rows'][0]['status'], 'not_run')

    def test_native_link_role_is_distinct_from_button(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'reference.txt').write_text('Actual Practice Start is a DOM link')
            contract = {'requirements': [{'id': 'start-role', 'state': 'entry', 'kind': 'element_role',
                'element': 'start', 'role': 'link', 'evidence': ['reference.txt']}]}
            element = {'role': 'AXLink'}
            observed = {'states': {'entry': {'elements': {'start': element}}}}
            self.assertEqual(compare(root, contract, observed)['rows'][0]['status'], 'pass')
            element['role'] = 'AXButton'
            self.assertEqual(compare(root, contract, observed)['rows'][0]['status'], 'fail')
            element.clear()
            self.assertEqual(compare(root, contract, observed)['rows'][0]['status'], 'unavailable')

    def test_native_textbox_role_does_not_accept_static_text(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'reference.txt').write_text('Observed editable age input')
            contract = {'requirements': [{'id': 'age', 'state': 'form', 'kind': 'element_role', 'element': 'age', 'role': 'textbox', 'evidence': ['reference.txt']}]}
            element = {'role': 'AXTextField'}
            observed = {'states': {'form': {'elements': {'age': element}}}}
            self.assertEqual(compare(root, contract, observed)['rows'][0]['status'], 'pass')
            element['role'] = 'AXStaticText'
            self.assertEqual(compare(root, contract, observed)['rows'][0]['status'], 'fail')
