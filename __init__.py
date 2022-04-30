bl_info = {
    "name": "Blender2NieR (NieR:Automata Data Exporter)",
    "author": "Woeful_Wolf",
    "version": (0, 3, 0),
    "blender": (2, 80, 0),
    "location": "File > Export",
    "description": "Export NieR:Automata WMB/WTP/WTA/DTT/DAT/COL files.",
    "category": "Import-Export"}

import traceback
import sys
import bpy, os
from bpy_extras.io_utils import ExportHelper,ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty

from . import util
from .wta_wtp_exporter import wta_wtp_ui_manager
from .dat_dtt_exporter import dat_dtt_ui_manager
from .col import col_ui_manager

class ExportBlender2NieRLay(bpy.types.Operator, ExportHelper):
    '''Export a NieR:Automata LAY File'''
    bl_idname = "export.lay_data"
    bl_label = "Export LAY File"
    bl_options = {'PRESET'}
    filename_ext = ".lay"
    filter_glob: StringProperty(default="*.lay", options={'HIDDEN'})

    def execute(self, context):
        from .lay import lay_exporter

        lay_exporter.main(self.filepath)
        return {'FINISHED'}

class ExportBlender2NieRCol(bpy.types.Operator, ExportHelper):
    '''Export a NieR:Automata COL File'''
    bl_idname = "export.col_data"
    bl_label = "Export COL File"
    bl_options = {'PRESET'}
    filename_ext = ".col"
    filter_glob: StringProperty(default="*.col", options={'HIDDEN'})

    generateColTree: bpy.props.BoolProperty(name="Generate Collision Tree", description="This automatically generates colTreeNodes based on your geometry and assignes the right meshes to the right colTreeNodes. Only disable it if you are manually adjusting them", default=True)
    centre_origins: bpy.props.BoolProperty(name="Centre Origins", description="This automatically centres the origins of all your objects. (Recommended)", default=True)
    triangluate_meshes: bpy.props.BoolProperty(name="Triangulate Meshes", description="This automatically adds and applies the Triangulate Modifier on all your objects. (Slow)", default=True)

    def execute(self, context):
        from .col import col_exporter

        if self.centre_origins:
            print("Centering origins...")
            col_exporter.centre_origins()

        if self.triangluate_meshes:
            print("Triangulating meshes...")
            col_exporter.triangulate_meshes() 

        col_exporter.main(self.filepath, self.generateColTree)
        return {'FINISHED'}

class ExportBlender2NieR(bpy.types.Operator, ExportHelper):
    '''Export a NieR:Automata WMB File'''
    bl_idname = "export.wmb_data"
    bl_label = "Export WMB File"
    bl_options = {'PRESET'}
    filename_ext = ".wmb"
    filter_glob: StringProperty(default="*.wmb", options={'HIDDEN'})

    centre_origins: bpy.props.BoolProperty(name="Centre Origins", description="This automatically centres the origins of all your objects. (Recommended)", default=True)
    #purge_materials: bpy.props.BoolProperty(name="Purge Materials", description="This permanently removes all unused materials from the .blend file before exporting. Enable if you have invalid materials remaining in your project", default=False)
    triangluate_meshes: bpy.props.BoolProperty(name="Triangulate Meshes", description="This automatically adds and applies the Triangulate Modifier on all your objects. Only disable if you know your meshes are triangulated and you wish to reduce export times", default=True)
    delete_loose_geometry: bpy.props.BoolProperty(name="Delete Loose Geometry", description="This automatically runs the Blender2NieR 'Delete Loose Geometry (All)' operator before exporting. It deletes all loose vertices or edges that could result in unwanted results in-game", default=True)

    def execute(self, context):
        from .wmb import wmb_exporter
        from . import util
        
        bpy.data.collections['WMB'].all_objects[0].select_set(True)

        if self.centre_origins:
            print("Centering origins...")
            wmb_exporter.centre_origins()

        """
        if self.purge_materials:
            print("Purging materials...")
            wmb_exporter.purge_unused_materials()
        """

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
    pcoll = preview_collections["main"]
    emil_icon = pcoll["emil"]
    self.layout.operator_context = 'INVOKE_DEFAULT'
    self.layout.operator(ExportBlender2NieR.bl_idname, text="WMB File for NieR:Automata (.wmb)", icon_value=emil_icon.icon_id)
    self.layout.operator(ExportBlender2NieRCol.bl_idname, text="Collision File for NieR:Automata (.col)", icon_value=emil_icon.icon_id)
    self.layout.operator(ExportBlender2NieRLay.bl_idname, text="Layout File for NieR:Automata (.lay)", icon_value=emil_icon.icon_id)

