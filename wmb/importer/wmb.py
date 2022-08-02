import os
import json
from time import time

from ...utils.util import print_class, create_dir
from ...utils.ioUtils import SmartIO, read_uint8_x4, to_string, read_float, read_float16, read_uint16, read_uint8, read_uint64
from ...wta_wtp.importer.wta import *


class WMB_Header(object):
	""" fucking header	"""
	def __init__(self, wmb_fp):
		super(WMB_Header, self).__init__()
		self.magicNumber = wmb_fp.read(4)										# ID
		if self.magicNumber == b'WMB3':
			self.version = "%08x" % (read_uint32(wmb_fp))					# Version
			self.unknown08 = read_uint32(wmb_fp)								# UnknownA
			self.flags = read_uint32(wmb_fp)									# flags & referenceBone
			self.bounding_box1 = read_float(wmb_fp)						# bounding_box
			self.bounding_box2 = read_float(wmb_fp)
			self.bounding_box3 = read_float(wmb_fp)
			self.bounding_box4 = read_float(wmb_fp)
			self.bounding_box5 = read_float(wmb_fp)
			self.bounding_box6 = read_float(wmb_fp)
			self.boneArrayOffset = read_uint32(wmb_fp)						# offsetBones
			self.boneCount = read_uint32(wmb_fp)								# numBones
			self.offsetBoneIndexTranslateTable = read_uint32(wmb_fp)			# offsetBoneIndexTranslateTable		
			self.boneIndexTranslateTableSize = read_uint32(wmb_fp) 			# boneIndexTranslateTableSize
			self.vertexGroupArrayOffset = read_uint32(wmb_fp)				# offsetVertexGroups
			self.vertexGroupCount = read_uint32(wmb_fp)						# numVertexGroups
			self.meshArrayOffset = read_uint32(wmb_fp)						# offsetBatches
			self.meshCount = read_uint32(wmb_fp)								# numBatches
			self.meshGroupInfoArrayHeaderOffset = read_uint32(wmb_fp)		# offsetLODS
			self.meshGroupInfoArrayCount = read_uint32(wmb_fp)				# numLODS
			self.colTreeNodesOffset = read_uint32(wmb_fp)					# offsetColTreeNodes
			self.colTreeNodesCount = read_uint32(wmb_fp)						# numColTreeNodes
			self.boneMapOffset = read_uint32(wmb_fp)							# offsetBoneMap
			self.boneMapCount = read_uint32(wmb_fp)							# numBoneMap
			self.bonesetOffset = read_uint32(wmb_fp)							# offsetBoneSets
			self.bonesetCount = read_uint32(wmb_fp)							# numBoneSets
			self.materialArrayOffset = read_uint32(wmb_fp)					# offsetMaterials
			self.materialCount = read_uint32(wmb_fp)							# numMaterials
			self.meshGroupOffset = read_uint32(wmb_fp)						# offsetMeshes
			self.meshGroupCount = read_uint32(wmb_fp)						# numMeshes
			self.offsetMeshMaterials = read_uint32(wmb_fp)					# offsetMeshMaterials
			self.numMeshMaterials = read_uint32(wmb_fp)						# numMeshMaterials
			self.unknownWorldDataArrayOffset = read_uint32(wmb_fp)			# offsetUnknown0				World Model Stuff
			self.unknownWorldDataArrayCount = read_uint32(wmb_fp)			# numUnknown0					World Model Stuff
			self.unknown8C = read_uint32(wmb_fp)

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
	
