import bpy, bmesh, math, mathutils

import xml.etree.ElementTree as ET
from ..common.bxm import bxmToXml, xmlToBxm

class ClothSearchOptions(bpy.types.PropertyGroup):
    filter_by_selected : bpy.props.BoolProperty(default=True)

class ClothVisualizationOptions(bpy.types.PropertyGroup):
    show_rot_limit : bpy.props.BoolProperty(default=False)

class ClothHeader(bpy.types.PropertyGroup):
    m_num : bpy.props.IntProperty()
    m_limit_spring_rate : bpy.props.FloatProperty()
    m_spd_rate : bpy.props.FloatProperty()
    m_stretchy : bpy.props.FloatProperty()
    m_bundle_num : bpy.props.IntProperty()
    m_bundle_num2 : bpy.props.IntProperty()
    m_thick : bpy.props.FloatProperty()
    m_gravity_vec : bpy.props.FloatVectorProperty()
    m_gravity_parts_no : bpy.props.IntProperty()
    m_first_bundle_rate : bpy.props.FloatProperty()
    m_wind_vec : bpy.props.FloatVectorProperty()
    m_wind_parts_no : bpy.props.IntProperty()
    m_wind_offset : bpy.props.FloatVectorProperty()
    m_wind_sin : bpy.props.FloatProperty()
    m_hit_adjust_rate : bpy.props.FloatProperty()
    m_original_rate : bpy.props.FloatProperty()
    m_parent_gravity : bpy.props.FloatProperty()
    m_fix_axis : bpy.props.IntProperty()
    m_b_no_stretchy : bpy.props.BoolProperty()
    m_b_world_wind_enable : bpy.props.BoolProperty()
    m_b_at_center : bpy.props.BoolProperty()
    m_b_late_add_mode : bpy.props.BoolProperty()
    m_expand_max : bpy.props.FloatProperty()

bone_items = []

def clp_bone_items(self, context):
    return bone_items

def update_clp_bone_items():
    global bone_items
    bone_items = []
    bone_items.append((str(4095), "None (4095)", ""))

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

class ClothWK(bpy.types.PropertyGroup):
    no : bpy.props.EnumProperty(items=clp_bone_items, default=0)
    no_up : bpy.props.EnumProperty(items=clp_bone_items, default=0)
    no_down : bpy.props.EnumProperty(items=clp_bone_items, default=0)
    no_side : bpy.props.EnumProperty(items=clp_bone_items, default=0)
    no_poly : bpy.props.EnumProperty(items=clp_bone_items, default=0)
    no_fix : bpy.props.EnumProperty(items=clp_bone_items, default=0)

    rot_limit : bpy.props.FloatProperty(default=0.35)
    offset : bpy.props.FloatVectorProperty(default=(0, -0.1, 0))
    m_original_rate : bpy.props.FloatProperty(default=0)

