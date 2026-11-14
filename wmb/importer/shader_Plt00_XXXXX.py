import bpy

from ...utils.nodes import (grid_location, add_node, connect, combine_color, separate_color, math_node, mix_node,
                            group_node, parameter_node, blend_mode_driver, texture_node, uv_node, material_output,
                            linear_to_srgb, uv_tiling, tangent_normal, specular_lobe, surface, wind_sway)


# material_array = [material_name, textures, uniforms, shader_name, technique_name, parameterGroups]
def plt00_xxxxx(material: bpy.types.Material, material_array, texture_dir: str):
    tree = material.node_tree
    links = tree.links

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
    normal = texture_node(material, texture_dir, 'g_NormalMap', grid_location(2, 9), uv, non_color=True)
    detail_normal = texture_node(material, texture_dir, 'g_DetailNormalMap', grid_location(2, 10), uv_detail, non_color=True)
    metallic_map, glossiness_map, thickness_map = separate_color(tree, mask.outputs['Color'], grid_location(3, 2))[:3]

    albedo_color = combine_color(tree, *(value('g_AlbedoColor_' + axis, 1.0, 3, -4 + i) for i, axis in enumerate('XYZ')), location=grid_location(4, -3))
    color = mix_node(tree, 'Color', value('g_bAlbedoOverWrite', 0.0, 4, -1), albedo.outputs['Color'], albedo_color, location=grid_location(5, 0))
    glossiness = mix_node(tree, 'Float', value('g_bGlossinessOverWrite', 0.0, 4, 4), glossiness_map, value('g_Glossiness', 0.0, 4, 5), location=grid_location(5, 4))
    metallic = mix_node(tree, 'Float', value('g_bMetalicOverWrite', 0.0, 4, 6), metallic_map, value('g_Metallic', 0.0, 4, 7), location=grid_location(5, 6))
    roughness = math_node(tree, 'SUBTRACT', 1.0, glossiness, location=grid_location(6, 4))

    shading_normal = group_node(tree, tangent_normal(), {
        'Normal Map': normal.outputs['Color'],
        'Use Normal Map': value('g_UseNormalMap', 1.0, 3, 8),
        'Detail Normal Map': detail_normal.outputs['Color'],
        'Detail Strength': mask.outputs['Alpha'],
        'Use Detail Normal Map': value('g_UseDetailNormalMap', 0.0, 3, 11),
    }, grid_location(4, 9)).outputs['Normal']

    thickness = math_node(tree, 'MULTIPLY', thickness_map, value('g_Tickness', 1.0, 4, 2), location=grid_location(5, 2))
    thin = math_node(tree, 'SUBTRACT', 1.0, thickness, location=grid_location(6, 2))
    lut_samples = []
    for i, column in enumerate((0.999, 0.001)):
        lookup = add_node(tree, 'ShaderNodeCombineXYZ', grid_location(7, -6 + i * 2))
        lookup.inputs['X'].default_value = column
        connect(tree, lookup.inputs['Y'], thin)
        lut = texture_node(material, texture_dir, 'g_LUT', grid_location(8, -6 + i * 2), lookup.outputs[0], non_color=True)
        if lut.type == 'TEX_IMAGE':
            lut.extension = 'EXTEND'
        lut_samples.append(lut.outputs['Color'])

    diffuse = add_node(tree, 'ShaderNodeBsdfDiffuse', grid_location(10, -6), hide=False)
    connect(tree, diffuse.inputs['Color'], mix_node(tree, 'Color', 1.0, color, lut_samples[0], location=grid_location(9, -6), blend='MULTIPLY'))
    connect(tree, diffuse.inputs['Normal'], shading_normal)

    back = mix_node(tree, 'Color', 1.0, color, lut_samples[1], location=grid_location(9, -4), blend='MULTIPLY')
    translucent = add_node(tree, 'ShaderNodeBsdfTranslucent', grid_location(10, -3), hide=False)
    connect(tree, translucent.inputs['Color'], mix_node(tree, 'Color', thin, (0.0, 0.0, 0.0, 1.0), back, location=grid_location(9, -3)))
    connect(tree, translucent.inputs['Normal'], shading_normal)

    lobe = group_node(tree, specular_lobe(), {
        'Color': color,
        'Metallic': metallic,
        'Roughness': roughness,
        'Normal': shading_normal,
    }, grid_location(10, 2))

    leaves = add_node(tree, 'ShaderNodeAddShader', grid_location(11, -4))
    links.new(diffuse.outputs[0], leaves.inputs[0])
    links.new(translucent.outputs[0], leaves.inputs[1])
    lit = add_node(tree, 'ShaderNodeAddShader', grid_location(12, -1))
    links.new(leaves.outputs[0], lit.inputs[0])
    links.new(lobe.outputs['BSDF'], lit.inputs[1])

    shader = group_node(tree, surface(), {
        'Shader': lit.outputs[0],
        'Alpha': albedo.outputs['Alpha'],
        '1-Bit Mask': value('g_1BitMask', 0.0, 12, -4),
        'Decal': value('g_Decal', 0.0, 12, -5),
    }, grid_location(13, 0)).outputs['Shader']
    output = material_output(tree, shader, grid_location(15, 0))

    vertex_color = add_node(tree, 'ShaderNodeVertexColor', grid_location(11, 6))
    vertex_color.layer_name = 'Col'
    sway = group_node(tree, wind_sway(), {
        'Vertex Color': group_node(tree, linear_to_srgb(), {'Color': vertex_color.outputs['Color']}, grid_location(12, 6)).outputs['Color'],
        'Swing Power': value('g_SwingPower', 0.0, 12, 7),
        'Swing Speed': value('g_SwingSpeed', 0.0, 12, 8),
        'Swing Height Cycle': value('g_SwingHeightCycle', 0.0, 12, 9),
    }, grid_location(13, 6)).outputs['Displacement']
    displacement = add_node(tree, 'ShaderNodeVectorDisplacement', grid_location(14, 6))
    displacement.space = 'OBJECT'
    displacement.inputs['Midlevel'].default_value = 0.0
    displacement.inputs['Scale'].default_value = 1.0
    connect(tree, displacement.inputs['Vector'], sway)
    links.new(displacement.outputs[0], output.inputs['Displacement'])
    if hasattr(material, 'displacement_method'):
        material.displacement_method = 'DISPLACEMENT'
    elif hasattr(material, 'cycles'):
        material.cycles.displacement_method = 'DISPLACEMENT'

    blend_mode_driver(material, ['g_Decal'])
    return material
