import bpy

from ...utils.nodes import (grid_location, add_node, connect, combine_color, separate_color, math_node, mix_node,
                            group_node, parameter_node, texture_node, uv_node, material_output,
                            linear_to_srgb, uv_tiling, uv_scroll, tangent_normal, shading, surface)


def two_layer(material, texture_dir: str, blend_alpha_switch: bool):
    tree = material.node_tree

    def value(name, default, x, y):
        return parameter_node(material, name, default, grid_location(x, y)).outputs[0]

    def scroll(uv, name, x, y):
        speed_x, speed_y = value(name + '_X', 0.0, x, y + 1), value(name + '_Y', 0.0, x, y + 2)
        return group_node(tree, uv_scroll(), {'UV': uv, 'X': speed_x, 'Y': speed_y}, grid_location(x + 1, y)).outputs['UV'], (speed_x, speed_y)

    def tiled(uv, name, x, y):
        return group_node(tree, uv_tiling(), {
            'UV': uv,
            'X': value(name + '_X', 1.0, x, y + 1),
            'Y': value(name + '_Y', 1.0, x, y + 2),
        }, grid_location(x + 1, y)).outputs['UV']

    uv_1 = uv_node(tree, 'UVMap1', grid_location(0, 0))
    uv_2 = uv_node(tree, 'UVMap2', grid_location(0, 6))
    layer_uv_1, speeds_1 = scroll(tiled(uv_1, 'g_MaterialTile1', 0, 0), 'g_UvAnimation1', 2, 0)
    layer_uv_2, _ = scroll(tiled(uv_2, 'g_MaterialTile2', 0, 3), 'g_UvAnimation2', 2, 3)
    detail_uvs = [scroll(tiled(uv_2, 'g_DetailNormalTile%d' % (i + 1), 0, 14 + i * 3), 'g_DN_Animation%d' % (i + 1), 2, 14 + i * 3)[0] for i in range(2)]
    uv_mask = mix_node(tree, 'Vector', value('g_UV2Use', 0.0, 0, 7), uv_1, uv_2, location=grid_location(1, 7))
    uv_mask = group_node(tree, uv_scroll(), {'UV': uv_mask, 'X': speeds_1[0], 'Y': speeds_1[1]}, grid_location(3, 7)).outputs['UV']

    albedos = [texture_node(material, texture_dir, 'g_AlbedoMap%d' % (i + 1), grid_location(4, i * 3), uv) for i, uv in enumerate((layer_uv_1, layer_uv_2))]
    mask = texture_node(material, texture_dir, 'g_MaskMap', grid_location(4, 7), uv_mask, non_color=True)
    light_map = texture_node(material, texture_dir, 'g_LightMap', grid_location(4, 8), uv_2, non_color=True)
    normals = [texture_node(material, texture_dir, 'g_NormalMap%d' % (i + 1), grid_location(4, 10 + i), uv, non_color=True) for i, uv in enumerate((layer_uv_1, layer_uv_2))]
    details = [texture_node(material, texture_dir, 'g_DetailNormalMap', grid_location(4, 14 + i * 3), uv, non_color=True) for i, uv in enumerate(detail_uvs)]
    metallic_map, glossiness_map, occlusion_map = separate_color(tree, mask.outputs['Color'], grid_location(5, 7))[:3]

    vertex_color = add_node(tree, 'ShaderNodeVertexColor', grid_location(4, -3))
    vertex_color.layer_name = 'Col'
    stored = group_node(tree, linear_to_srgb(), {'Color': vertex_color.outputs['Color']}, grid_location(5, -3)).outputs['Color']
    vertex = separate_color(tree, stored, grid_location(6, -3))
    height = albedos[0].outputs['Alpha']
    if blend_alpha_switch:
        height = mix_node(tree, 'Float', value('g_DisableBlendAlpha', 0.0, 5, -5), height, 0.0, location=grid_location(6, -4))
    difference = math_node(tree, 'SUBTRACT', vertex[0], height, location=grid_location(7, -3))
    weight = math_node(tree, 'DIVIDE', difference, value('g_InterpolationRate', 1.0, 7, -5), location=grid_location(8, -3), clamp=True)
    weight = math_node(tree, 'MULTIPLY', weight, albedos[1].outputs['Alpha'], location=grid_location(9, -3))

    def blend(type, first, second, y):
        return mix_node(tree, type, weight, first, second, location=grid_location(10, y))

    albedo_color = combine_color(tree, *(value('g_AlbedoColor_' + axis, 1.0, 10, -9 + i) for i, axis in enumerate('XYZ')), location=grid_location(11, -8))
    color = mix_node(tree, 'Color', value('g_bAlbedoOverWrite', 0.0, 11, -6), blend('Color', albedos[0].outputs['Color'], albedos[1].outputs['Color'], 0), albedo_color, location=grid_location(12, 0))
    glossiness_1 = mix_node(tree, 'Float', value('g_bGlossinessOverWrite', 0.0, 6, 5), glossiness_map, value('g_Glossiness1', 0.0, 6, 6), location=grid_location(7, 5))
    glossiness = blend('Float', glossiness_1, value('g_Glossiness2', 0.0, 9, 6), 5)
    metallic_1 = mix_node(tree, 'Float', value('g_bMetalicOverWrite', 0.0, 6, 8), metallic_map, value('g_Metallic1', 0.0, 6, 9), location=grid_location(7, 8))
    metallic = blend('Float', metallic_1, value('g_Metallic2', 0.0, 9, 9), 8)
    roughness = math_node(tree, 'SUBTRACT', 1.0, glossiness, location=grid_location(12, 5))

    occlusion = occlusion_map if mask.image is not None else 1.0
    if light_map.image is not None:
        light_map_occlusion = separate_color(tree, light_map.outputs['Color'], grid_location(5, 8))[1]
        occlusion = math_node(tree, 'MULTIPLY', occlusion, mix_node(tree, 'Float', value('g_UseOcclusionMap', 0.0, 6, 11), 1.0, light_map_occlusion, location=grid_location(7, 11)), location=grid_location(8, 11))

    shading_normal = group_node(tree, tangent_normal(), {
        'Normal Map': blend('Color', normals[0].outputs['Color'], normals[1].outputs['Color'], 13),
        'Use Normal Map': value('g_UseNormalMap', 1.0, 10, 15),
        'Detail Normal Map': blend('Color', details[0].outputs['Color'], details[1].outputs['Color'], 16),
        'Detail Strength': blend('Float', mask.outputs['Alpha'], 1.0, 17),
        'Use Detail Normal Map': value('g_UseDetailNormalMap', 0.0, 10, 18),
    }, grid_location(11, 13)).outputs['Normal']

    lit = group_node(tree, shading(), {
        'Color': color,
        'Metallic': metallic,
        'Roughness': roughness,
        'Normal': shading_normal,
        'Specular Normal': shading_normal,
    }, grid_location(13, 0)).outputs['BSDF']
    return value, vertex, albedos, lit, occlusion


def pbs11_xxxxx(material: bpy.types.Material, material_array, texture_dir: str):
    tree = material.node_tree
    _, _, _, lit, occlusion = two_layer(material, texture_dir, True)
    shader = group_node(tree, surface(), {
        'Shader': lit,
        'Occlusion': occlusion,
    }, grid_location(14, 0)).outputs['Shader']
    material_output(tree, shader, grid_location(15, 0))

    return material
