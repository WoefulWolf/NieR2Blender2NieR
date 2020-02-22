from blender2nier.util import *

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
        for vertex in vertexGroup.vertexes:                         # [position.xyz, tangents, mapping, mapping2, color]
            write_xyz(wmb_file, vertex[0])                          # position.xyz
            for val in vertex[1]:                                   # tangents
                write_byte(wmb_file, val)
            for val in vertex[2]:                                   # mapping
                write_float16(wmb_file, val)
            if vertexGroup.vertexFlags in [4, 14]:                        
                for val in vertex[3]:                               
                    write_float16(wmb_file, val)                    # mapping2
            else:
                for val in vertex[3]:                               
                    write_byte(wmb_file, val)                       # boneIndex
            for val in vertex[4]:                                   
                write_byte(wmb_file, val)                           # color/boneWeight

        wmb_file.seek(vertexGroup.vertexExDataOffset)
        for vertexExData in vertexGroup.vertexesExData:             # vertexesExData

            if vertexGroup.vertexExDataSize == 8:                   
                for val in vertexExData:                            # normal
                    write_float16(wmb_file, val)

            elif vertexGroup.vertexExDataSize == 12:
                for val in vertexExData[0]:                         # mapping2
                    write_float16(wmb_file, val)
                for val in vertexExData[1]:                         # normal
                    write_float16(wmb_file, val)

            elif vertexGroup.vertexExDataSize == 16 and vertexGroup.vertexFlags == 14:
                for val in vertexExData[0]:                         # normal
                    write_float16(wmb_file, val)
                for val in vertexExData[1]:                         # mapping3
                    write_float16(wmb_file, val)
                for val in vertexExData[2]:                         # mapping4
                    write_float16(wmb_file, val)

            elif vertexGroup.vertexExDataSize == 16:
                for val in vertexExData[0]:                         # mapping2
                    write_float16(wmb_file, val)
                for val in vertexExData[1]:                         # color
                    write_byte(wmb_file, val)
                for val in vertexExData[2]:                         # normal
                    write_float16(wmb_file, val)

            elif vertexGroup.vertexExDataSize == 20:
                for val in vertexExData[0]:                         # mapping2
                    write_float16(wmb_file, val)
                for val in vertexExData[1]:                         # color
                    write_byte(wmb_file, val)
                for val in vertexExData[2]:                         # normal
                    write_float16(wmb_file, val)
                for val in vertexExData[3]:                         # mapping 3
                    write_float16(wmb_file, val)

        for index in vertexGroup.indexes:                           # indexes
            write_uInt32(wmb_file, index)