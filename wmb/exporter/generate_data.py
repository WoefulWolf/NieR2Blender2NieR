# save data from Blender to Python object (still dependent on too many custom properties)
# these imports look redundant but idk todo check
from ...utils.util import allObjectsInCollectionInOrder
from ...utils.util import Vector3
from ...utils.util import *
from ...utils.util import getUsedMaterials
from ...utils.util import ShowMessageBox
import bpy, math
from mathutils import Vector
from time import time

def getRealName(name):
    splitname = name.split('-')
    splitname.pop(0)
    splitname.pop()
    return '-'.join(splitname)

class c_batch(object):
    def __init__(self, obj, vertexGroupIndex, indexStart, prev_numVertexes, boneSetIndex, vertexStart=0):
        self.vertexGroupIndex = vertexGroupIndex
        self.boneSetIndex = boneSetIndex
        self.vertexStart = vertexStart
        self.indexStart = indexStart
        self.numVertexes = len(obj.data.vertices) + prev_numVertexes
        self.numIndexes = len(obj.data.loops)
        self.numPrimitives = len(obj.data.polygons)
        self.blenderObj = obj

class c_batch_supplements(object): # wmb4
    def __init__(self, startPointer):
        allBatches = [x for x in allObjectsInCollectionInOrder('WMB') if x.type == "MESH"]
        allBatches = sorted(allBatches, key=lambda batch: batch['ID'])
        self.batchData = [[], [], [], []] # stupid pass by reference
        for batch in allBatches:
            batchDatum = [0] * 4
            batchDatum[0] = batch['ID']
            batchDatum[1] = batch['meshGroupIndex']
            batchDatum[2] = batch['Materials'][0]
            batchDatum[3] = batch['boneSetIndex'] # erroneously counting up, they should be 0 # fine on sam
            if not batch['batchGroup'] or batch['batchGroup'] < 0:
                batch['batchGroup'] = 0
            self.batchData[batch['batchGroup']].append(batchDatum)
        
        self.batchOffsets = [-1] * 4
        curOffset = startPointer + 32
        if curOffset % 16 > 0:
            curOffset += 16 - (curOffset % 16)
        for index, batchGroup in enumerate(self.batchData):
            if len(batchGroup) == 0:
                continue # break might work here
            #print(batchGroup)
            self.batchOffsets[index] = curOffset
            curOffset += 16 * len(batchGroup)
        
        self.supplementStructSize = curOffset - startPointer

class c_batches(object):
    def __init__(self, vertexGroupsCount, wmb4=False):
    
        self.vertexGroupsCount = vertexGroupsCount
        
        def get_batches(self):
            batches = []
            currentVertexGroup = -1
            
            allBatches = [x for x in allObjectsInCollectionInOrder('WMB') if x.type == "MESH"]
            indexNums = [0] * self.vertexGroupsCount
            vertexNums = [0] * self.vertexGroupsCount
            cur_indexStart = 0
            cur_numVertexes = 0
            
            for obj in sorted(allBatches, key=lambda batch: batch['ID']):
                obj_name = obj.name.split('-')
                obj_vertexGroupIndex = int(obj_name[0 if wmb4 else -1])
                print('[+] Generating Batch', obj.name)
                if obj_vertexGroupIndex != currentVertexGroup:      # Start of new vertex group
                    indexNums[currentVertexGroup] = cur_indexStart
                    vertexNums[currentVertexGroup] = cur_numVertexes
                    currentVertexGroup = obj_vertexGroupIndex
                    cur_indexStart = indexNums[currentVertexGroup]
                    cur_numVertexes = vertexNums[currentVertexGroup]

                if 'boneSetIndex' in obj:
                    obj_boneSetIndex = obj['boneSetIndex']
                else:
                    obj_boneSetIndex = -1
                
                if wmb4:
                    batches.append(c_batch(obj, obj_vertexGroupIndex, cur_indexStart, 0, obj_boneSetIndex, cur_numVertexes))
                else:
                    batches.append(c_batch(obj, obj_vertexGroupIndex, cur_indexStart, cur_numVertexes, obj_boneSetIndex))
                cur_indexStart += batches[-1].numIndexes
                cur_numVertexes = batches[-1].vertexStart + batches[-1].numVertexes
            #print([batch.vertexStart for batch in batches])
            return batches

        self.batches = get_batches(self)
        self.batches_StructSize = len(self.batches) * (20 if wmb4 else 28)

class c_boneIndexTranslateTable(object):
    def __init__(self, bones):

        self.firstLevel = []
        self.secondLevel = []
        self.thirdLevel = []

        for obj in bpy.data.collections['WMB'].all_objects:
            if obj.type == 'ARMATURE':
                for idx in range(len(obj.data['firstLevel'])):
                    self.firstLevel.append(obj.data['firstLevel'][idx])

                for idx in range(len(obj.data['secondLevel'])):
                    self.secondLevel.append(obj.data['secondLevel'][idx])

                for idx in range(len(obj.data['thirdLevel'])):
                    self.thirdLevel.append(obj.data['thirdLevel'][idx])

        self.firstLevel_Size = len(self.firstLevel)

        self.secondLevel_Size = len(self.secondLevel)   

        self.thirdLevel_Size = len(self.thirdLevel)


        self.boneIndexTranslateTable_StructSize = self.firstLevel_Size*2 + self.secondLevel_Size*2 + self.thirdLevel_Size*2

class c_boneMap(object):
    def __init__(self, bones):
        boneMap = []
        for obj in bpy.data.collections['WMB'].all_objects:
            if obj.type == 'ARMATURE':
                boneMap = obj.data['boneMap']
        
        self.boneMap = boneMap

        self.boneMap_StructSize = len(boneMap) * 4

class c_boneSet(object):
    def __init__(self, boneMap, boneSets_Offset, wmb4=False):

        def get_blender_boneSets(self):
            b_boneSets = []
            for obj in bpy.data.collections['WMB'].all_objects:
                if obj.type == 'ARMATURE':
                    for boneSet in obj.data['boneSetArray']:
                        b_boneSets.append(boneSet)
            
            return b_boneSets

        def get_boneSets(self, b_boneSets, boneSets_Offset):
            boneSets = []

            b_offset = boneSets_Offset + len(b_boneSets) * 8
            

            for b_boneSet in b_boneSets:
                if wmb4 and (b_offset % 16 > 0):
                    b_offset += 16 - (b_offset % 16)
                
                numBoneIndexes = len(b_boneSet)

                boneSets.append([b_offset, numBoneIndexes, b_boneSet])
                b_offset += len(b_boneSet) * (1 if wmb4 else 2)

            return boneSets, b_offset - boneSets_Offset
        
        blender_boneSets = get_blender_boneSets(self)

        self.boneSet, self.boneSet_StructSize = get_boneSets(self, blender_boneSets, boneSets_Offset)

        def get_boneSet_StructSize(self):
            boneSet_StructSize = len(self.boneSet) * 8
            for boneSet in self.boneSet:
                boneSet_StructSize += len(boneSet[2]) * (1 if wmb4 else 2)
                
            return boneSet_StructSize


        #self.boneSet_StructSize = get_boneSet_StructSize(self)

class c_b_boneSets(object):
    def __init__(self, wmb4=False):
        # Find Armature
        for obj in bpy.data.collections['WMB'].all_objects:
            if obj.type == 'ARMATURE':
                amt = obj
                break

        # Get boneMap
        if not wmb4:
            boneMap = []
            for val in amt.data['boneMap']:
                boneMap.append(val)
        
        #fuck it
        if wmb4:
            return
        
        
        # Get boneSets
        b_boneSets = []
        for obj in bpy.data.collections['WMB'].all_objects:
            if obj.type == 'MESH':
                vertex_group_bones = []
                if obj['boneSetIndex'] != -1:
                    for group in obj.vertex_groups:
                        boneID = int(group.name.replace("bone", ""))
                        boneMapIndex = boneMap.index(boneID) if not wmb4 else boneID
                        vertex_group_bones.append(boneMapIndex)
                    print(vertex_group_bones)
                    if vertex_group_bones not in b_boneSets:
                        if wmb4:
                            if len(b_boneSets) <= obj["boneSetIndex"]:
                                b_boneSets.append(vertex_group_bones)
                            else:
                                b_boneSets[obj["boneSetIndex"]].extend(vertex_group_bones)
                        else:
                            b_boneSets.append(vertex_group_bones)
                            obj["boneSetIndex"] = len(b_boneSets)-1
                    elif not wmb4:
                        obj["boneSetIndex"] = b_boneSets.index(vertex_group_bones)
        
        if wmb4:
            b_boneSets = [sorted(list(set(boneSet))) for boneSet in b_boneSets] # removing duplicates trick
        
        amt.data['boneSetArray'] = b_boneSets

