import sys
import json
import traceback
import random

verbose = False

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

def checkConsecutive(l):
    return sorted(l) == list(range(min(l), max(l)+1))

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
            shaders[shaderName]["Variables"] = list(variables.keys())
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

def find_diffs(shaderName, instances):
    dump = open("./dump.json", "a+")
    dump.seek(0)    
    found_shaders = json.load(dump)
    found_params = found_shaders[shaderName]["Parameters"]
    
    changedIndices = []
    for instance in instances:
        for otherInstance in instances:
            if instance == otherInstance:
                continue

            variables = instance[0]
            otherVariables = otherInstance[0]

            paramGroups = instance[1]
            otherParamGroups = otherInstance[1]

            if (len(paramGroups) != len(otherParamGroups)) or (len(variables) != len(otherVariables)):
                continue

            if (len(paramGroups) != 2 or len(otherParamGroups) != 2):
                continue

            diffs = []
            for index, (first, second) in enumerate(zip(paramGroups[0], otherParamGroups[0])):
                if first != second:
                    if (found_params[index] != "Unknown"):
                        continue
                    #print(index, first, second)
                    diffs.append(index)

            diffs2 = []
            for i in range(len(paramGroups[1])):
                if (paramGroups[1][i] != otherParamGroups[1][i]):
                    diffs2.append(i)

            varDiffs = []
            for index, (first, second) in enumerate(zip(variables.values(), otherVariables.values())):
                if first != second:
                    if "g_" not in list(variables.keys())[index]:
                        print(list(variables.keys())[index])
                        continue
                    #print(index, list(variables.keys())[index], first, second)
                    varDiffs.append(index)


            if (len(diffs) > 0):
                if verbose:
                    print('#'*25)
                    print(len(diffs), "x Instance differences:")
                    for diff in diffs:
                        print(diff, ":", paramGroups[0][diff], otherParamGroups[0][diff])

                    if (len(varDiffs) > 0):
                        print('#'*25)
                        print(len(varDiffs), "x Variable differences:")
                        for diff in varDiffs:
                            print(diff, ":", list(variables.keys())[diff])

                if (len(diffs) == len(varDiffs)):
                    if checkConsecutive(diffs) and checkConsecutive(varDiffs):
                        print("Found differences in shader", shaderName, "for variable indices", varDiffs, "- parameter indices", diffs)
                        for i, diff in enumerate(diffs):
                            found_params[diff] = list(variables.keys())[varDiffs[i]]
                            if (diff in changedIndices):
                                print("THE SAME INDEX WAS CHANGED TWICE! MAJOR PROBLEM!")
                                return
                            else:
                                changedIndices.append(diff)
            """
            if (len(diffs) == 1 and len(varDiffs) == 1 and len(diffs2) == 0):
                print("Found difference in shader", shaderName, "for variable", varDiffs[0], "index", diffs[0])
                found_params[diffs[0]] = varDiffs[0]
                if (diffs[0] in changedIndices):
                    print("THE SAME INDEX WAS CHANGED TWICE! MAJOR PROBLEM!")
                    return
                else:
                    changedIndices.append(diffs[0])
            """

    dump.truncate(0)
    json.dump(found_shaders, dump, indent= 4)
    dump.close()
    return changedIndices

def find_common_param_neighbours(shader_names):
    dump = open("./dump.json", "a+")
    dump.seek(0)    
    found_shaders = json.load(dump)

    params_before = {}
    params_after = {}

    inconsisstent_params = [] 

    changes_found = 0
    for shader_name in shader_names:
        found_params = found_shaders[shader_name]["Parameters"]
        for i in range(len(found_params)):
            if found_params[i] == "Unknown":
                continue
            if i != 0 and found_params[i-1] != "Unknown":
                if (found_params[i] in params_before) and params_before[found_params[i]] != found_params[i-1]:
                    inconsisstent_params.append(found_params[i])
                else:
                    params_before[found_params[i]] = found_params[i-1]
            if i+1 != len(found_params) and found_params[i+1] != "Unknown":
                if (found_params[i] in params_after) and params_after[found_params[i]] != found_params[i+1]:
                    inconsisstent_params.append(found_params[i])
                else:
                    params_after[found_params[i]] = found_params[i+1]

    for param in found_params:
        if (param != "Unknown") and (param not in inconsisstent_params):
            if param in params_before:
                for shader_name in shader_names:
                    if param not in found_shaders[shader_name]["Parameters"] or params_before[param] not in found_shaders[shader_name]["Variables"]:
                        continue
                    param_index = found_shaders[shader_name]["Parameters"].index(param)
                    if found_shaders[shader_name]["Parameters"][param_index - 1] == "Unknown":
                        found_shaders[shader_name]["Parameters"][param_index - 1] = params_before[param]
                        print("Identified common neighbour", params_before[param], "before", param, "in shader", shader_name)
                        changes_found += 1

            if param in params_after:
                for shader_name in shader_names:
                    if param not in found_shaders[shader_name]["Parameters"] or params_after[param] not in found_shaders[shader_name]["Variables"]:
                        continue
                    param_index = found_shaders[shader_name]["Parameters"].index(param)
                    if found_shaders[shader_name]["Parameters"][param_index + 1] == "Unknown":
                        found_shaders[shader_name]["Parameters"][param_index + 1] = params_after[param]
                        print("Identified common neighbour", params_after[param], "after", param, "in shader", shader_name)
                        changes_found += 1
    dump.truncate(0)
    json.dump(found_shaders, dump, indent= 4)
    dump.close()
    return changes_found

if __name__ == "__main__":
    matFiles = sys.argv[1::]
    #random.shuffle(matFiles)
    try:
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
            for name, instances in global_shaders.items():
                print("Checking shader:", name)
                totalChanges += len(find_diffs(name, instances))
            totalChanges += find_common_param_neighbours(list(global_shaders.keys()))
            print("Found", totalChanges, "new parameters.")
        input("Press Enter to Exit")
    except Exception as e:
        traceback.print_exc()
        print(e)
        input("ERROR! Press Enter to Exit")