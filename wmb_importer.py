import bpy, bmesh, math
from mathutils import Vector, Matrix
from .wmb import *

def show_message(message = "", title = "Message Box", icon = 'INFO'):
	def draw(self, context):
		self.layout.label(text = message)
		self.layout.alignment = 'CENTER'
	bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

def reset_blend():
	#bpy.ops.object.mode_set(mode='OBJECT')
	for collection in bpy.data.collections:
		for obj in collection.objects:
			collection.objects.unlink(obj)
		bpy.data.collections.remove(collection)
	for bpy_data_iter in (bpy.data.objects,bpy.data.meshes,bpy.data.lights,bpy.data.cameras):
		for id_data in bpy_data_iter:
			bpy_data_iter.remove(id_data)
	for material in bpy.data.materials:
		bpy.data.materials.remove(material)
	for amt in bpy.data.armatures:
		bpy.data.armatures.remove(amt)
	for obj in bpy.data.objects:
		bpy.data.objects.remove(obj)
		obj.user_clear()

def construct_armature(name, bone_data_array, firstLevel, secondLevel, thirdLevel, boneMap, boneSetArray):			# bone_data =[boneIndex, boneName, parentIndex, parentName, bone_pos, optional, boneNumber, localPos, local_rotation, world_rotation, world_position_tpose]
	print('[+] importing armature')
	bpy.ops.object.add(
		type='ARMATURE', 
		enter_editmode=True,
		location=(0,0,0))
	ob = bpy.context.object
	ob.show_in_front = False
	ob.name = name
	amt = ob.data
	amt.name = name +'Amt'
	 
	amt['firstLevel'] = firstLevel
	amt['secondLevel'] = secondLevel
	amt['thirdLevel'] = thirdLevel

	amt['boneMap'] = boneMap

	amt['boneSetArray'] = boneSetArray

	for bone_data in bone_data_array:
		bone = amt.edit_bones.new(bone_data[1])
		bone.head = Vector(bone_data[4]) 
		bone.tail = Vector(bone_data[4]) + Vector((0 , 0.01, 0))				
		bone['ID'] = bone_data[6]

		bone['localPosition'] = bone_data[7]
		bone['localRotation'] = bone_data[8]
		bone['worldRotation'] = bone_data[9]
		bone['TPOSE_worldPosition'] = bone_data[10]

	bones = amt.edit_bones
	for bone_data in bone_data_array:
		if bone_data[2] < 0xffff:						#this value need to edit in different games
			bone = bones[bone_data[1]]
			bone.parent = bones[bone_data[3]]
			#if bones[bone_data[3]]['ID'] != 0:
			if bones[bone_data[3]].head != bone.head:
				bones[bone_data[3]].tail = bone.head

	bpy.ops.object.mode_set(mode='OBJECT')
	ob.rotation_euler = (math.radians(90),0,0)
	# split armature
	return ob

def split_armature(name):
	amt = bpy.data.armatures[name]
	name = name.replace('Amt','')
	bones = amt.bones
	root_bones = [bone for bone in bones if not bone.parent]
	for i in range(len(root_bones)):
		bpy.ops.object.add(
			type='ARMATURE', 
			enter_editmode=True,
			location=(i * 2,0,0))
		ob_new = bpy.context.object
		ob_new.show_x_ray = False
		ob_new.name = "%s_%d" % (name, i)
		amt_new = ob_new.data
		amt_new.name = '%s_%d_Amt' % (name, i)
		copy_bone_tree(root_bones[i] ,amt_new)
		bpy.ops.object.mode_set(mode="OBJECT")
		ob_new.rotation_euler = (math.radians(90),0,0)
	bpy.ops.object.select_all(action="DESELECT")
	obj = bpy.data.objects[name]
	scene = bpy.context.scene
	scene.objects.unlink(obj)
	return False

def copy_bone_tree(source_root, target_amt):
	bone = target_amt.edit_bones.new(source_root.name)
	bone.head = source_root.head_local
	bone.tail = source_root.tail_local
	if source_root.parent:
		bone.parent = target_amt.edit_bones[source_root.parent.name]
	for child in source_root.children:
		copy_bone_tree(child, target_amt)

