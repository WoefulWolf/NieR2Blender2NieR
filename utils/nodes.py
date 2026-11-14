import bpy

from .util import getTexture

def grid_location(x, y):
    return (x * 300, y * -80)

def set_color_tag(node_group, tag):
    if hasattr(node_group, 'color_tag'):
        node_group.color_tag = tag

def mix_socket(sockets, name, type):
    identifier = '%s_%s' % (name, type)
    for socket in sockets:
        if socket.identifier == identifier:
            return socket
    return sockets[name]

def if_nz(type="Float"):
    types = ["Float", "Vector", "Color"]

    if type not in types:
        return None

    name = 'If Non-Zero (%s)' % type

    if name in bpy.data.node_groups:
        return bpy.data.node_groups[name]

    node_group = bpy.data.node_groups.new(name, 'ShaderNodeTree')
    set_color_tag(node_group, 'CONVERTER')

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
    links.new(greater_than_node.outputs['Value'], mix_socket(mix_node.inputs, 'Factor', 'Float'))
    links.new(group_input.outputs['True'], mix_socket(mix_node.inputs, 'B', type))
    links.new(group_input.outputs['False'], mix_socket(mix_node.inputs, 'A', type))

    links.new(mix_socket(mix_node.outputs, 'Result', type), group_output.inputs['Value'])

    return node_group

def binarize(type="Float"):
    types = ["Float", "Vector", "Color"]

    if type not in types:
        return None

    name = 'Binarize (%s)' % type

    if name in bpy.data.node_groups:
        return bpy.data.node_groups[name]

    node_group = bpy.data.node_groups.new(name, 'ShaderNodeTree')
    set_color_tag(node_group, 'CONVERTER')

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
    greater_than_node.inputs[1].default_value = 0.1
    greater_than_node.location = grid_location(1, 0)
    links.new(group_input.outputs['Value'], greater_than_node.inputs['Value'])

    mix_node = nodes.new(type='ShaderNodeMix')
    mix_node.blend_type = 'MIX'
    mix_node.data_type = type.upper() if type != "Color" else "RGBA"
    mix_node.location = grid_location(2, 0)
    links.new(greater_than_node.outputs['Value'], mix_socket(mix_node.inputs, 'Factor', 'Float'))
    links.new(group_input.outputs['True'], mix_socket(mix_node.inputs, 'B', type))
    links.new(group_input.outputs['False'], mix_socket(mix_node.inputs, 'A', type))

    links.new(mix_socket(mix_node.outputs, 'Result', type), group_output.inputs['Value'])

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
    set_color_tag(node_group, 'COLOR')

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


def connect(tree, socket, value):
    if isinstance(value, bpy.types.NodeSocket):
        tree.links.new(value, socket)
    elif value is not None:
        socket.default_value = value

def add_node(tree, bl_idname, location, label=None, hide=True):
    node = tree.nodes.new(bl_idname)
    node.location = location
    node.hide = hide
    if label:
        node.label = label
    return node

def math_node(tree, operation, *values, location=(0, 0), clamp=False):
    node = add_node(tree, 'ShaderNodeMath', location)
    node.operation = operation
    node.use_clamp = clamp
    for socket, value in zip(node.inputs, values):
        connect(tree, socket, value)
    return node.outputs[0]

def vector_math_node(tree, operation, *values, location=(0, 0)):
    node = add_node(tree, 'ShaderNodeVectorMath', location)
    node.operation = operation
    sockets = [node.inputs[0], node.inputs['Scale']] if operation == 'SCALE' else node.inputs
    for socket, value in zip(sockets, values):
        connect(tree, socket, value)
    return node.outputs[0]

def mix_node(tree, type, factor, a, b, location=(0, 0), blend='MIX'):
    node = add_node(tree, 'ShaderNodeMix', location)
    node.data_type = 'RGBA' if type == 'Color' else type.upper()
    node.blend_type = blend
    connect(tree, mix_socket(node.inputs, 'Factor', 'Float'), factor)
    connect(tree, mix_socket(node.inputs, 'A', type), a)
    connect(tree, mix_socket(node.inputs, 'B', type), b)
    return mix_socket(node.outputs, 'Result', type)

