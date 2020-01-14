from blender2nier.util import *

def create_wmb_boneSet(wmb_file, data):
    wmb_file.seek(data.boneSets_Offset)

    for boneSet in data.boneSet.boneSet:
        write_uInt32(wmb_file, boneSet[0])
        write_uInt32(wmb_file, boneSet[1])
    for boneSet in data.boneSet.boneSet:
        for entry in boneSet[2]:
            write_Int16(wmb_file, entry)