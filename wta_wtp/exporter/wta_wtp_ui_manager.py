import os
import re
from typing import List, Tuple
from itertools import count, filterfalse

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper, ImportHelper

from ...utils.util import getUsedMaterials, getNodeWithLabel, getAllObjectsWithMaterial, isSharedTexture, findPreferenceTexture, clearTextureIndex


def generateID(context):
    if len(context.scene.WTAMaterials) != 0:
        return context.scene.WTAMaterials[-1].id + 1
    else:
        return 0
        
def getWTAItemByID(context, id):
    for item in context.scene.WTAMaterials:
        if item.id == id:
            return item

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

def autoSetWtaTexPathsForMat(blendMat: bpy.types.Material, allWtaItems: List[WTAItems], warnings: List[str]):
    # filter relevant wta items for this material
    wtaItems = [item for item in allWtaItems if item.parent_mat == blendMat.name]

    # group blender textures by name
    def splitName(name: str, offset: int) -> Tuple[str, int]:
        """example: 'g_albedoMap1' -> ('g_albedoMap', 1 + offset)"""
        nameParts = re.match(r"^(\D+)(\d*)", name)
        if not nameParts:
            return None, -1
        baseName = nameParts.group(1)
        index = int(nameParts.group(2)) + offset if nameParts.group(2) != "" else 0
        return baseName, index
    
    texturesInMat = [
        { "name": node.label, "path": node.image.filepath_from_user() }
        for node in blendMat.node_tree.nodes
        if node.type == "TEX_IMAGE" and node.image is not None
    ]
    groupedTextures = {}    # { baseName: list[paths] }
    for tex in texturesInMat:
        baseName, index = splitName(tex["name"], 1)
        if not baseName:
            continue

        if baseName not in groupedTextures:
            groupedTextures[baseName] = []
        if len(groupedTextures[baseName]) < index + 1:
            groupedTextures[baseName].extend([None] * (index + 1 - len(groupedTextures[baseName])))
        groupedTextures[baseName][index] = tex["path"]
    
    # gather texture directories
    textureDirs = []
    for tex in texturesInMat:
        texDir = os.path.dirname(tex["path"])
        if texDir not in textureDirs:
            textureDirs.append(texDir)
    def searchForTexture(texId: str) -> str:
        for texDir in textureDirs:
            if not texDir:
                continue
            texPath = os.path.join(texDir, f"{texId}.dds")
            if os.path.exists(texPath):
                return texPath
        return findPreferenceTexture(texId)
    
    exactTextures = {tex["name"]: tex["path"] for tex in texturesInMat}

    # set wta texture paths
    for item in wtaItems:
        baseName, index = splitName(item.texture_map_type, -1)
        newTexPath = None
        if item.texture_map_type in exactTextures:
            newTexPath = exactTextures[item.texture_map_type] or None
        # best case: texture in texture groups
        elif baseName in groupedTextures and len(groupedTextures[baseName]) > index:
            newTexPath = groupedTextures[baseName][index]
        # if out of range and multiple textures with same name, try previous
        elif baseName in groupedTextures and index != -1 and 0 < len(groupedTextures[baseName]) < index + 1:
            index = len(groupedTextures[baseName]) - 1
            newTexPath = groupedTextures[baseName][index]
        # search in texture directories
        if newTexPath:
            # find other textures with same id
            # to ensure that there aren't multiple different textures with the same id
            existingTexPath = next(filter(lambda item2: item.texture_identifier == item2.texture_identifier and item2.texture_path and item2.texture_path != "None", allWtaItems), None)
            if existingTexPath:
                if existingTexPath.texture_path == newTexPath:
                    item.texture_path = newTexPath
                else:
                    item.texture_path = existingTexPath.texture_path
                    warnings.append(f"{item.texture_map_type} {item.texture_identifier} in {item.parent_mat} different from texture path in {existingTexPath.parent_mat}")
            else:
                item.texture_path = newTexPath
        else:
            newTexPath = searchForTexture(item.texture_identifier)
            if newTexPath:
                item.texture_path = newTexPath