def combine_color(tree, red, green, blue, location=(0, 0)):
    node = add_node(tree, 'ShaderNodeCombineColor', location)
    for socket, value in zip(node.inputs, (red, green, blue)):
        connect(tree, socket, value)
    return node.outputs['Color']

def separate_color(tree, color, location=(0, 0)):
    node = add_node(tree, 'ShaderNodeSeparateColor', location)
    connect(tree, node.inputs['Color'], color)
    return node.outputs

GROUP_VERSION = 3

def existing_group(name):
    group = bpy.data.node_groups.get(name)
    if group is None:
        return None
    if group.get('nier_version') == GROUP_VERSION:
        return group
    group.name = name + ' (old)'
    return None

def new_group(name, inputs, outputs, tag='CONVERTER'):
    node_group = bpy.data.node_groups.new(name, 'ShaderNodeTree')
    node_group['nier_version'] = GROUP_VERSION
    set_color_tag(node_group, tag)
    for in_out, sockets in (('INPUT', inputs), ('OUTPUT', outputs)):
        for socket_name, socket_type, default in sockets:
            socket = node_group.interface.new_socket(name=socket_name, in_out=in_out, socket_type='NodeSocket' + socket_type)
            if default is not None:
                socket.default_value = default
    group_input = add_node(node_group, 'NodeGroupInput', grid_location(-1, 0), hide=False)
    group_output = add_node(node_group, 'NodeGroupOutput', grid_location(12, 0), hide=False)
    return node_group, group_input.outputs, group_output.inputs

def group_node(tree, node_group, inputs, location):
    node = add_node(tree, 'ShaderNodeGroup', location, hide=False)
    node.node_tree = node_group
    for name, value in inputs.items():
        connect(tree, node.inputs[name], value)
    return node


def parameter_key(material, name):
    for key in material.keys():
        group, _, rest = key.partition('_')
        index, _, slot = rest.partition('_')
        if group.isdigit() and index.isdigit() and slot == name:
            return key
    return name if name in material else None

def parameter_node(material, name, default, location):
    node = add_node(material.node_tree, 'ShaderNodeValue', location, label=name, hide=False)
    node.width = 200
    key = parameter_key(material, name)
    if key is None:
        node.outputs[0].default_value = default
        return node
    node.outputs[0].default_value = float(material[key])
    driver = node.outputs[0].driver_add('default_value').driver
    driver.type = 'AVERAGE'
    variable = driver.variables.new()
    variable.type = 'SINGLE_PROP'
    target = variable.targets[0]
    target.id_type = 'MATERIAL'
    target.id = material
    target.data_path = '["%s"]' % key
    return node

def enum_value(material, prop, item):
    return material.bl_rna.properties[prop].enum_items[item].value

def flag_driver(material, prop, keys, on, off):
    driver = material.driver_add(prop).driver
    driver.type = 'SCRIPTED'
    for i, key in enumerate(keys):
        variable = driver.variables.new()
        variable.name = 'flag%d' % i
        variable.type = 'SINGLE_PROP'
        target = variable.targets[0]
        target.id_type = 'MATERIAL'
        target.id = material
        target.data_path = '["%s"]' % key
    flags = ', '.join(variable.name for variable in driver.variables)
    driver.expression = '%d if %s else %d' % (on, 'max(%s)' % flags if len(keys) > 1 else flags, off)

def blend_mode_driver(material, names):
    keys = [key for key in (parameter_key(material, name) for name in names) if key is not None]
    if not keys:
        return
    if hasattr(material, 'surface_render_method'):
        flag_driver(material, 'surface_render_method', keys, enum_value(material, 'surface_render_method', 'BLENDED'), enum_value(material, 'surface_render_method', material.surface_render_method))
        return
    flag_driver(material, 'blend_method', keys, enum_value(material, 'blend_method', 'BLEND'), enum_value(material, 'blend_method', material.blend_method))
    flag_driver(material, 'shadow_method', keys, enum_value(material, 'shadow_method', 'NONE'), enum_value(material, 'shadow_method', material.shadow_method))

