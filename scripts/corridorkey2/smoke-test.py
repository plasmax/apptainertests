"""CPU-only checks: no weights, GPU, network, or existing HF cache required."""
import socket
import tempfile
from pathlib import Path


def no_network(*args, **kwargs):
    raise RuntimeError('Smoke test attempted network access')


socket.socket.connect = no_network
socket.socket.connect_ex = no_network

import cv2
import numpy as np
import torch
import torchvision
import transformers
import timm
import safetensors
from moge.model.v2 import MoGeModel
from corridorkey.runtime import RuntimePaths, load_model

assert torch.__version__.split('+')[0] == '2.9.1'
assert torchvision.__version__.split('+')[0] == '0.24.1'
assert torch.version.cuda == '12.8'
assert Path('/opt/CorridorKey/weights').is_symlink()
assert Path('/opt/CorridorKey/vfms').is_symlink()
assert not list(Path('/models').rglob('*.safetensors'))

# Verify the OpenCV build supports HDR EXR input/output, not just imports.
with tempfile.TemporaryDirectory() as tmp:
    path = str(Path(tmp) / 'hdr.exr')
    image = np.full((2, 2, 3), 2.5, dtype=np.float32)
    assert cv2.imwrite(path, image)
    np.testing.assert_array_equal(cv2.imread(path, cv2.IMREAD_UNCHANGED), image)

print('CPU imports, CUDA wheel version, model-free layout and EXR round-trip passed.')
