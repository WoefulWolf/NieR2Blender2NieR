import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper


class ImportNierLay(bpy.types.Operator, ImportHelper):
    '''Load a Nier:Automata Lay (Layout) File.'''
    bl_idname = "import_scene.lay_data"
    bl_label = "Import Lay Data"
    bl_options = {'PRESET'}
    filename_ext = ".lay"
    filter_glob: StringProperty(default="*.lay", options={'HIDDEN'})

    def execute(self, context):
        from . import lay_importer
        return lay_importer.main(self.filepath, __package__)
