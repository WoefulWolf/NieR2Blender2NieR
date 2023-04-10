import bpy, bmesh, math, mathutils

import xml.etree.ElementTree as ET
from ..common.bxm import bxmToXml, xmlToBxm

bone_items = []

def clh_bone_items(self, context):
    return bone_items

def update_clh_bone_items():
    global bone_items
    bone_items = []

    armatureObj = None
    for obj in bpy.data.collections['WMB'].all_objects:
        if obj.type == 'ARMATURE':
            armatureObj = obj
            break

    if armatureObj is None:
        return
    for bone in armatureObj.data.bones:
        if 'ID' in bone:
            bone_items.append((str(bone['ID']), bone.name + " (" + str(bone['ID']) + ")", ""))

def get_bone_from_id(bone_id):
    armatureObj = None
    for obj in bpy.data.collections['WMB'].all_objects:
        if obj.type == 'ARMATURE':
            armatureObj = obj
            break

    for bone in armatureObj.data.bones:
        if 'ID' in bone:
            if str(bone['ID']) == bone_id:
                return bone

    return None

class UpdateBoneItems(bpy.types.Operator):
    bl_idname = "clh.update_bone_items"
    bl_label = "Update Bone Items"
    bl_description = "Update Bone Items"

    def execute(self, context):
        update_clh_bone_items()
        return {'FINISHED'}

class ClothATWK(bpy.types.PropertyGroup):
    p1 : bpy.props.EnumProperty(items=clh_bone_items, default=0)
    p2 : bpy.props.EnumProperty(items=clh_bone_items, default=0)
    weight : bpy.props.FloatProperty(default=0.5)
    radius : bpy.props.FloatProperty(default=0.1)
    offset1 : bpy.props.FloatVectorProperty(default=(0.0, 0.0, 0.0))
    offset2 : bpy.props.FloatVectorProperty(default=(0.0, 0.0, 0.0))
    capsule : bpy.props.BoolProperty(default=False)

def importCLH(filepath):
    update_clh_bone_items()
    xml = bxmToXml(filepath)
    assert xml.tag == "CLOTH_AT"

    bpy.context.scene.clh_clothatnum = int(xml.find("CLOTH_AT_NUM").text)
    
    cloth_at_wk_list = xml.find("CLOTH_AT_WK_LIST")
    cloth_at_wk = bpy.context.scene.clh_clothatwk
    cloth_at_wk.clear()

    for idx, xml_cloth_at_wk in enumerate(cloth_at_wk_list.findall("CLOTH_AT_WK")):
        cloth_at_wk_item = cloth_at_wk.add()
        cloth_at_wk_item.index = idx
        cloth_at_wk_item.p1 = xml_cloth_at_wk.find("p1").text
        cloth_at_wk_item.p2 = xml_cloth_at_wk.find("p2").text
        cloth_at_wk_item.weight = float(xml_cloth_at_wk.find("weight").text)
        cloth_at_wk_item.radius = float(xml_cloth_at_wk.find("radius").text)
        cloth_at_wk_item.offset1 = [float(x) for x in xml_cloth_at_wk.find("offset1").text.split()]
        cloth_at_wk_item.offset2 = [float(x) for x in xml_cloth_at_wk.find("offset2").text.split()]
        cloth_at_wk_item.capsule = bool(int(xml_cloth_at_wk.find("capsule").text))

def exportCLH(filepath):
    xml = ET.Element("CLOTH_AT")
    bpy.context.scene.clh_clothatnum = len(bpy.context.scene.clh_clothatwk)
    ET.SubElement(xml, "CLOTH_AT_NUM").text = str(bpy.context.scene.clh_clothatnum)

    xml_clothatwk_list = ET.SubElement(xml, "CLOTH_AT_WK_LIST")
    for cloth_at_wk_item in bpy.context.scene.clh_clothatwk:
        xml_clothatwk = ET.SubElement(xml_clothatwk_list, "CLOTH_AT_WK")
        ET.SubElement(xml_clothatwk, "p1").text = cloth_at_wk_item.p1
        ET.SubElement(xml_clothatwk, "p2").text = cloth_at_wk_item.p2
        ET.SubElement(xml_clothatwk, "weight").text = str(cloth_at_wk_item.weight)
        ET.SubElement(xml_clothatwk, "radius").text = str(cloth_at_wk_item.radius)
        ET.SubElement(xml_clothatwk, "offset1").text = " ".join([str(x) for x in cloth_at_wk_item.offset1])
        ET.SubElement(xml_clothatwk, "offset2").text = " ".join([str(x) for x in cloth_at_wk_item.offset2])
        ET.SubElement(xml_clothatwk, "capsule").text = str(int(cloth_at_wk_item.capsule))

    xmlToBxm(xml, filepath)