def handleAutoSetTextureWarnings(operatorSelf, warnings: List[str]):
    if len(warnings) == 0:
        return
    operatorSelf.report({'WARNING'}, f"{len(warnings)} ids have different texture paths! Check logs for details.")
    print(f"WARNING: {len(warnings)} ids have different texture paths")
    print("First encountered textures used instead. Consider changing the ids.")
    print("\n".join(warnings))

def isTextureTypeSupported(textureType: str) -> bool:
    for supportedTex in ['g_AlbedoMap', 'g_MaskMap', 'g_NormalMap', 'g_EnvMap', 'g_DetailNormalMap', 'g_IrradianceMap', 'g_CurvatureMap', 'g_SpreadPatternMap', 'g_LUT', 'g_LightMap', 'g_GradationMap', 'g_ParallaxMap']:
        if supportedTex in textureType:
            return True
    return False

def makeWtaMaterial(matName, textures: List[Tuple[str, str, str]]):
    for tex in textures:
        newID = generateID(bpy.context)
        newTex: WTAItems = bpy.context.scene.WTAMaterials.add()
        newTex.id = newID
        newTex.parent_mat = matName
        newTex.texture_map_type = tex[0]
        newTex.texture_identifier = tex[1]
        if tex[2] is not None and tex[2] != "None" and os.path.exists(tex[2]):
            newTex.texture_path = tex[2]
        else:
            newTex.texture_path = "None"

class GetMaterialsOperator(bpy.types.Operator):
    '''Fetch all NieR:Automata materials in scene'''
    bl_idname = "na.get_wta_materials"
    bl_label = "Fetch All Materials"
    bl_options = {"UNDO"}

    def execute(self, context):
        newMaterialsAdded = 0
        autoTextureWarnings = []
        clearTextureIndex()
        context.scene.WTAMaterials.clear()
        for mat in getUsedMaterials():
            try:
                wtaTextures: List[Tuple[str, str, str]] = [
                    (mapType, id, "None")
                    for mapType, id in mat.items()
                    if isTextureTypeSupported(mapType)
                ]
                makeWtaMaterial(mat.name, wtaTextures)
                newMaterialsAdded += 1
                autoSetWtaTexPathsForMat(mat, context.scene.WTAMaterials, autoTextureWarnings)
            except Exception as e:
                print(f"Error fetching material {mat.name}: {e}")

        handleAutoSetTextureWarnings(self, autoTextureWarnings)

        self.report({"INFO"}, f"Fetched {newMaterialsAdded} material{'s' if newMaterialsAdded != 1 else ''}")

        return {'FINISHED'}

class GetNewMaterialsOperator(bpy.types.Operator):
    '''Fetch newly added NieR:Automata materials in scene'''
    bl_idname = "na.get_new_wta_materials"
    bl_label = "Fetch New Materials"
    bl_options = {"UNDO"}

    def execute(self, context):
        def doesWtaMaterialExist(blenderMat: bpy.types.Material, context: bpy.types.Context) -> bool:
            for wtaMat in context.scene.WTAMaterials:
                if wtaMat.parent_mat == blenderMat.name:
                    return True

            return False
        
        newMaterialsAdded = 0
        autoTextureWarnings = []
        clearTextureIndex()
        for mat in getUsedMaterials():
            if doesWtaMaterialExist(mat, context):
                continue

            try:
                wtaTextures: List[Tuple[str, str, str]] = [
                    (mapType, id, "None")
                    for mapType, id in mat.items()
                    if isTextureTypeSupported(mapType)
                ]
                makeWtaMaterial(mat.name, wtaTextures)
                newMaterialsAdded += 1
                autoSetWtaTexPathsForMat(mat, context.scene.WTAMaterials, autoTextureWarnings)
            except Exception as e:
                print(f"Error fetching material {mat.name}: {e}")

        handleAutoSetTextureWarnings(self, autoTextureWarnings)

        self.report({"INFO"}, f"{newMaterialsAdded} new material{'s' if newMaterialsAdded != 1 else ''} added")

        return {'FINISHED'}