TEXTURE_TYPE_NAMES = [
    ['g_AlbedoMap1', 'g_AlbedoMap', 'g_AlbedoColor'],
    ['g_AlbedoMap2', 'g_PatternColorMap'],
    ['g_AlbedoMap3'],
    ['g_NormalMap1', 'g_NormalMap'],
    ['g_NormalMap2'],
    ['g_NormalMap3'],
    ['g_DetailNormalMap'],
    ['g_EnvMap'],
    ['g_MaskMap'],
    ['g_MaskMap2', 'g_EnvMapSp', 'g_ColorBlendMap', 'g_GradationMap'],
    ['g_LUT', 'g_SpreadPatternMap', 'g_BlendMap'],
    ['g_CurvatureMap', 'g_ParallaxMap'],
    ['g_LightMap'],
]

FLAT_NORMAL = (0.5, 0.5, 1.0, 1.0)
WHITE = (1.0, 1.0, 1.0, 1.0)

TEXTURE_DEFAULTS = [
    WHITE,
    WHITE,
    WHITE,
    FLAT_NORMAL,
    FLAT_NORMAL,
    FLAT_NORMAL,
    FLAT_NORMAL,
    None,
    (0.0, 0.0, 1.0, 0.0),
    (0.0, 0.0, 0.0, 0.0),
    None,
    None,
    WHITE,
]

CORE_TEXTURES = {
    '4e9c16f4': WHITE,
    '5864a24f': WHITE,
    '132ed5c3': (0.0, 0.0, 0.0, 1.0),
}

def texture_names(name):
    for names in TEXTURE_TYPE_NAMES:
        if name in names:
            return names
    return [name]

def texture_default(name):
    for names, default in zip(TEXTURE_TYPE_NAMES, TEXTURE_DEFAULTS):
        if name in names:
            return default
    return None

def flat_image(name, color, non_color):
    image = bpy.data.images.get(name)
    if image is None:
        image = bpy.data.images.new(name, 1, 1, alpha=True, float_buffer=True)
        image.generated_color = color
    if non_color:
        image.colorspace_settings.name = 'Non-Color'
    return image

CORE_PROCEDURAL_TEXTURES = {
    '7fd4929a': lambda: noise_normal(),
}

def texture_node(material, texture_dir, name, location, uv=None, non_color=False):
    tree = material.node_tree
    found = next((n for n in texture_names(name) if n in material), None)
    texture_id = material[found].lower() if found is not None else None
    texture_path = getTexture(texture_dir, material[found]) if found is not None else None
    if texture_path is None and texture_id in CORE_PROCEDURAL_TEXTURES:
        print('%s texture not found, using a procedural stand-in: %s' % (found, texture_id))
        node = group_node(tree, CORE_PROCEDURAL_TEXTURES[texture_id](), {'Vector': uv}, location)
        node.label = found
        node.hide = True
        return node

    node = add_node(tree, 'ShaderNodeTexImage', location)
    connect(tree, node.inputs['Vector'], uv)
    node.label = found or name
    if texture_path is not None:
        node.image = bpy.data.images.load(texture_path)
        if non_color:
            node.image.colorspace_settings.name = 'Non-Color'
        return node

    if texture_id:
        print('%s texture not found: %s' % (found, texture_id))
    core = CORE_TEXTURES.get(texture_id) if texture_id else None
    if core is not None:
        node.image = flat_image('Core %s' % texture_id, core, non_color)
    elif texture_default(name) is not None:
        node.image = flat_image('Default %s' % texture_names(name)[0], texture_default(name), non_color)
    return node

def uv_node(tree, uv_map, location):
    node = add_node(tree, 'ShaderNodeUVMap', location, label='UV1' if uv_map == 'UVMap1' else 'UV2')
    node.uv_map = uv_map
    return node.outputs['UV']

def material_output(tree, surface, location):
    node = add_node(tree, 'ShaderNodeOutputMaterial', location, hide=False)
    connect(tree, node.inputs['Surface'], surface)
    return node


