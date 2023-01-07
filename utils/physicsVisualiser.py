import bpy, os, math, mathutils
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper, ImportHelper

import xml.etree.ElementTree as ET

class SelectXMLFile(bpy.types.Operator, ImportHelper):
    '''Select Physics XML'''
    bl_idname = "na.select_physics_xml_file"
    bl_label = "Select XML File"
    bl_options = {"UNDO"}
    filter_glob: StringProperty(default="*.xml", options={'HIDDEN'})

    type: bpy.props.StringProperty(options={'HIDDEN'})

    def execute(self, context):
        filepath = self.filepath
        # Check if valid selection:
        if not os.path.exists(filepath):
            self.report({'ERROR'}, "Selection does not exist.")
            return {'CANCELLED'}

        if self.type == "clp":
            context.scene.ClothPhysicsFilepath = filepath
        elif self.type == "clh":
            context.scene.ClothHitboxesFilepath = filepath

        return {"FINISHED"}

def getBoneFromID(boneID, armature):
    for bone in armature.bones:
        if boneID == bone['ID']:
            return bone
    return None

class B2NUpdateCLPVisualization(bpy.types.Operator):
    '''Update Cloth Physics Visualization'''
    bl_idname = "na.update_clp_visualization"
    bl_label = "Update Cloth Physics Visualization"
    bl_options = {"UNDO"}

    def execute(self, context):
        # Get file path:
        filepath = context.scene.ClothPhysicsFilepath
        if not os.path.exists(filepath):
            self.report({'ERROR'}, "Please select a file.")
            return {'CANCELLED'}

        # Open file:
        tree = ET.parse(filepath)
        root = tree.getroot()

        for clothBone in root.iter('CLOTH_WK'):
            no = int(clothBone.find('no').text)
            noUp = int(clothBone.find('noUp').text)
            noDown = int(clothBone.find('noDown').text)
            noSide = int(clothBone.find('noSide').text)
            noPoly = int(clothBone.find('noPoly').text)

        return {"FINISHED"}

class B2NUpdateCLHVisualization(bpy.types.Operator):
    '''Update Cloth Hitboxes Visualization'''
    bl_idname = "na.update_clh_visualization"
    bl_label = "Update Cloth Hitboxes Visualization"
    bl_options = {"UNDO"}

    def execute(self, context):
        # Get file path:
        filepath = context.scene.ClothHitboxesFilepath
        if not os.path.exists(filepath):
            self.report({'ERROR'}, "Please select a file.")
            return {'CANCELLED'}

        clhCollection = bpy.data.collections.get("CLH")
        if not clhCollection:
            clhCollection = bpy.data.collections.new("CLH")
            bpy.context.scene.collection.children.link(clhCollection)

        for obj in clhCollection.objects:
            bpy.data.objects.remove(obj)

        # Open file:
        tree = ET.parse(filepath)
        root = tree.getroot()

        for hitbox in root.iter('CLOTH_AT_WK'):
            p1 = int(hitbox.find('p1').text)
            p2 = int(hitbox.find('p2').text)
            weight = float(hitbox.find('weight').text)
            radius = float(hitbox.find('radius').text)
            # Offsets are vectors so we need to split and convert each item to float:
            offset1 = hitbox.find('offset1').text.split(' ')
            offset1 = [float(i) for i in offset1]

            offset2 = hitbox.find('offset2').text.split(' ')
            offset2 = [float(i) for i in offset2]

            capsule = int(hitbox.find('capsule').text)

            # Get bones related to p1 and p2:
            armatureObj = None
            for obj in bpy.data.collections['WMB'].all_objects:
                if obj.type == 'ARMATURE':
                    armatureObj = obj
                    break

            if not armatureObj:
                self.report({'ERROR'}, "No armature found.")
                return {'CANCELLED'}

            bone1 = getBoneFromID(p1, armatureObj.data)
            bone2 = getBoneFromID(p2, armatureObj.data)

            if not bone1 or not bone2:
                print("No bone found hitbox.")
                self.report({'ERROR'}, "No bone found hitbox.")
                continue

            pos1 = bone1.head_local + mathutils.Vector(offset1)
            pos1.resize_4d()
            pos2 = bone2.head_local + mathutils.Vector(offset2)
            pos2.resize_4d()

            # Get direction:
            direction = pos2 - pos1

            if bone1 != bone2:
                # Create curve:
                curveData = bpy.data.curves.new('CLH_{}_{}_[{}]'.format(p1, p2, weight), type='CURVE')
                curveData.use_path = False
                curveData.dimensions = '3D'
                curveData.resolution_u = 1
                curveData.bevel_depth = radius
                if capsule == 0:
                    curveData.bevel_resolution = 0
                    pos1 -= direction.normalized() * radius
                    pos2 += direction.normalized() * radius
                    curveData.use_fill_caps = True
                
                # Create spline
                polyline = curveData.splines.new('POLY')
                polyline.points.add(1)
                polyline.points[0].co = pos1
                polyline.points[1].co = pos2

                # Create object and link to collection:
                curveObj = bpy.data.objects.new('CLH_{}_{}_[{}]'.format(p1, p2, weight), curveData)
                curveObj.display_type = 'WIRE'
                clhCollection.objects.link(curveObj)
                curveObj.show_name = True
                # Rotate 90 degrees on X axis:
                curveObj.rotation_euler = mathutils.Euler((math.radians(90), 0, 0), 'XYZ')

                if capsule == 1:
                    rot = (direction.xyz).to_track_quat('Z', 'Y').to_euler()

                    # Add empty objects at the end of the curve:
                    capsuleCap1Obj = bpy.data.objects.new('CLH_{}_{}_cap1'.format(p1, p2), None)
                    capsuleCap1Obj.empty_display_type = 'SPHERE'
                    capsuleCap1Obj.empty_display_size = radius
                    capsuleCap1Obj.location = pos1.xyz
                    capsuleCap1Obj.parent = curveObj
                    capsuleCap1Obj.rotation_euler = rot
                    clhCollection.objects.link(capsuleCap1Obj)

                    capsuleCap2Obj = bpy.data.objects.new('CLH_{}_{}_cap2'.format(p1, p2), None)
                    capsuleCap2Obj.empty_display_type = 'SPHERE'
                    capsuleCap2Obj.empty_display_size = radius
                    capsuleCap2Obj.location = pos2.xyz
                    capsuleCap2Obj.parent = curveObj
                    capsuleCap2Obj.rotation_euler = rot
                    clhCollection.objects.link(capsuleCap2Obj)

                bpy.ops.object.origin_set(
                    {"object" : curveObj,
                    "selected_objects" : [curveObj],
                    "selected_editable_objects" : [curveObj],
                    },
                    type='ORIGIN_GEOMETRY'
                )
                    
            else:
                if capsule == 1:
                    # Create empty sphere object:
                    emptyObj = bpy.data.objects.new('CLH_{}_{}_[{}]'.format(p1, p2, weight), None)
                    emptyObj.empty_display_type = 'SPHERE'
                    emptyObj.empty_display_size = radius
                    emptyObj.location = (pos1[0], -pos1[2], pos1[1])
                    emptyObj.show_name = True
                    clhCollection.objects.link(emptyObj)
                else:
                    # Create empty cylinder object:
                    emptyObj = bpy.data.objects.new('CLH_{}_{}_[{}]'.format(p1, p2, weight), None)
                    emptyObj.empty_display_type = 'CUBE'
                    emptyObj.empty_display_size = radius
                    emptyObj.location = (pos1[0], -pos1[2], pos1[1])
                    emptyObj.show_name = True
                    clhCollection.objects.link(emptyObj)

        return {"FINISHED"}