def construct_mesh(mesh_data, collection_name):			# [meshName, vertices, faces, has_bone, boneWeightInfoArray, boneSetIndex, meshGroupIndex, colors_mean, LOD_name, LOD_level, colTreeNodeIndex, unknownWorldDataIndex, boundingBox], collection_name
	name = mesh_data[0]
	for obj in bpy.data.objects:
		if obj.name == name:
			name = name + '-' + collection_name
	vertices = mesh_data[1]
	faces = mesh_data[2]
	has_bone = mesh_data[3]
	weight_infos = [[[],[]]]							# A real fan can recognize me even I am a 2 dimensional array
	print("[+] importing %s" % name)
	objmesh = bpy.data.meshes.new(name)
	if not name in bpy.data.objects.keys(): 
		obj = bpy.data.objects.new(name, objmesh)
	else:
		obj = bpy.data.objects[name]	
	obj.location = Vector((0,0,0))
	bpy.context.collection.objects.link(obj)
	objmesh.from_pydata(vertices, [], faces)
	objmesh.update(calc_edges=True)
	if has_bone:
		weight_infos = mesh_data[4]
		group_names = sorted(list(set(["bone%d" % i  for weight_info in weight_infos for i in weight_info[0]])))
		for group_name in group_names:
			obj.vertex_groups.new(name=group_name)
		for i in range(len(weight_infos)):
			for index in range(4):
				group_name = "bone%d"%weight_infos[i][0][index]
				weight = weight_infos[i][1][index]
				group = obj.vertex_groups[group_name]
				if weight:
					group.add([i], weight, "REPLACE")
	obj.rotation_euler = (math.radians(90),0,0)
	if mesh_data[5] != "None":
		obj['boneSetIndex'] = mesh_data[5]
	obj['meshGroupIndex'] = mesh_data[6]
	obj['vertexColours_mean'] = mesh_data[7]
	obj['LOD_Name'] = mesh_data[8]
	obj['LOD_Level'] = mesh_data[9]
	obj['colTreeNodeIndex'] = mesh_data[10]
	obj['unknownWorldDataIndex'] = mesh_data[11]
	obj['boundingBoxXYZ'] = [mesh_data[12][0], mesh_data[12][1], mesh_data[12][2]]
	obj['boundingBoxUVW'] = [mesh_data[12][3], mesh_data[12][4], mesh_data[12][5]]

	obj.data.flip_normals()
	return obj

def set_partent(parent, child):
	bpy.context.view_layer.objects.active = parent
	child.select_set(True)
	parent.select_set(True)
	bpy.ops.object.parent_set(type="ARMATURE")
	child.select_set(False)
	parent.select_set(False)

