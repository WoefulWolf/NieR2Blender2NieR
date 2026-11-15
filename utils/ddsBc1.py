import struct

import numpy as np


def expandBits(code, bits):
    return ((code << (8 - bits)) | (code >> (2 * bits - 8))) / 255.0


def encodeLevel(level):
    height, width = level.shape
    paddedHeight, paddedWidth = (height + 3) // 4 * 4, (width + 3) // 4 * 4
    level = np.pad(level, ((0, paddedHeight - height), (0, paddedWidth - width)), mode='edge')
    blocks = level.reshape(paddedHeight // 4, 4, paddedWidth // 4, 4).transpose(0, 2, 1, 3).reshape(-1, 16)
    high, low = blocks.max(1), blocks.min(1)
    greenHigh, greenLow = np.round(high * 63).astype(np.int64), np.round(low * 63).astype(np.int64)
    redHigh, redLow = np.round(high * 31).astype(np.int64), np.round(low * 31).astype(np.int64)
    color0 = (redHigh << 11) | (greenHigh << 5) | redHigh
    color1 = (redLow << 11) | (greenLow << 5) | redLow
    first, second = expandBits(greenHigh, 6), expandBits(greenLow, 6)
    palette = np.stack([first, second, (2 * first + second) / 3, (first + 2 * second) / 3], axis=1)
    indices = np.abs(blocks[:, :, None] - palette[:, None, :]).argmin(2)
    indices[color0 == color1] = 0
    packed = (indices.astype(np.uint64) << (2 * np.arange(16, dtype=np.uint64))).sum(1)
    out = np.empty(len(blocks), dtype=[('color0', '<u2'), ('color1', '<u2'), ('indices', '<u4')])
    out['color0'], out['color1'], out['indices'] = color0, color1, packed
    return out.tobytes()


def writeGreyBc1Dds(path, values):
    level = np.clip(np.asarray(values, np.float64)[::-1], 0.0, 1.0)
    height, width = level.shape
    levels = []
    while True:
        levels.append(encodeLevel(level))
        if level.shape == (1, 1):
            break
        nextHeight, nextWidth = max(1, level.shape[0] // 2), max(1, level.shape[1] // 2)
        level = level[:nextHeight * 2, :nextWidth * 2].reshape(nextHeight, level.shape[0] // nextHeight, nextWidth, level.shape[1] // nextWidth).mean((1, 3))
    header = struct.pack('<4s7I44x2I4s5I4I4x', b'DDS ', 124, 0xA1007, height, width,
                         max(1, (width + 3) // 4) * max(1, (height + 3) // 4) * 8, 0, len(levels),
                         32, 4, b'DXT1', 0, 0, 0, 0, 0, 0x401008, 0, 0, 0)
    with open(path, 'wb') as file:
        file.write(header)
        for data in levels:
            file.write(data)
