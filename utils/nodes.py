import bpy

def grid_location(x, y):
    return (x * 300, y * -80)

def if_nz(type="Float"):
    types = ["Float", "Vector", "Color"]

    if type not in types:
        return None

    name = 'If Non-Zero (%s)' % type

    if name in bpy.data.node_groups:
        return bpy.data.node_groups[name]

    node_group = bpy.data.node_groups.new(name, 'ShaderNodeTree')
    node_group.color_tag = 'CONVERTER'

    interface = node_group.interface
    interface.new_socket(
        name='Value',
        in_out='INPUT',
        socket_type='NodeSocketFloat'
    )
    interface.new_socket(
        name='True',
        in_out='INPUT',
        socket_type='NodeSocket%s' % type
    )
    interface.new_socket(
        name='False',
        in_out='INPUT',
        socket_type='NodeSocket%s' % type
    )
    interface.new_socket(
        name='Value',
        in_out='OUTPUT',
        socket_type='NodeSocket%s' % type
    )

    nodes = node_group.nodes
    links = node_group.links

    nodes.clear()

    group_input = nodes.new('NodeGroupInput')
    group_input.location = grid_location(0, 1)
    group_output = nodes.new('NodeGroupOutput')
    group_output.location = grid_location(3, 0)

    greater_than_node = nodes.new(type='ShaderNodeMath')
    greater_than_node.operation = 'GREATER_THAN'
    greater_than_node.inputs[1].default_value = 0.0
    greater_than_node.location = grid_location(1, 0)
    links.new(group_input.outputs['Value'], greater_than_node.inputs['Value'])

    mix_node = nodes.new(type='ShaderNodeMix')
    mix_node.blend_type = 'MIX'
    mix_node.data_type = type.upper() if type != "Color" else "RGBA"
    mix_node.location = grid_location(2, 0)
    links.new(greater_than_node.outputs['Value'], mix_node.inputs['Factor'])
    links.new(group_input.outputs['True'], mix_node.inputs['B'])
    links.new(group_input.outputs['False'], mix_node.inputs['A'])

    links.new(mix_node.outputs['Result'], group_output.inputs['Value'])

    return node_group

def invert_channel(channel="Green"):
    channels = ["Red", "Green", "Blue"]
    if channel not in channels:
        return None
    
    unaffected_channels = channels
    unaffected_channels.remove(channel)

    name = 'Invert ' + channel
    if name in bpy.data.node_groups:
        return bpy.data.node_groups[name]

    node_group = bpy.data.node_groups.new(name, 'ShaderNodeTree')
    node_group.color_tag = 'COLOR'

    interface = node_group.interface
    interface.new_socket(
        name='Color',
        in_out='INPUT',
        socket_type='NodeSocketColor'
    )
    interface.new_socket(
        name='Color',
        in_out='OUTPUT',
        socket_type='NodeSocketColor'
    )

    nodes = node_group.nodes
    links = node_group.links

    nodes.clear()

    group_input = nodes.new('NodeGroupInput')
    group_output = nodes.new('NodeGroupOutput')

    sep_col_node = nodes.new(type='ShaderNodeSeparateColor')
    links.new(group_input.outputs['Color'], sep_col_node.inputs['Color'])

    # 1 - Selected Channel
    subtract_node = nodes.new(type='ShaderNodeMath')
    subtract_node.operation = 'SUBTRACT'
    subtract_node.inputs[0].default_value = 1.0
    links.new(sep_col_node.outputs[channel], subtract_node.inputs[1])

    # Combine again
    cmb_col_shader = nodes.new(type="ShaderNodeCombineColor")
    for unaffected_channel in unaffected_channels:
        links.new(sep_col_node.outputs[unaffected_channel], cmb_col_shader.inputs[unaffected_channel])
    links.new(subtract_node.outputs[0], cmb_col_shader.inputs[channel])
	
    links.new(cmb_col_shader.outputs['Color'], group_output.inputs['Color'])

    return node_group