def linear_to_srgb():
    name = 'Linear to sRGB'
    group = existing_group(name)
    if group is not None:
        return group
    group, inputs, outputs = new_group(name, [('Color', 'Color', None)], [('Color', 'Color', None)], 'COLOR')
    channels = separate_color(group, inputs['Color'], grid_location(0, 0))
    encoded = []
    for i in range(3):
        y = i * 3
        low = math_node(group, 'MULTIPLY', channels[i], 12.92, location=grid_location(1, y))
        high = math_node(group, 'MULTIPLY_ADD', math_node(group, 'POWER', channels[i], 1 / 2.4, location=grid_location(1, y + 1)), 1.055, -0.055, location=grid_location(2, y + 1))
        above = math_node(group, 'GREATER_THAN', channels[i], 0.0031308, location=grid_location(2, y + 2))
        encoded.append(mix_node(group, 'Float', above, low, high, location=grid_location(3, y)))
    connect(group, outputs['Color'], combine_color(group, *encoded, location=grid_location(4, 0)))
    return group

def uv_tiling():
    name = 'NieR UV Tiling'
    group = existing_group(name)
    if group is not None:
        return group
    group, inputs, outputs = new_group(name, [('UV', 'Vector', None), ('X', 'Float', 1.0), ('Y', 'Float', 1.0)], [('UV', 'Vector', None)], 'VECTOR')
    scale = add_node(group, 'ShaderNodeCombineXYZ', grid_location(0, 1))
    connect(group, scale.inputs['X'], inputs['X'])
    connect(group, scale.inputs['Y'], inputs['Y'])
    scale.inputs['Z'].default_value = 1.0
    connect(group, outputs['UV'], vector_math_node(group, 'MULTIPLY', inputs['UV'], scale.outputs[0], location=grid_location(1, 0)))
    return group

def noise_normal():
    name = 'NieR Noise Normal'
    group = existing_group(name)
    if group is not None:
        return group
    group, inputs, outputs = new_group(name, [
        ('Vector', 'Vector', None),
        ('Scale X', 'Float', 40.0),
        ('Scale Y', 'Float', 96.0),
        ('Strength X', 'Float', 0.89),
        ('Strength Y', 'Float', 1.84),
        ('Step', 'Float', 1.5 / 128.0),
    ], [('Color', 'Color', None)], 'TEXTURE')

    scale = add_node(group, 'ShaderNodeCombineXYZ', grid_location(0, 1))
    connect(group, scale.inputs['X'], inputs['Scale X'])
    connect(group, scale.inputs['Y'], inputs['Scale Y'])
    scale.inputs['Z'].default_value = 1.0

    def height(offset, y):
        point = inputs['Vector']
        if offset is not None:
            step = add_node(group, 'ShaderNodeCombineXYZ', grid_location(0, y + 1))
            connect(group, step.inputs[offset], inputs['Step'])
            point = vector_math_node(group, 'ADD', point, step.outputs[0], location=grid_location(1, y))
        point = vector_math_node(group, 'MULTIPLY', point, scale.outputs[0], location=grid_location(2, y))
        noise = add_node(group, 'ShaderNodeTexNoise', grid_location(3, y))
        noise.inputs['Scale'].default_value = 1.0
        noise.inputs['Detail'].default_value = 0.0
        connect(group, noise.inputs['Vector'], point)
        return noise.outputs['Fac']

    centre = height(None, 0)
    slopes = [math_node(group, 'MULTIPLY_ADD', math_node(group, 'SUBTRACT', centre, height(axis, 3 + i * 3), location=grid_location(4, 3 + i * 3)), inputs['Strength ' + axis], 0.5, location=grid_location(5, 3 + i * 3))
              for i, axis in enumerate(('X', 'Y'))]
    connect(group, outputs['Color'], combine_color(group, slopes[0], slopes[1], 1.0, location=grid_location(6, 0)))
    return group