class B2NPhysicsToolsPanel(bpy.types.Panel):
    bl_label = "Physics Tools"
    bl_idname = "B2N_PT_PHYSICS_TOOLS"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "NA: Physics Tools"

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.label(text="Cloth Physics: NOT IMPLEMENTED")
        row = layout.row(align=True)
        row.prop(context.scene, "ClothPhysicsFilepath", text="")
        row.operator("na.select_physics_xml_file", text="", icon="FILE").type = "clp"
        row = layout.row()
        row.operator("na.update_clp_visualization", text="Update Visualization")

        row = layout.row()
        row.label(text="Cloth Hitboxes:")
        row = layout.row(align=True)
        row.prop(context.scene, "ClothHitboxesFilepath", text="")
        row.operator("na.select_physics_xml_file", text="", icon="FILE").type = "clh"
        row = layout.row()
        row.operator("na.update_clh_visualization", text="Update Visualization")

def register():
    bpy.utils.register_class(SelectXMLFile)
    bpy.utils.register_class(B2NPhysicsToolsPanel)

    bpy.utils.register_class(B2NUpdateCLPVisualization)
    bpy.utils.register_class(B2NUpdateCLHVisualization)

    bpy.types.Scene.ClothPhysicsFilepath = bpy.props.StringProperty(
        name = "Cloth Physics XML Filepath (CLP)",
        description = "Cloth Physics XML Filepath (CLP)"
    )

    bpy.types.Scene.ClothHitboxesFilepath = bpy.props.StringProperty(
        name = "Cloth Hitboxes XML Filepath (CLH)",
        description = "Cloth Hitboxes XML Filepath (CLH)"
    )

def unregister():
    bpy.utils.unregister_class(SelectXMLFile)
    bpy.utils.unregister_class(B2NPhysicsToolsPanel)

    bpy.utils.unregister_class(B2NUpdateCLPVisualization)
    bpy.utils.unregister_class(B2NUpdateCLHVisualization)

    del bpy.types.Scene.ClothPhysicsFilepath
    del bpy.types.Scene.ClothHitboxesFilepath