class c_bones(object):
    def __init__(self, wmb4=False):

        def get_bones(self):
            _bones = []
            numBones = 0
            armatures = [x for x in bpy.data.collections['WMB'].all_objects if x.type == 'ARMATURE']
            for obj in armatures:
                numBones = len(obj.data.bones)
                first_bone = obj.data.bones[0]

            if numBones > 1:
                for obj in armatures:
                    for bone in obj.data.bones:
                        ID = bone['ID']

                        if bone.parent:
                            parent_name = bone.parent.name
                            parentIndex = int(parent_name.replace('bone', '').replace('fakeBone', ''))
                        else:
                            parentIndex = -1

                        localPosition = Vector3(bone['localPosition'][0], bone['localPosition'][1], bone['localPosition'][2])

                        localRotation = Vector3(bone['localRotation'][0], bone['localRotation'][1], bone['localRotation'][2])
                        localScale = Vector3(1, 1, 1) # Same here but 1, 1, 1. Makes sense. Bones don't "really" have scale.
                        
                        #if wmb4:
                        #    position = Vector3(bone.tail_local[0], bone.tail_local[1], bone.tail_local[2])
                        position = Vector3(bone.head_local[0], bone.head_local[1], bone.head_local[2])
                        rotation = Vector3(bone['worldRotation'][0], bone['worldRotation'][1], bone['worldRotation'][2])
                        scale = localScale

                        tPosition = Vector3(bone['TPOSE_worldPosition'][0], bone['TPOSE_worldPosition'][1], bone['TPOSE_worldPosition'][2])

                        blenderName = bone.name

                        bone = [ID, parentIndex, localPosition.xyz, localRotation.xyz, localScale.xyz, position.xyz, rotation.xyz, scale.xyz, tPosition.xyz, blenderName]
                        _bones.append(bone)
                
            elif numBones == 1:
                for obj in armatures:
                    for bone in obj.data.bones:
                        ID = bone['ID']
                        parentIndex = -1
                        localPosition = Vector3(bone['localPosition'][0], bone['localPosition'][1], bone['localPosition'][2])
                        localRotation = Vector3(0, 0, 0) # I haven't seen anything here besides 0, 0, 0.
                        localScale = Vector3(1, 1, 1) # Same here but 1, 1, 1. Makes sense. Bones don't "really" have scale.

                        position = localPosition
                        rotation = localRotation
                        scale = localScale

                        tPosition = localPosition

                        blenderName = bone.name
                        bone = [ID, parentIndex, localPosition.xyz, localRotation.xyz, localScale.xyz, position.xyz, rotation.xyz, scale.xyz, tPosition.xyz, blenderName]
                        _bones.append(bone)

            return _bones
                        
        self.bones = get_bones(self)
        self.bones_StructSize = len(self.bones) * (32 if wmb4 else 88)

def getColMeshIndex(objToFind):
    colMeshObjs = [obj for obj in bpy.data.collections['WMB'].all_objects if obj.type == 'MESH']
    for i, obj in enumerate(colMeshObjs):
        if obj == objToFind:
            return i
    return -1

# Basic generation algorithm:
# 1. Find unassigned mesh with the largest volume and create a volume for it.
# 2. Look for any other meshes that are also in aforementioned volume and assign to it.
# 3. If no more meshes can be assigned to the volume, return to step 1 until all meshes are assigned to a volume.

def generate_colTreeNodes():
    print("[+] Generating custom colTreeNodes")
    # Create and setup collection
    colCollection = bpy.data.collections.get("WMB")
    custom_colTreeNodesCollection = bpy.data.collections.get("custom_wmb_colTreeNodes")
    if not custom_colTreeNodesCollection:
        custom_colTreeNodesCollection = bpy.data.collections.new("custom_wmb_colTreeNodes")
        colCollection.children.link(custom_colTreeNodesCollection)
    for obj in [o for o in custom_colTreeNodesCollection.objects]:
        bpy.data.objects.remove(obj)

    # Create Root Node
    rootNode = bpy.data.objects.new("custom_Root_wmb", None)
    rootNode.hide_viewport = True
    custom_colTreeNodesCollection.objects.link(rootNode)
    rootNode.rotation_euler = (math.radians(90),0,0)

    unassigned_objs = [obj for obj in bpy.data.collections['WMB'].all_objects if obj.type == 'MESH']

    nodes = []
    while len(unassigned_objs) > 0:
        largest_obj = max(unassigned_objs, key=lambda x: getObjectVolume(x))
        unassigned_objs.remove(largest_obj)

        sub_objects = []
        for obj in unassigned_objs:
            #if len(sub_objects) >= 15:    # Do not put more than 15 + 1 meshes in a volume
            #    break

            if volumeInsideOther(getObjectCenter(obj), obj.dimensions, getObjectCenter(largest_obj), largest_obj.dimensions):
                sub_objects.append(obj)

        for obj in sub_objects:
            unassigned_objs.remove(obj)

        # Create Empty
        colEmptyName = str(len(nodes)) + "_wmb"
        colEmpty = bpy.data.objects.new(colEmptyName, None)
        custom_colTreeNodesCollection.objects.link(colEmpty)
        colEmpty.parent = rootNode
        colEmpty.empty_display_type = 'CUBE'

        colEmpty.location = getObjectCenter(largest_obj)
        colEmpty.scale = np.divide(largest_obj.dimensions, 2)

        meshIndices = [getColMeshIndex(largest_obj)]
        for obj in sub_objects:
            meshIndices.append(getColMeshIndex(obj))

        colEmpty["meshIndices"] = meshIndices

        # Create Custom ColTreeNode
        node = custom_ColTreeNode()
        node.index = len(nodes)
        node.bObj = colEmpty
        node.position = colEmpty.location
        node.scale = colEmpty.scale
        node.meshIndices = meshIndices
        node.meshIndexCount = len(node.meshIndices)

        colEmpty.name = str(node.index) + "_" + str(node.left) + "_" + str(node.right) + "_wmb"

        nodes.append(node)

    print("   [>] Number of leaf nodes generated...", len(nodes))

    # Start connecting leaf nodes up into tree
    deepest_nodes = nodes
    while len(deepest_nodes) > 1:
        deepest_nodes_sorted = sorted(deepest_nodes, key=lambda x: x.getVolume())
        joined_nodes = []
        new_nodes = []
        for i in range(len(deepest_nodes_sorted)-1):
            if deepest_nodes_sorted[i] in joined_nodes:
                continue
            closest_dist = getDistanceTo(deepest_nodes_sorted[i].position, deepest_nodes_sorted[i+1].position)
            closest_node = deepest_nodes_sorted[i+1]
            for j in range(len(deepest_nodes_sorted)):
                if deepest_nodes_sorted[i] == deepest_nodes_sorted[j] or deepest_nodes_sorted[j] in joined_nodes:
                    continue
                dist = getDistanceTo(deepest_nodes_sorted[i].position, deepest_nodes_sorted[j].position)
                if dist < closest_dist:
                    closest_dist = dist
                    closest_node = deepest_nodes_sorted[j]
            
            # deepest_Nodes[i] and closest_node should be joined
            colEmptyName = str(len(nodes)) + "_wmb"
            colEmpty = bpy.data.objects.new(colEmptyName, None)
            custom_colTreeNodesCollection.objects.link(colEmpty)
            colEmpty.parent = rootNode
            colEmpty.empty_display_type = 'CUBE'
            loc, scale = getVolumeSurrounding(deepest_nodes_sorted[i].position, deepest_nodes_sorted[i].scale*2, closest_node.position, closest_node.scale*2)

            colEmpty.location = loc
            colEmpty.scale = scale

            node = custom_ColTreeNode()
            node.index = len(nodes)
            node.bObj = colEmpty
            node.position = colEmpty.location
            node.scale = colEmpty.scale
            node.left = deepest_nodes_sorted[i].index
            node.right = closest_node.index

            colEmpty.name = str(node.index) + "_" + str(node.left) + "_" + str(node.right) + "_wmb"

            joined_nodes.append(deepest_nodes_sorted[i])
            joined_nodes.append(closest_node)
            nodes.append(node)
            new_nodes.append(node)


        unassigned_nodes= []
        for node in deepest_nodes_sorted:
            if node not in joined_nodes:
                unassigned_nodes.append(node)

        deepest_nodes = new_nodes + unassigned_nodes
        print("   [>] Number of new nodes generated for upper level...", len(deepest_nodes))

    # Let's fix the ordering of the tree in Blender
    indexOffset = len(nodes) - 1
    for node in nodes:
        node.index = indexOffset - node.index
        if (node.left != -1):
            node.left = indexOffset - node.left
        if (node.left != -1):
            node.right = indexOffset - node.right
        node.bObj.name = str(node.index) + "_" + str(node.left) + "_" + str(node.right) + "_wmb"

    # Clean up Blender's duplicate nam
    for node in nodes:
        splitName = node.bObj.name.split(".")
        node.bObj.name = splitName[0]


    nodes = sorted(nodes, key=lambda x: x.index) 
    return nodes

def updateMeshColTreeNodeIndices(colTreeNodes):
    batchObjs = [obj for obj in bpy.data.collections['WMB'].all_objects if obj.type == 'MESH']

    for node in colTreeNodes:
        for meshIndex in node.meshIndices:
            batchObjs[meshIndex]["colTreeNodeIndex"] = node.index

