import os
import bpy

from ...utils.util import getTexture
from ...utils.nodes import grid_location, invert_channel, if_nz

# material_array = [material_name, textures, uniforms, shader_name, technique_name, parameterGroups]
def pbs00_xxxxx(material: bpy.types.Material, material_array, texture_dir: str):
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
    # for name, value in material.items():
    #     if name.startswith('0_'):
    #         value_node: bpy.types.ShaderNodeValue = nodes.new('ShaderNodeValue')
    #         value_node.name = name
    #         value_node.label = name
    #         value_node.outputs[0].default_value = value
    #         value_node.location = grid_location(-2, index)
    #         value_node.width = 200
    #         index += 1

    # UV Map nodes
    uv_1: bpy.types.ShaderNodeUVMap = nodes.new('ShaderNodeUVMap')
    uv_1.label = 'UV1'
    uv_1.uv_map = 'UVMap1'
    uv_1.location = grid_location(0, 0)
    uv_1.hide = True

    uv_2: bpy.types.ShaderNodeUVMap = nodes.new('ShaderNodeUVMap')
    uv_2.label = 'UV2'
    uv_2.uv_map = 'UVMap2'
    uv_2.location = grid_location(0, 1)
    uv_2.hide = True

    # g_UV2Use logic
    if_nz_uv2 = nodes.new('ShaderNodeGroup')
    if_nz_uv2.node_tree = if_nz("Vector")
    if_nz_uv2.location = grid_location(1, 0)
    if_nz_uv2.hide = True

    value_node: bpy.types.ShaderNodeValue = nodes.new('ShaderNodeValue')
    value_node.label = 'g_UV2Use'
    value_node.outputs[0].default_value = material['g_UV2Use'] if 'g_UV2Use' in material else 0.0
    value_node.location = grid_location(0, -1.5)
    value_node.width = 200

    links.new(value_node.outputs[0], if_nz_uv2.inputs['Value'])
    links.new(uv_1.outputs[0], if_nz_uv2.inputs['False'])
    links.new(uv_2.outputs[0], if_nz_uv2.inputs['True'])

    # Multiply UV output by g_Tile_XY
    uv_mad: bpy.types.ShaderNodeVectorMath = nodes.new('ShaderNodeVectorMath')
    uv_mad.operation = 'MULTIPLY_ADD'
    uv_mad.location = grid_location(2, 0)
    uv_mad.hide = True

    cmb_node: bpy.types.ShaderNodeCombineXYZ = nodes.new('ShaderNodeCombineXYZ')
    cmb_node.location = grid_location(1, 1)
    cmb_node.hide = True
    links.new(if_nz_uv2.outputs['Value'], uv_mad.inputs[0])
    links.new(cmb_node.outputs['Vector'], uv_mad.inputs[1])

    value_node: bpy.types.ShaderNodeValue = nodes.new('ShaderNodeValue')
    value_node.label = 'g_Tile_X'
    value_node.outputs[0].default_value = material['g_Tile_X'] if 'g_Tile_X' in material else 1.0
    value_node.location = grid_location(0, 1.5)
    value_node.width = 200
    links.new(value_node.outputs[0], cmb_node.inputs['X'])

    value_node: bpy.types.ShaderNodeValue = nodes.new('ShaderNodeValue')
    value_node.label = 'g_Tile_X'
    value_node.outputs[0].default_value = material['g_Tile_X'] if 'g_Tile_X' in material else 1.0
    value_node.location = grid_location(0, 2.5)
    value_node.width = 200
    links.new(value_node.outputs[0], cmb_node.inputs['Y'])

    # Albedo Map
    albedo: bpy.types.ShaderNodeTexImage = nodes.new('ShaderNodeTexImage')
    albedo.label = 'g_AlbedoMap'
    albedo.location = grid_location(3, 0)
    albedo.hide = True
    if 'g_AlbedoMap' in material:
        albedo_texture_path = getTexture(texture_dir, material['g_AlbedoMap'])
        if albedo_texture_path != None:
            albedo.image = bpy.data.images.load(albedo_texture_path)
        else:
            print('g_AlbedoMap1 texture not found: %s' % material['g_AlbedoMap'])
    links.new(uv_mad.outputs[0], albedo.inputs[0])

    # g_1BitMask
    value_node: bpy.types.ShaderNodeValue = nodes.new('ShaderNodeValue')
    value_node.label = 'g_1BitMask'
    value_node.outputs[0].default_value = material['g_1BitMask'] if 'g_1BitMask' in material else 0.0
    value_node.location = grid_location(3, -1.5)
    value_node.width = 200
    
    if_nz_1bitmask = nodes.new('ShaderNodeGroup')
    if_nz_1bitmask.node_tree = if_nz("Float")
    if_nz_1bitmask.location = grid_location(4, -1)
    if_nz_1bitmask.hide = True
    if_nz_1bitmask.inputs['False'].default_value = 1.0
    links.new(value_node.outputs[0], if_nz_1bitmask.inputs['Value'])
    links.new(albedo.outputs[1], if_nz_1bitmask.inputs['True'])

    bitmask = nodes.new('ShaderNodeGroup')
    bitmask.label = 'Binarize'
    bitmask.node_tree = if_nz("Float")
    bitmask.location = grid_location(5, -1)
    bitmask.hide = True
    bitmask.inputs['True'].default_value = 1.0
    bitmask.inputs['False'].default_value = 0.0
    links.new(if_nz_1bitmask.outputs['Value'], bitmask.inputs['Value'])

    # Create principled shader node
    principled: bpy.types.ShaderNodeBsdfPrincipled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.location = grid_location(6, 0)
    # links.new(albedo.outputs[0], principled.inputs[0])
    links.new(bitmask.outputs['Value'], principled.inputs["Alpha"])

    # Create Material Output Node
    material_output: bpy.types.ShaderNodeOutputMaterial = nodes.new('ShaderNodeOutputMaterial')
    material_output.location = grid_location(7, 0)
    links.new(principled.outputs[0], material_output.inputs[0])

    # Create MaskMap (Metallic, Roughness, AO) Texture Nodes
    mask: bpy.types.ShaderNodeTexImage = nodes.new('ShaderNodeTexImage')
    mask.label = 'g_MaskMap'
    mask.location = grid_location(3, 1)
    mask.hide = True
    if 'g_MaskMap' in material:
        mask_texture_path = getTexture(texture_dir, material['g_MaskMap'])
        if mask_texture_path != None:
            mask.image = bpy.data.images.load(mask_texture_path)
        else:
            print('g_MaskMap texture not found: %s' % material['g_MaskMap'])
    links.new(uv_mad.outputs[0], mask.inputs[0])
    mask_invert_g = nodes.new('ShaderNodeGroup')
    mask_invert_g.node_tree = invert_channel("Green")
    mask_invert_g.location = grid_location(4, 1)
    mask_invert_g.hide = True
    links.new(mask.outputs['Color'], mask_invert_g.inputs['Color'])
    mask_sep: bpy.types.ShaderNodeSeparateColor = nodes.new('ShaderNodeSeparateColor')
    mask_sep.location = grid_location(5, 1)
    mask_sep.hide = True
    links.new(mask_invert_g.outputs['Color'], mask_sep.inputs[0])
    links.new(mask_sep.outputs['Red'], principled.inputs['Metallic'])
    links.new(mask_sep.outputs['Green'], principled.inputs['Roughness'])

    # Ambient Occlusiion
    ao_multiply: bpy.types.ShaderNodeMixRGB = nodes.new('ShaderNodeMixRGB')
    ao_multiply.location = grid_location(5, 0)
    ao_multiply.hide = True
    ao_multiply.blend_type = 'MULTIPLY'
    ao_multiply.inputs[0].default_value = 1.0
    links.new(albedo.outputs[0], ao_multiply.inputs[1])
    links.new(mask_sep.outputs['Blue'], ao_multiply.inputs[2])
    links.new(ao_multiply.outputs['Color'], principled.inputs['Base Color'])

    # Normal
    normal: bpy.types.ShaderNodeTexImage = nodes.new('ShaderNodeTexImage')
    normal.label = 'g_NormalMap'
    normal.location = grid_location(2, 2)
    normal.hide = True
    if 'g_NormalMap' in material:
        normal_texture_path = getTexture(texture_dir, material['g_NormalMap'])
        if normal_texture_path != None:
            normal.image = bpy.data.images.load(normal_texture_path)
            normal.image.colorspace_settings.name = 'Non-Color'
        else:
            print('g_NormalMap texture not found: %s' % material['g_NormalMap'])
    links.new(uv_mad.outputs[0], normal.inputs[0])
    
    if_nz_normal = nodes.new('ShaderNodeGroup')
    if_nz_normal.node_tree = if_nz("Color")
    if_nz_normal.location = grid_location(3, 2)
    if_nz_normal.hide = True
    if_nz_normal.inputs['False'].default_value = (0.5, 0.5, 1.0, 1.0)
    links.new(normal.outputs[0], if_nz_normal.inputs['True'])

    # g_UseNormalMap
    value_node: bpy.types.ShaderNodeValue = nodes.new('ShaderNodeValue')
    value_node.label = 'g_UseNormalMap'
    value_node.outputs[0].default_value = material['g_UseNormalMap'] if 'g_UseNormalMap' in material else 1.0
    value_node.location = grid_location(2, 2.5)
    value_node.width = 200
    links.new(value_node.outputs[0], if_nz_normal.inputs['Value'])

    # Invert Normal Green Channel for OpenGL
    normal_invert_g = nodes.new('ShaderNodeGroup')
    normal_invert_g.node_tree = invert_channel("Green")
    normal_invert_g.location = grid_location(4, 2)
    normal_invert_g.hide = True
    links.new(if_nz_normal.outputs['Value'], normal_invert_g.inputs['Color'])

    # Normal Map Node
    normal_map: bpy.types.ShaderNodeNormalMap = nodes.new('ShaderNodeNormalMap')
    normal_map.location = grid_location(5, 2)
    normal_map.hide = True
    links.new(normal_invert_g.outputs[0], normal_map.inputs[1])
    links.new(normal_map.outputs[0], principled.inputs[5])

    # Multiply UV output by g_DetailNormalTile_XY
    uv_mad_dn: bpy.types.ShaderNodeVectorMath = nodes.new('ShaderNodeVectorMath')
    uv_mad_dn.operation = 'MULTIPLY_ADD'
    uv_mad_dn.location = grid_location(2, 4.5)
    uv_mad_dn.hide = True

    cmb_node: bpy.types.ShaderNodeCombineXYZ = nodes.new('ShaderNodeCombineXYZ')
    cmb_node.location = grid_location(1, 4.5)
    cmb_node.hide = True
    links.new(if_nz_uv2.outputs['Value'], uv_mad_dn.inputs[0])
    links.new(cmb_node.outputs['Vector'], uv_mad_dn.inputs[1])

    value_node: bpy.types.ShaderNodeValue = nodes.new('ShaderNodeValue')
    value_node.label = 'g_DetailNormalTile_X'
    value_node.outputs[0].default_value = material['g_DetailNormalTile_X'] if 'g_DetailNormalTile_X' in material else 1.0
    value_node.location = grid_location(0, 4)
    value_node.width = 200
    links.new(value_node.outputs[0], cmb_node.inputs['X'])

    value_node: bpy.types.ShaderNodeValue = nodes.new('ShaderNodeValue')
    value_node.label = 'g_DetailNormalTile_Y'
    value_node.outputs[0].default_value = material['g_DetailNormalTile_Y'] if 'g_DetailNormalTile_Y' in material else 1.0
    value_node.location = grid_location(0, 5)
    value_node.width = 200
    links.new(value_node.outputs[0], cmb_node.inputs['Y'])

    # Detail Normal
    detail_normal: bpy.types.ShaderNodeTexImage = nodes.new('ShaderNodeTexImage')
    detail_normal.label = 'g_DetailNormalMap'
    detail_normal.location = grid_location(2, 5)
    detail_normal.hide = True
    if 'g_DetailNormalMap' in material:
        detail_normal_texture_path = getTexture(texture_dir, material['g_DetailNormalMap'])
        if detail_normal_texture_path != None:
            detail_normal.image = bpy.data.images.load(detail_normal_texture_path)
            detail_normal.image.colorspace_settings.name = 'Non-Color'
        else:
            print('g_DetailNormalMap texture not found: %s' % material['g_DetailNormalMap'])
    links.new(uv_mad_dn.outputs[0], detail_normal.inputs[0])

    # Invert Normal Green Channel for OpenGL
    detail_normal_invert_g = nodes.new('ShaderNodeGroup')
    detail_normal_invert_g.node_tree = invert_channel("Green")
    detail_normal_invert_g.location = grid_location(3, 5)
    detail_normal_invert_g.hide = True
    links.new(detail_normal.outputs[0], detail_normal_invert_g.inputs['Color'])

    # Detail Normal Map Node
    detail_normal_map: bpy.types.ShaderNodeNormalMap = nodes.new('ShaderNodeNormalMap')
    detail_normal_map.location = grid_location(4, 5)
    detail_normal_map.hide = True
    links.new(detail_normal_invert_g.outputs[0], detail_normal_map.inputs[1])

    # DetailedNormal = detailNormal.xy * maskAlpha + normal;
    final_detailed_normal_map: bpy.types.ShaderNodeVectorMath = nodes.new('ShaderNodeVectorMath')
    final_detailed_normal_map.operation = 'MULTIPLY_ADD'
    final_detailed_normal_map.location = grid_location(5, 5)
    final_detailed_normal_map.hide = True
    links.new(detail_normal_map.outputs[0], final_detailed_normal_map.inputs[0])
    links.new(mask.outputs[1], final_detailed_normal_map.inputs[1])
    links.new(normal_map.outputs[0], final_detailed_normal_map.inputs[2])

    # g_UseDetailNormalMap
    value_node: bpy.types.ShaderNodeValue = nodes.new('ShaderNodeValue')
    value_node.label = 'g_UseDetailNormalMap'
    value_node.outputs[0].default_value = material['g_UseDetailNormalMap'] if 'g_UseDetailNormalMap' in material else 0.0
    value_node.location = grid_location(4, 3.5)
    value_node.width = 200
    
    if_nz_dn = nodes.new('ShaderNodeGroup')
    if_nz_dn.node_tree = if_nz("Vector")
    if_nz_dn.location = grid_location(5, 3.5)
    if_nz_dn.hide = True
    links.new(value_node.outputs[0], if_nz_dn.inputs['Value'])
    links.new(final_detailed_normal_map.outputs[0], if_nz_dn.inputs['True'])
    links.new(normal_map.outputs[0], if_nz_dn.inputs['False'])
    links.new(if_nz_dn.outputs[0], principled.inputs[5])

    return material