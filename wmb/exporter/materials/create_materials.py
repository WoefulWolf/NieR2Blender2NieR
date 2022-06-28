from .material import c_material
from ....utils.util import getUsedMaterials


class c_materials(object):
    def __init__(self, materialsStart):
        
        def get_materials(self):
            materials = []
            offsetMaterialName = materialsStart

            for mat in getUsedMaterials():
                offsetMaterialName += 48                        # Material Headers

            for mat in getUsedMaterials():
                print('[+] Generating Material', mat.name)
                material = c_material(offsetMaterialName, mat)
                materials.append(material)

                offsetMaterialName += material.materialNames_StructSize

            return materials
        
        def get_materials_StructSize(self, materials):
            materials_StructSize = 0
            for material in materials:
                materials_StructSize += 48 + material.materialNames_StructSize
            return materials_StructSize

        self.materials = get_materials(self)
        self.materials_StructSize = get_materials_StructSize(self, self.materials)