class AssignBulkTextures(bpy.types.Operator, ImportHelper):
    '''Quickly assign textures from a directory (according to filename)'''
    bl_idname = "na.assign_original"
    bl_label = "Select Textures Directory"
    bl_options = {"UNDO"}
    
    filename_ext = ""
    dirpath : StringProperty(name = "", description="Choose a textures directory:", subtype='DIR_PATH')

    def execute(self, context):
        assigned_textures = []

        directory = os.path.dirname(self.filepath)
        for filename in os.listdir(directory):
            if not filename.endswith('.dds'):
                continue
            file_texture_id = filename[:-4].lower()
            for item in context.scene.WTAMaterials:
                if item.texture_identifier.lower() == file_texture_id:
                    item.texture_path = directory + '/' + filename
                    # Keep track of what was assigned, without duplicates.
                    if filename not in assigned_textures:
                        assigned_textures.append(filename)

        self.report({"INFO"}, f"Successfully assigned {len(assigned_textures)} textures.")
        return{'FINISHED'}

class PurgeUnusedMaterials(bpy.types.Operator):
    '''Permanently remove all unused materials'''
    bl_idname = "na.purge_materials"
    bl_label = "Purge Materials"
    bl_options = {"UNDO"}

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
    bl_options = {"UNDO"}

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
    bl_options = {"UNDO"}

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
    bl_options = {"PRESET"}
    filename_ext = ".wta"
    filter_glob: StringProperty(default="*.wta", options={'HIDDEN'})

    def execute(self, context):
        from . import export_wta
        export_wta.main(context, self.filepath)
        return{'FINISHED'}

class FilepathSelector(bpy.types.Operator, ImportHelper):
    '''Open a DDS file for this texture. Rows with the same identifier get it too'''
    bl_idname = "na.filepath_selector"
    bl_label = "Open File"
    bl_options = {"UNDO"}

    filename_ext = ".dds"
    filter_glob: StringProperty(default="*.dds", options={'HIDDEN'})

    id : bpy.props.IntProperty(options={'HIDDEN'})

    def execute(self, context):
        changed_identifier = getWTAItemByID(context, self.id).texture_identifier

        fdir = self.properties.filepath
        for item in context.scene.WTAMaterials:
            if item.texture_identifier == changed_identifier:
                item.texture_path = fdir

        return{'FINISHED'}

def defaultColorspace(mapType: str) -> str:
    return "sRGB" if any(hint in mapType for hint in ("Albedo", "Color", "EnvMap", "Irradiance")) else "Non-Color"

def loadSyncedImage(path: str, colorspace: str, loaded: dict) -> bpy.types.Image:
    key = (os.path.normcase(os.path.abspath(bpy.path.abspath(path))), colorspace)
    if key not in loaded:
        image = next((image for image in bpy.data.images
                      if image.source == "FILE" and image.colorspace_settings.name == colorspace
                      and os.path.normcase(os.path.abspath(bpy.path.abspath(image.filepath))) == key[0]), None)
        if image is None:
            image = bpy.data.images.load(path, check_existing=False)
            image.colorspace_settings.name = colorspace
        else:
            image.reload()
        loaded[key] = image
    return loaded[key]

def replaceWithImageNode(tree: bpy.types.NodeTree, node: bpy.types.Node, image: bpy.types.Image):
    imageNode = tree.nodes.new("ShaderNodeTexImage")
    imageNode.location = node.location
    imageNode.parent = node.parent
    imageNode.label = node.label
    imageNode.hide = node.hide
    imageNode.image = image
    for link in list(tree.links):
        if link.to_node == node and link.to_socket.name == "Vector":
            tree.links.new(link.from_socket, imageNode.inputs["Vector"])
        elif link.from_node == node:
            tree.links.new(imageNode.outputs.get(link.from_socket.name, imageNode.outputs["Color"]), link.to_socket)
    tree.nodes.remove(node)

