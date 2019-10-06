import bpy, bmesh, math, mathutils

class c_material(object):
    def __init__(self, offsetMaterial, material):
        self.offsetMaterial = offsetMaterial
        self.b_material = material

        def get_textures(self, material, offsetTextures):
            offset = offsetTextures
            numTextures = 0
            textures = []
            for key, value in material.items():
                if (isinstance(value, str)) and (key.find('g_') != -1):
                    numTextures += 1

            offsetName = offset + numTextures * 8


            for key, value in material.items():
                if (isinstance(value, str)) and (key.find('g_') != -1):
                    texture = value
                    name = key

                    offset += 4 + 4 + len(key)
                    textures.append([offsetName, texture, name])
                    offsetName += len(name) + 1
            return textures

        def get_textures_StructSize(self, textures):
            textures_StructSize = 0
            for texture in textures:
                textures_StructSize += 8
                textures_StructSize += len(texture[2]) + 1
            return textures_StructSize

        def get_numParameterGroups(self, material):
            numParameterGroups = 0
            parameterGroups = []

            def Check(char):
                try: 
                    int(char)
                    return True
                except ValueError:
                    return False

            for key, value in material.items():
                if Check(key[0]):
                    if not key[0] in parameterGroups:
                        numParameterGroups += 1
                        parameterGroups.append(key[0])

            return numParameterGroups

        def get_parameterGroups(self, material, offsetParameterGroups, numParameterGroups):
            parameterGroups = []
            offsetParameters = offsetParameterGroups + numParameterGroups * 12

            for i in range(numParameterGroups):
                index = i

                if index == 1:
                    index = -1

                parameters = []
                for key, value in material.items():
                    if key[0] == str(i):
                        parameters.append(value)
                        
                numParameters = len(parameters)

                parameterGroups.append([index, offsetParameters, numParameters, parameters])

                offsetParameters += numParameters * 4

            return parameterGroups

        def get_parameterGroups_StructSize(self, parameterGroups):
            parameterGroups_StructSize = 0
            for parameterGroup in parameterGroups:
                parameterGroups_StructSize += 12 + parameterGroup[2] * 4
            return parameterGroups_StructSize

        def get_variables(self, material, offsetVariables):
            numVariables = 0
            for key, val in material.items():
                if (isinstance(val, float)) and (key[0] not in ('0', '1')):
                    numVariables += 1
            
            variables = []
            offset = offsetVariables + numVariables * 8
            for key, val in material.items():
                if (isinstance(val, float)) and (key[0] not in ('0', '1')):
                    offsetName = offset
                    value = val
                    name = key
                    variables.append([offsetName, value, name])
                    offset += len(name) + 1
            return variables

        def get_variables_StructSize(self, variables):
            variables_StructSize = 0
            for variable in variables:
                variables_StructSize += 8
                variables_StructSize += len(variable[2])
            return variables_StructSize

        self.unknown0 = [2016, 7, 5, 15]            # This is probably always the same as far as I know?

        self.offsetName = self.offsetMaterial + 48

        self.offsetShaderName = self.offsetName + len(self.b_material.name) + 1

        self.offsetTechniqueName = self.offsetShaderName + len(self.b_material['Shader_Name']) + 1

        self.unknown1 = 1                           # This proabably also the same mostly

        self.offsetTextures = self.offsetTechniqueName + len(self.b_material['Technique_Name']) + 1

        self.textures = get_textures(self, self.b_material, self.offsetTextures)

        self.numTextures = len(self.textures)

        self.offsetParameterGroups = self.offsetTextures + get_textures_StructSize(self, self.textures)

        self.numParameterGroups = get_numParameterGroups(self, self.b_material)  

        self.parameterGroups = get_parameterGroups(self, self.b_material, self.offsetParameterGroups, self.numParameterGroups)

        self.offsetVariables = self.offsetParameterGroups + get_parameterGroups_StructSize(self, self.parameterGroups)

        self.variables = get_variables(self, self.b_material, self.offsetVariables)

        self.numVariables = len(self.variables)

        self.name = self.b_material.name

        self.shaderName = self.b_material['Shader_Name']

        self.techniqueName = self.b_material['Technique_Name']

        self.material_StructSize = self.offsetVariables + get_variables_StructSize(self, self.variables) - self.offsetMaterial