def consturct_materials(texture_dir, material):
	material_name = material[0]
	textures = material[1]
	uniforms = material[2]
	shader_name = material[3]
	technique_name = material[4]
	parameterGroups = material[5]
	print('[+] importing material %s' % material_name)
	material = bpy.data.materials.new( '%s' % (material_name))
	material['Shader_Name'] = shader_name
	material['Technique_Name'] = technique_name
	# Enable Nodes
	material.use_nodes = True
	# Clear Nodes and Links
	material.node_tree.links.clear()
	material.node_tree.nodes.clear()
	# Recreate Nodes and Links with references
	nodes = material.node_tree.nodes
	links = material.node_tree.links
	# PrincipledBSDF and Ouput Shader
	output = nodes.new(type='ShaderNodeOutputMaterial')
	output.location = 1200,0
	principled = nodes.new(type='ShaderNodeBsdfPrincipled')
	principled.location = 900,0
	output_link = links.new( principled.outputs['BSDF'], output.inputs['Surface'] )
	# Normal Map Amount Counter
	normal_map_count = 0
	# Mask Map Count
	mask_map_count = 0
	# Alpha Channel
	material.blend_method = 'CLIP'

	#print("\n".join(["%s:%f" %(key, uniforms[key]) for key in sorted(uniforms.keys())]))
	# Shader Parameters
	for key in uniforms.keys():
		material[key] = uniforms.get(key)
		#print(key, material[key])
		if key.lower().find("g_glossiness") > -1:
			principled.inputs['Roughness'].default_value = 1 - uniforms[key]

	# Custom Shader Parameters
	for gindx, parameterGroup in enumerate(parameterGroups):
		for pindx, parameter in enumerate(parameterGroup):
			if pindx == 5:
				material[str(gindx) + '_UseAlpha_' + str(pindx)] = parameter
			else:
				material[str(gindx) + '_' + str(pindx)] = parameter

	albedo_maps = {}
	normal_maps = {}
	mask_maps = {}

	for texturesType in textures.keys():
		textures_type = texturesType.lower()
		material[texturesType] = textures.get(texturesType)
		texture_file = "%s/%s.dds" % (texture_dir, textures[texturesType])
		if os.path.exists(texture_file):
			if textures_type.find('albedo') > -1:
				albedo_maps[textures_type] = textures.get(texturesType)
			elif textures_type.find('normal') > -1:
				normal_maps[textures_type] = textures.get(texturesType)
			elif textures_type.find('mask') > -1:
				mask_maps[textures_type] = textures.get(texturesType)

	

	# Albedo Nodes
	albedo_nodes = []
	albedo_mixRGB_nodes = []
	for i, textureID in enumerate(albedo_maps.values()):
		texture_file = "%s/%s.dds" % (texture_dir, textureID)
		if os.path.exists(texture_file):
			albedo_image = nodes.new(type='ShaderNodeTexImage')
			albedo_nodes.append(albedo_image)
			albedo_image.location = 0,i*-60
			albedo_image.image = bpy.data.images.load(texture_file)
			albedo_image.hide = True
			if i > 0:
				albedo_image.label = "g_AlbedoMap" + str(i-1)
			else:
				albedo_image.label = "g_AlbedoMap"

			if i > 0:
				mixRGB_shader = nodes.new(type='ShaderNodeMixRGB')
				albedo_mixRGB_nodes.append(mixRGB_shader)
				mixRGB_shader.location = 300,(i-1)*-60
				mixRGB_shader.hide = True
	# Albedo Links
	if len(albedo_nodes) == 1:
		albedo_principled = links.new(albedo_nodes[0].outputs['Color'], principled.inputs['Base Color'])
		alpha_link = links.new(albedo_nodes[0].outputs['Alpha'], principled.inputs['Alpha'])
	else:
		if len(albedo_mixRGB_nodes) > 0:
			albedo_link = links.new(albedo_nodes[0].outputs['Color'], albedo_mixRGB_nodes[0].inputs['Color2'])
			for i in range(len(albedo_mixRGB_nodes)):
				albedo_link = links.new(albedo_nodes[i+1].outputs['Color'], albedo_mixRGB_nodes[i].inputs['Color1'])
				alpha_link = links.new(albedo_nodes[i].outputs['Alpha'], albedo_mixRGB_nodes[i].inputs['Fac'])
				if i > 0:
					mixRGB_link = links.new(albedo_mixRGB_nodes[i-1].outputs['Color'], albedo_mixRGB_nodes[i].inputs['Color2'])
			mixRGB_link = links.new(albedo_mixRGB_nodes[-1].outputs['Color'], principled.inputs['Base Color'])

	# Mask Nodes
	# Mask Image Texture (R = Metallic, G = Glossines (Inverted Roughness), B = AO)
	mask_nodes = []
	mask_sepRGB_nodes = []
	mask_invert_nodes = []
	for i, textureID in enumerate(mask_maps.values()):
		texture_file = "%s/%s.dds" % (texture_dir, textureID)
		if os.path.exists(texture_file):
			mask_image = nodes.new(type='ShaderNodeTexImage')
			mask_nodes.append(mask_image)
			mask_image.location = 0, ((len(albedo_maps)+1)*-60)-i*60
			mask_image.image = bpy.data.images.load(texture_file)
			mask_image.image.colorspace_settings.name = 'Non-Color'
			mask_image.hide = True
			if i > 0:
				mask_image.label = "g_MaskMap" + str(i-1)
			else:
				mask_image.label = "g_MaskMap"

			if 'Hair' not in material['Shader_Name']:
				sepRGB_shader = nodes.new(type="ShaderNodeSeparateRGB")
				mask_sepRGB_nodes.append(sepRGB_shader)
				sepRGB_shader.location = 300, ((len(albedo_maps)+1)*-60)-i*60
				sepRGB_shader.hide = True
				
				invert_shader = nodes.new(type="ShaderNodeInvert")
				mask_invert_nodes.append(invert_shader)
				invert_shader.location = 600, ((len(albedo_maps)+1)*-60)-i*60
				invert_shader.hide = True
	#Mask Links
	if len(mask_nodes) > 0:
		if 'Hair' not in material['Shader_Name']:
			mask_link = links.new(mask_nodes[0].outputs['Color'], mask_sepRGB_nodes[0].inputs['Image'])
			r_link = links.new(mask_sepRGB_nodes[0].outputs['R'], principled.inputs['Metallic'])
			g_link = links.new(mask_sepRGB_nodes[0].outputs['G'], mask_invert_nodes[0].inputs['Color'])
			invert_link = links.new(mask_invert_nodes[0].outputs['Color'], principled.inputs['Roughness'])
		else:
			mask_link = links.new(mask_nodes[0].outputs['Color'], principled.inputs['Metallic'])

	# Normal Nodes
	normal_nodes = []
	normal_mixRGB_nodes = []
	for i, textureID in enumerate(normal_maps.values()):
		texture_file = "%s/%s.dds" % (texture_dir, textureID)
		if os.path.exists(texture_file):
			normal_image = nodes.new(type='ShaderNodeTexImage')
			normal_nodes.append(normal_image)
			normal_image.location = 0, ((len(albedo_maps)+1)*-60) + ((len(mask_maps)+1)*-60)-i*60
			normal_image.image = bpy.data.images.load(texture_file)
			normal_image.image.colorspace_settings.name = 'Non-Color'
			normal_image.hide = True
			if i > 0:
				normal_image.label = "g_NormalMap" + str(i-1)
			else:
				normal_image.label = "g_NormalMap"

			if i > 0:
				n_mixRGB_shader = nodes.new(type='ShaderNodeMixRGB')
				normal_mixRGB_nodes.append(n_mixRGB_shader)
				n_mixRGB_shader.location = 300, ((len(albedo_maps)+1)*-60) + ((len(mask_maps)+1)*-60)-(i-1)*60
				n_mixRGB_shader.hide = True
	if len(normal_nodes) > 0:
		normalmap_shader = nodes.new(type='ShaderNodeNormalMap')
		normalmap_shader.location = 600, ((len(albedo_maps)+1)*-60) + ((len(mask_maps)+1)*-60)-(i-1)*60
		normalmap_link = links.new(normalmap_shader.outputs['Normal'], principled.inputs['Normal'])
		normalmap_shader.hide = True
	# Normal Links
	if len(normal_nodes) == 1:
		normal_link = links.new(normal_nodes[0].outputs['Color'], normalmap_shader.inputs['Color'])
	else:
		if len(normal_mixRGB_nodes) > 0:
			normal_link = links.new(normal_nodes[0].outputs['Color'], normal_mixRGB_nodes[0].inputs['Color2'])
			for i in range(len(normal_mixRGB_nodes)):
				normal_link = links.new(normal_nodes[i+1].outputs['Color'], normal_mixRGB_nodes[i].inputs['Color1'])
				if i < len(albedo_nodes):
					n_alpha_link = links.new(albedo_nodes[i].outputs['Alpha'], normal_mixRGB_nodes[i].inputs['Fac'])
				if i > 0:
					n_mixRGB_link = links.new(normal_mixRGB_nodes[i-1].outputs['Color'], normal_mixRGB_nodes[i].inputs['Color2'])
			mixRGB_link = links.new(normal_mixRGB_nodes[-1].outputs['Color'], normalmap_shader.inputs['Color'])
				


	"""
	for texturesType in textures.keys():
		textures_type = texturesType.lower() 
		flag = False
		material[texturesType] = textures.get(texturesType)					# Add textures as custom properties
		for type_key in ['albedo', "normal", "mask"]:				# TO_DO:, 'env','parallax','irradiance','curvature']:
			if textures_type.find(type_key) > -1:
				flag = True
		if flag:
			texture_name = "%s_%s"%(textures[texturesType],texturesType)
			texture_file = "%s/%s.dds" % (texture_dir, textures[texturesType])
			if os.path.exists(texture_file):
				if not texture_name in bpy.data.textures.keys():
					print('[+] importing texture %s' % texture_name)
					texture = bpy.data.textures.new('%s' % (texture_name), type = 'IMAGE')
					texture.image = bpy.data.images.load(texture_file)
				else:
					texture = bpy.data.textures[texture_name]
				#material_textureslot = material.texture_slots.add()
				#material_textureslot.use_map_color_diffuse = False
				if textures_type.find("normal") > -1:
					#Normal Map
					if normal_map_count == 0: # Only 1 Normal Map
						normal_map = nodes.new(type='ShaderNodeNormalMap')
						normal_map.location = 420,-500
						normal_map_link = links.new(normal_map.outputs['Normal'], principled.inputs['Normal'])
						#Normal Image Texture
						normal_image = nodes.new(type='ShaderNodeTexImage')
						normal_image.location = 0,-600
						normal_image.image = bpy.data.images.load(texture_file)
						normal_image.image.colorspace_settings.name = 'Non-Color'
						normal_image_link = links.new(normal_image.outputs['Color'], normal_map.inputs['Color'])
						normal_map_count += 1
					else: # 2 Normal Maps
						links.remove(normal_image_link)

						mixRGB_shader = nodes.new(type='ShaderNodeMixRGB')
						mixRGB_shader.location = 260,-500
						mixRGB_shader_link = links.new(mixRGB_shader.outputs['Color'], normal_map.inputs['Color'])
						normal_image_link = links.new(normal_image.outputs['Color'], mixRGB_shader.inputs['Color1'])

						normal_image2 = nodes.new(type='ShaderNodeTexImage')
						normal_image2.location = 0,-800
						normal_image2.image = bpy.data.images.load(texture_file)
						normal_image2.image.colorspace_settings.name = 'Non-Color'
						normal_image_link2 = links.new(normal_image2.outputs['Color'], mixRGB_shader.inputs['Color2'])
				elif textures_type.find("mask") > -1:	#Only add first MaskMap
					#Mask Image Texture (R = Metallic, G = Glossines (Inverted Roughness), B = AO)
					mask_image = nodes.new(type='ShaderNodeTexImage')
					mask_image.location = -250,-250
					mask_image.image = bpy.data.images.load(texture_file)
					mask_image.image.colorspace_settings.name = 'Non-Color'
					if mask_map_count == 0:
						if not 'Hair' in material['Shader_Name']:
							seperate_rgb = nodes.new(type="ShaderNodeSeparateRGB")
							seperate_rgb.location = 25,-250
							mask_map_link = links.new(mask_image.outputs['Color'], seperate_rgb.inputs['Image'])
							r_channel_link = links.new(seperate_rgb.outputs['R'], principled.inputs['Metallic'])				# R -> Mettalic
							g_channel_invert = nodes.new(type="ShaderNodeInvert")
							g_channel_invert.location = 200,-325
							g_channel_link = links.new(seperate_rgb.outputs['G'], g_channel_invert.inputs['Color'])				# G -> Invert
							g_inverted_link = links.new(g_channel_invert.outputs['Color'], principled.inputs['Roughness'])		# Invert -> Roughness
							if False:																							# DISABLED BAKED AO (just set this to true if you want it, but Blender's AO is better)
								b_channel_multiply = nodes.new(type="ShaderNodeMixRGB")
								b_channel_multiply.location = 350,0
								b_channel_multiply.blend_type = 'MULTIPLY'
								b_channel_link = links.new(seperate_rgb.outputs['B'], b_channel_multiply.inputs[2])					# AO
								albedo_multiply_link = links.new(diffuse_image.outputs['Color'], b_channel_multiply.inputs[1])
								b_channel_multiply.inputs["Fac"].default_value = 1
								multiply_link = links.new(b_channel_multiply.outputs['Color'], principled.inputs['Base Color'])
							
						else:
							mask_link = links.new(mask_image.outputs['Color'], principled.inputs['Metallic'])

						mask_map_count += 1
				elif textures_type.find("light") > -1:
					print("light not implemented yet in Nier2Blender_2_80")
				elif textures_type.find("env") > -1:
					print("env not implemented yet in Nier2Blender_2_80")
					#material_textureslot.use_map_ambient = True
				elif textures_type.find("parallax") > -1:
					print("parralax not implemented yet in Nier2Blender_2_80")
					#material_textureslot.use_map_displacement
				elif textures_type.find("irradiance") > -1:
					print("irradiance not implemented yet in Nier2Blender_2_80")
					#material_textureslot.use_map_emit = True
				elif textures_type.find("curvature") > -1:
					print("curvature not implemented yet in Nier2Blender_2_80")
					#material_textureslot.use_map_warp = True
				else:
					# Diffuse Image Texture (Albedo)
					diffuse_image = nodes.new(type='ShaderNodeTexImage')
					diffuse_image.location = 0,0
					diffuse_image.image = bpy.data.images.load(texture_file)
					diffuse_image_link = links.new(diffuse_image.outputs['Color'], principled.inputs['Base Color'])

					# Alpha Channel
					material.blend_method = 'CLIP'

					alpha_link = links.new(diffuse_image.outputs['Alpha'], principled.inputs['Alpha'])
					
				print('[+] adding texture %s to material %s' % (texture_name, material_name))
				#material_textureslot.texture = texture
				#material_textureslot.texture_coords = 'UV'
		else:
			print("[!] not supported texture %s_%s" % (textures[texturesType], texturesType))
	#if not material.texture_slots[0]:
		#print("[!] no textute found for material %s" % material_name)
	"""
	return material

