from .batch import c_batch
from ....utils.util import allObjectsInCollectionInOrder


class c_batches(object):
    def __init__(self, vertexGroupsCount):
        
        def get_batches(self):
            batches = []
            currentVertexGroup = -1

            for obj in (x for x in allObjectsInCollectionInOrder('WMB') if x.type == "MESH"):
                obj_name = obj.name.split('-')
                obj_vertexGroupIndex = int(obj_name[-1])
                print('[+] Generating Batch', obj.name)
                
                if obj_vertexGroupIndex != currentVertexGroup:      # Start of new vertex group
                    currentVertexGroup = obj_vertexGroupIndex
                    cur_indexStart = 0
                    cur_numVertexes = 0

                if 'boneSetIndex' in obj:
                    obj_boneSetIndex = obj['boneSetIndex']
                else:
                    obj_boneSetIndex = -1

                batches.append(c_batch(obj, obj_vertexGroupIndex, cur_indexStart, cur_numVertexes, obj_boneSetIndex))
                cur_indexStart += batches[len(batches)-1].numIndexes
                cur_numVertexes = batches[len(batches)-1].numVertexes

            return batches

        self.batches = get_batches(self)
        self.batches_StructSize = len(self.batches) * 28
