"""Test download dispatch and offline checks without fetching model bytes."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('download_models',
    Path(__file__).with_name('download-models.py'))
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class DownloadTests(unittest.TestCase):
    def test_offline_check_does_not_download_and_reports_missing_files(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(helper.subprocess, 'run') as run:
            with patch('sys.argv', ['download-models', tmp, '--check']):
                with self.assertRaisesRegex(RuntimeError, 'Missing or empty model files'):
                    helper.main()
            run.assert_not_called()
            for name in helper.REQUIRED:
                dest = Path(tmp) / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(b'test fixture')
            with patch('sys.argv', ['download-models', tmp, '--check']):
                helper.main()
            run.assert_not_called()

    def test_download_uses_external_directory_and_only_child_goes_online(self):
        with tempfile.TemporaryDirectory(prefix='models with spaces ') as tmp:
            root = Path(tmp)
            revision = root / 'source-revision'
            revision.write_text('test-source-sha\n')
            def fake_download(command, *, env, check):
                self.assertEqual(command[command.index('--package_root') + 1], tmp)
                self.assertEqual(command[-2:], ['--corridorkey_revision', 'model-sha'])
                self.assertEqual(env['HF_HUB_OFFLINE'], '0')
                self.assertEqual(env['TRANSFORMERS_OFFLINE'], '0')
                self.assertTrue(check)
                for name in helper.REQUIRED:
                    dest = root / name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(b'test fixture')
            # Replace only the source-revision path, leaving real filesystem IO intact.
            original_path = helper.Path
            def path(value):
                return revision if value == '/opt/corridorkey-source-revision' else original_path(value)
            with patch.dict(os.environ, {'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1'}):
                with patch.object(helper, 'Path', side_effect=path), \
                     patch.object(helper.subprocess, 'run', side_effect=fake_download), \
                     patch('sys.argv', ['download-models', tmp, '--revision', 'model-sha']):
                    helper.main()
                self.assertEqual(os.environ['HF_HUB_OFFLINE'], '1')
                self.assertEqual(os.environ['TRANSFORMERS_OFFLINE'], '1')
            self.assertIn('model-sha', (root / 'corridorkey-container.json').read_text())


if __name__ == '__main__':
    unittest.main()