def add_material_to_mesh(mesh, materials , uvs):
	for material in materials:
		#print('linking material %s to mesh object %s' % (material.name, mesh.name))
		mesh.data.materials.append(material)
	bpy.context.view_layer.objects.active = mesh
	bpy.ops.object.mode_set(mode="EDIT")
	bm = bmesh.from_edit_mesh(mesh.data)
	uv_layer = bm.loops.layers.uv.verify()
	#bm.faces.layers.tex.verify()
	for face in bm.faces:
		face.material_index = 0
		for l in face.loops:
			luv = l[uv_layer]
			ind = l.vert.index
			luv.uv = Vector(uvs[ind])
	bpy.ops.object.mode_set(mode='OBJECT')
	mesh.select_set(True)
	bpy.ops.object.shade_smooth()
	#mesh.hide = True
	mesh.select_set(False)
	
def format_wmb_mesh(wmb, collection_name):
	meshes = []
	uvs = []
	usedVerticeIndexArrays = []
	mesh_array = wmb.meshArray
	#each vertexgroup -> each lod -> each group -> mesh
	for vertexGroupIndex in range(wmb.wmb3_header.vertexGroupCount):
		uv = [(vertex.textureU, 1 - vertex.textureV) for vertex in wmb.vertexGroupArray[vertexGroupIndex].vertexArray]
		uvs.append(uv)
		for meshGroupInfoArrayIndex in range(len(wmb.meshGroupInfoArray)):
			meshGroupInfo =  wmb.meshGroupInfoArray[meshGroupInfoArrayIndex]
			groupedMeshArray = meshGroupInfo.groupedMeshArray
			mesh_start = meshGroupInfo.meshStart
			LOD_name = meshGroupInfo.meshGroupInfoname
			LOD_level = meshGroupInfo.lodLevel
			for meshGroupIndex in range(wmb.wmb3_header.meshGroupCount):
				meshIndexArray = []
				for groupedMeshIndex in range(len(groupedMeshArray)):
					if groupedMeshArray[groupedMeshIndex].meshGroupIndex == meshGroupIndex:
						meshIndexArray.append([mesh_start + groupedMeshIndex, groupedMeshArray[groupedMeshIndex].colTreeNodeIndex, groupedMeshArray[groupedMeshIndex].unknownWorldDataIndex])
				meshGroup = wmb.meshGroupArray[meshGroupIndex]
				for meshArrayData in (meshIndexArray):
					meshArrayIndex = meshArrayData[0]
					colTreeNodeIndex = meshArrayData[1]
					unknownWorldDataIndex = meshArrayData[2]
					meshVertexGroupIndex = wmb.meshArray[meshArrayIndex].vertexGroupIndex
					if meshVertexGroupIndex == vertexGroupIndex:
						meshName = "%d-%s-%d"%(meshArrayIndex, meshGroup.meshGroupname, vertexGroupIndex)
						meshInfo = wmb.clear_unused_vertex(meshArrayIndex, meshVertexGroupIndex)
						vertices = meshInfo[0]
						faces =  meshInfo[1]
						usedVerticeIndexArray = meshInfo[2]
						boneWeightInfoArray = meshInfo[3]
						colors_mean = meshInfo[4]
						usedVerticeIndexArrays.append(usedVerticeIndexArray)
						flag = False
						has_bone = wmb.hasBone
						boneSetIndex = wmb.meshArray[meshArrayIndex].bonesetIndex
						if boneSetIndex == 0xffffffff:
							boneSetIndex = -1
						boundingBox = meshGroup.boundingBox
						obj = construct_mesh([meshName, vertices, faces, has_bone, boneWeightInfoArray, boneSetIndex, meshGroupIndex, colors_mean, LOD_name, LOD_level, colTreeNodeIndex, unknownWorldDataIndex, boundingBox], collection_name)
						meshes.append(obj)
	return meshes, uvs, usedVerticeIndexArrays

