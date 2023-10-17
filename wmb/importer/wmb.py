# load from .wmb into Python object
import os
import json
import bpy
import struct # even for only two lines
from time import time

from ...utils.util import print_class, create_dir
from ...utils.ioUtils import SmartIO, read_uint8_x4, to_string, read_float, read_float16, read_uint16, read_uint8, read_uint64, read_int16, read_int32, read_string
from ...wta_wtp.importer.wta import *

DEBUG_HEADER_PRINT = True
DEBUG_VERTEXGROUP_PRINT = False
#DEBUG_VERTEX_PRINT = # Don't even *think* about it.
DEBUG_BATCHES_PRINT = False
DEBUG_BATCHSUPPLEMENT_PRINT = True
DEBUG_BONE_PRINT = False # do not recommend, there can be lots of bones
DEBUG_BITT_PRINT = False # nothing at all
DEBUG_BONESET_PRINT = False
DEBUG_MATERIAL_PRINT = True
DEBUG_TEXTURE_PRINT = True # pretty short, pretty worthwhile
DEBUG_MESH_PRINT = False

class WMB_Header(object):
    """ fucking header    """
    size = 112 + 16 # apparently padding, can't be too safe
    def __init__(self, wmb_fp):
        super(WMB_Header, self).__init__()
        if wmb_fp is None:
            return
        self.magicNumber = wmb_fp.read(4)                               # ID
        if self.magicNumber == b'WMB3':
            self.version = "%08x" % (read_uint32(wmb_fp))               # Version
            self.unknown08 = read_uint32(wmb_fp)                        # UnknownA
            self.flags = read_uint32(wmb_fp)                            # flags & referenceBone
            
            self.bounding_box1 = read_float(wmb_fp)                     # bounding_box
            self.bounding_box2 = read_float(wmb_fp)                     
            self.bounding_box3 = read_float(wmb_fp)
            self.bounding_box4 = read_float(wmb_fp)
            
            self.bounding_box5 = read_float(wmb_fp)
            self.bounding_box6 = read_float(wmb_fp)
            self.bonePointer = read_uint32(wmb_fp)
            self.boneCount = read_uint32(wmb_fp)
            
            self.boneTranslateTablePointer = read_uint32(wmb_fp)
            self.boneTranslateTableSize = read_uint32(wmb_fp) # Wait, size? Not count? Check this.
            self.vertexGroupPointer = read_uint32(wmb_fp)
            self.vertexGroupCount = read_uint32(wmb_fp)
            
            self.meshPointer = read_uint32(wmb_fp)
            self.meshCount = read_uint32(wmb_fp)
            self.meshGroupInfoPointer = read_uint32(wmb_fp)
            self.meshGroupInfoCount = read_uint32(wmb_fp)
            
            self.colTreeNodesPointer = read_uint32(wmb_fp)
            self.colTreeNodesCount = read_uint32(wmb_fp)
            self.boneMapPointer = read_uint32(wmb_fp)
            self.boneMapCount = read_uint32(wmb_fp)
            
            self.boneSetPointer = read_uint32(wmb_fp)
            self.boneSetCount = read_uint32(wmb_fp)
            self.materialPointer = read_uint32(wmb_fp)
            self.materialCount = read_uint32(wmb_fp)
            
            self.meshGroupPointer = read_uint32(wmb_fp)
            self.meshGroupCount = read_uint32(wmb_fp)
            self.meshMaterialsPointer = read_uint32(wmb_fp) # Unaccessed??
            self.meshMaterialsCount = read_uint32(wmb_fp)
            
            self.unknownWorldDataPointer = read_uint32(wmb_fp)      # World Model Stuff
            self.unknownWorldDataCount = read_uint32(wmb_fp)        # World Model Stuff
            self.unknown8C = read_uint32(wmb_fp)                    # Maybe just padding lol
        
        elif self.magicNumber == b'WMB4':
            self.version = "%08x" % (read_uint32(wmb_fp))
            self.vertexFormat = read_uint32(wmb_fp)             # Vertex data format, ex. 0x137
            self.referenceBone = read_uint16(wmb_fp)
            self.flags = read_int16(wmb_fp)                     # flags & referenceBone
            
            self.bounding_box1 = read_float(wmb_fp)             # bounding_box pos 1
            self.bounding_box2 = read_float(wmb_fp)                     
            self.bounding_box3 = read_float(wmb_fp)
            self.bounding_box4 = read_float(wmb_fp)             # bounding_box pos 2
            
            self.bounding_box5 = read_float(wmb_fp)
            self.bounding_box6 = read_float(wmb_fp)
            self.vertexGroupPointer = read_uint32(wmb_fp)
            self.vertexGroupCount = read_uint32(wmb_fp)
            
            self.batchPointer = read_uint32(wmb_fp)
            self.batchCount = read_uint32(wmb_fp)
            self.batchDescriptionPointer = read_uint32(wmb_fp)  # No count on this one
            self.bonePointer = read_uint32(wmb_fp)
            
            self.boneCount = read_uint32(wmb_fp)
            self.boneTranslateTablePointer = read_uint32(wmb_fp)
            self.boneTranslateTableSize = read_uint32(wmb_fp)   # This one isn't count, but size.
            self.boneSetPointer = read_uint32(wmb_fp)
            
            self.boneSetCount = read_uint32(wmb_fp)
            self.materialPointer = read_uint32(wmb_fp)
            self.materialCount = read_uint32(wmb_fp)
            self.texturePointer = read_uint32(wmb_fp)
            
            self.textureCount = read_uint32(wmb_fp)
            self.meshPointer = read_uint32(wmb_fp)
            self.meshCount = read_uint32(wmb_fp)
            self.unknownPointer = read_uint32(wmb_fp)
            
            if DEBUG_HEADER_PRINT:
                print("WMB4 header information")
                print(" version       %s" % self.version)
                print(" vertexFormat  %s" % hex(self.vertexFormat))
                print(" referenceBone %d" % self.referenceBone)
                print(" flags         %s" % hex(self.flags))
                print(" bounding_box1 %d" % self.bounding_box1)
                print(" bounding_box2 %d" % self.bounding_box2)
                print(" bounding_box3 %d" % self.bounding_box3)
                print(" bounding_box4 %d" % self.bounding_box4)
                print(" bounding_box5 %d" % self.bounding_box5)
                print(" bounding_box6 %d" % self.bounding_box6)
                print()
                print(" Name               Pointer Count")
                print(" vertexGroup       ", hex(self.vertexGroupPointer).rjust(7, " "), str(self.vertexGroupCount).rjust(6, " "))
                print(" batch             ", hex(self.batchPointer).rjust(7, " "), str(self.batchCount).rjust(6, " "))
                print(" batchDescription  ", hex(self.batchDescriptionPointer).rjust(7, " "))
                print(" bone              ", hex(self.bonePointer).rjust(7, " "), str(self.boneCount).rjust(6, " "))
                print(" boneTranslateTable", hex(self.boneTranslateTablePointer).rjust(7, " "), str(self.boneTranslateTableSize).rjust(6, " "))
                print(" boneSet           ", hex(self.boneSetPointer).rjust(7, " "), str(self.boneSetCount).rjust(6, " "))
                print(" material          ", hex(self.materialPointer).rjust(7, " "), str(self.materialCount).rjust(6, " "))
                print(" texture           ", hex(self.texturePointer).rjust(7, " "), str(self.textureCount).rjust(6, " "))
                print(" mesh              ", hex(self.meshPointer).rjust(7, " "), str(self.meshCount).rjust(6, " "))
                print(" ??????            ", hex(self.unknownPointer).rjust(7, " "))



class wmb3_bone(object):
    """docstring for wmb3_bone"""
    def __init__(self, wmb_fp,index):
        super(wmb3_bone, self).__init__()
        self.boneIndex = index
        self.boneNumber = read_uint16(wmb_fp)                
        self.parentIndex = read_uint16(wmb_fp)

        local_positionX = read_float(wmb_fp)         
        local_positionY = read_float(wmb_fp)        
        local_positionZ = read_float(wmb_fp)    
        
        local_rotationX = read_float(wmb_fp)         
        local_rotationY = read_float(wmb_fp)         
        local_rotationZ = read_float(wmb_fp)        

        self.local_scaleX = read_float(wmb_fp)
        self.local_scaleY = read_float(wmb_fp)
        self.local_scaleZ = read_float(wmb_fp)

        world_positionX = read_float(wmb_fp)
        world_positionY = read_float(wmb_fp)
        world_positionZ = read_float(wmb_fp)
        
        world_rotationX = read_float(wmb_fp)
        world_rotationY = read_float(wmb_fp)
        world_rotationZ = read_float(wmb_fp)

        world_scaleX = read_float(wmb_fp)
        world_scaleY = read_float(wmb_fp)
        world_scaleZ = read_float(wmb_fp)

        world_position_tposeX = read_float(wmb_fp)
        world_position_tposeY = read_float(wmb_fp)
        world_position_tposeZ = read_float(wmb_fp)

        self.local_position = (local_positionX, local_positionY, local_positionZ)
        self.local_rotation = (local_rotationX, local_rotationY, local_rotationZ)

        self.world_position = (world_positionX, world_positionY, world_positionZ)
        self.world_rotation = (world_rotationX, world_rotationY, world_rotationZ)
        self.world_scale = (world_scaleX, world_scaleY, world_scaleZ)

        self.world_position_tpose = (world_position_tposeX, world_position_tposeY, world_position_tposeZ)

class wmb3_boneMap(object):
    """docstring for wmb3_boneMap"""
    def __init__(self, wmb_fp):
        super(wmb3_boneMap, self).__init__()
        self.boneMapPointer = read_uint32(wmb_fp)                    
        self.boneMapCount = read_uint32(wmb_fp)    

