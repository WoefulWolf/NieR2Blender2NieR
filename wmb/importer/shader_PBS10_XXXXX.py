import os
import bpy

from ...utils.util import getTexture

# material_array = [material_name, textures, uniforms, shader_name, technique_name, parameterGroups]
def pbs10_xxxxx(material: bpy.types.Material, material_array, texture_dir: str):
    material_name = material_array[0]
    textures = material_array[1]
    uniforms = material_array[2]
    shader_name = material_array[3]
    technique_name = material_array[4]
    parameterGroups = material_array[5]

    nodes = material.node_tree.nodes
    links = material.node_tree.links

    # Shader parameters
    # index = 0
    # value_nodes = {}
    # for name, value in material.items():
    #     if name.startswith('0_'):
    #         value_node: bpy.types.ShaderNodeValue = nodes.new('ShaderNodeValue')
    #         value_node.name = name
    #         value_node.label = name
    #         value_node.outputs[0].default_value = value
    #         value_node.location = (0, -index * 100)
    #         value_node.width = 200
    #         value_nodes[name] = value_node
    #         index += 1

    # UV Map nodes
    uv_1: bpy.types.ShaderNodeUVMap = nodes.new('ShaderNodeUVMap')
    uv_1.uv_map = 'UVMap1'

    uv_2: bpy.types.ShaderNodeUVMap = nodes.new('ShaderNodeUVMap')
    uv_2.uv_map = 'UVMap2'

    # Multply Add nodes with g_MaterialTile%_X and g_MaterialTile%_Y
    uv_1_mad: bpy.types.ShaderNodeVectorMath = nodes.new('ShaderNodeVectorMath')
    uv_1_mad.operation = 'MULTIPLY_ADD'
    if '0_20_g_MaterialTile1_X' in material and '0_21_g_MaterialTile1_Y' in material:
        uv_1_mad.inputs[1].default_value = (material['0_20_g_MaterialTile1_X'], material['0_21_g_MaterialTile1_Y'], 0)
    else:
        uv_1_mad.inputs[1].default_value = (1.0, 1.0, 0)
    links.new(uv_1.outputs[0], uv_1_mad.inputs[0])

    uv_2_mad: bpy.types.ShaderNodeVectorMath = nodes.new('ShaderNodeVectorMath')
    uv_2_mad.operation = 'MULTIPLY_ADD'
    if '0_22_g_MaterialTile2_X' in material and '0_23_g_MaterialTile2_Y' in material:
        uv_2_mad.inputs[1].default_value = (material['0_22_g_MaterialTile2_X'], material['0_23_g_MaterialTile2_Y'], 0)
    else:
        uv_2_mad.inputs[1].default_value = (1.0, 1.0, 0)
    links.new(uv_2.outputs[0], uv_2_mad.inputs[0])

    # Create Albedo Texture Nodes
    albedo_1: bpy.types.ShaderNodeTexImage = nodes.new('ShaderNodeTexImage')
    albedo_1.label = 'g_AlbedoMap1'
    if 'g_AlbedoMap1' in material:
        albedo_1_texture_path = getTexture(texture_dir, material['g_AlbedoMap1'])
        if albedo_1_texture_path != None:
            albedo_1.image = bpy.data.images.load(albedo_1_texture_path)
        else:
            print('g_AlbedoMap1 texture not found: %s' % material['g_AlbedoMap1'])
    links.new(uv_1_mad.outputs[0], albedo_1.inputs[0])

    albedo_2: bpy.types.ShaderNodeTexImage = nodes.new('ShaderNodeTexImage')
    albedo_2.label = 'g_AlbedoMap2'
    if 'g_AlbedoMap2' in material:
        albedo_2_texture_path = getTexture(texture_dir, material['g_AlbedoMap2'])
        if albedo_2_texture_path != None:
            albedo_2.image = bpy.data.images.load(albedo_2_texture_path)
        else:
            print('g_AlbedoMap2 texture not found: %s' % material['g_AlbedoMap2'])
    links.new(uv_2_mad.outputs[0], albedo_2.inputs[0])

    albedo_3: bpy.types.ShaderNodeTexImage = nodes.new('ShaderNodeTexImage')
    albedo_3.label = 'g_AlbedoMap3'
    if 'g_AlbedoMap3' in material:
        albedo_3_texture_path = getTexture(texture_dir, material['g_AlbedoMap3'])
        if albedo_3_texture_path != None:
            albedo_3.image = bpy.data.images.load(albedo_3_texture_path)
        else:
            print('g_AlbedoMap3 texture not found: %s' % material['g_AlbedoMap3'])
    links.new(uv_2_mad.outputs[0], albedo_3.inputs[0])

    # Color Attribute
    color: bpy.types.ShaderNodeVertexColor = nodes.new('ShaderNodeVertexColor')
    color.layer_name = 'Col'

    # Separate Color into RGB
    color_sep: bpy.types.ShaderNodeSeparateRGB = nodes.new('ShaderNodeSeparateRGB')
    links.new(color.outputs[0], color_sep.inputs[0])

    # Create Mask 1 Multiply Add Node
    mask_1_mad: bpy.types.ShaderNodeMath = nodes.new('ShaderNodeMath')
    mask_1_mad.operation = 'MULTIPLY_ADD'
    links.new(albedo_1.outputs[1], mask_1_mad.inputs[0])        # Connect albedo 1 alpha to mad value
    mask_1_mad.inputs[1].default_value = -1                     # Set mask 1 mad multiplier to -1
    links.new(color_sep.outputs[0], mask_1_mad.inputs[2])       # Connect color red to mask 1 mad addend

    # Create Mask 2 Multiply Add Node
    mask_2_mad: bpy.types.ShaderNodeMath = nodes.new('ShaderNodeMath')
    mask_2_mad.operation = 'MULTIPLY_ADD'
    links.new(albedo_2.outputs[1], mask_2_mad.inputs[0])        # Connect albedo 2 alpha to mad value
    mask_2_mad.inputs[1].default_value = -1                     # Set mask 2 mad multiplier to -1
    links.new(color_sep.outputs[1], mask_2_mad.inputs[2])       # Connect color green to mask 2 mad addend

    # Divide Mask 1 by g_InterPolationRate
    mask_1_div: bpy.types.ShaderNodeMath = nodes.new('ShaderNodeMath')
    mask_1_div.operation = 'DIVIDE'
    if 'g_InterpolationRate' in material:
        mask_1_div.inputs[1].default_value = material['g_InterpolationRate']
    links.new(mask_1_mad.outputs[0], mask_1_div.inputs[0])

    # Divide Mask 2 by g_InterPolationRate
    mask_2_div: bpy.types.ShaderNodeMath = nodes.new('ShaderNodeMath')
    mask_2_div.operation = 'DIVIDE'
    if 'g_InterpolationRate' in material:
        mask_2_div.inputs[1].default_value = material['g_InterpolationRate']
    links.new(mask_2_mad.outputs[0], mask_2_div.inputs[0])

    # Create Albedo Mix Nodes
    albedo_mix_1: bpy.types.ShaderNodeMixRGB = nodes.new('ShaderNodeMixRGB')
    links.new(mask_1_div.outputs[0], albedo_mix_1.inputs[0])           # Connect mask 1 divide to mix 1 factor
    links.new(albedo_1.outputs[0], albedo_mix_1.inputs[1])             # Connect albedo 1 color to mix 1 color 1
    links.new(albedo_2.outputs[0], albedo_mix_1.inputs[2])             # Connect albedo 2 color to mix 1 color 2

    albedo_mix_2: bpy.types.ShaderNodeMixRGB = nodes.new('ShaderNodeMixRGB')
    links.new(mask_2_div.outputs[0], albedo_mix_2.inputs[0])           # Connect mask 2 divide to mix 2 factor
    links.new(albedo_mix_1.outputs[0], albedo_mix_2.inputs[1])         # Connect mix 1 color to mix 2 color 1
    links.new(albedo_3.outputs[0], albedo_mix_2.inputs[2])             # Connect albedo 3 color to mix 2 color 2

    # Create principled shader node
    principled: bpy.types.ShaderNodeBsdfPrincipled = nodes.new('ShaderNodeBsdfPrincipled')
    links.new(albedo_mix_2.outputs[0], principled.inputs[0])           # Connect albedo mix 2 color to principled base color

    # Create Material Output Node
    material_output: bpy.types.ShaderNodeOutputMaterial = nodes.new('ShaderNodeOutputMaterial')
    links.new(principled.outputs[0], material_output.inputs[0])        # Connect principled shader to material output

    # Create Normal Texture Nodes
    normal_1: bpy.types.ShaderNodeTexImage = nodes.new('ShaderNodeTexImage')
    normal_1.label = 'g_NormalMap1'
    if 'g_NormalMap1' in material:
        normal_1_texture_path = getTexture(texture_dir, material['g_NormalMap1'])
        if normal_1_texture_path != None:
            normal_1.image = bpy.data.images.load(normal_1_texture_path)
            normal_1.image.colorspace_settings.name = 'Non-Color'
        else:
            print('g_NormalMap1 texture not found: %s' % material['g_NormalMap1'])
    links.new(uv_1_mad.outputs[0], normal_1.inputs[0])

    normal_2: bpy.types.ShaderNodeTexImage = nodes.new('ShaderNodeTexImage')
    normal_2.label = 'g_NormalMap2'
    if 'g_NormalMap2' in material:
        normal_2_texture_path = getTexture(texture_dir, material['g_NormalMap2'])
        if normal_2_texture_path != None:
            normal_2.image = bpy.data.images.load(normal_2_texture_path)
            normal_2.image.colorspace_settings.name = 'Non-Color'
        else:
            print('g_NormalMap2 texture not found: %s' % material['g_NormalMap2'])
    links.new(uv_2_mad.outputs[0], normal_2.inputs[0])

    normal_3: bpy.types.ShaderNodeTexImage = nodes.new('ShaderNodeTexImage')
    normal_3.label = 'g_NormalMap3'
    if 'g_NormalMap3' in material:
        normal_3_texture_path = getTexture(texture_dir, material['g_NormalMap3'])
        if normal_3_texture_path != None:
            normal_3.image = bpy.data.images.load(normal_3_texture_path)
            normal_3.image.colorspace_settings.name = 'Non-Color'
        else:
            print('g_NormalMap3 texture not found: %s' % material['g_NormalMap3'])
    links.new(uv_2_mad.outputs[0], normal_3.inputs[0])

    # Create Normal Map Mix Nodes
    normal_mix_1: bpy.types.ShaderNodeMixRGB = nodes.new('ShaderNodeMixRGB')
    links.new(mask_1_div.outputs[0], normal_mix_1.inputs[0])           # Connect mask 1 divide to mix 1 factor
    links.new(normal_1.outputs[0], normal_mix_1.inputs[1])             # Connect normal 1 color to mix 1 color 1
    links.new(normal_2.outputs[0], normal_mix_1.inputs[2])             # Connect normal 2 color to mix 1 color 2

    normal_mix_2: bpy.types.ShaderNodeMixRGB = nodes.new('ShaderNodeMixRGB')
    links.new(mask_2_div.outputs[0], normal_mix_2.inputs[0])           # Connect mask 2 divide to mix 2 factor
    links.new(normal_mix_1.outputs[0], normal_mix_2.inputs[1])         # Connect mix 1 color to mix 2 color 1
    links.new(normal_3.outputs[0], normal_mix_2.inputs[2])             # Connect normal 3 color to mix 2 color 2

    # Create Normal Map Multiply Node
    normal_mul: bpy.types.ShaderNodeVectorMath = nodes.new('ShaderNodeVectorMath')
    normal_mul.operation = 'MULTIPLY'
    normal_mul.inputs[1].default_value = (1.0, 1.0, 1.0)
    if 'g_NormalReverse' in material:
        if material['g_NormalReverse'] == 1:
            normal_mul.inputs[1].default_value = (1.0, -1.0, 1.0)
    links.new(normal_mix_2.outputs[0], normal_mul.inputs[0])

    # Create Normal Map Node
    normal: bpy.types.ShaderNodeNormalMap = nodes.new('ShaderNodeNormalMap')
    links.new(normal_mul.outputs[0], normal.inputs[1])

    # Connect Normal Map to Principled Normal
    links.new(normal.outputs[0], principled.inputs[5])

    return material