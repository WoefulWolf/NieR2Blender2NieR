import os
import sys
import struct
import numpy as np
import bpy

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
    write_buffer(file, 1)

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
    f16 = np.float16(val)
    f16.tofile(file)

def close_wmb(wmb_file):
    write_buffer(wmb_file, 32)
    write_string(wmb_file, 'WMB created with Blender2NieR v0.1.10 by Woeful_Wolf')
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

def show_message(message = "", title = "Message Box", icon = 'INFO'):
	def draw(self, context):
		self.layout.label(text = message)
		self.layout.alignment = 'CENTER'
	bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)