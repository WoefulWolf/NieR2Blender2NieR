import bpy
from bpy_extras.io_utils import ExportHelper


class ExportNierGaArea(bpy.types.Operator, ExportHelper):
    '''Export a Nier:Automata Ga Area File.'''
    bl_idname = "export_scene.ga_area"
    bl_label = "Export GAArea.bxm"
    bl_options = {'PRESET', 'UNDO'}
    filename_ext = ".bxm"
    filter_glob: bpy.props.StringProperty(default="*.bxm", options={'HIDDEN'})

    def execute(self, context):
        from . import gaAreaExporter
        gaAreaExporter.exportGaArea(self.filepath)
        return {'FINISHED'}