class wmb3_vertexGroup(object):
	"""docstring for wmb3_vertexGroup"""
	def __init__(self, wmb_fp, faceSize):
		super(wmb3_vertexGroup, self).__init__()
		self.faceSize = faceSize
		self.vertexGroupHeader = wmb3_vertexHeader(wmb_fp)

		self.vertexFlags = self.vertexGroupHeader.vertexFlags	
		
		self.vertexArray = [None] * self.vertexGroupHeader.vertexCount
		wmb_fp.seek(self.vertexGroupHeader.vertexArrayOffset)
		for vertex_index in range(self.vertexGroupHeader.vertexCount):
			vertex = wmb3_vertex(wmb_fp, self.vertexGroupHeader.vertexFlags)
			self.vertexArray[vertex_index] = vertex

		self.vertexesExDataArray = [None] * self.vertexGroupHeader.vertexCount
		wmb_fp.seek(self.vertexGroupHeader.vertexExDataArrayOffset)
		for vertexIndex in range(self.vertexGroupHeader.vertexCount):
			self.vertexesExDataArray[vertexIndex] = wmb3_vertexExData(wmb_fp, self.vertexGroupHeader.vertexFlags)

		self.faceRawArray = [None] * self.vertexGroupHeader.faceCount
		wmb_fp.seek(self.vertexGroupHeader.faceArrayOffset)
		for face_index in range(self.vertexGroupHeader.faceCount):
			if faceSize == 2:
				self.faceRawArray[face_index] = read_uint16(wmb_fp) + 1
			else:
				self.faceRawArray[face_index] = read_uint32(wmb_fp) + 1

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
		self.boneMapOffset = read_uint32(wmb_fp)					
		self.boneMapCount = read_uint32(wmb_fp)	

class wmb3_boneSet(object):
	"""docstring for wmb3_boneSet"""
	def __init__(self, wmb_fp, boneSetCount):
		super(wmb3_boneSet, self).__init__()
		self.boneSetArray = []
		self.boneSetCount = boneSetCount
		boneSetInfoArray = []
		for index in range(boneSetCount):
			offset =  read_uint32(wmb_fp)
			count = read_uint32(wmb_fp)
			boneSetInfoArray.append([offset, count])
		for boneSetInfo in boneSetInfoArray:
			wmb_fp.seek(boneSetInfo[0])
			boneSet = []
			for index in range(boneSetInfo[1]):
				boneSet.append(read_uint16(wmb_fp))
			self.boneSetArray.append(boneSet)

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
		self.materialName = to_string(wmb_fp.read(256))
		wmb_fp.seek(effectNameOffset)
		self.effectName = to_string(wmb_fp.read(256))
		wmb_fp.seek(techniqueNameOffset)
		self.techniqueName = to_string(wmb_fp.read(256))
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
			#print("Could not load json: " , ex)
			pass
		
		# Clear file contents
		mat_list_file.truncate(0)
		file_dict[self.materialName] = {}
		# Append textures to materials in the dictionary
		for i in range(textureNum):
			wmb_fp.seek(textureOffset + i * 8)
			offset = read_uint32(wmb_fp)
			identifier = "%08x"%read_uint32(wmb_fp)
			wmb_fp.seek(offset)
			textureTypeName = to_string(wmb_fp.read(256))
			self.textureArray[textureTypeName] = identifier
			# Add new texture to nested material dictionary

		file_dict[self.materialName]["Textures"] = self.textureArray

		file_dict[self.materialName]["Shader_Name"] = self.effectName
		file_dict[self.materialName]["Technique_Name"] = self.techniqueName
		wmb_fp.seek(paramterGroupsOffset)
		self.parameterGroups = []
		for i in range(numParameterGroups):
			wmb_fp.seek(paramterGroupsOffset + i * 12)
			parameters = []
			index = read_uint32(wmb_fp)
			offset = read_uint32(wmb_fp)
			num = read_uint32(wmb_fp)
			wmb_fp.seek(offset)
			for k in range(num):
				param = read_float(wmb_fp)
				parameters.append(param)
			self.parameterGroups.append(parameters)

		wmb_fp.seek(varOffset)
		self.uniformArray = {}
		for i in range(varNum):
			wmb_fp.seek(varOffset + i * 8)
			offset = read_uint32(wmb_fp)
			value = read_float(wmb_fp)
			wmb_fp.seek(offset)
			name = to_string(wmb_fp.read(256))
			self.uniformArray[name] = value

		file_dict[self.materialName]["ParameterGroups"] = self.parameterGroups
		file_dict[self.materialName]["Variables"] = self.uniformArray

		# Write the current material to materials.json
		json.dump(file_dict, mat_list_file, indent= 4)
		mat_list_file.close()

