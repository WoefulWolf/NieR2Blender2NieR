import bpy, bmesh, math

from blender2nier.batches.batch import c_batch

class c_batches(object):
    def __init__(self, boneMap):
        
        def get_batches(self):
            batches = []
            boneSetIndex = -1

            for obj in bpy.data.objects:
                if obj.type == 'MESH':
                    obj_name = obj.name.split('-')
                    obj_vertexGroupIndex = int(obj_name[-1])

                    if boneMap is not None:
                        for index, bone in enumerate(boneMap.boneMap):
                            if len(obj.vertex_groups) > 0:
                                if bone == int(obj.vertex_groups[0].name[-1]):
                                    boneSetIndex = index


                    if len(batches) == 0:
                        batches.append(c_batch(obj, obj_vertexGroupIndex, 0, 0, boneSetIndex))
                    else:
                        batches.append(c_batch(obj, obj_vertexGroupIndex, batches[len(batches)-1].indexStart + batches[len(batches)-1].numIndexes, batches[len(batches)-1].numVertexes, boneSetIndex))


            return batches

        self.batches = get_batches(self)
        self.batches_StructSize =len(self.batches) * 28