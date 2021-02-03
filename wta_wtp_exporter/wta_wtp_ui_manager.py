import bpy
import os
from bpy_extras.io_utils import ExportHelper,ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty

def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

class WTAItems(bpy.types.PropertyGroup):
    index : bpy.props.IntProperty()

    parent_mat : bpy.props.StringProperty()

    texture_map_type : bpy.props.StringProperty()
    texture_identifier : bpy.props.StringProperty()
    texture_path : bpy.props.StringProperty()

class GetMaterialsOperator(bpy.types.Operator):
    '''Fetch all NieR:Automata materials in scene'''
    bl_idname = "na.get_wta_materials"
    bl_label = "Fetch NieR:Automata Materials"

    def execute(self, context):
        context.scene.WTAMaterials.clear()
        for mat in bpy.data.materials:
            for key, value in mat.items():
                # Only include listed textures map types
                if any(substring in key for substring in ['g_AlbedoMap', 'g_MaskMap', 'g_NormalMap', 'g_EnvMap', 'g_DetailNormalMap', 'g_IrradianceMap', 'g_CurvatureMap', 'g_SpreadPatternMap']):
                    id = len(context.scene.WTAMaterials)
                    new_tex = context.scene.WTAMaterials.add()
                    new_tex.index = id

                    new_tex.parent_mat = mat.name
                    new_tex.texture_map_type = key
                    new_tex.texture_identifier = value
                    new_tex.texture_path = 'None'

        return {'FINISHED'}

class AssignBulkTextures(bpy.types.Operator, ImportHelper):
    '''Quickly assign textures from a directory (according to filename)'''
    bl_idname = "na.assign_original"
    bl_label = "Select Textures Directory"
    filename_ext = ""
    dirpath : StringProperty(name = "", description="Choose a textures directory:", subtype='DIR_PATH')

    def execute(self, context):
        assigned_textures = []

        directory = os.path.dirname(self.filepath)
        for filename in os.listdir(directory):
            for item in context.scene.WTAMaterials:
                if item.texture_identifier == filename[:-4] and filename[-4:] == '.dds':
                    item.texture_path = directory + '\\' + filename
                    # Keep track of what was assigned, without duplicates.
                    if filename not in assigned_textures:
                        assigned_textures.append(filename)

        ShowMessageBox('Successfully assigned ' + str(len(assigned_textures)) + ' textures.', 'Assign Textures', 'INFO')
        return{'FINISHED'}

class PurgeUnusedMaterials(bpy.types.Operator):
    '''Permanently remove all unused materials'''
    bl_idname = "na.purge_materials"
    bl_label = "Purge Materials"

    def execute(self, context):
        for material in bpy.data.materials:
            if not material.users:
                print('Purging unused material:', material)
                bpy.data.materials.remove(material)
        return{'FINISHED'}

class ExportWTPOperator(bpy.types.Operator, ExportHelper):
    '''Export a NieR:Automata WTP File'''
    bl_idname = "na.export_wtp"
    bl_label = "Export WTP"
    bl_options = {'PRESET'}
    filename_ext = ".wtp"
    filter_glob: StringProperty(default="*.wtp", options={'HIDDEN'})

    def execute(self, context):
        from . import export_wtp
        export_wtp.main(context, self.filepath)
        return{'FINISHED'}

class ExportWTAOperator(bpy.types.Operator, ExportHelper):
    '''Export a NieR:Automata WTA File'''
    bl_idname = "na.export_wta"
    bl_label = "Export WTA"
    bl_options = {'PRESET'}
    filename_ext = ".wta"
    filter_glob: StringProperty(default="*.wta", options={'HIDDEN'})

    def execute(self, context):
        from . import export_wta
        export_wta.main(context, self.filepath)
        return{'FINISHED'}

class FilepathSelector(bpy.types.Operator, ExportHelper):
    '''Select texture file'''
    bl_idname = "na.filepath_selector"
    bl_label = "Select Texture"
    filename_ext = ""

    id : bpy.props.IntProperty(options={'HIDDEN'})

    def execute(self, context):
        changed_identifier = context.scene.WTAMaterials[self.id].texture_identifier

        fdir = self.properties.filepath
        for item in context.scene.WTAMaterials:
            if item.texture_identifier == changed_identifier:
                item.texture_path = fdir

        return{'FINISHED'}

