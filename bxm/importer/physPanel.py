import os, bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper, ImportHelper

from . import clpImporter
from . import clhImporter

class OpenBXMFile(bpy.types.Operator, ImportHelper):
    '''Open Physics BXM File'''
    bl_idname = "na.open_physics_bxm_file"
    bl_label = "Open BXM File"
    bl_options = {"UNDO"}
    filter_glob: StringProperty(default="*.bxm", options={'HIDDEN'})

    type: bpy.props.StringProperty(options={'HIDDEN'})

    def execute(self, context):
        filepath = self.filepath
        # Check if valid selection:
        if not os.path.exists(filepath):
            self.report({'ERROR'}, "Selection does not exist.")
            return {'CANCELLED'}
        
        if self.type == "clp":
            clpImporter.importCLP(filepath)
        elif self.type == "clh":
            clhImporter.importCLH(filepath)

        return {"FINISHED"}
    
class SaveBXMFile(bpy.types.Operator, ExportHelper):
    '''Save Physics BXM File'''
    bl_idname = "na.save_physics_bxm_file"
    bl_label = "Save BXM File"
    bl_options = {"UNDO"}
    filename_ext = ".bxm"
    filter_glob: StringProperty(default="*.bxm", options={'HIDDEN'})

    type: bpy.props.StringProperty(options={'HIDDEN'})

    def execute(self, context):
        filepath = self.filepath
        
        if self.type == "clp":
            clpImporter.exportCLP(filepath)
        elif self.type == "clh":
            clhImporter.exportCLH(filepath)

        return {"FINISHED"}

class B2NPhysicsEditor(bpy.types.Panel):
    bl_label = "NieR:Automata Physics Editor"
    bl_idname = "B2N_PT_PhysicsEditorToplevel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "NA: Physics Editor"

    def draw(self, context):
        return
    
# CLP
class B2NCLPEditor(bpy.types.Panel):
    bl_label = "CLP Editor"
    bl_idname = "B2N_PT_CLPEditor"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = B2NPhysicsEditor.bl_idname
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator("clp.update_bone_items", text="Update Bones List")

        row = layout.row()
        row.operator("na.open_physics_bxm_file", text="Open CLP BXM File").type = "clp"

        row = layout.row()
        row.operator("na.save_physics_bxm_file", text="Save CLP BXM File").type = "clp"
        return
    
class B2NCLPHeader(bpy.types.Panel):
    bl_label = "CLP Header"
    bl_idname = "B2N_PT_CLPHeader"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = B2NCLPEditor.bl_idname

    def draw(self, context):
        layout = self.layout
        clpImporter.drawCLPHeader(layout)
        return
    
class B2NCLPList(bpy.types.Panel):
    bl_label = "CLP List"
    bl_idname = "B2N_PT_CLPList"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = B2NCLPEditor.bl_idname

    def draw(self, context):
        layout = self.layout
        clpImporter.drawCLPWKList(layout)
        return
    
class B2NCLPVisualizer(bpy.types.Panel):
    bl_label = "CLP Visualizer"
    bl_idname = "B2N_PT_CLPVisualizer"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = B2NCLPEditor.bl_idname

    def draw(self, context):
        layout = self.layout
        clpImporter.drawCLPVisualizer(layout)
        return
    
# CLH
class B2NCLHEditor(bpy.types.Panel):
    bl_label = "CLH Editor"
    bl_idname = "B2N_PT_CLHEditor"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = B2NPhysicsEditor.bl_idname
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator("clh.update_bone_items", text="Update Bones List")

        row = layout.row()
        row.operator("na.open_physics_bxm_file", text="Open CLH BXM File").type = "clh"

        row = layout.row()
        row.operator("na.save_physics_bxm_file", text="Save CLH BXM File").type = "clh"
        return
    
class B2NCLHList(bpy.types.Panel):
    bl_label = "CLH List"
    bl_idname = "B2N_PT_CLHList"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = B2NCLHEditor.bl_idname

    def draw(self, context):
        layout = self.layout
        clhImporter.drawCLHWKList(layout)
        return

class B2NCLHVisualizer(bpy.types.Panel):
    bl_label = "CLH Visualizer"
    bl_idname = "B2N_PT_CLHVisualizer"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = B2NCLHEditor.bl_idname

    def draw(self, context):
        layout = self.layout
        clhImporter.drawCLHVisualizer(layout)
        return
    
def register():
    bpy.utils.register_class(B2NPhysicsEditor)

    bpy.utils.register_class(B2NCLPEditor)
    bpy.utils.register_class(B2NCLPHeader)
    bpy.utils.register_class(B2NCLPList)
    bpy.utils.register_class(B2NCLPVisualizer)

    bpy.utils.register_class(B2NCLHEditor)
    bpy.utils.register_class(B2NCLHList)
    bpy.utils.register_class(B2NCLHVisualizer)

    bpy.utils.register_class(OpenBXMFile)
    bpy.utils.register_class(SaveBXMFile)

    clpImporter.register()
    clhImporter.register()
    
def unregister():
    bpy.utils.unregister_class(B2NPhysicsEditor)

    bpy.utils.unregister_class(B2NCLPEditor)
    bpy.utils.unregister_class(B2NCLPHeader)
    bpy.utils.unregister_class(B2NCLPList)
    bpy.utils.unregister_class(B2NCLPVisualizer)

    bpy.utils.unregister_class(B2NCLHEditor)
    bpy.utils.unregister_class(B2NCLHList)
    bpy.utils.unregister_class(B2NCLHVisualizer)

    bpy.utils.unregister_class(OpenBXMFile)
    bpy.utils.unregister_class(SaveBXMFile)

    clpImporter.unregister()
    clhImporter.unregister()