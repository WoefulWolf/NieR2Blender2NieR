from nier2blender.util import *
from nier2blender.wta import *
class WMB_Header(object):
	""" fucking header	"""
	def __init__(self, wmb_fp):
		super(WMB_Header, self).__init__()
		self.magicNumber = wmb_fp.read(4)
		if self.magicNumber == b'WMB3':
			self.version = "%08x" % (to_int(wmb_fp.read(4)))
			self.unknown08 = to_int(wmb_fp.read(4))
			self.flags = to_int(wmb_fp.read(4))
			self.bounding_box1 = to_float(wmb_fp.read(4))
			self.bounding_box2 = to_float(wmb_fp.read(4))
			self.bounding_box3 = to_float(wmb_fp.read(4))
			self.bounding_box4 = to_float(wmb_fp.read(4))
			self.bounding_box5 = to_float(wmb_fp.read(4))
			self.bounding_box6 = to_float(wmb_fp.read(4))
			self.boneArrayOffset = to_int(wmb_fp.read(4))
			self.boneCount = to_int(wmb_fp.read(4))
			self.unknownChunk1Offset = to_int(wmb_fp.read(4))
			self.unknownChunk1DataCount = to_int(wmb_fp.read(4)) 
			self.vertexGroupArrayOffset = to_int(wmb_fp.read(4))
			self.vertexGroupCount = to_int(wmb_fp.read(4))
			self.meshArrayOffset = to_int(wmb_fp.read(4))
			self.meshCount = to_int(wmb_fp.read(4))
			self.meshGroupInfoArrayHeaderOffset = to_int(wmb_fp.read(4))
			self.meshGroupInfoArrayCount = to_int(wmb_fp.read(4))
			self.unknownChunk2Offset = to_int(wmb_fp.read(4))
			self.unknownChunk2DataCount = to_int(wmb_fp.read(4))
			self.boneMapOffset = to_int(wmb_fp.read(4))
			self.boneMapCount = to_int(wmb_fp.read(4))
			self.bonesetOffset = to_int(wmb_fp.read(4))
			self.bonesetCount = to_int(wmb_fp.read(4))
			self.materialArrayOffset = to_int(wmb_fp.read(4))
			self.materialCount = to_int(wmb_fp.read(4))
			self.meshGroupOffset = to_int(wmb_fp.read(4))
			self.meshGroupCount = to_int(wmb_fp.read(4))
			self.unknownChunk3Offset = to_int(wmb_fp.read(4))
			self.unknownChunk3DataCount = to_int(wmb_fp.read(4))
			self.unknown84 = to_int(wmb_fp.read(4))
			self.unknown88 = to_int(wmb_fp.read(4))
			self.unknown8C = to_int(wmb_fp.read(4))

class wmb3_vertexHeader(object):
	"""docstring for wmb3_vertexHeader"""
	def __init__(self, wmb_fp):
		super(wmb3_vertexHeader, self).__init__()
		self.vertexArrayOffset = to_int(wmb_fp.read(4))		
		self.boneWeightArrayOffset = to_int(wmb_fp.read(4))	
		self.unknown08 = to_int(wmb_fp.read(4))				
		self.unknown0C = to_int(wmb_fp.read(4))				
		self.vertexStride = to_int(wmb_fp.read(4))			
		self.boneWeightStride = to_int(wmb_fp.read(4))		
		self.unknown18 = to_int(wmb_fp.read(4))				
		self.unknown1C = to_int(wmb_fp.read(4))				
		self.vertexCount = to_int(wmb_fp.read(4))			
		self.unknown24 = to_int(wmb_fp.read(4))
		self.faceArrayOffset = to_int(wmb_fp.read(4))		
		self.faceCount = to_int(wmb_fp.read(4))				

class wmb3_vertex(object):
	"""docstring for wmb3_vertex"""
	def __init__(self, wmb_fp , stride):
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
		if stride > 0x14:										
			self.boneIndices = [to_int(wmb_fp.read(1)) for i in range(4)]
		if stride > 0x18:										
			self.boneWeights = [to_int(wmb_fp.read(1))/255 for i in range(4)]

class wmb3_boneWeight(object):
	"""docstring for wmb3_boneWeight"""
	def __init__(self, wmb_fp, stride):
		super(wmb3_boneWeight, self).__init__()
		self.unknown00 = hex(to_int(wmb_fp.read(4)))				
		if stride > 0xC:
			self.unknown04 = hex(to_int(wmb_fp.read(4)))
		if stride > 0x8:											
			self.unknown08 = hex(to_int(wmb_fp.read(4)))
		self.unknown0C = hex(to_int(wmb_fp.read(4)))
		if stride > 0x10:	
			self.unknown10 = hex(to_int(wmb_fp.read(4)))
		if stride > 0x14:	
			self.unknown14 = hex(to_int(wmb_fp.read(4)))
		if stride > 0x18:
			self.unknown18 = hex(to_int(wmb_fp.read(4))) 
		
