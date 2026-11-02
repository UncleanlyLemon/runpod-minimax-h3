import asyncio, importlib.util, json, sys, types, unittest
from pathlib import Path
from unittest.mock import patch, AsyncMock
sys.modules.setdefault('runpod',types.ModuleType('runpod'))
import handler

class ResultsTests(unittest.TestCase):
    def test_partial_node_rejection_is_not_success(self):
        response={'prompt_id':'p','node_errors':{'126':{'errors':[{'message':'missing required input'}]}}}
        with patch.object(handler,'_http',return_value=json.dumps(response).encode()):
            with self.assertRaisesRegex(RuntimeError,'rejected workflow nodes'):
                asyncio.run(handler._queue_and_wait({}))
    def test_empty_media_is_failure(self):
        history={'status':{'completed':True,'status_str':'success','messages':[]},'outputs':{}}
        with patch.object(handler,'_ensure_comfy',new=AsyncMock()),patch.object(handler,'_prune_volume_outputs'),patch.object(handler,'_patch',return_value={}),patch.object(handler,'_queue_and_wait',new=AsyncMock(return_value=history)),patch.object(handler,'_collect_outputs',return_value=([],{})),patch.object(handler,'_collect_new_files',return_value=[]):
            with self.assertRaisesRegex(RuntimeError,'No media was produced'):
                asyncio.run(handler.handler({'id':'test','input':{'prompt_graph':{}}}))
    def test_saved_media_is_returned(self):
        media=[{'filename':'clip.mp4','b64':'test'}]
        with patch.object(handler,'_ensure_comfy',new=AsyncMock()),patch.object(handler,'_prune_volume_outputs'),patch.object(handler,'_patch',return_value={}),patch.object(handler,'_queue_and_wait',new=AsyncMock(return_value={'outputs':{'126':{}}})),patch.object(handler,'_collect_outputs',return_value=(media,{})):
            self.assertEqual(asyncio.run(handler.handler({'id':'test','input':{'prompt_graph':{}}}))['outputs'],media)
