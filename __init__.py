bl_info = {
    "name": "Nier2Blender2NieR (NieR:Automata Data Exporter)",
    "author": "Woeful_Wolf & RaiderB",
    "version": (0, 3, 1),
    "blender": (2, 80, 0),
    "description": "Import/Export NieR:Automata WMB/WTP/WTA/DTT/DAT/COL/LAY files.",
    "category": "Import-Export"}


import bpy
from bpy.app.handlers import persistent
from . import preferences
from .col.exporter import col_ui_manager
from .col.exporter.col_ui_manager import enableCollisionTools, disableCollisionTools
from .dat_dtt.exporter import dat_dtt_ui_manager
from .utils.util import *
from .utils.utilOperators import RecalculateObjectIndices, RemoveUnusedVertexGroups, MergeVertexGroupCopies, \
    DeleteLooseGeometrySelected, DeleteLooseGeometryAll, RipMeshByUVIslands
from .utils.visibilitySwitcher import enableVisibilitySelector, disableVisibilitySelector
from .utils import visibilitySwitcher
from .wta_wtp.exporter import wta_wtp_ui_manager
from .bxm.exporter.gaAreaExportOperator import ExportNierGaArea
from .bxm.exporter.sarExportOperator import ExportNierSar
from .bxm.importer.gaAreaImportOperator import ImportNierGaArea
from .bxm.importer.sarImportOperator import ImportNierSar
from .col.exporter.colExportOperator import ExportNierCol
from .col.importer.colImportOperator import ImportNierCol
from .dat_dtt.importer.datImportOperator import ImportNierDtt, ImportNierDat
from .lay.exporter.layExportOperator import ExportNierLay
from .lay.importer.layImportOperator import ImportNierLay
from .wmb.exporter.wmbExportOperator import ExportNierWmb
from .wmb.importer.wmbImportOperator import ImportNierWmb
from .wta_wtp.importer.wtpImportOperator import ExtractNierWtaWtp
from .xmlScripting.importer.yaxXmlImportOperator import ImportNierYaxXml


class NierObjectMenu(bpy.types.Menu):
    bl_idname = 'OBJECT_MT_n2b2n'
    bl_label = 'NieR Tools'
    def draw(self, context):
        self.layout.operator(RecalculateObjectIndices.bl_idname)
        self.layout.operator(RemoveUnusedVertexGroups.bl_idname)
        self.layout.operator(MergeVertexGroupCopies.bl_idname)
        self.layout.operator(DeleteLooseGeometrySelected.bl_idname)
        self.layout.operator(DeleteLooseGeometryAll.bl_idname)
        self.layout.operator(RipMeshByUVIslands.bl_idname)
        self.layout.operator(CreateLayVisualization.bl_idname, icon="CUBE")

class CreateLayVisualization(bpy.types.Operator):
    """Create Layout Object Visualization"""
    bl_idname = "n2b.create_lay_vis"
    bl_label = "Create Layout Object Visualization"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from .lay.importer.lay_importer import updateVisualizationObject
        for obj in bpy.context.selected_objects:
            if len(obj.name) < 6:
                self.report({"ERROR"}, f"{obj.name} name needs to be at least 6 characters long!")
                return {"CANCELLED"}
            updateVisualizationObject(obj, obj.name[:6], True)
        return {'FINISHED'}

