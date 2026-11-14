import bpy

from ...utils.nodes import (grid_location, add_node, combine_color, separate_color, mix_node, group_node,
                            parameter_node, texture_node, uv_node, material_output,
                            uv_tiling, tangent_normal, fuzz, anisotropy, shading, surface)


# material_array = [material_name, textures, uniforms, shader_name, technique_name, parameterGroups]
def clt00_xxxxx(material: bpy.types.Material, material_array, texture_dir: str):
    tree = material.node_tree

    def value(name, default, x, y):
        return parameter_node(material, name, default, grid_location(x, y)).outputs[0]

    uv = group_node(tree, uv_tiling(), {
        'UV': uv_node(tree, 'UVMap1', grid_location(0, 0)),
        'X': value('g_Tile_X', 1.0, 0, 1),
        'Y': value('g_Tile_Y', 1.0, 0, 2),
    }, grid_location(1, 0)).outputs['UV']
    uv_detail = group_node(tree, uv_tiling(), {
        'UV': uv_node(tree, 'UVMap2', grid_location(0, 10)),
        'X': value('g_DetailNormalTile_X', 1.0, 0, 11),
        'Y': value('g_DetailNormalTile_Y', 1.0, 0, 12),
    }, grid_location(1, 10)).outputs['UV']

    albedo = texture_node(material, texture_dir, 'g_AlbedoMap', grid_location(2, 0), uv)
    mask = texture_node(material, texture_dir, 'g_MaskMap', grid_location(2, 1), uv, non_color=True)
    mask_2 = texture_node(material, texture_dir, 'g_MaskMap2', grid_location(2, 2), uv, non_color=True)
    normal = texture_node(material, texture_dir, 'g_NormalMap', grid_location(2, 9), uv, non_color=True)
    detail_normal = texture_node(material, texture_dir, 'g_DetailNormalMap', grid_location(2, 10), uv_detail, non_color=True)
    metallic_map, glossiness_map, occlusion_map = separate_color(tree, mask.outputs['Color'], grid_location(3, 1))[:3]
    anisotropy_mask, fuzz_mask = separate_color(tree, mask_2.outputs['Color'], grid_location(3, 2))[:2]

    albedo_color = combine_color(tree, *(value('g_AlbedoColor_' + axis, 1.0, 3, -4 + i) for i, axis in enumerate('XYZ')), location=grid_location(4, -3))
    color = mix_node(tree, 'Color', value('g_bAlbedoOverWrite', 0.0, 4, -1), albedo.outputs['Color'], albedo_color, location=grid_location(5, 0))
    glossiness = mix_node(tree, 'Float', value('g_bGlossinessOverWrite', 0.0, 4, 4), glossiness_map, value('g_Glossiness', 0.0, 4, 5), location=grid_location(5, 4))
    metallic = mix_node(tree, 'Float', value('g_bMetalicOverWrite', 0.0, 4, 6), metallic_map, value('g_Metallic', 0.0, 4, 7), location=grid_location(5, 6))

    shading_normal = group_node(tree, tangent_normal(), {
        'Normal Map': normal.outputs['Color'],
        'Use Normal Map': value('g_UseNormalMap', 1.0, 3, 8),
        'Detail Normal Map': detail_normal.outputs['Color'],
        'Detail Strength': mask.outputs['Alpha'],
        'Use Detail Normal Map': value('g_UseDetailNormalMap', 0.0, 3, 11),
    }, grid_location(4, 9)).outputs['Normal']

    fuzz_correction = combine_color(tree, *(value('g_FuzzColorCorrection_' + axis, 1.0, 5, -8 + i) for i, axis in enumerate('XYZ')), location=grid_location(6, -7))
    base_color = group_node(tree, fuzz(), {
        'Color': color,
        'Normal': shading_normal,
        'Fuzz Mask': fuzz_mask,
        'Exponent': value('g_FuzzExponent', 1.0, 6, -6),
        'Highlight': value('g_HilIghtIntensity', 1.0, 6, -5),
        'Mask Effective': value('g_FuzzMaskEffective', 0.0, 6, -4),
        'Reverse': value('g_FuzzReverse', 0.0, 6, -3),
        'Multiply': value('g_FuzzMul', 0.0, 6, -2),
        'Correction': fuzz_correction,
    }, grid_location(7, -3)).outputs['Color']

    highlight = group_node(tree, anisotropy(), {
        'Glossiness': glossiness,
        'Mask': anisotropy_mask,
        'Mode': value('g_AnisoLightMode', 0.0, 6, 2),
        'Mode 2': value('g_AnisoLightMode2', 0.0, 6, 3),
        'Anisotropic': value('g_Anisotropic', 0.0, 6, 4),
        'Anisotropic X': value('g_Anisotropic_X', 0.0, 6, 5),
        'Anisotropic Y': value('g_Anisotropic_Y', 0.0, 6, 6),
    }, grid_location(7, 3))

    tangent = add_node(tree, 'ShaderNodeTangent', grid_location(7, 9))
    tangent.direction_type = 'UV_MAP'
    tangent.uv_map = 'UVMap1'

    lit = group_node(tree, shading(), {
        'Color': base_color,
        'Metallic': metallic,
        'Roughness': highlight.outputs['Roughness'],
        'Anisotropy': highlight.outputs['Anisotropy'],
        'Rotation': highlight.outputs['Rotation'],
        'Normal': shading_normal,
        'Specular Normal': shading_normal,
        'Tangent': tangent.outputs['Tangent'],
    }, grid_location(8, 0))

    shader = group_node(tree, surface(), {
        'Shader': lit.outputs['BSDF'],
        'Occlusion': occlusion_map if mask.image is not None else 1.0,
        'Alpha': albedo.outputs['Alpha'],
        '1-Bit Mask': value('g_1BitMask', 0.0, 8, -3),
    }, grid_location(9, 0)).outputs['Shader']
    material_output(tree, shader, grid_location(10, 0))

    return material
