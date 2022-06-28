import ctypes
import os
import struct


def to_bytes(arg):
	if type(arg) == int:
		return struct.pack('<I', arg)
	if type(arg) == str:
		return struct.pack('<I', int(arg, 16))

def pad_dds_files(texture_file_array):
    ddsArray = texture_file_array

    sectorsPerCluster = ctypes.c_ulonglong(0)
    bytesPerSector = ctypes.c_ulonglong(0)
    
    #print(dds_cSize)
    for i in range(len(ddsArray)):
        dds_dir = os.path.dirname(ddsArray[i])
        rootPathName = ctypes.c_wchar_p(u"" + dds_dir)
        ctypes.windll.kernel32.GetDiskFreeSpaceW(rootPathName, ctypes.pointer(sectorsPerCluster), ctypes.pointer(bytesPerSector), None, None,)
        dds_cSize = sectorsPerCluster.value * bytesPerSector.value

        dds_lSize = os.stat(ddsArray[i]).st_size
        dds_dSize = ((dds_lSize + (dds_cSize - 1)) // dds_cSize) * dds_cSize
        #print(paddingAmount)
        if dds_dSize < 12289:
            paddingAmount = 12288 - dds_lSize 
        elif dds_dSize < 176129:
            paddingAmount = 176128 - dds_lSize 
        elif dds_dSize < 352257:
            paddingAmount = 352256 - dds_lSize 
        elif dds_dSize < 528385:
            paddingAmount = 528384 - dds_lSize 
        elif dds_dSize < 700417:
            paddingAmount = 700416 - dds_lSize 
        elif dds_dSize < 2797569:
            paddingAmount = 2797568 - dds_lSize 
        else:
            paddingAmount = dds_dSize - dds_lSize
        #print(os.stat(ddsArray[i]).st_size)
        dds_fp = open(ddsArray[i], 'ab')
        dds_fp.seek(dds_lSize)
        
        if i != len(ddsArray)-1 and paddingAmount != 0:
            #print("-Padding dds: " + ddsArray[i] + " with " + str(paddingAmount) + " bytes")
            for j in range(paddingAmount-4):
                dds_fp.write(b'\x00')
            dds_fp.write(struct.pack('<I', paddingAmount))
        dds_fp.close()