from time import time

from ....utils.ioUtils import write_Int32, write_uInt32


def create_wmb_vertexGroups(wmb_file, data):
    wmb_file.seek(data.vertexGroups_Offset)
    
    for vertexGroup in data.vertexGroups.vertexGroups:
        write_uInt32(wmb_file, vertexGroup.vertexOffset)            # vertexOffset
        write_uInt32(wmb_file, vertexGroup.vertexExDataOffset)      # vertexExDataOffset
        for val in vertexGroup.unknownOffset:                       # unknownOffset
            write_uInt32(wmb_file, val)
        write_uInt32(wmb_file, vertexGroup.vertexSize)              # vertexSize
        write_uInt32(wmb_file, vertexGroup.vertexExDataSize)        # vertexExDataSize
        for val in vertexGroup.unknownSize:                         # unknownSize
            write_uInt32(wmb_file, val)
        write_Int32(wmb_file, vertexGroup.numVertexes)              # numVertexes
        write_Int32(wmb_file, vertexGroup.vertexFlags)              # vertexFlags
        write_Int32(wmb_file, vertexGroup.indexBufferOffset)        # indexBufferOffset
        write_Int32(wmb_file, vertexGroup.numIndexes)               # numIndexes

    for vertexGroup in data.vertexGroups.vertexGroups:
        wmb_file.write(vertexGroup.vertexBuffer)
        wmb_file.seek(vertexGroup.vertexExDataOffset)
        wmb_file.write(vertexGroup.vertexExDataBuffer)
        wmb_file.write(vertexGroup.indexBuffer)
        