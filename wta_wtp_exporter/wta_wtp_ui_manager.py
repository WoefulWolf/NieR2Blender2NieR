import bpy
import os
from bpy_extras.io_utils import ExportHelper,ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
import re

def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

def generateID(context):
    if len(context.scene.WTAMaterials) != 0:
        return context.scene.WTAMaterials[-1].id + 1
    else:
        return 0

def getManualTextureItems(context):
    manual_items = []
    for item in context.scene.WTAMaterials:
        if item.parent_mat == "":
            manual_items.append(item)
    return manual_items

class WTAItems(bpy.types.PropertyGroup):
    id : bpy.props.IntProperty()

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
                if any(substring in key for substring in ['g_AlbedoMap', 'g_MaskMap', 'g_NormalMap', 'g_EnvMap', 'g_DetailNormalMap', 'g_IrradianceMap', 'g_CurvatureMap', 'g_SpreadPatternMap', 'g_LUT', 'g_LightMap', 'g_GradationMap']):
                    id = generateID(context)
                    new_tex = context.scene.WTAMaterials.add()
                    new_tex.id = id

                    new_tex.parent_mat = mat.name
                    new_tex.texture_map_type = key
                    new_tex.texture_identifier = value
                    new_tex.texture_path = 'None'

        return {'FINISHED'}

class GetNewMaterialsOperator(bpy.types.Operator):
    '''Fetch newly added NieR:Automata materials in scene'''
    bl_idname = "na.get_new_wta_materials"
    bl_label = "Fetch New Materials"

    def execute(self, context):
        def doesWtaMaterialExist(blenderMat: bpy.types.Material, context: bpy.types.Context) -> bool:
            for wtaMat in context.scene.WTAMaterials:
                if wtaMat.parent_mat == blenderMat.name:
                    return True

            return False
        
        newMaterialsAdded = 0
        for mat in bpy.data.materials:
            if doesWtaMaterialExist(mat, context):
                continue

            newMaterialsAdded += 1
            for key, value in mat.items():
                if not any(substring in key for substring in ['g_AlbedoMap', 'g_MaskMap', 'g_NormalMap', 'g_EnvMap', 'g_DetailNormalMap', 'g_IrradianceMap', 'g_CurvatureMap', 'g_SpreadPatternMap', 'g_LUT', 'g_LightMap', 'g_GradationMap']):
                    continue

                id = generateID(context)
                new_tex = context.scene.WTAMaterials.add()
                new_tex.id = id

                new_tex.parent_mat = mat.name
                new_tex.texture_map_type = key
                new_tex.texture_identifier = value
                new_tex.texture_path = 'None'


        ShowMessageBox(f"{newMaterialsAdded} new material{'s' if newMaterialsAdded != 1 else ''} added")

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
                    item.texture_path = directory + '/' + filename
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

class RemoveWtaMaterial(bpy.types.Operator):
    '''Removes a material by id'''
    bl_idname = "na.remove_wta_material"
    bl_label = "Remove Wta Material"

    material_name : bpy.props.StringProperty()

    def execute(self, context):
        i = 0
        while i < len(context.scene.WTAMaterials):
            material = context.scene.WTAMaterials[i]
            if material.parent_mat == self.material_name:
                context.scene.WTAMaterials.remove(i)
            else:
                i += 1

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

class FilepathSelector(bpy.types.Operator, ImportHelper):
    '''Select texture file'''
    bl_idname = "na.filepath_selector"
    bl_label = "Select Texture"
    filename_ext = ".dds"
    filter_glob: StringProperty(default="*.dds", options={'HIDDEN'})

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

class AddManualTextureOperator(bpy.types.Operator):
    '''Manually add a texture to be exported'''
    bl_idname = "na.add_manual_texture"
    bl_label = "Add Texture"

    def execute(self, context):
        id = generateID(context)
        new_tex = context.scene.WTAMaterials.add()
        new_tex.id = id
        new_tex.parent_mat = ""
        new_tex.texture_map_type = "Enter Map Type"
        new_tex.texture_identifier = "Enter Identifier"
        new_tex.texture_path = 'Enter Path'
        return {"FINISHED"}

