from blender2nier.util import *

def create_wmb_boneMap(wmb_file, data):
    for boneMap in data.boneMap.boneMap:
        write_Int32(wmb_file, boneMap)