class c_colTreeNodes(object):
    def __init__(self):
        def get_colTreeNodes():
            customColTreeNodes = generate_colTreeNodes()
            updateMeshColTreeNodeIndices(customColTreeNodes)

            colTreeNodes = []
            #b_colTreeNodes = bpy.context.scene['colTreeNodes']
            for node in customColTreeNodes:
                colTreeNodes.append([node.position, node.scale, node.left, node.right])
            """
            for key in b_colTreeNodes.keys():
                val = b_colTreeNodes[key]
                p1 = [val[0], val[1], val[2]]
                p2 = [val[3], val[4], val[5]]
                left = int(val[6])
                right = int(val[7])
                colTreeNodes.append([p1, p2, left, right])
            """
            return colTreeNodes

        def get_colTreeNodesSize(colTreeNodes):
            colTreeNodesSize = len(colTreeNodes) * 32
            return colTreeNodesSize

        self.colTreeNodes = get_colTreeNodes()
        self.colTreeNodesSize = get_colTreeNodesSize(self.colTreeNodes)
        self.colTreeNodesCount = len(self.colTreeNodes)

class c_lod(object):
    def __init__(self, lodsStart, batches, lod_level):
        def get_lodBatches(self, batches, lod_level):
            lodBatches = []
            for batch in batches.batches:
                if batch.blenderObj['LOD_Level'] == lod_level:
                    lodBatches.append(batch)
            return lodBatches

        def get_batchInfos(self, batches):
            batchesInfos = []
            for batch in batches:                                     
                vertexGroupIndex = batch.vertexGroupIndex
                meshIndex = batch.blenderObj['meshGroupIndex']

                for slot in batch.blenderObj.material_slots:
                    material = slot.material
                for mat_index, mat in enumerate(getUsedMaterials()):
                    if mat == material:
                        materialIndex = mat_index
                        break
                
                colTreeNodeIndex = batch.blenderObj['colTreeNodeIndex']
                meshMatPairIndex = meshIndex
                unknownWorldDataIndex = batch.blenderObj['unknownWorldDataIndex']
                batchInfo = [vertexGroupIndex, meshIndex, materialIndex, colTreeNodeIndex, meshMatPairIndex, unknownWorldDataIndex]
                batchesInfos.append(batchInfo)
            return batchesInfos

        self.lodBatches = get_lodBatches(self, batches, lod_level)
        self.numBatchInfos = len(self.lodBatches)
        self.offsetName = lodsStart + self.numBatchInfos * 24
        self.lodLevel = lod_level
        self.batchStart = batches.batches.index(self.lodBatches[0])
        self.name = self.lodBatches[0].blenderObj['LOD_Name']
        self.offsetBatchInfos = self.offsetName - 24 * self.numBatchInfos
        self.batchInfos = get_batchInfos(self, self.lodBatches)
        self.lod_StructSize = len(self.name) + 1 + len(self.batchInfos) * 24

class c_lods(object):
    def __init__(self, lodsStart, batches):
        def get_lod_levels(batches):
            lod_levels = []
            for batch in batches.batches:
                level = batch.blenderObj['LOD_Level']
                if level not in lod_levels:
                    lod_levels.append(level)
            return lod_levels

        def get_lods(lodsStart, batches):
            lod_levels = get_lod_levels(batches)
            lods = []
            currentLodStart = lodsStart + len(lod_levels) * 20
            for lod_level in lod_levels:
                print('[+] Generating LOD', str(lod_level))
                lods.append(c_lod(currentLodStart, batches, lod_level))
                currentLodStart += lods[-1].lod_StructSize
            return lods

        def get_lodsStructSize(lods):
            lodsStructSize = len(lods) * 20
            for lod in lods:
                lodsStructSize += lod.lod_StructSize
            return lodsStructSize

        self.lods = get_lods(lodsStart, batches)
        self.lods_StructSize = get_lodsStructSize(self.lods)

class c_material(object):
    def __init__(self, offsetMaterialName, material, wmb4=False):
        self.offsetMaterial = offsetMaterialName
        self.b_material = material

        def get_textures(self, material, offsetTextures):
            offset = offsetTextures
            numTextures = 0
            textures = []
            
            for key, value in material.items():
                #print(key, value)
                if (isinstance(value, str)):
                    if (key.find('g_') != -1) or(wmb4 and (key.find('tex') != -1 or key.find('Map') != -1)):
                        #print(key, value)
                        numTextures += 1

            offsetName = offset + numTextures * 8


            for key, value in material.items():
                if (isinstance(value, str)) and ((key.find('g_') != -1) or(wmb4 and (key.find('tex') != -1 or key.find('Map') != -1))):
                    texture = value
                    name = key
                    
                    offset += 4 + 4 + len(key) # but it isn't used after this?
                    textures.append([offsetName, texture, name])
                    if not wmb4:
                        offsetName += len(name) + 1
            
            if wmb4: # proper sorting
                sortedTextures = []
                for tex in textures:
                    name = tex[2]
                    if name.find('tex') != -1:
                        num = name[3:]
                    else:
                        mapIndx = name.find('Map')
                        num = name[(mapIndx + 3):]
                    sortedTextures.append([tex, num])
                
                # I'm using "tex" really loosely here, since it's become:
                # [[offsetName, texture, name], num]
                sortedTextures = sorted(sortedTextures, key=lambda tex: tex[1])
                return [tex[0] for tex in sortedTextures]
            
            return textures

        def get_textures_StructSize(self, textures):
            textures_StructSize = 0
            for texture in textures:
                #print(texture[1])
                textures_StructSize += 8 if not wmb4 else 4
                if not wmb4:
                    textures_StructSize += len(texture[2]) + 1
            #print(textures_StructSize)
            return textures_StructSize

        def get_numParameterGroups(self, material):
            numParameterGroups = 0
            parameterGroups = []

            def Check(char):
                try: 
                    int(char)
                    return True
                except ValueError:
                    return False

            for key, value in material.items():
                if Check(key[0]):
                    if not key[0] in parameterGroups:
                        numParameterGroups += 1
                        parameterGroups.append(key[0])

            return numParameterGroups

        def get_parameterGroups(self, material, offsetParameterGroups, numParameterGroups):
            parameterGroups = []
            offsetParameters = offsetParameterGroups + numParameterGroups * 12

            for i in range(numParameterGroups):
                index = i

                if index == 1:
                    index = -1

                parameters = []
                if not wmb4:
                    for key, value in material.items():
                        if key[0] == str(i):
                            parameters.append(value)
                else:
                    for j in range(4):
                        parameters.append(material[str(i)][j])
                        
                numParameters = len(parameters)

                parameterGroups.append([index, offsetParameters, numParameters, parameters])

                offsetParameters += numParameters * 4

            return parameterGroups

        def get_parameterGroups_StructSize(self, parameterGroups):
            parameterGroups_StructSize = 0
            for parameterGroup in parameterGroups:
                if not wmb4:
                    parameterGroups_StructSize += 12 + parameterGroup[2] * 4
                else:
                    parameterGroups_StructSize += 16
            return parameterGroups_StructSize

        def get_variables(self, material, offsetVariables):
            numVariables = 0
            for key, val in material.items():
                if (isinstance(val, float)) and (key[0] not in ('0', '1')):
                    numVariables += 1
            
            variables = []
            offset = offsetVariables + numVariables * 8
            for key, val in material.items():
                if (isinstance(val, float)) and (key[0] not in ('0', '1')):
                    offsetName = offset
                    value = val
                    name = key
                    variables.append([offsetName, value, name])
                    offset += len(name) + 1
            return variables

        def get_variables_StructSize(self, variables):
            if wmb4:
                return 0
            variables_StructSize = 0
            for variable in variables:
                variables_StructSize += 8
                variables_StructSize += len(variable[2]) + 1
            return variables_StructSize

        self.unknown0 = [] if wmb4 else [2016, 7, 5, 15] # This is probably always the same as far as I know?

        self.offsetName = self.offsetMaterial

        self.offsetShaderName = self.offsetName + len(self.b_material.name) + 1
        if wmb4:
            self.offsetShaderName = self.offsetName

        if not 'Shader_Name' in self.b_material:
            ShowMessageBox('Shader_Name not found. The exporter just tried converting a material that does not have all the required data. Check system console for details.', 'Invalid Material', 'ERROR')
            print('[ERROR] Invalid Material: Shader_Name not found.')
            print(' - If you know all materials used are valid, try ticking "Purge Materials" at export, this will clear all unused materials from your Blender file that might still be lingering.')
            print(' - WARNING: THIS WILL PERMANENTLY REMOVE ALL UNUSED MATERIALS.')

        self.offsetTechniqueName = self.offsetShaderName + len(self.b_material['Shader_Name']) + 1

        self.unknown1 = 1                           # This probably also the same mostly

        self.offsetTextures = self.offsetTechniqueName + len(self.b_material['Technique_Name']) + 1
        if wmb4:
            self.offsetTextures = self.offsetShaderName + len(self.b_material['Shader_Name'])
            self.offsetTextures += 16 - (self.offsetTextures % 16)

        self.textures = get_textures(self, self.b_material, self.offsetTextures)

        self.numTextures = len(self.textures)

        self.offsetParameterGroups = self.offsetTextures + get_textures_StructSize(self, self.textures)
        #print(hex(self.offsetParameterGroups))
        if wmb4 and (self.offsetParameterGroups % 16 > 0):
            self.offsetParameterGroups += 16 - (self.offsetParameterGroups % 16)

        self.numParameterGroups = get_numParameterGroups(self, self.b_material)  

        self.parameterGroups = get_parameterGroups(self, self.b_material, self.offsetParameterGroups, self.numParameterGroups)

        self.offsetVariables = self.offsetParameterGroups + get_parameterGroups_StructSize(self, self.parameterGroups)

        self.variables = get_variables(self, self.b_material, self.offsetVariables)

        self.numVariables = len(self.variables)

        self.name = self.b_material.name

        self.shaderName = self.b_material['Shader_Name']

        self.techniqueName = self.b_material['Technique_Name']
        
        self.materialNames_StructSize = self.offsetVariables + get_variables_StructSize(self, self.variables) - self.offsetName
        print(self.offsetShaderName, self.offsetTextures, self.offsetParameterGroups, self.materialNames_StructSize)

