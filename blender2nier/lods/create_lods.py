import bpy, bmesh, math, mathutils
from blender2nier.lods.lods import c_lod

class c_lods(object):
    def __init__(self, lodsStart, batches):
        def get_lod_levels(batches):
            lod_levels = []
            for batch in batches.batches:
                level = batch.blenderObj['LOD_Level']
                if level not in lod_levels:
                    lod_levels.append(level)
            return lod_levels

        def get_lods(lodsStart, batches):
            lod_levels = get_lod_levels(batches)
            lods = []
            currentLodStart = lodsStart + len(lod_levels) * 20
            for lod_level in lod_levels:
                print('[+] Generating LOD', str(lod_level))
                lods.append(c_lod(currentLodStart, batches, lod_level))
                currentLodStart += lods[-1].lod_StructSize
            return lods

        def get_lodsStructSize(lods):
            lodsStructSize = len(lods) * 20
            for lod in lods:
                lodsStructSize += lod.lod_StructSize
            return lodsStructSize

        self.lods = get_lods(lodsStart, batches)
        self.lods_StructSize = get_lodsStructSize(self.lods)