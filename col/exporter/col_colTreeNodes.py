import math


def update_offsetMeshIndices(colTreeNodes, meshIndicesStartOffset):
    currentOffset = meshIndicesStartOffset
    for colTreeNode in colTreeNodes:
        colTreeNode.meshIndexCount = len(colTreeNode.meshIndices)
        if colTreeNode.meshIndexCount > 0:
            colTreeNode.offsetMeshIndices = currentOffset
            currentOffset += colTreeNode.meshIndexCount * 4
"""
def inside_volume(obj, node, precision):
    obj_local_bbox_center = 0.125 * sum((Vector(b) for b in obj.bound_box), Vector())
    obj_global_bbox_center = obj.matrix_world @ obj_local_bbox_center
    
    node_center = [node.p1.x, -node.p1.z, node.p1.y]
    node_scale = node.p2

    node_x_min = round(node_center[0] - node_scale[0], precision)
    node_x_max = round(node_center[0] + node_scale[0], precision)

    node_y_min = round(node_center[1] - node_scale[1], precision)
    node_y_max = round(node_center[1] + node_scale[1], precision)

    node_z_min = round(node_center[2] - node_scale[2], precision)
    node_z_max = round(node_center[2] + node_scale[2], precision)

    obj_x_min = round(obj_global_bbox_center[0] - obj.dimensions.x/2, precision)
    obj_x_max = round(obj_global_bbox_center[0] + obj.dimensions.x/2, precision)

    obj_y_min = round(obj_global_bbox_center[1] - obj.dimensions.y/2, precision)
    obj_y_max = round(obj_global_bbox_center[1] + obj.dimensions.y/2, precision)

    obj_z_min = round(obj_global_bbox_center[2] - obj.dimensions.z/2, precision)
    obj_z_max = round(obj_global_bbox_center[2] + obj.dimensions.z/2, precision)

    if obj_x_max <= node_x_max and obj_y_max <= node_y_max and obj_z_max <= node_z_max:
        if obj_x_min >= node_x_min and obj_y_min >= node_y_min and obj_z_min >= node_z_min:
            return True

    return False

def calculate_meshIndices(colTreeNodes):
    print("Calculating colTreeNodes' meshIndices...")
    addedObjects = []

    for node in reversed(colTreeNodes):
        newMeshIndices = []
        for idx, obj in enumerate(bpy.data.collections['COL'].objects):
            if obj.type == 'MESH' and obj not in addedObjects:
                if inside_volume(obj, node, 4):
                    newMeshIndices.append(idx)
                    addedObjects.append(obj)
        node.meshIndices = newMeshIndices
        node.bObj["meshIndices"] = newMeshIndices
    
    failedMeshes = []
    for obj in bpy.data.collections['COL'].objects:
        if obj not in addedObjects:
            failedMeshes.append(obj)
            print("[!] Failed to find colTreeNode for mesh:", obj.name)
    if len(failedMeshes) > 0:
        print("[!]", len(failedMeshes), "meshes could not be placed in a node. Consider manually assigning these and exporting again (with automatic calculation disabled) or adjusting node sizes if you experience collision problems in-game.")
    else:
        print("[>] All meshes found appropriate nodes! :D")
"""
def getColMeshIndex(objToFind):
    colMeshObjs = [obj for obj in objectsInCollectionInOrder("COL") if obj.type == 'MESH']
    for i, obj in enumerate(colMeshObjs):
        if obj == objToFind:
            return i
    return -1

# Basic generation algorithm:
# 1. Find unassigned mesh with the largest volume and create a volume for it.
# 2. Look for any other meshes that are also in aforementioned volume and assign to it.
# 3. If no more meshes can be assigned to the volume, return to step 1 until all meshes are assigned to a volume.

