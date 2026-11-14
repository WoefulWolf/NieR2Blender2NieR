import bpy

from ...utils.nodes import (grid_location, combine_color, separate_color, math_node, mix_node, group_node,
                            parameter_node, texture_node, uv_node, material_output,
                            uv_tiling, tangent_normal, shading, surface)


# material_array = [material_name, textures, uniforms, shader_name, technique_name, parameterGroups]
def pbs00_xxxxx(material: bpy.types.Material, material_array, texture_dir: str):
    tree = material.node_tree

    def value(name, default, x, y):
        return parameter_node(material, name, default, grid_location(x, y)).outputs[0]

    uv_2 = uv_node(tree, 'UVMap2', grid_location(0, 10))
    uv = group_node(tree, uv_tiling(), {
        'UV': uv_node(tree, 'UVMap1', grid_location(0, 0)),
        'X': value('g_Tile_X', 1.0, 0, 1),
        'Y': value('g_Tile_Y', 1.0, 0, 2),
    }, grid_location(1, 0)).outputs['UV']
    uv_detail = group_node(tree, uv_tiling(), {
        'UV': uv_2,
        'X': value('g_DetailNormalTile_X', 1.0, 0, 11),
        'Y': value('g_DetailNormalTile_Y', 1.0, 0, 12),
    }, grid_location(1, 10)).outputs['UV']
    uv_mask = mix_node(tree, 'Vector', value('g_UV2Use', 0.0, 0, 4), uv, uv_2, location=grid_location(1, 4))

    albedo = texture_node(material, texture_dir, 'g_AlbedoMap', grid_location(2, 0), uv)
    mask = texture_node(material, texture_dir, 'g_MaskMap', grid_location(2, 2), uv_mask, non_color=True)
    light_map = texture_node(material, texture_dir, 'g_LightMap', grid_location(2, 3), uv_2, non_color=True)
    normal = texture_node(material, texture_dir, 'g_NormalMap', grid_location(2, 9), uv, non_color=True)
    detail_normal = texture_node(material, texture_dir, 'g_DetailNormalMap', grid_location(2, 10), uv_detail, non_color=True)
    metallic_map, glossiness_map, occlusion_map = separate_color(tree, mask.outputs['Color'], grid_location(3, 2))[:3]

    albedo_color = combine_color(tree, *(value('g_AlbedoColor_' + axis, 1.0, 3, -4 + i) for i, axis in enumerate('XYZ')), location=grid_location(4, -3))
    color = mix_node(tree, 'Color', value('g_bAlbedoOverWrite', 0.0, 4, -1), albedo.outputs['Color'], albedo_color, location=grid_location(5, 0))
    glossiness = mix_node(tree, 'Float', value('g_bGlossinessOverWrite', 0.0, 4, 4), glossiness_map, value('g_Glossiness', 0.0, 4, 5), location=grid_location(5, 4))
    metallic = mix_node(tree, 'Float', value('g_bMetalicOverWrite', 0.0, 4, 6), metallic_map, value('g_Metallic', 0.0, 4, 7), location=grid_location(5, 6))
    roughness = math_node(tree, 'SUBTRACT', 1.0, glossiness, location=grid_location(6, 4))

    occlusion = occlusion_map if mask.image is not None else 1.0
    if light_map.image is not None:
        light_map_occlusion = separate_color(tree, light_map.outputs['Color'], grid_location(3, 3))[1]
        occlusion = math_node(tree, 'MULTIPLY', occlusion, mix_node(tree, 'Float', value('g_UseOcclusionMap', 0.0, 4, 3), 1.0, light_map_occlusion, location=grid_location(5, 3)), location=grid_location(6, 3))

    shading_normal = group_node(tree, tangent_normal(), {
        'Normal Map': normal.outputs['Color'],
        'Use Normal Map': value('g_UseNormalMap', 1.0, 3, 8),
        'Detail Normal Map': detail_normal.outputs['Color'],
        'Detail Strength': mask.outputs['Alpha'],
        'Use Detail Normal Map': value('g_UseDetailNormalMap', 0.0, 3, 11),
    }, grid_location(4, 9)).outputs['Normal']

    lit = group_node(tree, shading(), {
        'Color': color,
        'Metallic': metallic,
        'Roughness': roughness,
        'Normal': shading_normal,
        'Specular Normal': shading_normal,
    }, grid_location(7, 0))

    shader = group_node(tree, surface(), {
        'Shader': lit.outputs['BSDF'],
        'Occlusion': occlusion,
        'Alpha': albedo.outputs['Alpha'],
        '1-Bit Mask': value('g_1BitMask', 0.0, 7, -3),
    }, grid_location(8, 0)).outputs['Shader']
    material_output(tree, shader, grid_location(9, 0))

    return material