def get_wmb_material(wmb, texture_dir):
	materials = []
	if wmb.wta:
		for materialIndex in range(len(wmb.materialArray)):
			material = wmb.materialArray[materialIndex]
			material_name = material.materialName
			shader_name = material.effectName
			technique_name = material.techniqueName
			uniforms = material.uniformArray
			textures = material.textureArray
			parameterGroups = material.parameterGroups
			for key in textures.keys():
				identifier = textures[key]
				try:
					texture_stream = wmb.wta.getTextureByIdentifier(identifier,wmb.wtp_fp)
					if texture_stream:
						if not os.path.exists("%s\%s.dds" %(texture_dir, identifier)):
							create_dir(texture_dir)
							texture_fp = open("%s\%s.dds" %(texture_dir, identifier), "wb")
							print('[+] dumping %s.dds'% identifier)
							texture_fp.write(texture_stream)
							texture_fp.close()
				except:
					continue
			materials.append([material_name,textures,uniforms,shader_name,technique_name,parameterGroups])
	else:
		print('Missing .wta')
		show_message("Error: Could not open .wta file, textures not imported. Is it missing? (Maybe DAT not extracted?)", 'Could Not Open .wta File', 'ERROR')
		for materialIndex in range(len(wmb.materialArray)):
			material = wmb.materialArray[materialIndex]
			material_name = material.materialName
			shader_name = material.effectName
			technique_name = material.techniqueName
			uniforms = material.uniformArray
			textures = material.textureArray
			parameterGroups = material.parameterGroups
			materials.append([material_name,textures,uniforms,shader_name,technique_name,parameterGroups])
		
	return materials