def importCLP(filepath):
    update_clp_bone_items()
    xml = bxmToXml(filepath)
    assert xml.tag == "CLOTH"
    
    # Header
    clothheader = bpy.context.scene.clp_clothheader
    xml_clothheader = xml.find("CLOTH_HEADER")
    clothheader.m_num = int(xml_clothheader.find("m_Num").text)
    clothheader.m_limit_spring_rate = float(xml_clothheader.find("m_LimitSpringRate").text)
    clothheader.m_spd_rate = float(xml_clothheader.find("m_SpdRate").text)
    clothheader.m_stretchy = float(xml_clothheader.find("m_Stretchy").text)
    clothheader.m_bundle_num = int(xml_clothheader.find("m_BundleNum").text)
    clothheader.m_bundle_num2 = int(xml_clothheader.find("m_BundleNum2").text)
    clothheader.m_thick = float(xml_clothheader.find("m_Thick").text)
    clothheader.m_gravity_vec = [float(x) for x in xml_clothheader.find("m_GravityVec").text.split()]
    clothheader.m_gravity_parts_no = int(xml_clothheader.find("m_GravityPartsNo").text)
    clothheader.m_first_bundle_rate = float(xml_clothheader.find("m_FirstBundleRate").text)
    clothheader.m_wind_vec = [float(x) for x in xml_clothheader.find("m_WindVec").text.split()]
    clothheader.m_wind_parts_no = int(xml_clothheader.find("m_WindPartsNo").text)
    clothheader.m_wind_offset = [float(x) for x in xml_clothheader.find("m_WindOffset").text.split()]
    clothheader.m_wind_sin = float(xml_clothheader.find("m_WindSin").text)
    clothheader.m_hit_adjust_rate = float(xml_clothheader.find("m_HitAdjustRate").text)
    clothheader.m_original_rate = float(xml_clothheader.find("m_OriginalRate").text)
    clothheader.m_parent_gravity = float(xml_clothheader.find("m_ParentGravity").text)
    clothheader.m_fix_axis = int(xml_clothheader.find("m_FixAxis").text)
    clothheader.m_b_no_stretchy = bool(int(xml_clothheader.find("m_bNoStretchy").text))
    clothheader.m_b_world_wind_enable = bool(int(xml_clothheader.find("m_bWorldWindEnable").text))
    clothheader.m_b_at_center = bool(int(xml_clothheader.find("m_bAtCenter").text))
    clothheader.m_b_late_add_mode = bool(int(xml_clothheader.find("m_bLateAddMode").text))
    clothheader.m_expand_max = float(xml_clothheader.find("m_ExpandMax").text)

    cloth_wk_list = xml.find("CLOTH_WK_LIST")
    cloth_wk = bpy.context.scene.clp_clothwk
    cloth_wk.clear()
    for xml_cloth_wk in cloth_wk_list.findall("CLOTH_WK"):
        cloth_wk_item = cloth_wk.add()

        cloth_wk_item.no = xml_cloth_wk.find("no").text
        cloth_wk_item.no_up = xml_cloth_wk.find("noUp").text
        cloth_wk_item.no_down = xml_cloth_wk.find("noDown").text
        cloth_wk_item.no_side = xml_cloth_wk.find("noSide").text
        cloth_wk_item.no_poly = xml_cloth_wk.find("noPoly").text
        cloth_wk_item.no_fix = xml_cloth_wk.find("noFix").text

        cloth_wk_item.rot_limit = float(xml_cloth_wk.find("rotLimit").text)
        cloth_wk_item.offset = [float(x) for x in xml_cloth_wk.find("offset").text.split()]
        cloth_wk_item.m_original_rate = float(xml_cloth_wk.find("m_OriginalRate").text)

