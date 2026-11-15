import math
import os
import random
import time

import bmesh
import bpy
import numpy as np

from .ddsBc1 import writeGreyBc1Dds
from .nodes import parameter_key

PUSH_DISTANCE = 0.003
DILATE_STEPS = 16
OWN_UV_OVERLAP_LIMIT = 0.02
OWN_UV_CHECK_SIZE = 512
MINIMUM_ATLAS_FILL = 0.02
MINIMUM_TEXTURE_SIZE = 32
BAKE_NODE_NAME = 'NA Lightmap Bake'
BAKE_UV_NAME = 'NA Lightmap UV'


class LightmapBakeError(Exception):
    pass


def wmbMeshes():
    if 'WMB' not in bpy.data.collections:
        return []
    return [obj for obj in bpy.data.collections['WMB'].all_objects
            if obj.type == 'MESH' and obj.mesh_group_props.lod_level >= 0]


def parameterValue(material, name):
    key = parameter_key(material, name)
    return float(material[key]) if key is not None else 0.0


def canTakeLightmap(material):
    return material is not None and parameter_key(material, 'g_UseOcclusionMap') is not None \
        and not parameterValue(material, 'g_Decal') and not parameterValue(material, 'g_1BitMask')


def keepsSecondUv(material):
    return material.get('Shader_Name') != 'PBS00_XXXXX' or parameterValue(material, 'g_UV2Use') != 0 \
        or parameterValue(material, 'g_UseDetailNormalMap') != 0


def blocksLight(material):
    return material is not None and not str(material.get('Shader_Name', '')).startswith('CNS') \
        and not parameterValue(material, 'g_Decal') and not parameterValue(material, 'g_1BitMask')


def listedMaterials():
    found = set()
    for obj in wmbMeshes():
        for slot in obj.material_slots:
            if canTakeLightmap(slot.material):
                found.add(slot.material)
    return sorted(found, key=lambda material: material.name.lower())


def faceMask(obj, materials):
    slots = [index for index, slot in enumerate(obj.material_slots) if slot.material in materials]
    indices = np.empty(len(obj.data.polygons), np.int64)
    obj.data.polygons.foreach_get('material_index', indices)
    return np.isin(indices, slots)


def surfaceAreas(obj, mask):
    mesh = obj.data
    mesh.calc_loop_triangles()
    count = len(mesh.loop_triangles)
    loops = np.empty(count * 3, np.int64)
    mesh.loop_triangles.foreach_get('loops', loops)
    vertices = np.empty(count * 3, np.int64)
    mesh.loop_triangles.foreach_get('vertices', vertices)
    polygons = np.empty(count, np.int64)
    mesh.loop_triangles.foreach_get('polygon_index', polygons)
    keep = mask[polygons]
    positions = np.empty(len(mesh.vertices) * 3, np.float32)
    mesh.vertices.foreach_get('co', positions)
    matrix = np.array(obj.matrix_world)
    positions = positions.reshape(-1, 3) @ matrix[:3, :3].T + matrix[:3, 3]
    corners = positions[vertices.reshape(-1, 3)[keep]]
    worldArea = np.linalg.norm(np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0]), axis=1).sum() / 2
    uvs = np.empty(len(mesh.loops) * 2, np.float32)
    mesh.uv_layers[1].data.foreach_get('uv', uvs)
    uvCorners = uvs.reshape(-1, 2)[loops.reshape(-1, 3)[keep]]
    first, second = uvCorners[:, 1] - uvCorners[:, 0], uvCorners[:, 2] - uvCorners[:, 0]
    uvArea = np.abs(first[:, 0] * second[:, 1] - first[:, 1] * second[:, 0]).sum() / 2
    return float(worldArea), float(uvArea)


def scaledTextureSizes(worldAreas, largest, scaleToArea):
    biggest = max(worldAreas.values(), default=0.0)
    sizes = {}
    for key, area in worldAreas.items():
        if not scaleToArea or biggest <= 0 or area <= 0:
            sizes[key] = largest
            continue
        wanted = largest * math.sqrt(area / biggest)
        sizes[key] = int(min(largest, max(MINIMUM_TEXTURE_SIZE, 2 ** round(math.log2(wanted)))))
    return sizes


