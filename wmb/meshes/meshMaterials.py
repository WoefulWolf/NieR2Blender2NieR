import bpy, bmesh, math
from ...util import getUsedMaterials

class c_meshMaterials(object):
    def __init__(self, meshes, lods):
        def get_meshMaterials(self):
            meshMaterials = []
            for mesh_indx, mesh in enumerate(meshes.meshes):
                blenderObj = mesh.blenderObj
                for slot in blenderObj.material_slots:
                    material = slot.material
                    for mat_indx, mat in enumerate(getUsedMaterials()):
                        if mat == material:
                            struct = [mesh_indx, mat_indx]
                            if struct not in meshMaterials:
                                meshMaterials.append(struct)
                                break
            return meshMaterials

        self.meshMaterials = get_meshMaterials(self)
        self.meshMaterials_StructSize = len(self.meshMaterials) * 8
        
        # Update LODS meshMatPairs
        for lod in lods.lods:
            for batchInfo in lod.batchInfos:
                for meshMat_indx, meshMaterial in enumerate(self.meshMaterials):
                    if meshMaterial[0] == batchInfo[1] and meshMaterial[1] == batchInfo[2]:
                        batchInfo[4] = meshMat_indx
                        break