def menu_func_utils(self, context):
    self.layout.menu(B2NObjectMenu.bl_idname)

classes = (
    ExportBlender2NieR,
    ExportBlender2NieRCol,
    ExportBlender2NieRLay,
    B2NObjectMenu,
    util.B2NRecalculateObjectIndices,
    util.B2NRemoveUnusedVertexGroups,
    util.B2NMergeVertexGroupCopies,
    util.B2NDeleteLooseGeometrySelected,
    util.B2NDeleteLooseGeometryAll,
    util.B2NRipMeshByUVIslands,
)

preview_collections = {}


def register():
    # Custom icons
    import bpy.utils.previews
    pcoll = bpy.utils.previews.new()
    my_icons_dir = os.path.join(os.path.dirname(__file__), "icons")
    pcoll.load("emil", os.path.join(my_icons_dir, "emil.png"), 'IMAGE')
    preview_collections["main"] = pcoll

    for cls in classes:
        bpy.utils.register_class(cls)

    wta_wtp_ui_manager.register()
    dat_dtt_ui_manager.register()
    col_ui_manager.register()
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.VIEW3D_MT_object.append(menu_func_utils)

    bpy.types.Object.collisionType = bpy.props.EnumProperty(name="Collision Type", items=collisionTypes, update=updateCollisionType)
    bpy.types.Object.UNKNOWN_collisionType = bpy.props.IntProperty(name="Unknown Collision Type", min=0, max=255, update=updateCollisionType)
    bpy.types.Object.slidable = bpy.props.BoolProperty(name="Slidable/Modifier")
    bpy.types.Object.surfaceType = bpy.props.EnumProperty(name="Surface Type", items=surfaceTypes)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    wta_wtp_ui_manager.unregister()
    dat_dtt_ui_manager.unregister()
    col_ui_manager.unregister()
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.VIEW3D_MT_object.remove(menu_func_utils)

if __name__ == '__main__':
    register()


## Extras
def setColourByCollisionType(obj):
    opacity = 1.0
    collisionType = int(obj.collisionType)
    if collisionType == 127:
        obj.color = [0.0, 1.0, 0.0, opacity]
    elif collisionType == 88:
        obj.color = [0.0, 0.5, 1.0, opacity]
    elif collisionType == 3:
        obj.color = [1.0, 0.5, 0.0, opacity]
    elif collisionType == 255:
        obj.color = [1.0, 0.0, 0.0, opacity]
    else:
        obj.color = [1.0, 0.45, 1.0, opacity]

def updateCollisionType(self, context):
    setColourByCollisionType(self)

collisionTypes = [
    ("-1", "UNKNOWN", ""),
    ("3", "Block Actors", "If modifier is enabled, this will not block players who are jumping (e.g. to prevent accidentally walking off ledges)."),
    ("88", "Water", ""),
    ("127", "Grabbable Block All", ""),
    ("255", "Block All", "")
]

# Identified by NSA Cloud
surfaceTypes = [
    ("-1", "UNKNOWN", ""),
    ("0", "Concrete1", ""),
    ("1", "Dirt", ""),
    ("2", "Concrete2", ""),
    ("3", "Metal Floor", ""),
    ("4", "Rubble", ""),
    ("5", "Metal Grate", ""),
    ("6", "Gravel", ""),
    ("7", "Rope Bridge", ""),
    ("8", "Grass", ""),
    ("9", "Wood Plank", ""),
    ("11", "Water", ""),
    ("12", "Sand", ""),
    ("13", "Rocky Gravel 1", ""),
    ("15", "Mud", ""),
    ("16", "Rocky Gravel 2", ""),
    ("17", "Concrete 3", ""),
    ("18", "Bunker Floor", ""),
    ("22", "Concrete 4", ""),
    ("23", "Car", ""),
    ("24", "Flowers", "")
]