def menu_func_import(self, context):
    pcoll = preview_collections["main"]
    yorha_icon = pcoll["yorha"]
    self.layout.operator(ImportNierDtt.bl_idname, text="DTT File for Nier:Automata (.dtt)", icon_value=yorha_icon.icon_id)
    self.layout.operator(ImportNierWmb.bl_idname, text="WMB File for Nier:Automata (.wmb)", icon_value=yorha_icon.icon_id)
    self.layout.operator(ImportNierDat.bl_idname, text="DAT File for Nier:Automata (col+lay) (.dat)", icon_value=yorha_icon.icon_id)
    self.layout.operator(ImportNierCol.bl_idname, text="Collision File for Nier:Automata (.col)", icon_value=yorha_icon.icon_id)
    self.layout.operator(ImportNierLay.bl_idname, text="Layout File for Nier:Automata (.lay)", icon_value=yorha_icon.icon_id)
    self.layout.operator(ImportNierSar.bl_idname, text="Audio Environment File (.sar)", icon_value=yorha_icon.icon_id)
    self.layout.operator(ImportNierGaArea.bl_idname, text="Visual Environment File (GAArea.bxm)", icon_value=yorha_icon.icon_id)
    self.layout.operator(ImportNierYaxXml.bl_idname, text="YAX XML for Nier:Automata (.xml)", icon_value=yorha_icon.icon_id)
    self.layout.operator(ExtractNierWtaWtp.bl_idname, text="Extract Textures (.wta/.wtp)", icon_value=yorha_icon.icon_id)

def menu_func_export(self, context):
    pcoll = preview_collections["main"]
    emil_icon = pcoll["emil"]
    self.layout.operator_context = 'INVOKE_DEFAULT'
    self.layout.operator(ExportNierWmb.bl_idname, text="WMB File for NieR:Automata (.wmb)", icon_value=emil_icon.icon_id)
    self.layout.operator(ExportNierCol.bl_idname, text="Collision File for NieR:Automata (.col)", icon_value=emil_icon.icon_id)
    self.layout.operator(ExportNierLay.bl_idname, text="Layout File for NieR:Automata (.lay)", icon_value=emil_icon.icon_id)
    self.layout.operator(ExportNierSar.bl_idname, text="Audio Environment File (.sar)", icon_value=emil_icon.icon_id)
    self.layout.operator(ExportNierGaArea.bl_idname, text="Visual Environment File (GAArea.bxm)", icon_value=emil_icon.icon_id)

def menu_func_utils(self, context):
    pcoll = preview_collections["main"]
    yorha_icon = pcoll["yorha"]
    self.layout.menu(NierObjectMenu.bl_idname, icon_value=yorha_icon.icon_id)

classes = (
    ImportNierWmb,
    ImportNierDtt,
    ImportNierDat,
    ImportNierCol,
    ImportNierLay,
    ImportNierSar,
    ImportNierGaArea,
    ImportNierYaxXml,
    ExportNierWmb,
    ExportNierCol,
    ExportNierSar,
    ExportNierLay,
    ExportNierGaArea,
    ExtractNierWtaWtp,
    CreateLayVisualization,
    NierObjectMenu,
    RecalculateObjectIndices,
    RemoveUnusedVertexGroups,
    MergeVertexGroupCopies,
    DeleteLooseGeometrySelected,
    DeleteLooseGeometryAll,
    RipMeshByUVIslands,
)

preview_collections = {}

def register():
    # Custom icons
    import bpy.utils.previews
    pcoll = bpy.utils.previews.new()
    my_icons_dir = os.path.join(os.path.dirname(__file__), "icons")
    pcoll.load("emil", os.path.join(my_icons_dir, "emil.png"), 'IMAGE')
    pcoll.load("yorha", os.path.join(my_icons_dir, "yorha-filled.png"), 'IMAGE')
    preview_collections["main"] = pcoll

    for cls in classes:
        bpy.utils.register_class(cls)

    wta_wtp_ui_manager.register()
    dat_dtt_ui_manager.register()
    preferences.register()
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.VIEW3D_MT_object.append(menu_func_utils)

    bpy.types.Object.collisionType = bpy.props.EnumProperty(name="Collision Type", items=collisionTypes, update=updateCollisionType)
    bpy.types.Object.UNKNOWN_collisionType = bpy.props.IntProperty(name="Unknown Collision Type", min=0, max=255, update=updateCollisionType)
    bpy.types.Object.colModifier = bpy.props.EnumProperty(name="Modifier", items=colModifierTypes)
    bpy.types.Object.surfaceType = bpy.props.EnumProperty(name="Surface Type", items=surfaceTypes)

    bpy.app.handlers.load_post.append(checkCustomPanelsEnableDisable)
    bpy.app.handlers.load_post.append(checkOldVersionMigration)
    bpy.app.handlers.depsgraph_update_post.append(initialCheckCustomPanelsEnableDisable)

