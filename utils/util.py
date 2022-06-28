import os
import re
import bmesh
import bpy
import numpy as np
from mathutils import Vector


def uInt32_array_size(array):
    return len(array) * 4

class Vector3(object):
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.xyz = [x, y, z]

def show_message(message = "", title = "Message Box", icon = 'INFO'):
    def draw(self, context):
        self.layout.label(text = message)
        self.layout.alignment = 'CENTER'
    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

def getUsedMaterials():
    materials = []
    for obj in (x for x in bpy.data.collections['WMB'].all_objects if x.type == "MESH"):
        for slot in obj.material_slots:
            material = slot.material
            if material not in materials:
                materials.append(material)
    return materials

def getObjectCenter(obj):
    obj_local_bbox_center = 0.125 * sum((Vector(b) for b in obj.bound_box), Vector())
    #obj_global_bbox_center = obj.matrix_world @ obj_local_bbox_center
    return obj_local_bbox_center

def getGlobalBoundingBox():
    xVals = []
    yVals = []
    zVals = []

    for obj in (x for x in bpy.data.collections['WMB'].all_objects if x.type == "MESH"):
        xVals.extend([getObjectCenter(obj)[0] - obj.dimensions[0]/2, getObjectCenter(obj)[0] + obj.dimensions[0]/2])
        yVals.extend([getObjectCenter(obj)[1] - obj.dimensions[1]/2, getObjectCenter(obj)[1] + obj.dimensions[1]/2])
        zVals.extend([getObjectCenter(obj)[2] - obj.dimensions[2]/2, getObjectCenter(obj)[2] + obj.dimensions[2]/2])

    minX = min(xVals)
    maxX = max(xVals)
    minY = min(yVals)
    maxY = max(yVals)
    minZ = min(zVals)
    maxZ = max(zVals)

    midPoint = [(minX + maxX)/2, (minY + maxY)/2, (minZ + maxZ)/2]
    scale = [maxX - midPoint[0], maxY - midPoint[1], maxZ - midPoint[2]]
    return midPoint, scale

class RecalculateObjectIndices(bpy.types.Operator):
    """Re-calculate object indices for ordering (e.g. ##_Body_0)"""
    bl_idname = "b2n.recalculateobjectindices"
    bl_label = "Re-calculate Object Indices"
    bl_options = {'REGISTER', 'UNDO'}

    def recalculateIndicesInCollection(self, collectionName: str):
        if collectionName not in bpy.data.collections:
            return
        objects_list = []
        for obj in bpy.data.collections[collectionName].all_objects:
            if obj.type == "MESH":
                objects_list.append(obj)
        objects_list.sort(key = lambda x: int(x.name.split("-")[0]))

        for idx, obj in reversed(list(enumerate(objects_list))):
            split_name = obj.name.split("-")
            obj.name = str(idx) + "-" + split_name[1] + "-" + split_name[2]

        for obj in bpy.data.collections[collectionName].all_objects:
            if obj.type == "MESH":
                regex = re.search(".*(?=\.)", obj.name)
                if regex != None:
                    obj.name = regex.group()

    def execute(self, context):
        self.recalculateIndicesInCollection("WMB")
        self.recalculateIndicesInCollection("COL")

        return {'FINISHED'}

class RemoveUnusedVertexGroups(bpy.types.Operator):
    """Remove all unused vertex groups."""
    bl_idname = "b2n.removeunusedvertexgroups"
    bl_label = "Remove Unused Vertex Groups"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ob = bpy.context.active_object
        ob.update_from_editmode()

        vgroup_used = {i: False for i, k in enumerate(ob.vertex_groups)}
        vgroup_names = {i: k.name for i, k in enumerate(ob.vertex_groups)}

        for v in ob.data.vertices:
            for g in v.groups:
                if g.weight > 0.0:
                    vgroup_used[g.group] = True
                    vgroup_name = vgroup_names[g.group]
                    armatch = re.search('((.R|.L)(.(\d)+)?)(?!.)', vgroup_name)
                    if armatch != None:
                        tag = armatch.group()
                        mirror_tag =  tag.replace(".R", ".L") if armatch.group(2) == ".R" else tag.replace(".L", ".R")
                        mirror_vgname = vgroup_name.replace(tag, mirror_tag)
                        for i, name in sorted(vgroup_names.items(), reverse=True):
                            if mirror_vgname == name:
                                vgroup_used[i] = True
                                break
        v_unused_count = 0
        for i, used in sorted(vgroup_used.items(), reverse=True):
            if not used:
                v_unused_count += 1
                ob.vertex_groups.remove(ob.vertex_groups[i])

        show_message(str(v_unused_count) + ' vertex groups were unused and have been removed.', 'Blender2NieR: Tool Info')
        return {'FINISHED'}

