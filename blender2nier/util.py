import os
import sys
import struct

def create_wmb(filepath):
    print('Creating wmb file: ', filepath)
    wmb_file = open(filepath, 'wb')
    return wmb_file

def write_float(file, float):
    entry = struct.pack('<f', float)
    file.write(entry)

def write_char(file, char):
    entry = struct.pack('<s', bytes(char, 'utf-8'))
    file.write(entry)

def write_string(file, str):
    for char in str:
        write_char(file, char)

def write_Int32(file, int):
    entry = struct.pack('<L', int)
    file.write(entry)

def write_uInt32(file, int):
    entry = struct.pack('<l', int)
    file.write(entry)

def write_Int16(file, int):
    entry = struct.pack('<h', int)
    file.write(entry)

def write_uInt16(file, int):
    entry = struct.pack('<H', int)
    file.write(entry)

def write_xyz(file, xyz):
    for float in xyz:
        write_float(file, float)

def close_wmb(wmb_file):
    wmb_file.flush()
    wmb_file.close()

def uInt32_array_size(array):
    return len(array) * 4

class Vector3(object):
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.xyz = [x, y, z]