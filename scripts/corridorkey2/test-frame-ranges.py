"""Selected ranges must preserve source-frame and hint alignment without copying plates."""
from contextlib import ExitStack
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

module_path = Path(__file__).with_name('hint-channels.py')
if not module_path.exists():
    module_path = Path('/opt/corridorkey-launch.py')
spec = importlib.util.spec_from_file_location('frame_ranges', module_path)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class RangeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='range tests ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.plate = self.root / 'plate frames'
        self.hints = self.root / 'roto frames'
        self.plate.mkdir()
        self.hints.mkdir()
        for n in range(9, 13):
            (self.plate / f'shot.v002.{n}.exr').write_bytes(f'plate {n}'.encode())
        for n in range(8, 14):
            (self.hints / f'roto.{n:04}.exr').write_bytes(f'hint {n}'.encode())

    def test_inclusive_range_matches_hint_numbers_and_cleans_links(self):
        args = ['--input', str(self.plate), '--hint_video', str(self.hints),
                '--hint_first_frame', str(self.hints), '--output_dir', 'result']
        with ExitStack() as stack:
            updated = helper.prepare_frame_range(args, 10, 11, stack)
            plate = Path(updated[updated.index('--input') + 1])
            hints = Path(updated[updated.index('--hint_video') + 1])
            first = Path(updated[updated.index('--hint_first_frame') + 1])
            self.assertEqual([p.read_bytes() for p in sorted(plate.iterdir())], [b'plate 10', b'plate 11'])
            self.assertEqual([p.read_bytes() for p in sorted(hints.iterdir())], [b'hint 10', b'hint 11'])
            self.assertEqual([p.read_bytes() for p in first.iterdir()], [b'hint 10'])
            self.assertTrue(all(p.is_symlink() for p in plate.iterdir()))
            self.assertEqual(plate.name, self.plate.name)
        self.assertFalse(plate.exists())
        self.assertEqual(len(list(self.plate.iterdir())), 4)

    def test_single_frame_and_open_ranges_and_equals_syntax(self):
        for start, end, expected in [(10, 10, [10]), (None, 10, [9, 10]), (11, None, [11, 12])]:
            with self.subTest(start=start, end=end), ExitStack() as stack:
                updated = helper.prepare_frame_range(['--input=' + str(self.plate)], start, end, stack)
                staged = Path(updated[0].split('=', 1)[1])
                self.assertEqual([p.read_bytes() for p in sorted(staged.iterdir())],
                                 [f'plate {n}'.encode() for n in expected])

    def test_rejects_ambiguous_or_incomplete_selections(self):
        args = ['--input', str(self.plate)]
        cases = [(args, 12, 10), (args, 8, 10),
                 (args + ['--num_frames', '1'], 10, 11),
                 (args + ['--start_mode', 'middle'], 10, 11),
                 (args + ['--hint_video', str(self.root / 'hint.mov')], 10, 11)]
        for arguments, start, end in cases:
            with self.subTest(arguments=arguments, start=start), ExitStack() as stack:
                with self.assertRaises(ValueError):
                    helper.prepare_frame_range(arguments, start, end, stack)
        (self.hints / 'roto.0010.exr').unlink()
        with ExitStack() as stack, self.assertRaisesRegex(ValueError, 'missing frame'):
            helper.prepare_frame_range(args + ['--hint_video', str(self.hints)], 10, 11, stack)
        (self.plate / 'shot.v002.10.exr').unlink()
        with ExitStack() as stack, self.assertRaisesRegex(ValueError, 'every frame'):
            helper.prepare_frame_range(args, 9, 11, stack)

    def test_rejects_duplicate_and_unnumbered_files(self):
        for filename in ['another.10.exr', 'preview.exr']:
            path = self.plate / filename
            path.touch()
            with self.subTest(filename=filename), self.assertRaises(ValueError):
                helper.numbered_frames(self.plate)
            path.unlink()

    def test_launcher_range_lifetime_and_first_hint_file(self):
        hint = self.root / 'selected-first-frame.exr'
        hint.write_bytes(b'first frame')
        argv = ['corridorkey', '--input', str(self.plate), '--start_frame', '10',
                '--end_frame=11', '--hint_first_frame', str(hint), '--output_dir', 'output']
        staged = []
        def fake_infer(*args, **kwargs):
            actual = helper.sys.argv
            self.assertNotIn('--start_frame', actual)
            self.assertNotIn('--end_frame=11', actual)
            self.assertEqual(actual[actual.index('--hint_first_frame') + 1], str(hint))
            path = Path(actual[actual.index('--input') + 1])
            self.assertEqual(len(list(path.iterdir())), 2)
            staged.append(path)
            raise RuntimeError('simulated inference failure')
        with patch('sys.argv', argv), patch.object(helper.runpy, 'run_path', side_effect=fake_infer):
            with self.assertRaisesRegex(RuntimeError, 'simulated inference failure'):
                helper.main()
        self.assertFalse(staged[0].exists())


@unittest.skipUnless((Path(os.environ.get('CORRIDORKEY_PACKAGE_ROOT', '/opt/CorridorKey')) /
                      'corridorkey/video_io.py').exists(), 'Upstream reader test runs inside container')
class ReaderIntegrationTests(unittest.TestCase):
    def test_upstream_reads_selected_plate_and_hint_exrs(self):
        from corridorkey import video_io as io
        import numpy as np
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
            root = Path(tmp)
            plate, hint = root / 'plate', root / 'hint'
            plate.mkdir()
            hint.mkdir()
            for n in range(1001, 1005):
                image = np.full((2, 2, 3), (n - 1000) / 8, dtype=np.float32)
                self.assertTrue(io.cv2.imwrite(str(plate / f'plate.{n}.exr'), image))
                self.assertTrue(io.cv2.imwrite(str(hint / f'roto.{n}.exr'), image))
            args = helper.prepare_frame_range(['--input', str(plate), '--hint_video', str(hint)], 1002, 1003, stack)
            source = args[args.index('--input') + 1]
            masks = args[args.index('--hint_video') + 1]
            meta = io.probe_frame_dir_meta(source, num_frames=-1, shape_quantum=2,
                fps=24, exr_linear=True, model_scale=1.0)
            self.assertEqual(meta['num_frames'], 2)
            self.assertEqual(meta['native_fps'], 24)
            reader = io.SequentialHintFrameDirWindowReader(masks, meta)
            mattes = reader.window(0, 2).float().numpy()
            for i, expected in enumerate((0.25, 0.375)):
                np.testing.assert_allclose(io.read_image_rgb(meta['frame_paths'][i]), expected)
                np.testing.assert_allclose(mattes[i], expected)
            reader.close()


if __name__ == '__main__':
    unittest.main()
