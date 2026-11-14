import math
import bpy

from ...utils.nodes import (grid_location, add_node, connect, combine_color, separate_color, math_node, vector_math_node,
                            mix_node, group_node, parameter_node, texture_node, uv_node, material_output, WHITE,
                            uv_tiling, tangent_normal, specular_lobe, surface)


# material_array = [material_name, textures, uniforms, shader_name, technique_name, parameterGroups]
def skn00_xxxxx(material: bpy.types.Material, material_array, texture_dir: str):
    tree = material.node_tree
    links = tree.links

    def value(name, default, x, y):
        return parameter_node(material, name, default, grid_location(x, y)).outputs[0]

    uv = uv_node(tree, 'UVMap1', grid_location(1, 0))
    uv_detail = group_node(tree, uv_tiling(), {
        'UV': uv_node(tree, 'UVMap2', grid_location(0, 10)),
        'X': value('g_DetailNormalTile_X', 1.0, 0, 11),
        'Y': value('g_DetailNormalTile_Y', 1.0, 0, 12),
    }, grid_location(1, 10)).outputs['UV']

    albedo = texture_node(material, texture_dir, 'g_AlbedoMap', grid_location(2, 0), uv)
    mask = texture_node(material, texture_dir, 'g_MaskMap', grid_location(2, 1), uv, non_color=True)
    curvature = texture_node(material, texture_dir, 'g_CurvatureMap', grid_location(2, 2), uv, non_color=True)
    normal = texture_node(material, texture_dir, 'g_NormalMap', grid_location(2, 9), uv, non_color=True)
    detail_normal = texture_node(material, texture_dir, 'g_DetailNormalMap', grid_location(2, 10), uv_detail, non_color=True)
    metallic_map, glossiness_map, occlusion_map = separate_color(tree, mask.outputs['Color'], grid_location(3, 1))[:3]
    thickness = separate_color(tree, curvature.outputs['Color'], grid_location(3, 2))[0]

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

    occlusion_color = combine_color(tree, *(value('g_OcclusionColor_' + axis, 1.0, 5, -9 + i) for i, axis in enumerate('XYZ')), location=grid_location(6, -8))
    occlusion = mix_node(tree, 'Color', occlusion_map, occlusion_color, WHITE, location=grid_location(7, -6))

    dielectric_color = vector_math_node(tree, 'SCALE', color, math_node(tree, 'SUBTRACT', 1.0, metallic, location=grid_location(6, -1)), location=grid_location(7, -1))
    diffuse_color = mix_node(tree, 'Color', 1.0, dielectric_color, occlusion, location=grid_location(8, -2), blend='MULTIPLY')

    subsurface = add_node(tree, 'ShaderNodeSubsurfaceScattering', grid_location(9, -6), hide=False)
    subsurface.inputs['Scale'].default_value = 0.005
    subsurface.inputs['Radius'].default_value = (1.0, 0.2, 0.1)
    connect(tree, subsurface.inputs['Color'], diffuse_color)
    connect(tree, subsurface.inputs['Normal'], shading_normal)

    transmission_color = combine_color(tree, *(value('g_TransMissionColor_' + axis, 0.0, 7, -12 + i) for i, axis in enumerate('XYZ')), location=grid_location(8, -11))
    transmission = vector_math_node(tree, 'SCALE', transmission_color, math_node(tree, 'POWER', thickness, 4.0, location=grid_location(8, -9)), location=grid_location(9, -9))
    translucent = add_node(tree, 'ShaderNodeBsdfTranslucent', grid_location(10, -9), hide=False)
    connect(tree, translucent.inputs['Color'], mix_node(tree, 'Color', 1.0, diffuse_color, transmission, location=grid_location(10, -10), blend='MULTIPLY'))
    connect(tree, translucent.inputs['Normal'], shading_normal)

    roughness = math_node(tree, 'POWER', math_node(tree, 'SUBTRACT', 1.0, glossiness, location=grid_location(6, 4)), 0.5, location=grid_location(7, 4))
    lobe = group_node(tree, specular_lobe(), {
        'Color': color,
        'Metallic': metallic,
        'Roughness': roughness,
        'Normal': shading_normal,
        'Dielectric': math_node(tree, 'MULTIPLY', value('g_rho_s', 1.0, 7, 7), math.pi * 0.028, location=grid_location(8, 7)),
        'Tint': occlusion,
    }, grid_location(10, 2))

    added = add_node(tree, 'ShaderNodeAddShader', grid_location(11, -6))
    links.new(subsurface.outputs[0], added.inputs[0])
    links.new(translucent.outputs[0], added.inputs[1])
    lit = add_node(tree, 'ShaderNodeAddShader', grid_location(12, -2))
    links.new(added.outputs[0], lit.inputs[0])
    links.new(lobe.outputs['BSDF'], lit.inputs[1])

    shader = group_node(tree, surface(), {
        'Shader': lit.outputs[0],
        'Alpha': albedo.outputs['Alpha'],
        '1-Bit Mask': value('g_1BitMask', 0.0, 12, -4),
    }, grid_location(13, 0)).outputs['Shader']
    material_output(tree, shader, grid_location(14, 0))

    return material
