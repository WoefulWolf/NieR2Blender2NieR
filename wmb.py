from .util import *
from .wta import *
import numpy as np
import json

class WMB_Header(object):
	""" fucking header	"""
	def __init__(self, wmb_fp):
		super(WMB_Header, self).__init__()
		self.magicNumber = wmb_fp.read(4)										# ID
		if self.magicNumber == b'WMB3':
			self.version = "%08x" % (to_int(wmb_fp.read(4)))					# Version
			self.unknown08 = to_int(wmb_fp.read(4))								# UnknownA
			self.flags = to_int(wmb_fp.read(4))									# flags & referenceBone
			self.bounding_box1 = to_float(wmb_fp.read(4))						# bounding_box
			self.bounding_box2 = to_float(wmb_fp.read(4))
			self.bounding_box3 = to_float(wmb_fp.read(4))
			self.bounding_box4 = to_float(wmb_fp.read(4))
			self.bounding_box5 = to_float(wmb_fp.read(4))
			self.bounding_box6 = to_float(wmb_fp.read(4))
			self.boneArrayOffset = to_int(wmb_fp.read(4))						# offsetBones
			self.boneCount = to_int(wmb_fp.read(4))								# numBones
			self.offsetBoneIndexTranslateTable = to_int(wmb_fp.read(4))			# offsetBoneIndexTranslateTable		
			self.boneIndexTranslateTableSize = to_int(wmb_fp.read(4)) 			# boneIndexTranslateTableSize
			self.vertexGroupArrayOffset = to_int(wmb_fp.read(4))				# offsetVertexGroups
			self.vertexGroupCount = to_int(wmb_fp.read(4))						# numVertexGroups
			self.meshArrayOffset = to_int(wmb_fp.read(4))						# offsetBatches
			self.meshCount = to_int(wmb_fp.read(4))								# numBatches
			self.meshGroupInfoArrayHeaderOffset = to_int(wmb_fp.read(4))		# offsetLODS
			self.meshGroupInfoArrayCount = to_int(wmb_fp.read(4))				# numLODS
			self.colTreeNodesOffset = to_int(wmb_fp.read(4))					# offsetColTreeNodes
			self.colTreeNodesCount = to_int(wmb_fp.read(4))						# numColTreeNodes
			self.boneMapOffset = to_int(wmb_fp.read(4))							# offsetBoneMap
			self.boneMapCount = to_int(wmb_fp.read(4))							# numBoneMap
			self.bonesetOffset = to_int(wmb_fp.read(4))							# offsetBoneSets
			self.bonesetCount = to_int(wmb_fp.read(4))							# numBoneSets
			self.materialArrayOffset = to_int(wmb_fp.read(4))					# offsetMaterials
			self.materialCount = to_int(wmb_fp.read(4))							# numMaterials
			self.meshGroupOffset = to_int(wmb_fp.read(4))						# offsetMeshes
			self.meshGroupCount = to_int(wmb_fp.read(4))						# numMeshes
			self.offsetMeshMaterials = to_int(wmb_fp.read(4))					# offsetMeshMaterials
			self.numMeshMaterials = to_int(wmb_fp.read(4))						# numMeshMaterials
			self.unknownWorldDataArrayOffset = to_int(wmb_fp.read(4))			# offsetUnknown0				World Model Stuff
			self.unknownWorldDataArrayCount = to_int(wmb_fp.read(4))			# numUnknown0					World Model Stuff
			self.unknown8C = to_int(wmb_fp.read(4))

class wmb3_vertexHeader(object):
	"""docstring for wmb3_vertexHeader"""
	def __init__(self, wmb_fp):
		super(wmb3_vertexHeader, self).__init__()
		self.vertexArrayOffset = to_int(wmb_fp.read(4))		
		self.vertexExDataArrayOffset = to_int(wmb_fp.read(4))	
		self.unknown08 = to_int(wmb_fp.read(4))				
		self.unknown0C = to_int(wmb_fp.read(4))				
		self.vertexStride = to_int(wmb_fp.read(4))			
		self.vertexExDataStride = to_int(wmb_fp.read(4))		
		self.unknown18 = to_int(wmb_fp.read(4))				
		self.unknown1C = to_int(wmb_fp.read(4))				
		self.vertexCount = to_int(wmb_fp.read(4))			
		self.vertexFlags = to_int(wmb_fp.read(4))
		self.faceArrayOffset = to_int(wmb_fp.read(4))		
		self.faceCount = to_int(wmb_fp.read(4))				

