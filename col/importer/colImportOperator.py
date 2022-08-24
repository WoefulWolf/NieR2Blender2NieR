import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

from ..exporter.col_ui_manager import enableCollisionTools
from ...utils.util import setExportFieldsFromImportFile


class ImportNierCol(bpy.types.Operator, ImportHelper):
    '''Load a Nier:Automata Col (Collision) File.'''
    bl_idname = "import_scene.col_data"
    bl_label = "Import Col Data"
    bl_options = {'PRESET'}
    filename_ext = ".col"
    filter_glob: StringProperty(default="*.col", options={'HIDDEN'})

    def execute(self, context):
        from . import col_importer

        setExportFieldsFromImportFile(self.filepath, False)
        enableCollisionTools()

        return col_importer.main(self.filepath)
