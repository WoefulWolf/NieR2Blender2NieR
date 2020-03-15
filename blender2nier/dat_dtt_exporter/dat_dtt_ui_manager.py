import bpy
import os
from bpy_extras.io_utils import ExportHelper,ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.app.handlers import persistent

def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

class DATItems(bpy.types.PropertyGroup):
    index : bpy.props.IntProperty()
    path : bpy.props.StringProperty()

class CreateDATDTTData(bpy.types.Operator):
    '''Initialize DAT & DTT'''
    bl_idname = "na.create_dat_data"
    bl_label = "Initialize DAT & DTT"

    def execute(self, context):
        if len(context.scene.DATData) != 2:
            context.scene.DATData.clear()
            dat = context.scene.DATData.add()
            dat.index = 0
            dat.path = 'None'

            dtt = context.scene.DATData.add()
            dtt.index = 1
            dtt.path = 'None'

        return {'FINISHED'}

class ExportDATOperator(bpy.types.Operator, ExportHelper):
    '''Export DAT'''
    bl_idname = "na.export_dat"
    bl_label = "Export DAT"
    filename_ext = ".dat"
    filter_glob: StringProperty(default="*.dat", options={'HIDDEN'})

    def execute(self, context):
        from blender2nier.dat_dtt_exporter import export_dat
        export_dat.main(context.scene.DATData[0].path, self.filepath)
        return {'FINISHED'}

class ExportDTTOperator(bpy.types.Operator, ExportHelper):
    '''Export DTT'''
    bl_idname = "na.export_dtt"
    bl_label = "Export DTT"
    filename_ext = ".dtt"
    filter_glob: StringProperty(default="*.dtt", options={'HIDDEN'})

    def execute(self, context):
        from blender2nier.dat_dtt_exporter import export_dat
        export_dat.main(context.scene.DATData[1].path, self.filepath)
        return {'FINISHED'}

class DAT_DTT_PT_Export(bpy.types.Panel):
    bl_label = "NieR:Automata DAT/DTT Export"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "output"

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.scale_y = 1.5
        row.operator("na.create_dat_data")

        row = layout.row()
        if len(context.scene.DATData) != 0:
            box = row.box()
            row = box.row()
            row.label(text="DAT Directory:")
            row.prop(context.scene.DATData[0], "path", text="")
            row.operator("na.folder_select", icon="FILE_FOLDER", text="").id = context.scene.DATData[0].index

            row = layout.row()
            box = row.box()
            row = box.row()
            row.label(text="DTT Directory:")
            row.prop(context.scene.DATData[1], "path", text="")
            row.operator("na.folder_select", icon="FILE_FOLDER", text="").id = context.scene.DATData[1].index

            row = layout.row()
            row.scale_y = 2.0
            row.operator("na.export_dat")
            row.operator("na.export_dtt")

class SelectFolder(bpy.types.Operator, ImportHelper):
    '''Select Folder'''
    bl_idname = "na.folder_select"
    bl_label = "Select Directory"
    filename_ext = ""
    dirpath : StringProperty(name = "", description="Choose directory:", subtype='DIR_PATH')

    id : bpy.props.IntProperty(options={'HIDDEN'})

    def execute(self, context):
        directory = os.path.dirname(self.filepath)
        context.scene.DATData[self.id].path = directory

        return {'FINISHED'}

def register():
    bpy.utils.register_class(DATItems)
    bpy.utils.register_class(DAT_DTT_PT_Export)
    bpy.utils.register_class(CreateDATDTTData)
    bpy.utils.register_class(SelectFolder)
    bpy.utils.register_class(ExportDATOperator)
    bpy.utils.register_class(ExportDTTOperator)

    bpy.types.Scene.DATData = bpy.props.CollectionProperty(type=DATItems)

def unregister():
    bpy.utils.unregister_class(DATItems)
    bpy.utils.unregister_class(DAT_DTT_PT_Export)
    bpy.utils.unregister_class(CreateDATDTTData)
    bpy.utils.unregister_class(SelectFolder)
    bpy.utils.unregister_class(ExportDATOperator)
    bpy.utils.unregister_class(ExportDTTOperator)