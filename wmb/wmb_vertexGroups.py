from ..util import *

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
        for vertex in vertexGroup.vertexes:                         # [position.xyz, tangents, normal, uv_maps, boneIndexes, boneWeights, color]
            write_xyz(wmb_file, vertex[0])                          # position.xyz
            for val in vertex[1]:                                   # tangents
                write_byte(wmb_file, val)
            for val in vertex[3][0]:                                # UVMap 1
                write_float16(wmb_file, val)
            if vertexGroup.vertexFlags == 0:                        # Normal
                for val in vertex[2]:
                    write_float16(wmb_file, val)
            if vertexGroup.vertexFlags in [1, 4, 5, 12, 14]:
                for val in vertex[3][1]:                            # UVMap 2
                    write_float16(wmb_file, val)
            if vertexGroup.vertexFlags in [7, 10, 11]:
                for val in vertex[4]:                               
                    write_byte(wmb_file, val)                       # Bone Indices
                for val in vertex[5]:                                   
                    write_byte(wmb_file, val)                       # Bone Weights
            if vertexGroup.vertexFlags in [4, 5, 12, 14]:
                for val in vertex[6]:                                   
                    write_byte(wmb_file, val)                       # Color

        wmb_file.seek(vertexGroup.vertexExDataOffset)
        for vertexExData in vertexGroup.vertexesExData:             # [normal, uv_maps, color]
            if vertexGroup.vertexFlags in [1, 4]:                   # [1, 4]
                for val in vertexExData[0]:                         # normal
                    write_float16(wmb_file, val)
            elif vertexGroup.vertexFlags == 5:                      # [5]
                for val in vertexExData[0]:                         # normal
                    write_float16(wmb_file, val)
                for val in vertexExData[1][0]:                      # UVMap 3
                    write_float16(wmb_file, val)
            elif vertexGroup.vertexFlags == 7:                      # [7]
                for val in vertexExData[1][0]:                      # UVMap 1
                    write_float16(wmb_file, val)
                for val in vertexExData[0]:                         # normal
                    write_float16(wmb_file, val)
            elif vertexGroup.vertexFlags == 10:                     # [10]
                for val in vertexExData[1][0]:                      # UVMap 1
                    write_float16(wmb_file, val)
                for val in vertexExData[2]:                         # Color                               
                    write_byte(wmb_file, val)
                for val in vertexExData[0]:                         # normal
                    write_float16(wmb_file, val)
            elif vertexGroup.vertexFlags == 11:                     # [11]
                for val in vertexExData[1][0]:                      # UVMap 1
                    write_float16(wmb_file, val)
                for val in vertexExData[2]:                         # Color                                   
                    write_byte(wmb_file, val)
                for val in vertexExData[0]:                         # normal
                    write_float16(wmb_file, val)
                for val in vertexExData[1][1]:                      # UVMap 2
                    write_float16(wmb_file, val)
            elif vertexGroup.vertexFlags == 12:                     # [12]
                for val in vertexExData[0]:                         # normal
                    write_float16(wmb_file, val)
                for val in vertexExData[1][0]:                      # UVMap 3
                    write_float16(wmb_file, val)
                for val in vertexExData[1][1]:                      # UVMap 4
                    write_float16(wmb_file, val)
                for val in vertexExData[1][2]:                      # UVMap 5
                    write_float16(wmb_file, val)
            elif vertexGroup.vertexFlags == 14:                     # [14]
                for val in vertexExData[0]:                         # normal
                    write_float16(wmb_file, val)
                for val in vertexExData[1][0]:                      # UVMap 3
                    write_float16(wmb_file, val)
                for val in vertexExData[1][1]:                      # UVMap 4
                    write_float16(wmb_file, val)

        for index in vertexGroup.indexes:                           # indexes
            write_uInt32(wmb_file, index)
        