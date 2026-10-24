"""Channel semantics locally; real EXR/reader integration inside the image."""
import argparse
import importlib.util
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

import numpy as np

module_path = Path(__file__).with_name('hint-channels.py')
if not module_path.exists():
    module_path = Path('/opt/corridorkey-launch.py')
spec = importlib.util.spec_from_file_location('hint_channels', module_path)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class ChannelTests(unittest.TestCase):
    def test_channel_names_and_combinations(self):
        for value, expected in [('red', 'r'), ('GREEN', 'g'), ('blue', 'b'),
                                ('alpha', 'a'), ('r,g', 'rg'), ('rgb', 'rgb'), ('auto', 'auto')]:
            with self.subTest(value=value):
                self.assertEqual(helper.parse_channels(value), expected)
        for value in ('', 'rr', 'yellow', 'r,x'):
            with self.subTest(value=value), self.assertRaises(argparse.ArgumentTypeError):
                helper.parse_channels(value)

    def test_bgra_order_and_union(self):
        # Deliberately different channels, with green larger than red at pixel 2.
        image = np.array([[[0.1, 0.2, 0.8, 1.0], [0.2, 0.7, 0.3, 1.0]]])
        for channel, expected in [('r', [[0.8, 0.3]]), ('g', [[0.2, 0.7]]),
                                  ('b', [[0.1, 0.2]]), ('a', [[1, 1]]),
                                  ('rgb', [[0.8, 0.7]]), ('rg', [[0.8, 0.7]])]:
            with self.subTest(channel=channel):
                np.testing.assert_array_equal(helper.select_channels(image, channel), expected)
        with self.assertRaisesRegex(ValueError, 'absent'):
            helper.select_channels(image[..., :3], 'a')
        with self.assertRaisesRegex(ValueError, 'single-channel'):
            helper.select_channels(image[..., 0], 'r')

    def test_normalization_and_preprocess_selection(self):
        for dtype, scale in [(np.uint8, 255), (np.uint16, 65535), (np.float32, 1)]:
            image = np.array([[[0, scale, 0, scale]]], dtype=dtype)
            io = types.SimpleNamespace(
                cv2=types.SimpleNamespace(imread=lambda *args: image, IMREAD_UNCHANGED=-1),
                read_hint_image=lambda p: None,
                preprocess_hint_frame=lambda frame, meta: frame)
            helper.install_channel_selection(io, 'g')
            np.testing.assert_array_equal(io.read_hint_image('fixture'), [[1.0]])
            # Full-shot readers receive a single channel and retain upstream scaling.
            np.testing.assert_array_equal(io.preprocess_hint_frame(image, {}), [[scale]])

    def test_auto_preserves_original_readers(self):
        io = types.SimpleNamespace(read_hint_image=object(), preprocess_hint_frame=object())
        originals = (io.read_hint_image, io.preprocess_hint_frame)
        helper.install_channel_selection(io, 'auto')
        self.assertEqual(originals, (io.read_hint_image, io.preprocess_hint_frame))

    def test_cli_removes_only_channel_option(self):
        argv = ['corridorkey', '--hint_channel', 'auto', '--input', 'plate with spaces',
                '--hint_first_frame', 'hint.exr', '--output_dir', 'output']
        with patch('sys.argv', argv), patch.object(helper.runpy, 'run_path') as run:
            helper.main()
            self.assertEqual(helper.sys.argv[1:], argv[3:])
            run.assert_called_once_with('/opt/CorridorKey/infer.py', run_name='__main__')


@unittest.skipUnless((Path(os.environ.get('CORRIDORKEY_PACKAGE_ROOT', '/opt/CorridorKey')) /
                      'corridorkey/video_io.py').exists(),
                     'Real EXR and upstream reader checks run inside the container')
class ExrIntegrationTests(unittest.TestCase):
    def test_first_frame_and_full_shot_use_identical_selected_mattes(self):
        from corridorkey import video_io as io
        import torch
        image = np.zeros((2, 2, 4), dtype=np.float32)
        image[..., 0] = 0.125  # B
        image[..., 1] = 0.5    # G
        image[..., 2] = 0.75   # R
        image[..., 3] = 1.0    # A: must not override an explicit RGB selection
        meta = {'shape_hw': (2, 2), 'model_native_hw': (2, 2), 'native_hw': (2, 2),
                'pad': (0, 0, 0, 0), 'num_frames': 1}
        original_read, original_preprocess = io.read_hint_image, io.preprocess_hint_frame
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'roto.1001.exr'
            self.assertTrue(io.cv2.imwrite(str(path), image))
            for channels, expected in [('r', 0.75), ('g', 0.5), ('b', 0.125),
                                       ('a', 1.0), ('rgb', 0.75), ('gb', 0.5)]:
                with self.subTest(channels=channels), \
                     patch.object(io, 'read_hint_image', original_read), \
                     patch.object(io, 'preprocess_hint_frame', original_preprocess):
                    helper.install_channel_selection(io, channels)
                    first = io.load_initial_hint_frame(str(path), meta)
                    reader = io.SequentialHintFrameDirWindowReader(tmp, meta)
                    full = reader.window(0, 1)[0]
                    reader.close()
                    torch.testing.assert_close(first, torch.full_like(first, expected))
                    torch.testing.assert_close(full, first)


if __name__ == '__main__':
    unittest.main()