class MoveClothATWK(bpy.types.Operator):
    bl_idname = "clh.move_cloth_at_wk"
    bl_label = "Move Cloth AT WK"
    bl_description = "Move Cloth AT WK"

    index : bpy.props.IntProperty()
    direction : bpy.props.StringProperty(default="UP")

    def execute(self, context):
        if self.direction == "UP":
            bpy.context.scene.clh_clothatwk.move(self.index, self.index - 1)
        elif self.direction == "DOWN":
            bpy.context.scene.clh_clothatwk.move(self.index, self.index + 1)

        return {'FINISHED'}

class AddClothATWK(bpy.types.Operator):
    bl_idname = "clh.add_cloth_at_wk"
    bl_label = "Add ClothATWK"
    bl_description = "Add ClothATWK"

    def execute(self, context):
        cloth_atwk = bpy.context.scene.clh_clothatwk
        cloth_atwk_item = cloth_atwk.add()

        return {'FINISHED'}
    
class RemoveClothATWK(bpy.types.Operator):
    bl_idname = "clh.remove_cloth_at_wk"
    bl_label = "Remove ClothATWK"
    bl_description = "Remove ClothATWK"

    index : bpy.props.IntProperty()

    def execute(self, context):
        cloth_atwk = bpy.context.scene.clh_clothatwk
        # Remove using index
        cloth_atwk.remove(self.index)

        return {'FINISHED'}

def drawCLHWKList(layout):
    row = layout.row()
    row.operator("clh.add_cloth_at_wk", text="Add ClothATWK")

    next_container = layout
    for idx, cloth_at_wk in enumerate(bpy.context.scene.clh_clothatwk):
        if cloth_at_wk.capsule:
            next_container = layout.box()

        box = next_container.box()

        if not cloth_at_wk.capsule:
            next_container = layout

        row = box.row(align=True)
        label = "CLOTH_AT_WK " + str(idx)
        row.label(text=label)

        move_up = row.operator("clh.move_cloth_at_wk", text="", icon="TRIA_UP")
        move_up.index = idx
        move_up.direction = "UP"

        move_down = row.operator("clh.move_cloth_at_wk", text="", icon="TRIA_DOWN")
        move_down.index = idx
        move_down.direction = "DOWN"

        remove = row.operator("clh.remove_cloth_at_wk", text="", icon="X").index = idx

        row = box.row()
        row.prop(cloth_at_wk, "p1", text="P1")
        row.prop(cloth_at_wk, "p2", text="P2")
        row = box.row()
        row.prop(cloth_at_wk, "offset1", text="Offset1")
        row.prop(cloth_at_wk, "offset2", text="Offset2")
        row = box.row()
        row.prop(cloth_at_wk, "weight", text="Weight")
        row.prop(cloth_at_wk, "radius", text="Radius")
        row.prop(cloth_at_wk, "capsule", text="Capsule")