class wmb3_vertex(object):
	"""docstring for wmb3_vertex"""
	def __init__(self, wmb_fp, vertex_flags):
		super(wmb3_vertex, self).__init__()
		self.positionX = to_float(wmb_fp.read(4))
		self.positionY = to_float(wmb_fp.read(4))
		self.positionZ = to_float(wmb_fp.read(4))
		self.normalX = to_int(wmb_fp.read(1)) * 2 / 255			
		self.normalY = to_int(wmb_fp.read(1)) * 2 / 255	
		self.normalZ = to_int(wmb_fp.read(1)) * 2 / 255	
		wmb_fp.read(1)											
		self.textureU = to_float16(wmb_fp.read(2))				
		self.textureV = to_float16(wmb_fp.read(2))
		if vertex_flags in [0]:
			self.normal = hex(to_int(wmb_fp.read(8)))
		if vertex_flags in [1, 4, 5, 12, 14]:
			self.textureU2 = to_float16(wmb_fp.read(2))				
			self.textureV2 = to_float16(wmb_fp.read(2))
		if vertex_flags in [7, 10, 11]:										
			self.boneIndices = [to_int(wmb_fp.read(1)) for i in range(4)]									
			self.boneWeights = [to_int(wmb_fp.read(1))/255 for i in range(4)]
		if vertex_flags in [4, 5, 12, 14]:
			self.color = [to_int(wmb_fp.read(1)) for i in range(4)]

class wmb3_vertexExData(object):
	"""docstring for wmb3_vertexExData"""
	def __init__(self, wmb_fp, vertex_flags):
		super(wmb3_vertexExData, self).__init__()
		
		#0x0 has no ExVertexData

		if vertex_flags in [1, 4]: #0x1, 0x4
			self.normal = hex(to_int(wmb_fp.read(8)))

		elif vertex_flags in [5]: #0x5
			self.normal = hex(to_int(wmb_fp.read(8)))
			self.textureU3 = to_float16(wmb_fp.read(2))				
			self.textureV3 = to_float16(wmb_fp.read(2))

		elif vertex_flags in [7]: #0x7
			self.textureU2 = to_float16(wmb_fp.read(2))				
			self.textureV2 = to_float16(wmb_fp.read(2))
			self.normal = hex(to_int(wmb_fp.read(8)))

		elif vertex_flags in [10]: #0xa
			self.textureU2 = to_float16(wmb_fp.read(2))				
			self.textureV2 = to_float16(wmb_fp.read(2))
			self.color = [to_int(wmb_fp.read(1)) for i in range(4)]
			self.normal = hex(to_int(wmb_fp.read(8)))

		elif vertex_flags in [11]: #0xb
			self.textureU2 = to_float16(wmb_fp.read(2))				
			self.textureV2 = to_float16(wmb_fp.read(2))
			self.color = [to_int(wmb_fp.read(1)) for i in range(4)]
			self.normal = hex(to_int(wmb_fp.read(8)))
			self.textureU3 = to_float16(wmb_fp.read(2))				
			self.textureV3 = to_float16(wmb_fp.read(2))
		
		elif vertex_flags in [12]: #0xc
			self.normal = hex(to_int(wmb_fp.read(8)))
			self.textureU3 = to_float16(wmb_fp.read(2))				
			self.textureV3 = to_float16(wmb_fp.read(2))
			self.textureU4 = to_float16(wmb_fp.read(2))				
			self.textureV4 = to_float16(wmb_fp.read(2))
			self.textureU5 = to_float16(wmb_fp.read(2))				
			self.textureV5 = to_float16(wmb_fp.read(2))

		elif vertex_flags in [14]: #0xe
			self.normal = hex(to_int(wmb_fp.read(8)))
			self.textureU3 = to_float16(wmb_fp.read(2))				
			self.textureV3 = to_float16(wmb_fp.read(2))
			self.textureU4 = to_float16(wmb_fp.read(2))				
			self.textureV4 = to_float16(wmb_fp.read(2))
		
