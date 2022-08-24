import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

from ...utils.visibilitySwitcher import enableVisibilitySelector
from ...utils.util import setExportFieldsFromImportFile


class ImportNierWmb(bpy.types.Operator, ImportHelper):
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

        setExportFieldsFromImportFile(self.filepath, False)
        enableVisibilitySelector()

        return wmb_importer.main(False, self.filepath)