def tangent_normal():
    name = 'NieR Tangent Normal'
    group = existing_group(name)
    if group is not None:
        return group
    flat = (0.5, 0.5, 1.0, 1.0)
    group, inputs, outputs = new_group(name, [
        ('Normal Map', 'Color', flat),
        ('Use Normal Map', 'Float', 1.0),
        ('Detail Normal Map', 'Color', flat),
        ('Detail Strength', 'Float', 0.0),
        ('Use Detail Normal Map', 'Float', 0.0),
        ('Offset', 'Vector', (0.0, 0.0, 0.0)),
        ('Shift', 'Float', 0.0),
    ], [('Normal', 'Vector', None)], 'VECTOR')

    color = mix_node(group, 'Color', inputs['Use Normal Map'], flat, inputs['Normal Map'], location=grid_location(0, 0))
    normal = vector_math_node(group, 'SUBTRACT', color, (0.5, 0.5, 0.5), location=grid_location(1, 0))
    detail = vector_math_node(group, 'MULTIPLY_ADD', inputs['Detail Normal Map'], (2.0, 2.0, 0.0), (-1.0, -1.0, 0.0), location=grid_location(0, 2))
    strength = math_node(group, 'MULTIPLY', inputs['Detail Strength'], inputs['Use Detail Normal Map'], location=grid_location(0, 3))
    normal = vector_math_node(group, 'MULTIPLY_ADD', detail, strength, normal, location=grid_location(2, 1))
    normal = vector_math_node(group, 'ADD', normal, inputs['Offset'], location=grid_location(3, 1))
    normal = vector_math_node(group, 'NORMALIZE', normal, location=grid_location(4, 1))
    shift = vector_math_node(group, 'SCALE', (1.0, -1.0, 1.0), inputs['Shift'], location=grid_location(4, 2))
    normal = vector_math_node(group, 'SUBTRACT', normal, shift, location=grid_location(5, 1))
    normal = vector_math_node(group, 'NORMALIZE', normal, location=grid_location(6, 1))
    encoded = vector_math_node(group, 'MULTIPLY_ADD', normal, (0.5, -0.5, 0.5), (0.5, 0.5, 0.5), location=grid_location(7, 1))

    normal_map = add_node(group, 'ShaderNodeNormalMap', grid_location(8, 1))
    normal_map.uv_map = 'UVMap1'
    connect(group, normal_map.inputs['Color'], encoded)
    connect(group, outputs['Normal'], normal_map.outputs['Normal'])
    return group

def surface():
    name = 'NieR Surface'
    group = existing_group(name)
    if group is not None:
        return group
    group, inputs, outputs = new_group(name, [
        ('Shader', 'Shader', None),
        ('Occlusion', 'Float', 1.0),
        ('Alpha', 'Float', 1.0),
        ('1-Bit Mask', 'Float', 0.0),
        ('Decal', 'Float', 0.0),
    ], [('Shader', 'Shader', None)], 'SHADER')

    black = add_node(group, 'ShaderNodeEmission', grid_location(0, 1), label='No light')
    black.inputs['Color'].default_value = (0.0, 0.0, 0.0, 1.0)
    black.inputs['Strength'].default_value = 0.0
    occluded = add_node(group, 'ShaderNodeMixShader', grid_location(1, 0), label='Occlusion')
    connect(group, occluded.inputs[0], inputs['Occlusion'])
    connect(group, occluded.inputs[1], black.outputs[0])
    connect(group, occluded.inputs[2], inputs['Shader'])

    kept = math_node(group, 'GREATER_THAN', inputs['Alpha'], 0.8 - 1e-6, location=grid_location(0, 3))
    visible = mix_node(group, 'Float', inputs['1-Bit Mask'], 1.0, kept, location=grid_location(1, 3))
    blended = mix_node(group, 'Float', inputs['Decal'], 1.0, inputs['Alpha'], location=grid_location(1, 4))
    light_path = add_node(group, 'ShaderNodeLightPath', grid_location(0, 5))
    no_shadow = math_node(group, 'MULTIPLY', inputs['Decal'], light_path.outputs['Is Shadow Ray'], location=grid_location(1, 5))
    coverage = math_node(group, 'MULTIPLY', visible, blended, location=grid_location(2, 3))
    coverage = math_node(group, 'MULTIPLY', coverage, math_node(group, 'SUBTRACT', 1.0, no_shadow, location=grid_location(2, 5)), location=grid_location(3, 3))
    transparent = add_node(group, 'ShaderNodeBsdfTransparent', grid_location(1, 2))
    cut_out = add_node(group, 'ShaderNodeMixShader', grid_location(4, 0), label='Cut-out')
    connect(group, cut_out.inputs[0], coverage)
    connect(group, cut_out.inputs[1], transparent.outputs[0])
    connect(group, cut_out.inputs[2], occluded.outputs[0])
    connect(group, outputs['Shader'], cut_out.outputs[0])
    return group

