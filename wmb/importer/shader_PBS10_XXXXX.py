import bpy

from ...utils.nodes import (grid_location, add_node, connect, combine_color, separate_color, math_node, mix_node,
                            group_node, parameter_node, texture_node, uv_node, material_output,
                            linear_to_srgb, uv_tiling, tangent_normal, layer_blend, shading, surface)


# material_array = [material_name, textures, uniforms, shader_name, technique_name, parameterGroups]
def pbs10_xxxxx(material: bpy.types.Material, material_array, texture_dir: str):
    tree = material.node_tree

    def value(name, default, x, y):
        return parameter_node(material, name, default, grid_location(x, y)).outputs[0]

    uv_1 = uv_node(tree, 'UVMap1', grid_location(0, 0))
    uv_2 = uv_node(tree, 'UVMap2', grid_location(0, 4))
    layer_uvs = [group_node(tree, uv_tiling(), {
        'UV': layer_uv,
        'X': value('g_MaterialTile%d_X' % (i + 1), 1.0, 0, 1 + i * 2),
        'Y': value('g_MaterialTile%d_Y' % (i + 1), 1.0, 0, 2 + i * 2),
    }, grid_location(1, i * 3)).outputs['UV'] for i, layer_uv in enumerate((uv_1, uv_2, uv_2))]
    uv_mask = mix_node(tree, 'Vector', value('g_UV2Use', 0.0, 0, 9), uv_1, uv_2, location=grid_location(1, 9))

    albedos = [texture_node(material, texture_dir, 'g_AlbedoMap%d' % (i + 1), grid_location(2, i), layer_uvs[i]) for i in range(3)]
    normals = [texture_node(material, texture_dir, 'g_NormalMap%d' % (i + 1), grid_location(2, 12 + i), layer_uvs[i], non_color=True) for i in range(3)]
    mask = texture_node(material, texture_dir, 'g_MaskMap', grid_location(2, 9), uv_mask, non_color=True)
    light_map = texture_node(material, texture_dir, 'g_LightMap', grid_location(2, 10), uv_2, non_color=True)
    metallic_map, glossiness_map, occlusion_map = separate_color(tree, mask.outputs['Color'], grid_location(3, 9))[:3]

    vertex_color = add_node(tree, 'ShaderNodeVertexColor', grid_location(2, -3))
    vertex_color.layer_name = 'Col'
    stored = group_node(tree, linear_to_srgb(), {'Color': vertex_color.outputs['Color']}, grid_location(3, -3)).outputs['Color']
    vertex = separate_color(tree, stored, grid_location(4, -3))
    rate = value('g_InterpolationRate', 1.0, 3, -5)
    weights = []
    for i in range(2):
        height = albedos[i].outputs['Alpha']
        weight = add_node(tree, 'ShaderNodeMapRange', grid_location(5, -4 + i))
        connect(tree, weight.inputs['Value'], vertex[i])
        connect(tree, weight.inputs['From Min'], height)
        connect(tree, weight.inputs['From Max'], math_node(tree, 'ADD', height, rate, location=grid_location(4, -5 + i)))
        weights.append(weight.outputs['Result'])

    def blend(type, layers, y):
        return group_node(tree, layer_blend(type), {
            'Weight 2': weights[0],
            'Weight 3': weights[1],
            'Layer 1': layers[0],
            'Layer 2': layers[1],
            'Layer 3': layers[2],
        }, grid_location(6, y)).outputs['Result']

    albedo_color = combine_color(tree, *(value('g_AlbedoColor_' + axis, 1.0, 6, -9 + i) for i, axis in enumerate('XYZ')), location=grid_location(7, -8))
    color = mix_node(tree, 'Color', value('g_bAlbedoOverWrite', 0.0, 7, -6), blend('Color', [albedo.outputs['Color'] for albedo in albedos], 0), albedo_color, location=grid_location(8, 0))
    glossiness_1 = mix_node(tree, 'Float', value('g_bGlossinessOverWrite', 0.0, 4, 4), glossiness_map, value('g_Glossiness1', 0.0, 4, 5), location=grid_location(5, 4))
    glossiness = blend('Float', [glossiness_1, value('g_Glossiness2', 0.0, 5, 5), value('g_Glossiness3', 0.0, 5, 6)], 4)
    metallic_1 = mix_node(tree, 'Float', value('g_bMetalicOverWrite', 0.0, 4, 7), metallic_map, value('g_Metallic1', 0.0, 4, 8), location=grid_location(5, 7))
    metallic = blend('Float', [metallic_1, value('g_Metallic2', 0.0, 5, 8), value('g_Metallic3', 0.0, 5, 9)], 7)
    roughness = math_node(tree, 'SUBTRACT', 1.0, glossiness, location=grid_location(8, 4))

    occlusion = occlusion_map if mask.image is not None else 1.0
    if light_map.image is not None:
        light_map_occlusion = separate_color(tree, light_map.outputs['Color'], grid_location(3, 10))[1]
        occlusion = math_node(tree, 'MULTIPLY', occlusion, mix_node(tree, 'Float', value('g_UseOcclusionMap', 0.0, 4, 10), 1.0, light_map_occlusion, location=grid_location(5, 10)), location=grid_location(6, 10))

    shading_normal = group_node(tree, tangent_normal(), {
        'Normal Map': blend('Color', [normal.outputs['Color'] for normal in normals], 12),
        'Use Normal Map': value('g_UseNormalMap', 1.0, 6, 15),
    }, grid_location(7, 12)).outputs['Normal']

    lit = group_node(tree, shading(), {
        'Color': color,
        'Metallic': metallic,
        'Roughness': roughness,
        'Normal': shading_normal,
        'Specular Normal': shading_normal,
    }, grid_location(9, 0))

    shader = group_node(tree, surface(), {
        'Shader': lit.outputs['BSDF'],
        'Occlusion': occlusion,
    }, grid_location(10, 0)).outputs['Shader']
    material_output(tree, shader, grid_location(11, 0))

    return material
