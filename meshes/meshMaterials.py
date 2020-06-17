import bpy, bmesh, math

class c_meshMaterials(object):
    def __init__(self, meshes, lods):
        def get_meshMaterials(self):
            meshMaterials = []
            for mesh_indx, mesh in enumerate(meshes.meshes):
                for obj in bpy.data.objects:
                    if obj.type == 'MESH':
                        if obj['meshGroupIndex'] == mesh_indx:
                            blenderObj = obj
                            for slot in blenderObj.material_slots:
                                material = slot.material
                                for mat_indx, mat in enumerate(bpy.data.materials):
                                    if mat == material:
                                        struct = [mesh_indx, mat_indx]
                                        if struct not in meshMaterials:
                                            meshMaterials.append(struct)
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