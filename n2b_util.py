#encoding = utf-8
import os
import sys
import struct

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

def create_dir(dirpath):
	if not os.path.exists(dirpath):
		os.makedirs(dirpath)

def find_files(dir_name,ext):
	filenameArray = []
	for dirpath,dirnames,filename in os.walk(dir_name):
		for file in filename:
			filename = "%s\%s"%(dirpath,file)
			#print(filename)
			if filename.find(ext) > -1:
				filenameArray.append(filename)
	return filenameArray

def print_class(obj):
	print ('\n'.join(sorted(['%s:\t%s ' % item for item in obj.__dict__.items() if item[0].find('Offset') < 0 or item[0].find('unknown') < 0 ])))
	print('\n')

def current_postion(fp):
	print(hex(fp.tell()))