class c_materials(object):
    def __init__(self, materialsStart, wmb4=False):
        
        def get_materials(self):
            materials = []
            offsetMaterialName = materialsStart

            for mat in getUsedMaterials():
                offsetMaterialName += 48 if not wmb4 else 24 # Material Headers
            if wmb4 and (offsetMaterialName%16>0):
                offsetMaterialName += 16 - (offsetMaterialName%16)

            for mat in getUsedMaterials():
                print('[+] Generating Material', mat.name)
                material = c_material(offsetMaterialName, mat, wmb4)
                materials.append(material)

                offsetMaterialName += material.materialNames_StructSize

            return materials
        
        def get_materials_StructSize(self, materials):
            materials_StructSize = 0
            for material in materials:
                materials_StructSize += (48 if not wmb4 else 24) + material.materialNames_StructSize
                #if wmb4 and (materials_StructSize%16>0):
                #    materials_StructSize += 16 - (materials_StructSize%16)
                    
            return materials_StructSize

        self.materials = get_materials(self)
        self.materials_StructSize = get_materials_StructSize(self, self.materials)

def getObjectCenter(obj):
    obj_local_bbox_center = 0.125 * sum((Vector(b) for b in obj.bound_box), Vector())
    #obj_global_bbox_center = obj.matrix_world @ obj_local_bbox_center
    return obj_local_bbox_center

def getMeshBoundingBox(meshObj):
    xVals = []
    yVals = []
    zVals = []

    meshName = getRealName(meshObj.name)
    for obj in (x for x in bpy.data.collections['WMB'].all_objects if x.type == "MESH"):
        if getRealName(obj.name) == meshName:
            xVals.extend([getObjectCenter(obj)[0] - obj.dimensions[0]/2, getObjectCenter(obj)[0] + obj.dimensions[0]/2])
            yVals.extend([getObjectCenter(obj)[1] - obj.dimensions[1]/2, getObjectCenter(obj)[1] + obj.dimensions[1]/2])
            zVals.extend([getObjectCenter(obj)[2] - obj.dimensions[2]/2, getObjectCenter(obj)[2] + obj.dimensions[2]/2])

    minX = min(xVals)
    maxX = max(xVals)
    minY = min(yVals)
    maxY = max(yVals)
    minZ = min(zVals)
    maxZ = max(zVals)

    midPoint = [(minX + maxX)/2, (minY + maxY)/2, (minZ + maxZ)/2]
    scale = [maxX - midPoint[0], maxY - midPoint[1], maxZ - midPoint[2]]
    return midPoint, scale

class c_mesh(object):
    def __init__(self, offsetMeshes, numMeshes, obj, wmb4=False, meshIDOffset=0):

        def get_BoundingBox(self, obj):
            midPoint, scale = getMeshBoundingBox(obj)
            return midPoint + scale

        def get_materials(self, obj):
            materials = []
            obj_mesh_name = getRealName(obj.name)
            for mesh in (x for x in allObjectsInCollectionInOrder('WMB') if x.type == "MESH"):
                if getRealName(mesh.name) == obj_mesh_name:
                    for slot in mesh.material_slots:
                        material = slot.material
                        for indx, mat in enumerate(getUsedMaterials()):
                            if mat == material:
                                matID = indx
                                if matID not in materials:
                                    materials.append(matID)
                                    
            materials.sort()
            return materials

        def get_bones(self, obj):
            bones = []
            numBones = 0
            obj_mesh_name = getRealName(obj.name)
            for mesh in (x for x in allObjectsInCollectionInOrder('WMB') if x.type == "MESH"):
                if getRealName(mesh.name) == obj_mesh_name:
                    for vertexGroup in mesh.vertex_groups:
                        boneName = vertexGroup.name.replace('bone', '')
                        if int(boneName) not in bones:
                            bones.append(int(boneName))
                            numBones += 1
            if len(bones) == 0:
                bones.append(0)

            bones.sort()
            return bones, numBones
      
        self.bones, self.numBones = get_bones(self, obj)

        self.nameOffset = offsetMeshes + numMeshes * (44 if not wmb4 else 68)

        self.boundingBox = get_BoundingBox(self, obj)

        self.name = getRealName(obj.name)
        
        if wmb4:
            self.batches = []
            for mesh in (x for x in allObjectsInCollectionInOrder('WMB') if x.type == "MESH"):
                if getRealName(mesh.name) == getRealName(obj.name):
                    self.batches.append(mesh['ID'])
            
            self.batches = sorted(self.batches)
            
            if meshIDOffset == 0:
                prevBatch = self.batches[0] - 1
                for batch in self.batches:
                    if prevBatch + 1 < batch:
                        meshIDOffset = batch - 1
                        break
                    prevBatch = batch
            
            self.batches0 = self.batches
            self.batches1 = []
            self.batches2 = []
            self.batches3 = []
            if meshIDOffset > 0:
                for i, batch in enumerate(self.batches):
                    if batch > meshIDOffset:
                        self.batches0 = self.batches[0:i]
                        self.batches3 = self.batches[i:]
                        break
                
                self.batches3 = [batch - meshIDOffset - 1 for batch in self.batches3]
            #print(self.name, self.batches0, self.batches1, self.batches2, self.batches3)
        
        self.meshIDOffset = meshIDOffset
        
        if wmb4:
            self.batch0Pointer = self.nameOffset + len(self.name) + 1
            
            self.batch1Pointer = self.batch0Pointer
            self.batch1Pointer += len(self.batches0) * 2
            if (self.batch1Pointer % 16) > 0:
                self.batch1Pointer += 16 - (self.batch1Pointer % 16)
            
            self.batch2Pointer = self.batch1Pointer
            self.batch2Pointer += len(self.batches1) * 2
            if (self.batch2Pointer % 16) > 0:
                self.batch2Pointer += 16 - (self.batch2Pointer % 16)
            
            self.batch3Pointer = self.batch2Pointer
            self.batch3Pointer += len(self.batches2) * 2
            if (self.batch3Pointer % 16) > 0:
                self.batch3Pointer += 16 - (self.batch3Pointer % 16)
            
            self.offsetMaterials = self.batch3Pointer
            self.offsetMaterials += len(self.batches3) * 2
            if (self.offsetMaterials % 16) > 0:
                self.offsetMaterials += 16 - (self.offsetMaterials % 16)
            
            if len(self.batches1) == 0:
                self.batch1Pointer = 0
            if len(self.batches2) == 0:
                self.batch2Pointer = 0
            if len(self.batches3) == 0:
                self.batch3Pointer = 0
        else:
            self.offsetMaterials = self.nameOffset + len(self.name) + 1

        self.materials = get_materials(self, obj)

        self.numMaterials = len(self.materials)

        if self.numBones > 0 and not wmb4:
            self.offsetBones = self.offsetMaterials + 2*self.numMaterials
            self.lastOffset = self.offsetBones
        else:
            self.offsetBones = 0 
            self.numBones = 0    
            self.lastOffset = self.offsetMaterials

        def get_mesh_StructSize(self):
            mesh_StructSize = 4 + 24 + 4 + 4 + 4 + 4
            if wmb4:
                mesh_StructSize = 68
            mesh_StructSize += len(self.name) + 1
            if wmb4:
                #print(mesh_StructSize % 16)
                mesh_StructSize += self.offsetMaterials - self.batch0Pointer
                mesh_StructSize += len(self.materials) * 2
            else:
                mesh_StructSize += len(self.materials) * 2
                mesh_StructSize += len(self.bones) * 2
            return mesh_StructSize

        self.mesh_StructSize = get_mesh_StructSize(self)

        self.blenderObj = obj

