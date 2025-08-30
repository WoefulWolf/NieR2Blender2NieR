from ....utils.util import getUsedMaterials, getAllMeshNamesInOrder, getMeshName

class c_lod(object):
    def __init__(self, lodsStart, batches, lod_level):
        def get_lodBatches(self, batches, lod_level):
            lodBatches = []
            for batch in batches.batches:
                if batch.blenderObj.mesh_group_props.lod_level == lod_level:
                    lodBatches.append(batch)
            return lodBatches

        def get_batchInfos(self, batches):
            meshes = getAllMeshNamesInOrder('WMB')

            batchesInfos = []
            for batch in batches:                                     
                vertexGroupIndex = batch.vertexGroupIndex

                mesh_name = getMeshName(batch.blenderObj)
                meshIndex = meshes.index(mesh_name)

                for slot in batch.blenderObj.material_slots:
                    material = slot.material
                for mat_index, mat in enumerate(getUsedMaterials()):
                    if mat == material:
                        materialIndex = mat_index
                        break
                
                colTreeNodeIndex = batch.blenderObj['colTreeNodeIndex'] if 'colTreeNodeIndex' in batch.blenderObj else -1
                meshMatPairIndex = meshIndex
                unknownWorldDataIndex = batch.blenderObj['unknownWorldDataIndex'] if 'unknownWorldDataIndex' in batch.blenderObj else -1
                batchInfo = [vertexGroupIndex, meshIndex, materialIndex, colTreeNodeIndex, meshMatPairIndex, unknownWorldDataIndex]
                batchesInfos.append(batchInfo)
            return batchesInfos

        self.lodBatches = get_lodBatches(self, batches, lod_level)
        self.numBatchInfos = len(self.lodBatches)
        self.offsetName = lodsStart + self.numBatchInfos * 24
        self.lodLevel = lod_level
        self.batchStart = batches.batches.index(self.lodBatches[0])
        self.name = self.lodBatches[0].blenderObj.mesh_group_props.lod_name
        self.offsetBatchInfos = self.offsetName - 24 * self.numBatchInfos
        self.batchInfos = get_batchInfos(self, self.lodBatches)
        self.lod_StructSize = len(self.name) + 1 + len(self.batchInfos) * 24