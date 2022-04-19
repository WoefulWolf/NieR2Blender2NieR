import os
import sys
import struct
import numpy as np
import bpy
import re
import bmesh
from mathutils import Vector

def create_wmb(filepath):
    print('Creating wmb file: ', filepath)
    wmb_file = open(filepath, 'wb')
    return wmb_file

def write_float(file, float):
    entry = struct.pack('<f', float)
    file.write(entry)

def write_char(file, char):
    entry = struct.pack('<s', bytes(char, 'utf-8'))
    file.write(entry)

def write_string(file, str):
    for char in str:
        write_char(file, char)
    write_buffer(file, 1)

def write_Int32(file, int):
    entry = struct.pack('<i', int)
    file.write(entry)

def write_uInt32(file, int):
    entry = struct.pack('<I', int)
    file.write(entry)

def write_Int16(file, int):
    entry = struct.pack('<h', int)
    file.write(entry)

def write_uInt16(file, int):
    entry = struct.pack('<H', int)
    file.write(entry)

def write_xyz(file, xyz):
    for val in xyz:
        write_float(file, val)

def write_buffer(file, size):
    for i in range(size):
        write_char(file, '')

def write_byte(file, val):
    entry = struct.pack('B', val)
    file.write(entry)

def write_float16(file, val):
    entry = struct.pack("<e", val)
    file.write(entry)

def close_wmb(wmb_file, generated_data):
    wmb_file.seek(generated_data.lods_Offset-52)
    write_string(wmb_file, 'WMB created with Blender2NieR v0.3.0 by Woeful_Wolf')
    wmb_file.flush()
    wmb_file.close()

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

class B2NRecalculateObjectIndices(bpy.types.Operator):
    """Re-calculate object indices for ordering (e.g. ##_Body_0)"""
    bl_idname = "b2n.recalculateobjectindices"
    bl_label = "Re-calculate Object Indices"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        objects_list = []
        for obj in bpy.data.collections['WMB'].all_objects:
            if obj.type == "MESH":
                objects_list.append(obj)
        objects_list.sort(key = lambda x: int(x.name.split("-")[0]))

        for idx, obj in reversed(list(enumerate(objects_list))):
            split_name = obj.name.split("-")
            obj.name = str(idx) + "-" + split_name[1] + "-" + split_name[2]

        for obj in bpy.data.collections['WMB'].all_objects:
            if obj.type == "MESH":
                regex = re.search(".*(?=\.)", obj.name)
                if regex != None:
                    obj.name = regex.group()

        return {'FINISHED'}

class B2NRemoveUnusedVertexGroups(bpy.types.Operator):
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
                    armatch = re.search('((.R|.L)(.(\d){1,}){0,1})(?!.)', vgroup_name)
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

class B2NMergeVertexGroupCopies(bpy.types.Operator):
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

class B2NDeleteLooseGeometrySelected(bpy.types.Operator):
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

class B2NDeleteLooseGeometryAll(bpy.types.Operator):
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

class B2NRipMeshByUVIslands(bpy.types.Operator):
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