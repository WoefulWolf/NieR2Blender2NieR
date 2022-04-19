from ...util import *

def create_wmb_lods(wmb_file, data):
    wmb_file.seek(data.lods_Offset)

    lods = data.lods.lods
    for lod in lods:
        write_uInt32(wmb_file, lod.offsetName)                 # offsetName
        write_Int32(wmb_file, lod.lodLevel)                    # lodLevel
        write_uInt32(wmb_file, lod.batchStart)                 # batchStart
        write_uInt32(wmb_file, lod.offsetBatchInfos)           # offsetBatchInfos
        write_uInt32(wmb_file, lod.numBatchInfos)              # numBatchInfos

    for lod in lods:
        for batchInfo in lod.batchInfos:                       # [vertexGroupIndex, meshIndex, materialIndex, colTreeNodeIndex, meshMatPairIndex, indexToUnknown1]
            write_uInt32(wmb_file, batchInfo[0])                # vertexGroupIndex
            write_uInt32(wmb_file, batchInfo[1])                # meshIndex
            write_uInt32(wmb_file, batchInfo[2])                # materialIndex
            write_Int32(wmb_file, batchInfo[3])                 # colTreeNodeIndex
            write_uInt32(wmb_file, batchInfo[4])                # meshMatPairIndex
            write_Int32(wmb_file, batchInfo[5])                 # indexToUnknown1
        
        write_string(wmb_file, lod.name)                       # name