def import_colTreeNodes(wmb, collection):
	colTreeNodesDict = {}
	#collision_col = bpy.data.collections.new("CollisionNodes")
	#collection.children.link(collision_col)
	for index, node in enumerate(wmb.colTreeNodes):
		colTreeNodeName = 'colTreeNode' + str(index)
		colTreeNode = [node.p1[0], node.p1[1], node.p1[2], node.p2[0], node.p2[1], node.p2[2], node.left, node.right]
		colTreeNodesDict[colTreeNodeName] = colTreeNode

		"""
		bpy.ops.mesh.primitive_cube_add(enter_editmode=False, align='WORLD', location=(node.p1[0], node.p1[1], node.p1[2]))
		col_Bound = bpy.context.active_object
		col_Bound.name =  str(index) + "-" + str(node.left) + "-" + str(node.right)
		bpy.ops.transform.resize(value=(node.p2[0], node.p2[1], node.p2[2]))
		bpy.ops.transform.rotate(value=math.radians(90), orient_axis='X', center_override=(0, 0, 0))
		bpy.context.object.display_type = 'BOUNDS'
		collision_col.objects.link(col_Bound)
		collection.objects.unlink(col_Bound)
		"""

	bpy.context.scene['colTreeNodes'] = colTreeNodesDict

