from blender2nier.util import *

def create_wmb_lods(wmb_file, data):
    wmb_file.seek(data.lods_Offset)

    lods = data.lods
    write_uInt32(wmb_file, lods.offsetName)                 # offsetName
    write_Int32(wmb_file, lods.lodLevel)                    # lodLevel
    write_uInt32(wmb_file, lods.batchStart)                 # batchStart
    write_uInt32(wmb_file, lods.offsetBatchInfos)           # offsetBatchInfos
    write_uInt32(wmb_file, lods.numBatchInfos)              # numBatchInfos

    for batchInfo in lods.batchInfos:                       # [vertexGroupIndex, meshIndex, materialIndex, colTreeNodeIndex, meshMatPairIndex, indexToUnknown1]
        write_uInt32(wmb_file, batchInfo[0])                # vertexGroupIndex
        write_uInt32(wmb_file, batchInfo[1])                # meshIndex
        write_uInt32(wmb_file, batchInfo[2])                # materialIndex
        write_Int32(wmb_file, batchInfo[3])                 # colTreeNodeIndex
        write_uInt32(wmb_file, batchInfo[4])                # meshMatPairIndex
        write_Int32(wmb_file, batchInfo[5])                 # indexToUnknown1

    write_string(wmb_file, lods.name)                       # name