def textureGroups(materials, sizes, largest, packTogether):
    if not packTogether:
        return [[[material], sizes[material]] for material in materials]
    pages = []
    for material in sorted(materials, key=lambda material: (-sizes[material], material.name.lower())):
        area = sizes[material] ** 2
        page = next((page for page in pages if page[1] + area <= largest * largest), None)
        if page is None:
            page = [[], 0]
            pages.append(page)
        page[0].append(material)
        page[1] += area
    groups = []
    for members, used in pages:
        size = MINIMUM_TEXTURE_SIZE
        while size * size < used:
            size *= 2
        groups.append([members, min(size, largest)])
    return groups


def secondUvTriangles(obj, mask):
    mesh = obj.data
    mesh.calc_loop_triangles()
    count = len(mesh.loop_triangles)
    loops = np.empty(count * 3, np.int64)
    mesh.loop_triangles.foreach_get('loops', loops)
    polygons = np.empty(count, np.int64)
    mesh.loop_triangles.foreach_get('polygon_index', polygons)
    uvs = np.empty(len(mesh.loops) * 2, np.float32)
    mesh.uv_layers[1].data.foreach_get('uv', uvs)
    return uvs.reshape(-1, 2)[loops.reshape(-1, 3)[mask[polygons]]]


def overlapShare(triangles, size):
    if len(triangles) == 0:
        return 0.0
    if triangles.min() < -0.001 or triangles.max() > 1.001:
        return 1.0
    grid = np.zeros((size, size), np.int32)
    for a, b, c in triangles.astype(np.float64) * size:
        low = np.clip(np.floor(np.minimum(np.minimum(a, b), c)).astype(int), 0, size - 1)
        high = np.clip(np.ceil(np.maximum(np.maximum(a, b), c)).astype(int), 0, size)
        area = (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])
        if (high <= low).any() or abs(area) < 1e-12:
            continue
        xs, ys = np.meshgrid(np.arange(low[0], high[0]) + 0.5, np.arange(low[1], high[1]) + 0.5)
        first = ((xs - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (ys - a[1])) / area
        second = ((b[0] - a[0]) * (ys - a[1]) - (xs - a[0]) * (b[1] - a[1])) / area
        grid[low[1]:high[1], low[0]:high[0]] += (first >= 0) & (second >= 0) & (first + second <= 1)
    covered = int((grid > 0).sum())
    return float((grid > 1).sum()) / covered if covered else 0.0


def cornerNormals(mesh):
    normals = np.empty(len(mesh.loops) * 3, np.float32)
    if hasattr(mesh, 'corner_normals') and len(mesh.corner_normals) == len(mesh.loops):
        mesh.corner_normals.foreach_get('vector', normals)
    else:
        mesh.calc_normals_split()
        mesh.loops.foreach_get('normal', normals)
    return normals.reshape(-1, 3)


def splitSecondUvSeams(mesh):
    normals = cornerNormals(mesh)
    before = len(mesh.vertices)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    layer = bm.loops.layers.uv[mesh.uv_layers[1].name]

    def uvKey(loop):
        uv = loop[layer].uv
        return round(uv.x, 6), round(uv.y, 6)

    seams = []
    for edge in bm.edges:
        if len(edge.link_faces) < 2:
            continue
        for vert in edge.verts:
            keys = {uvKey(next(loop for loop in face.loops if loop.vert is vert)) for face in edge.link_faces}
            if len(keys) > 1:
                seams.append(edge)
                break
    bmesh.ops.split_edges(bm, edges=seams)
    for vert in list(bm.verts):
        groups = {}
        for loop in vert.link_loops:
            groups.setdefault(uvKey(loop), []).append(loop)
        for loops in list(groups.values())[1:]:
            for loop in loops:
                bmesh.utils.loop_separate(loop)
    bm.to_mesh(mesh)
    bm.free()
    if hasattr(mesh, 'use_auto_smooth'):
        mesh.use_auto_smooth = True
    mesh.normals_split_custom_set(normals)
    return len(mesh.vertices) - before


def unwrapAtlas(context, masks, resolution, marginPixels):
    objects = list(masks)
    previousActive = {obj: obj.data.uv_layers.active_index for obj in objects}
    for obj in objects:
        obj.data.polygons.foreach_set('select', masks[obj])
        obj.data.uv_layers.active_index = 1
    for obj in context.view_layer.objects:
        obj.select_set(obj in masks)
    context.view_layer.objects.active = objects[0]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.0, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.average_islands_scale()
    bpy.ops.uv.pack_islands(rotate=True, margin_method='FRACTION', margin=marginPixels / resolution, shape_method='CONCAVE')
    bpy.ops.object.mode_set(mode='OBJECT')
    for obj, index in previousActive.items():
        obj.data.uv_layers.active_index = index


def useConfiguredDevice(scene):
    try:
        preferences = bpy.context.preferences.addons['cycles'].preferences
        preferences.get_devices()
        if preferences.compute_device_type != 'NONE' and any(device.use and device.type != 'CPU' for device in preferences.devices):
            scene.cycles.device = 'GPU'
            return preferences.compute_device_type
    except (KeyError, AttributeError):
        pass
    scene.cycles.device = 'CPU'
    return 'CPU'


def newBakeImage(name, size):
    image = bpy.data.images.new(name, size, size, alpha=True, float_buffer=True)
    image.colorspace_settings.name = 'Non-Color'
    image.generated_color = (0.0, 0.0, 0.0, 0.0)
    return image


def pushedCopy(context, obj, createdMeshes):
    copy = obj.copy()
    copy.data = obj.data.copy()
    createdMeshes.append(copy.data)
    context.scene.collection.objects.link(copy)
    copy.hide_viewport = False
    copy.hide_render = False
    copy.hide_set(False)
    mesh = copy.data
    if len(mesh.uv_layers) > 1:
        mesh.uv_layers[1].name = BAKE_UV_NAME
    positions = np.empty(len(mesh.vertices) * 3, np.float32)
    mesh.vertices.foreach_get('co', positions)
    normals = np.empty(len(mesh.vertices) * 3, np.float32)
    mesh.vertex_normals.foreach_get('vector', normals)
    scale = max(abs(value) for value in obj.matrix_world.to_scale()) or 1.0
    mesh.vertices.foreach_set('co', positions + normals * (PUSH_DISTANCE / scale))
    mesh.update()
    return copy


def joinedCopies(context, objects, name, createdMeshes):
    copies = [pushedCopy(context, obj, createdMeshes) for obj in objects]
    for obj in context.view_layer.objects:
        obj.select_set(obj in copies)
    context.view_layer.objects.active = copies[0]
    if len(copies) > 1:
        bpy.ops.object.join()
    joined = context.view_layer.objects.active
    joined.name = name
    return joined


def removeObject(obj):
    bpy.data.objects.remove(obj)


def bakedValues(image):
    pixels = np.empty(image.size[0] * image.size[1] * 4, np.float32)
    image.pixels.foreach_get(pixels)
    pixels = pixels.reshape(image.size[1], image.size[0], 4)
    return pixels[..., 1], pixels[..., 3] > 0


def dilate(values, filled, steps):
    values = np.where(filled, values, 0.0).astype(np.float32)
    filled = filled.copy()
    for _ in range(steps):
        total = np.zeros_like(values)
        count = np.zeros_like(values)
        paddedValues = np.pad(values, 1)
        paddedFilled = np.pad(filled.astype(np.float32), 1)
        for dy in (0, 1, 2):
            for dx in (0, 1, 2):
                if dy == dx == 1:
                    continue
                total += paddedValues[dy:dy + values.shape[0], dx:dx + values.shape[1]]
                count += paddedFilled[dy:dy + values.shape[0], dx:dx + values.shape[1]]
        grow = ~filled & (count > 0)
        values[grow] = total[grow] / count[grow]
        filled |= grow
    return np.where(filled, values, 1.0)


def newTextureIdentifier(scene):
    used = {str(value).lower() for material in bpy.data.materials for value in material.values() if isinstance(value, str)}
    used |= {item.texture_identifier.lower() for item in getattr(scene, 'WTAMaterials', [])}
    while True:
        identifier = '%08x' % random.getrandbits(31)
        if identifier not in used:
            return identifier


def assignLightmap(scene, material, identifier, path, image):
    material['g_LightMap'] = identifier
    material[parameter_key(material, 'g_UseOcclusionMap')] = 1.0
    if material.node_tree is not None:
        for node in material.node_tree.nodes:
            if node.type == 'TEX_IMAGE' and node.label == 'g_LightMap':
                node.image = image
    for item in getattr(scene, 'WTAMaterials', []):
        if item.parent_mat == material.name and item.texture_map_type == 'g_LightMap':
            item.texture_identifier = identifier
            item.texture_path = path


def progress(message, detail=False):
    print('[>]' if detail else '[+]', message, flush=True)


def groupLabel(members):
    return members[0].name + (' +%d more' % (len(members) - 1) if len(members) > 1 else '')


def bakeLightmaps(context, directory):
    scene = context.scene
    settings = scene.lightmap_baker
    largestSize = int(settings.max_resolution)
    started = time.perf_counter()
    lines = []
    meshes = wmbMeshes()
    ticked = [material for material in listedMaterials() if material.lightmap_bake]
    if not ticked:
        raise LightmapBakeError('No materials are ticked for baking')

    users = {material: [obj for obj in meshes if faceMask(obj, {material}).any()] for material in ticked}
    usable = []
    for material in ticked:
        missing = [obj.name for obj in users[material] if len(obj.data.uv_layers) < 2]
        if missing:
            lines.append('Skipped %s: %s has no second UV map' % (material.name, missing[0]))
        else:
            usable.append(material)

    ownUv, atlas = [], []
    keeping = [material for material in usable if keepsSecondUv(material)]
    for material in usable:
        if not keepsSecondUv(material):
            atlas.append(material)
            continue
        progress('Checking existing UVs %d/%d: %s' % (keeping.index(material) + 1, len(keeping), material.name))
        triangles = np.concatenate([secondUvTriangles(obj, faceMask(obj, {material})) for obj in users[material]])
        overlap = overlapShare(triangles, OWN_UV_CHECK_SIZE)
        if overlap > OWN_UV_OVERLAP_LIMIT:
            lines.append('Skipped %s: its second UV map shapes its look and overlaps itself (%.0f%%)' % (material.name, 100 * overlap))
        else:
            ownUv.append(material)
    if not atlas and not ownUv:
        raise LightmapBakeError('Nothing to bake. ' + '; '.join(lines))

    if context.object is not None and context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    visibleBefore = {obj: obj.visible_get() for obj in meshes}
    hiddenBefore = {obj: (obj.hide_get(), obj.hide_viewport) for obj in context.view_layer.objects}
    renderHiddenBefore = {obj: obj.hide_render for obj in scene.objects}
    selectedBefore = set(context.selected_objects)
    activeBefore = context.view_layer.objects.active
    engineBefore = scene.render.engine
    deviceBefore = scene.cycles.device
    samplesBefore = scene.cycles.samples
    worldBefore = scene.world
    distanceBefore = worldBefore.light_settings.distance if worldBefore is not None else None
    temporaryImages, temporaryWorld, bakeObjects, createdMeshes = [], None, [], []

    try:
        worldAreas = {material: sum(surfaceAreas(obj, faceMask(obj, {material}))[0] for obj in users[material]) for material in atlas + ownUv}
        sizes = scaledTextureSizes(worldAreas, largestSize, settings.scale_to_area)
        groups = textureGroups(atlas, sizes, largestSize, settings.pack_together) + [[[material], sizes[material]] for material in ownUv]
        progress('Baking %d material%s into %d texture%s' % (len(atlas) + len(ownUv), '' if len(atlas) + len(ownUv) == 1 else 's', len(groups), '' if len(groups) == 1 else 's'))
        atlasObjects = [obj for obj in meshes if faceMask(obj, set(atlas)).any()]
        verticesAdded = 0
        if atlasObjects:
            for obj in atlasObjects:
                obj.hide_viewport = False
                obj.hide_set(False)
            blocked = [obj.name for obj in atlasObjects if not obj.visible_get()]
            if blocked:
                raise LightmapBakeError('%s is in a hidden collection; show its collection and bake again' % blocked[0])
            originalUvs = {}
            for obj in atlasObjects:
                originalUvs[obj] = np.empty(len(obj.data.loops) * 2, np.float32)
                obj.data.uv_layers[1].data.foreach_get('uv', originalUvs[obj])
            packing = [group for group in groups if group[0][0] in atlas]
            for group in groups:
                members, size = group
                if members[0] not in atlas:
                    continue
                progress('Packing UVs %d/%d: %s at %d px' % (packing.index(group) + 1, len(packing), groupLabel(members), size))
                masks = {obj: faceMask(obj, set(members)) for obj in atlasObjects}
                masks = {obj: mask for obj, mask in masks.items() if mask.any()}
                while True:
                    unwrapAtlas(context, masks, size, settings.island_margin)
                    uvArea = sum(surfaceAreas(obj, mask)[1] for obj, mask in masks.items())
                    if uvArea >= MINIMUM_ATLAS_FILL or size >= largestSize:
                        break
                    progress("Islands don't fit at %d px, trying %d px" % (size, size * 2), detail=True)
                    size *= 2
                group[1] = size
                if uvArea < MINIMUM_ATLAS_FILL:
                    for obj, uvs in originalUvs.items():
                        obj.data.uv_layers[1].data.foreach_set('uv', uvs)
                    raise LightmapBakeError('The UV islands of %s%s only use %.1f%% of a %d px texture, so a %d px margin around each one '
                                            "doesn't fit. Raise Max Resolution, lower Island Margin or turn off Scale To Surface Area" % (
                                                members[0].name, ' and %d more' % (len(members) - 1) if len(members) > 1 else '',
                                                100 * uvArea, size, settings.island_margin))
            step = max(1, len(atlasObjects) // 10)
            for index, obj in enumerate(atlasObjects):
                if index % step == 0:
                    progress('Splitting UV seams %d/%d meshes' % (index + 1, len(atlasObjects)), detail=index > 0)
                verticesAdded += splitSecondUvSeams(obj.data)

        scene.render.engine = 'CYCLES'
        device = useConfiguredDevice(scene)
        scene.cycles.samples = settings.samples
        if scene.world is None:
            temporaryWorld = bpy.data.worlds.new('NA Lightmap Bake World')
            scene.world = temporaryWorld
        scene.world.light_settings.distance = settings.ao_distance

        images = {}
        for index, (members, size) in enumerate(groups):
            image = newBakeImage('NA Lightmap %d' % index, size)
            temporaryImages.append(image)
            for material in members:
                images[material] = image
        dummy = newBakeImage('NA Lightmap Unused', 8)
        temporaryImages.append(dummy)

        targets = [obj for obj in meshes if faceMask(obj, set(images)).any()]
        for material in {slot.material for obj in targets for slot in obj.material_slots if slot.material is not None}:
            if material.node_tree is None:
                material.use_nodes = True
            node = material.node_tree.nodes.new('ShaderNodeTexImage')
            node.name = BAKE_NODE_NAME
            node.image = images.get(material, dummy)
            material.node_tree.nodes.active = node

        passes = {}
        for obj in targets:
            passes.setdefault((obj.mesh_group_props.lod_level, visibleBefore[obj]), []).append(obj)
        for passNumber, ((lodLevel, visible), passTargets) in enumerate(sorted(passes.items(), key=lambda item: (item[0][0], not item[0][1])), 1):
            occluders = [obj for obj in meshes if obj not in passTargets and obj.mesh_group_props.lod_level == lodLevel
                         and visibleBefore[obj] == visible and any(blocksLight(slot.material) for slot in obj.material_slots)]
            progress('Baking %d/%d: LOD %d %s meshes (%d meshes, %d occluders, %d samples on %s)' % (
                passNumber, len(passes), lodLevel, 'visible' if visible else 'hidden', len(passTargets), len(occluders), settings.samples, device))
            passStart = time.perf_counter()
            bakeObject = joinedCopies(context, passTargets, 'NA Lightmap Bake Targets', createdMeshes)
            bakeObjects.append(bakeObject)
            blocker = joinedCopies(context, occluders, 'NA Lightmap Bake Blockers', createdMeshes) if occluders else None
            if blocker is not None:
                bakeObjects.append(blocker)
            for obj in scene.objects:
                obj.hide_render = obj not in (bakeObject, blocker)
            for obj in context.view_layer.objects:
                obj.select_set(obj is bakeObject)
            context.view_layer.objects.active = bakeObject
            bpy.ops.object.bake(type='AO', uv_layer=BAKE_UV_NAME, margin=0, use_clear=False,
                                use_selected_to_active=False, target='IMAGE_TEXTURES')
            progress('Baked in %.1fs' % (time.perf_counter() - passStart), detail=True)
            for obj in (bakeObject, blocker):
                if obj is not None:
                    bakeObjects.remove(obj)
                    removeObject(obj)
            lines.append('Baked LOD %d %s meshes: %d meshes, %d occluders in %.1fs (%s)' % (
                lodLevel, 'visible' if visible else 'hidden', len(passTargets), len(occluders), time.perf_counter() - passStart, device))

        written = {}
        bakedImages = sorted({image for image in images.values()}, key=lambda image: -image.size[0])
        for number, image in enumerate(bakedImages, 1):
            values, filled = bakedValues(image)
            identifier = newTextureIdentifier(scene)
            path = os.path.join(directory, identifier + '.dds')
            progress('Writing %d/%d: %s (%d px)' % (number, len(bakedImages), os.path.basename(path), image.size[0]))
            writeGreyBc1Dds(path, dilate(values, filled, DILATE_STEPS))
            loaded = bpy.data.images.load(path, check_existing=False)
            loaded.colorspace_settings.name = 'Non-Color'
            written[image] = (identifier, path, loaded)
        for material, image in images.items():
            identifier, path, loaded = written[image]
            assignLightmap(scene, material, identifier, path, loaded)
        for image, (identifier, path, _) in sorted(written.items(), key=lambda item: -item[0].size[0]):
            members = [material for material, baked in images.items() if baked is image]
            areas = [surfaceAreas(obj, faceMask(obj, set(members))) for obj in meshes if faceMask(obj, set(members)).any()]
            worldArea, uvArea = sum(a[0] for a in areas), sum(a[1] for a in areas)
            density = image.size[0] * math.sqrt(uvArea / worldArea) if worldArea > 0 else 0.0
            lines.append('Wrote %s (%d px, %.0f%% used, %.1f texels per metre) for %s' % (
                os.path.basename(path), image.size[0], 100 * uvArea, density, ', '.join(material.name for material in members)))
        if verticesAdded:
            lines.append('Split %d vertices along the new UV seams' % verticesAdded)
    finally:
        for obj in list(bakeObjects):
            removeObject(obj)
        for mesh in createdMeshes:
            try:
                if mesh.users == 0:
                    bpy.data.meshes.remove(mesh)
            except ReferenceError:
                pass
        for material in bpy.data.materials:
            if material.node_tree is not None and BAKE_NODE_NAME in material.node_tree.nodes:
                material.node_tree.nodes.remove(material.node_tree.nodes[BAKE_NODE_NAME])
        for image in temporaryImages:
            bpy.data.images.remove(image)
        scene.render.engine = engineBefore
        scene.cycles.device = deviceBefore
        scene.cycles.samples = samplesBefore
        if temporaryWorld is not None:
            scene.world = worldBefore
            bpy.data.worlds.remove(temporaryWorld)
        elif worldBefore is not None:
            worldBefore.light_settings.distance = distanceBefore
        for obj, hidden in renderHiddenBefore.items():
            obj.hide_render = hidden
        for obj, (hidden, viewportHidden) in hiddenBefore.items():
            obj.hide_viewport = viewportHidden
            obj.hide_set(hidden)
        for obj in context.view_layer.objects:
            obj.select_set(obj in selectedBefore)
        context.view_layer.objects.active = activeBefore
    lines.append('Done in %.1fs' % (time.perf_counter() - started))
    return lines


class LightmapBakerSettings(bpy.types.PropertyGroup):
    max_resolution: bpy.props.EnumProperty(
        name="Max Resolution",
        description="Width and height of the largest lightmap texture",
        items=[('512', "512", ""), ('1024', "1024", ""), ('2048', "2048", ""), ('4096', "4096", "")],
        default='2048',
    )
    pack_together: bpy.props.BoolProperty(
        name="Pack Material Lightmaps Together",
        description="Combine materials whose lightmaps are smaller than Max Resolution into shared textures, e.g. four 2048 px lightmaps into one 4096 px texture. "
                    "Off: every material gets its own texture",
        default=True,
    )
    scale_to_area: bpy.props.BoolProperty(
        name="Scale To Surface Area",
        description="Give the material with the most surface a Max Resolution lightmap and shrink the others by how much less surface they cover. "
                    "Off: every lightmap uses Max Resolution",
        default=True,
    )
    ao_distance: bpy.props.FloatProperty(
        name="AO Distance",
        description="How far the occlusion spreads: geometry further away than this doesn't darken a surface",
        default=2.0, min=0.01, soft_max=20.0, subtype='DISTANCE', unit='LENGTH',
    )
    samples: bpy.props.IntProperty(
        name="Samples",
        description="Rays per texel; fewer is faster but noisier",
        default=512, min=1, soft_max=4096,
    )
    island_margin: bpy.props.IntProperty(
        name="Island Margin",
        description="Gap between UV islands in pixels, so neighbouring islands don't bleed into each other",
        default=2, min=0, max=32, subtype='PIXEL',
    )
    output_directory: bpy.props.StringProperty(subtype='DIR_PATH')


class LightmapBakeSetAll(bpy.types.Operator):
    bl_idname = "na.lightmap_bake_set_all"
    bl_label = "Tick All"
    bl_description = "Tick or untick every material in the lightmap baker"
    bl_options = {'UNDO'}

    state: bpy.props.BoolProperty()

    def execute(self, context):
        for material in listedMaterials():
            material.lightmap_bake = self.state
        return {'FINISHED'}


class LightmapBake(bpy.types.Operator):
    bl_idname = "na.lightmap_bake"
    bl_label = "Bake Lightmap"
    bl_description = "Unwrap a lightmap UV for the ticked materials, bake ambient occlusion into it and save it as DDS in the chosen folder"
    bl_options = {'REGISTER', 'UNDO'}

    directory: bpy.props.StringProperty(subtype='DIR_PATH')
    filter_folder: bpy.props.BoolProperty(default=True, options={'HIDDEN'})

    def invoke(self, context, event):
        self.directory = context.scene.lightmap_baker.output_directory
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        directory = bpy.path.abspath(self.directory)
        if not directory or not os.path.isdir(directory):
            self.report({'ERROR'}, "Choose an existing folder for the lightmap textures")
            return {'CANCELLED'}
        context.scene.lightmap_baker.output_directory = self.directory
        try:
            lines = bakeLightmaps(context, directory)
        except LightmapBakeError as error:
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}
        for line in lines:
            print('[!]' if line.startswith('Skipped') else '[i]', line)
        self.report({'INFO'}, ' | '.join(lines))
        return {'FINISHED'}


class NA_PT_LightmapBaker(bpy.types.Panel):
    bl_label = "Lightmap Baker"
    bl_idname = "NA_PT_lightmap_baker"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "NA: Lightmap Baker"

    def draw(self, context):
        layout = self.layout
        materials = listedMaterials()
        if not materials:
            layout.label(text="No WMB materials can take a lightmap")
            return
        settings = context.scene.lightmap_baker
        column = layout.column(align=True)
        column.prop(settings, 'max_resolution')
        column.prop(settings, 'scale_to_area')
        column.prop(settings, 'pack_together')
        column.prop(settings, 'ao_distance')
        column.prop(settings, 'samples')
        column.prop(settings, 'island_margin')

        row = layout.row(align=True)
        row.label(text="Materials")
        tickAll = row.operator(LightmapBakeSetAll.bl_idname, text="", icon='CHECKBOX_HLT')
        tickAll.state = True
        tickNone = row.operator(LightmapBakeSetAll.bl_idname, text="", icon='CHECKBOX_DEHLT')
        tickNone.state = False
        box = layout.box()
        for material in materials:
            row = box.row()
            row.prop(material, 'lightmap_bake', text=material.name)
            if keepsSecondUv(material):
                row.label(text="own UV")
        layout.operator(LightmapBake.bl_idname, icon='RENDER_STILL')


classes = (
    LightmapBakerSettings,
    LightmapBakeSetAll,
    LightmapBake,
    NA_PT_LightmapBaker,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.lightmap_baker = bpy.props.PointerProperty(type=LightmapBakerSettings)
    bpy.types.Material.lightmap_bake = bpy.props.BoolProperty(
        name="Bake Lightmap",
        description="Include this material's faces in the next lightmap bake",
        default=True,
    )


def unregister():
    del bpy.types.Material.lightmap_bake
    del bpy.types.Scene.lightmap_baker
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
