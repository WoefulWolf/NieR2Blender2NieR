import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper
import os

from .motExporter import exportMot

class ExportNierMot(bpy.types.Operator, ExportHelper):
    """Export a Nier Animation mot file"""
    bl_idname = "export_scene.mot"
    bl_label = "Export Nier Animation Data"
    bl_options = {'UNDO'}

    patchExisting: bpy.props.BoolProperty(
        name="Patch Existing",
        description="Patch existing mot file instead of creating a new one",
        default=False
    )
    filename_ext = ".mot"
    filter_glob: bpy.props.StringProperty(default="*.mot", options={'HIDDEN'})

    def execute(self, context):
        from .motExporter import exportMot

        if self.patchExisting and not os.path.exists(self.filepath):
            self.report({'ERROR'}, "File does not exist")
            return {'CANCELLED'}
        
        exportMot(self.filepath, self.patchExisting)

        self.report({'INFO'}, "Exported mot file")

        return {'FINISHED'}