class c_meshes(object):
    def __init__(self, offsetMeshes, wmb4=False):
        
        self.meshIDOffset = 0
        def get_meshes(self, offsetMeshes):
            meshes = []

            meshNames = []
            
            for obj in (x for x in allObjectsInCollectionInOrder('WMB') if x.type == "MESH"):
                obj_name = getRealName(obj.name)
                if obj_name not in meshNames:
                    meshNames.append(obj_name)

            numMeshes = len(meshNames)

            #sort mesh names by meshGroupIndex
            meshNamesSorted = [None] * numMeshes
            for meshName in meshNames:
                for obj in (x for x in allObjectsInCollectionInOrder('WMB') if x.type == "MESH"):
                    obj_name = getRealName(obj.name)
                    if obj_name == meshName:
                        meshNamesSorted[obj["meshGroupIndex"]] = meshName
                        break
            print("Meshes to generate:", meshNamesSorted)

            meshes_added = []
            # first name pointer is aligned
            if wmb4 and ((offsetMeshes + numMeshes*68) % 16 > 0):
                offsetMeshes += 16 - ((offsetMeshes + numMeshes*68) % 16)
            
            for meshName in meshNamesSorted:
                for obj in (x for x in allObjectsInCollectionInOrder('WMB') if x.type == "MESH"):
                    obj_name = getRealName(obj.name)
                    if obj_name == meshName:
                        if obj_name not in meshes_added:
                            print('[+] Generating Mesh', meshName)
                            mesh = c_mesh(offsetMeshes, numMeshes, obj, wmb4, self.meshIDOffset)
                            self.meshIDOffset = mesh.meshIDOffset
                            meshes.append(mesh)
                            meshes_added.append(obj_name)
                            offsetMeshes += mesh.mesh_StructSize
                            offsetMeshes -= 68 if wmb4 else 44
                            break

            return meshes

        def get_meshes_StructSize(self, meshes):
            meshes_StructSize = 0
            for mesh in meshes:
                meshes_StructSize += mesh.mesh_StructSize
            return meshes_StructSize

        self.meshes = get_meshes(self, offsetMeshes)

        self.meshes_StructSize = get_meshes_StructSize(self, self.meshes)

class c_meshMaterials(object):
    def __init__(self, meshes, lods):
        def get_meshMaterials(self):
            meshMaterials = []
            for mesh_index, mesh in enumerate(meshes.meshes):
                blenderObj = mesh.blenderObj
                for slot in blenderObj.material_slots:
                    material = slot.material
                    for mat_index, mat in enumerate(getUsedMaterials()):
                        if mat == material:
                            struct = [mesh_index, mat_index]
                            if struct not in meshMaterials:
                                meshMaterials.append(struct)
                                break
            return meshMaterials

        self.meshMaterials = get_meshMaterials(self)
        self.meshMaterials_StructSize = len(self.meshMaterials) * 8
        
        # Update LODS meshMatPairs
        if lods is not None:
            for lod in lods.lods:
                for batchInfo in lod.batchInfos:
                    for meshMat_index, meshMaterial in enumerate(self.meshMaterials):
                        if meshMaterial[0] == batchInfo[1] and meshMaterial[1] == batchInfo[2]:
                            batchInfo[4] = meshMat_index
                            break

class c_textures(object): # wmb4
    def __init__(self, texturesPointer, materials):
        self.textures = []
        for mat in materials:
            #for tex in mat.textures:
            """
             1 (maybe 0 too) is first
             then 3
             then 5 OR 6
             then 7
             then 4 OR 9
             1 is BEFORE 7
             no 2 or 8
             1 is BEFORE 3... ok
             is it just skipping 2, 4, 8?
             wtf platinum
            """
            for index in [0, 1, 3, 5, 6, 7, 9, 10, 11, 12, 13]:
                if index >= len(mat.textures):
                    break
                if mat.textures[index][1] not in (x[1] for x in self.textures):
                    self.textures.append([0x63, mat.textures[index][1]])
        
        #print(self.textures)
        self.textures_StructSize = 8 * len(self.textures)

class c_unknownWorldData(object):
    def __init__(self):
        def get_unknownWorldData():
            unknownWorldData = []
            b_unknownWorldData = bpy.context.scene['unknownWorldData']
            for key in b_unknownWorldData.keys():
                val = b_unknownWorldData[key]
                unknownWorldData.append([val[0], val[1], val[2], val[3], val[4], val[5]])
            return unknownWorldData

        def get_unknownWorldDataSize(unknownWorldData):
            unknownWorldDataSize = len(unknownWorldData) * 24
            return unknownWorldDataSize

        self.unknownWorldData = get_unknownWorldData()
        self.unknownWorldDataSize = get_unknownWorldDataSize(self.unknownWorldData)
        self.unknownWorldDataCount = len(self.unknownWorldData)