class RemoveManualTextureOperator(bpy.types.Operator):
    '''Remove a manually added texture'''
    bl_idname = "na.remove_manual_texture"
    bl_label = "Remove"

    id : bpy.props.IntProperty(options={'HIDDEN'})

    def execute(self, context):
        index_to_remove = 0
        for i, item in enumerate(context.scene.WTAMaterials):
            if item.id == self.id:
                index_to_remove = i
                break

        context.scene.WTAMaterials.remove(index_to_remove)
        return {"FINISHED"}

class TextureFilepathSelector(bpy.types.Operator, ImportHelper):
    '''Select texture file for Texture Replacer'''
    bl_idname = "na.texture_filepath_selector"
    bl_label = "Select Texture"
    filename_ext = ".dds"
    filter_glob: StringProperty(default="*.dds", options={'HIDDEN'})

    def execute(self, context):
        context.scene.ReplaceTexturePath = self.properties.filepath

        return{'FINISHED'}

class MassTextureReplacer(bpy.types.Operator):
    '''Replace all texture paths that match set id'''
    bl_idname = "na.mass_texture_replacer"
    bl_label = "Replace Textures"

    def execute(self, context):
        replacedTextures = 0

        searchId = context.scene.ReplaceTextureName
        replaceId = context.scene.NewTextureName
        replacePath = context.scene.ReplaceTexturePath

        if not searchId:
            ShowMessageBox("Empty Search Identifier not allowed!")
            return{"CANCELLED"}

        for item in context.scene.WTAMaterials:
            if not textureMatchesSearch(item, searchId, newTexture=replacePath):
                continue

            replacedTextures += 1
            if replaceId:
                item.texture_identifier = replaceId
            if replacePath:
                item.texture_path = replacePath

        ShowMessageBox(f"Replaced {replacedTextures} texture{'s' if replacedTextures != 1 else ''}")
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
        row.operator("na.get_new_wta_materials")

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

def textureMatchesSearch(
    mat : WTAItems, searchStr : str,
    checkIdName = True, checkTexName = False, checkMatName = False, checkTexPath = False,
    useRegex = False,
    newTexture : str = None
) -> bool:
    
    if useRegex:
        compFunc = lambda pattern, str: re.search(pattern, str, re.I)
    else:
        compFunc = lambda str1, str2: str1.lower() in str2.lower()
    
    return compFunc(searchStr, mat.texture_identifier) and checkIdName and \
           (not newTexture or mat.texture_path != newTexture) or \
           compFunc(searchStr, mat.parent_mat) and checkMatName or \
           compFunc(searchStr, mat.texture_map_type) and checkTexName or \
           compFunc(searchStr, mat.texture_path) and checkTexPath or \
           not searchStr