def layer_blend(type):
    name = 'NieR Layer Blend (%s)' % type
    group = existing_group(name)
    if group is not None:
        return group
    group, inputs, outputs = new_group(name, [
        ('Weight 2', 'Float', 0.0),
        ('Weight 3', 'Float', 0.0),
        ('Layer 1', type, None),
        ('Layer 2', type, None),
        ('Layer 3', type, None),
    ], [('Result', type, None)])
    blended = mix_node(group, type, inputs['Weight 2'], inputs['Layer 1'], inputs['Layer 2'], location=grid_location(0, 0))
    connect(group, outputs['Result'], mix_node(group, type, inputs['Weight 3'], blended, inputs['Layer 3'], location=grid_location(1, 0)))
    return group

def fuzz():
    name = 'NieR Fuzz'
    group = existing_group(name)
    if group is not None:
        return group
    group, inputs, outputs = new_group(name, [
        ('Color', 'Color', (0.8, 0.8, 0.8, 1.0)),
        ('Normal', 'Vector', None),
        ('Fuzz Mask', 'Float', 0.0),
        ('Exponent', 'Float', 1.0),
        ('Highlight', 'Float', 1.0),
        ('Mask Effective', 'Float', 0.0),
        ('Reverse', 'Float', 0.0),
        ('Multiply', 'Float', 0.0),
        ('Correction', 'Color', (1.0, 1.0, 1.0, 1.0)),
    ], [('Color', 'Color', None)], 'COLOR')

    facing = add_node(group, 'ShaderNodeLayerWeight', grid_location(0, 1))
    facing.inputs['Blend'].default_value = 0.5
    connect(group, facing.inputs['Normal'], inputs['Normal'])
    rim = math_node(group, 'POWER', facing.outputs['Facing'], inputs['Exponent'], location=grid_location(1, 1))

    hsv = add_node(group, 'ShaderNodeSeparateColor', grid_location(0, -2))
    hsv.mode = 'HSV'
    connect(group, hsv.inputs['Color'], inputs['Color'])
    hsl = add_node(group, 'ShaderNodeCombineColor', grid_location(1, -2))
    hsl.mode = 'HSL'
    connect(group, hsl.inputs[0], hsv.outputs[0])
    connect(group, hsl.inputs[1], hsv.outputs[1])
    hsl.inputs[2].default_value = 0.5
    has_hue = math_node(group, 'GREATER_THAN', hsv.outputs[0], 0.0, location=grid_location(1, -3))
    tint = mix_node(group, 'Color', has_hue, (0.0, 0.0, 0.0, 1.0), hsl.outputs[0], location=grid_location(2, -2))

    grazing = math_node(group, 'DIVIDE', rim, math_node(group, 'MAXIMUM', inputs['Mask Effective'], 1e-6, location=grid_location(1, 3)), location=grid_location(2, 2))
    fuzz_mask = mix_node(group, 'Float', grazing, inputs['Fuzz Mask'], 1.0, location=grid_location(3, 2))
    amount = math_node(group, 'MULTIPLY', fuzz_mask, math_node(group, 'MULTIPLY', rim, inputs['Highlight'], location=grid_location(2, 1)), location=grid_location(4, 1))
    amount = mix_node(group, 'Float', inputs['Reverse'], amount, math_node(group, 'SUBTRACT', 1.0, amount, location=grid_location(5, 2)), location=grid_location(6, 1))

    fuzz = vector_math_node(group, 'MULTIPLY', vector_math_node(group, 'SCALE', tint, amount, location=grid_location(7, -1)), inputs['Correction'], location=grid_location(8, -1))
    added = mix_node(group, 'Color', 1.0, inputs['Color'], fuzz, location=grid_location(9, -2), blend='ADD')
    multiplied = mix_node(group, 'Color', 1.0, inputs['Color'], fuzz, location=grid_location(9, -1), blend='MULTIPLY')
    fuzzed = mix_node(group, 'Color', inputs['Multiply'], added, multiplied, location=grid_location(10, -1))

    boost = mix_node(group, 'Float', rim, 1.0, inputs['Highlight'], location=grid_location(9, 1))
    connect(group, outputs['Color'], vector_math_node(group, 'SCALE', fuzzed, boost, location=grid_location(11, 0)))
    return group

