import bpy
from bpy_extras.io_utils import ImportHelper


class ImportNierGaArea(bpy.types.Operator, ImportHelper):
    '''Load a Nier:Automata Ga Area File.'''
    bl_idname = "import_scene.ga_area"
    bl_label = "Import GAArea.bxm"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".bxm"
    filter_glob: bpy.props.StringProperty(default="*.bxm", options={'HIDDEN'})

    def doImport(self, filepath):
        from . import gaAreaImporter
        gaAreaImporter.importGaArea(filepath)

    def execute(self, context):
        self.doImport(self.filepath)
        return {'FINISHED'}