class wmb3_meshGroup(object):
	"""docstring for wmb3_meshGroupInfo"""
	def __init__(self, wmb_fp):
		super(wmb3_meshGroup, self).__init__()
		nameOffset = read_uint32(wmb_fp)
		self.boundingBox = []
		for i in range(6):
			self.boundingBox.append(read_float(wmb_fp))								
		materialIndexArrayOffset = read_uint32(wmb_fp)
		materialIndexArrayCount =  read_uint32(wmb_fp)
		boneIndexArrayOffset =read_uint32(wmb_fp)
		boneIndexArrayCount =  read_uint32(wmb_fp)
		wmb_fp.seek(nameOffset)
		self.meshGroupname = to_string(wmb_fp.read(256))
		self.materialIndexArray = []
		self.boneIndexArray = []
		wmb_fp.seek(materialIndexArrayOffset)
		for i in range(materialIndexArrayCount):
			self.materialIndexArray.append(read_uint16(wmb_fp))
		wmb_fp.seek(boneIndexArrayOffset)
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
		if self.colTreeNodeIndex == 4294967295:	
			self.colTreeNodeIndex = -1					
		self.meshGroupInfoMaterialPair = read_uint32(wmb_fp)
		self.unknownWorldDataIndex = read_uint32(wmb_fp)
		if self.unknownWorldDataIndex == 4294967295:	
			self.unknownWorldDataIndex = -1
		
		
class wmb3_meshGroupInfo(object):
	"""docstring for wmb3_meshGroupInfo"""
	def __init__(self, wmb_fp):
		super(wmb3_meshGroupInfo, self).__init__()
		self.nameOffset = read_uint32(wmb_fp)					
		self.lodLevel = read_uint32(wmb_fp)
		if self.lodLevel == 4294967295:	
			self.lodLevel = -1				
		self.meshStart = read_uint32(wmb_fp)						
		meshGroupInfoOffset = read_uint32(wmb_fp)			
		self.meshCount = read_uint32(wmb_fp)						
		wmb_fp.seek(self.nameOffset)
		self.meshGroupInfoname = to_string(wmb_fp.read(256))
		wmb_fp.seek(meshGroupInfoOffset)
		self.groupedMeshArray = []
		for i in range(self.meshCount):
			groupedMesh = wmb3_groupedMesh(wmb_fp)
			self.groupedMeshArray.append(groupedMesh)

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

		
class wmb3_worldData(object):
	"""docstring for wmb3_unknownWorldData"""
	def __init__(self, wmb_fp):
		self.unknownWorldData = []
		for entry in range(6):
			self.unknownWorldData.append(wmb_fp.read(4))
		
