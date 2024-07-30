import re

import bpy


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

        layout.label(text="Current Object Collision")
        if context.object and "collisionType" in context.object:
            row = layout.row()
            row.label(text="Collision Type")
            row.prop(context.object, "collisionType", text="")
            if context.object.collisionType == "-1":
                row = layout.row()
                row.label(text="Unknown type")
                row.prop(context.object, "UNKNOWN_collisionType", text="")
            row = layout.row()
            row.label(text="Surface Type")
            row.prop(context.object, "surfaceType", text="")
            row = layout.row()
            row.label(text="Modifier")
            row.prop(context.object, "colModifier", text="")

            if len(bpy.context.selected_objects) > 1:
                row = layout.row()
                row.operator("b2n.apply_collision_to_all_selected")
        else:
            row = layout.row()
            row.label(text="No collision for this object")

        layout.separator()
        layout.label(text="Other Collision Tools")

        layout.operator("b2n.join_collision_objects")
        layout.operator("b2n.fix_collision_objects_order")
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
            obj.collisionType = context.object.collisionType
            obj.UNKNOWN_collisionType = context.object.UNKNOWN_collisionType
            obj.colModifier = context.object.colModifier
            obj.surfaceType = context.object.surfaceType
            if "unknownByte" in context.object:
                obj["unknownByte"] = context.object["unknownByte"]
        return {"FINISHED"}

class B2NJoinCollisionObjects(bpy.types.Operator):
    """Join Collision Objects"""
    bl_idname = "b2n.join_collision_objects"
    bl_label = "Join Similar Collision Objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        def objToKey(obj):
            return str({
                'name': re.sub(r'^\d+-', '', obj.name),
                'collisionType': obj.collisionType,
                'surfaceType': obj.surfaceType,
                'modifier': obj.colModifier,
                "unknownByte": obj["unknownByte"],
            })

        groupedObjects = {}
        for obj in bpy.data.collections["COL"].objects:
            if obj.type != "MESH":
                continue
            
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

class B2NFixCollisionObjectsOrder(bpy.types.Operator):
    """Fix Collision Objects Order"""
    bl_idname = "b2n.fix_collision_objects_order"
    bl_label = "Fix Collision Objects Order"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        objects = list(bpy.data.collections["COL"].objects)
        # Gather object names in order
        namesOrder = []
        groupedObjects = {}
        for obj in objects:
            objName = re.match(r'^\d+-(.*-\d+)$', obj.name)
            if not objName:
                continue
            objName = objName.group(1)
            if objName not in groupedObjects:
                namesOrder.append(objName)
                groupedObjects[objName] = []
            groupedObjects[objName].append(obj)

        # bring objects in order
        i = 0
        for name in namesOrder:
            for obj in groupedObjects[name]:
                obj.name = f"{i}-{name}"
                i += 1

        return {'FINISHED'}

class B2NSelectEmptyCollisionObjects(bpy.types.Operator):
    bl_idname = "b2n.select_empty_collision_objects"
    bl_label = "Select Empty Collision Objects"
    bl_description = "Select collision objects with 0 vertices"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        zeroObjectsCount = 0
        for obj in bpy.data.collections["COL"].objects:
            if obj.type != "MESH":
                continue

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
    bpy.utils.register_class(B2NFixCollisionObjectsOrder)
    bpy.utils.register_class(B2NSelectEmptyCollisionObjects)

    bpy.types.Scene.collisionTools = bpy.props.PointerProperty(type=CollisionToolsData)

def unregister():
    if not hasattr(bpy.types, B2NCollisionToolsPanel.bl_idname):
        return
    bpy.utils.unregister_class(CollisionToolsData)
    bpy.utils.unregister_class(B2NCollisionToolsPanel)
    bpy.utils.unregister_class(B2NApplyCollisionToAllSelected)
    bpy.utils.unregister_class(B2NJoinCollisionObjects)
    bpy.utils.unregister_class(B2NFixCollisionObjectsOrder)
    bpy.utils.unregister_class(B2NSelectEmptyCollisionObjects)