class UpdateCLHVisualizer(bpy.types.Operator):
    bl_idname = "clh.update_clh_visualizer"
    bl_label = "Update CLH Visualizer"
    bl_description = "Update CLH Visualizer"

    def execute(self, context):
        update_clh_bone_items()
        
        clhCollection = bpy.data.collections.get("CLH")
        if not clhCollection:
            clhCollection = bpy.data.collections.new("CLH")
            bpy.context.scene.collection.children.link(clhCollection)

        for obj in clhCollection.objects:
            bpy.data.objects.remove(obj)

        selected_objs = []
        active_selected_obj = None
        for idx, cloth_at_wk in enumerate(bpy.context.scene.clh_clothatwk):
            p1_bone = get_bone_from_id(cloth_at_wk.p1)
            p2_bone = get_bone_from_id(cloth_at_wk.p2)

            if p1_bone is None or p2_bone is None:
                continue

            pos1 = p1_bone.head_local + mathutils.Vector(cloth_at_wk.offset1)
            pos2 = p2_bone.head_local + mathutils.Vector(cloth_at_wk.offset2)

            # Rotate 90 on x
            pos1.rotate(mathutils.Euler((math.pi / 2, 0, 0), 'XYZ'))
            pos2.rotate(mathutils.Euler((math.pi / 2, 0, 0), 'XYZ'))

            weight = cloth_at_wk.weight

            # Use weight to determine how far between the two points the sphere should be
            final_pos = pos2.lerp(pos1, weight)

            name = "CLOTH_AT_WK " + str(idx)

            mesh = bpy.data.meshes.new(name)
            obj = bpy.data.objects.new(name, mesh)

            clhCollection.objects.link(obj)

            bm = bmesh.new()
            bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=9, radius=cloth_at_wk.radius)
            bm.to_mesh(mesh)
            bm.free()

            obj.location = final_pos

            obj.color = (0.0, 1.0, 0.0, 1.0)

            if active_selected_obj is not None:
                obj.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
                selected_objs.append(obj)

                with bpy.context.temp_override(active_object=active_selected_obj, selected_editable_objects=selected_objs):
                    bpy.ops.object.join()

                active_selected_obj = None

            # Create a cylinder to the next point if this point is a capsule
            if cloth_at_wk.capsule:
                selected_objs = [obj]
                next_cloth_at_wk = bpy.context.scene.clh_clothatwk[idx + 1]
                next_p1_bone = get_bone_from_id(next_cloth_at_wk.p1)
                next_p2_bone = get_bone_from_id(next_cloth_at_wk.p2)

                if next_p1_bone is None or next_p2_bone is None:
                    continue
                
                next_pos1 = next_p1_bone.head_local + mathutils.Vector(next_cloth_at_wk.offset1)
                next_pos2 = next_p2_bone.head_local + mathutils.Vector(next_cloth_at_wk.offset2)

                next_pos1.rotate(mathutils.Euler((math.pi / 2, 0, 0), 'XYZ'))
                next_pos2.rotate(mathutils.Euler((math.pi / 2, 0, 0), 'XYZ'))

                next_weight = next_cloth_at_wk.weight
                next_final_pos = next_pos2.lerp(next_pos1, next_weight)

                direction = next_final_pos - final_pos

                name = "CLOTH_AT_WK " + str(idx) + " to " + str(idx + 1) + " capsule"

                mesh = bpy.data.meshes.new(name)
                cyl_obj = bpy.data.objects.new(name, mesh)

                clhCollection.objects.link(cyl_obj)

                bm = bmesh.new()
                bmesh.ops.create_cone(bm, cap_ends=False, cap_tris=True, segments=16, radius1=cloth_at_wk.radius, radius2=next_cloth_at_wk.radius, depth=direction.length)
                bm.to_mesh(mesh)
                bm.free()

                # Rotate the cylinder to point in the right direction
                cyl_obj.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
                obj.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()

                # Set the location to the midpoint between the two points
                cyl_obj.location = final_pos.lerp(next_final_pos, 0.5)

                cyl_obj.color = (1.0, 0.0, 0.0, 1.0)

                selected_objs.append(cyl_obj)
                active_selected_obj = cyl_obj


        return {'FINISHED'}
    
class ClearCLHVisualizer(bpy.types.Operator):
    bl_idname = "clh.clear_clh_visualizer"
    bl_label = "Clear CLH Visualizer"
    bl_description = "Clear CLH Visualizer"

    def execute(self, context):
        clhCollection = bpy.data.collections.get("CLH")
        if not clhCollection:
            clhCollection = bpy.data.collections.new("CLH")
            bpy.context.scene.collection.children.link(clhCollection)

        for obj in clhCollection.objects:
            bpy.data.objects.remove(obj)

        return {'FINISHED'}

def drawCLHVisualizer(layout):
    row = layout.row()
    row.operator("clh.update_clh_visualizer")

    row = layout.row()
    row.operator("clh.clear_clh_visualizer")


def register():
    bpy.utils.register_class(ClothATWK)
    bpy.utils.register_class(UpdateBoneItems)
    bpy.utils.register_class(MoveClothATWK)
    bpy.utils.register_class(AddClothATWK)
    bpy.utils.register_class(RemoveClothATWK)

    bpy.utils.register_class(UpdateCLHVisualizer)
    bpy.utils.register_class(ClearCLHVisualizer)

    bpy.types.Scene.clh_clothatnum = bpy.props.IntProperty(default=0)
    bpy.types.Scene.clh_clothatwk = bpy.props.CollectionProperty(type=ClothATWK)

def unregister():
    bpy.utils.unregister_class(ClothATWK)
    bpy.utils.unregister_class(UpdateBoneItems)
    bpy.utils.unregister_class(MoveClothATWK)
    bpy.utils.unregister_class(AddClothATWK)
    bpy.utils.unregister_class(RemoveClothATWK)

    bpy.utils.unregister_class(UpdateCLHVisualizer)
    bpy.utils.unregister_class(ClearCLHVisualizer)

    del bpy.types.Scene.clh_clothatnum
    del bpy.types.Scene.clh_clothatwk