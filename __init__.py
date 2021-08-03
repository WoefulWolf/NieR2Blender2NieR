bl_info = {
    "name": "Blender2NieR (NieR:Automata Model Exporter)",
    "author": "Woeful_Wolf",
    "version": (0, 2, 1),
    "blender": (2, 80, 0),
    "location": "File > Export",
    "description": "Export NieR:Automata WMB/WTP/WTA/DTT/DAT files.",
    "category": "Import-Export"}

import traceback
import sys
import bpy
from bpy_extras.io_utils import ExportHelper,ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty

from . import util
from .wta_wtp_exporter import wta_wtp_ui_manager
from .dat_dtt_exporter import dat_dtt_ui_manager

class ExportBlender2Nier(bpy.types.Operator, ExportHelper):
    '''Export a NieR:Automata WMB File'''
    bl_idname = "export.wmb_data"
    bl_label = "Export WMB File"
    bl_options = {'PRESET'}
    filename_ext = ".wmb"
    filter_glob: StringProperty(default="*.wmb", options={'HIDDEN'})

    centre_origins: bpy.props.BoolProperty(name="Centre Origins", description="This automatically centres the origins of all your objects. (Recommended)", default=True)
    purge_materials: bpy.props.BoolProperty(name="Purge Materials", description="This permanently removes all unused materials from the .blend file before exporting. Enable if you have invalid materials remaining in your project", default=False)
    triangluate_meshes: bpy.props.BoolProperty(name="Triangulate Meshes", description="This automatically adds and applies the Triangulate Modifier on all your objects. Only disable if you know your meshes are triangulated and you wish to reduce export times", default=True)
    delete_loose_geometry: bpy.props.BoolProperty(name="Delete Loose Geometry", description="This automatically runs the Blender2NieR 'Delete Loose Geometry (All)' operator before exporting. It deletes all loose vertices or edges that could result in unwanted results in-game", default=True)

    def execute(self, context):
        from . import wmb_exporter
        from . import util
        
        bpy.data.objects[0].select_set(True)

        if self.centre_origins:
            print("Centering origins...")
            wmb_exporter.centre_origins()

        if self.purge_materials:
            print("Purging materials...")
            wmb_exporter.purge_unused_materials()

        if self.triangluate_meshes:
            print("Triangulating meshes...")
            wmb_exporter.triangulate_meshes() 

        if self.delete_loose_geometry:
            print("Deleting loose geometry...")
            bpy.ops.b2n.deleteloosegeometryall()
        
        try:
            print("Starting export...")
            wmb_exporter.main(self.filepath)
            return wmb_exporter.restore_blend()
        except:
            print(traceback.format_exc())
            util.show_message('Error: An unexpected error has occurred during export. Please check the console for more info.', 'WMB Export Error', 'ERROR')
            return {'CANCELLED'}

class B2NObjectMenu(bpy.types.Menu):
    bl_idname = 'OBJECT_MT_b2n'
    bl_label = 'Blender2NieR'
    def draw(self, context):
        self.layout.operator(util.B2NRecalculateObjectIndices.bl_idname)
        self.layout.operator(util.B2NRemoveUnusedVertexGroups.bl_idname)
        self.layout.operator(util.B2NMergeVertexGroupCopies.bl_idname)
        self.layout.operator(util.B2NDeleteLooseGeometrySelected.bl_idname)
        self.layout.operator(util.B2NDeleteLooseGeometryAll.bl_idname)
        self.layout.operator(util.B2NRipMeshByUVIslands.bl_idname)

def menu_func_export(self, context):
    self.layout.operator_context = 'INVOKE_DEFAULT'
    self.layout.operator(ExportBlender2Nier.bl_idname, text="WMB File for NieR:Automata (.wmb)")

def menu_func_utils(self, context):
    self.layout.menu(B2NObjectMenu.bl_idname)

def register():
    bpy.utils.register_class(ExportBlender2Nier)
    bpy.utils.register_class(B2NObjectMenu)
    bpy.utils.register_class(util.B2NRecalculateObjectIndices)
    bpy.utils.register_class(util.B2NRemoveUnusedVertexGroups)
    bpy.utils.register_class(util.B2NMergeVertexGroupCopies)
    bpy.utils.register_class(util.B2NDeleteLooseGeometrySelected)
    bpy.utils.register_class(util.B2NDeleteLooseGeometryAll)
    bpy.utils.register_class(util.B2NRipMeshByUVIslands)
    wta_wtp_ui_manager.register()
    dat_dtt_ui_manager.register()
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.VIEW3D_MT_object.append(menu_func_utils)


def unregister():
    bpy.utils.unregister_class(ExportBlender2Nier)
    bpy.utils.unregister_class(B2NObjectMenu)
    bpy.utils.unregister_class(util.B2NRecalculateObjectIndices)
    bpy.utils.unregister_class(util.B2NRemoveUnusedVertexGroups)
    bpy.utils.unregister_class(util.B2NMergeVertexGroupCopies)
    bpy.utils.unregister_class(util.B2NDeleteLooseGeometrySelected)
    bpy.utils.unregister_class(util.B2NDeleteLooseGeometryAll)
    bpy.utils.unregister_class(util.B2NRipMeshByUVIslands)
    wta_wtp_ui_manager.unregister()
    dat_dtt_ui_manager.unregister()
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.VIEW3D_MT_object.remove(menu_func_utils)


if __name__ == '__main__':
    register()