def import_unknowWorldDataArray(wmb):
	unknownWorldDataDict = {}
	for index, unknownWorldData in enumerate(wmb.unknownWorldDataArray):
		unknownWorldDataName = 'unknownWorldData' + str(index)
		unknownWorldDataDict[unknownWorldDataName] = unknownWorldData.unknownWorldData
	bpy.context.scene['unknownWorldData'] = unknownWorldDataDict

def import_wmb_boundingbox(wmb):
	boundingBoxXYZ = [wmb.wmb3_header.bounding_box1, wmb.wmb3_header.bounding_box2, wmb.wmb3_header.bounding_box3]
	boundingBoxUVW = [wmb.wmb3_header.bounding_box4, wmb.wmb3_header.bounding_box5, wmb.wmb3_header.bounding_box6]
	bpy.context.scene['boundingBoxXYZ'] = boundingBoxXYZ
	bpy.context.scene['boundingBoxUVW'] = boundingBoxUVW

def main(wmb_file = os.path.split(os.path.realpath(__file__))[0] + '\\test\\pl0000.dtt\\pl0000.wmb'):
	#reset_blend()
	wmb = WMB3(wmb_file)
	wmbname = wmb_file.split('\\')[-1]
	collection_name = wmbname[:-4]

	col = bpy.data.collections.new(collection_name)
	bpy.context.scene.collection.children.link(col)
	bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[-1]
	texture_dir = wmb_file.replace(wmbname, '\\textures\\')
	import_wmb_boundingbox(wmb)
	if wmb.hasBone:
		boneArray = [[bone.boneIndex, "bone%d"%bone.boneIndex, bone.parentIndex,"bone%d"%bone.parentIndex, bone.world_position, bone.world_rotation, bone.boneNumber, bone.local_position, bone.local_rotation, bone.world_rotation, bone.world_position_tpose] for bone in wmb.boneArray]
		armature_no_wmb = wmbname.replace('.wmb','')
		armature_name_split = armature_no_wmb.split('/')
		armature_name = armature_name_split[len(armature_name_split)-1] # THIS IS SPAGHETT I KNOW. I WAS TIRED
		construct_armature(armature_name, boneArray, wmb.firstLevel, wmb.secondLevel, wmb.thirdLevel, wmb.boneMap, wmb.boneSetArray)
	meshes, uvs, usedVerticeIndexArrays = format_wmb_mesh(wmb, collection_name)
	wmb_materials = get_wmb_material(wmb, texture_dir)
	materials = []
	for materialIndex in range(len(wmb_materials)):
		material = wmb_materials[materialIndex]
		print(material)
		materials.append(consturct_materials(texture_dir, material))
	print('Linking materials to objects...')
	for meshGroupInfo in wmb.meshGroupInfoArray:
		for Index in range(len(meshGroupInfo.groupedMeshArray)):
			mesh_start = meshGroupInfo.meshStart
			meshIndex = int(meshes[Index + mesh_start].name.split('-')[0])
			materialIndex = meshGroupInfo.groupedMeshArray[meshIndex - mesh_start].materialIndex
			groupIndex = int(meshes[Index + mesh_start].name.split('-')[2])
			uv = []
			for i in range(len(usedVerticeIndexArrays[Index + mesh_start])):
				VertexIndex = usedVerticeIndexArrays[Index + mesh_start][i]
				uv.append( uvs[groupIndex][VertexIndex])
			if len(materials) > 0:
				add_material_to_mesh(meshes[Index + mesh_start], [materials[materialIndex]], uv)
	if wmb.hasBone:
		amt = bpy.data.objects.get(armature_name)
	if wmb.hasBone:
		for mesh in meshes:
			set_partent(amt,mesh)
	if wmb.hasColTreeNodes:
		import_colTreeNodes(wmb, col)
	if wmb.hasUnknownWorldData:
		import_unknowWorldDataArray(wmb)

	print('Importing finished. ;)')
	return {'FINISHED'}

if __name__ == '__main__':
	main()