class wmb3_boneSet(object):
    """docstring for wmb3_boneSet"""
    def __init__(self, wmb_fp, boneSetCount):
        super(wmb3_boneSet, self).__init__()
        self.boneSetArray = []
        self.boneSetCount = boneSetCount
        boneSetInfoArray = []
        #print("Iterating over boneSetCount, length %d" % boneSetCount)
        for index in range(boneSetCount):
            offset = read_uint32(wmb_fp)
            count = read_uint32(wmb_fp)
            boneSetInfoArray.append([offset, count])
        #print("Iterating, really, not using range(), over boneSetInfoArray, length " + str(len(boneSetInfoArray)))
        for boneSetInfo in boneSetInfoArray:
            wmb_fp.seek(boneSetInfo[0])
            #print("Seeking to boneSetInfo[0]: %s" % hex(boneSetInfo[0]))
            boneSet = []
            #print("Iterating over boneSetInfo[1], length %d" % boneSetInfo[1])
            for index in range(boneSetInfo[1]):
                boneSet.append(read_uint16(wmb_fp))
            self.boneSetArray.append(boneSet)

class wmb3_colTreeNode(object):
    """docstring for colTreeNode"""
    def __init__(self, wmb_fp):
        p1_x = read_float(wmb_fp)
        p1_y = read_float(wmb_fp)
        p1_z = read_float(wmb_fp)
        self.p1 = (p1_x, p1_y, p1_z)

        p2_x = read_float(wmb_fp)
        p2_y = read_float(wmb_fp)
        p2_z = read_float(wmb_fp)
        self.p2 = (p2_x, p2_y, p2_z)

        self.left = read_uint32(wmb_fp)
        if self.left == 4294967295:
            self.left = -1

        self.right = read_uint32(wmb_fp)
        if self.right == 4294967295:
            self.right = -1

class wmb3_material(object):
    """docstring for wmb3_material"""
    def __init__(self, wmb_fp):
        super(wmb3_material, self).__init__()
        read_uint16(wmb_fp)
        read_uint16(wmb_fp)
        read_uint16(wmb_fp)
        read_uint16(wmb_fp)
        materialNameOffset = read_uint32(wmb_fp)
        effectNameOffset = read_uint32(wmb_fp)
        techniqueNameOffset = read_uint32(wmb_fp)
        read_uint32(wmb_fp)
        textureOffset = read_uint32(wmb_fp)
        textureNum = read_uint32(wmb_fp)
        paramterGroupsOffset = read_uint32(wmb_fp)
        numParameterGroups = read_uint32(wmb_fp)
        varOffset = read_uint32(wmb_fp)
        varNum = read_uint32(wmb_fp)
        wmb_fp.seek(materialNameOffset)
        #print("Seeking to materialNameOffset: %s" % hex(materialNameOffset))
        self.materialName = to_string(wmb_fp.read(0x100))
        wmb_fp.seek(effectNameOffset)
        #print("Seeking to effectNameOffset: %s" % hex(effectNameOffset))
        self.effectName = to_string(wmb_fp.read(0x100))
        wmb_fp.seek(techniqueNameOffset)
        #print("Seeking to techniqueNameOffset: %s" % hex(techniqueNameOffset))
        self.techniqueName = to_string(wmb_fp.read(0x100))
        self.textureArray = {}

        path_split = wmb_fp.name.split(os.sep)
        mat_list_filepath = os.sep.join(path_split[:-3])
        mat_list_file = open(os.path.join(mat_list_filepath, 'materials.json'), 'a+')
        mat_list_file.seek(0)
        file_dict = {}
        # Try to load json from pre-existing file
        try:
            file_dict = json.load(mat_list_file)
        except Exception as ex:
            print("Could not load json: " , ex)
            pass
        
        # Clear file contents
        mat_list_file.truncate(0)
        file_dict[self.materialName] = {}
        # Append textures to materials in the dictionary
        #print("Iterating over textureNum, length %d" % textureNum)
        for i in range(textureNum):
            wmb_fp.seek(textureOffset + i * 8)
            #print("Seeking to textureOffset + i * 8: %s" % hex(textureOffset + i * 8))
            offset = read_uint32(wmb_fp)
            identifier = "%08x"%read_uint32(wmb_fp)
            wmb_fp.seek(offset)
            #print("Seeking to offset: %s" % hex(offset))
            textureTypeName = to_string(wmb_fp.read(256))
            self.textureArray[textureTypeName] = identifier
            # Add new texture to nested material dictionary

        file_dict[self.materialName]["Textures"] = self.textureArray

        file_dict[self.materialName]["Shader_Name"] = self.effectName
        file_dict[self.materialName]["Technique_Name"] = self.techniqueName
        wmb_fp.seek(paramterGroupsOffset)
        #print("Seeking to paramterGroupsOffset: %s" % hex(paramterGroupsOffset))
        self.parameterGroups = []
        #print("Iterating over numParameterGroups, length %d" % numParameterGroups)
        for i in range(numParameterGroups):
            wmb_fp.seek(paramterGroupsOffset + i * 12)
            #print("Seeking to paramterGroupsOffset + i * 12: %s" % hex(paramterGroupsOffset + i * 12))
            parameters = []
            index = read_uint32(wmb_fp)
            offset = read_uint32(wmb_fp)
            num = read_uint32(wmb_fp)
            wmb_fp.seek(offset)
            #print("Seeking to offset: %s" % hex(offset))
            #print("Iterating over num, length %d" % num)
            for k in range(num):
                param = read_float(wmb_fp)
                parameters.append(param)
            self.parameterGroups.append(parameters)

        wmb_fp.seek(varOffset)
        #print("Seeking to varOffset: %s" % hex(varOffset))
        self.uniformArray = {}
        #print("Iterating over varNum, length %d" % varNum)
        for i in range(varNum):
            wmb_fp.seek(varOffset + i * 8)
            #print("Seeking to varOffset + i * 8: %s" % hex(varOffset + i * 8))
            offset = read_uint32(wmb_fp)
            value = read_float(wmb_fp)
            wmb_fp.seek(offset)
            #print("Seeking to offset: %s" % hex(offset))
            name = to_string(wmb_fp.read(0x100))
            self.uniformArray[name] = value

        file_dict[self.materialName]["ParameterGroups"] = self.parameterGroups
        file_dict[self.materialName]["Variables"] = self.uniformArray

        # Write the current material to materials.json
        json.dump(file_dict, mat_list_file, indent= 4)
        mat_list_file.close()

class wmb3_mesh(object):
    """docstring for wmb3_mesh"""
    def __init__(self, wmb_fp):
        super(wmb3_mesh, self).__init__()
        self.vertexGroupIndex = read_uint32(wmb_fp)
        self.bonesetIndex = read_uint32(wmb_fp)                    
        self.vertexStart = read_uint32(wmb_fp)                
        self.faceStart = read_uint32(wmb_fp)                    
        self.vertexCount = read_uint32(wmb_fp)                
        self.faceCount = read_uint32(wmb_fp)                    
        self.unknown18 = read_uint32(wmb_fp)

class wmb3_meshGroup(object):
    """docstring for wmb3_meshGroupInfo"""
    def __init__(self, wmb_fp):
        super(wmb3_meshGroup, self).__init__()
        nameOffset = read_uint32(wmb_fp)
        self.boundingBox = []
        #print("Iterating over 6, length %d" % 6)
        for i in range(6):
            self.boundingBox.append(read_float(wmb_fp))                                
        materialIndexArrayOffset = read_uint32(wmb_fp)
        materialIndexArrayCount = read_uint32(wmb_fp)
        boneIndexArrayOffset = read_uint32(wmb_fp)
        boneIndexArrayCount = read_uint32(wmb_fp)
        wmb_fp.seek(nameOffset)
        #print("Seeking to nameOffset: %s" % hex(nameOffset))
        self.meshGroupname = to_string(wmb_fp.read(256))
        self.materialIndexArray = []
        self.boneIndexArray = []
        wmb_fp.seek(materialIndexArrayOffset)
        #print("Seeking to materialIndexArrayOffset: %s" % hex(materialIndexArrayOffset))
        #print("Iterating over materialIndexArrayCount, length %d" % materialIndexArrayCount)
        for i in range(materialIndexArrayCount):
            self.materialIndexArray.append(read_uint16(wmb_fp))
        wmb_fp.seek(boneIndexArrayOffset)
        #print("Seeking to boneIndexArrayOffset: %s" % hex(boneIndexArrayOffset))
        #print("Iterating over boneIndexArrayCount, length %d" % boneIndexArrayCount)
        for i in range(boneIndexArrayCount):
            self.boneIndexArray.append(read_uint16(wmb_fp))

class wmb3_groupedMesh(object):
    """docstring for wmb3_groupedMesh"""
    def __init__(self, wmb_fp):
        super(wmb3_groupedMesh, self).__init__()
        self.vertexGroupIndex = read_uint32(wmb_fp)
        self.meshGroupIndex = read_uint32(wmb_fp)
        self.materialIndex = read_uint32(wmb_fp)
        self.colTreeNodeIndex = read_uint32(wmb_fp) 
        if self.colTreeNodeIndex == 0xffffffff:    
            self.colTreeNodeIndex = -1                    
        self.meshGroupInfoMaterialPair = read_uint32(wmb_fp)
        self.unknownWorldDataIndex = read_uint32(wmb_fp)
        if self.unknownWorldDataIndex == 0xffffffff:    
            self.unknownWorldDataIndex = -1