class wmb3_vertexGroup(object):
	"""docstring for wmb3_vertexGroup"""
	def __init__(self, wmb_fp, faceSize):
		super(wmb3_vertexGroup, self).__init__()
		self.faceSize = faceSize
		self.vertexGroupHeader = wmb3_vertexHeader(wmb_fp)

		self.vertexFlags = self.vertexGroupHeader.vertexFlags	
		
		self.vertexArray = []
		wmb_fp.seek(self.vertexGroupHeader.vertexArrayOffset)
		for vertex_index in range(self.vertexGroupHeader.vertexCount):
			vertex = wmb3_vertex(wmb_fp, self.vertexGroupHeader.vertexFlags)
			self.vertexArray.append(vertex)

		self.vertexesExDataArray = []
		wmb_fp.seek(self.vertexGroupHeader.vertexExDataArrayOffset)
		for vertexIndex in range(self.vertexGroupHeader.vertexCount):
			self.vertexesExDataArray.append(wmb3_vertexExData(wmb_fp, self.vertexGroupHeader.vertexFlags))

		self.faceRawArray = []
		wmb_fp.seek(self.vertexGroupHeader.faceArrayOffset)
		for face_index in range(self.vertexGroupHeader.faceCount):
			if faceSize == 2:
				self.faceRawArray.append(to_int(wmb_fp.read(2)) + 1)
			else:
				self.faceRawArray.append(to_int(wmb_fp.read(4)) + 1)

class wmb3_mesh(object):
	"""docstring for wmb3_mesh"""
	def __init__(self, wmb_fp):
		super(wmb3_mesh, self).__init__()
		self.vertexGroupIndex = to_int(wmb_fp.read(4))
		self.bonesetIndex = to_int(wmb_fp.read(4))					
		self.vertexStart = to_int(wmb_fp.read(4))				
		self.faceStart = to_int(wmb_fp.read(4))					
		self.vertexCount = to_int(wmb_fp.read(4))				
		self.faceCount = to_int(wmb_fp.read(4))					
		self.unknown18 = to_int(wmb_fp.read(4))
				
class wmb3_bone(object):
	"""docstring for wmb3_bone"""
	def __init__(self, wmb_fp,index):
		super(wmb3_bone, self).__init__()
		self.boneIndex = index
		self.boneNumber = to_int(wmb_fp.read(2))				
		self.parentIndex = to_int(wmb_fp.read(2))

		local_positionX = to_float(wmb_fp.read(4))		 
		local_positionY = to_float(wmb_fp.read(4))		
		local_positionZ = to_float(wmb_fp.read(4))	
		
		local_rotationX = to_float(wmb_fp.read(4))		 
		local_rotationY = to_float(wmb_fp.read(4))		 
		local_rotationZ = to_float(wmb_fp.read(4))		

		self.local_scaleX = to_float(wmb_fp.read(4))
		self.local_scaleY = to_float(wmb_fp.read(4))
		self.local_scaleZ = to_float(wmb_fp.read(4))

		world_positionX = to_float(wmb_fp.read(4))
		world_positionY = to_float(wmb_fp.read(4))
		world_positionZ = to_float(wmb_fp.read(4))
		
		world_rotationX = to_float(wmb_fp.read(4))
		world_rotationY = to_float(wmb_fp.read(4))
		world_rotationZ = to_float(wmb_fp.read(4))

		world_scaleX = to_float(wmb_fp.read(4))
		world_scaleY = to_float(wmb_fp.read(4))
		world_scaleZ = to_float(wmb_fp.read(4))

		world_position_tposeX = to_float(wmb_fp.read(4))
		world_position_tposeY = to_float(wmb_fp.read(4))
		world_position_tposeZ = to_float(wmb_fp.read(4))

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
		self.boneMapOffset = to_int(wmb_fp.read(4))					
		self.boneMapCount = to_int(wmb_fp.read(4))	

class wmb3_boneSet(object):
	"""docstring for wmb3_boneSet"""
	def __init__(self, wmb_fp, boneSetCount):
		super(wmb3_boneSet, self).__init__()
		self.boneSetArray = []
		self.boneSetCount = boneSetCount
		boneSetInfoArray = []
		for index in range(boneSetCount):
			offset =  to_int(wmb_fp.read(4))
			count = to_int(wmb_fp.read(4))
			boneSetInfoArray.append([offset, count])
		for boneSetInfo in boneSetInfoArray:
			wmb_fp.seek(boneSetInfo[0])
			boneSet = []
			for index in range(boneSetInfo[1]):
				boneSet.append(to_int(wmb_fp.read(2)))
			self.boneSetArray.append(boneSet)

