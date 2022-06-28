from ....utils.util import *

def create_wmb_materials(wmb_file, data):
    wmb_file.seek(data.materials_Offset)

    for material in data.materials.materials:
        for val in material.unknown0:                           # unknown0
            write_uInt16(wmb_file, val)
        write_uInt32(wmb_file, material.offsetName)             # offsetName
        write_uInt32(wmb_file, material.offsetShaderName)       # offsetShaderName
        write_uInt32(wmb_file, material.offsetTechniqueName)    # offsetTechniqueName
        write_uInt32(wmb_file, material.unknown1)               # unknown1
        write_uInt32(wmb_file, material.offsetTextures)         # offsetTextures
        write_uInt32(wmb_file, material.numTextures)            # numTextures
        write_uInt32(wmb_file, material.offsetParameterGroups)  # offsetParameterGroups
        write_uInt32(wmb_file, material.numParameterGroups)     # numParameterGroups
        write_uInt32(wmb_file, material.offsetVariables)        # offsetVariables
        write_uInt32(wmb_file, material.numVariables)           # numVariables
    for material in data.materials.materials:
        write_string(wmb_file, material.name)                   # name
        write_string(wmb_file, material.shaderName)             # shaderName
        write_string(wmb_file, material.techniqueName)          # techniqueName
        for texture in material.textures:                       # [offsetName, texture, name]
            write_uInt32(wmb_file, texture[0])
            write_uInt32(wmb_file, int(texture[1], 16))
        for texture in material.textures:
            write_string(wmb_file, texture[2])
        for parameterGroup in material.parameterGroups:         # [index, offsetParameters, numParameters, parameters]
            write_Int32(wmb_file, parameterGroup[0])
            write_uInt32(wmb_file, parameterGroup[1])
            write_uInt32(wmb_file, parameterGroup[2])
        for parameterGroup in material.parameterGroups:
            for value in parameterGroup[3]:
                write_float(wmb_file, value)
        for variable in material.variables:                     # [offsetName, value, name]
            write_uInt32(wmb_file, variable[0])
            write_float(wmb_file, variable[1])
        for variable in material.variables:
            write_string(wmb_file, variable[2])
