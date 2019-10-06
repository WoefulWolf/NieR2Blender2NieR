import bpy, bmesh, math, mathutils

class c_lods(object):
    def __init__(self, lodsStart, batches):
        def get_batchInfos(self, batches):
            batchesInfos = []
            meshIndex = -1
            for batch in batches.batches:                                       # Bunch of stuff TODO here
                vertexGroupIndex = batch.vertexGroupIndex
                meshIndex += 1 
                materialIndex = 0
                colTreeNodeIndex = -1
                meshMatPairIndex = meshIndex
                indexToUnknown1 = -1
                batchInfo = [vertexGroupIndex, meshIndex, materialIndex, colTreeNodeIndex, meshMatPairIndex, indexToUnknown1]
                batchesInfos.append(batchInfo)
            return batchesInfos

        self.numBatchInfos = len(batches.batches)
        self.offsetName = lodsStart + 20 + self.numBatchInfos * 24
        self.lodLevel = 0
        self.batchStart = 0
        self.name = 'LOD0'
        self.offsetBatchInfos = self.offsetName - 24 * len(batches.batches)
        self.batchInfos = get_batchInfos(self, batches)
        self.lods_StructSize = 20 + len(self.name) + 1 + len(self.batchInfos) * 24