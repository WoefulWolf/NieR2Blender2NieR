import bpy

from .shader_Wtr00_XXXXX import water


def wtr02_xxxxx(material: bpy.types.Material, material_array, texture_dir: str):
    return water(material, texture_dir, False)