class wmb3_meshGroupInfo(object):
    """docstring for wmb3_meshGroupInfo"""
    def __init__(self, wmb_fp):
        super(wmb3_meshGroupInfo, self).__init__()
        self.nameOffset = read_uint32(wmb_fp)                    
        self.lodLevel = read_uint32(wmb_fp)
        if self.lodLevel == 0xffffffff:    
            self.lodLevel = -1                
        self.meshStart = read_uint32(wmb_fp)                        
        meshGroupInfoOffset = read_uint32(wmb_fp)            
        self.meshCount = read_uint32(wmb_fp)                        
        wmb_fp.seek(self.nameOffset)
        #print("Seeking to self.nameOffset: %s" % hex(self.nameOffset))
        self.meshGroupInfoname = to_string(wmb_fp.read(0x100))
        wmb_fp.seek(meshGroupInfoOffset)
        #print("Seeking to meshGroupInfoOffset: %s" % hex(meshGroupInfoOffset))
        self.groupedMeshArray = []
        #print("Iterating over self.meshCount, length %d" % self.meshCount)
        for i in range(self.meshCount):
            groupedMesh = wmb3_groupedMesh(wmb_fp)
            self.groupedMeshArray.append(groupedMesh)

class wmb3_vertexHeader(object):
    """docstring for wmb3_vertexHeader"""
    def __init__(self, wmb_fp):
        super(wmb3_vertexHeader, self).__init__()
        self.vertexArrayOffset = read_uint32(wmb_fp)        
        self.vertexExDataArrayOffset = read_uint32(wmb_fp)    
        self.unknown08 = read_uint32(wmb_fp)                
        self.unknown0C = read_uint32(wmb_fp)                
        self.vertexStride = read_uint32(wmb_fp)            
        self.vertexExDataStride = read_uint32(wmb_fp)        
        self.unknown18 = read_uint32(wmb_fp)                
        self.unknown1C = read_uint32(wmb_fp)                
        self.vertexCount = read_uint32(wmb_fp)            
        self.vertexFlags = read_uint32(wmb_fp)
        self.faceArrayOffset = read_uint32(wmb_fp)        
        self.faceCount = read_uint32(wmb_fp)                

class wmb3_vertexGroup(object):
    """docstring for wmb3_vertexGroup"""
    def __init__(self, wmb_fp, faceSize):
        super(wmb3_vertexGroup, self).__init__()
        self.faceSize = faceSize
        self.vertexGroupHeader = wmb3_vertexHeader(wmb_fp)

        self.vertexFlags = self.vertexGroupHeader.vertexFlags    
        
        self.vertexArray = [None] * self.vertexGroupHeader.vertexCount
        wmb_fp.seek(self.vertexGroupHeader.vertexArrayOffset)
        #print("Seeking to self.vertexGroupHeader.vertexArrayOffset: %s" % hex(self.vertexGroupHeader.vertexArrayOffset))
        #print("Iterating over self.vertexGroupHeader.vertexCount, length %d" % self.vertexGroupHeader.vertexCount)
        for vertex_index in range(self.vertexGroupHeader.vertexCount):
            vertex = wmb3_vertex(wmb_fp, self.vertexGroupHeader.vertexFlags)
            self.vertexArray[vertex_index] = vertex

        self.vertexesExDataArray = [None] * self.vertexGroupHeader.vertexCount
        wmb_fp.seek(self.vertexGroupHeader.vertexExDataArrayOffset)
        #print("Seeking to self.vertexGroupHeader.vertexExDataArrayOffset: %s" % hex(self.vertexGroupHeader.vertexExDataArrayOffset))
        #print("Iterating over self.vertexGroupHeader.vertexCount, length %d" % self.vertexGroupHeader.vertexCount)
        for vertexIndex in range(self.vertexGroupHeader.vertexCount):
            self.vertexesExDataArray[vertexIndex] = wmb3_vertexExData(wmb_fp, self.vertexGroupHeader.vertexFlags)

        self.faceRawArray = [None] * self.vertexGroupHeader.faceCount
        wmb_fp.seek(self.vertexGroupHeader.faceArrayOffset)
        #print("Seeking to self.vertexGroupHeader.faceArrayOffset: %s" % hex(self.vertexGroupHeader.faceArrayOffset))
        #print("Iterating over self.vertexGroupHeader.faceCount, length %d" % self.vertexGroupHeader.faceCount)
        for face_index in range(self.vertexGroupHeader.faceCount):
            if faceSize == 2:
                self.faceRawArray[face_index] = read_uint16(wmb_fp) + 1
            else:
                self.faceRawArray[face_index] = read_uint32(wmb_fp) + 1

class wmb3_vertex(object):
    smartRead = SmartIO.makeFormat(
        SmartIO.float,
        SmartIO.float,
        SmartIO.float,
        SmartIO.uint8,
        SmartIO.uint8,
        SmartIO.uint8,
        SmartIO.uint8,
        SmartIO.float16,
        SmartIO.float16,
    )
    smartReadUV2 = SmartIO.makeFormat(
        SmartIO.float16,
        SmartIO.float16,
    )

    """docstring for wmb3_vertex"""
    def __init__(self, wmb_fp, vertex_flags):
        super(wmb3_vertex, self).__init__()
        # self.positionX = read_float(wmb_fp)
        # self.positionY = read_float(wmb_fp)
        # self.positionZ = read_float(wmb_fp)
        # self.normalX = read_uint8(wmb_fp) * 2 / 255            
        # self.normalY = read_uint8(wmb_fp) * 2 / 255    
        # self.normalZ = read_uint8(wmb_fp) * 2 / 255    
        # wmb_fp.read(1)                                            
        # self.textureU = read_float16(wmb_fp)                
        # self.textureV = read_float16(wmb_fp)
        self.positionX, \
        self.positionY, \
        self.positionZ, \
        self.normalX, \
        self.normalY, \
        self.normalZ, \
        _, \
        self.textureU, \
        self.textureV = wmb3_vertex.smartRead.read(wmb_fp)
        self.normalX = self.normalX * 2 / 255
        self.normalY = self.normalY * 2 / 255
        self.normalZ = self.normalZ * 2 / 255

        if vertex_flags == 0:
            self.normal = hex(read_uint64(wmb_fp))
        if vertex_flags in {1, 4, 5, 12, 14}:
            # self.textureU2 = read_float16(wmb_fp)                
            # self.textureV2 = read_float16(wmb_fp)
            self.textureU2, \
            self.textureV2 = wmb3_vertex.smartReadUV2.read(wmb_fp)
        if vertex_flags in {7, 10, 11}:
            self.boneIndices = read_uint8_x4(wmb_fp)
            self.boneWeights = [x / 255 for x in read_uint8_x4(wmb_fp)]
        if vertex_flags in {4, 5, 12, 14}:
            self.color = read_uint8_x4(wmb_fp)

class wmb3_vertexExData(object):
    smartRead5 = SmartIO.makeFormat(
        SmartIO.uint64,
        SmartIO.float16,
        SmartIO.float16,
    )
    smartRead7 = SmartIO.makeFormat(
        SmartIO.float16,
        SmartIO.float16,
        SmartIO.uint64,
    )
    smartRead10 = SmartIO.makeFormat(
        SmartIO.float16,
        SmartIO.float16,
        SmartIO.uint8,
        SmartIO.uint8,
        SmartIO.uint8,
        SmartIO.uint8,
        SmartIO.uint64,
    )
    smartRead11 = SmartIO.makeFormat(
        SmartIO.float16,
        SmartIO.float16,
        SmartIO.uint8,
        SmartIO.uint8,
        SmartIO.uint8,
        SmartIO.uint8,
        SmartIO.uint64,
        SmartIO.float16,
        SmartIO.float16,
    )
    smartRead12 = SmartIO.makeFormat(
        SmartIO.uint64,
        SmartIO.float16,
        SmartIO.float16,
        SmartIO.float16,
        SmartIO.float16,
        SmartIO.float16,
        SmartIO.float16,
    )
    smartRead14 = SmartIO.makeFormat(
        SmartIO.uint64,
        SmartIO.float16,
        SmartIO.float16,
        SmartIO.float16,
        SmartIO.float16,
    )

    """docstring for wmb3_vertexExData"""
    def __init__(self, wmb_fp, vertex_flags):
        super(wmb3_vertexExData, self).__init__()
        
        #0x0 has no ExVertexData

        if vertex_flags in {1, 4}: #0x1, 0x4
            self.normal = hex(read_uint64(wmb_fp))

        elif vertex_flags == 5: #0x5
            # self.normal = hex(read_uint64(wmb_fp))
            # self.textureU3 = read_float16(wmb_fp)                
            # self.textureV3 = read_float16(wmb_fp)
            self.normal, \
            self.textureU3, \
            self.textureV3 = wmb3_vertexExData.smartRead5.read(wmb_fp)
            self.normal = hex(self.normal)

        elif vertex_flags == 7: #0x7
            # self.textureU2 = read_float16(wmb_fp)                
            # self.textureV2 = read_float16(wmb_fp)
            # self.normal = hex(read_uint64(wmb_fp))
            self.textureU2, \
            self.textureV2, \
            self.normal = wmb3_vertexExData.smartRead7.read(wmb_fp)
            self.normal = hex(self.normal)

        elif vertex_flags == 10: #0xa
            # self.textureU2 = read_float16(wmb_fp)                
            # self.textureV2 = read_float16(wmb_fp)
            # self.color = read_uint8_x4(wmb_fp)
            # self.normal = hex(read_uint64(wmb_fp))
            self.color = [0, 0, 0, 0]
            self.textureU2, \
            self.textureV2, \
            self.color[0], \
            self.color[1], \
            self.color[2], \
            self.color[3], \
            self.normal = wmb3_vertexExData.smartRead10.read(wmb_fp)
            self.normal = hex(self.normal)

        elif vertex_flags == 11: #0xb
            # self.textureU2 = read_float16(wmb_fp)                
            # self.textureV2 = read_float16(wmb_fp)
            # self.color = read_uint8_x4(wmb_fp)
            # self.normal = hex(read_uint64(wmb_fp))
            # self.textureU3 = read_float16(wmb_fp)                
            # self.textureV3 = read_float16(wmb_fp)
            self.color = [0, 0, 0, 0]
            self.textureU2, \
            self.textureV2, \
            self.color[0], \
            self.color[1], \
            self.color[2], \
            self.color[3], \
            self.normal, \
            self.textureU3, \
            self.textureV3 = wmb3_vertexExData.smartRead11.read(wmb_fp)
            self.normal = hex(self.normal)

        elif vertex_flags == 12: #0xc
            # self.normal = hex(read_uint64(wmb_fp))
            # self.textureU3 = read_float16(wmb_fp)                
            # self.textureV3 = read_float16(wmb_fp)
            # self.textureU4 = read_float16(wmb_fp)                
            # self.textureV4 = read_float16(wmb_fp)
            # self.textureU5 = read_float16(wmb_fp)                
            # self.textureV5 = read_float16(wmb_fp)
            self.normal, \
            self.textureU3, \
            self.textureV3, \
            self.textureU4, \
            self.textureV4, \
            self.textureU5, \
            self.textureV5 = wmb3_vertexExData.smartRead12.read(wmb_fp)
            self.normal = hex(self.normal)

        elif vertex_flags == 14: #0xe
            # self.normal = hex(read_uint64(wmb_fp))
            # self.textureU3 = read_float16(wmb_fp)                
            # self.textureV3 = read_float16(wmb_fp)
            # self.textureU4 = read_float16(wmb_fp)                
            # self.textureV4 = read_float16(wmb_fp)
            self.normal, \
            self.textureU3, \
            self.textureV3, \
            self.textureU4, \
            self.textureV4 = wmb3_vertexExData.smartRead14.read(wmb_fp)
            self.normal = hex(self.normal)

