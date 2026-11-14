import bpy

from ...utils.nodes import (grid_location, add_node, connect, combine_color, mix_node, vector_math_node,
                            group_node, parameter_node, blend_mode_driver, texture_node, uv_node, material_output, WHITE,
                            uv_tiling, uv_scroll, surface)


# material_array = [material_name, textures, uniforms, shader_name, technique_name, parameterGroups]
def cns00_xxxxx(material: bpy.types.Material, material_array, texture_dir: str):
    tree = material.node_tree
    links = tree.links

    def value(name, default, x, y):
        return parameter_node(material, name, default, grid_location(x, y)).outputs[0]

    uv = group_node(tree, uv_tiling(), {
        'UV': uv_node(tree, 'UVMap1', grid_location(0, 0)),
        'X': value('g_Tile_X', 1.0, 0, 1),
        'Y': value('g_Tile_Y', 1.0, 0, 2),
    }, grid_location(1, 0)).outputs['UV']
    uv = group_node(tree, uv_scroll(), {
        'UV': uv,
        'X': value('g_UvAnimation_X', 0.0, 1, 1),
        'Y': value('g_UvAnimation_Y', 0.0, 1, 2),
    }, grid_location(2, 0)).outputs['UV']
    albedo = texture_node(material, texture_dir, 'g_AlbedoMap', grid_location(3, 0), uv)

    albedo_color = combine_color(tree, *(value('g_AlbedoColor_' + axis, 1.0, 2, -4 + i) for i, axis in enumerate('XYZ')), location=grid_location(3, -3))
    color = mix_node(tree, 'Color', value('g_bAlbedoOverWrite', 0.0, 3, -1), albedo.outputs['Color'], albedo_color, location=grid_location(4, 0))
    color = vector_math_node(tree, 'SCALE', color, value('g_Intensity', 1.0, 4, 2), location=grid_location(5, 0))

    emission = add_node(tree, 'ShaderNodeEmission', grid_location(6, -2))
    connect(tree, emission.inputs['Color'], color)

    light_path = add_node(tree, 'ShaderNodeLightPath', grid_location(5, 3))
    multiplier = mix_node(tree, 'Color', light_path.outputs['Is Camera Ray'], WHITE, color, location=grid_location(6, 1))
    multiply = add_node(tree, 'ShaderNodeBsdfTransparent', grid_location(7, 1), label='Multiply')
    connect(tree, multiply.inputs['Color'], multiplier)

    blend = add_node(tree, 'ShaderNodeMixShader', grid_location(8, 0), label='Multiplication Blend')
    connect(tree, blend.inputs[0], value('g_UseMultiplicationBlend', 0.0, 7, -2))
    links.new(emission.outputs[0], blend.inputs[1])
    links.new(multiply.outputs[0], blend.inputs[2])

    shader = group_node(tree, surface(), {
        'Shader': blend.outputs[0],
        'Alpha': albedo.outputs['Alpha'],
        '1-Bit Mask': value('g_1BitMask', 0.0, 8, -3),
        'Decal': value('g_Decal', 0.0, 8, -4),
    }, grid_location(9, 0)).outputs['Shader']
    material_output(tree, shader, grid_location(10, 0))
    blend_mode_driver(material, ['g_Decal', 'g_UseMultiplicationBlend'])

    return material
