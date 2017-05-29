import bpy, bmesh, math
from mathutils import Vector, Matrix
from nier2blender.wmb import *

def reset_blend():
	bpy.ops.object.mode_set(mode='OBJECT')
	for scene in bpy.data.scenes:
		for obj in scene.objects:
			scene.objects.unlink(obj)
	for bpy_data_iter in (bpy.data.objects,bpy.data.meshes,bpy.data.lamps,bpy.data.cameras):
		for id_data in bpy_data_iter:
			bpy_data_iter.remove(id_data)
	for material in bpy.data.materials:
		bpy.data.materials.remove(material)
	for amt in bpy.data.armatures:
		bpy.data.armatures.remove(amt)
	for obj in bpy.data.objects:
		bpy.data.objects.remove(obj)
		obj.user_clear()

def construct_armature(name, bone_data_array):			# bone_data =[boneIndex, boneName, parentIndex, parentName, bone_pos, optional ]
	print('[+] importing armature')
	bpy.ops.object.add(
		type='ARMATURE', 
		enter_editmode=True,
		location=(0,0,0))
	ob = bpy.context.object
	ob.show_x_ray = False
	ob.name = name
	amt = ob.data
	amt.name = name +'Amt'
	for bone_data in bone_data_array:	
		bone = amt.edit_bones.new(bone_data[1])
		bone.head = Vector(bone_data[4]) 
		bone.tail = Vector(bone_data[4]) + Vector((0 , 0.01, 0))
	bones = amt.edit_bones
	for bone_data in bone_data_array:
		if bone_data[2] < 0xffff:						#this value need to edit in different games
			bone = bones[bone_data[1]]
			bone.parent = bones[bone_data[3]]
			bones[bone_data[3]].tail = bone.head
	bpy.ops.object.mode_set(mode='OBJECT')
	ob.rotation_euler = (math.tan(1),0,0)
	#split_armature(amt.name)							#current not used
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
		ob_new.rotation_euler = (math.tan(1),0,0)
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

def construct_mesh(mesh_data):
	name = mesh_data[0]
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
	bpy.context.scene.objects.link(obj)
	objmesh.from_pydata(vertices, [], faces)
	objmesh.update(calc_edges=True)
	if has_bone:
		weight_infos = mesh_data[4]
		group_names = sorted(list(set(["bone%d" % i  for weight_info in weight_infos for i in weight_info[0]])))
		for group_name in group_names:
			obj.vertex_groups.new(group_name)
		for i in range(len(weight_infos)):
			for index in range(4):
				group_name = "bone%d"%weight_infos[i][0][index]
				weight = weight_infos[i][1][index]
				group = obj.vertex_groups[group_name]
				if weight:
					group.add([i], weight, "REPLACE")
	obj.rotation_euler = (math.tan(1),0,0)
	return obj

def set_partent(parent, child):
	bpy.context.scene.objects.active = parent
	child.select = True
	parent.select = True
	bpy.ops.object.parent_set(type="ARMATURE")
	child.select = False
	parent.select = False

def consturct_materials(texture_dir ,material):
	material_name = material[0]
	textures = material[1]
	uniforms = material[2]
	print('[+] importing material %s' % material_name)
	material = bpy.data.materials.new( '%s' % (material_name))
	#print("\n".join(["%s:%f" %(key, uniforms[key]) for key in sorted(uniforms.keys())]))
	for key in uniforms.keys():
		if key.lower().find("g_glossiness") > -1:
			material.specular_intensity = uniforms[key]
	for texturesType in textures.keys():
		textures_type = texturesType.lower() 
		flag = False
		for type_key in ['albedo', "normal"]:				# TO_DO:, 'mask', 'light', 'env','parallax','irradiance','curvature']:
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
				material_textureslot = material.texture_slots.add()
				material_textureslot.use_map_color_diffuse = False
				if textures_type.find("normal") > -1:
					texture.use_normal_map = True
					material_textureslot.use_map_normal = True
				elif textures_type.find("mask") > -1:
					material_textureslot.use_map_specular = True
					#texture.use_calculate_alpha = True
					#material_textureslot.use_map_alpha = True
				elif textures_type.find("light") > -1:
					material_textureslot.use_map_diffuse = True
				elif textures_type.find("env") > -1:
					material_textureslot.use_map_ambient = True
				elif textures_type.find("parallax") > -1:
					material_textureslot.use_map_displacement
				elif textures_type.find("irradiance") > -1:
					material_textureslot.use_map_emit = True
				elif textures_type.find("curvature") > -1:
					material_textureslot.use_map_warp = True
				else:
					material_textureslot.use_map_color_diffuse = True
				print('[+] adding texture %s to material %s' % (texture_name, material_name))
				material_textureslot.texture = texture
				material_textureslot.texture_coords = 'UV'
		else:
			print("[!] not supported texture %s_%s" % (textures[texturesType], texturesType))
	if not material.texture_slots[0]:
		print("[!] no textute found for material %s" % material_name)
	return material