def unregister():
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()

    for cls in classes:
        bpy.utils.unregister_class(cls)

    wta_wtp_ui_manager.unregister()
    dat_dtt_ui_manager.unregister()
    col_ui_manager.unregister()
    visibilitySwitcher.unregister()
    preferences.unregister()
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.VIEW3D_MT_object.remove(menu_func_utils)

    bpy.app.handlers.load_post.remove(checkCustomPanelsEnableDisable)
    bpy.app.handlers.load_post.remove(checkOldVersionMigration)
    if initialCheckCustomPanelsEnableDisable in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(initialCheckCustomPanelsEnableDisable)

@persistent
def checkCustomPanelsEnableDisable(_, __):
    if "WMB" in bpy.data.collections:
        enableVisibilitySelector()
    else:
        disableVisibilitySelector()
    if "COL" in bpy.data.collections:
        enableCollisionTools()
    else:
        disableCollisionTools()

def initialCheckCustomPanelsEnableDisable(_, __):
    # during registration bpy.data is not yet available, so wait for first depsgraph update
    if hasattr(bpy.data, "collections"):
        checkCustomPanelsEnableDisable(_, __)
        bpy.app.handlers.depsgraph_update_post.remove(initialCheckCustomPanelsEnableDisable)

@persistent
def checkOldVersionMigration(_, __):
    migrateOldWmbCollection()
    migrateDatDirs()

def migrateOldWmbCollection():
    # check if current file is an old wmb import
    if "hasMigratedToN2B2N" in bpy.context.scene:
        return
    if "WMB" in bpy.data.collections:
        return
    if "boundingBoxUVW" not in bpy.context.scene or "boundingBoxXYZ" not in bpy.context.scene:
        return
    if not any(["LOD_Level" not in obj for obj in bpy.data.objects]):
        return

    # migrate
    # find collection with WMB objects
    oldWmbColl: bpy.types.Collection = None
    for collection in bpy.context.scene.collection.children:
        if not any(["LOD_Level" in obj for obj in collection.all_objects]):
            continue
        oldWmbColl = collection
        break
    if oldWmbColl is None:
        return

    bpy.context.scene.collection.children.unlink(oldWmbColl)
    parentWmbColl = bpy.data.collections.new("WMB")
    bpy.context.scene.collection.children.link(parentWmbColl)
    parentWmbColl.children.link(oldWmbColl)
    
    bpy.context.scene["hasMigratedToN2B2N"] = True

    print("Migrated scene to new version")

def migrateDatDirs():
    dirTypes = [
        {
            "key": "DatDir",
            "newList": bpy.context.scene.DatContents
        },
        {
            "key": "DttDir",
            "newList": bpy.context.scene.DttContents
        }
    ]
    for dirType in dirTypes:
        if dirType["key"] not in bpy.context.scene or len(dirType["newList"]) > 0:
            continue
        datDir = bpy.context.scene[dirType["key"]]
        if os.path.isdir(datDir):
            if not importContentsFileFromFolder(datDir, dirType["newList"]):
                print("No dat_info.json or file_order.metadata found in " + datDir)

## Collision Extras
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

colModifierTypes = [
    ("0", "", ""),
    ("1", "Slidable", ""),
    ("2", "Transparent wall", ""),
    ("8", "Unknown (8)", ""),
    ("32", "Unknown (32)", ""),
    ("129", "Unknown (129)", ""),
]

if __name__ == '__main__':
    register()