import bpy

from ...utils.nodes import (grid_location, add_node, combine_color, separate_color, math_node, mix_node, vector_math_node,
                            group_node, parameter_node, texture_node, uv_node, material_output, blended,
                            linear_to_srgb, uv_tiling, uv_scroll, tangent_normal, shading, surface,
                            water_opacity, water_surface)


def water(material, texture_dir: str, layered: bool):
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
    vertex_color = add_node(tree, 'ShaderNodeVertexColor', grid_location(4, -3))
    vertex_color.layer_name = 'Col'
    stored = group_node(tree, linear_to_srgb(), {'Color': vertex_color.outputs['Color']}, grid_location(5, -3)).outputs['Color']
    vertex = separate_color(tree, stored, grid_location(6, -3))

    if layered:
        layer_uv_1, speeds_1 = scroll(tiled(uv_1, 'g_MaterialTile1', 0, 0), 'g_UvAnimation1', 2, 0)
        layer_uv_2, _ = scroll(tiled(uv_2, 'g_MaterialTile2', 0, 3), 'g_UvAnimation2', 2, 3)
        normal_uvs = [layer_uv_1] + [scroll(tiled(uv_2, 'g_NormalTile%d' % i, 0, 11 + i * 3), 'g_Normal_Animation%d' % i, 2, 11 + i * 3)[0] for i in (1, 2)]
        uv_mask = mix_node(tree, 'Vector', value('g_UV2Use', 0.0, 0, 7), uv_1, uv_2, location=grid_location(1, 7))
        uv_mask = group_node(tree, uv_scroll(), {'UV': uv_mask, 'X': speeds_1[0], 'Y': speeds_1[1]}, grid_location(3, 7)).outputs['UV']

        albedos = [texture_node(material, texture_dir, 'g_AlbedoMap%d' % (i + 1), grid_location(4, i * 3), uv) for i, uv in enumerate((layer_uv_1, layer_uv_2))]
        mask = texture_node(material, texture_dir, 'g_MaskMap', grid_location(4, 7), uv_mask, non_color=True)
        metallic_map, glossiness_map = separate_color(tree, mask.outputs['Color'], grid_location(5, 7))[:2]

        difference = math_node(tree, 'SUBTRACT', vertex[0], albedos[0].outputs['Alpha'], location=grid_location(7, -3))
        weight = math_node(tree, 'DIVIDE', difference, value('g_InterpolationRate', 1.0, 7, -5), location=grid_location(8, -3), clamp=True)
        weight = math_node(tree, 'MULTIPLY', weight, albedos[1].outputs['Alpha'], location=grid_location(9, -3))

        albedo_color = combine_color(tree, *(value('g_AlbedoColor_' + axis, 1.0, 10, -9 + i) for i, axis in enumerate('XYZ')), location=grid_location(11, -8))
        layers = mix_node(tree, 'Color', weight, albedos[0].outputs['Color'], albedos[1].outputs['Color'], location=grid_location(10, 0))
        color = mix_node(tree, 'Color', value('g_bAlbedoOverWrite', 0.0, 11, -6), layers, albedo_color, location=grid_location(12, 0))
        glossiness = mix_node(tree, 'Float', value('g_bGlossinessOverWrite', 0.0, 6, 5), glossiness_map, value('g_Glossiness1', 0.0, 6, 6), location=grid_location(7, 5))
        glossiness = mix_node(tree, 'Float', weight, glossiness, value('g_Glossiness2', 0.0, 9, 6), location=grid_location(10, 5))
        metallic = mix_node(tree, 'Float', value('g_bMetalicOverWrite', 0.0, 6, 8), metallic_map, value('g_Metallic1', 0.0, 6, 9), location=grid_location(7, 8))
        metallic = mix_node(tree, 'Float', weight, metallic, value('g_Metallic2', 0.0, 9, 9), location=grid_location(10, 8))
        opacity_mask = math_node(tree, 'MULTIPLY', albedos[0].outputs['Alpha'], vertex[2], location=grid_location(12, -3))
    else:
        normal_uvs = [uv_1, uv_2, uv_2]
        color = combine_color(tree, *(value('g_AlbedoColor_' + axis, 1.0, 10, -9 + i) for i, axis in enumerate('XYZ')), location=grid_location(12, 0))
        glossiness = value('g_Glossiness', 0.0, 10, 5)
        metallic = value('g_Metallic', 0.0, 10, 8)
        opacity_mask = vertex[2]

    normals = [texture_node(material, texture_dir, 'g_NormalMap%d' % (i + 1), grid_location(4, 11 + i * 3), uv, non_color=True) for i, uv in enumerate(normal_uvs)]
    summed = vector_math_node(tree, 'ADD', normals[0].outputs['Color'], vector_math_node(tree, 'MULTIPLY', normals[1].outputs['Color'], (1.0, 1.0, 0.0), location=grid_location(5, 14)), location=grid_location(6, 12))
    summed = vector_math_node(tree, 'ADD', summed, vector_math_node(tree, 'MULTIPLY', normals[2].outputs['Color'], (1.0, 1.0, 0.0), location=grid_location(5, 17)), location=grid_location(7, 12))
    summed = vector_math_node(tree, 'ADD', summed, (-1.5, -1.5, 0.0), location=grid_location(8, 12))
    calm = math_node(tree, 'SUBTRACT', 1.0, vertex_color.outputs['Alpha'], location=grid_location(8, 14))
    calm = combine_color(tree, calm, calm, 1.0, location=grid_location(9, 14))
    normal_map = vector_math_node(tree, 'MULTIPLY_ADD', summed, calm, (0.5, 0.5, 0.0), location=grid_location(10, 12))
    shading_normal = group_node(tree, tangent_normal(), {'Normal Map': normal_map}, grid_location(11, 12)).outputs['Normal']

    refraction = value('g_RefractBlend', 0.0, 12, 3)
    lit = group_node(tree, shading(), {
        'Color': vector_math_node(tree, 'SCALE', color, math_node(tree, 'SUBTRACT', 1.0, refraction, location=grid_location(12, 2)), location=grid_location(13, 1)),
        'Metallic': metallic,
        'Roughness': math_node(tree, 'SUBTRACT', 1.0, glossiness, location=grid_location(12, 5)),
        'Normal': shading_normal,
        'Specular Normal': shading_normal,
    }, grid_location(14, 0)).outputs['BSDF']

    fog = combine_color(tree, *(value('g_CamToSurfaceFogColor_' + axis, 0.0, 14, 3 + i) for i, axis in enumerate('XYZ')), location=grid_location(15, 3))
    surface_shader = group_node(tree, water_surface(), {
        'Shader': lit,
        'Refraction': refraction,
        'Fog Color': fog,
        'Fog Near': value('g_CamToSurfaceNearZ', 0.0, 14, 7),
        'Fog Far': value('g_CamToSurfaceFarZ', 10000.0, 14, 8),
    }, grid_location(16, 0)).outputs['Shader']

    opacity = group_node(tree, water_opacity(), {
        'Mask': opacity_mask,
        'Fresnel Exp U': value('g_FresnelExpU', 0.0, 15, -7),
        'Fresnel Exp V': value('g_FresnelExpV', 0.0, 15, -6),
        'Strength': value('g_TranslucentStrength', 1.0, 15, -5),
        'Power': value('g_TranslucentPow', 1.0, 15, -4),
    }, grid_location(16, -4)).outputs['Alpha']
    shader = group_node(tree, surface(), {
        'Shader': surface_shader,
        'Alpha': opacity,
        'Decal': 1.0,
    }, grid_location(17, 0)).outputs['Shader']
    material_output(tree, shader, grid_location(18, 0))
    blended(material)

    return material


def wtr00_xxxxx(material: bpy.types.Material, material_array, texture_dir: str):
    return water(material, texture_dir, True)