def add_material_to_mesh(mesh, materials , uvs):
	for material in materials:
		print('linking material %s to mesh object %s' % (material.name, mesh.name))
		mesh.data.materials.append(material)
	bpy.context.scene.objects.active = mesh
	bpy.ops.object.mode_set(mode="EDIT")
	bm = bmesh.from_edit_mesh(mesh.data)
	uv_layer = bm.loops.layers.uv.verify()
	bm.faces.layers.tex.verify()
	for face in bm.faces:
		face.material_index = 0
		for l in face.loops:
			luv = l[uv_layer]
			ind = l.vert.index
			luv.uv = Vector(uvs[ind])
	bpy.ops.object.mode_set(mode='OBJECT')
	mesh.select = True
	bpy.ops.object.shade_smooth()
	#mesh.hide = True
	mesh.select = False
	
def format_wmb_mesh(wmb):
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
			for meshGroupIndex in range(wmb.wmb3_header.meshGroupCount):
				meshIndexArray = []
				for groupedMeshIndex in range(len(groupedMeshArray)):
					if groupedMeshArray[groupedMeshIndex].meshGroupIndex == meshGroupIndex:
						meshIndexArray.append(mesh_start + groupedMeshIndex)
				meshGroup = wmb.meshGroupArray[meshGroupIndex]
				for meshArrayIndex in (meshIndexArray):
					meshVertexGroupIndex = wmb.meshArray[meshArrayIndex].vertexGroupIndex
					if meshVertexGroupIndex == vertexGroupIndex:
						meshName = "%s_%d_%d"%(meshGroup.meshGroupname, meshArrayIndex, vertexGroupIndex)
						meshInfo = wmb.clear_unused_vertex(meshArrayIndex, meshVertexGroupIndex)
						vertices = meshInfo[0]
						faces =  meshInfo[1]
						usedVerticeIndexArray = meshInfo[2]
						boneWeightInfoArray = meshInfo[3]
						usedVerticeIndexArrays.append(usedVerticeIndexArray)
						flag = False
						has_bone = wmb.hasBone
						obj = construct_mesh([meshName, vertices, faces, has_bone, boneWeightInfoArray])
						meshes.append(obj)
	return meshes, uvs, usedVerticeIndexArrays

def get_wmb_material(wmb, texture_dir):
	materials = []
	if wmb.wta:
		for materialIndex in range(len(wmb.materialArray)):
			material = wmb.materialArray[materialIndex]
			material_name = material.materialName
			uniforms = material.uniformArray
			textures = material.textureArray
			for key in textures.keys():
				identifier = textures[key]
				texture_stream = wmb.wta.getTextureByIdentifier(identifier,wmb.wtp_fp)
				if texture_stream:
					if not os.path.exists("%s\%s.dds" %(texture_dir, identifier)):
						create_dir(texture_dir)
						texture_fp = open("%s\%s.dds" %(texture_dir, identifier), "wb")
						print('[+] dumping %s.dds'% identifier)
						texture_fp.write(texture_stream)
						texture_fp.close()
			materials.append([material_name,textures,uniforms])
	else:
		print('missing wta')
	return materials

def main(wmb_file = os.path.split(os.path.realpath(__file__))[0] + '\\test\\pl0000.dtt\\pl0000.wmb'):
	reset_blend()
	wmb = WMB3(wmb_file)
	wmbname = wmb_file.split('\\')[-1]
	texture_dir = wmb_file.replace(wmbname, '') 
	if wmb.hasBone:
		boneArray = [[bone.boneIndex, "bone%d"%bone.boneIndex, bone.parentIndex,"bone%d"%bone.parentIndex , bone.world_position, bone.world_rotation, bone.boneNumber] for bone in wmb.boneArray]
		construct_armature(wmbname.replace('.wmb','') ,boneArray)
	meshes, uvs, usedVerticeIndexArrays = format_wmb_mesh(wmb)
	wmb_materials = get_wmb_material(wmb, texture_dir)
	materials = []
	for materialIndex in range(len(wmb_materials)):
		material = wmb_materials[materialIndex]
		materials.append(consturct_materials(texture_dir, material))
	for meshGroupInfo in wmb.meshGroupInfoArray:
		for Index in range(len(meshGroupInfo.groupedMeshArray)):
			mesh_start = meshGroupInfo.meshStart
			meshIndex = int(meshes[Index + mesh_start].name.split('_')[-2])
			materialIndex = meshGroupInfo.groupedMeshArray[meshIndex - mesh_start].materialIndex
			groupIndex = int(meshes[Index + mesh_start].name.split('_')[-1])
			uv = []
			for i in range(len(usedVerticeIndexArrays[Index + mesh_start])):
				VertexIndex = usedVerticeIndexArrays[Index + mesh_start][i]
				uv.append( uvs[groupIndex][VertexIndex])
			add_material_to_mesh(meshes[Index + mesh_start], [materials[materialIndex]], uv)
	amt = bpy.data.objects.get(wmbname.replace('.wmb',''))
	if wmb.hasBone:
		for mesh in meshes:
			set_partent(amt,mesh)
	return {'FINISHED'}

if __name__ == '__main__':
	main()