class wmb3_worldData(object):
    """docstring for wmb3_unknownWorldData"""
    def __init__(self, wmb_fp):
        self.unknownWorldData = []
        #print("Iterating over 6, length %d" % 6)
        for entry in range(6):
            self.unknownWorldData.append(wmb_fp.read(4))



class wmb4_batch(object):
    """docstring for wmb4_batch"""
    def read(self, wmb_fp):
        self.batchGroup = -1 # overwritten later
        self.vertexGroupIndex = read_uint32(wmb_fp)
        self.vertexStart = read_int32(wmb_fp)
        self.indexStart = read_int32(wmb_fp)
        self.numVertexes = read_uint32(wmb_fp)
        self.numIndexes = read_uint32(wmb_fp)
        if DEBUG_BATCHES_PRINT:
            print(" ",
              self.vertexGroupIndex.ljust(10, " "),
              ("%d-%d" % (self.vertexStart, self.vertexStart + self.numVertexes)).ljust(11, " "),
              ("%d-%d" % (self.indexStart, self.indexStart + self.numIndexes))
            )
        

class wmb4_batchDescription(object):
    """docstring for wmb4_batchDescription"""
    def read(self, wmb_fp):
        self.batchDataPointers = []
        self.batchDataCounts = []
        self.batchData = []
        #print("Iterating over 4, length %d" % 4)
        for dataNum in range(4):
            if DEBUG_BATCHSUPPLEMENT_PRINT:
                print("Batch supplement for group", dataNum)
            self.batchDataPointers.append(read_uint32(wmb_fp))
            self.batchDataCounts.append(read_uint32(wmb_fp))
            self.batchData.append(load_data_array(wmb_fp, self.batchDataPointers[-1], self.batchDataCounts[-1], wmb4_batchData))
        #print("Batch data pointers:", [hex(f) for f in self.batchDataPointers])

class wmb4_batchData(object):
    """docstring for wmb4_batchData"""
    def read(self, wmb_fp):
        self.batchIndex = read_uint32(wmb_fp)
        self.meshIndex = read_uint32(wmb_fp)
        self.materialIndex = read_uint16(wmb_fp)
        self.boneSetsIndex = read_int16(wmb_fp)
        self.unknown10 = read_uint32(wmb_fp) # again, maybe just padding
        
        if DEBUG_BATCHSUPPLEMENT_PRINT:
            print(" Batch: %s;   Mesh: %s;   Material: %s;   Bone set: %s" % (str(self.batchIndex).rjust(3, " "), str(self.meshIndex).rjust(3, " "), str(self.materialIndex).rjust(3, " "), str(self.boneSetsIndex).rjust(3, " ")))

class wmb4_bone(object):
    """docstring for wmb4_bone"""
    def read(self, wmb_fp, index):
        super(wmb4_bone, self).__init__()
        self.boneIndex = index
        self.boneNumber = read_int16(wmb_fp)
        self.unknown02 = read_int16(wmb_fp) # one is global index
        self.parentIndex = read_int16(wmb_fp)
        self.unknownRotation = read_int16(wmb_fp) # rotation order or smth

        relativePositionX = read_float(wmb_fp)
        relativePositionY = read_float(wmb_fp)
        relativePositionZ = read_float(wmb_fp)
        
        positionX = read_float(wmb_fp)
        positionY = read_float(wmb_fp)
        positionZ = read_float(wmb_fp)

        self.local_position = (relativePositionX, relativePositionY, relativePositionZ)
        self.local_rotation = (0, 0, 0)
        
        self.world_position = (positionX, positionY, positionZ)
        self.world_rotation = (relativePositionX, relativePositionY, relativePositionZ)
        #self.boneNumber = self.boneIndex
        # self... wait, why is world_rotation used twice?
        self.world_position_tpose = (0, 0, 0)
        
        if DEBUG_BONE_PRINT:
            # there are lots of bones, so this should be compressed better
            print()
            print("index:      ", index)
            print("ID:         ", self.boneNumber)
            print("Unknown:    ", self.unknown02)
            print("Parent:     ", self.parentIndex)
            print("Rotation(?):", self.unknownRotation)
            print("Position A: ", "(%s, %s, %s)" % self.local_position)
            print("Position B: ", "(%s, %s, %s)" % self.world_position)
        

class wmb4_boneSet(object):
    """docstring for wmb4_boneSet"""
    def read(self, wmb_fp):
        super(wmb4_boneSet, self).__init__()
        self.pointer = read_uint32(wmb_fp)
        self.count = read_uint32(wmb_fp)
        self.boneSet = load_data_array(wmb_fp, self.pointer, self.count, uint8)
        if DEBUG_BONESET_PRINT:
            print("Count:", self.count, "Data:", self.boneSet)

class wmb4_boneTranslateTable(object):
    """docstring for wmb4_boneTranslateTable"""
    def read(self, wmb_fp):
        self.firstLevel = []
        self.secondLevel = []
        self.thirdLevel = []
        for entry in range(16):
            self.firstLevel.append(read_int16(wmb_fp))

        firstLevel_Entry_Count = 0
        for entry in self.firstLevel:
            if entry != -1:
                firstLevel_Entry_Count += 1

        #print("Iterating over firstLevel_Entry_Count * 16, length %d" % firstLevel_Entry_Count * 16)
        for entry in range(firstLevel_Entry_Count * 16):
            self.secondLevel.append(read_int16(wmb_fp))

        secondLevel_Entry_Count = 0
        for entry in self.secondLevel:
            if entry != -1:
                secondLevel_Entry_Count += 1

        #print("Iterating over secondLevel_Entry_Count * 16, length %d" % secondLevel_Entry_Count * 16)
        for entry in range(secondLevel_Entry_Count * 16):
            self.thirdLevel.append(read_int16(wmb_fp))

class wmb4_material(object):
    """docstring for wmb4_material"""
    class paramFunc(object):
        def read(self, wmb_fp):
            self.x = read_float(wmb_fp)
            self.y = read_float(wmb_fp)
            self.z = read_float(wmb_fp)
            self.w = read_float(wmb_fp)
    
    def read(self, wmb_fp):
        super(wmb4_material, self).__init__()
        self.shaderNamePointer = read_uint32(wmb_fp)
        self.texturesPointer = read_uint32(wmb_fp)
        # by context, probably another offset.
        # check for unread data in the file.
        self.unknown08 = read_uint32(wmb_fp)
        self.parametersPointer = read_uint32(wmb_fp)
        
        self.texturesCount = read_uint16(wmb_fp) # wait so what's this
        self.trueTexturesCount = read_uint16(wmb_fp) # texture count, 4 or 5
        self.unknown14 = read_uint16(wmb_fp) # and the mystery count.
        self.parametersCount = read_uint16(wmb_fp)
        
        texturesArray = load_data_array(wmb_fp, self.texturesPointer, self.trueTexturesCount*2, uint32)
        
        if self.parametersCount/4 % 1 != 0:
            print("Hey, idiot, you have incomplete parameters in your materials. It's gonna read some garbage data, since each one should have exactly four attributes: xyzw. Actually, I'm not sure if it'll read garbage or stop early. Idiot.")
        
        self.parameters = load_data_array(wmb_fp, self.parametersPointer, int(self.parametersCount/4), self.paramFunc)
        
        self.effectName = load_data(wmb_fp, self.shaderNamePointer, filestring)
        self.techniqueName = "NoTechnique"
        self.uniformArray = {}
        self.textureArray = {}
        self.textureFlagArray = []
        for i, texture in enumerate(texturesArray):
            if i % 2 == 0:
                self.textureFlagArray.append(texture)
                continue
            else:
                trueI = int((i - 1) / 2) # bad method, don't care tonight
            if self.textureFlagArray[trueI] in {0, 1}:
                self.textureArray["albedoMap" + str(trueI)] = texture
            elif self.textureFlagArray[trueI] == 2:
                self.textureArray["normalMap" + str(trueI)] = texture
            elif self.textureFlagArray[trueI] == 7:
                self.textureArray["specularMap" + str(trueI)] = texture
            else:
                self.textureArray["tex" + str(trueI)] = texture
        
        if DEBUG_MATERIAL_PRINT:
            print("Count:", self.trueTexturesCount*2, "Data:", texturesArray)
            print("Shader params:", [(a.x, a.y, a.z, a.w) for a in self.parameters])
        self.parameterGroups = self.parameters
        self.materialName = "UnusedMaterial" # mesh name overrides
        self.wmb4 = True

