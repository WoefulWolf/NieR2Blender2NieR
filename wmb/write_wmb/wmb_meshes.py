from ...util import *

def create_wmb_meshes(wmb_file, data):
    wmb_file.seek(data.meshes_Offset)

    for mesh in data.meshes.meshes:
        write_uInt32(wmb_file, mesh.nameOffset)             # nameOffset
        for val in mesh.boundingBox:                        # boundingBox [x, y, z, u, v, m]
            write_float(wmb_file, val)
        write_uInt32(wmb_file, mesh.offsetMaterials)        # offsetMaterials
        write_uInt32(wmb_file, mesh.numMaterials)           # numMaterials
        write_uInt32(wmb_file, mesh.offsetBones)            # offsetBones
        write_uInt32(wmb_file, mesh.numBones)               # numBones

    for mesh in data.meshes.meshes:
        write_string(wmb_file, mesh.name)                   # name
        for material in mesh.materials:
            write_uInt16(wmb_file, material)                # materials
        if mesh.numBones != 0:
            for bone in mesh.bones:
                write_uInt16(wmb_file, bone)                    # bones