import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

from ...utils.visibilitySwitcher import enableVisibilitySelector
from ...utils.util import setExportFieldsFromImportFile


class ImportSCR(bpy.types.Operator, ImportHelper):
    '''Load a MGR SCR File.'''
    bl_idname = "import_scene.scr_data"
    bl_label = "Import SCR Data"
    bl_options = {'PRESET'}
    filename_ext = ".scr"
    filter_glob: StringProperty(default="*.scr", options={'HIDDEN'})

    reset_blend: bpy.props.BoolProperty(name="Reset Blender Scene on Import", default=True)

    def execute(self, context):
        from . import scr_importer
        if self.reset_blend:
            scr_importer.reset_blend()

        setExportFieldsFromImportFile(self.filepath, False)
        enableVisibilitySelector()

        return scr_importer.ImportSCR.main(self.filepath, False)