class c_vertexGroup(object):
    def __init__(self, vertexGroupIndex, vertexesStart, wmb4=False):
        self.vertexGroupIndex = vertexGroupIndex
        self.vertexGroupStart = vertexesStart

        def get_blenderObjects(self):
            objs = {}
            meshes = sorted([x for x in allObjectsInCollectionInOrder('WMB') if x.type == "MESH"], key=lambda mesh: mesh['ID'])
            
            for index, obj in enumerate(meshes):
                obj_name = obj.name.split('-')
                if int(obj_name[0 if wmb4 else -1]) == vertexGroupIndex:
                    if len(obj.data.uv_layers) == 0:
                        obj.data.uv_layers.new()
                    obj.data.calc_tangents()
                    if not wmb4:
                        objs[int(obj_name[0])] = obj
                    else:
                        #if len(obj_name) == 2:
                        #    objs[0] = obj # didn't put a number on the first one
                        #else:
                        #    objs[int(obj_name[-1])] = obj
                        objs[index] = obj

            blenderObjects = []
            for key in sorted (objs):
                blenderObjects.append(objs[key])
            print(blenderObjects)
            return blenderObjects
        
        self.blenderObjects = get_blenderObjects(self)
        
        def get_numVertices(self):
            numVertices = 0
            for obj in self.blenderObjects:
                numVertices += len(obj.data.vertices)
            return numVertices
        numVertices = get_numVertices(self)

        def get_numIndexes(self):
            numIndexes = 0
            for obj in self.blenderObjects:
                numIndexes += len(obj.data.polygons)
            return numIndexes * 3
        
        def get_blenderVertices(self):
            blenderVertices = []
            blenderObjects = self.blenderObjects

            for obj in blenderObjects:
                blenderVertices.append([obj.data.vertices, obj])
            return blenderVertices
            
        blenderVertices = get_blenderVertices(self)

        def get_blenderLoops(self, objOwner):
            blenderLoops = []
            blenderLoops += objOwner.data.loops

            return blenderLoops

        def get_blenderUVCoords(self, objOwner, loopIndex, uvSlot):
            if uvSlot > len(objOwner.data.uv_layers)-1:
                print(" - UV Maps Error: Not enough UV Map layers! (Tried accessing UV layer number", uvSlot + 1, "of object", objOwner.name, "but it does not exist. Adding one!")
                objOwner.data.uv_layers.new()
            uv_coords = objOwner.data.uv_layers[uvSlot].data[loopIndex].uv
            return [uv_coords.x, 1-uv_coords.y]

        # Has bones = 7, 10, 11
        # 1 UV  = 0
        # 2 UVs = 1, 4, 7, 10
        # 3 UVs = 5, 11
        # 4 UVs = 14
        # 5 UVs = 12
        # Has Color = 4, 5, 10, 11, 12, 14

        if len(self.blenderObjects[0].data.uv_layers) == 1:         # 0
            self.vertexFlags = 0
        elif len(self.blenderObjects[0].data.uv_layers) == 2:       # 1, 4, 7, 10
            if self.blenderObjects[0]['boneSetIndex'] != -1:        # > 7, 10
                if self.blenderObjects[0].data.vertex_colors:       # >> 10
                    self.vertexFlags = 10
                else:                                               # >> 7
                    self.vertexFlags = 7

            else:                                                   # > 1, 4
                if self.blenderObjects[0].data.vertex_colors:       # >> 4
                    self.vertexFlags = 4
                else:                                               # >> 1
                    self.vertexFlags = 1


        elif len(self.blenderObjects[0].data.uv_layers) == 3:       # 5, 11
            if self.blenderObjects[0]['boneSetIndex'] != -1:        # >> 11
                self.vertexFlags = 11
            else:                                                   # >> 5
                self.vertexFlags = 5

        elif len(self.blenderObjects[0].data.uv_layers) == 4:       # 14
            self.vertexFlags = 14
        elif len(self.blenderObjects[0].data.uv_layers) == 5:       # 12
            self.vertexFlags = 12
        else:
            print(" - UV Maps Error: No UV Map found!")
        
        #print("   Vertex Group %d has vertexFlags %d" % (vertexGroupIndex, self.vertexFlags))
        
        if self.vertexFlags == 0:
            self.vertexExDataSize = 0
        if self.vertexFlags == 4:                                         
            self.vertexExDataSize = 8       
        elif self.vertexFlags in {5, 7}:                                          
            self.vertexExDataSize = 12                                    
        elif self.vertexFlags in {10, 14}:
            self.vertexExDataSize = 16
        elif self.vertexFlags in {11, 12}:
            self.vertexExDataSize = 20
        
        if wmb4:
            vertexFormat = bpy.data.collections['WMB']['vertexFormat']
            if vertexFormat in {0x10337, 0x00337}:
                self.vertexExDataSize = 8
            elif vertexFormat == 0x10137:
                self.vertexExDataSize = 4
            else:
                self.vertexExDataSize = 0

        def get_boneMap(self):
            boneMap = []
            for obj in bpy.data.collections['WMB'].all_objects:
                if obj.type == 'ARMATURE':
                    boneMapRef = obj.data["boneMap"]
                    for val in boneMapRef:
                        boneMap.append(val)
                    return boneMap

        self.boneMap = get_boneMap(self) if not wmb4 else None

        def get_boneSet(self, boneSetIndex):
            boneSet = []
            if boneSetIndex == -1:
                return boneSet
            for obj in bpy.data.collections['WMB'].all_objects:
                if obj.type == 'ARMATURE':
                    boneSetArrayRef = obj.data["boneSetArray"][boneSetIndex]
                    #print(boneSetArrayRef)
                    #print(obj.data["boneSetArray"])
                    for val in boneSetArrayRef:
                        boneSet.append(val)
                    #print(boneSet)
                    return boneSet

        def get_vertexesData(self):
            vertexes = []
            vertexesExData = []
            for bvertex_obj in blenderVertices:
                bvertex_obj_obj = bvertex_obj[1]
                print('   [>] Generating vertex data for object', bvertex_obj_obj.name)
                loops = get_blenderLoops(self, bvertex_obj_obj)
                sorted_loops = sorted(loops, key=lambda loop: loop.vertex_index)

                if self.vertexFlags not in {0, 1, 4, 5, 12, 14} or wmb4:
                    boneSet = get_boneSet(self, bvertex_obj_obj["boneSetIndex"])
                
                previousIndex = -1
                for loop in sorted_loops:
                    if loop.vertex_index == previousIndex:
                        continue

                    previousIndex = loop.vertex_index
            
                    bvertex = bvertex_obj[0][loop.vertex_index]
                    # XYZ Position
                    position = [bvertex.co.x, bvertex.co.y, bvertex.co.z]

                    # Tangents
                    loopTangent = loop.tangent * 127
                    tx = int(loopTangent[0] + 127.0)
                    ty = int(loopTangent[1] + 127.0)
                    tz = int(loopTangent[2] + 127.0)
                    sign = int(-loop.bitangent_sign*127.0+128.0)

                    tangents = [tx, ty, tz, sign]

                    # Normal
                    normal = []
                    if self.vertexFlags == 0 or wmb4:
                        normal = [loop.normal[0], loop.normal[1], loop.normal[2], 0]
                        if wmb4:
                            #print(normal)
                            # what the fuck is this, 11 bit values?
                            """
                            if (normal[0] < 0):
                                normal[0] = -(0x400-normal[0])
                                normal[0] ^= 0x400
                            if (normal[1] < 0):
                                normal[1] = -(0x400-normal[1])
                                normal[1] ^= 0x400
                            if (normal[2] < 0):
                                normal[2] = -(0x200-normal[2])
                                normal[2] ^= 0x200
                            true_normal = normal[0] # bits 0-11
                            true_normal |= normal[1]<<11
                            true_normal |= normal[2]<<22
                            normal = true_normal
                            """
                            # help me chatgpt, you're my only hope
                            nx = int(round(normal[0] * float((1<<10)-1)))
                            ny = int(round(normal[1] * float((1<<10)-1)))
                            nz = int(round(normal[2] * float((1<<9 )-1)))
                            if nx < 0:
                                nx += (1 << 10)
                                nx ^= 1 << 10
                            if ny < 0:
                                ny += (1 << 10)
                                ny ^= 1 << 10
                            if nz < 0:
                                nz += (1 << 9)
                                nz ^= 1 << 9
                            normal = nx | (ny << 11) | (nz << 22)
                        
                    # UVs
                    uv_maps = []

                    uv1 = get_blenderUVCoords(self, bvertex_obj_obj, loop.index, 0)
                    uv_maps.append(uv1)

                    if self.vertexFlags in {1, 4, 5, 12, 14}:
                        uv2 = get_blenderUVCoords(self, bvertex_obj_obj, loop.index, 1)
                        uv_maps.append(uv2)

                    # Bones
                    boneIndexes = []
                    boneWeights = []
                    if self.vertexFlags in {7, 10, 11} or (wmb4 and vertexFormat & 0x30 == 0x30):
                        # Bone Indices
                        for groupRef in bvertex.groups:
                            if len(boneIndexes) < 4:
                                boneGroupName = bvertex_obj_obj.vertex_groups[groupRef.group].name
                                boneID = int(boneGroupName.replace("bone", ""))
                                if not wmb4:
                                    boneMapIndx = self.boneMap.index(boneID)
                                    boneSetIndx = boneSet.index(boneMapIndx)
                                    boneIndexes.append(boneSetIndx)
                                else:
                                    try:
                                        boneSetIndx = boneSet.index(boneID)
                                    except: # bone not in set? well fuck that
                                        for obj in bpy.data.collections['WMB'].all_objects:
                                            if obj.type == 'ARMATURE':
                                            
                                                allbonesets = list(obj.data["boneSetArray"])
                                                boneSet = list(allbonesets[bvertex_obj_obj["boneSetIndex"]])
                                                if boneID not in boneSet:
                                                    boneSet.append(boneID)
                                                allbonesets[bvertex_obj_obj["boneSetIndex"]] = boneSet
                                                obj.data["boneSetArray"] = allbonesets
                                                boneSetIndx = boneSet.index(boneID) # i swear to god # !!!
                                    
                                    if boneSetIndx < 0 or boneSetIndx > 255:
                                        print("Hmm, boneID of", boneSetIndx, "could be a problem...")
                                        print(boneSet)
                                    
                                    boneIndexes.append(boneSetIndx)
                        
                        if len(boneIndexes) == 0:
                            print(len(vertexes) ,"- Vertex Weights Error: Vertex has no assigned groups. At least 1 required. Try using Blender's [Select -> Select All By Trait > Ungrouped Verts] function to find them.")

                        while len(boneIndexes) < 4:
                            boneIndexes.append(0)
                        
                        # Bone Weights
                        weights = [group.weight for group in bvertex.groups]
                        weightsSum = sum(weights)

                        if len(weights) >  4:
                            print(len(vertexes), "- Vertex Weights Error: Vertex has weights assigned to more than 4 groups. Try using Blender's [Weights -> Limit Total] function.")

                        normalized_weights = []                                             # Force normalize the weights as Blender's normalization sometimes get some rounding issues.
                        for val in weights:
                            if val > 0:
                                normalized_weights.append(float(val)/weightsSum)
                            else:
                                normalized_weights.append(0)

                        for val in normalized_weights:
                            if len(boneWeights) < 4:
                                weight = math.floor(val * 256.0)
                                if val == 1.0:
                                    weight = 255
                                boneWeights.append(weight)
                        
                        while len(boneWeights) < 4:
                            boneWeights.append(0)

                        while sum(boneWeights) < 255:                     # MOAR checks to make sure weights are normalized but in bytes. (A bit cheating but these values should make such a minor impact.)
                            boneWeights[0] += 1

                        while sum(boneWeights) > 255:                     
                            boneWeights[0] -= 1

                        if sum(boneWeights) != 255:                       # If EVEN the FORCED normalization doesn't work, say something :/
                            print(len(vertexes), "- Vertex Weights Error: Vertex has a total weight not equal to 1.0. Try using Blender's [Weights -> Normalize All] function.") 

                    color = []
                    if self.vertexFlags in {4, 5, 12, 14} or (wmb4 and vertexFormat >= 0x337):
                        if len (bvertex_obj_obj.data.vertex_colors) == 0:
                            print("Object had no vertex colour layer when one was expected - creating one.")
                            new_vertex_colors = bvertex_obj_obj.data.vertex_colors.new()
                        loop_color = bvertex_obj_obj.data.vertex_colors.active.data[loop.index].color
                        color = [int(loop_color[0]*255), int(loop_color[1]*255), int(loop_color[2]*255), int(loop_color[3]*255)]

                    vertexes.append([position, tangents, normal, uv_maps, boneIndexes, boneWeights, color])

                    
                    ##################################################
                    ###### Now lets do the extra data shit ###########
                    ##################################################
                    normal = []
                    uv_maps = []
                    color = []
                    if wmb4:
                        if vertexFormat in {0x10337, 0x10137, 0x00337}:
                            if vertexFormat != 0x10137:
                                uv2 = get_blenderUVCoords(self, bvertex_obj_obj, loop.index, 1)
                                uv_maps.append(uv2)
                            loop_color = bvertex_obj_obj.data.vertex_colors.active.data[loop.index].color
                            color = [int(loop_color[0]*255), int(loop_color[1]*255), int(loop_color[2]*255), int(loop_color[3]*255)]
                    
                    else:
                        
                        if self.vertexFlags in {10, 11}:
                            if len (bvertex_obj_obj.data.vertex_colors) == 0:
                                print("Object had no vertex colour layer when one was expected - creating one.")
                                new_vertex_colors = bvertex_obj_obj.data.vertex_colors.new()

                        if self.vertexFlags in {1, 4, 5, 7, 10, 11, 12, 14}:
                            normal = [loop.normal[0], loop.normal[1], loop.normal[2], 0]
                        
                        if self.vertexFlags == 5:
                            uv3 = get_blenderUVCoords(self, bvertex_obj_obj, loop.index, 2)
                            uv_maps.append(uv3)

                        elif self.vertexFlags == 7:
                            uv2 = get_blenderUVCoords(self, bvertex_obj_obj, loop.index, 1)
                            uv_maps.append(uv2)

                        elif self.vertexFlags == 10:
                            uv2 = get_blenderUVCoords(self, bvertex_obj_obj, loop.index, 1)
                            uv_maps.append(uv2)
                            loop_color = bvertex_obj_obj.data.vertex_colors.active.data[loop.index].color
                            color = [int(loop_color[0]*255), int(loop_color[1]*255), int(loop_color[2]*255), int(loop_color[3]*255)]

                        elif self.vertexFlags == 11:
                            uv2 = get_blenderUVCoords(self, bvertex_obj_obj, loop.index, 1)
                            uv_maps.append(uv2)
                            loop_color = bvertex_obj_obj.data.vertex_colors.active.data[loop.index].color
                            color = [int(loop_color[0]*255), int(loop_color[1]*255), int(loop_color[2]*255), int(loop_color[3]*255)]
                            uv3 = get_blenderUVCoords(self, bvertex_obj_obj, loop.index, 1)
                            uv_maps.append(uv3)

                        elif self.vertexFlags == 12:
                            uv3 = get_blenderUVCoords(self, bvertex_obj_obj, loop.index, 2)
                            uv_maps.append(uv3)
                            uv4 = get_blenderUVCoords(self, bvertex_obj_obj, loop.index, 3)
                            uv_maps.append(uv4)
                            uv5 = get_blenderUVCoords(self, bvertex_obj_obj, loop.index, 4)
                            uv_maps.append(uv5)

                        elif self.vertexFlags == 14:
                            uv3 = get_blenderUVCoords(self, bvertex_obj_obj, loop.index, 2)
                            uv_maps.append(uv3)
                            uv4 = get_blenderUVCoords(self, bvertex_obj_obj, loop.index, 3)
                            uv_maps.append(uv4)
                    
                    vertexExData = [normal, uv_maps, color]
                    vertexesExData.append(vertexExData)
            #print(hex(len(vertexes)))
            
            return vertexes, vertexesExData

        def get_indexes(self):
            indexesOffset = 0
            indexes = []
            for obj in self.blenderObjects:
                for loop in obj.data.loops:
                    indexes.append(loop.vertex_index + indexesOffset)
                if not wmb4:
                    indexesOffset += len(obj.data.vertices)

            # Reverse this loop order
            flip_counter = 0
            for i in range(len(indexes)):
                if flip_counter == 2:
                    indexes[i], indexes[i-1] = indexes[i-1], indexes[i]
                    flip_counter = 0
                    continue
                flip_counter += 1

            return indexes

        self.vertexSize = 32 if wmb4 else 28

        self.vertexOffset = self.vertexGroupStart                       
        self.vertexExDataOffset = self.vertexOffset + numVertices * self.vertexSize
        if wmb4 and self.vertexExDataSize == 0:
            self.vertexExDataOffset = 0

        self.unknownOffset = [0, 0]  # Don't question it, it's unknown okay?

        self.unknownSize = [0, 0]    # THIS IS UNKOWN TOO OKAY? LEAVE ME BE
        # *unknown

        self.numVertexes = numVertices

        self.indexBufferOffset = self.vertexOffset + numVertices * (self.vertexSize + self.vertexExDataSize)
        if wmb4 and (self.indexBufferOffset % 16 > 0):
            self.indexBufferOffset += 16 - (self.indexBufferOffset % 16)
        
        self.numIndexes = get_numIndexes(self)

        self.vertexes, self.vertexesExData = get_vertexesData(self)
        
        self.indexes = get_indexes(self)

        self.vertexGroupSize = (self.indexBufferOffset - self.vertexOffset) + (self.numIndexes * (2 if wmb4 else 4))