def anisotropy():
    name = 'NieR Anisotropy'
    group = existing_group(name)
    if group is not None:
        return group
    group, inputs, outputs = new_group(name, [
        ('Glossiness', 'Float', 0.0),
        ('Mask', 'Float', 0.0),
        ('Mode', 'Float', 0.0),
        ('Mode 2', 'Float', 0.0),
        ('Anisotropic', 'Float', 0.0),
        ('Anisotropic X', 'Float', 0.0),
        ('Anisotropic Y', 'Float', 0.0),
    ], [('Roughness', 'Float', None), ('Anisotropy', 'Float', None), ('Rotation', 'Float', None), ('Active', 'Float', None)])

    def math(operation, *values, x=0, y=0, clamp=False):
        return math_node(group, operation, *values, location=grid_location(x, y), clamp=clamp)

    roughness = math('SUBTRACT', 1.0, inputs['Glossiness'])
    masked = math('GREATER_THAN', inputs['Mask'], 0.0, y=1)
    on_2 = math('MULTIPLY', masked, math('GREATER_THAN', inputs['Mode 2'], 0.0, y=3), x=1, y=3)
    on_1 = math('MULTIPLY', math('MULTIPLY', masked, math('GREATER_THAN', inputs['Mode'], 0.0, y=2), x=1, y=2), math('SUBTRACT', 1.0, on_2, x=2, y=3), x=2, y=2)

    alpha = math('MAXIMUM', math('MULTIPLY', roughness, roughness, x=1, y=5), 0.001, x=2, y=5)
    alpha_2 = math('MULTIPLY', alpha, alpha, x=3, y=5)

    def axis(name, y):
        exponent = math('DIVIDE', inputs[name], alpha_2, x=4, y=y)
        return math('SQRT', math('DIVIDE', 2.0, math('ADD', exponent, 2.0, x=5, y=y), x=6, y=y), x=7, y=y)
    alpha_x = axis('Anisotropic X', 6)
    alpha_y = axis('Anisotropic Y', 7)
    roughness_2 = math('POWER', math('MULTIPLY', alpha_x, alpha_y, x=8, y=6), 0.25, x=9, y=6)
    ratio = math('DIVIDE', math('MINIMUM', alpha_x, alpha_y, x=8, y=7), math('MAXIMUM', alpha_x, alpha_y, x=8, y=8), x=9, y=7)
    anisotropy_2 = math('SUBTRACT', math('SQRT', ratio, x=10, y=7), 1.0, x=11, y=7)
    rotation_2 = math('MULTIPLY', math('GREATER_THAN', alpha_y, alpha_x, x=9, y=8), 0.25, x=10, y=8)
    anisotropy_1 = math('SUBTRACT', math('SQRT', math('MULTIPLY_ADD', inputs['Anisotropic'], -0.9, 1.0, x=1, y=4), x=2, y=4), 1.0, x=3, y=4)

    shading = mix_node(group, 'Float', on_1, roughness, math('MULTIPLY', roughness, roughness, x=3, y=0), location=grid_location(4, 0))
    connect(group, outputs['Roughness'], mix_node(group, 'Float', on_2, shading, roughness_2, location=grid_location(11, 0)))
    anisotropy = mix_node(group, 'Float', on_1, 0.0, anisotropy_1, location=grid_location(4, 2))
    connect(group, outputs['Anisotropy'], mix_node(group, 'Float', on_2, anisotropy, anisotropy_2, location=grid_location(11, 2)))
    connect(group, outputs['Rotation'], mix_node(group, 'Float', on_2, 0.0, rotation_2, location=grid_location(11, 8)))
    connect(group, outputs['Active'], math('ADD', on_1, on_2, x=11, y=9))
    return group

