import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper

from . import col_exporter
from ...utils.util import centre_origins, triangulate_meshes


class ExportNierCol(bpy.types.Operator, ExportHelper):
    '''Export a NieR:Automata COL File'''
    bl_idname = "export.col_data"
    bl_label = "Export COL File"
    bl_options = {'PRESET'}
    filename_ext = ".col"
    filter_glob: StringProperty(default="*.col", options={'HIDDEN'})

    generateColTree: bpy.props.BoolProperty(name="Generate Collision Tree", description="This automatically generates colTreeNodes based on your geometry and assigns the right meshes to the right colTreeNodes. Only disable it if you are manually adjusting them", default=True)
    centre_origins: bpy.props.BoolProperty(name="Centre Origins", description="This automatically centres the origins of all your objects. (Recommended)", default=True)
    triangulate_meshes: bpy.props.BoolProperty(name="Triangulate Meshes", description="This automatically adds and applies the Triangulate Modifier on all your objects. (Slow)", default=True)

    def execute(self, context):

        if self.centre_origins:
            print("Centering origins...")
            centre_origins("COL")

        if self.triangulate_meshes:
            print("Triangulating meshes...")
            triangulate_meshes("COL")

        col_exporter.main(self.filepath, self.generateColTree)
        return {'FINISHED'}