class SyncBlenderMaterials(bpy.types.Operator):
    '''Sync the texture of Blender's materials to these'''
    bl_idname = "na.sync_blender_materials"
    bl_label = "Sync Blender Materials"
    bl_options = {"UNDO"}

    def execute(self, context):
        usedMaterials = {mat.name: mat for mat in getUsedMaterials() if mat is not None and mat.node_tree is not None}
        loaded = {}
        renamedUvMaps = set()
        synced = 0
        missing = []
        for item in context.scene.WTAMaterials:
            if item.texture_path in ("None", "") or item.parent_mat not in usedMaterials:
                continue
            if not os.path.isfile(bpy.path.abspath(item.texture_path)):
                missing.append(item.texture_path)
                continue
            mat = usedMaterials[item.parent_mat]
            nodes = mat.node_tree.nodes

            # Rename used uv maps
            if mat.name not in renamedUvMaps:
                renamedUvMaps.add(mat.name)
                uv_nodes_count = 0
                while getNodeWithLabel(nodes, "UV" + str(uv_nodes_count + 1)):
                    uv_nodes_count += 1
                for obj in getAllObjectsWithMaterial("WMB", mat.name):
                    for uv_index in range(min(uv_nodes_count, len(obj.data.uv_layers))):
                        obj.data.uv_layers[uv_index].name = "UVMap" + str(uv_index + 1)

            matching = [node for node in nodes if node.label == item.texture_map_type]
            for node in matching:
                if node.type == "TEX_IMAGE":
                    colorspace = node.image.colorspace_settings.name if node.image is not None else defaultColorspace(item.texture_map_type)
                    node.image = loadSyncedImage(item.texture_path, colorspace, loaded)
                elif node.type == "GROUP":
                    replaceWithImageNode(mat.node_tree, node, loadSyncedImage(item.texture_path, defaultColorspace(item.texture_map_type), loaded))
            synced += len(matching)
            if not matching and "Principled BSDF" in nodes:
                # add new texture node
                node = nodes.new("ShaderNodeTexImage")
                node.label = item.texture_map_type
                node.image = loadSyncedImage(item.texture_path, defaultColorspace(item.texture_map_type), loaded)
                synced += 1
                # link up
                if "Albedo" in node.label:
                    mat.node_tree.links.new(node.outputs[0], nodes["Principled BSDF"].inputs["Base Color"])
                elif "Alpha" in node.label:
                    mat.node_tree.links.new(node.outputs[0], nodes["Principled BSDF"].inputs["Alpha"])
                else:
                    print("Unhandled texture map type:", node.label)

        if missing:
            self.report({"WARNING"}, f"Synced {synced} texture node{'s' if synced != 1 else ''}; {len(missing)} texture file{'s' if len(missing) != 1 else ''} not found, e.g. {missing[0]}")
        else:
            self.report({"INFO"}, f"Synced {synced} texture node{'s' if synced != 1 else ''}")
        return {'FINISHED'}

class SyncMaterialIdentifiers(bpy.types.Operator):
    '''Sync the texture identifiers of materials to these'''
    bl_idname = "na.sync_material_identifiers"
    bl_label = "Sync Identifiers in Materials"
    bl_options = {"UNDO"}

    def execute(self, context):
        for item in context.scene.WTAMaterials:
            for mat in getUsedMaterials():
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
    bl_options = {"UNDO"}

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
    bl_options = {"UNDO"}

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
    '''Open a DDS file for the Texture Replacer'''
    bl_idname = "na.texture_filepath_selector"
    bl_label = "Open File"
    bl_options = {"UNDO"}

    filename_ext = ".dds"
    filter_glob: StringProperty(default="*.dds", options={'HIDDEN'})

    def execute(self, context):
        context.scene.ReplaceTexturePath = self.properties.filepath

        return{'FINISHED'}

class MassTextureReplacer(bpy.types.Operator):
    '''Replace all texture paths that match set id'''
    bl_idname = "na.mass_texture_replacer"
    bl_label = "Replace Textures"
    bl_options = {"UNDO"}

    def execute(self, context):
        replacedTextures = 0

        searchId = context.scene.ReplaceTextureName
        replaceId = context.scene.NewTextureName
        replacePath = context.scene.ReplaceTexturePath

        if not searchId:
            self.report({"ERROR"}, "Empty Search Identifier not allowed!")
            return{"CANCELLED"}

        for item in context.scene.WTAMaterials:
            if not textureMatchesSearch(item, searchId, newTexture=replacePath):
                continue

            replacedTextures += 1
            if replaceId:
                item.texture_identifier = replaceId
            if replacePath:
                item.texture_path = replacePath

        self.report({"INFO"}, f"Replaced {replacedTextures} texture{'s' if replacedTextures != 1 else ''}")
        return{'FINISHED'}

