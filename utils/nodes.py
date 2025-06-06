import bpy

def grid_location(x, y):
    return (x * 300, y * -80)

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