import copy
import unittest
from audio_inputs import attach_reference_audio


class AudioWiringTests(unittest.TestCase):
    def graph(self):
        return {"h3": {"class_type": "MiniMaxH3ReferenceToVideo", "inputs": {
            "audio_vae": ["vae", 0], "ref_images.ref_image_0": ["image", 0]}}}

    def test_multiple_audio_and_image_preserved(self):
        graph = self.graph()
        calls = []
        def upload(name, data):
            calls.append((name, data))
            return name
        attach_reference_audio(graph, {"reference_audio": [
            {"data": "YQ==", "filename": "one.wav"},
            {"data": "Yg==", "filename": "two.mp3"}]}, upload, lambda value: value)
        inputs = graph["h3"]["inputs"]
        self.assertEqual(inputs["ref_images.ref_image_0"], ["image", 0])
        for index in range(2):
            link = inputs[f"ref_audios.ref_audio_{index}"]
            self.assertEqual(graph[link[0]]["class_type"], "LoadAudio")
        self.assertEqual(len(calls), 2)
        self.assertTrue(calls[1][0].endswith(".mp3"))

    def test_existing_workflow_unchanged_without_audio(self):
        graph = self.graph()
        original = copy.deepcopy(graph)
        attach_reference_audio(graph, {}, None, None)
        self.assertEqual(graph, original)

    def test_invalid_inputs_fail_before_upload(self):
        for sources in ([], [{}], [{"data": "http://example.com/a.wav"}],
                        [{"data": "YQ==", "filename": "a.exe"}],
                        [{"data": "YQ==", "filename": "a.wav"}] * 4):
            with self.subTest(sources=sources), self.assertRaises(ValueError):
                attach_reference_audio(self.graph(), {"reference_audio": sources},
                                       lambda *_: self.fail("must not upload"), None)

    def test_wrong_model_path_fails(self):
        graph = {"h3": {"class_type": "MiniMaxH3ImageToVideo", "inputs": {}}}
        with self.assertRaises(ValueError):
            attach_reference_audio(graph, {"reference_audio": [{"data": "YQ==", "filename": "a.wav"}]}, None, None)

    def test_existing_audio_cannot_be_overwritten(self):
        graph = self.graph()
        graph["h3"]["inputs"]["ref_audios.ref_audio_0"] = ["existing", 0]
        with self.assertRaises(ValueError):
            attach_reference_audio(graph, {"reference_audio": [{"data": "YQ==", "filename": "a.wav"}]}, None, None)


if __name__ == "__main__":
    unittest.main()
