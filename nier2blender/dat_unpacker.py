#encoding = utf-8
import os
import sys
import struct

def little_endian_to_float(bs):
    return struct.unpack("<f", bs)[0]

def little_endian_to_int(bs):
    return int.from_bytes(bs, byteorder='little')

def create_dir(dirpath):
	if not os.path.exists(dirpath):
		os.makedirs(dirpath)

def read_header(fp):
	Magic = fp.read(4)
	if list(Magic) == [68, 65, 84, 0]:
		FileCount = little_endian_to_int(fp.read(4))
		FileTableOffset = little_endian_to_int(fp.read(4))
		ExtensionTableOffset = little_endian_to_int(fp.read(4))
		NameTableOffset = little_endian_to_int(fp.read(4))
		SizeTableOffset = little_endian_to_int(fp.read(4))
		UnknownOffset1C = little_endian_to_int(fp.read(4))
		Unknown20 = little_endian_to_int(fp.read(4))
		print(
'''FileCount: %08x
FileTableOffset: %08x
ExtensionTableOffset:%08x
NameTableOffset:%08x
SizeTableOffset:%08x
UnknownOffset1C:%08x
Unknown20:%08x
'''%
			(FileCount, FileTableOffset, ExtensionTableOffset,NameTableOffset,SizeTableOffset,UnknownOffset1C,Unknown20)
		)
		return (FileCount, FileTableOffset, ExtensionTableOffset,NameTableOffset,SizeTableOffset,UnknownOffset1C,Unknown20)
	else:
		print('[-] error magic number detected')
		return False

def get_fileinfo(fp, index, FileTableOffset, ExtensionTableOffset, NameTableOffset, SizeTableOffset):
	fp.seek(FileTableOffset + index * 4)
	FileOffset = little_endian_to_int(fp.read(4))
	fp.seek(ExtensionTableOffset + index * 4)
	Extension = fp.read(4).decode('utf-8')
	fp.seek(SizeTableOffset + index * 4)
	Size = little_endian_to_int(fp.read(4))
	fp.seek(NameTableOffset)
	FilenameAlignment = little_endian_to_int(fp.read(4))
	i = 0
	while i < index:
		if list(fp.read(FilenameAlignment))[FilenameAlignment-1] == 0:
			i += 1
	Filename = fp.read(256).split(b'\x00')[0].decode('ascii')
	print(
'''
FileIndex: %d
Filename: %s
FileOffset: %08x
Size: %08x
Extension: %s'''%
(index,Filename,FileOffset,Size,Extension)
		)
	return index,Filename,FileOffset,Size,Extension

def extract_file(fp, filename, FileOffset, Size, extract_dir):
	create_dir(extract_dir)
	fp.seek(FileOffset)
	FileContent = fp.read(Size)
	outfile = open(extract_dir + '/'+filename,'wb')
	print("extracting file %s to %s/%s"%(filename,extract_dir,filename))
	outfile.write(FileContent)
	outfile.close()
	if filename.find('wtp') > -1 :
		wtp_fp = open(extract_dir + '/'+filename,"rb")
		content = wtp_fp.read(Size)
		dds_group = content.split(b'DDS ')
		dds_group = dds_group[1:]
		for i in range(len(dds_group)):
			print("unpacking %s to %s/%s"%(filename,extract_dir ,filename.replace('.wtp','_%d.dds'%i)))
			dds_fp = open(extract_dir + '/'+filename.replace('.wtp','_%d.dds'%i), "wb")
			dds_fp.write(b'DDS ')
			dds_fp.write(dds_group[i])
			dds_fp.close()
		wtp_fp.close()
		#os.remove("%s/%s"%(extract_dir,filename))
	print("done")

def get_all_files(path):
	pass

def main(filename, extract_dir, ROOT_DIR):
	fp = open(filename,"rb")
	headers = read_header(fp)
	if headers:
		FileCount, FileTableOffset, ExtensionTableOffset,NameTableOffset,SizeTableOffset,UnknownOffset1C,Unknown20 = headers
		for i in range(FileCount):
			extract_dir_sub = ''
			index,Filename,FileOffset,Size,Extension = get_fileinfo(fp, i, FileTableOffset,ExtensionTableOffset, NameTableOffset,SizeTableOffset)
			if extract_dir != '':
				extract_dir_sub = extract_dir + '\\' + filename.replace(ROOT_DIR ,'') 
				extract_file(fp, Filename, FileOffset, Size, extract_dir_sub)


if __name__ == '__main__':
	extract_dir = ''
	dirname = ''
	useage = "\nUseage:\npython dat_unpacker.py your_dat_path your_extract_path"
	useage1 = "\nUseage:\nblender --background --python dat_unpacker.py your_dat_path your_extract_path"
	if len(sys.argv) < 3:
		print(useage)
		exit()
	if len(sys.argv) > 2:
		dir_name = sys.argv[1]
		extract_dir = sys.argv[2]
		print()
		if os.path.split(sys.argv[0])[-1].lower().find("blender") >-1:
			if len(sys.argv) < 6:
				print(useage1)
				exit()
			dir_name = sys.argv[4]
			extract_dir = sys.argv[5]
		if not os.path.exists(extract_dir):
			create_dir(extract_dir)
	ROOT_DIR = dir_name
	for dirpath,dirnames,filename in os.walk(dir_name):
		for file in filename:
			filename = "%s\%s"%(dirpath,file)
			main(filename, extract_dir, ROOT_DIR)
