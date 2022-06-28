import struct


def create_wmb(filepath):
    print('Creating wmb file: ', filepath)
    wmb_file = open(filepath, 'wb')
    return wmb_file


def to_float(bs):
	return struct.unpack("<f", bs)[0]


def to_float16(bs):
	return struct.unpack("<e", bs)[0]


def to_uint(bs):
	return (int.from_bytes(bs, byteorder='little', signed=False))


def to_int(bs):
	return (int.from_bytes(bs, byteorder='little', signed=True))


def to_string(bs, encoding = 'utf8'):
	return bs.split(b'\x00')[0].decode(encoding)


def to_ushort(bs):
	return struct.unpack("<H", bs)[0]


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
    entry = struct.pack("<e", val)
    file.write(entry)


def close_wmb(wmb_file, generated_data):
    wmb_file.seek(generated_data.lods_Offset-52)
    write_string(wmb_file, 'WMB created with Blender2NieR v0.3.0 by Woeful_Wolf')
    wmb_file.flush()
    wmb_file.close()
