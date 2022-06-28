import bpy
from bpy_extras.io_utils import ExportHelper

class ExportNierSar(bpy.types.Operator, ExportHelper):
    '''Export a Nier:Automata Sar (Skeleton) File.'''
    bl_idname = "export_scene.sar"
    bl_label = "Export Sar Data"
    bl_options = {'PRESET', 'UNDO'}
    filename_ext = ".sar"
    filter_glob: bpy.props.StringProperty(default="*.sar", options={'HIDDEN'})

    def execute(self, context):
        from . import sarExporter
        sarExporter.exportSar(self.filepath)
        return {'FINISHED'}
