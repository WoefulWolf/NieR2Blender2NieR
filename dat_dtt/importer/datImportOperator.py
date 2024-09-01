import os

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

from ...consts import DAT_EXTENSIONS
from ...col.exporter.col_ui_manager import enableCollisionTools
from ...utils.visibilitySwitcher import enableVisibilitySelector
from ...utils.util import setExportFieldsFromImportFile

def importDtt(only_extract, filepath):
    head = os.path.split(filepath)[0]
    tail = os.path.split(filepath)[1]
    tailless_tail = tail[:-4]
    dat_filepath = os.path.join(head, tailless_tail + '.dat')
    extract_dir = os.path.join(head, 'nier2blender_extracted')
    from . import dat_unpacker
    if os.path.isfile(dat_filepath):
        dat_unpacker.main(dat_filepath, os.path.join(extract_dir, tailless_tail + '.dat'), dat_filepath)   # dat
    else:
        print('DAT not found. Only extracting DTT. (No materials, collisions or layouts will automatically be imported)')

    extracted_files = dat_unpacker.main(filepath, os.path.join(extract_dir, tailless_tail + '.dtt'), filepath)       # dtt

    wmb_filepath = os.path.join(extract_dir, tailless_tail + '.dtt', tailless_tail + '.wmb')
    if not os.path.exists(wmb_filepath):
        wmb_filepath = os.path.join(extract_dir, tailless_tail + '.dat', tailless_tail + '.wmb')                     # if not in dtt, then must be in dat

    # WTA/WTP
    wtaPath = os.path.join(extract_dir, tailless_tail + '.dat', tailless_tail + '.wta')
    wtpPath = os.path.join(extract_dir, tailless_tail + '.dtt', tailless_tail + '.wtp')
    if os.path.isfile(wtaPath) and os.path.isfile(wtpPath):
        texturesExtractDir = os.path.join(extract_dir, tailless_tail + '.dtt', "textures")
        from ...wta_wtp.importer import wtpImportOperator
        wtpImportOperator.extractFromWta(wtaPath, wtpPath, texturesExtractDir)

    if only_extract:
        return {'FINISHED'}

    setExportFieldsFromImportFile(filepath, True)
    enableVisibilitySelector()

    # WMB
    from ...wmb.importer import wmb_importer
    wmb_importer.main(only_extract, wmb_filepath)

    # COL
    col_filepath = os.path.join(extract_dir, tailless_tail + '.dat', tailless_tail + '.col')
    if os.path.isfile(col_filepath):
        from ...col.importer import col_importer
        col_importer.main(col_filepath)
        enableCollisionTools()

    # LAY
    lay_filepath = os.path.join(extract_dir, tailless_tail + '.dat', 'Layout.lay')
    if os.path.isfile(lay_filepath):
        from ...lay.importer import lay_importer
        lay_importer.main(lay_filepath)

    return {'FINISHED'}

class ImportNierDtt(bpy.types.Operator, ImportHelper):
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
        from ...wmb.importer import wmb_importer
        if self.reset_blend and not self.only_extract:
            wmb_importer.reset_blend()
        if self.bulk_import:
            folder = os.path.split(self.filepath)[0]
            for filename in os.listdir(folder):
                if filename[-4:] == '.dtt':
                    try:
                        filepath = os.path.join(folder, filename)
                        importDtt(self.only_extract, filepath)
                    except:
                        print('ERROR: FAILED TO IMPORT', filename)
            return {'FINISHED'}

        else:
            return importDtt(self.only_extract, self.filepath)

class ImportNierDat(bpy.types.Operator, ImportHelper):
    '''Load a Nier:Automata DAT File.'''
    bl_idname = "import_scene.dat_data"
    bl_label = "Import DAT Data"
    bl_options = {'PRESET'}
    filename_ext = ".dat"
    filter_glob: StringProperty(default=";".join([f"*{ext}" for ext in DAT_EXTENSIONS]), options={'HIDDEN'})

    reset_blend: bpy.props.BoolProperty(name="Reset Blender Scene on Import", default=True)
    bulk_import: bpy.props.BoolProperty(name="Bulk Import All DTT/DATs In Folder (Experimental)", default=False)
    only_extract: bpy.props.BoolProperty(name="Only Extract DTT/DAT Contents. (Experimental)", default=False)

    def doImport(self, onlyExtract, filepath):
        head = os.path.split(filepath)[0]
        tail = os.path.split(filepath)[1]
        ext = tail[-4:]
        tailless_tail = tail[:-4]
        dat_filepath = os.path.join(head, tailless_tail + ext)
        extract_dir = os.path.join(head, 'nier2blender_extracted')
        from . import dat_unpacker
        if os.path.isfile(dat_filepath):
            dat_unpacker.main(dat_filepath, os.path.join(extract_dir, tailless_tail + ext), dat_filepath)   # dat

        if onlyExtract:
            return {'FINISHED'}

        setExportFieldsFromImportFile(filepath, True)

        # COL
        col_filepath = os.path.join(extract_dir, tailless_tail + '.dat', tailless_tail + '.col')
        if os.path.isfile(col_filepath):
            from ...col.importer import col_importer
            col_importer.main(col_filepath)
            enableCollisionTools()

        # LAY
        lay_filepath = os.path.join(extract_dir, tailless_tail + '.dat', 'Layout.lay')
        if os.path.isfile(lay_filepath):
            from ...lay.importer import lay_importer
            lay_importer.main(lay_filepath)

        return {'FINISHED'}

    def execute(self, context):
        from ...wmb.importer import wmb_importer
        if self.reset_blend and not self.only_extract:
            wmb_importer.reset_blend()
        if self.bulk_import:
            folder = os.path.split(self.filepath)[0]
            for filename in os.listdir(folder):
                if filename[-4:] in DAT_EXTENSIONS:
                    try:
                        filepath = os.path.join(folder, filename)
                        self.doImport(self.only_extract, filepath)
                    except:
                        print('ERROR: FAILED TO IMPORT', filename)
            return {'FINISHED'}

        else:
            return self.doImport(self.only_extract, self.filepath)
