import traceback

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper


class ExportNierWmb(bpy.types.Operator, ExportHelper):
    '''Export a NieR:Automata WMB File'''
    bl_idname = "export.wmb_data"
    bl_label = "Export WMB File"
    bl_options = {'PRESET'}
    filename_ext = ".wmb"
    filter_glob: StringProperty(default="*.wmb", options={'HIDDEN'})

    centre_origins: bpy.props.BoolProperty(name="Centre Origins", description="This automatically centres the origins of all your objects. (Recommended)", default=True)
    triangulate_meshes: bpy.props.BoolProperty(name="Triangulate Meshes", description="This automatically adds and applies the Triangulate Modifier on all your objects. Only disable if you know your meshes are triangulated and you wish to reduce export times", default=True)
    delete_loose_geometry: bpy.props.BoolProperty(name="Delete Loose Geometry", description="This automatically runs the 'Delete Loose Geometry (All)' operator before exporting. It deletes all loose vertices or edges that could result in unwanted results in-game", default=True)

    def execute(self, context):
        from . import wmb_exporter

        bpy.data.collections['WMB'].all_objects[0].select_set(True)

        if self.centre_origins:
            print("Centering origins...")
            wmb_exporter.centre_origins("WMB")

        """
        if self.purge_materials:
            print("Purging materials...")
            wmb_exporter.purge_unused_materials()
        """

        if self.triangulate_meshes:
            print("Triangulating meshes...")
            wmb_exporter.triangulate_meshes("WMB")

        if self.delete_loose_geometry:
            print("Deleting loose geometry...")
            bpy.ops.b2n.deleteloosegeometryall()

        try:
            print("Starting export...")
            wmb_exporter.main(self.filepath)
            return wmb_exporter.restore_blend()
        except:
            print(traceback.format_exc())
            self.report({'ERROR'}, "An unexpected error has occurred during export. Please check the console for more info.")
            return {'CANCELLED'}
