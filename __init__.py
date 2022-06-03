bl_info = {
    "name": "NieR2Blender (NieR:Automata Data Importer)",
    "author": "Woeful_Wolf (Original by C4nf3ng)",
    "version": (3, 0),
    "blender": (2, 80, 0),
    "api": 38019,
    "location": "File > Import",
    "description": "Import Nier:Automata Data",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export"}

import bpy
import os
from bpy_extras.io_utils import ExportHelper,ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty

class ImportNier2blender(bpy.types.Operator, ImportHelper):
    '''Load a Nier:Automata WMB File.'''
    bl_idname = "import_scene.wmb_data"
    bl_label = "Import WMB Data"
    bl_options = {'PRESET'}
    filename_ext = ".wmb"
    filter_glob: StringProperty(default="*.wmb", options={'HIDDEN'})

    reset_blend: bpy.props.BoolProperty(name="Reset Blender Scene on Import", default=True)

    def execute(self, context):
        from . import wmb_importer
        if self.reset_blend:
            wmb_importer.reset_blend()
        return wmb_importer.main(False, self.filepath)

def importDat(only_extract, filepath):
    head = os.path.split(filepath)[0]
    tail = os.path.split(filepath)[1]
    tailless_tail = tail[:-4]
    dat_filepath = head + '\\' + tailless_tail + '.dat'
    extract_dir = head + '\\nier2blender_extracted'
    from . import dat_unpacker
    if os.path.isfile(dat_filepath):
        dat_unpacker.main(dat_filepath, extract_dir + '\\' + tailless_tail + '.dat', dat_filepath)   # dat
    else:
        print('DAT not found. Only extracting DTT. (No materials, collisions or layouts will automatically be imported)')

    last_filename = dat_unpacker.main(filepath, extract_dir + '\\' + tailless_tail + '.dtt', filepath)       # dtt

    wmb_filepath = extract_dir + '\\' + tailless_tail + '.dtt\\' + last_filename[:-4] + '.wmb'
    if not os.path.exists(wmb_filepath):
        wmb_filepath = extract_dir + '\\' + tailless_tail + '.dat\\' + last_filename[:-4] + '.wmb'                     # if not in dtt, then must be in dat

    # WMB
    from . import wmb_importer
    wmb_importer.main(only_extract, wmb_filepath)

    if only_extract:
        return {'FINISHED'}

    # COL
    col_filepath = extract_dir + '\\' + tailless_tail + '.dat\\' + tailless_tail + '.col'
    if os.path.isfile(col_filepath):
        from . import col_importer
        col_importer.main(col_filepath)

    # LAY
    lay_filepath = extract_dir + '\\' + tailless_tail + '.dat\\' + 'Layout.lay'
    if os.path.isfile(lay_filepath):
        from . import lay_importer
        lay_importer.main(lay_filepath, __name__)

    return {'FINISHED'}

class ImportDATNier2blender(bpy.types.Operator, ImportHelper):
    '''Load a Nier:Automata DTT (and DAT) File.'''
    bl_idname = "import_scene.dtt_data"
    bl_label = "Import DTT (and DAT) Data"
    bl_options = {'PRESET'}
    filename_ext = ".dtt"
    filter_glob: StringProperty(default="*.dtt", options={'HIDDEN'})

    reset_blend: bpy.props.BoolProperty(name="Reset Blender Scene on Import", default=True)
    bulk_import: bpy.props.BoolProperty(name="Bulk Import All DTT/DATs In Folder (Experimental)", default=False)
    only_extract: bpy.props.BoolProperty(name="Only Extract DTT/DAT Contents. (Experimental)", default=False)

    def execute(self, context):
        from . import wmb_importer
        if self.reset_blend and not self.only_extract:
            wmb_importer.reset_blend()
        if self.bulk_import:
            folder = os.path.split(self.filepath)[0]
            for filename in os.listdir(folder):
                if filename[-4:] == '.dtt':
                    try:
                        filepath = folder + '\\' + filename
                        importDat(self.only_extract, filepath)
                    except:
                        print('ERROR: FAILED TO IMPORT', filename)
            return {'FINISHED'}

        else:
            return importDat(self.only_extract, self.filepath)

class ImportColNier2Blender(bpy.types.Operator, ImportHelper):
    '''Load a Nier:Automata Col (Collision) File.'''
    bl_idname = "import_scene.col_data"
    bl_label = "Import Col Data"
    bl_options = {'PRESET'}
    filename_ext = ".col"
    filter_glob: StringProperty(default="*.col", options={'HIDDEN'})

    def execute(self, context):
        from . import col_importer
        return col_importer.main(self.filepath)

class ImportLayNier2Blender(bpy.types.Operator, ImportHelper):
    '''Load a Nier:Automata Lay (Layout) File.'''
    bl_idname = "import_scene.lay_data"
    bl_label = "Import Lay Data"
    bl_options = {'PRESET'}
    filename_ext = ".lay"
    filter_glob: StringProperty(default="*.lay", options={'HIDDEN'})

    def execute(self, context):
        from . import lay_importer
        return lay_importer.main(self.filepath, __name__)

class SelectDirectory(bpy.types.Operator, ImportHelper):
    '''Select Directory'''
    bl_idname = "n2b.folder_select"
    bl_label = "Select Directory"
    filename_ext = ""
    dirpath : StringProperty(name = "", description="Choose directory:", subtype='DIR_PATH')

    target : bpy.props.StringProperty(options={'HIDDEN'})

    def execute(self, context):
        directory = os.path.dirname(self.filepath)
        if self.target == "data005":
            context.preferences.addons[__name__].preferences.data005_dir = directory
        elif self.target == "data015":
            context.preferences.addons[__name__].preferences.data015_dir = directory
        else:
            print("Invalid target", self.target)
            return {"CANCELLED"}

        return {'FINISHED'}

class NieR2BlenderPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__
    data005_dir : StringProperty(options={'HIDDEN'})
    data015_dir : StringProperty(options={'HIDDEN'})

    def draw(self, context):
        layout = self.layout
        
        layout.label(text="Assign Directories Below If You Wish To Enable Bounding Box Visualization With Layout Import:")
        box = layout.box()
        box.label(text="Path To Extracted data005.cpk Directory:")
        row = box.row(align=True)
        row.prop(self, "data005_dir", text="")
        row.operator("n2b.folder_select", icon="FILE_FOLDER", text="").target = "data005"

        box.label(text="Path To Extracted data015.cpk Directory:")
        row = box.row(align=True)
        row.prop(self, "data015_dir", text="")
        row.operator("n2b.folder_select", icon="FILE_FOLDER", text="").target = "data015"

class NieR2BlenderCreateObjBBox(bpy.types.Operator):
    """Create Layout Object Bounding Box"""
    bl_idname = "n2b.create_lay_bb"
    bl_label = "Create Layout Object Bounding Box"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from .lay_importer import getModelBoundingBox, createBoundingBoxObject
        for obj in bpy.context.selected_objects:
            boundingBox = getModelBoundingBox(obj.name.split("_")[0], __name__)
            if boundingBox:
                createBoundingBoxObject(obj, obj.name + "-BoundingBox", bpy.data.collections.get("lay_layAssets"), boundingBox)
            else:
                self.report({'WARNING'}, "Couldn't find dtt of " + obj.name)
        return {'FINISHED'}

class N2BLayoutObjectMenu(bpy.types.Menu):
    bl_idname = 'OBJECT_MT_n2blayout'
    bl_label = 'NieR2Blender'
    def draw(self, context):
        self.layout.operator(NieR2BlenderCreateObjBBox.bl_idname, icon="CUBE")

def menu_func_utils(self, context):
    pcoll = preview_collections["main"]
    yorha_icon = pcoll["yorha"]
    self.layout.menu(N2BLayoutObjectMenu.bl_idname, icon_value=yorha_icon.icon_id)

def menu_func_import(self, context):
    pcoll = preview_collections["main"]
    yorha_icon = pcoll["yorha"]
    self.layout.operator(ImportDATNier2blender.bl_idname, text="DTT File for Nier:Automata (.dtt)", icon_value=yorha_icon.icon_id)
    self.layout.operator(ImportNier2blender.bl_idname, text="WMB File for Nier:Automata (.wmb)", icon_value=yorha_icon.icon_id)
    self.layout.operator(ImportColNier2Blender.bl_idname, text="Collision File for Nier:Automata (.col)", icon_value=yorha_icon.icon_id)
    self.layout.operator(ImportLayNier2Blender.bl_idname, text="Layout File for Nier:Automata (.lay)", icon_value=yorha_icon.icon_id)

classes = (
    ImportNier2blender,
    ImportDATNier2blender,
    ImportColNier2Blender,
    ImportLayNier2Blender,
    SelectDirectory,
    NieR2BlenderPreferences,
    NieR2BlenderCreateObjBBox,
    N2BLayoutObjectMenu
)

preview_collections = {}

def register():
    # Custom icons
    import bpy.utils.previews
    pcoll = bpy.utils.previews.new()
    my_icons_dir = os.path.join(os.path.dirname(__file__), "icons")
    pcoll.load("yorha", os.path.join(my_icons_dir, "yorha-filled.png"), 'IMAGE')
    preview_collections["main"] = pcoll

    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.VIEW3D_MT_object.append(menu_func_utils)


def unregister():
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()

    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.VIEW3D_MT_object.remove(menu_func_utils)

if __name__ == '__main__':
    register()