CORE_TEXTURES_2D = [
    ("4e9c16f4", "White", "32x32 plain white. The game's default light map and mask texture"),
    ("5864a24f", "White (8x8)", "8x8 plain white"),
    ("132ed5c3", "Black", "8x8 plain black"),
    ("7fd4929a", "Detail Noise Normal", "128x128 fine noise normal map, the game's default detail normal"),
    ("6b4c494d", "UV Checker Grid", "256x256 labelled colour grid, a debug placeholder"),
    ("5ff85fe8", "Colour Grading LUT (Neutral)", "256x16 neutral 16x16x16 colour lookup table"),
    ("04409bc2", "Falloff Gradient", "512x512 radial gradient from black to light grey"),
    ("0ee619dc", "Dither Pattern 1", "64x64 black and white dither pattern"),
    ("459fb4d0", "Dither Pattern 2", "64x64 black and white dither pattern"),
    ("40ec4ff8", "Dither Pattern 3", "64x64 black and white dither pattern"),
    ("6f484148", "Dither Pattern 4", "64x64 black and white dither pattern"),
]
CORE_TEXTURES_CUBE = [
    ("1fbc0984", "Desert Sky", "128 px cube map of a sandy desert under a blue sky, the game's default environment and irradiance map"),
    ("3f44a76d", "Overcast Sky (Blurred)", "128 px blurred grey-blue sky cube map"),
    ("21d3f88f", "Dusk Sky (Blurred)", "64 px blurred dark blue sky cube map"),
    ("2c96a3cb", "Grey Gradient", "32 px grey cube map, lighter above than below"),
    ("5b91935d", "Light Grey Gradient (No Alpha)", "32 px light grey cube map with zero alpha"),
    ("359ff271", "Studio Lights", "32 px grey cube map with bright window-like panels"),
    ("3c3cad4d", "Black With Light Spots", "64 px black cube map with a few soft bright spots"),
    ("4d9109fe", "Mid Grey", "8 px flat 50% grey cube map"),
    ("32f23668", "Dark Grey", "32 px flat dark grey cube map"),
    ("4298c2e7", "Black", "32 px flat black cube map"),
]

def isCubeTextureSlot(mapType: str) -> bool:
    return "EnvMap" in mapType or "Irradiance" in mapType

CORE_TEXTURE_ITEMS = {
    cube: [(identifier, f"{name} ({identifier})", description) for identifier, name, description in textures]
    for cube, textures in ((False, CORE_TEXTURES_2D), (True, CORE_TEXTURES_CUBE))
}

def coreTextureItems(self, context):
    return CORE_TEXTURE_ITEMS[self.cube]

class UseCoreTexture(bpy.types.Operator):
    bl_idname = "na.use_core_texture"
    bl_label = "Core Textures"
    bl_description = "Use one of the game's built-in core textures for this slot. They're always loaded, so nothing gets packed"
    bl_options = {"UNDO", "INTERNAL"}

    id: bpy.props.IntProperty()
    cube: bpy.props.BoolProperty()
    texture: bpy.props.EnumProperty(name="Core Texture", items=coreTextureItems)

    def invoke(self, context, event):
        item = getWTAItemByID(context, self.id)
        if item is None:
            return {"CANCELLED"}
        identifiers = [entry[0] for entry in (CORE_TEXTURES_CUBE if self.cube else CORE_TEXTURES_2D)]
        if item.texture_identifier.lower() in identifiers:
            self.texture = item.texture_identifier.lower()
        return context.window_manager.invoke_props_dialog(self, width=360)

    def draw(self, context):
        item = getWTAItemByID(context, self.id)
        layout = self.layout
        if item is not None:
            layout.label(text=f"{item.texture_map_type} in {item.parent_mat}")
        layout.column().prop(self, "texture", expand=True)

    def execute(self, context):
        item = getWTAItemByID(context, self.id)
        if item is None:
            return {"CANCELLED"}
        item.texture_identifier = self.texture
        item.texture_path = "None"
        mat = bpy.data.materials.get(item.parent_mat)
        if mat is not None and item.texture_map_type in mat:
            mat[item.texture_map_type] = self.texture
        self.report({"INFO"}, f"{item.texture_map_type} in {item.parent_mat} now uses core texture {self.texture}")
        return {"FINISHED"}

