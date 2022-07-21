from time import time

from ....utils.util import setTiming, timing
from ....utils.ioUtils import SmartIO, write_Int32, write_uInt32, write_xyz, write_byte, write_float16


@timing(["main", "create_wmb_vertexGroups"])
def create_wmb_vertexGroups(wmb_file, data):
    wmb_file.seek(data.vertexGroups_Offset)
    
    t1 = time()
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
    setTiming(["main", "create_wmb_vertexGroups", "1"], time() - t1)

    writePos = SmartIO.makeFormat(SmartIO.float, SmartIO.float, SmartIO.float)
    writeTangent = SmartIO.makeFormat(SmartIO.uint8, SmartIO.uint8, SmartIO.uint8, SmartIO.uint8)
    writeNormal = SmartIO.makeFormat(SmartIO.float16, SmartIO.float16, SmartIO.float16, SmartIO.float16)
    writeUV = SmartIO.makeFormat(SmartIO.float16, SmartIO.float16)
    writeColor = writeTangent
    for vertexGroup in data.vertexGroups.vertexGroups:
        t1 = time()
        for vertex in vertexGroup.vertexes:                         # [position.xyz, tangents, normal, uv_maps, boneIndexes, boneWeights, color]
            # write_xyz(wmb_file, vertex[0])                          # position.xyz
            writePos.write(wmb_file, vertex[0])
            # for val in vertex[1]:                                   # tangents
                # write_byte(wmb_file, val)
            writeTangent.write(wmb_file, vertex[1])
            # for val in vertex[3][0]:                                # UVMap 1
            #     write_float16(wmb_file, val)
            writeUV.write(wmb_file, vertex[3][0])
            if vertexGroup.vertexFlags == 0:                        # Normal
                # for val in vertex[2]:
                #     write_float16(wmb_file, val)
                writeNormal.write(wmb_file, vertex[2])
            if vertexGroup.vertexFlags in {1, 4, 5, 12, 14}:
                # for val in vertex[3][1]:                            # UVMap 2
                #     write_float16(wmb_file, val)
                writeUV.write(wmb_file, vertex[3][1])
            if vertexGroup.vertexFlags in {7, 10, 11}:
                for val in vertex[4]:                               
                    write_byte(wmb_file, val)                       # Bone Indices
                for val in vertex[5]:                                   
                    write_byte(wmb_file, val)                       # Bone Weights
            if vertexGroup.vertexFlags in {4, 5, 12, 14}:
                # for val in vertex[6]:                                   
                #     write_byte(wmb_file, val)                       # Color
                writeColor.write(wmb_file, vertex[6])

        setTiming(["main", "create_wmb_vertexGroups", "2"], time() - t1)

        t1 = time()
        wmb_file.seek(vertexGroup.vertexExDataOffset)
        for vertexExData in vertexGroup.vertexesExData:             # [normal, uv_maps, color]
            if vertexGroup.vertexFlags in {1, 4}:                   # [1, 4]
                # for val in vertexExData[0]:                         # normal
                #     write_float16(wmb_file, val)
                writeNormal.write(wmb_file, vertexExData[0])
            elif vertexGroup.vertexFlags == 5:                      # [5]
                # for val in vertexExData[0]:                         # normal
                #     write_float16(wmb_file, val)
                writeNormal.write(wmb_file, vertexExData[0])
                # for val in vertexExData[1][0]:                      # UVMap 3
                #     write_float16(wmb_file, val)
                writeUV.write(wmb_file, vertexExData[1][0])
            elif vertexGroup.vertexFlags == 7:                      # [7]
                # for val in vertexExData[1][0]:                      # UVMap 1
                #     write_float16(wmb_file, val)
                writeUV.write(wmb_file, vertexExData[1][0])
                # for val in vertexExData[0]:                         # normal
                #     write_float16(wmb_file, val)
                writeNormal.write(wmb_file, vertexExData[0])
            elif vertexGroup.vertexFlags == 10:                     # [10]
                # for val in vertexExData[1][0]:                      # UVMap 1
                #     write_float16(wmb_file, val)
                writeUV.write(wmb_file, vertexExData[1][0])
                # for val in vertexExData[2]:                         # Color                               
                #     write_byte(wmb_file, val)
                writeColor.write(wmb_file, vertexExData[2])
                # for val in vertexExData[0]:                         # normal
                #     write_float16(wmb_file, val)
                writeNormal.write(wmb_file, vertexExData[0])
            elif vertexGroup.vertexFlags == 11:                     # [11]
                # for val in vertexExData[1][0]:                      # UVMap 1
                #     write_float16(wmb_file, val)
                writeUV.write(wmb_file, vertexExData[1][0])
                # for val in vertexExData[2]:                         # Color
                #     write_byte(wmb_file, val)
                writeColor.write(wmb_file, vertexExData[2])
                # for val in vertexExData[0]:                         # normal
                #     write_float16(wmb_file, val)
                writeNormal.write(wmb_file, vertexExData[0])
                # for val in vertexExData[1][1]:                      # UVMap 2
                #     write_float16(wmb_file, val)
                writeUV.write(wmb_file, vertexExData[1][1])
            elif vertexGroup.vertexFlags == 12:                     # [12]
                # for val in vertexExData[0]:                         # normal
                #     write_float16(wmb_file, val)
                writeNormal.write(wmb_file, vertexExData[0])
                # for val in vertexExData[1][0]:                      # UVMap 3
                #     write_float16(wmb_file, val)
                writeUV.write(wmb_file, vertexExData[1][0])
                # for val in vertexExData[1][1]:                      # UVMap 4
                #     write_float16(wmb_file, val)
                writeUV.write(wmb_file, vertexExData[1][1])
                # for val in vertexExData[1][2]:                      # UVMap 5
                #     write_float16(wmb_file, val)
                writeUV.write(wmb_file, vertexExData[1][2])
            elif vertexGroup.vertexFlags == 14:                     # [14]
                # for val in vertexExData[0]:                         # normal
                #     write_float16(wmb_file, val)
                writeNormal.write(wmb_file, vertexExData[0])
                # for val in vertexExData[1][0]:                      # UVMap 3
                #     write_float16(wmb_file, val)
                writeUV.write(wmb_file, vertexExData[1][0])
                # for val in vertexExData[1][1]:                      # UVMap 4
                #     write_float16(wmb_file, val)
                writeUV.write(wmb_file, vertexExData[1][1])

        setTiming(["main", "create_wmb_vertexGroups", "3"], time() - t1)

        t1 = time()
        for index in vertexGroup.indexes:                           # indexes
            write_uInt32(wmb_file, index)
        setTiming(["main", "create_wmb_vertexGroups", "4"], time() - t1)
        