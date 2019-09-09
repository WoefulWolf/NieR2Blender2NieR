bl_info = {
    "name": "Nier: Automata Model Importer",
    "author": "C4nf3ng (2.80 by Woeful_Wolf)",
    "version": (1, 1),
    "blender": (2, 80, 0),
    "api": 38019,
    "location": "File > Import-Export",
    "description": "Import Nier:Automata Model Data",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export"}

#just for Break

import bpy
import os
from bpy_extras.io_utils import ExportHelper,ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty

class ImportNier2blender(bpy.types.Operator, ImportHelper):
    '''Load a Nier:Automata WMB File.'''
    bl_idname = "import.wmb_data"
    bl_label = "Import WMB Data"
    bl_options = {'PRESET'}
    filename_ext = ".wmb"
    filter_glob: StringProperty(default="*.wmb", options={'HIDDEN'})

    def execute(self, context):
        from nier2blender_2_80 import wmb_importer
        return wmb_importer.main(self.filepath)

class ImportDATNier2blender(bpy.types.Operator, ImportHelper):
    '''Load a Nier:Automata DTT (and DAT) File.'''
    bl_idname = "import.dtt_data"
    bl_label = "Import DTT (and DAT) Data"
    bl_options = {'PRESET'}
    filename_ext = ".dtt"
    filter_glob: StringProperty(default="*.dtt", options={'HIDDEN'})

    def execute(self, context):
        head = os.path.split(self.filepath)[0]
        tail = os.path.split(self.filepath)[1]
        tailless_tail = tail[:-4]
        dat_filepath = head + '\\' + tailless_tail + '.dat'
        extract_dir = head + '\\nier2blender_extracted'
        from nier2blender_2_80 import dat_unpacker
        if os.path.isfile(dat_filepath):
            dat_unpacker.main(dat_filepath, extract_dir + '\\' + tailless_tail + '.dat', dat_filepath)   # dat
        else:
            print('DAT not found. Only extracting DTT. (No materials will automatically be imported)')

        wtp_filename = dat_unpacker.main(self.filepath, extract_dir + '\\' + tailless_tail + '.dtt', self.filepath)       # dtt

        print(wtp_filename)
        wmb_filepath = extract_dir + '\\' + tailless_tail + '.dtt\\' + wtp_filename[:-4] + '.wmb'
        print(self.filepath)
        print(dat_filepath)
        print(wmb_filepath)
        from nier2blender_2_80 import wmb_importer
        return wmb_importer.main(wmb_filepath)

# Registration

def menu_func_import(self, context):
    self.layout.operator(ImportNier2blender.bl_idname, text="WMB File for Nier:Automata (.wmb)")

def menu_func_import_dat(self, context):
    self.layout.operator(ImportDATNier2blender.bl_idname, text="DTT File for Nier:Automata (.dtt)")

def register():
    bpy.utils.register_class(ImportNier2blender)
    bpy.utils.register_class(ImportDATNier2blender)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_dat)

def unregister():
    bpy.utils.unregister_class(ImportNier2blender)
    bpy.utils.unregister_class(ImportDATNier2blender)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_dat)


if __name__ == '__main__':
    register()