class c_vertexGroups(object):
    def __init__(self, offsetVertexGroups, wmb4=False):
        self.offsetVertexGroups = offsetVertexGroups
        
        # Alright, before we do anything, let's fix the mess that is object IDs
        allMeshes = [obj for obj in bpy.data.collections['WMB'].all_objects if obj.type == 'MESH']
        for obj in allMeshes:
            obj['ID'] += 1000 * obj['batchGroup'] # make sure it's sorted by batch group
        
        allIDs = sorted([obj['ID'] for obj in allMeshes])
        allMeshes = sorted(allMeshes, key=lambda batch: batch['ID']) # sort
        
        for obj in allMeshes:
            obj['ID'] = allIDs.index(obj['ID']) # masterstroke
        
        print("New IDs generated:")
        print([(obj.name, obj['ID']) for obj in allMeshes])
        

        def get_vertexGroups(self, offsetVertexGroups):
            vertexGroupIndex = []

            for obj in bpy.data.collections['WMB'].all_objects:
                if obj.type == 'MESH':
                    obj_name = obj.name.split('-')
                    obj_vertexGroupIndex = int(obj_name[0 if wmb4 else -1])
                    if obj_vertexGroupIndex not in vertexGroupIndex:
                        vertexGroupIndex.append(obj_vertexGroupIndex)

            vertexGroupIndex.sort()
            
            vertexGroupHeaderSize = 28 if wmb4 else 48
            
            vertexesOffset = offsetVertexGroups + len(vertexGroupIndex) * vertexGroupHeaderSize
            if vertexesOffset % 16 > 0:
                vertexesOffset += 16 - (vertexesOffset % 16)
            
            vertexGroups = []
            for index in vertexGroupIndex:
                print('[+] Creating Vertex Group', index)
                vertexGroups.append(c_vertexGroup(index, vertexesOffset, wmb4))
                vertexesOffset += vertexGroups[index].vertexGroupSize
                padAmount = 0
                if wmb4 and (vertexesOffset % 16 > 0):
                    padAmount = 16 - (vertexesOffset % 16)
                    vertexesOffset += padAmount
                    vertexGroups[index].vertexGroupSize += padAmount
            
            if padAmount > 0: # no padding on end
                print("Removing excess padding of %d bytes from vertex group %d" % (padAmount, index))
                print("This leaves the offset at", hex(vertexesOffset-padAmount))
                vertexGroups[index].vertexGroupSize -= padAmount
            
            return vertexGroups

        self.vertexGroups = get_vertexGroups(self, self.offsetVertexGroups)

        def get_vertexGroupsSize(self, vertexGroups):
            vertexGroupsSize = len(vertexGroups) * (28 if wmb4 else 48)
            if wmb4 and (vertexGroupsSize % 16 > 0):
                vertexGroupsSize += 16 - (vertexGroupsSize % 16)

            for vertexGroup in vertexGroups:
                vertexGroupsSize += vertexGroup.vertexGroupSize
            return vertexGroupsSize

        self.vertexGroups_StructSize = get_vertexGroupsSize(self, self.vertexGroups)