def exportCLP(filepath):
    # Create XML from blender data
    xml = ET.Element("CLOTH")
    xml_clothheader = ET.SubElement(xml, "CLOTH_HEADER")
    xml_clothwk_list = ET.SubElement(xml, "CLOTH_WK_LIST")
    
    # Header
    clothheader = bpy.context.scene.clp_clothheader
    # Update header m_Num
    clothheader.m_num = len(bpy.context.scene.clp_clothwk)
    ET.SubElement(xml_clothheader, "m_Num").text = str(clothheader.m_num)
    ET.SubElement(xml_clothheader, "m_LimitSpringRate").text = str(clothheader.m_limit_spring_rate)
    ET.SubElement(xml_clothheader, "m_SpdRate").text = str(clothheader.m_spd_rate)
    ET.SubElement(xml_clothheader, "m_Stretchy").text = str(clothheader.m_stretchy)
    ET.SubElement(xml_clothheader, "m_BundleNum").text = str(clothheader.m_bundle_num)
    ET.SubElement(xml_clothheader, "m_BundleNum2").text = str(clothheader.m_bundle_num2)
    ET.SubElement(xml_clothheader, "m_Thick").text = str(clothheader.m_thick)
    ET.SubElement(xml_clothheader, "m_GravityVec").text = " ".join([str(x) for x in clothheader.m_gravity_vec])
    ET.SubElement(xml_clothheader, "m_GravityPartsNo").text = str(clothheader.m_gravity_parts_no)
    ET.SubElement(xml_clothheader, "m_FirstBundleRate").text = str(clothheader.m_first_bundle_rate)
    ET.SubElement(xml_clothheader, "m_WindVec").text = " ".join([str(x) for x in clothheader.m_wind_vec])
    ET.SubElement(xml_clothheader, "m_WindPartsNo").text = str(clothheader.m_wind_parts_no)
    ET.SubElement(xml_clothheader, "m_WindOffset").text = " ".join([str(x) for x in clothheader.m_wind_offset])
    ET.SubElement(xml_clothheader, "m_WindSin").text = str(clothheader.m_wind_sin)
    ET.SubElement(xml_clothheader, "m_HitAdjustRate").text = str(clothheader.m_hit_adjust_rate)
    ET.SubElement(xml_clothheader, "m_OriginalRate").text = str(clothheader.m_original_rate)
    ET.SubElement(xml_clothheader, "m_ParentGravity").text = str(clothheader.m_parent_gravity)
    ET.SubElement(xml_clothheader, "m_FixAxis").text = str(clothheader.m_fix_axis)
    ET.SubElement(xml_clothheader, "m_bNoStretchy").text = str(int(clothheader.m_b_no_stretchy))
    ET.SubElement(xml_clothheader, "m_bWorldWindEnable").text = str(int(clothheader.m_b_world_wind_enable))
    ET.SubElement(xml_clothheader, "m_bAtCenter").text = str(int(clothheader.m_b_at_center))
    ET.SubElement(xml_clothheader, "m_bLateAddMode").text = str(int(clothheader.m_b_late_add_mode))
    ET.SubElement(xml_clothheader, "m_ExpandMax").text = str(clothheader.m_expand_max)

    # Cloth List
    cloth_wk = bpy.context.scene.clp_clothwk
    for cloth_wk_item in cloth_wk:
        xml_clothwk = ET.SubElement(xml_clothwk_list, "CLOTH_WK")
        ET.SubElement(xml_clothwk, "no").text = cloth_wk_item.no
        ET.SubElement(xml_clothwk, "noUp").text = cloth_wk_item.no_up
        ET.SubElement(xml_clothwk, "noDown").text = cloth_wk_item.no_down
        ET.SubElement(xml_clothwk, "noSide").text = cloth_wk_item.no_side
        ET.SubElement(xml_clothwk, "noPoly").text = cloth_wk_item.no_poly
        ET.SubElement(xml_clothwk, "noFix").text = cloth_wk_item.no_fix
        ET.SubElement(xml_clothwk, "rotLimit").text = str(cloth_wk_item.rot_limit)
        ET.SubElement(xml_clothwk, "offset").text = " ".join([str(x) for x in cloth_wk_item.offset])
        ET.SubElement(xml_clothwk, "m_OriginalRate").text = str(cloth_wk_item.m_original_rate)

    # Write BXM to file
    xmlToBxm(xml, filepath)

def drawCLPHeader(layout):
    layout.label(text="CLOTH_HEADER")
    clothheader = bpy.context.scene.clp_clothheader
    layout.prop(clothheader, "m_limit_spring_rate")
    layout.prop(clothheader, "m_spd_rate")
    layout.prop(clothheader, "m_stretchy")
    layout.prop(clothheader, "m_bundle_num")
    layout.prop(clothheader, "m_bundle_num2")
    layout.prop(clothheader, "m_thick")
    layout.prop(clothheader, "m_gravity_vec")
    layout.prop(clothheader, "m_gravity_parts_no")
    layout.prop(clothheader, "m_first_bundle_rate")
    layout.prop(clothheader, "m_wind_vec")
    layout.prop(clothheader, "m_wind_parts_no")
    layout.prop(clothheader, "m_wind_offset")
    layout.prop(clothheader, "m_wind_sin")
    layout.prop(clothheader, "m_hit_adjust_rate")
    layout.prop(clothheader, "m_original_rate")
    layout.prop(clothheader, "m_parent_gravity")
    layout.prop(clothheader, "m_fix_axis")
    layout.prop(clothheader, "m_b_no_stretchy")
    layout.prop(clothheader, "m_b_world_wind_enable")
    layout.prop(clothheader, "m_b_at_center")
    layout.prop(clothheader, "m_b_late_add_mode")
    layout.prop(clothheader, "m_expand_max")

class UpdateBoneItems(bpy.types.Operator):
    bl_idname = "clp.update_bone_items"
    bl_label = "Update Bone Items"
    bl_description = "Update Bone Items"

    def execute(self, context):
        update_clp_bone_items()
        return {'FINISHED'}


