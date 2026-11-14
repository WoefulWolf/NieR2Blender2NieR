import bpy

from ....utils.util import getUsedMaterials, allObjectsInCollectionInOrder, getBoneIndices, getMeshName, getAllMeshObjectsInOrder, getGameBoundingBox

def getMeshGroupBones(obj):
    bones = []
    boneIndices = getBoneIndices("WMB")
    obj_mesh_name = getMeshName(obj)
    for mesh in getAllMeshObjectsInOrder('WMB'):
        if getMeshName(mesh) == obj_mesh_name:
            for vertexGroup in mesh.vertex_groups:
                boneName = boneIndices.get(vertexGroup.name)
                if boneName is not None and boneName not in bones:
                    bones.append(boneName)

    if len(bones) == 0:
        rigidBones = [mesh['rigidBone'] for mesh in getAllMeshObjectsInOrder('WMB') if getMeshName(mesh) == obj_mesh_name and mesh.get('rigidBone') in boneIndices]
        if rigidBones:
            bones.append(boneIndices[rigidBones[0]])

    if len(bones) == 0:
        for armature in bpy.data.collections['WMB'].all_objects:
            if armature.type == 'ARMATURE' and len(armature.data.bones) > 0:
                bones.append(0)
                break

    bones.sort()
    return bones

def getMeshBoundingBox(meshObj):
    meshName = getMeshName(meshObj)
    return getGameBoundingBox([obj for obj in getAllMeshObjectsInOrder('WMB') if getMeshName(obj) == meshName])

class c_mesh(object):
    def __init__(self, offsetMeshes, numMeshes, obj):

        def get_BoundingBox(self, obj):
            midPoint, scale = getMeshBoundingBox(obj)
            return midPoint + scale

        def get_materials(self, obj):
            materials = []
            obj_mesh_name = getMeshName(obj)
            for mesh in getAllMeshObjectsInOrder('WMB'):
                if getMeshName(mesh) == obj_mesh_name:
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
            bones = getMeshGroupBones(obj)
            return bones, len(bones)
      
        self.bones, self.numBones = get_bones(self, obj)

        self.nameOffset = offsetMeshes + numMeshes * 44

        self.boundingBox = get_BoundingBox(self, obj)

        self.name = getMeshName(obj)

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