class c_generate_data(object):
    def __init__(self, wmb4=False):
        hasArmature = False
        hasColTreeNodes = False
        hasUnknownWorldData = False

        for obj in bpy.data.collections['WMB'].all_objects:
            if obj.type == 'ARMATURE':
                print('Armature found, exporting bones structures.')
                hasArmature = True
                break

        if 'colTreeNodes' in bpy.context.scene:
            hasColTreeNodes = True

        if 'unknownWorldData' in bpy.context.scene:
            hasUnknownWorldData = True

        # Generate custom boneSets from Blender vertex groups
        if hasArmature:
            self.b_boneSets = c_b_boneSets(wmb4)

        currentOffset = 0

        self.header_Offset = currentOffset
        self.header_Size = 112 if wmb4 else 136
        currentOffset += self.header_Size
        print('header_Size: ', self.header_Size)

        currentOffset += 16 - (currentOffset % 16)
        
        if not wmb4:
            
            if hasArmature:
                self.bones_Offset = currentOffset
                self.bones = c_bones()
                self.numBones = len(self.bones.bones)
                self.bones_Size = self.bones.bones_StructSize
                currentOffset += self.bones_Size
                print('bones_Size: ', self.bones_Size)

                currentOffset += 16 - (currentOffset % 16)

                self.boneIndexTranslateTable_Offset = currentOffset
                self.boneIndexTranslateTable = c_boneIndexTranslateTable(self.bones)
                self.boneIndexTranslateTable_Size = self.boneIndexTranslateTable.boneIndexTranslateTable_StructSize
                currentOffset += self.boneIndexTranslateTable_Size
                print('boneIndexTranslateTable_Size: ', self.boneIndexTranslateTable_Size)
            else:
                self.bones_Offset = 0
                self.bones = None
                self.numBones = 0
                self.bones_Size = 0
                self.boneIndexTranslateTable_Offset = 0
                self.boneIndexTranslateTable_Size = 0


            currentOffset += 16 - (currentOffset % 16)

            self.vertexGroups_Offset = currentOffset
            self.vertexGroups = c_vertexGroups(self.vertexGroups_Offset)
            self.vertexGroupsCount = len(self.vertexGroups.vertexGroups)
            self.vertexGroups_Size = self.vertexGroups.vertexGroups_StructSize
            currentOffset += self.vertexGroups_Size
            print('vertexGroups_Size: ', self.vertexGroups_Size)

            currentOffset += 16 - (currentOffset % 16)

            if hasArmature:
                self.boneMap = c_boneMap(self.bones)
                self.numBoneMap = len(self.boneMap.boneMap)
            else:
                self.boneMap = None
                self.numBoneMap = 0

            self.batches_Offset = currentOffset
            self.batches = c_batches(self.vertexGroupsCount)
            self.batches_Size = self.batches.batches_StructSize
            currentOffset += self.batches_Size
            print('batches_Size: ', self.batches_Size)

            currentOffset += 52

            # Generate custom colTreeNodes in time for LOD data
            if hasColTreeNodes:
                self.colTreeNodes = c_colTreeNodes()
            self.lods_Offset = currentOffset
            self.lods = c_lods(self.lods_Offset, self.batches)
            self.lods_Size = self.lods.lods_StructSize
            self.lodsCount = len(self.lods.lods)
            currentOffset += self.lods_Size
            print('lods_Size: ', self.lods_Size)

            currentOffset += 16 - (currentOffset % 16)

            self.meshMaterials_Offset = currentOffset
            self.meshMaterials_Size = len(self.batches.batches) * 8
            currentOffset += self.meshMaterials_Size
            print('meshMaterials_Size: ', self.meshMaterials_Size)

            currentOffset += 16 - (currentOffset % 16)

            # ColTreeNodes Data actually gets stored here
            if hasColTreeNodes:
                self.colTreeNodes_Offset = currentOffset
                self.colTreeNodesSize = self.colTreeNodes.colTreeNodesSize
                self.colTreeNodesCount = self.colTreeNodes.colTreeNodesCount
                currentOffset += self.colTreeNodesSize
            else:
                self.colTreeNodes = None
                self.colTreeNodes_Offset = 0
                self.colTreeNodesCount = 0

            currentOffset += 16 - (currentOffset % 16)

            if hasArmature:
                self.boneSets_Offset = currentOffset

                if self.boneMap is None or len(self.boneMap.boneMap) > 1:
                    self.boneSet = c_boneSet(self.boneMap, self.boneSets_Offset)
                    self.boneSet_Size = self.boneSet.boneSet_StructSize
                    currentOffset += self.boneSet_Size
                else:
                    self.boneSets_Offset = 0

                currentOffset += 16 - (currentOffset % 16)

                self.boneMap_Offset = currentOffset
                self.boneMap_Size = self.boneMap.boneMap_StructSize
                currentOffset += self.boneMap_Size
                print('boneMap_Size: ', self.boneMap_Size)
            else:
                self.boneMap_Offset = 0
                self.boneSets_Offset = 0

            self.meshes_Offset = currentOffset
            self.meshes = c_meshes(self.meshes_Offset)
            self.meshes_Size = self.meshes.meshes_StructSize
            currentOffset += self.meshes_Size
            print('meshes_Size: ', self.meshes_Size)
            if not hasArmature:
                for mesh in self.meshes.meshes:
                    mesh.numBones = 0

            currentOffset += 16 - (currentOffset % 16)

            self.materials_Offset = currentOffset
            self.materials = c_materials(self.materials_Offset)
            self.materials_Size = self.materials.materials_StructSize
            currentOffset += self.materials_Size
            print('materials_Size: ', self.materials_Size)

            if hasUnknownWorldData:
                self.unknownWorldData_Offset = currentOffset
                self.unknownWorldData = c_unknownWorldData()
                self.unknownWorldDataSize = self.unknownWorldData.unknownWorldDataSize
                self.unknownWorldDataCount = self.unknownWorldData.unknownWorldDataCount
                currentOffset += self.unknownWorldDataSize
            else:
                self.unknownWorldData = None
                self.unknownWorldData_Offset = 0
                self.unknownWorldDataCount = 0

            self.meshMaterials = c_meshMaterials(self.meshes, self.lods)
            self.meshMaterials_Size = self.meshMaterials.meshMaterials_StructSize
            
        else:
            
            self.vertexFormat = bpy.data.collections['WMB']['vertexFormat']

            self.vertexGroups_Offset = currentOffset
            self.vertexGroups = c_vertexGroups(self.vertexGroups_Offset, True)
            self.vertexGroupsCount = len(self.vertexGroups.vertexGroups)
            self.vertexGroups_Size = self.vertexGroups.vertexGroups_StructSize
            currentOffset += self.vertexGroups_Size
            print('vertexGroups_Size: ', self.vertexGroups_Size)

            #currentOffset += 16 - (currentOffset % 16)
            
            self.batches_Offset = currentOffset
            self.batches = c_batches(self.vertexGroupsCount, wmb4)
            self.batches_Size = self.batches.batches_StructSize
            currentOffset += self.batches_Size
            print('batches_Size: ', self.batches_Size)

            #currentOffset += 16 - (currentOffset % 16)
            
            self.batchDescPointer = currentOffset
            self.batchDescriptions = c_batch_supplements(currentOffset)
            self.batchDescSize = self.batchDescriptions.supplementStructSize
            currentOffset += self.batchDescSize
            print('batchDescSize: ', self.batchDescSize)
            
            #currentOffset += 16 - (currentOffset % 16)
            
            if hasArmature:
                self.bones_Offset = currentOffset
                self.bones = c_bones(True)
                self.numBones = len(self.bones.bones)
                self.bones_Size = self.bones.bones_StructSize
                currentOffset += self.bones_Size
                print('bones_Size: ', self.bones_Size)

                #currentOffset += 16 - (currentOffset % 16)

                self.boneIndexTranslateTable_Offset = currentOffset
                self.boneIndexTranslateTable = c_boneIndexTranslateTable(self.bones)
                self.boneIndexTranslateTable_Size = self.boneIndexTranslateTable.boneIndexTranslateTable_StructSize
                currentOffset += self.boneIndexTranslateTable_Size
                print('boneIndexTranslateTable_Size: ', self.boneIndexTranslateTable_Size)

                # psyche, this one is padded
                currentOffset += 16 - (currentOffset % 16)
            else:
                self.bones_Offset = 0
                self.bones = None
                self.numBones = 0
                self.bones_Size = 0
                self.boneIndexTranslateTable_Offset = 0
                self.boneIndexTranslateTable_Size = 0

            self.boneMap = None
            self.numBoneMap = 0

            self.lods = None

            self.colTreeNodes = None
            self.colTreeNodes_Offset = 0
            self.colTreeNodesCount = 0

            if hasArmature:
                self.boneSets_Offset = currentOffset
                self.boneSet = c_boneSet(self.boneMap, self.boneSets_Offset, True)
                self.boneSet_Size = self.boneSet.boneSet_StructSize
                currentOffset += self.boneSet_Size
                print('boneSet_Size: ', self.boneSet_Size)

                #currentOffset += 16 - (currentOffset % 16)
            else:
                self.boneMap_Offset = 0
                self.boneSets_Offset = 0

            self.materials_Offset = currentOffset
            self.materials = c_materials(self.materials_Offset, True)
            self.materials_Size = self.materials.materials_StructSize
            currentOffset += self.materials_Size
            print('materials_Size: ', self.materials_Size)
            
            currentOffset += 16 - (currentOffset % 16)
            
            self.textures_Offset = currentOffset
            self.textures = c_textures(self.textures_Offset, self.materials.materials)
            self.textures_Size = self.textures.textures_StructSize
            # TODO fuck, this doesn't parse in the normal order... now I need to track every pointer # huh?
            currentOffset += self.textures_Size
            print('textures_Size: ', self.textures_Size)
            
            if currentOffset % 16 > 0:
                currentOffset += 16 - (currentOffset % 16)
            
            self.meshes_Offset = currentOffset
            self.meshes = c_meshes(self.meshes_Offset, True)
            self.meshes_Size = self.meshes.meshes_StructSize
            currentOffset += self.meshes_Size
            print('meshes_Size: ', self.meshes_Size)
            
            if not hasArmature:
                for mesh in self.meshes.meshes:
                    mesh.numBones = 0
            