class SyncBlenderMaterials(bpy.types.Operator):
    '''Sync the texture of Blender's materials to these'''
    bl_idname = "na.sync_blender_materials"
    bl_label = "Sync Blender Materials"

    def execute(self, context):
        for item in context.scene.WTAMaterials:
            if item.texture_path == "None":
                continue
            for mat in bpy.data.materials:
                if mat.name == item.parent_mat:
                    nodes = mat.node_tree.nodes
                    for node in nodes:
                        if node.label == item.texture_map_type:
                            node.image = bpy.data.images.load(item.texture_path)
                            if "MaskMap" in node.label or "NormalMap" in node.label:
                                node.image.colorspace_settings.name = 'Non-Color'
                            break
                    break
        return{'FINISHED'}

class SyncMaterialIdentifiers(bpy.types.Operator):
    '''Sync the texture identifiers of materials to these'''
    bl_idname = "na.sync_material_identifiers"
    bl_label = "Sync Identifiers in Materials"

    def execute(self, context):
        for item in context.scene.WTAMaterials:
            for mat in bpy.data.materials:
                if mat.name == item.parent_mat:
                    for key in mat.keys():
                        if key == item.texture_map_type:
                            mat[key] = item.texture_identifier
                            break
                    break
        return{'FINISHED'}


class WTA_WTP_PT_Export(bpy.types.Panel):
    bl_label = "NieR:Automata WTP/WTA Export"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "output"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator("na.purge_materials")

        row = layout.row()
        row.scale_y = 2.0
        row.operator("na.get_wta_materials")

        row = layout.row()
        row.operator("na.assign_original")

        row = layout.row()
        row.operator("na.export_wtp")
        row.operator("na.export_wta")

        pad = layout.row()
        row = layout.row()
        row.label(text="Materials:")
        row = layout.row()
        row.operator("na.sync_material_identifiers")
        row.operator("na.sync_blender_materials")

        loaded_mats = []
        for item in context.scene.WTAMaterials:
            # Split material categories into boxes
            if item.parent_mat not in loaded_mats:  
                box = layout.box()
                box.label(text=item.parent_mat + ':', icon='MATERIAL')
            
            row = box.row()
            row.label(text=item.texture_map_type)
            row.prop(item, "texture_identifier", text="")
            row.prop(item, "texture_path", text="")
            row.operator("na.filepath_selector", icon="FILE_FOLDER", text="").id = item.index

            loaded_mats.append(item.parent_mat)

        row = layout.row()
        row.label(text='Hints:')
        row = layout.row()
        box = row.box()
        row = box.row()
        row.label(text='- Texture identifier has to be 8 HEX characters long.')
        row = box.row()
        row.label(text='- Textures have to be in DDS format (DXT1, DXT3, DXT5).')
        row = box.row()
        row.label(text='- It is recommended to "Sync Identifiers in Materials" before WMB export.')

def register():
    bpy.utils.register_class(WTAItems)
    bpy.utils.register_class(GetMaterialsOperator)
    bpy.utils.register_class(WTA_WTP_PT_Export)
    bpy.utils.register_class(FilepathSelector)
    bpy.utils.register_class(ExportWTAOperator)
    bpy.utils.register_class(ExportWTPOperator)
    bpy.utils.register_class(PurgeUnusedMaterials)
    bpy.utils.register_class(AssignBulkTextures)
    bpy.utils.register_class(SyncBlenderMaterials)
    bpy.utils.register_class(SyncMaterialIdentifiers)

    bpy.types.Scene.WTAMaterials = bpy.props.CollectionProperty(type=WTAItems)

def unregister():
    bpy.utils.unregister_class(WTAItems)
    bpy.utils.unregister_class(GetMaterialsOperator)
    bpy.utils.unregister_class(WTA_WTP_PT_Export)
    bpy.utils.unregister_class(FilepathSelector)
    bpy.utils.unregister_class(ExportWTAOperator)
    bpy.utils.unregister_class(ExportWTPOperator)
    bpy.utils.unregister_class(PurgeUnusedMaterials)
    bpy.utils.unregister_class(AssignBulkTextures)
    bpy.utils.unregister_class(SyncBlenderMaterials)
    bpy.utils.unregister_class(SyncMaterialIdentifiers)