class wmb3_material(object):
	"""docstring for wmb3_material"""
	def __init__(self, wmb_fp):
		super(wmb3_material, self).__init__()
		to_int(wmb_fp.read(2))
		to_int(wmb_fp.read(2))
		to_int(wmb_fp.read(2))
		to_int(wmb_fp.read(2))
		materialNameOffset = to_int(wmb_fp.read(4))
		effectNameOffset = to_int(wmb_fp.read(4))
		techniqueNameOffset = to_int(wmb_fp.read(4))
		to_int(wmb_fp.read(4))
		textureOffset = to_int(wmb_fp.read(4))
		textureNum = to_int(wmb_fp.read(4))
		paramterGroupsOffset = to_int(wmb_fp.read(4))
		numParameterGroups = to_int(wmb_fp.read(4))
		varOffset = to_int(wmb_fp.read(4))
		varNum = to_int(wmb_fp.read(4))
		wmb_fp.seek(materialNameOffset)
		self.materialName = to_string(wmb_fp.read(256))
		wmb_fp.seek(effectNameOffset)
		self.effectName = to_string(wmb_fp.read(256))
		wmb_fp.seek(techniqueNameOffset)
		self.techniqueName = to_string(wmb_fp.read(256))
		self.textureArray = {}

		path_split = wmb_fp.name.split('\\')

		mat_list_filepath = "\\".join(path_split[:-3])
		mat_list_file = open(mat_list_filepath + '\\materials.json', 'a') #
		mat_dict = {}
		if os.path.getsize(mat_list_filepath + '\\materials.json') == 0:
			# Initialize a new dictionary if file is empty
			mat_dict[self.materialName] = {}
		else:
			# Load dictionary from json
			mat_dict = json.loads(mat_list_file)
		for i in range(textureNum):
			wmb_fp.seek(textureOffset + i * 8)
			offset = to_int(wmb_fp.read(4))
			identifier = "%08x"%to_int(wmb_fp.read(4))
			wmb_fp.seek(offset)
			textureTypeName = to_string(wmb_fp.read(256))
			self.textureArray[textureTypeName] = identifier
			# Add new texture to nested material dictionary
			mat_dict[self.materialName][textureTypeName] = identifier

		mat_list_file.write(json.dumps(mat_dict))
		mat_list_file.close() 
		

		wmb_fp.seek(paramterGroupsOffset)
		self.parameterGroups = []
		for i in range(numParameterGroups):
			wmb_fp.seek(paramterGroupsOffset + i * 12)
			parameters = []
			index = to_int(wmb_fp.read(4))
			offset = to_int(wmb_fp.read(4))
			num = to_int(wmb_fp.read(4))
			wmb_fp.seek(offset)
			for k in range(num):
				param = to_float(wmb_fp.read(4))
				parameters.append(param)
			self.parameterGroups.append(parameters)

		wmb_fp.seek(varOffset)
		self.uniformArray = {}
		for i in range(varNum):
			wmb_fp.seek(varOffset + i * 8)
			offset = to_int(wmb_fp.read(4))
			value = to_float(wmb_fp.read(4))
			wmb_fp.seek(offset)
			self.uniformArray [to_string(wmb_fp.read(256))] = value
			

class wmb3_meshGroup(object):
	"""docstring for wmb3_meshGroupInfo"""
	def __init__(self, wmb_fp):
		super(wmb3_meshGroup, self).__init__()
		nameOffset = to_int(wmb_fp.read(4))
		self.boundingBox = []
		for i in range(6):
			self.boundingBox.append(to_float(wmb_fp.read(4)))								
		materialIndexArrayOffset = to_int(wmb_fp.read(4))
		materialIndexArrayCount =  to_int(wmb_fp.read(4))
		boneIndexArrayOffset =to_int(wmb_fp.read(4))
		boneIndexArrayCount =  to_int(wmb_fp.read(4))
		wmb_fp.seek(nameOffset)
		self.meshGroupname = to_string(wmb_fp.read(256))
		self.materialIndexArray = []
		self.boneIndexArray = []
		wmb_fp.seek(materialIndexArrayOffset)
		for i in range(materialIndexArrayCount):
			self.materialIndexArray.append(to_int(wmb_fp.read(2)))
		wmb_fp.seek(boneIndexArrayOffset)
		for i in range(boneIndexArrayCount):
			self.boneIndexArray.append(to_int(wmb_fp.read(2)))
		