class SharedTextureInfo(bpy.types.Operator):
    bl_idname = "na.shared_texture_info"
    bl_label = "Shared Texture"
    bl_options = {"INTERNAL"}

    @classmethod
    def description(cls, context, properties):
        if context.scene.bSkipSharedTextures:
            return ("Shared texture: this file is inside one of the texture directories in the add-on preferences, "
                    "so it won't be exported into the WTA/WTP (Skip Exporting Shared Textures is on)")
        return ("Shared texture: this file is inside one of the texture directories in the add-on preferences. "
                "It will still be exported, because Skip Exporting Shared Textures is off")

    def execute(self, context):
        self.report({"INFO"}, self.description(context, None))
        return {"FINISHED"}

def drawSharedTextureIcon(row, item):
    if isSharedTexture(item.texture_identifier, item.texture_path):
        row.operator(SharedTextureInfo.bl_idname, icon="LINKED", text="", emboss=False)
    else:
        row.label(text="", icon="BLANK1")

class WTA_WTP_PT_Export(bpy.types.Panel):
    bl_label = "NieR:Automata WTP/WTA Textures"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "output"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.ui_units_x = .5
        row.scale_y = 1.5
        row.operator("na.get_wta_materials")
        row.operator("na.get_new_wta_materials")

        row = layout.row()
        row.scale_y = 1.25
        row.operator("na.assign_original")

        row = layout.row()
        row.scale_y = 1.5
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

        layout.prop(context.scene, "bSkipSharedTextures")
        layout.prop(context.scene, "bFilterToSelected")

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
            row.operator("na.texture_filepath_selector", icon="FILEBROWSER", text="")
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
        selectedMaterials = None
        if context.scene.bFilterToSelected:
            selectedMaterials = {slot.material.name for obj in context.selected_objects for slot in obj.material_slots if slot.material is not None}
        loaded_mats = []
        for item in context.scene.WTAMaterials:
            # Skip if this texture has no Blender material (is thus manual texture)
            if item.parent_mat == "":
                continue
            if selectedMaterials is not None and item.parent_mat not in selectedMaterials:
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
            row.operator("na.filepath_selector", icon="FILEBROWSER", text="").id = item.id
            coreOp = row.operator(UseCoreTexture.bl_idname, icon="TEXTURE", text="")
            coreOp.id = item.id
            coreOp.cube = isCubeTextureSlot(item.texture_map_type)
            drawSharedTextureIcon(row, item)

            loaded_mats.append(item.parent_mat)

        if len(loaded_mats) == 0:
            if selectedMaterials is not None:
                layout.label(text="Select objects in the 3D viewport to list their materials" if not context.selected_objects
                             else "The selected objects use none of these materials", icon="INFO")
            else:
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
            row.operator("na.filepath_selector", icon="FILEBROWSER", text="").id = item.id
            drawSharedTextureIcon(row, item)
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
    bpy.utils.register_class(SharedTextureInfo)
    bpy.utils.register_class(UseCoreTexture)

    bpy.types.Scene.WTAMaterials = bpy.props.CollectionProperty(type=WTAItems)
    bpy.types.Scene.bFilterToSelected = bpy.props.BoolProperty(
        name = "Filter To Selected",
        default = False,
        description = "Only list the materials of the objects selected in the 3D viewport",
    )
    bpy.types.Scene.bSkipSharedTextures = bpy.props.BoolProperty(
        name = "Skip Exporting Shared Textures",
        default = True,
        description = "Don't export textures whose file is inside one of the texture directories in the add-on preferences into the WTA/WTP; the game is expected to have them already",
    )
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
    bpy.utils.unregister_class(SharedTextureInfo)
    bpy.utils.unregister_class(UseCoreTexture)

    del bpy.types.Scene.WTAMaterials
    del bpy.types.Scene.bSkipSharedTextures
    del bpy.types.Scene.bFilterToSelected
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