class WTA_WTP_PT_Materials(bpy.types.Panel):
    bl_parent_id = "WTA_WTP_PT_Export"
    bl_label = "Blender Materials"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "output"

    def draw(self, context):
        layout = self.layout

        # texture replacer
        row = layout.row()
        row.alignment = "LEFT"
        row.prop(context.scene, "bShowMassReplacer", emboss=False,
            text="Find, rename & replace textures",
            icon = "TRIA_DOWN" if context.scene.bShowMassReplacer else "TRIA_RIGHT")
        if context.scene.bShowMassReplacer:
            row = layout.row()
            row.label(text="Identifier")
            row.label(text="New Identifier")
            row.label(text="Path")
            row.label(text="", icon="FILE_BLANK")
            row = layout.row()
            row.prop(context.scene, "ReplaceTextureName", text="")
            row.prop(context.scene, "NewTextureName", text="")
            row.prop(context.scene, "ReplaceTexturePath", text="")
            row.operator("na.texture_filepath_selector", icon="FILE", text="")
            row = layout.row()
            replacableTexturesCount = len([ mat for mat in context.scene.WTAMaterials
                 if textureMatchesSearch(mat, context.scene.ReplaceTextureName, newTexture=context.scene.ReplaceTexturePath) ])
            replacableTexturesCountStr = str(replacableTexturesCount) if replacableTexturesCount < len(context.scene.WTAMaterials) else "all"
            row.operator("na.mass_texture_replacer", text=f"Replace {replacableTexturesCountStr} Texture{'s' if replacableTexturesCountStr != '1' else ''}")
            layout.separator()

        # search
        row = layout.row(align=True)
        row.prop(context.scene, "MatSearchStr", icon="VIEWZOOM", text="")
        row.prop(context.scene, "bSearchRegex", icon="EVENT_R", text="")
        row.prop(context.scene, "bSearchMatName", icon="MATERIAL", text="")
        row.prop(context.scene, "bSearchTexName", icon="TEXTURE", text="")
        row.prop(context.scene, "bSearchIdentifiers", icon="OBJECT_DATA", text="")
        row.prop(context.scene, "bSearchTexPaths", icon="FILE", text="")

        # materials
        loaded_mats = []
        for item in context.scene.WTAMaterials:
            # Skip if this texture has no Blender material (is thus manual texture)
            if item.parent_mat == "":
                continue
            # text search filter
            if not textureMatchesSearch(item, context.scene.MatSearchStr,
                    checkMatName=context.scene.bSearchMatName, checkTexName=context.scene.bSearchTexName,
                    checkIdName=context.scene.bSearchIdentifiers, checkTexPath=context.scene.bSearchTexPaths,
                    useRegex=context.scene.bSearchRegex):
                continue
            # Split material categories into boxes
            if item.parent_mat not in loaded_mats:  
                box = layout.box()
                row = box.row()
                row.label(text=item.parent_mat + ':', icon='MATERIAL')
                row.operator("na.remove_wta_material", icon="X", text="", emboss=False).material_name = item.parent_mat
            
            row = box.row()
            row.label(text=item.texture_map_type)
            row.prop(item, "texture_identifier", text="")
            row.prop(item, "texture_path", text="")
            row.operator("na.filepath_selector", icon="FILE", text="").id = item.id

            loaded_mats.append(item.parent_mat)

        if len(loaded_mats) == 0:
            layout.label(text="No materials found", icon="INFO")

class WTA_WTP_PT_Manual(bpy.types.Panel):
    bl_parent_id = "WTA_WTP_PT_Export"
    bl_label = "Manually Add Textures To Export"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "output"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.scale_y = 1.5
        row.operator("na.add_manual_texture")

        manual_items = getManualTextureItems(context)

        for item in manual_items:
            box = layout.box()
            row = box.row()
            row.prop(item, "texture_map_type", text="")
            row.prop(item, "texture_identifier", text="")
            row.prop(item, "texture_path", text="")
            row.operator("na.filepath_selector", icon="FILE", text="").id = item.id
            row.operator("na.remove_manual_texture", icon="X", text="").id = item.id

