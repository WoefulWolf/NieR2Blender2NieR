import math

import bpy
import numpy as np
from mathutils import Vector


def getObjectCenter(obj):
    obj_local_bbox_center = 0.125 * sum((Vector(b) for b in obj.bound_box), Vector())
    #obj_global_bbox_center = obj.matrix_world @ obj_local_bbox_center
    return obj_local_bbox_center

def getObjectVolume(obj):
    return np.prod(obj.dimensions)

def volumeInsideOther(volumeCenter, volumeScale, otherVolumeCenter, otherVolumeScale):
    xVals = [volumeCenter[0] - volumeScale[0]/2, volumeCenter[0] + volumeScale[0]/2]
    yVals = [volumeCenter[1] - volumeScale[1]/2, volumeCenter[1] + volumeScale[1]/2]
    zVals = [volumeCenter[2] - volumeScale[2]/2, volumeCenter[2] + volumeScale[2]/2]

    other_xVals = [otherVolumeCenter[0] - otherVolumeScale[0]/2, otherVolumeCenter[0] + otherVolumeScale[0]/2]
    other_yVals = [otherVolumeCenter[1] - otherVolumeScale[1]/2, otherVolumeCenter[1] + otherVolumeScale[1]/2]
    other_zVals = [otherVolumeCenter[2] - otherVolumeScale[2]/2, otherVolumeCenter[2] + otherVolumeScale[2]/2]

    if (max(xVals) <= max(other_xVals) and max(yVals) <= max(other_yVals) and max(zVals) <= max(other_zVals)):
        if (min(xVals) >= min(other_xVals) and min(yVals) >= min(other_yVals) and min(zVals) >= min(other_zVals)):
            return True
    return False

def getColMeshIndex(objToFind):
    colMeshObjs = [obj for obj in bpy.data.collections['WMB'].all_objects if obj.type == 'MESH']
    for i, obj in enumerate(colMeshObjs):
        if obj == objToFind:
            return i
    return -1

def getDistanceTo(pos, otherPos):
    return np.linalg.norm(otherPos - pos)

def getVolumeSurrounding(volumeCenter, volumeScale, otherVolumeCenter, otherVolumeScale):
    xVals = [volumeCenter[0] - volumeScale[0]/2, volumeCenter[0] + volumeScale[0]/2, otherVolumeCenter[0] - otherVolumeScale[0]/2, otherVolumeCenter[0] + otherVolumeScale[0]/2]
    yVals = [volumeCenter[1] - volumeScale[1]/2, volumeCenter[1] + volumeScale[1]/2, otherVolumeCenter[1] - otherVolumeScale[1]/2, otherVolumeCenter[1] + otherVolumeScale[1]/2]
    zVals = [volumeCenter[2] - volumeScale[2]/2, volumeCenter[2] + volumeScale[2]/2, otherVolumeCenter[2] - otherVolumeScale[2]/2, otherVolumeCenter[2] + otherVolumeScale[2]/2]

    minX = min(xVals)
    maxX = max(xVals)
    minY = min(yVals)
    maxY = max(yVals)
    minZ = min(zVals)
    maxZ = max(zVals)

    midPoint = [(minX + maxX)/2, (minY + maxY)/2, (minZ + maxZ)/2]
    scale = [maxX - midPoint[0], maxY - midPoint[1], maxZ - midPoint[2]]
    return midPoint, scale

# Basic generation algorithm:
# 1. Find unassigned mesh with largest volume and create a volume for it.
# 2. Look for any other meshes that are also in aforementioned volume and assign to it.
# 3. If no more meshes can be assigned to the volume, return to step 1 until all meshes are assigned to a volume.

class custom_ColTreeNode:
    def __init__(self):
        self.index = -1
        self.bObj = None

        self.position = [0, 0, 0]
        self.scale = [1, 1, 1]
        
        self.left = -1
        self.right = -1

        self.offsetMeshIndices = 0
        self.meshIndexCount = 0
        self.meshIndices = []

        self.structSize = 12 + 12 + (4*4)

    def getVolume(self):
        return np.prod(self.scale)

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

    # Lets fix the ordering of the tree in Blender
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