class AddClothWK(bpy.types.Operator):
    bl_idname = "clp.add_clothwk"
    bl_label = "Add ClothWK"
    bl_description = "Add ClothWK"

    def execute(self, context):
        cloth_wk = bpy.context.scene.clp_clothwk
        selected_bones = bpy.context.selected_bones
        
        if selected_bones:
            for bone in selected_bones:
                if 'ID' in bone:
                    cloth_wk_item = cloth_wk.add()
                    cloth_wk_item.no = str(bone['ID'])
        else:
            return {'CANCELLED'}

        return {'FINISHED'}
    
class RemoveClothWK(bpy.types.Operator):
    bl_idname = "clp.remove_clothwk"
    bl_label = "Remove ClothWK"
    bl_description = "Remove ClothWK"

    index : bpy.props.IntProperty()

    def execute(self, context):
        cloth_wk = bpy.context.scene.clp_clothwk
        # Remove using index
        cloth_wk.remove(self.index)

        return {'FINISHED'}

def drawCLPWKList(layout):
    row = layout.row()
    row.operator("clp.add_clothwk")

    search_options = bpy.context.scene.clp_search_options
    row = layout.row()
    row.prop(search_options, "filter_by_selected")

    layout.label(text="CLOTH_WK_LIST")

    selected_bones = bpy.context.selected_bones
    selected_bone_ids = []
    if selected_bones:
        for bone in selected_bones:
            if 'ID' in bone:
                selected_bone_ids.append(str(bone['ID']))

    cloth_wk = bpy.context.scene.clp_clothwk
    for index, item in enumerate(cloth_wk):
        if search_options.filter_by_selected:
            if item.no not in selected_bone_ids:
                continue

        box = layout.box()

        # Align label to left and remove button to right
        row = box.row(align=True)
        row.label(text=item.no)
        row.operator("clp.remove_clothwk", text="", icon='X', emboss=False).index = index

        row = box.row()
        row.prop(item, "no")
        row = box.row()
        row.prop(item, "no_up")
        row = box.row()
        row.prop(item, "no_down")
        row = box.row()
        row.prop(item, "no_side")
        row.prop(item, "no_poly")
        row = box.row()
        row.prop(item, "no_fix")
        row = box.row()
        row.prop(item, "offset")
        row = box.row()
        row.prop(item, "rot_limit")
        row.prop(item, "m_original_rate")

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

class UpdateCLPVisualizer(bpy.types.Operator):
    bl_idname = "clp.update_clp_visualizer"
    bl_label = "Update CLP Visualizer"
    bl_description = "Update CLP Visualizer"

    def execute(self, context):
        update_clp_bone_items()

        clpCollection = bpy.data.collections.get("CLP")
        if not clpCollection:
            clpCollection = bpy.data.collections.new("CLP")
            bpy.context.scene.collection.children.link(clpCollection)

        for obj in clpCollection.objects:
            bpy.data.objects.remove(obj)

        gpencil_data = bpy.data.grease_pencils.new("CLP")
        gpencil = bpy.data.objects.new("CLP", gpencil_data)
        gpencil.rotation_euler = mathutils.Euler((math.radians(90), 0, 0), 'XYZ')
        clpCollection.objects.link(gpencil)

        gp_layer = gpencil_data.layers.new("CLP_Lines")
        gp_frame = gp_layer.frames.new(0)

        for clothwk in bpy.context.scene.clp_clothwk:
            bone = get_bone_from_id(clothwk.no)
            bone_down = get_bone_from_id(clothwk.no_down)
            if bone and bone_down and clothwk.no_down != "4095":
                gp_stroke = gp_frame.strokes.new()
                gp_stroke.line_width = 4
                gp_stroke.points.add(2)
                gp_stroke.points[0].co = bone.head_local
                gp_stroke.points[1].co = bone_down.head_local

                if bpy.context.scene.clp_visualization_options.show_rot_limit:
                    mesh = bpy.data.meshes.new(clothwk.no + " rot_limit")
                    obj = bpy.data.objects.new(clothwk.no + " rot_limit", mesh)

                    # Add the object into the scene.
                    clpCollection.objects.link(obj)

                    # Create cone with opening angle equal to rot_limit
                    # r = h * tan(rot_limit)
                    direction = bone_down.head_local - bone.head_local
                    height = direction.length
                    radius = height * math.tan(clothwk.rot_limit)
                    bm = bmesh.new()
                    bmesh.ops.create_cone(bm, cap_ends=False, cap_tris=True, segments=32, radius1=0, radius2=radius, depth=height)
                    # Move all vertices down so that the cone is centered at the origin
                    bmesh.ops.translate(bm, vec=(0, 0, height/2), verts=bm.verts)
                    bm.to_mesh(mesh)
                    bm.free()

                    # Rotate direction 90 degrees around X axis
                    direction.rotate(mathutils.Euler((math.radians(90), 0, 0), 'XYZ'))

                    loc = bone.head_local.copy()
                    loc.rotate(mathutils.Euler((math.radians(90), 0, 0), 'XYZ'))
                    obj.location = loc

                    obj.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
                    # Scale to match bone length
                    obj.scale = (0.5, 0.5, 0.5)

                    # Set viewport display to wireframe
                    obj.display_type = 'WIRE'

            if clothwk.no_side != "4095":
                bone_side = get_bone_from_id(clothwk.no_side)
                if bone and bone_side:
                    gp_stroke = gp_frame.strokes.new()
                    gp_stroke.line_width = 4
                    gp_stroke.points.add(2)
                    gp_stroke.points[0].co = bone.head_local
                    gp_stroke.points[1].co = bone_side.head_local

            if clothwk.no_down != "4095" and clothwk.no_poly != "4095":
                bone_poly = get_bone_from_id(clothwk.no_poly)
                if bone_down and bone_poly:
                    gp_stroke = gp_frame.strokes.new()
                    gp_stroke.line_width = 4
                    gp_stroke.points.add(2)
                    gp_stroke.points[0].co = bone_down.head_local
                    gp_stroke.points[1].co = bone_poly.head_local

        return {'FINISHED'}
    
