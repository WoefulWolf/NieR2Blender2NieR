import bpy

from ...utils.nodes import grid_location, math_node, group_node, material_output, blended, water_opacity, surface
from .shader_PBS11_XXXXX import two_layer


def wtr01_xxxxx(material: bpy.types.Material, material_array, texture_dir: str):
    tree = material.node_tree
    value, vertex, albedos, lit, occlusion = two_layer(material, texture_dir, False)

    opacity = group_node(tree, water_opacity(), {
        'Mask': math_node(tree, 'MULTIPLY', albedos[0].outputs['Alpha'], vertex[2], location=grid_location(12, -3)),
        'Fresnel Exp U': value('g_FresnelExpU', 0.0, 12, -7),
        'Fresnel Exp V': value('g_FresnelExpV', 0.0, 12, -6),
        'Strength': value('g_TranslucentStrength', 1.0, 12, -5),
        'Power': value('g_TranslucentPow', 1.0, 12, -4),
    }, grid_location(13, -4)).outputs['Alpha']

    shader = group_node(tree, surface(), {
        'Shader': lit,
        'Occlusion': occlusion,
        'Alpha': opacity,
        'Decal': 1.0,
    }, grid_location(14, 0)).outputs['Shader']
    material_output(tree, shader, grid_location(15, 0))
    blended(material)

    return material
