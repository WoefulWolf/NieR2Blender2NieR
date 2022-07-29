import sys
import json
import traceback
import random

global_shaders = {}

def shared_chars(s1, s2):
    count = 0
    for i, char in enumerate(s1):
        if (i > len(s2) - 1):
            return count
        if (char == s2[i]):
            count += 1
    return count

def find_pattern_count(pattern, list):
    count = 0
    for i in range(len(list)-len(pattern)+1):
        if (list[i:i + len(pattern)] == pattern):
            count += 1
    return count

def extractMats(fp):
    file = open(fp)
    data = json.load(file)
    file.close()
    
    dump = open("./dump.json", "a+")
    dump.seek(0)    
    try:
        shaders = json.load(dump)
    except:
        shaders = {}

    for matName, mat in data.items():
        if ("Shader_Name" not in mat):
            break

        shaderName = mat["Shader_Name"]
        technique = mat["Technique_Name"]
        parameters  = mat["ParameterGroups"]
        variables = mat["Variables"]

        if technique != "Default":
            continue

        if len(parameters) == 0:
            continue

        if shaderName not in global_shaders:
            global_shaders[shaderName] = []
        global_shaders[shaderName].append([variables, parameters, matName])

        if shaderName not in shaders:
            shaders[shaderName] = {}
            #shaders[shaderName]["Variables"] = list(variables.keys())
            shaders[shaderName]["Parameters"] = ["Unknown"] * len(parameters[0])

        mappedParameters = ["Unknown"] * len(parameters[0])
        # Find singles
        varVals = list(variables.values())
        for name, value in variables.items():
            for i, param in enumerate(parameters[0]):
                if (value == param) and (parameters[0].count(value) == 1) and(varVals.count(value) == 1):
                    mappedParameters[i] = name
        """
        # Find vector2
        i = 0
        variablesList = list(variables.keys())
        valuesList = list(variables.values())
        for i in range(len(valuesList)-1):
            if (find_pattern_count(valuesList[i:i+2], parameters[0]) == 1 and find_pattern_count(valuesList[i:i+2], valuesList) == 1):
                sharedWithFirst = shared_chars(variablesList[i], variablesList[i+1])
                if (sharedWithFirst > 10):
                    for j in range(len(parameters[0])):
                        if (parameters[0][j] == valuesList[i] and parameters[0][j+1] == valuesList[i+1]):
                            mappedParameters[j] = variablesList[i]
                            mappedParameters[j+1] = variablesList[i+1]
                            break
        

        # Find vector3
        i = 0
        variablesList = list(variables.keys())
        valuesList = list(variables.values())
        for i in range(len(valuesList)-2):
            if (find_pattern_count(valuesList[i:i+3], parameters[0]) == 1 and find_pattern_count(valuesList[i:i+3], valuesList) == 1):
                sharedWithFirst = shared_chars(variablesList[i], variablesList[i+1])
                sharedWithSecond = shared_chars(variablesList[i], variablesList[i+2])
                if (sharedWithFirst > 10 and sharedWithSecond > 10 and sharedWithFirst == sharedWithSecond):
                    for j in range(len(parameters[0])):
                        if (parameters[0][j] == valuesList[i] and parameters[0][j+1] == valuesList[i+1] and parameters[0][j+2] == valuesList[i+2]):
                            mappedParameters[j] = variablesList[i]
                            mappedParameters[j+1] = variablesList[i+1]
                            mappedParameters[j+2] = variablesList[i+2]
                            break
        """
        for i, param in enumerate(mappedParameters):
            if (shaders[shaderName]["Parameters"][i] != "Unknown") or (param == "Unknown"):
                continue
            shaders[shaderName]["Parameters"][i] = param
            print("Found new", param, "match in material", matName, "for shader", shaderName, "index", i)

    dump.truncate(0)
    json.dump(shaders, dump, indent= 4)
    dump.close()

def find_diffs(shaderName, shaders):
    dump = open("./dump.json", "a+")
    dump.seek(0)    
    found_shaders = json.load(dump)
    found_params = found_shaders[shaderName]["Parameters"]
    
    changedIndices = []
    for instance in shaders:
        for otherInstance in shaders:
            if instance == otherInstance:
                continue

            if (len(instance[1]) != len(otherInstance[1])) or (len(instance[0]) != len(otherInstance[0])):
                continue

            if (len(instance[1]) != 2 or len(otherInstance[1]) != 2):
                continue

            diffs = []
            for i in range(len(instance[1][0])):
                if (instance[1][0][i] != otherInstance[1][0][i]):
                    if (found_params[i] == "Unknown"):
                        diffs.append(i)

            diffs2 = []
            for i in range(len(instance[1][1])):
                if (instance[1][1][i] != otherInstance[1][1][i]):
                    diffs2.append(i)

            varDiffs = []
            for key in instance[0].keys():
                if key not in found_params:
                    if (instance[0][key] != otherInstance[0][key]):
                        varDiffs.append(key)
            
            if (len(diffs) == 1 and len(varDiffs) == 1 and len(diffs2) == 0):
                print("Found difference in shader", shaderName, "for variable", varDiffs[0], "index", diffs[0])
                found_params[diffs[0]] = varDiffs[0]
                if (diffs[0] in changedIndices):
                    print("THE SAME INDEX WAS CHANGED TWICE! MAJOR PROBLEM!")
                    return
                else:
                    changedIndices.append(diffs[0])

    dump.truncate(0)
    json.dump(found_shaders, dump, indent= 4)
    dump.close()
    return changedIndices

if __name__ == "__main__":
    matFiles = sys.argv[1::]
    #random.shuffle(matFiles)
    print(matFiles)
    for matFile in matFiles:
        print(matFile)
        try:
            extractMats(matFile)
        except Exception as e:
            traceback.print_exc()
            break
    
    totalChanges = 1
    while totalChanges > 0:
        print("Starting diff finder pass...")
        totalChanges = 0
        for name, shaders in global_shaders.items():
            totalChanges += len(find_diffs(name, shaders))
        print("Diff finder found", totalChanges, "new parameters.")
    
    input("Press Enter to Exit")