import string

from ...utils.util import ShowMessageBox


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

        # Check if identifier is 8 chars long
        if len( texture.texture_identifier) != 8:
            print('[!] WTA/WTP Export Error: A texture identifier is not characters long.')
            ShowMessageBox('A texture identifier is not characters long.', 'WTA/WTP Export Error', 'ERROR')
            return None, None, None

        # Check if identifier is valid hex
        if not all(c in string.hexdigits for c in texture.texture_identifier):
            print('[!] WTA/WTP Export Error: A texture identifier contains a non-hex character.')
            ShowMessageBox('A texture identifier contains a non-hex character.', 'WTA/WTP Export Error', 'ERROR')
            return None, None, None

        # Assign Identifier.
        identifiers_array.append(texture.texture_identifier)

        # Check if path is valid and assign.
        if not texture.texture_path.lower().endswith('.dds'):
            if texture.parent_mat == "":
                print('[!] WTA/WTP Export Error: A manual ' + texture.texture_map_type + ' texture does not have a valid texture assigned.')
                ShowMessageBox('A manual ' + texture.texture_map_type + ' texture does not have a valid texture assigned.', 'WTA/WTP Export Error', 'ERROR') 
            else:
                print('[!] WTA/WTP Export Error: A texture in material', texture.parent_mat, 'does not have a valid path assigned.')
                ShowMessageBox(texture.parent_mat + ' does not have a valid texture assigned to ' + texture.texture_map_type, 'WTA/WTP Export Error', 'ERROR') 
            return None, None, None

        texture_paths_array.append(texture.texture_path)

        # Assign Albedo & EnvMap Indexes
        if texture.texture_map_type in ['albedoMap0', 'tex9']:
            albedo_indexes.append(true_index)
        
        true_index += 1

    return identifiers_array, texture_paths_array, albedo_indexes