class ClearCLPVisualizer(bpy.types.Operator):
    bl_idname = "clp.clear_clp_visualizer"
    bl_label = "Clear CLP Visualizer"
    bl_description = "Clear CLP Visualizer"

    def execute(self, context):
        clpCollection = bpy.data.collections.get("CLP")
        if not clpCollection:
            clpCollection = bpy.data.collections.new("CLP")
            bpy.context.scene.collection.children.link(clpCollection)

        for obj in clpCollection.objects:
            bpy.data.objects.remove(obj)

        return {'FINISHED'}

def drawCLPVisualizer(layout):
    row = layout.row()
    viz_options = bpy.context.scene.clp_visualization_options
    row.prop(viz_options, "show_rot_limit", text="Show Rotation Limits")

    row = layout.row()
    row.operator("clp.update_clp_visualizer")

    row = layout.row()
    row.operator("clp.clear_clp_visualizer")

def register():
    bone_items.append((str(4095), "None (4095)", ""))
    bpy.utils.register_class(ClothHeader)
    bpy.utils.register_class(ClothWK)
    bpy.utils.register_class(ClothSearchOptions)
    bpy.utils.register_class(ClothVisualizationOptions)
    bpy.utils.register_class(UpdateBoneItems)
    bpy.utils.register_class(AddClothWK)
    bpy.utils.register_class(RemoveClothWK)
    bpy.utils.register_class(UpdateCLPVisualizer)
    bpy.utils.register_class(ClearCLPVisualizer)

    bpy.types.Scene.clp_clothheader = bpy.props.PointerProperty(type=ClothHeader)
    bpy.types.Scene.clp_clothwk = bpy.props.CollectionProperty(type=ClothWK)
    bpy.types.Scene.clp_search_options = bpy.props.PointerProperty(type=ClothSearchOptions)
    bpy.types.Scene.clp_visualization_options = bpy.props.PointerProperty(type=ClothVisualizationOptions)

def unregister():
    del bpy.types.Scene.clp_clothheader
    del bpy.types.Scene.clp_clothwk
    del bpy.types.Scene.clp_search_options
    del bpy.types.Scene.clp_visualization_options

    bpy.utils.unregister_class(ClothHeader)
    bpy.utils.unregister_class(ClothWK)
    bpy.utils.unregister_class(ClothSearchOptions)
    bpy.utils.unregister_class(ClothVisualizationOptions)
    bpy.utils.unregister_class(UpdateBoneItems)
    bpy.utils.unregister_class(AddClothWK)
    bpy.utils.unregister_class(RemoveClothWK)
    bpy.utils.unregister_class(UpdateCLPVisualizer)
    bpy.utils.unregister_class(ClearCLPVisualizer)