def generate_colTreeNodes():
    # Create and setup collection
    colCollection = bpy.data.collections.get("COL")
    custom_colTreeNodesCollection = bpy.data.collections.get("custom_col_colTreeNodes")
    if not custom_colTreeNodesCollection:
        custom_colTreeNodesCollection = bpy.data.collections.new("custom_col_colTreeNodes")
        colCollection.children.link(custom_colTreeNodesCollection)
        bpy.context.view_layer.active_layer_collection.children["COL"].children["custom_col_colTreeNodes"].hide_viewport = True
    for obj in [o for o in custom_colTreeNodesCollection.objects]:
        bpy.data.objects.remove(obj)

    # Create Root Node
    rootNode = bpy.data.objects.new("custom_Root_col", None)
    rootNode.hide_viewport = True
    custom_colTreeNodesCollection.objects.link(rootNode)
    rootNode.rotation_euler = (math.radians(90),0,0)

    unassigned_objs = [obj for obj in objectsInCollectionInOrder("COL") if obj.type == 'MESH']

    nodes = []
    while len(unassigned_objs) > 0:
        largest_obj = max(unassigned_objs, key=lambda x: getObjectVolume(x))
        unassigned_objs.remove(largest_obj)

        sub_objects = []
        for obj in unassigned_objs:
            if len(sub_objects) >= 15:    # Do not put more than 15 + 1 meshes in a volume
                break

            if volumeInsideOther(getObjectCenter(obj), obj.dimensions, getObjectCenter(largest_obj), largest_obj.dimensions):
                sub_objects.append(obj)

        for obj in sub_objects:
            unassigned_objs.remove(obj)

        # Create Empty
        colEmptyName = str(len(nodes)) + "_col"
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

        colEmpty.name = str(node.index) + "_" + str(node.left) + "_" + str(node.right) + "_col"

        nodes.append(node)

    print("Number of leaf nodes generated...", len(nodes))

    # Start connecting leaf nodes up into tree
    deepest_nodes = nodes
    max_dist_modifier = 1
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
            
            if closest_dist > max_dist_modifier * 10:
                continue

            # deepest_Nodes[i] and closest_node should be joined
            colEmptyName = str(len(nodes)) + "_col"
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

            colEmpty.name = str(node.index) + "_" + str(node.left) + "_" + str(node.right) + "_col"

            joined_nodes.append(deepest_nodes_sorted[i])
            joined_nodes.append(closest_node)
            nodes.append(node)
            new_nodes.append(node)


        unassigned_nodes= []
        for node in deepest_nodes_sorted:
            if node not in joined_nodes:
                unassigned_nodes.append(node)
                
        if deepest_nodes == new_nodes + unassigned_nodes:
            print("No nodes could be grouped, increasing max distance modifier...")
            max_dist_modifier = max_dist_modifier + 1
        else:
            print(len(unassigned_nodes), "nodes ascending level...")

        deepest_nodes = new_nodes + unassigned_nodes
        #print("Number of nodes generated for this level...", len(deepest_nodes))

    # Let's fix the ordering of the tree in Blender
    indexOffset = len(nodes) - 1
    for node in nodes:
        node.index = indexOffset - node.index
        if (node.left != -1):
            node.left = indexOffset - node.left
        if (node.left != -1):
            node.right = indexOffset - node.right
        node.bObj.name = str(node.index) + "_" + str(node.left) + "_" + str(node.right) + "_col"

    # Clean up Blender's duplicate nam
    for node in nodes:
        splitName = node.bObj.name.split(".")
        node.bObj.name = splitName[0]


    nodes = sorted(nodes, key=lambda x: x.index) 
    return nodes

class ColTreeNode:
    def __init__(self, bObj):
        self.bObj = bObj

        self.position = bObj.location
        self.scale = bObj.scale

        split_name = bObj.name.split("_")
        
        self.left = int(split_name[1])
        self.right = int(split_name[2])

        self.offsetMeshIndices = 0
        self.meshIndexCount = 0
        self.meshIndices = []

        self.structSize = 12 + 12 + (4*4)


class ColTreeNodes:
    def __init__(self, colTreeNodesStartOffset, generateColTree):
        self.structSize = 0

        self.colTreeNodes = []
        for obj in objectsInCollectionInOrder("col_colTreeNodes"):
            if "Root" not in obj.name:
                newColTreeNode = ColTreeNode(obj)
                self.colTreeNodes.append(newColTreeNode)
                self.structSize += newColTreeNode.structSize
        if generateColTree:
            self.colTreeNodes = generate_colTreeNodes()
            self.structSize = len(self.colTreeNodes) * self.colTreeNodes[0].structSize
            #calculate_meshIndices(self.colTreeNodes)
        update_offsetMeshIndices(self.colTreeNodes, colTreeNodesStartOffset + self.structSize)

from ...util import *

def write_col_colTreeNodes(col_file, data):
    col_file.seek(data.offsetColTreeNodes)

    for colTreeNode in data.colTreeNodes.colTreeNodes:
        for val in colTreeNode.position:
            write_float(col_file, val)
        for val in colTreeNode.scale:
            write_float(col_file, val)

        write_Int32(col_file, colTreeNode.left)
        write_Int32(col_file, colTreeNode.right)

        write_uInt32(col_file, colTreeNode.offsetMeshIndices)
        write_uInt32(col_file, colTreeNode.meshIndexCount)

    for colTreeNode in data.colTreeNodes.colTreeNodes:
        if len(colTreeNode.meshIndices) > 0:
            for meshIndex in colTreeNode.meshIndices:
                write_uInt32(col_file, meshIndex)