from blender2nier.util import *

def create_wmb_meshMaterials(wmb_file, data):
    wmb_file.seek(data.meshMaterials_Offset)

    for meshMaterial in data.meshMaterials.meshMaterials:                # [meshID, materialID]
        print(meshMaterial[0])
        print(meshMaterial[1])
        write_uInt32(wmb_file, meshMaterial[0])                          # meshID
        write_uInt32(wmb_file, meshMaterial[1])                          # materialID