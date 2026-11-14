import bpy

from ...utils.nodes import (grid_location, add_node, connect, combine_color, separate_color, math_node, vector_math_node,
                            mix_node, group_node, parameter_node, texture_node, uv_node, material_output,
                            uv_tiling, tangent_normal, fuzz, anisotropy, specular_lobe, shading, surface)

# material_array = [material_name, textures, uniforms, shader_name, technique_name, parameterGroups]
def hair01_xxxxx(material: bpy.types.Material, material_array, texture_dir: str):
    tree = material.node_tree
    links = tree.links

    def value(name, default, x, y):
        return parameter_node(material, name, default, grid_location(x, y)).outputs[0]

    uv = uv_node(tree, 'UVMap1', grid_location(1, 0))
    uv_2 = uv_node(tree, 'UVMap2', grid_location(0, 10))
    uv_detail = group_node(tree, uv_tiling(), {
        'UV': uv_2,
        'X': value('g_DetailNormalTile_X', 1.0, 0, 11),
        'Y': value('g_DetailNormalTile_Y', 1.0, 0, 12),
    }, grid_location(1, 10)).outputs['UV']
    uv_noise = group_node(tree, uv_tiling(), {
        'UV': uv_2,
        'X': value('g_NoiseTile_X', 1.0, 0, 14),
        'Y': value('g_NoiseTile_Y', 1.0, 0, 15),
    }, grid_location(1, 14)).outputs['UV']

    albedo = texture_node(material, texture_dir, 'g_AlbedoMap', grid_location(2, 0), uv)
    mask = texture_node(material, texture_dir, 'g_MaskMap', grid_location(2, 1), uv, non_color=True)
    mask_2 = texture_node(material, texture_dir, 'g_MaskMap2', grid_location(2, 2), uv, non_color=True)
    normal = texture_node(material, texture_dir, 'g_NormalMap', grid_location(2, 9), uv, non_color=True)
    detail_normal = texture_node(material, texture_dir, 'g_DetailNormalMap', grid_location(2, 10), uv_detail, non_color=True)
    noise = add_node(tree, 'ShaderNodeTexImage', grid_location(2, 14), label=mask.label + ' (noise)')
    noise.image = mask.image
    connect(tree, noise.inputs['Vector'], uv_noise)
    metallic_map, glossiness_map, occlusion_map = separate_color(tree, mask.outputs['Color'], grid_location(3, 1))[:3]
    anisotropy_mask, fuzz_mask = separate_color(tree, mask_2.outputs['Color'], grid_location(3, 2))[:2]

    albedo_color = combine_color(tree, *(value('g_AlbedoColor_' + axis, 1.0, 3, -4 + i) for i, axis in enumerate('XYZ')), location=grid_location(4, -3))
    color = mix_node(tree, 'Color', value('g_bAlbedoOverWrite', 0.0, 4, -1), albedo.outputs['Color'], albedo_color, location=grid_location(5, 0))
    glossiness = mix_node(tree, 'Float', value('g_bGlossinessOverWrite', 0.0, 4, 4), glossiness_map, value('g_Glossiness', 0.0, 4, 5), location=grid_location(5, 4))
    metallic = mix_node(tree, 'Float', value('g_bMetalicOverWrite', 0.0, 4, 6), metallic_map, value('g_Metallic', 0.0, 4, 7), location=grid_location(5, 6))

    normal_inputs = {
        'Normal Map': normal.outputs['Color'],
        'Use Normal Map': value('g_UseNormalMap', 1.0, 3, 8),
        'Detail Normal Map': detail_normal.outputs['Color'],
        'Detail Strength': mask.outputs['Alpha'],
        'Use Detail Normal Map': value('g_UseDetailNormalMap', 0.0, 3, 11),
        'Offset': vector_math_node(tree, 'SCALE', (0.0, 0.05, 0.0), noise.outputs['Alpha'], location=grid_location(3, 14)),
    }
    shading_normal = group_node(tree, tangent_normal(), normal_inputs, grid_location(4, 9)).outputs['Normal']
    shifted_normals = [group_node(tree, tangent_normal(), dict(normal_inputs, Shift=value(name, 0.0, 4, 17 + i * 8)), grid_location(5, 17 + i * 8)).outputs['Normal']
                       for i, name in enumerate(('g_SpecShift', 'g_SecondarySpecShift'))]

    base_color = group_node(tree, fuzz(), {
        'Color': color,
        'Normal': shading_normal,
        'Fuzz Mask': fuzz_mask,
        'Exponent': value('g_FuzzExponent', 1.0, 6, -6),
        'Highlight': value('g_HilIghtIntensity', 1.0, 6, -5),
        'Mask Effective': value('g_FuzzMaskEffective', 0.0, 6, -4),
    }, grid_location(7, -3)).outputs['Color']

    modes = {
        'Mask': anisotropy_mask,
        'Mode': value('g_AnisoLightMode', 0.0, 6, 2),
        'Mode 2': value('g_AnisoLightMode2', 0.0, 6, 3),
        'Anisotropic': value('g_Anisotropic', 0.0, 6, 4),
        'Anisotropic X': value('g_Anisotropic_X', 0.0, 6, 5),
        'Anisotropic Y': value('g_Anisotropic_Y', 0.0, 6, 6),
    }
    secondary_glossiness = math_node(tree, 'MULTIPLY', glossiness, value('g_SecondaryGlossiness', 1.0, 6, 13), location=grid_location(7, 12))
    highlights = [group_node(tree, anisotropy(), dict(modes, Glossiness=lobe_glossiness), grid_location(8, 3 + i * 9))
                  for i, lobe_glossiness in enumerate((glossiness, secondary_glossiness))]

    tangent = add_node(tree, 'ShaderNodeTangent', grid_location(8, 20))
    tangent.direction_type = 'UV_MAP'
    tangent.uv_map = 'UVMap1'

    lobe_normals = [mix_node(tree, 'Vector', highlight.outputs['Active'], shading_normal, shifted_normals[i], location=grid_location(9, 5 + i * 9))
                    for i, highlight in enumerate(highlights)]
    lit = group_node(tree, shading(), {
        'Color': base_color,
        'Metallic': metallic,
        'Roughness': highlights[0].outputs['Roughness'],
        'Anisotropy': highlights[0].outputs['Anisotropy'],
        'Rotation': highlights[0].outputs['Rotation'],
        'Normal': shading_normal,
        'Specular Normal': lobe_normals[0],
        'Tangent': tangent.outputs['Tangent'],
    }, grid_location(10, 0))
    secondary = group_node(tree, specular_lobe(), {
        'Color': base_color,
        'Metallic': value('g_SecondaryMetalic', 0.0, 9, 22),
        'Roughness': highlights[1].outputs['Roughness'],
        'Anisotropy': highlights[1].outputs['Anisotropy'],
        'Rotation': highlights[1].outputs['Rotation'],
        'Normal': lobe_normals[1],
        'Tangent': tangent.outputs['Tangent'],
    }, grid_location(10, 12))
    added = add_node(tree, 'ShaderNodeAddShader', grid_location(11, 0))
    links.new(lit.outputs['BSDF'], added.inputs[0])
    links.new(secondary.outputs['BSDF'], added.inputs[1])
    shader = added.outputs[0]

    shader = group_node(tree, surface(), {
        'Shader': shader,
        'Occlusion': occlusion_map if mask.image is not None else 1.0,
        'Alpha': albedo.outputs['Alpha'],
        '1-Bit Mask': value('g_1BitMask', 0.0, 11, -3),
    }, grid_location(12, 0)).outputs['Shader']
    material_output(tree, shader, grid_location(13, 0))

    return material
