import bpy
from mathutils import Vector

from ....utils.util import getUsedMaterials, allObjectsInCollectionInOrder, getBoneIndexByName

def getObjectCenter(obj):
    obj_local_bbox_center = 0.125 * sum((Vector(b) for b in obj.bound_box), Vector())
    #obj_global_bbox_center = obj.matrix_world @ obj_local_bbox_center
    return obj_local_bbox_center

def getMeshBoundingBox(meshObj):
    xVals = []
    yVals = []
    zVals = []

    meshName = meshObj.name.split("-")[1]
    for obj in (x for x in bpy.data.collections['WMB'].all_objects if x.type == "MESH"):
        if obj.name.split("-")[1] == meshName:
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
    def __init__(self, offsetMeshes, numMeshes, obj):

        def get_BoundingBox(self, obj):
            midPoint, scale = getMeshBoundingBox(obj)
            return midPoint + scale

        def get_materials(self, obj):
            materials = []
            obj_mesh_name = obj.name.split('-')[1]
            for mesh in (x for x in allObjectsInCollectionInOrder('WMB') if x.type == "MESH"):
                if mesh.name.split('-')[1] == obj_mesh_name:
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
            obj_mesh_name = obj.name.split('-')[1]
            for mesh in (x for x in allObjectsInCollectionInOrder('WMB') if x.type == "MESH"):
                if mesh.name.split('-')[1] == obj_mesh_name:
                    for vertexGroup in mesh.vertex_groups:
                        boneName = getBoneIndexByName("WMB", vertexGroup.name)
                        if boneName not in bones:
                            if boneName:
                                bones.append(boneName)
                                numBones += 1
            if len(bones) == 0:
                bones.append(0)

            bones.sort()
            return bones, numBones
      
        self.bones, self.numBones = get_bones(self, obj)

        self.nameOffset = offsetMeshes + numMeshes * 44

        self.boundingBox = get_BoundingBox(self, obj)

        self.name = obj.name.split('-')[1]

        self.offsetMaterials = self.nameOffset + len(self.name) + 1

        self.materials =  get_materials(self, obj)

        self.numMaterials = len(self.materials)

        if self.numBones > 0:
            self.offsetBones = self.offsetMaterials + 2*self.numMaterials
        else:
            self.offsetBones = 0     

        def get_mesh_StructSize(self):
            mesh_StructSize = 0
            mesh_StructSize += 4 + 24 + 4 + 4 + 4 + 4
            mesh_StructSize += len(self.name) + 1
            mesh_StructSize += len(self.materials) * 2
            mesh_StructSize += len(self.bones) * 2
            return mesh_StructSize

        self.mesh_StructSize = get_mesh_StructSize(self)

        self.blenderObj = obj