class wmb4_mesh(object):
    """docstring for wmb4_mesh"""
    def read(self, wmb_fp, scr_mode=None):
        super(wmb4_mesh, self).__init__()
        self.namePointer = read_uint32(wmb_fp)
        self.boundingBox = []
        #print("Iterating over 6, length %d" % 6)
        for i in range(6):
            self.boundingBox.append(read_float(wmb_fp))
        
        self.batch0Pointer = read_uint32(wmb_fp)
        self.batch0Count = read_uint32(wmb_fp)
        self.batch1Pointer = read_uint32(wmb_fp)
        self.batch1Count = read_uint32(wmb_fp)
        self.batch2Pointer = read_uint32(wmb_fp)
        self.batch2Count = read_uint32(wmb_fp)
        self.batch3Pointer = read_uint32(wmb_fp)
        self.batch3Count = read_uint32(wmb_fp)
        
        self.materialsPointer = read_uint32(wmb_fp)
        self.materialsCount = read_uint32(wmb_fp)
        
        self.name = load_data(wmb_fp, self.namePointer, filestring)
        if scr_mode is not None and scr_mode[0]:
            if self.name != "SCR_MESH":
                print()
                print("Hey, very interesting. A map file with custom mesh names.")
            else:
                self.name = scr_mode[1]
        if DEBUG_MESH_PRINT:
            print("\nMesh name: %s" % self.name)
        
        self.batches0 = load_data_array(wmb_fp, self.batch0Pointer, self.batch0Count, uint16)
        self.batches1 = load_data_array(wmb_fp, self.batch1Pointer, self.batch1Count, uint16)
        self.batches2 = load_data_array(wmb_fp, self.batch2Pointer, self.batch2Count, uint16)
        self.batches3 = load_data_array(wmb_fp, self.batch3Pointer, self.batch3Count, uint16)
        if DEBUG_MESH_PRINT:
            print("Batches:", self.batches0, self.batches1, self.batches2, self.batches3)
        
        self.materials = load_data_array(wmb_fp, self.materialsPointer, self.materialsCount, uint16)

class wmb4_texture(object):
    """The WMB4 texture is delightfully simple."""
    def read(self, wmb_fp):
        super(wmb4_texture, self).__init__()
        self.flags = read_uint32(wmb_fp)
        self.id = "%08x" % read_uint32(wmb_fp)

class wmb4_vertexGroup(object):
    """docstring for wmb4_vertexGroup"""
    def size(a):
        return 28 + 0
    def read(self, wmb_fp, vertexFormat):
        self.vertexesDataPointer = read_uint32(wmb_fp)
        self.extraVertexesDataPointer = read_uint32(wmb_fp)
        self.unknownPointer = read_uint32(wmb_fp)
        self.unknownCount = read_uint32(wmb_fp) # might actually be another pointer lol idk
        # or what if it's just padding?
        self.vertexesCount = read_uint32(wmb_fp)
        self.faceIndexesPointer = read_uint32(wmb_fp)
        self.faceIndexesCount = read_uint32(wmb_fp)
        
        
        if DEBUG_VERTEXGROUP_PRINT:
            print()
            print("Vertex group information    Pointer Count")
            print(" vertexesData            " + hex(self.vertexesDataPointer).rjust(10, " ") + str(self.vertexesCount).rjust(6, " "))
            print(" extraVertexesData       " + hex(self.extraVertexesDataPointer).rjust(10, " "))
            print(" unknown                 " + hex(self.unknownPointer).rjust(10, " ") + str(self.unknownCount).rjust(6, " "))
            print(" faceIndexes             " + hex(self.faceIndexesPointer).rjust(10, " ") + str(self.faceIndexesCount).rjust(6, " "))
        
        
        self.vertexArray = load_data_array(wmb_fp, self.vertexesDataPointer, self.vertexesCount, wmb4_vertex, vertexFormat)
        
        if vertexFormat in {0x10337, 0x10137, 0x00337}:
            self.vertexesExDataArray = load_data_array(wmb_fp, self.extraVertexesDataPointer, self.vertexesCount, wmb4_vertexExData, vertexFormat)
        else:
            self.vertexesExDataArray = [None] * self.vertexesCount
        
        self.unknownArray = load_data_array(wmb_fp, self.unknownPointer, self.unknownCount, uint32)
        # mercifully empty
        
        self.faceRawArray = load_data_array(wmb_fp, self.faceIndexesPointer, self.faceIndexesCount, uint16)
        
        self.vertexFlags = None # <trollface>

class wmb4_vertex(object):
    smartRead10337 = SmartIO.makeFormat( # 10137, 00337, 00137 same
        SmartIO.float,   # x
        SmartIO.float,   # y
        SmartIO.float,   # z
        SmartIO.float16, # texture u
        SmartIO.float16, # texture v
        SmartIO.uint8,   # normal x
        SmartIO.uint8,   # normal y
        SmartIO.uint8,   # normal z
        SmartIO.uint8,   # normal padding
        SmartIO.uint8,   # tangent x
        SmartIO.uint8,   # tangent y
        SmartIO.uint8,   # tangent z
        SmartIO.uint8,   # tangent d
        SmartIO.uint8, SmartIO.uint8, SmartIO.uint8, SmartIO.uint8, # boneIndexes
        SmartIO.uint8, SmartIO.uint8, SmartIO.uint8, SmartIO.uint8  # boneWeights
    )
    smartRead10307 = SmartIO.makeFormat(
        SmartIO.float,   # x
        SmartIO.float,   # y
        SmartIO.float,   # z
        SmartIO.float16, # texture u
        SmartIO.float16, # texture v
        SmartIO.uint8,   # normal x
        SmartIO.uint8,   # normal y
        SmartIO.uint8,   # normal z
        SmartIO.uint8,   # normal padding
        SmartIO.uint8,   # tangent x
        SmartIO.uint8,   # tangent y
        SmartIO.uint8,   # tangent z
        SmartIO.uint8,   # tangent d
        SmartIO.uint32,  # color
        SmartIO.float16, # texture2 u
        SmartIO.float16  # texture2 v
    )
    smartRead10107 = SmartIO.makeFormat(
        SmartIO.float,   # x
        SmartIO.float,   # y
        SmartIO.float,   # z
        SmartIO.float16, # texture u
        SmartIO.float16, # texture v
        SmartIO.uint8,   # normal x
        SmartIO.uint8,   # normal y
        SmartIO.uint8,   # normal z
        SmartIO.uint8,   # normal padding
        SmartIO.uint8,   # tangent x
        SmartIO.uint8,   # tangent y
        SmartIO.uint8,   # tangent z
        SmartIO.uint8,   # tangent d
        SmartIO.uint32   # color
    )
    smartRead00107 = SmartIO.makeFormat(
        SmartIO.float,   # x
        SmartIO.float,   # y
        SmartIO.float,   # z
        SmartIO.float16, # texture u
        SmartIO.float16, # texture v
        SmartIO.uint8,   # normal x
        SmartIO.uint8,   # normal y
        SmartIO.uint8,   # normal z
        SmartIO.uint8,   # normal padding
        SmartIO.uint8,   # tangent x
        SmartIO.uint8,   # tangent y
        SmartIO.uint8,   # tangent z
        SmartIO.uint8,   # tangent d
    )
    
    """docstring for wmb4_vertex"""
    def read(self, wmb_fp, vertexFormat):
        if (vertexFormat & 0x137) == 0x137: # 10337, 10137, 00337, 00137, all match this
            # everything I did with the indexes is horrible here todo fix
            boneIndex = [0] * 4
            boneWeight = [0] * 4
            self.positionX, self.positionY, self.positionZ, \
            self.textureU, self.textureV, \
            self.normalX, self.normalY, self.normalZ, _, \
            self.tangentX, self.tangentY, self.tangentZ, self.tangentD, \
            boneIndex[0], boneIndex[1], boneIndex[2], boneIndex[3], \
            boneWeight[0], boneWeight[1], boneWeight[2], boneWeight[3] \
            = wmb4_vertex.smartRead10337.read(wmb_fp)
            self.boneIndices = boneIndex
            self.boneWeights = [weight/255 for weight in boneWeight]
            # All these values are discarded??
            self.normalX *= 2/255
            self.normalY *= 2/255
            self.normalZ *= 2/255
            self.tangentX *= 2/255
            self.tangentY *= 2/255
            self.tangentZ *= 2/255
            self.tangentD *= 2/255
            return
        
        elif vertexFormat == 0x10307:
            self.positionX, self.positionY, self.positionZ, \
            self.textureU, self.textureV, \
            self.normalX, self.normalY, self.normalZ, _, \
            self.tangentX, self.tangentY, self.tangentZ, self.tangentD, \
            self.color, \
            self.textureU2, self.textureV2 \
            = wmb4_vertex.smartRead10307.read(wmb_fp)
            
            self.color = list(struct.unpack("<BBBB", struct.pack("<I", self.color))) # byte me
            return
            
        elif vertexFormat == 0x10107:
            self.positionX, self.positionY, self.positionZ, \
            self.textureU, self.textureV, \
            self.normalX, self.normalY, self.normalZ, _, \
            self.tangentX, self.tangentY, self.tangentZ, self.tangentD, \
            self.color \
            = wmb4_vertex.smartRead10107.read(wmb_fp)
            
            self.color = list(struct.unpack("<BBBB", struct.pack("<I", self.color))) # byte me
            return
            
        elif vertexFormat == 0x00107:
            self.positionX, self.positionY, self.positionZ, \
            self.textureU, self.textureV, \
            self.normalX, self.normalY, self.normalZ, _, \
            self.tangentX, self.tangentY, self.tangentZ, self.tangentD \
            = wmb4_vertex.smartRead00107.read(wmb_fp)
            return
            
        else:
            print("God fucking DAMMIT Kris, the vertex format is %s." % hex(vertexFormat))
            return

