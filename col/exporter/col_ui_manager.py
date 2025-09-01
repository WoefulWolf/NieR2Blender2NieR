import re

import bpy
from ...utils.util import getAllMeshObjectsInOrder, getMeshName, setColourByCollisionType

def onGlobalAlphaChange(self, context):
    for obj in bpy.data.collections["COL"].objects:
        if obj.type != "MESH":
            continue
        obj.color[3] = context.scene.collisionTools.globalAlpha

class CollisionToolsData(bpy.types.PropertyGroup):
    globalAlpha: bpy.props.FloatProperty(name="Collision Alpha", default=1.0, min=0.0, max=1.0, update = onGlobalAlphaChange)

class B2NCollisionToolsPanel(bpy.types.Panel):
    bl_label = "Collision Tools"
    bl_idname = "B2N_PT_COLLISION_TOOLS"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "NA: Collision Tools"

    def draw(self, context):
        layout = self.layout

        if len(bpy.context.selected_objects) > 1:
            row = layout.row()
            row.operator("b2n.apply_collision_to_all_selected")
        layout.operator("b2n.join_collision_objects")
        layout.operator("b2n.select_empty_collision_objects")
        row = layout.row()
        row.label(text="Collision Alpha")
        row.prop(context.scene.collisionTools, "globalAlpha", text="")

class B2NApplyCollisionToAllSelected(bpy.types.Operator):
    bl_idname = "b2n.apply_collision_to_all_selected"
    bl_label = "Apply Collision to All Selected"
    bl_description = "Apply collision settings to all selected objects"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        for obj in bpy.context.selected_objects:
            if obj.type != "MESH":
                continue
            obj.col_mesh_props.is_col_mesh = context.object.col_mesh_props.is_col_mesh
            obj.col_mesh_props.col_type = context.object.col_mesh_props.col_type
            obj.col_mesh_props.unk_col_type = context.object.col_mesh_props.unk_col_type
            obj.col_mesh_props.modifier = context.object.col_mesh_props.modifier
            obj.col_mesh_props.surface_type = context.object.col_mesh_props.surface_type
            obj.col_mesh_props.unk_surface_type = context.object.col_mesh_props.unk_surface_type
            obj.col_mesh_props.unk_byte = context.object.col_mesh_props.unk_byte
            setColourByCollisionType(obj)
        return {"FINISHED"}

class B2NJoinCollisionObjects(bpy.types.Operator):
    """Join Collision Objects"""
    bl_idname = "b2n.join_collision_objects"
    bl_label = "Join Similar Collision Objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        def objToKey(obj):
            return str({
                'name': getMeshName(obj),
                'is_col_mesh': obj.col_mesh_props.is_col_mesh,
                'col_type': obj.col_mesh_props.col_type,
                'unk_col_type': obj.col_mesh_props.unk_col_type,
                'modifier': obj.col_mesh_props.modifier,
                'surface_type': obj.col_mesh_props.surface_type,
                'unk_surface_type': obj.col_mesh_props.unk_surface_type,
                'unk_byte': obj.col_mesh_props.unk_byte,
            })

        groupedObjects = {}
        for obj in getAllMeshObjectsInOrder("COL"):
            key = objToKey(obj)
            if key not in groupedObjects:
                groupedObjects[key] = []
            groupedObjects[key].append(obj)


        for key, objects in groupedObjects.items():
            if len(objects) == 1:
                continue
            bpy.ops.object.select_all(action='DESELECT')
            for obj in objects:
                obj.select_set(True)
            bpy.context.view_layer.objects.active = objects[0]
            bpy.ops.object.join()

        return {'FINISHED'}

class B2NSelectEmptyCollisionObjects(bpy.types.Operator):
    bl_idname = "b2n.select_empty_collision_objects"
    bl_label = "Select Empty Collision Objects"
    bl_description = "Select collision objects with 0 vertices"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        zeroObjectsCount = 0
        for obj in getAllMeshObjectsInOrder("COL"):
            if len(obj.data.vertices) == 0:
                zeroObjectsCount += 1
                obj.select_set(True)
                bpy.context.view_layer.objects.active = obj

        self.report({'INFO'}, f"{zeroObjectsCount} object{'' if zeroObjectsCount == 1 else 's'} with 0 vertices")

        return {'FINISHED'}

def enableCollisionTools():
    if hasattr(bpy.types, B2NCollisionToolsPanel.bl_idname):
        return
    register()

def disableCollisionTools():
    if not hasattr(bpy.types, B2NCollisionToolsPanel.bl_idname):
        return
    unregister()

def register():
    if hasattr(bpy.types, B2NCollisionToolsPanel.bl_idname):
        return
    bpy.utils.register_class(CollisionToolsData)
    bpy.utils.register_class(B2NCollisionToolsPanel)
    bpy.utils.register_class(B2NApplyCollisionToAllSelected)
    bpy.utils.register_class(B2NJoinCollisionObjects)
    bpy.utils.register_class(B2NSelectEmptyCollisionObjects)

    bpy.types.Scene.collisionTools = bpy.props.PointerProperty(type=CollisionToolsData)

def unregister():
    if not hasattr(bpy.types, B2NCollisionToolsPanel.bl_idname):
        return
    bpy.utils.unregister_class(CollisionToolsData)
    bpy.utils.unregister_class(B2NCollisionToolsPanel)
    bpy.utils.unregister_class(B2NApplyCollisionToAllSelected)
    bpy.utils.unregister_class(B2NJoinCollisionObjects)
    bpy.utils.unregister_class(B2NSelectEmptyCollisionObjects)
