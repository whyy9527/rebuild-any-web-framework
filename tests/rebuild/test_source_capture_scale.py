import tempfile,unittest
from pathlib import Path
try:
 from PIL import Image
except ImportError:
 Image = None
from capabilities.rebuild.images import compare_capture
@unittest.skipIf(Image is None, "Pillow unavailable")
class SourceCaptureScale(unittest.TestCase):
 def test_explicit_source_scale_normalizes_but_does_not_hide_wrong_content(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);Image.new('RGB',(8,8),'white').save(root/'source.png');Image.new('RGB',(4,4),'white').save(root/'candidate.png')
   source=dict(content_rect_points=[0,0,4,4],window_points=[4,4],backing_scale=2);candidate=dict(path='candidate.png',content_rect_points=[0,0,4,4],window_points=[4,4],backing_scale=1);req=dict(reference_image='source.png',pixels=[4,4],reference_capture=source)
   self.assertEqual(compare_capture(root,req,dict(capture=candidate))['status'],'pass')
   Image.new('RGB',(4,4),(250,255,255)).save(root/'candidate.png');self.assertEqual(compare_capture(root,req,dict(capture=candidate))['status'],'fail')
   req.pop('reference_capture')
   with self.assertRaises(ValueError):compare_capture(root,req,dict(capture=candidate))
 def test_source_geometry_cannot_be_invented_to_fit_a_different_file(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);Image.new('RGB',(4,4),'white').save(root/'source.png');candidate=dict(path='source.png',content_rect_points=[0,0,4,4],window_points=[4,4],backing_scale=1);req=dict(reference_image='source.png',pixels=[4,4],reference_capture=dict(content_rect_points=[0,0,4,4],window_points=[4,4],backing_scale=2))
   with self.assertRaises(ValueError):compare_capture(root,req,dict(capture=candidate))
   req['reference_capture']['content_rect_points']=[0,1,4,4]
   with self.assertRaises(ValueError):compare_capture(root,req,dict(capture=candidate))

 def test_matching_pixels_do_not_excuse_a_known_state_transition(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);Image.new('RGB',(4,4),'white').save(root/'frame.png');geometry=dict(content_rect_points=[0,0,4,4],window_points=[4,4],backing_scale=1)
   req=dict(reference_image='frame.png',pixels=[4,4],reference_capture=dict(geometry,state_consistent=False));state=dict(capture=dict(geometry,path='frame.png'))
   with self.assertRaises(ValueError):compare_capture(root,req,state)
   req['reference_capture']['state_consistent']=True;state['capture']['state_consistent']=False
   self.assertEqual(compare_capture(root,req,state)['status'],'unavailable')