class wmb4_vertexExData(object):
    """docstring for wmb4_vertexExData"""
    def read(self, wmb_fp, vertexFormat):
        if (vertexFormat & 0x337) == 0x337: # both 10337 and 00337
            self.color = list(read_uint8_x4(wmb_fp))
            self.textureU2 = read_float16(wmb_fp)
            self.textureV2 = read_float16(wmb_fp)
            return
            
        elif vertexFormat == 0x10137:
            self.color = list(read_uint8_x4(wmb_fp))
            return
        
        else:
            print("How the FUCK did you get here, the function call is *directly* inside a check for vertexFormat matching... Somehow, it's", hex(vertexFormat))
            return

class int16(object):
    """
    int16 class for reading data and
    returning to original location via load_data
    """
    type = "int"
    def __init__(self):
        self.val = 0
    def read(self, wmb_fp):
        self.val = read_int16(wmb_fp)

class uint16(object):
    """
    uint16 class for reading data and
    returning to original location via load_data
    """
    type = "int"
    def __init__(self):
        self.val = 0
    def read(self, wmb_fp):
        self.val = read_uint16(wmb_fp)

class uint8(object):
    """
    uint8 class for reading data and
    returning to original location via load_data
    """
    type = "int"
    def __init__(self):
        self.val = 0
    def read(self, wmb_fp):
        self.val = read_uint8(wmb_fp)

class uint32(object):
    """
    uint32 class for reading data and
    returning to original location via load_data
    """
    type = "int"
    def __init__(self):
        self.val = 0
    def read(self, wmb_fp):
        self.val = read_uint32(wmb_fp)

class filestring(object):
    """
    filestring class for reading data and
    returning to original location via load_data
    """
    type = "string"
    def __init__(self):
        self.val = ""
    def read(self, wmb_fp):
        self.val = read_string(wmb_fp)

