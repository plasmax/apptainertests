#!/usr/local/bin/python
"""Download all CorridorKey 2.0 assets to a portable local directory.

Default destination: /models (bind your host directory here). To download to
another path, pass it as the first argument; bind that directory to /models
when running inference. --check only checks local files and needs no network.
"""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

PACKAGE = Path('/opt/CorridorKey')
REQUIRED = (
    'weights/corridorkey_v2.safetensors',
    'weights/foundation_stats.safetensors',
    'vfms/moge/model.pt',
    'vfms/rvm/pretrain_rvm_small16_256_204031069.npz',
    'vfms/cradio/C-RADIOv4-SO400M/config.json',
    'vfms/cradio/C-RADIOv4-SO400M/hf_model.py',
    'vfms/cradio/C-RADIOv4-SO400M/model.safetensors',
)


def check(root):
    missing = [name for name in REQUIRED
               if not (root / name).is_file() or (root / name).stat().st_size == 0]
    if missing:
        raise RuntimeError('Missing or empty model files:\n  ' + '\n  '.join(missing))


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('directory', nargs='?', default='/models')
    parser.add_argument('--check', action='store_true', help='Check required local files only.')
    parser.add_argument('--revision', help='Optional CorridorKey Hugging Face model revision.')
    args = parser.parse_args()
    root = Path(args.directory).expanduser().resolve()
    if not args.check:
        root.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        # Only this download subprocess opts into online access.
        env['HF_HUB_OFFLINE'] = '0'
        env['TRANSFORMERS_OFFLINE'] = '0'
        command = [sys.executable, str(PACKAGE / 'scripts/download_weights.py'),
                   '--package_root', str(root)]
        if args.revision:
            command.extend(['--corridorkey_revision', args.revision])
        subprocess.run(command, env=env, check=True)
    check(root)
    if not args.check:
        (root / 'corridorkey-container.json').write_text(json.dumps({
            'source_revision': Path('/opt/corridorkey-source-revision').read_text().strip(),
            'corridorkey_model_revision': args.revision or 'main (at download time)',
            'foundation_revisions': 'Pinned in the bundled upstream scripts/download_weights.py',
        }, indent=2) + '\n')
    print(f'Model files present in {root}. Bind this directory to /models for offline inference.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        sys.exit(str(exc))
