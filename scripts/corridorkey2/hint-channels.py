"""Container-only hint channel selection; the pinned upstream source stays intact."""
import argparse
import runpy
import sys
from pathlib import Path

PACKAGE = Path('/opt/CorridorKey')


def parse_channels(value):
    value = value.lower().strip()
    if value == 'auto':
        return value
    aliases = {'red': 'r', 'green': 'g', 'blue': 'b', 'alpha': 'a'}
    value = aliases.get(value, value).replace(',', '')
    if not value or any(c not in 'rgba' for c in value) or len(set(value)) != len(value):
        raise argparse.ArgumentTypeError('Use auto, r, g, b, a, rgb, or a combination such as r,g.')
    return value


def select_channels(image, channels):
    """Select logical RGBA from OpenCV BGR(A); combine masks using max."""
    if image is None:
        raise ValueError('Hint image/frame could not be decoded')
    if image.ndim == 2:
        raise ValueError(f'--hint_channel {channels}: single-channel image has no named RGB/alpha channels; use auto')
    indices = {'b': 0, 'g': 1, 'r': 2, 'a': 3}
    for channel in channels:
        if indices[channel] >= image.shape[2]:
            raise ValueError(f'--hint_channel {channels}: requested {channel} channel is absent')
    return image[..., [indices[c] for c in channels]].max(axis=-1)


def install_channel_selection(video_io, channels):
    """Patch both first-frame image reads and full-shot image/video preprocessing."""
    if channels == 'auto':
        return
    import numpy as np
    cv2 = video_io.cv2
    original_preprocess = video_io.preprocess_hint_frame

    def read_hint_image(path):
        image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
        if image is None:
            raise FileNotFoundError(f'Could not decode hint: {path}')
        hint = select_channels(image, channels)
        if hint.dtype == np.uint8:
            hint = hint.astype(np.float32) / 255.0
        elif hint.dtype == np.uint16:
            hint = hint.astype(np.float32) / 65535.0
        else:
            hint = hint.astype(np.float32)
        return np.clip(hint, 0.0, 1.0)

    def preprocess_hint_frame(frame, meta):
        return original_preprocess(select_channels(frame, channels), meta)

    video_io.read_hint_image = read_hint_image
    video_io.preprocess_hint_frame = preprocess_hint_frame


def main():
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False,
        description='Additional CorridorKey container options (all other arguments pass to infer.py).')
    parser.add_argument('--hint_channel', default='auto', type=parse_channels,
        metavar='auto|r|g|b|a|rgb',
        help='Channel(s) for first-frame and full-shot hints. Combinations (e.g. r,g or rgb) use max. Default auto preserves upstream behaviour.')
    args, remaining = parser.parse_known_args()
    if '--help' in remaining or '-h' in remaining:
        print(parser.format_help(), flush=True)
    elif args.hint_channel != 'auto':
        # The module object is shared with runtime.py and its imported readers.
        from corridorkey import video_io
        install_channel_selection(video_io, args.hint_channel)
        print(f'Hint channels: {args.hint_channel} (multiple channels combined with max)', flush=True)
    sys.argv = [str(PACKAGE / 'infer.py'), *remaining]
    runpy.run_path(sys.argv[0], run_name='__main__')


if __name__ == '__main__':
    main()