class WMB(object):
    """docstring for WMB"""
    def __init__(self, wmb_file, only_extract):
        super(WMB, self).__init__()
        wmb_fp = 0
        wta_fp = 0
        wtp_fp = 0
        self.wta = 0

        wmb_path = wmb_file
        if not os.path.exists(wmb_path):
            wmb_path = wmb_file.replace('.dat','.dtt')
        wtp_path = wmb_file.replace('.dat','.dtt').replace('.wmb','.wtp')
        wta_path = wmb_file.replace('.dtt','.dat').replace('.wmb','.wta')
        scr_mode = False
        wmbinscr_name = ""
        if "extracted_scr" in wmb_path:
            scr_mode = True
            split_path = wmb_file.replace("/", "\\").split("\\")
            wmbinscr_name = split_path.pop()[:-4] # wmb name
            split_path.pop() # "extracted_scr"
            datdttname = split_path.pop()[:-4] # e.g. "ra01"
            # wtb is both wtp and wta
            wtp_path = "\\".join(split_path) + "\\%s.dtt\\%sscr.wtb" % (datdttname, datdttname)
            wta_path = "\\".join(split_path) + "\\%s.dtt\\%sscr.wtb" % (datdttname, datdttname)
            if os.path.exists(wtp_path.replace('scr.wtb', 'cmn.wtb')):
                # common files, jackpot!
                pass # todo: load this somewhere other files can get it
        if os.path.exists(wtp_path):    
            print('open wtp file')
            self.wtp_fp = open(wtp_path,'rb')
        if os.path.exists(wta_path):
            print('open wta file')
            wta_fp = open(wta_path,'rb')
        
        self.wta = None
        if wta_fp:
            self.wta = WTA(wta_fp)
            wta_fp.close()

        if os.path.exists(wmb_path):
            wmb_fp = open(wmb_path, "rb")
        else:
            print("DTT/DAT does not contain WMB file.")
            print("Last attempted path:", wmb_path)
            return
        
        
        
        self.wmb_header = WMB_Header(wmb_fp)
        if self.wmb_header.magicNumber == b'WMB3':
            self.hasBone = False
            if self.wmb_header.boneCount > 0:
                self.hasBone = True

            wmb_fp.seek(self.wmb_header.bonePointer)
            #print("Seeking to self.wmb_header.bonePointer: %s" % hex(self.wmb_header.bonePointer))
            self.boneArray = []
            #print("Iterating over self.wmb_header.boneCount, length %d" % self.wmb_header.boneCount)
            for boneIndex in range(self.wmb_header.boneCount):
                self.boneArray.append(wmb3_bone(wmb_fp,boneIndex))
            
            # indexBoneTranslateTable
            self.firstLevel = []
            self.secondLevel = []
            self.thirdLevel = []
            if self.wmb_header.boneTranslateTablePointer > 0:
                wmb_fp.seek(self.wmb_header.boneTranslateTablePointer)
                #print("Seeking to self.wmb_header.boneTranslateTablePointer: %s" % hex(self.wmb_header.boneTranslateTablePointer))
                #print("Iterating over 16, length %d" % 16)
                for entry in range(16):
                    self.firstLevel.append(read_uint16(wmb_fp))
                    if self.firstLevel[-1] == 65535:
                        self.firstLevel[-1] = -1

                firstLevel_Entry_Count = 0
                for entry in self.firstLevel:
                    if entry != -1:
                        firstLevel_Entry_Count += 1

                #print("Iterating over firstLevel_Entry_Count * 16, length %d" % firstLevel_Entry_Count * 16)
                for entry in range(firstLevel_Entry_Count * 16):
                    self.secondLevel.append(read_uint16(wmb_fp))
                    if self.secondLevel[-1] == 65535:
                        self.secondLevel[-1] = -1

                secondLevel_Entry_Count = 0
                for entry in self.secondLevel:
                    if entry != -1:
                        secondLevel_Entry_Count += 1

                #print("Iterating over secondLevel_Entry_Count * 16, length %d" % secondLevel_Entry_Count * 16)
                for entry in range(secondLevel_Entry_Count * 16):
                    self.thirdLevel.append(read_uint16(wmb_fp))
                    if self.thirdLevel[-1] == 65535:
                        self.thirdLevel[-1] = -1


                wmb_fp.seek(self.wmb_header.boneTranslateTablePointer)
                #print("Seeking to self.wmb_header.boneTranslateTablePointer: %s" % hex(self.wmb_header.boneTranslateTablePointer))
                unknownData1Array = []
                #print("Iterating over self.wmb_header.boneTranslateTableSize, length %d" % self.wmb_header.boneTranslateTableSize)
                for i in range(self.wmb_header.boneTranslateTableSize):
                    unknownData1Array.append(read_uint8(wmb_fp))

            self.materialArray = []
            #print("Iterating over self.wmb_header.materialCount, length %d" % self.wmb_header.materialCount)
            for materialIndex in range(self.wmb_header.materialCount):
                wmb_fp.seek(self.wmb_header.materialPointer + materialIndex * 0x30)
                #print("Seeking to self.wmb_header.materialPointer + materialIndex * 0x30: %s" % hex(self.wmb_header.materialPointer + materialIndex * 0x30))
                material = wmb3_material(wmb_fp)
                self.materialArray.append(material)

            if only_extract:
                return

            self.vertexGroupArray = []
            #print("Iterating over self.wmb_header.vertexGroupCount, length %d" % self.wmb_header.vertexGroupCount)
            for vertexGroupIndex in range(self.wmb_header.vertexGroupCount):
                wmb_fp.seek(self.wmb_header.vertexGroupPointer + 0x30 * vertexGroupIndex)
                #print("Seeking to self.wmb_header.vertexGroupPointer + 0x30 * vertexGroupIndex: %s" % hex(self.wmb_header.vertexGroupPointer + 0x30 * vertexGroupIndex))

                vertexGroup = wmb3_vertexGroup(wmb_fp,((self.wmb_header.flags & 0x8) and 4 or 2))
                self.vertexGroupArray.append(vertexGroup)

            self.meshArray = []
            wmb_fp.seek(self.wmb_header.meshPointer)
            #print("Seeking to self.wmb_header.meshPointer: %s" % hex(self.wmb_header.meshPointer))
            #print("Iterating over self.wmb_header.meshCount, length %d" % self.wmb_header.meshCount)
            for meshIndex in range(self.wmb_header.meshCount):
                mesh = wmb3_mesh(wmb_fp)
                self.meshArray.append(mesh)

            self.meshGroupInfoArray = []
            #print("Iterating over self.wmb_header.meshGroupInfoCount, length %d" % self.wmb_header.meshGroupInfoCount)
            for meshGroupInfoArrayIndex in range(self.wmb_header.meshGroupInfoCount):
                wmb_fp.seek(self.wmb_header.meshGroupInfoPointer + meshGroupInfoArrayIndex * 0x14)
                #print("Seeking to self.wmb_header.meshGroupInfoPointer + meshGroupInfoArrayIndex * 0x14: %s" % hex(self.wmb_header.meshGroupInfoPointer + meshGroupInfoArrayIndex * 0x14))
                meshGroupInfo= wmb3_meshGroupInfo(wmb_fp)
                self.meshGroupInfoArray.append(meshGroupInfo)

            self.meshGroupArray = []
            #print("Iterating over self.wmb_header.meshGroupCount, length %d" % self.wmb_header.meshGroupCount)
            for meshGroupIndex in range(self.wmb_header.meshGroupCount):
                wmb_fp.seek(self.wmb_header.meshGroupPointer + meshGroupIndex * 0x2c)
                #print("Seeking to self.wmb_header.meshGroupPointer + meshGroupIndex * 0x2c: %s" % hex(self.wmb_header.meshGroupPointer + meshGroupIndex * 0x2c))
                meshGroup = wmb3_meshGroup(wmb_fp)
                
                self.meshGroupArray.append(meshGroup)

            wmb_fp.seek(self.wmb_header.boneMapPointer)
            #print("Seeking to self.wmb_header.boneMapPointer: %s" % hex(self.wmb_header.boneMapPointer))
            self.boneMap = []
            #print("Iterating over self.wmb_header.boneMapCount, length %d" % self.wmb_header.boneMapCount)
            for index in range(self.wmb_header.boneMapCount):
                self.boneMap.append(read_uint32(wmb_fp))
            wmb_fp.seek(self.wmb_header.boneSetPointer)
            #print("Seeking to self.wmb_header.boneSetPointer: %s" % hex(self.wmb_header.boneSetPointer))
            self.boneSetArray = wmb3_boneSet(wmb_fp, self.wmb_header.boneSetCount).boneSetArray

            # colTreeNode
            self.hasColTreeNodes = False
            if self.wmb_header.colTreeNodesPointer > 0:
                self.hasColTreeNodes = True
                self.colTreeNodes = []
                wmb_fp.seek(self.wmb_header.colTreeNodesPointer)
                #print("Seeking to self.wmb_header.colTreeNodesPointer: %s" % hex(self.wmb_header.colTreeNodesPointer))
                #print("Iterating over self.wmb_header.colTreeNodesCount, length %d" % self.wmb_header.colTreeNodesCount)
                for index in range(self.wmb_header.colTreeNodesCount):
                    self.colTreeNodes.append(wmb3_colTreeNode(wmb_fp))
            
            # World Model Data
            self.hasUnknownWorldData = False
            if self.wmb_header.unknownWorldDataPointer > 0:
                self.hasUnknownWorldData = True
                self.unknownWorldDataArray = []
                wmb_fp.seek(self.wmb_header.unknownWorldDataPointer)
                #print("Seeking to self.wmb_header.unknownWorldDataPointer: %s" % hex(self.wmb_header.unknownWorldDataPointer))
                #print("Iterating over self.wmb_header.unknownWorldDataCount, length %d" % self.wmb_header.unknownWorldDataCount)
                for index in range(self.wmb_header.unknownWorldDataCount):
                    self.unknownWorldDataArray.append(wmb3_worldData(wmb_fp))
        
        elif self.wmb_header.magicNumber == b'WMB4':
            self.vertexGroupArray = load_data_array(wmb_fp, self.wmb_header.vertexGroupPointer, self.wmb_header.vertexGroupCount, wmb4_vertexGroup, self.wmb_header.vertexFormat)
            
            if DEBUG_BATCHES_PRINT:
                print()
                print("Batches:")
                print("vertexGroup vertexRange indexRange")
            self.batchArray = load_data_array(wmb_fp, self.wmb_header.batchPointer, self.wmb_header.batchCount, wmb4_batch)
            
            if DEBUG_BATCHSUPPLEMENT_PRINT:
                print()
                print("Batch supplement data:")
            self.batchDescription = load_data(wmb_fp, self.wmb_header.batchDescriptionPointer, wmb4_batchDescription)
            self.batchDataArray = []
            for batchDataSubgroup in self.batchDescription.batchData:
                self.batchDataArray.extend(batchDataSubgroup)
            
            # hack
            for dataNum, batchDataSubgroup in enumerate(self.batchDescription.batchData):
                for batchData in batchDataSubgroup:
                    self.batchArray[batchData.batchIndex].batchGroup = dataNum
            
            self.hasBone = self.wmb_header.boneCount > 0
            if DEBUG_BONE_PRINT:
                print()
                print("Bones?", self.hasBone)
                if self.hasBone:
                    print("Enjoy the debug bone data:")
            self.boneArray = load_data_array(wmb_fp, self.wmb_header.bonePointer, self.wmb_header.boneCount, wmb4_bone, None, True)
            
            if DEBUG_BITT_PRINT:
                print()
                print("The boneIndexTranslateTable? I got no debug info besides what's in the header.")
            boneTranslateTable = load_data(wmb_fp, self.wmb_header.boneTranslateTablePointer, wmb4_boneTranslateTable)
            if boneTranslateTable is not None:
                self.firstLevel = boneTranslateTable.firstLevel
                self.secondLevel = boneTranslateTable.secondLevel
                self.thirdLevel = boneTranslateTable.thirdLevel
            
            if DEBUG_BONESET_PRINT:
                print()
                print("Bonesets:")
            boneSetArrayTrue = load_data_array(wmb_fp, self.wmb_header.boneSetPointer, self.wmb_header.boneSetCount, wmb4_boneSet)
            # is this cheating
            self.boneSetArray = [item.boneSet for item in boneSetArrayTrue]
            #print(self.boneSetArray)
            
            if DEBUG_MATERIAL_PRINT:
                print()
                print("Material info (specifically textures, not shaders; not yet):")
            self.materialArray = load_data_array(wmb_fp, self.wmb_header.materialPointer, self.wmb_header.materialCount, wmb4_material)
            
            if DEBUG_TEXTURE_PRINT:
                print()
                print("Just have the textures array if you care so bad")
            self.textureArray = load_data_array(wmb_fp, self.wmb_header.texturePointer, self.wmb_header.textureCount, wmb4_texture)
            if DEBUG_TEXTURE_PRINT:
                print([(item.id, hex(item.flags)) for item in self.textureArray])
            
            if DEBUG_MESH_PRINT:
                print()
                print("Meshes (batches separated by batchGroup, naturally):")
            self.meshArray = load_data_array(wmb_fp, self.wmb_header.meshPointer, self.wmb_header.meshCount, wmb4_mesh, [scr_mode, wmbinscr_name])
            
            for mesh in self.meshArray:
                for materialIndex, material in enumerate(mesh.materials):
                    self.materialArray[material].materialName = mesh.name + "-%d" % materialIndex
            
            self.boneMap = None # <trollface>
            self.hasColTreeNodes = False # maybe this could be before the version check
            self.hasUnknownWorldData = False
            
            print("\n\n")
            print("Continuing to wmb_importer.py...\n")
        
        else:
            print("You madman! This isn't WMB3 or WMB4, but %s!" % self.wmb_header.magicNumber.decode("ascii"))

    def clear_unused_vertex(self, meshArrayIndex,vertexGroupIndex, wmb4=False):
        mesh = self.meshArray[meshArrayIndex]
        vertexGroup = self.vertexGroupArray[vertexGroupIndex]
        
        faceRawStart = mesh.faceStart
        faceRawCount = mesh.faceCount
        vertexStart = mesh.vertexStart
        vertexCount = mesh.vertexCount

        vertexesExData = vertexGroup.vertexesExDataArray[vertexStart : vertexStart + vertexCount]

        vertex_colors = []
        
        facesRaw = vertexGroup.faceRawArray[faceRawStart : faceRawStart + faceRawCount ]
        if not wmb4:
            facesRaw = [index - 1 for index in facesRaw]
        usedVertexIndexArray = sorted(list(set(facesRaw))) # oneliner to remove duplicates
        
        """
        print("Vertex group index:", vertexGroupIndex, "Face first index:", faceRawStart, "Face last index:", faceRawStart+faceRawCount)
        print("Faces range from %d to %d" % (min(facesRaw), max(facesRaw)))
        print([("[" if i%3==0 else "") + str(face).rjust(3, " ") + ("]" if i%3==2 else "") for i, face in enumerate(facesRaw)])
        """
        # mappingDict is the reverse lookup for usedVertexIndexArray
        mappingDict = {}
        for newIndex, vertid in enumerate(usedVertexIndexArray):
            mappingDict[vertid] = newIndex
        #print(mappingDict)
        # After this loop, facesRaw now points to indexes in usedVertices (below)
        for i, vertex in enumerate(facesRaw):
            facesRaw[i] = mappingDict[vertex]
        faces = [0] * int(faceRawCount / 3)
        usedVertices = [0] * len(usedVertexIndexArray)
        boneWeightInfos = [[],[]]
        #print("Iterating over 0, faceRawCount, 3, length %d" % 0, faceRawCount, 3)
        for i in range(0, faceRawCount, 3):
            faces[int(i/3)] = ( facesRaw[i], facesRaw[i + 1], facesRaw[i + 2] )
        meshVertices = vertexGroup.vertexArray[vertexStart : vertexStart + vertexCount]

        if self.hasBone:
            boneWeightInfos = [0] * len(usedVertexIndexArray)
        for newIndex, i in enumerate(usedVertexIndexArray):
            usedVertices[newIndex] = (meshVertices[i].positionX, meshVertices[i].positionY, meshVertices[i].positionZ)

            # Vertex_Colors are stored in VertexData
            if vertexGroup.vertexFlags in {4, 5, 12, 14} or (wmb4 and self.wmb_header.vertexFormat in {0x10307, 0x10107}):
                vertex_colors.append(meshVertices[i].color)
            # Vertex_Colors are stored in VertexExData
            if vertexGroup.vertexFlags in {10, 11} or (wmb4 and self.wmb_header.vertexFormat in {0x10337, 0x10137, 0x00337}):
                vertex_colors.append(vertexesExData[i].color)

            if self.hasBone:
                bonesetIndex = mesh.bonesetIndex
                if bonesetIndex != -1:
                    boneSet = self.boneSetArray[bonesetIndex]
                    if not wmb4:
                        boneIndices = [self.boneMap[boneSet[index]] for index in meshVertices[i].boneIndices]
                    else:
                        #boneIndices = meshVertices[i].boneIndices
                        # this is really rather obvious
                        try:
                            boneIndices = [boneSet[index] for index in meshVertices[i].boneIndices]
                        except:
                            print()
                            print("Hey! Something's wrong with the bone set. The mesh %s has these bone indices:" % mesh.name)
                            #print([vertexes.boneIndices for vertexes in meshVertices])
                            print("...nevermind that's way too much to print")
                            print("(They go up to %d)" % max([max(vertexes.boneIndices) for vertexes in meshVertices]))
                            print("But the bone set (#%d) only has %d bones." % (bonesetIndex, len(boneSet)))
                            print("How terrible! Time to crash.")
                            assert False
                    boneWeightInfos[newIndex] = [boneIndices, meshVertices[i].boneWeights]
                    s = sum(meshVertices[i].boneWeights)
                    if s > 1.000000001 or s < 0.999999:
                        print('[-] error weight detect %f' % s)
                        print(meshVertices[i].boneWeights) 
                else:
                    self.hasBone = False
        return usedVertices, faces, usedVertexIndexArray, boneWeightInfos, vertex_colors, vertexStart

