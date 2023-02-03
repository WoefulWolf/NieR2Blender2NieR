import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

from .motImporter import importMot

class ImportNierMot(bpy.types.Operator, ImportHelper):
    """Import a Nier Animation mot file"""
    bl_idname = "import_scene.mot"
    bl_label = "Import Nier Animation Data"
    bl_options = {'UNDO'}

    filename_ext = ".mot"
    filter_glob: bpy.props.StringProperty(default="*.mot", options={'HIDDEN'})

    def execute(self, context):
        from .motImporter import importMot

        importMot(self.filepath)

        self.report({'INFO'}, "Imported mot file")

        return {'FINISHED'}
