from __future__ import annotations
import struct
from typing import Any, List, Tuple

# Little Endian

def read_int8(file) -> int:
    entry = file.read(1)
    return struct.unpack('<b', entry)[0]

def read_uint8(file) -> int:
    entry = file.read(1)
    return struct.unpack('B', entry)[0]

def read_uint8_x4(file) -> Tuple[int]:
    entry = file.read(4)
    return struct.unpack('BBBB', entry)

def read_int16(file) -> int:
    entry = file.read(2)
    return struct.unpack('<h', entry)[0]

def read_uint16(file) -> int:
    entry = file.read(2)
    return struct.unpack('<H', entry)[0]

def read_int32(file) -> int:
    entry = file.read(4)
    return struct.unpack('<i', entry)[0]

def read_uint32(file) -> int:
    entry = file.read(4)
    return struct.unpack('<I', entry)[0]

def read_int64(file) -> int:
    entry = file.read(8)
    return struct.unpack('<q', entry)[0]

def read_uint64(file) -> int:
    entry = file.read(8)
    return struct.unpack('<Q', entry)[0]

def read_float16(file) -> float:
    entry = file.read(2)
    return struct.unpack('<e', entry)[0]

def read_float(file) -> float:
    entry = file.read(4)
    return struct.unpack('<f', entry)[0]

class SmartRead:
    int8 = "b"
    uint8 = "B"
    int16 = "h"
    uint16 = "H"
    int32 = "i"
    uint32 = "I"
    int64 = "q"
    uint64 = "Q"
    float16 = "e"
    float = "f"

    format: str
    count: int

    def __init__(self, format: str):
        self.format = format
        self.count = struct.calcsize(format)

    @classmethod
    def makeFormat(cls, *formats: List[str]) -> SmartRead:
        return SmartRead("<" + "".join(formats))
    
    def read(self, file) -> Tuple[Any]:
        return struct.unpack(self.format, file.read(self.count))

def to_uint(bs):
	return int.from_bytes(bs, byteorder='little', signed=False)

def write_char(file, char):
    entry = struct.pack('<s', bytes(char, 'utf-8'))
    file.write(entry)


def write_Int32(file, int):
    entry = struct.pack('<i', int)
    file.write(entry)


def write_uInt32(file, int):
    entry = struct.pack('<I', int)
    file.write(entry)


def write_Int16(file, int):
    entry = struct.pack('<h', int)
    file.write(entry)


def write_uInt16(file, int):
    entry = struct.pack('<H', int)
    file.write(entry)


def write_float(file, float):
    entry = struct.pack('<f', float)
    file.write(entry)


def write_xyz(file, xyz):
    for val in xyz:
        write_float(file, val)


def write_buffer(file, size):
    for i in range(size):
        write_char(file, '')


def write_byte(file, val):
    entry = struct.pack('B', val)
    file.write(entry)


def write_float16(file, val):
    entry = struct.pack("<e", val)
    file.write(entry)

# WMB

def create_wmb(filepath):
    print('Creating wmb file: ', filepath)
    wmb_file = open(filepath, 'wb')
    return wmb_file


def close_wmb(wmb_file, generated_data):
    wmb_file.seek(generated_data.lods_Offset-52)
    write_string(wmb_file, 'WMB created with Blender2NieR v0.3.0 by Woeful_Wolf')
    wmb_file.flush()
    wmb_file.close()

# String

def to_string(bs, encoding = 'utf8'):
    return bs.split(b'\x00')[0].decode(encoding)

def read_string(file, maxBen = -1) -> str:
    binaryString = b""
    while maxBen == -1 or len(binaryString) > maxBen:
        char = readBe_char(file)
        if char == b'\x00':
            break
        binaryString += char
    return binaryString.decode('utf-8')


def write_string(file, str):
    for char in str:
        write_char(file, char)
    write_buffer(file, 1)

# Big Endian

def readBe_int16(file) -> int:
    entry = file.read(2)
    return struct.unpack('>h', entry)[0]

def readBe_int32(file) -> int:
    entry = file.read(4)
    return struct.unpack('>i', entry)[0]

def readBe_char(file) -> str:
    entry = file.read(1)
    return struct.unpack('>c', entry)[0]

def writeBe_char(file, char):
    entry = struct.pack('>s', bytes(char, 'utf-8'))
    file.write(entry)

def writeBe_int32(file, int):
    entry = struct.pack('>i', int)
    file.write(entry)

def writeBe_int16(file, int):
    entry = struct.pack('>h', int)
    file.write(entry)
