from ....utils.util import getUsedMaterials
from ....utils.util import allObjectsInCollectionInOrder

class c_meshMaterials(object):
    def __init__(self):
        def get_meshMaterials(self):
            meshMaterials = []
            meshNames = []

            for obj in (x for x in allObjectsInCollectionInOrder('WMB') if x.type == "MESH"):
                obj_name = obj.name.split('-')[1]
                if obj_name not in meshNames:
                    meshNames.append(obj_name)

            for obj in (x for x in allObjectsInCollectionInOrder('WMB') if x.type == "MESH"):
                obj_name = obj.name.split('-')[1]

                mesh_index = meshNames.index(obj_name)
                
                for slot in obj.material_slots:
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
        
    def updateLods(self, lods):
        # Update LODS meshMatPairs
        for lod in lods.lods:
            for batchInfo in lod.batchInfos:
                for meshMat_index, meshMaterial in enumerate(self.meshMaterials):
                    if meshMaterial[0] == batchInfo[1] and meshMaterial[1] == batchInfo[2]:
                        batchInfo[4] = meshMat_index
                        break