def specular_lobe():
    name = 'NieR Specular Lobe'
    group = existing_group(name)
    if group is not None:
        return group
    group, inputs, outputs = new_group(name, [
        ('Color', 'Color', (0.8, 0.8, 0.8, 1.0)),
        ('Metallic', 'Float', 0.0),
        ('Roughness', 'Float', 0.5),
        ('Anisotropy', 'Float', 0.0),
        ('Rotation', 'Float', 0.0),
        ('Normal', 'Vector', None),
        ('Tangent', 'Vector', None),
        ('Dielectric', 'Float', 0.08),
        ('Tint', 'Color', (1.0, 1.0, 1.0, 1.0)),
    ], [('BSDF', 'Shader', None)], 'SHADER')

    dielectric = combine_color(group, inputs['Dielectric'], inputs['Dielectric'], inputs['Dielectric'], location=grid_location(0, 1))
    reflectance = mix_node(group, 'Color', inputs['Metallic'], dielectric, inputs['Color'], location=grid_location(1, 0))
    reflectance = mix_node(group, 'Color', 1.0, reflectance, inputs['Tint'], location=grid_location(2, 0), blend='MULTIPLY')
    if hasattr(bpy.types, 'ShaderNodeBsdfMetallic'):
        lobe = add_node(group, 'ShaderNodeBsdfMetallic', grid_location(4, 0), hide=False)
        lobe.fresnel_type = 'F82'
        connect(group, lobe.inputs['Edge Tint'], inputs['Tint'])
        connect(group, lobe.inputs['Base Color'], reflectance)
    else:
        lobe = add_node(group, 'ShaderNodeBsdfGlossy', grid_location(4, 0), hide=False)
        facing = add_node(group, 'ShaderNodeLayerWeight', grid_location(2, 2))
        facing.inputs['Blend'].default_value = 0.5
        connect(group, facing.inputs['Normal'], inputs['Normal'])
        edge = math_node(group, 'POWER', facing.outputs['Facing'], 5.0, location=grid_location(3, 2))
        connect(group, lobe.inputs['Color'], mix_node(group, 'Color', edge, reflectance, inputs['Tint'], location=grid_location(3, 0)))
    lobe.distribution = 'GGX'
    for socket_name in ('Roughness', 'Anisotropy', 'Rotation', 'Normal', 'Tangent'):
        connect(group, lobe.inputs[socket_name], inputs[socket_name])
    connect(group, outputs['BSDF'], lobe.outputs[0])
    return group

def shading():
    name = 'NieR Shading'
    group = existing_group(name)
    if group is not None:
        return group
    group, inputs, outputs = new_group(name, [
        ('Color', 'Color', (0.8, 0.8, 0.8, 1.0)),
        ('Metallic', 'Float', 0.0),
        ('Roughness', 'Float', 0.5),
        ('Anisotropy', 'Float', 0.0),
        ('Rotation', 'Float', 0.0),
        ('Normal', 'Vector', None),
        ('Specular Normal', 'Vector', None),
        ('Tangent', 'Vector', None),
    ], [('BSDF', 'Shader', None)], 'SHADER')

    diffuse = add_node(group, 'ShaderNodeBsdfDiffuse', grid_location(1, -2), hide=False)
    dielectric = math_node(group, 'SUBTRACT', 1.0, inputs['Metallic'], location=grid_location(0, -2))
    connect(group, diffuse.inputs['Color'], vector_math_node(group, 'SCALE', inputs['Color'], dielectric, location=grid_location(0, -3)))
    connect(group, diffuse.inputs['Normal'], inputs['Normal'])

    lobe = group_node(group, specular_lobe(), {
        'Color': inputs['Color'],
        'Metallic': inputs['Metallic'],
        'Roughness': inputs['Roughness'],
        'Anisotropy': inputs['Anisotropy'],
        'Rotation': inputs['Rotation'],
        'Normal': inputs['Specular Normal'],
        'Tangent': inputs['Tangent'],
    }, grid_location(1, 2))

    added = add_node(group, 'ShaderNodeAddShader', grid_location(3, 0))
    connect(group, added.inputs[0], diffuse.outputs['BSDF'])
    connect(group, added.inputs[1], lobe.outputs['BSDF'])
    connect(group, outputs['BSDF'], added.outputs[0])
    return group
