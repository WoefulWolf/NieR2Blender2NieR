import re
import bmesh
import bpy

from .util import ShowMessageBox


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
                    obj.data.name = regex.group()

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

        ShowMessageBox(str(v_unused_count) + ' vertex groups were unused and have been removed.', 'Blender2NieR: Tool Info')
        return {'FINISHED'}


def merge_vertex_group_weights(obj, base, other):
    mix_modifier = obj.modifiers.new("MergeWeights", "VERTEX_WEIGHT_MIX")
    mix_modifier.vertex_group_a = base.name
    mix_modifier.vertex_group_b = other.name
    mix_modifier.mix_mode = "ADD"
    mix_modifier.mix_set = "B"

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
                    for group2 in v_groups:
                        if (group2 == group1):
                            continue
                        if (group2.name.split(".")[0] == group1.name):
                            v_merged_count += 1
                            merge_vertex_group_weights(obj, group1, group2)

            for mod in obj.modifiers:
                if ("MergeWeights" in mod.name):
                    bpy.ops.object.modifier_apply(modifier=mod.name)

            for vg in obj.vertex_groups:
                if ("." in vg.name):
                    obj.vertex_groups.remove(vg)

        bpy.context.view_layer.objects.active = last_active
        ShowMessageBox(str(v_merged_count) + ' vertex groups had name copies and have been merged.', 'Blender2NieR: Tool Info')

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

        if v_delete_count > 0:
            ShowMessageBox(str(v_delete_count) + ' vertexes have been deleted.', 'Blender2NieR: Tool Info')
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

        if v_delete_count > 0:
            ShowMessageBox(str(v_delete_count) + ' vertexes have been deleted.', 'Blender2NieR: Tool Info')
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
