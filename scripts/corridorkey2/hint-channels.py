"""Container-only hint channel selection; the pinned upstream source stays intact."""
import argparse
from contextlib import ExitStack
import re
import runpy
import sys
import tempfile
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


def numbered_frames(directory):
    """Read the final integer before the extension, e.g. plate.v002.1050.exr."""
    directory = Path(directory).expanduser().resolve()
    if not directory.is_dir():
        raise ValueError(f'Frame ranges require an image-sequence directory: {directory}')
    result = {}
    for path in sorted(directory.iterdir()):
        if not path.is_file() or path.suffix not in ('.exr', '.png', '.jpg', '.jpeg'):
            continue
        match = re.search(r'(\d+)$', path.stem)
        if not match:
            raise ValueError(f'Cannot read frame number from {path.name}; use names such as plate.1050.exr')
        number = int(match.group(1))
        if number in result:
            raise ValueError(f'Duplicate frame {number} in {directory}; use one sequence per directory')
        result[number] = path
    if not result:
        raise ValueError(f'No numbered image frames in {directory}')
    return result


def replace_argument(arguments, option, value):
    arguments = list(arguments)
    for i, argument in enumerate(arguments):
        if argument == option:
            arguments[i + 1] = str(value)
        elif argument.startswith(option + '='):
            arguments[i] = option + '=' + str(value)
    return arguments


def prepare_frame_range(arguments, start, end, stack):
    if start is None and end is None:
        return arguments
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.add_argument('--input', required=True)
    parser.add_argument('--hint_video')
    parser.add_argument('--hint_first_frame')
    parser.add_argument('--num_frames', type=int, default=-1)
    parser.add_argument('--start_mode', default='begin')
    parser.add_argument('--temp_dir')
    opts, _ = parser.parse_known_args(arguments)
    if opts.num_frames != -1 or opts.start_mode != 'begin':
        raise ValueError('Use --start_frame/--end_frame without --num_frames or a non-begin --start_mode')
    plate = numbered_frames(opts.input)
    start = min(plate) if start is None else start
    end = max(plate) if end is None else end
    if start > end:
        raise ValueError('--start_frame must be <= --end_frame (both are inclusive)')
    # A dense, unambiguous range is required; never silently skip missing frames.
    numbers = sorted(n for n in plate if start <= n <= end)
    if not numbers or numbers[0] != start or numbers[-1] != end or len(numbers) != end - start + 1:
        raise ValueError(f'Plate does not contain every frame from {start} to {end}')
    hint = numbered_frames(opts.hint_video) if opts.hint_video and opts.hint_video.lower() not in ('none', 'off', 'null', '-') else None
    if hint is not None:
        missing = [n for n in numbers if n not in hint]
        if missing:
            raise ValueError(f'Full-shot hints are missing frame(s): {missing[:10]}')
    first = None
    if opts.hint_first_frame and Path(opts.hint_first_frame).is_dir():
        first = numbered_frames(opts.hint_first_frame)
        if start not in first:
            raise ValueError(f'First-frame hint directory is missing selected start frame {start}')
    temp_parent = None
    if opts.temp_dir:
        temp_parent = Path(opts.temp_dir).expanduser()
        temp_parent.mkdir(parents=True, exist_ok=True)
    staging = Path(stack.enter_context(tempfile.TemporaryDirectory(prefix='corridorkey-range-', dir=temp_parent)))

    def stage(frames, selected, kind, original):
        # Retain input directory/parent names for upstream output naming.
        original = Path(original).resolve()
        target = staging / kind / original.parent.name / original.name
        target.mkdir(parents=True)
        for number in selected:
            source = frames[number]
            # Fixed padding guarantees numeric order even for unpadded filenames.
            (target / f'frame.{number:020d}{source.suffix}').symlink_to(source)
        return target

    arguments = replace_argument(arguments, '--input', stage(plate, numbers, 'plate', opts.input))
    if hint is not None:
        arguments = replace_argument(arguments, '--hint_video', stage(hint, numbers, 'hint', opts.hint_video))
    if first is not None:
        arguments = replace_argument(arguments, '--hint_first_frame', stage(first, [start], 'first', opts.hint_first_frame))
    print(f'Frame range: {start}-{end} inclusive ({len(numbers)} frames), source: {Path(opts.input).resolve()}', flush=True)
    return arguments


def main():
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False,
        description='Additional CorridorKey container options (all other arguments pass to infer.py).')
    parser.add_argument('--hint_channel', default='auto', type=parse_channels,
        metavar='auto|r|g|b|a|rgb',
        help='Channel(s) for first-frame and full-shot hints. Combinations (e.g. r,g or rgb) use max. Default auto preserves upstream behaviour.')
    parser.add_argument('--start_frame', type=int, help='First filename frame number to process, inclusive (image sequences only).')
    parser.add_argument('--end_frame', type=int, help='Last filename frame number to process, inclusive (image sequences only).')
    args, remaining = parser.parse_known_args()
    if '--help' in remaining or '-h' in remaining:
        print(parser.format_help(), flush=True)
    elif args.hint_channel != 'auto':
        # The module object is shared with runtime.py and its imported readers.
        from corridorkey import video_io
        install_channel_selection(video_io, args.hint_channel)
        print(f'Hint channels: {args.hint_channel} (multiple channels combined with max)', flush=True)
    with ExitStack() as stack:
        if '--help' not in remaining and '-h' not in remaining:
            try:
                remaining = prepare_frame_range(remaining, args.start_frame, args.end_frame, stack)
            except (ValueError, OSError) as exc:
                parser.error(str(exc))
        sys.argv = [str(PACKAGE / 'infer.py'), *remaining]
        runpy.run_path(sys.argv[0], run_name='__main__')


if __name__ == '__main__':
    main()