def load_data(wmb_fp, pointer, chunkClass, other=None):
    pos = wmb_fp.tell()
    final = None
    if pointer > 0:
        wmb_fp.seek(pointer)
        #print("Seeking to %sPointer: %s" % (chunkClass.__name__, hex(pointer)))
        final = chunkClass()
        if other is not None:
            final.read(wmb_fp, other)
        else:
            final.read(wmb_fp)
        wmb_fp.seek(pos)
        if "type" in chunkClass.__dict__ and chunkClass.type in {"int", "string"}:
            return final.val
    return final

def load_data_array(wmb_fp, pointer, count, chunkClass, other=None, useIndex=False):
    array = []
    pos = wmb_fp.tell()
    if pointer > 0:
        wmb_fp.seek(pointer)
        #print("Seeking to %sPointer: %s" % (chunkClass.__name__, hex(pointer)))
        
        # putting the for in the if is, uh, maybe optimized idk
        if other is not None:
            #print("Iterating over %sCount, length %d" % (chunkClass.__name__, count))
            for itemIndex in range(count):
                #print("This could be a print. %d" % itemIndex)
                item = chunkClass()
                item.read(wmb_fp, other)
                if "type" in chunkClass.__dict__ and chunkClass.type in {"int", "string"}:
                    item = item.val
                array.append(item)
        elif useIndex:
            #print("Iterating over %sCount, length %d" % (chunkClass.__name__, count))
            for itemIndex in range(count):
                #print("This could be a print. %d" % itemIndex)
                item = chunkClass()
                item.read(wmb_fp, itemIndex)
                if "type" in chunkClass.__dict__ and chunkClass.type in {"int", "string"}:
                    item = item.val
                array.append(item)
        else:
            #print("Iterating over %sCount, length %d" % (chunkClass.__name__, count))
            for itemIndex in range(count):
                #print("This could be a print. %d" % itemIndex)
                item = chunkClass()
                item.read(wmb_fp)
                if "type" in chunkClass.__dict__ and chunkClass.type in {"int", "string"}:
                    item = item.val
                array.append(item)
        wmb_fp.seek(pos)
        #print("Seeking to return position: %s" % hex(pos))
    return array


def export_obj(wmb, wta, wtp_fp, obj_file):
    if not obj_file:
        obj_file = 'test'
    create_dir('out/%s'%obj_file)
    obj_file = 'out/%s/%s'%(obj_file, obj_file)
    textureArray = []
    
    if (wta and wtp_fp):
        #print("Iterating over wmb.wmb_header.materialCount, length %d" % wmb.wmb_header.materialCount)
        for materialIndex in range(wmb.wmb_header.materialCount):
            material = wmb.materialArray[materialIndex]
            materialName = material.materialName
            if 'g_AlbedoMap' in material.textureArray.keys():
                identifier = material.textureArray['g_AlbedoMap']
                textureFile = "%s%s"%('out/texture/',identifier)
                textureArray.append(textureFile)
            if 'g_NormalMap' in material.textureArray.keys():
                identifier = material.textureArray['g_NormalMap']
                textureFile = "%s%s"%('out/texture/',identifier)
                textureArray.append(textureFile)
        """
        for textureFile in textureArray:
            texture = wta.getTextureByIdentifier(textureFile.replace('out/texture/',''), wtp_fp)
            if texture:
                texture_fp = open("%s.dds"%textureFile, "wb")
                #print('dumping %s.dds'%textureFile)
                texture_fp.write(texture)
                texture_fp.close()
        """

    mtl = open("%s.mtl"%obj_file, 'w')
    #print("Iterating over wmb.wmb_header.materialCount, length %d" % wmb.wmb_header.materialCount)
    for materialIndex in range(wmb.wmb_header.materialCount):
        material = wmb.materialArray[materialIndex]
        materialName = material.materialName
        if 'g_AlbedoMap' in material.textureArray.keys():
            identifier = material.textureArray['g_AlbedoMap']
            textureFile = "%s%s"%('out/texture/',identifier)
            mtl.write('newmtl %s\n'%(identifier))
            mtl.write('Ns 96.0784\nNi 1.5000\nd 1.0000\nTr 0.0000\nTf 1.0000 1.0000 1.0000 \nillum 2\nKa 0.0000 0.0000 0.0000\nKd 0.6400 0.6400 0.6400\nKs 0.0873 0.0873 0.0873\nKe 0.0000 0.0000 0.0000\n')
            mtl.write('map_Ka %s.dds\nmap_Kd %s.dds\n'%(textureFile.replace('out','..'),textureFile.replace('out','..')))
        if 'g_NormalMap' in material.textureArray.keys():
            identifier = material.textureArray['g_NormalMap']
            textureFile2 = "%s%s"%('out/texture/',identifier)    
            mtl.write("bump %s.dds\n"%textureFile2.replace('out','..'))
        mtl.write('\n')
    mtl.close()

    
    #print("Iterating over wmb.wmb_header.vertexGroupCount, length %d" % wmb.wmb_header.vertexGroupCount)
    for vertexGroupIndex in range(wmb.wmb_header.vertexGroupCount):
        
        #print("Iterating over wmb.wmb_header.meshGroupCount, length %d" % wmb.wmb_header.meshGroupCount)
        for meshGroupIndex in range(wmb.wmb_header.meshGroupCount):
            meshIndexArray = []
            
            groupedMeshArray = wmb.meshGroupInfoArray[0].groupedMeshArray
            for groupedMeshIndex in range(len(groupedMeshArray)):
                if groupedMeshArray[groupedMeshIndex].meshGroupIndex == meshGroupIndex:
                    meshIndexArray.append(groupedMeshIndex)
            meshGroup = wmb.meshGroupArray[meshGroupIndex]
            for meshArrayIndex in (meshIndexArray):
                meshVertexGroupIndex = wmb.meshArray[meshArrayIndex].vertexGroupIndex
                if meshVertexGroupIndex == vertexGroupIndex:
                    if  not os.path.exists('%s_%s_%d.obj'%(obj_file,meshGroup.meshGroupname,vertexGroupIndex)):
                        obj = open('%s_%s_%d.obj'%(obj_file,meshGroup.meshGroupname,vertexGroupIndex),"w")
                        obj.write('mtllib ./%s.mtl\n'%obj_file.split('/')[-1])
                        #print("Iterating over wmb.vertexGroupArray[vertexGroupIndex].vertexGroupHeader.vertexCount, length %d" % wmb.vertexGroupArray[vertexGroupIndex].vertexGroupHeader.vertexCount)
                        for vertexIndex in range(wmb.vertexGroupArray[vertexGroupIndex].vertexGroupHeader.vertexCount):
                            vertex = wmb.vertexGroupArray[vertexGroupIndex].vertexArray[vertexIndex]
                            obj.write('v %f %f %f\n'%(vertex.positionX,vertex.positionY,vertex.positionZ))
                            obj.write('vt %f %f\n'%(vertex.textureU,1 - vertex.textureV))
                            obj.write('vn %f %f %f\n'%(vertex.normalX, vertex.normalY, vertex.normalZ))
                    else:
                        obj = open('%s_%s_%d.obj'%(obj_file,meshGroup.meshGroupname,vertexGroupIndex),"a+")
                    if 'g_AlbedoMap' in wmb.materialArray[groupedMeshArray[meshArrayIndex].materialIndex].textureArray.keys():
                        textureFile = wmb.materialArray[groupedMeshArray[meshArrayIndex].materialIndex].textureArray["g_AlbedoMap"]
                        obj.write('usemtl %s\n'%textureFile.split('/')[-1])
                    #print('dumping %s_%s_%d.obj'%(obj_file,meshGroup.meshGroupname,vertexGroupIndex))
                    obj.write('g %s%d\n'% (meshGroup.meshGroupname,vertexGroupIndex))
                    faceRawStart = wmb.meshArray[meshArrayIndex].faceStart
                    faceRawNum = wmb.meshArray[meshArrayIndex].faceCount
                    vertexStart = wmb.meshArray[meshArrayIndex].vertexStart
                    vertexNum = wmb.meshArray[meshArrayIndex].vertexCount
                    faceRawArray = wmb.vertexGroupArray[meshVertexGroupIndex].faceRawArray
                    
                    for i in range(int(faceRawNum/3)):
                        obj.write('f %d/%d/%d %d/%d/%d %d/%d/%d\n'%(
                                faceRawArray[faceRawStart + i * 3],faceRawArray[faceRawStart + i * 3],faceRawArray[faceRawStart + i * 3],
                                faceRawArray[faceRawStart + i * 3 + 1],faceRawArray[faceRawStart + i * 3 + 1],faceRawArray[faceRawStart + i * 3 + 1],
                                faceRawArray[faceRawStart + i * 3 + 2],faceRawArray[faceRawStart + i * 3 + 2],faceRawArray[faceRawStart + i * 3 + 2],
                            )
                        )
                    obj.close()

def main(arg, wmb_fp, wta_fp, wtp_fp, dump):
    wmb = WMB(wmb_fp)
    wmb_fp.close()
    wta = 0
    if wta_fp:
        wta = WTA(wta_fp)
        wta_fp.close()
    if dump:
        obj_file = os.path.split(arg)[-1].replace('.wmb','')
        export_obj(wmb, wta, wtp_fp, obj_file)
        if wtp_fp:
            wtp_fp.close()

if __name__ == '__main__':
    pass
