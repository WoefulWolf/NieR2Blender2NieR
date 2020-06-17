import bpy
import os.path
from .wta_wtp_ui_manager import ShowMessageBox

def generate(context):
    wta_data = context.scene.WTAMaterials

    identifiers_array = []
    texture_paths_array = []
    albedo_indexes = []

    true_index = 0
    for index, texture in enumerate(wta_data):
        # Avoid duplicates
        if texture.texture_identifier in identifiers_array or texture.texture_path == 'None':
            continue

        # Assign Identifier.
        identifiers_array.append(texture.texture_identifier)

        # Check if path is valid and assign.
        if texture.texture_path != 'None' and not texture.texture_path.lower().endswith('.dds'):
            print('[!] WTA Export Error: A texture in material', texture.parent_mat, 'does not have a valid path assigned.')
            ShowMessageBox(texture.parent_mat + ' does not have a valid texture assigned to ' + texture.texture_map_type, 'WTA Export Error', 'ERROR') 
            return None, None, None

        texture_paths_array.append(texture.texture_path)

        # Assign Albedo & EnvMap Indexes
        if texture.texture_map_type in ['g_AlbedoMap', 'g_EnvMap']:
            albedo_indexes.append(true_index)
        
        true_index += 1

    return identifiers_array, texture_paths_array, albedo_indexes