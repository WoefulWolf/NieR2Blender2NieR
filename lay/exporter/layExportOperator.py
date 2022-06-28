import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper


class ExportNierLay(bpy.types.Operator, ExportHelper):
    '''Export a NieR:Automata LAY File'''
    bl_idname = "export.lay_data"
    bl_label = "Export LAY File"
    bl_options = {'PRESET'}
    filename_ext = ".lay"
    filter_glob: StringProperty(default="*.lay", options={'HIDDEN'})

    def execute(self, context):
        from . import lay_exporter

        lay_exporter.main(self.filepath)
        return {'FINISHED'}