class WMB3(object):
	"""docstring for WMB3"""
	def __init__(self, wmb_file, only_extract):
		super(WMB3, self).__init__()
		wmb_fp = 0
		wta_fp = 0
		wtp_fp = 0
		self.wta = 0

		wmb_path = wmb_file
		if not os.path.exists(wmb_path):
			wmb_path = wmb_file.replace('.dat','.dtt')
		wtp_path = wmb_file.replace('.dat','.dtt').replace('.wmb','.wtp')
		wta_path = wmb_file.replace('.dtt','.dat').replace('.wmb','.wta')

		if os.path.exists(wtp_path):	
			print('open wtp file')
			self.wtp_fp = open(wtp_path,'rb')
		if os.path.exists(wta_path):
			print('open wta file')
			wta_fp = open(wta_path,'rb')
		
		if wta_fp:
			self.wta = WTA(wta_fp)
			wta_fp.close()

		if os.path.exists(wmb_path):
			wmb_fp = open(wmb_path, "rb")
		else:
			print("DTT/DAT does not contain WMB file.")
			return

		self.wmb3_header = WMB_Header(wmb_fp)
		self.hasBone = False
		if self.wmb3_header.boneCount > 0:
			self.hasBone = True

		wmb_fp.seek(self.wmb3_header.boneArrayOffset)
		self.boneArray = []
		for boneIndex in range(self.wmb3_header.boneCount):
			self.boneArray.append(wmb3_bone(wmb_fp,boneIndex))
		
		# indexBoneTranslateTable
		self.firstLevel = []
		self.secondLevel = []
		self.thirdLevel = []
		if self.wmb3_header.offsetBoneIndexTranslateTable > 0:
			wmb_fp.seek(self.wmb3_header.offsetBoneIndexTranslateTable)
			for entry in range(16):
				self.firstLevel.append(read_uint16(wmb_fp))
				if self.firstLevel[-1] == 65535:
					self.firstLevel[-1] = -1

			firstLevel_Entry_Count = 0
			for entry in self.firstLevel:
				if entry != -1:
					firstLevel_Entry_Count += 1

			for entry in range(firstLevel_Entry_Count * 16):
				self.secondLevel.append(read_uint16(wmb_fp))
				if self.secondLevel[-1] == 65535:
					self.secondLevel[-1] = -1

			secondLevel_Entry_Count = 0
			for entry in self.secondLevel:
				if entry != -1:
					secondLevel_Entry_Count += 1

			for entry in range(secondLevel_Entry_Count * 16):
				self.thirdLevel.append(read_uint16(wmb_fp))
				if self.thirdLevel[-1] == 65535:
					self.thirdLevel[-1] = -1


			wmb_fp.seek(self.wmb3_header.offsetBoneIndexTranslateTable)
			unknownData1Array = []
			for i in range(self.wmb3_header.boneIndexTranslateTableSize):
				unknownData1Array.append(read_uint8(wmb_fp))

		self.materialArray = []
		for materialIndex in range(self.wmb3_header.materialCount):
			wmb_fp.seek(self.wmb3_header.materialArrayOffset + materialIndex * 0x30)
			material = wmb3_material(wmb_fp)
			self.materialArray.append(material)

		if only_extract:
			return

		self.vertexGroupArray = []
		for vertexGroupIndex in range(self.wmb3_header.vertexGroupCount):
			wmb_fp.seek(self.wmb3_header.vertexGroupArrayOffset + 0x30 * vertexGroupIndex)

			vertexGroup = wmb3_vertexGroup(wmb_fp,((self.wmb3_header.flags & 0x8) and 4 or 2))
			self.vertexGroupArray.append(vertexGroup)

		self.meshArray = []
		wmb_fp.seek(self.wmb3_header.meshArrayOffset)
		for meshIndex in range(self.wmb3_header.meshCount):
			mesh = wmb3_mesh(wmb_fp)
			self.meshArray.append(mesh)

		self.meshGroupInfoArray = []
		for meshGroupInfoArrayIndex in range(self.wmb3_header.meshGroupInfoArrayCount):
			wmb_fp.seek(self.wmb3_header.meshGroupInfoArrayHeaderOffset + meshGroupInfoArrayIndex * 0x14)
			meshGroupInfo= wmb3_meshGroupInfo(wmb_fp)
			self.meshGroupInfoArray.append(meshGroupInfo)

		self.meshGroupArray = []
		for meshGroupIndex in range(self.wmb3_header.meshGroupCount):
			wmb_fp.seek(self.wmb3_header.meshGroupOffset + meshGroupIndex * 0x2c)
			meshGroup = wmb3_meshGroup(wmb_fp)
			
			self.meshGroupArray.append(meshGroup)

		wmb_fp.seek(self.wmb3_header.boneMapOffset)
		self.boneMap = []
		for index in range(self.wmb3_header.boneMapCount):
			self.boneMap.append(read_uint32(wmb_fp))
		wmb_fp.seek(self.wmb3_header.bonesetOffset)
		self.boneSetArray = wmb3_boneSet(wmb_fp, self.wmb3_header.bonesetCount).boneSetArray

		# colTreeNode
		self.hasColTreeNodes = False
		if self.wmb3_header.colTreeNodesOffset > 0:
			self.hasColTreeNodes = True
			self.colTreeNodes = []
			wmb_fp.seek(self.wmb3_header.colTreeNodesOffset)
			for index in range(self.wmb3_header.colTreeNodesCount):
				self.colTreeNodes.append(wmb3_colTreeNode(wmb_fp))
		
		# World Model Data
		self.hasUnknownWorldData = False
		if self.wmb3_header.unknownWorldDataArrayOffset > 0:
			self.hasUnknownWorldData = True
			self.unknownWorldDataArray = []
			wmb_fp.seek(self.wmb3_header.unknownWorldDataArrayOffset)
			for index in range(self.wmb3_header.unknownWorldDataArrayCount):
				self.unknownWorldDataArray.append(wmb3_worldData(wmb_fp))
				

	def clear_unused_vertex(self, meshArrayIndex,vertexGroupIndex):
		mesh = self.meshArray[meshArrayIndex]
		faceRawStart = mesh.faceStart
		faceRawCount = mesh.faceCount
		vertexStart = mesh.vertexStart
		vertexCount = mesh.vertexCount

		vertexesExDataArray = self.vertexGroupArray[vertexGroupIndex].vertexesExDataArray
		vertexesExData = vertexesExDataArray[vertexStart : vertexStart + vertexCount]

		vertex_colors = []

		faceRawArray = self.vertexGroupArray[vertexGroupIndex].faceRawArray
		facesRaw = faceRawArray[faceRawStart : faceRawStart + faceRawCount ]
		facesRaw = [index - 1 for index in facesRaw]
		usedVertexIndexArray = sorted(list(set(facesRaw)))
		mappingDict = {}
		for newIndex in range(len(usedVertexIndexArray)):
			mappingDict[usedVertexIndexArray[newIndex]] = newIndex
		for i in range(len(facesRaw)):
			facesRaw[i] = mappingDict[facesRaw[i]]
		faces = [0] * int(faceRawCount / 3)
		usedVertices = [0] * len(usedVertexIndexArray)
		boneWeightInfos = [[],[]]
		for i in range(0, faceRawCount, 3):
			faces[int(i/3)] = (facesRaw[i]  , facesRaw[i + 1]  , facesRaw[i + 2] )
		meshVertices = self.vertexGroupArray[vertexGroupIndex].vertexArray

		if self.hasBone:
			boneWeightInfos = [0] * len(usedVertexIndexArray)
		for newIndex in range(len(usedVertexIndexArray)):
			i = usedVertexIndexArray[newIndex]
			usedVertices[newIndex] = (meshVertices[i].positionX, meshVertices[i].positionY, meshVertices[i].positionZ)

			# Vertex_Colors are stored in VertexData
			if self.vertexGroupArray[vertexGroupIndex].vertexFlags in {4, 5, 12, 14}:
				vertex_colors.append(meshVertices[i].color)
			# Vertex_Colors are stored in VertexExData
			if self.vertexGroupArray[vertexGroupIndex].vertexFlags in {10, 11}:
				vertex_colors.append(vertexesExData[i].color)

			if self.hasBone:
				bonesetIndex = mesh.bonesetIndex
				boneSetArray = self.boneSetArray
				boneMap = self.boneMap
				if bonesetIndex < 0xffffffff:
					boneSet = boneSetArray[bonesetIndex]
					boneIndices = [boneMap[boneSet[index]] for index in  meshVertices[i].boneIndices]
					boneWeightInfos[newIndex] = [boneIndices, meshVertices[i].boneWeights]
					s = sum([weight for weight in meshVertices[i].boneWeights]) 
					if s > 1.000000001 or s < 0.999999:
						print('[-] error weight detect %f' % s)
						print(meshVertices[i].boneWeights) 
				else:
					self.hasBone = False
		return usedVertices, faces, usedVertexIndexArray, boneWeightInfos, vertex_colors


def export_obj(wmb, wta, wtp_fp, obj_file):
	if not obj_file:
		obj_file = 'test'
	create_dir('out/%s'%obj_file)
	obj_file = 'out/%s/%s'%(obj_file, obj_file)
	textureArray = []
	
	if (wta and wtp_fp):
		for materialIndex in range(wmb.wmb3_header.materialCount):
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
		for textureFile in textureArray:
			texture = wta.getTextureByIdentifier(textureFile.replace('out/texture/',''), wtp_fp)
			if texture:
				texture_fp = open("%s.dds"%textureFile, "wb")
				print('dumping %s.dds'%textureFile)
				texture_fp.write(texture)
				texture_fp.close()

	mtl = open("%s.mtl"%obj_file, 'w')
	for materialIndex in range(wmb.wmb3_header.materialCount):
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

	
	for vertexGroupIndex in range(wmb.wmb3_header.vertexGroupCount):
		
		for meshGroupIndex in range(wmb.wmb3_header.meshGroupCount):
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
					print('dumping %s_%s_%d.obj'%(obj_file,meshGroup.meshGroupname,vertexGroupIndex))
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
	wmb = WMB3(wmb_fp)
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