class wmb3_vertexGroup(object):
	"""docstring for wmb3_vertexGroup"""
	def __init__(self, wmb_fp, faceSize):
		super(wmb3_vertexGroup, self).__init__()
		self.faceSize = faceSize
		self.vertexGroupHeader = wmb3_vertexHeader(wmb_fp)
		
		
		self.vertexArray = []
		wmb_fp.seek(self.vertexGroupHeader.vertexArrayOffset)
		for vertex_index in range(self.vertexGroupHeader.vertexCount):
			vertex = wmb3_vertex(wmb_fp, self.vertexGroupHeader.vertexStride)
			self.vertexArray.append(vertex)

		self.boneWeightArray = []
		wmb_fp.seek(self.vertexGroupHeader.boneWeightArrayOffset)
		for vertexIndex in range(self.vertexGroupHeader.vertexCount):
			self.boneWeightArray.append(wmb3_boneWeight(wmb_fp,self.vertexGroupHeader.boneWeightStride))

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
		
		self.local_rotationX = to_float(wmb_fp.read(4))		 
		self.local_rotationY = to_float(wmb_fp.read(4))		 
		self.local_rotationZ = to_float(wmb_fp.read(4))		

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
		self.world_scale = (world_scaleX, world_scaleY, world_scaleZ)
		world_position_tposeX = to_float(wmb_fp.read(4))
		world_position_tposeY = to_float(wmb_fp.read(4))
		world_position_tposeZ = to_float(wmb_fp.read(4))
		self.local_position = (local_positionX, local_positionY, local_positionZ)

		self.world_position = (world_positionX, world_positionY, world_positionZ)
		self.world_rotation = (world_rotationX, world_rotationY, world_rotationZ)

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
		to_int(wmb_fp.read(4))
		to_int(wmb_fp.read(4))
		varOffset = to_int(wmb_fp.read(4))
		varNum = to_int(wmb_fp.read(4))
		wmb_fp.seek(materialNameOffset)
		self.materialName = to_string(wmb_fp.read(256))
		wmb_fp.seek(effectNameOffset)
		self.effectName = to_string(wmb_fp.read(256))
		wmb_fp.seek(techniqueNameOffset)
		self.techniqueName = to_string(wmb_fp.read(256))
		self.textureArray = {}
		for i in range(textureNum):
			wmb_fp.seek(textureOffset + i * 8)
			offset = to_int(wmb_fp.read(4))
			identifier = "%08x"%to_int(wmb_fp.read(4))
			wmb_fp.seek(offset)
			self.textureArray[to_string(wmb_fp.read(256))] = identifier
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
		bounding_box = wmb_fp.read(24)								
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
		self.unknown0C = to_int(wmb_fp.read(4)) 					
		self.meshGroupInfoMaterialPair = to_int(wmb_fp.read(4))
		self.unknown14 = to_int(wmb_fp.read(4))
		
class wmb3_meshGroupInfo(object):
	"""docstring for wmb3_meshGroupInfo"""
	def __init__(self, wmb_fp):
		super(wmb3_meshGroupInfo, self).__init__()
		self.nameOffset = to_int(wmb_fp.read(4))					
		self.unknown04 = to_int(wmb_fp.read(4))						
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
		
			
		
class WMB3(object):
	"""docstring for WMB3"""
	def __init__(self, wmb_file):
		super(WMB3, self).__init__()
		wmb_fp = 0
		wta_fp = 0
		wtp_fp = 0
		self.wta = 0
		if os.path.exists(wmb_file):
			wmb_fp = open(wmb_file, "rb")
		if os.path.exists(wmb_file.replace('.dtt','.dat').replace('.wmb','.wta')):
			print('open wta file')
			wta_fp = open(wmb_file.replace('.dtt','.dat').replace('.wmb','.wta'),'rb')
		if os.path.exists(wmb_file.replace('.wmb','.wtp')):	
			print('open wtp file')
			self.wtp_fp = open(wmb_file.replace('.wmb','.wtp'),'rb')
		
		if wta_fp:
			self.wta = WTA(wta_fp)
			wta_fp.close()
		self.wmb3_header = WMB_Header(wmb_fp)
		self.hasBone = False
		if self.wmb3_header.boneCount > 0:
			self.hasBone = True
		print_class(self.wmb3_header)
		wmb_fp.seek(self.wmb3_header.boneArrayOffset)
		self.boneArray = []
		for boneIndex in range(self.wmb3_header.boneCount):
			self.boneArray.append(wmb3_bone(wmb_fp,boneIndex))

		wmb_fp.seek(self.wmb3_header.unknownChunk1Offset)
		unknownData1Array = []
		for i in range(self.wmb3_header.unknownChunk1DataCount):
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
		#print_class(self.boneSets)
		
	def clear_unused_vertex(self, meshArrayIndex,vertexGroupIndex):
		mesh = self.meshArray[meshArrayIndex]
		faceRawStart = mesh.faceStart
		faceRawCount = mesh.faceCount
		vertexStart = mesh.vertexStart
		vertexCount = mesh.vertexCount
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
		return usedVertices ,faces, usedVertexIndexArray, boneWeightInfos


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