class wmb3_groupedMesh(object):
	"""docstring for wmb3_groupedMesh"""
	def __init__(self, wmb_fp):
		super(wmb3_groupedMesh, self).__init__()
		self.vertexGroupIndex = to_int(wmb_fp.read(4))
		self.meshGroupIndex = to_int(wmb_fp.read(4))
		self.materialIndex = to_int(wmb_fp.read(4))
		self.colTreeNodeIndex = to_int(wmb_fp.read(4)) 
		if self.colTreeNodeIndex == 4294967295:	
			self.colTreeNodeIndex = -1					
		self.meshGroupInfoMaterialPair = to_int(wmb_fp.read(4))
		self.unknownWorldDataIndex = to_int(wmb_fp.read(4))
		if self.unknownWorldDataIndex == 4294967295:	
			self.unknownWorldDataIndex = -1
		
		
class wmb3_meshGroupInfo(object):
	"""docstring for wmb3_meshGroupInfo"""
	def __init__(self, wmb_fp):
		super(wmb3_meshGroupInfo, self).__init__()
		self.nameOffset = to_int(wmb_fp.read(4))					
		self.lodLevel = to_int(wmb_fp.read(4))
		if self.lodLevel == 4294967295:	
			self.lodLevel = -1				
		self.meshStart = to_int(wmb_fp.read(4))						
		meshGroupInfoOffset = to_int(wmb_fp.read(4))			
		self.meshCount = to_int(wmb_fp.read(4))						
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
		p1_x = to_float(wmb_fp.read(4))
		p1_y = to_float(wmb_fp.read(4))
		p1_z = to_float(wmb_fp.read(4))
		self.p1 = (p1_x, p1_y, p1_z)

		p2_x = to_float(wmb_fp.read(4))
		p2_y = to_float(wmb_fp.read(4))
		p2_z = to_float(wmb_fp.read(4))
		self.p2 = (p2_x, p2_y, p2_z)

		self.left = to_int(wmb_fp.read(4))
		if self.left == 4294967295:
			self.left = -1

		self.right = to_int(wmb_fp.read(4))
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
	def __init__(self, wmb_file):
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
		print_class(self.wmb3_header)
		wmb_fp.seek(self.wmb3_header.boneArrayOffset)
		self.boneArray = []
		for boneIndex in range(self.wmb3_header.boneCount):
			self.boneArray.append(wmb3_bone(wmb_fp,boneIndex))

		
		# indexBoneTranslateTable
		wmb_fp.seek(self.wmb3_header.offsetBoneIndexTranslateTable)
		self.firstLevel = []
		for entry in range(16):
			self.firstLevel.append(to_int(wmb_fp.read(2)))
			if self.firstLevel[-1] == 65535:
				self.firstLevel[-1] = -1

		firstLevel_Entry_Count = 0
		for entry in self.firstLevel:
			if entry != -1:
				firstLevel_Entry_Count += 1

		self.secondLevel = []
		for entry in range(firstLevel_Entry_Count * 16):
			self.secondLevel.append(to_int(wmb_fp.read(2)))
			if self.secondLevel[-1] == 65535:
				self.secondLevel[-1] = -1

		secondLevel_Entry_Count = 0
		for entry in self.secondLevel:
			if entry != -1:
				secondLevel_Entry_Count += 1

		self.thirdLevel = []
		for entry in range(secondLevel_Entry_Count * 16):
			self.thirdLevel.append(to_int(wmb_fp.read(2)))
			if self.thirdLevel[-1] == 65535:
				self.thirdLevel[-1] = -1


		wmb_fp.seek(self.wmb3_header.offsetBoneIndexTranslateTable)
		unknownData1Array = []
		for i in range(self.wmb3_header.boneIndexTranslateTableSize):
			unknownData1Array.append(to_int(wmb_fp.read(1)))

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

		self.materialArray = []
		for materialIndex in range(self.wmb3_header.materialCount):
			wmb_fp.seek(self.wmb3_header.materialArrayOffset + materialIndex * 0x30)
			material = wmb3_material(wmb_fp)
			self.materialArray.append(material)

		wmb_fp.seek(self.wmb3_header.boneMapOffset)
		self.boneMap = []
		for index in range(self.wmb3_header.boneMapCount):
			self.boneMap.append(to_int(wmb_fp.read(4)))
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
			if self.vertexGroupArray[vertexGroupIndex].vertexFlags in [4, 5, 12, 14]:
				vertex_colors.append(meshVertices[i].color)
			# Vertex_Colors are stored in VertexExData
			if self.vertexGroupArray[vertexGroupIndex].vertexFlags in [10, 11]:
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
		obj_file = arg.split('\\')[-1].replace('.wmb','')
		export_obj(wmb, wta, wtp_fp, obj_file)
		if wtp_fp:
			wtp_fp.close()

if __name__ == '__main__':
	pass