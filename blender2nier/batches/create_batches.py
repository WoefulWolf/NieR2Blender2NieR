import bpy, bmesh, math

from blender2nier.batches.batch import c_batch

class c_batches(object):
    def __init__(self):
        
        def get_batches(self):
            batches = []

            for obj in bpy.data.objects:
                if obj.type == 'MESH':
                    obj_name = obj.name.split('_')
                    obj_vertexGroupIndex = int(obj_name[-1])

                    if len(batches) == 0:
                        batches.append(c_batch(obj, obj_vertexGroupIndex, 0, 0))
                    else:
                        batches.append(c_batch(obj, obj_vertexGroupIndex, batches[len(batches)-1].indexStart + batches[len(batches)-1].numIndexes, batches[len(batches)-1].numVertexes))

            return batches

        self.batches = get_batches(self)
        self.batches_StructSize =len(self.batches) * 28