class MergeVertexGroupCopies(bpy.types.Operator):
    """Merge vertex groups by name copies (etc. bone69 & bone69.001)"""
    bl_idname = "b2n.mergevertexgroupcopies"
    bl_label = "Merge Vertex Groups by Name Copies"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_objects = bpy.context.selected_objects
        last_active = bpy.context.active_object

        v_merged_count = 0
        for obj in selected_objects:
            bpy.context.view_layer.objects.active = obj
            v_groups = obj.vertex_groups
            for group1 in v_groups:
                if "." not in group1.name:
                    print(group1.name)
                    for group2 in v_groups:
                        if (group2.name.split(".")[0] == group1.name) and (group2 != group1):
                            v_merged_count += 1
                            bpy.ops.object.modifier_add(type="VERTEX_WEIGHT_MIX")
                            mix_modifier = bpy.context.object.modifiers["VertexWeightMix"]
                            mix_modifier.vertex_group_a = group1.name
                            mix_modifier.vertex_group_b = group2.name
                            mix_modifier.mix_mode = "ADD"
                            mix_modifier.mix_set = "B"
                            bpy.ops.object.modifier_apply(modifier="VertexWeightMix")
                            bpy.ops.object.vertex_group_set_active(group=group2.name)
                            bpy.ops.object.vertex_group_remove()

        bpy.context.view_layer.objects.active = last_active
        show_message(str(v_merged_count) + ' vertex groups had name copies and have been merged.', 'Blender2NieR: Tool Info')

        return {'FINISHED'}

class DeleteLooseGeometrySelected(bpy.types.Operator):
    """Delete Loose Geometry (Selected)"""
    bl_idname = "b2n.deleteloosegeometrysel"
    bl_label = "Delete Loose Geometry (Selected)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context = bpy.context
        meshes = set(o.data for o in context.selected_objects if o.type == 'MESH')
        bm = bmesh.new()

        v_delete_count = 0
        for m in meshes:

            bm.from_mesh(m)
            # verts with no linked faces
            verts = [v for v in bm.verts if not v.link_faces]

            print(f"{m.name}: removed {len(verts)} verts")
            v_delete_count += len(verts)
            # equiv of bmesh.ops.delete(bm, geom=verts, context='VERTS')
            for v in verts:
                bm.verts.remove(v)

            bm.to_mesh(m)
            m.update()
            bm.clear()

        show_message(str(v_delete_count) + ' vertexes have been deleted.', 'Blender2NieR: Tool Info')
        return {'FINISHED'}

class DeleteLooseGeometryAll(bpy.types.Operator):
    """Delete Loose Geometry (All)"""
    bl_idname = "b2n.deleteloosegeometryall"
    bl_label = "Delete Loose Geometry (All)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context = bpy.context
        meshes = set(o.data for o in bpy.data.objects if o.type == 'MESH')
        bm = bmesh.new()

        v_delete_count = 0
        for m in meshes:

            bm.from_mesh(m)
            # verts with no linked faces
            verts = [v for v in bm.verts if not v.link_faces]

            print(f"{m.name}: removed {len(verts)} verts")
            v_delete_count += len(verts)
            # equiv of bmesh.ops.delete(bm, geom=verts, context='VERTS')
            for v in verts:
                bm.verts.remove(v)

            bm.to_mesh(m)
            m.update()
            bm.clear()

        show_message(str(v_delete_count) + ' vertexes have been deleted.', 'Blender2NieR: Tool Info')
        return {'FINISHED'}

class RipMeshByUVIslands(bpy.types.Operator):
    """Rip Mesh by UV Islands"""
    bl_idname = "b2n.ripmeshbyuvislands"
    bl_label = "Rip Mesh by UV Islands"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        active_object = bpy.context.active_object
        bpy.ops.object.mode_set(mode = 'EDIT')

        bm = bmesh.from_edit_mesh(active_object.data)
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        bm.verts.ensure_lookup_table()
        #Store the current seams
        current_seams = [e for e in bm.edges if e.seam]
        #Clear seams
        for e in current_seams:
            e.seam = False
        #Make seams from uv islands with selection mess
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.select_all(action='SELECT')
        bpy.ops.uv.seams_from_islands(True)
        bpy.ops.uv.select_all(action='DESELECT')
        bpy.ops.mesh.select_all(action='DESELECT')
        #Get the result
        boundaries = [e for e in bm.edges if e.seam and len(e.link_faces) == 2]
        #Restore seams
        for e in boundaries:
            e.seam = False
        for e in current_seams:
            e.seam = True
        # Select the boundary edges
        for e in boundaries:
            e.select = True
        # Rip them
        bpy.ops.mesh.select_mode(type='EDGE')
        bpy.ops.mesh.rip('INVOKE_DEFAULT')
        bpy.ops.object.mode_set(mode = 'OBJECT')

        return {'FINISHED'}


def getObjKey(obj):
    p1 = obj.name.split('-')
    if p1[0].isdigit():
        return f"{int(p1[0]):04d}-"
    else:
        return f"0000-{obj.name}"

def objectsInCollectionInOrder(collectionName):
    return sorted(bpy.data.collections[collectionName].objects, key=getObjKey) if collectionName in bpy.data.collections else []

