from ..util import *

def create_wmb_boneMap(wmb_file, data):
    wmb_file.seek(data.boneMap_Offset)

    for boneMap in data.boneMap.boneMap:
        write_Int32(wmb_file, boneMap)