class WTA_WTP_PT_Hints(bpy.types.Panel):
    bl_parent_id = "WTA_WTP_PT_Export"
    bl_label = "Hints"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "output"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
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
    bpy.utils.register_class(GetNewMaterialsOperator)
    bpy.utils.register_class(AddManualTextureOperator)
    bpy.utils.register_class(RemoveManualTextureOperator)
    bpy.utils.register_class(RemoveWtaMaterial)
    bpy.utils.register_class(WTA_WTP_PT_Export)
    bpy.utils.register_class(WTA_WTP_PT_Materials)
    bpy.utils.register_class(WTA_WTP_PT_Manual)
    bpy.utils.register_class(WTA_WTP_PT_Hints)
    bpy.utils.register_class(FilepathSelector)
    bpy.utils.register_class(ExportWTAOperator)
    bpy.utils.register_class(ExportWTPOperator)
    bpy.utils.register_class(PurgeUnusedMaterials)
    bpy.utils.register_class(AssignBulkTextures)
    bpy.utils.register_class(SyncBlenderMaterials)
    bpy.utils.register_class(SyncMaterialIdentifiers)
    bpy.utils.register_class(TextureFilepathSelector)
    bpy.utils.register_class(MassTextureReplacer)

    bpy.types.Scene.WTAMaterials = bpy.props.CollectionProperty(type=WTAItems)
    # Mass texture replacer props
    bpy.types.Scene.bShowMassReplacer = bpy.props.BoolProperty (
        name = "Show texture replacer",
        default = False,
    )
    bpy.types.Scene.ReplaceTextureName = bpy.props.StringProperty (
        name = "Search ID",
        default = "",
        description = "",
        options = {"SKIP_SAVE", "TEXTEDIT_UPDATE"}
    )
    bpy.types.Scene.NewTextureName = bpy.props.StringProperty (
        name = "New ID",
        default = "",
        description = "If empty: don't change",
        options = {"SKIP_SAVE", "TEXTEDIT_UPDATE"}
    )
    bpy.types.Scene.ReplaceTexturePath = bpy.props.StringProperty (
        name = "Texture Path",
        default = "",
        description = "If empty: don't change",
        options = {"SKIP_SAVE", "TEXTEDIT_UPDATE"}
    )
    # materials search props
    bpy.types.Scene.MatSearchStr = bpy.props.StringProperty (
        # name = "Search String",
        default = "",
        description = "",
        options = {"SKIP_SAVE", "TEXTEDIT_UPDATE"}
    )
    bpy.types.Scene.bSearchMatName = bpy.props.BoolProperty (
        name = "Material Names",
        default = True,
        description = "Search in material names",
    )
    bpy.types.Scene.bSearchTexName = bpy.props.BoolProperty (
        name = "Texture Map Names",
        default = True,
        description = "Search in texture map names",
    )
    bpy.types.Scene.bSearchIdentifiers = bpy.props.BoolProperty (
        name = "Identifiers",
        default = True,
        description = "Search in identifiers",
    )
    bpy.types.Scene.bSearchTexPaths = bpy.props.BoolProperty (
        name = "Texture Paths",
        default = True,
        description = "Search in texture paths",
    )
    bpy.types.Scene.bSearchRegex = bpy.props.BoolProperty (
        name = "Regex Mode",
        default = False,
        description = "Use regular expressions",
    )

def unregister():
    bpy.utils.unregister_class(WTAItems)
    bpy.utils.unregister_class(GetMaterialsOperator)
    bpy.utils.unregister_class(GetNewMaterialsOperator)
    bpy.utils.unregister_class(AddManualTextureOperator)
    bpy.utils.unregister_class(RemoveManualTextureOperator)
    bpy.utils.unregister_class(RemoveWtaMaterial)
    bpy.utils.unregister_class(WTA_WTP_PT_Export)
    bpy.utils.unregister_class(WTA_WTP_PT_Materials)
    bpy.utils.unregister_class(WTA_WTP_PT_Manual)
    bpy.utils.unregister_class(WTA_WTP_PT_Hints)
    bpy.utils.unregister_class(FilepathSelector)
    bpy.utils.unregister_class(ExportWTAOperator)
    bpy.utils.unregister_class(ExportWTPOperator)
    bpy.utils.unregister_class(PurgeUnusedMaterials)
    bpy.utils.unregister_class(AssignBulkTextures)
    bpy.utils.unregister_class(SyncBlenderMaterials)
    bpy.utils.unregister_class(SyncMaterialIdentifiers)
    bpy.utils.unregister_class(TextureFilepathSelector)
    bpy.utils.unregister_class(MassTextureReplacer)

    del bpy.types.Scene.WTAMaterials
    del bpy.types.Scene.bShowMassReplacer
    del bpy.types.Scene.ReplaceTextureName
    del bpy.types.Scene.NewTextureName
    del bpy.types.Scene.ReplaceTexturePath
    del bpy.types.Scene.MatSearchStr
    del bpy.types.Scene.bSearchMatName
    del bpy.types.Scene.bSearchTexName
    del bpy.types.Scene.bSearchIdentifiers
    del bpy.types.Scene.bSearchTexPaths
    del bpy.types.Scene.bSearchRegex