def allObjectsInCollectionInOrder(collectionName):
    return sorted(bpy.data.collections[collectionName].all_objects, key=getObjKey) if collectionName in bpy.data.collections else []

def create_dir(dirpath):
	if not os.path.exists(dirpath):
		os.makedirs(dirpath)

def find_files(dir_name,ext):
	filenameArray = []
	for dirpath,dirnames,filename in os.walk(dir_name):
		for file in filename:
			filename = "%s\%s"%(dirpath,file)
			#print(filename)
			if filename.find(ext) > -1:
				filenameArray.append(filename)
	return filenameArray

def print_class(obj):
	print ('\n'.join(sorted(['%s:\t%s ' % item for item in obj.__dict__.items() if item[0].find('Offset') < 0 or item[0].find('unknown') < 0 ])))
	print('\n')

def current_postion(fp):
	print(hex(fp.tell()))

def getObjectCenter(obj):
    obj_local_bbox_center = 0.125 * sum((Vector(b) for b in obj.bound_box), Vector())
    #obj_global_bbox_center = obj.matrix_world @ obj_local_bbox_center
    return obj_local_bbox_center

def getObjectVolume(obj):
    return np.prod(obj.dimensions)

def volumeInsideOther(volumeCenter, volumeScale, otherVolumeCenter, otherVolumeScale):
    xVals = [volumeCenter[0] - volumeScale[0]/2, volumeCenter[0] + volumeScale[0]/2]
    yVals = [volumeCenter[1] - volumeScale[1]/2, volumeCenter[1] + volumeScale[1]/2]
    zVals = [volumeCenter[2] - volumeScale[2]/2, volumeCenter[2] + volumeScale[2]/2]

    other_xVals = [otherVolumeCenter[0] - otherVolumeScale[0]/2, otherVolumeCenter[0] + otherVolumeScale[0]/2]
    other_yVals = [otherVolumeCenter[1] - otherVolumeScale[1]/2, otherVolumeCenter[1] + otherVolumeScale[1]/2]
    other_zVals = [otherVolumeCenter[2] - otherVolumeScale[2]/2, otherVolumeCenter[2] + otherVolumeScale[2]/2]

    if (max(xVals) <= max(other_xVals) and max(yVals) <= max(other_yVals) and max(zVals) <= max(other_zVals)):
        if (min(xVals) >= min(other_xVals) and min(yVals) >= min(other_yVals) and min(zVals) >= min(other_zVals)):
            return True
    return False

def getDistanceTo(pos, otherPos):
    return np.linalg.norm(otherPos - pos)

def getVolumeSurrounding(volumeCenter, volumeScale, otherVolumeCenter, otherVolumeScale):
    xVals = [volumeCenter[0] - volumeScale[0]/2, volumeCenter[0] + volumeScale[0]/2, otherVolumeCenter[0] - otherVolumeScale[0]/2, otherVolumeCenter[0] + otherVolumeScale[0]/2]
    yVals = [volumeCenter[1] - volumeScale[1]/2, volumeCenter[1] + volumeScale[1]/2, otherVolumeCenter[1] - otherVolumeScale[1]/2, otherVolumeCenter[1] + otherVolumeScale[1]/2]
    zVals = [volumeCenter[2] - volumeScale[2]/2, volumeCenter[2] + volumeScale[2]/2, otherVolumeCenter[2] - otherVolumeScale[2]/2, otherVolumeCenter[2] + otherVolumeScale[2]/2]

    minX = min(xVals)
    maxX = max(xVals)
    minY = min(yVals)
    maxY = max(yVals)
    minZ = min(zVals)
    maxZ = max(zVals)

    midPoint = [(minX + maxX)/2, (minY + maxY)/2, (minZ + maxZ)/2]
    scale = [maxX - midPoint[0], maxY - midPoint[1], maxZ - midPoint[2]]
    return midPoint, scale

class custom_ColTreeNode:
    def __init__(self):
        self.index = -1
        self.bObj = None

        self.position = [0, 0, 0]
        self.scale = [1, 1, 1]

        self.left = -1
        self.right = -1

        self.offsetMeshIndices = 0
        self.meshIndexCount = 0
        self.meshIndices = []

        self.structSize = 12 + 12 + (4 * 4)

    def getVolume(self):
        return np.prod(self.scale)

def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)


def triangulate_meshes(collection: str):
    if bpy.context.object is not None:
        bpy.ops.object.mode_set(mode='OBJECT')
    for obj in bpy.data.collections[collection].all_objects:
        if obj.type == 'MESH':
            # Triangulate
            me = obj.data
            bm = bmesh.new()
            bm.from_mesh(me)
            bmesh.ops.triangulate(bm, faces=bm.faces[:])
            bm.to_mesh(me)
            bm.free()

def centre_origins(collection: str):
    if bpy.context.object is not None:
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.scene.cursor.location = [0, 0, 0]
    for obj in bpy.data.collections[collection].all_objects:
        if obj.type == 'MESH':
            obj.select_set(True)
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
            obj.select_set(False)
