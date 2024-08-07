import math
import mathutils

from ...utils.ioUtils import write_float, write_string, write_uInt32, write_byte
from ...utils.util import *

class Asset:
    def __init__(self, bObj):
        self.name = bObj.name
        
        rotator = mathutils.Euler((math.radians(-90), 0, 0), 'XYZ')

        location = mathutils.Vector(bObj.location)
        location.rotate(rotator)

        rotation = mathutils.Euler(bObj.rotation_euler, 'XYZ')
        rotation.rotate(rotator)

        self.pos = location
        self.rot = rotation
        self.scale = [bObj.scale[0], bObj.scale[2], bObj.scale[1]]

        self.unknownIndex = bObj["unknownIndex"]
        self.null1 = bObj["null1"]

        self.instances = getInstances(bObj)
        self.instanceCount = len(self.instances)

class Instance:
    def __init__(self, bObj):
        rotator = mathutils.Euler((math.radians(-90), 0, 0), 'XYZ')

        location = mathutils.Vector(bObj.location)
        location.rotate(rotator)

        rotation = mathutils.Euler(bObj.rotation_euler, 'XYZ')
        rotation.rotate(rotator)

        self.pos = location
        self.rot = rotation
        self.scale = [bObj.scale[0], bObj.scale[2], bObj.scale[1]]

class Assets:
    def __init__(self):
        self.assets = []
        for obj in bpy.data.collections['lay_layAssets'].all_objects:
            self.assets.append(Asset(obj))
        self.structSize = len(self.assets) * 112

        self.totalInstancesCount = 0
        for asset in self.assets:
            self.totalInstancesCount += asset.instanceCount
        
def getInstances(assetObj):
    instances = []
    for obj in bpy.data.collections['lay_layInstances'].all_objects:
        name = obj.name.split("-")[0]
        if name == assetObj.name:
            instances.append(Instance(obj))
    return instances

def write_assets(lay_file, data):
    for asset in data.assets.assets:
        nameStart = lay_file.tell()
        write_string(lay_file, asset.name)
        lay_file.seek(nameStart + 32)

        for val in asset.pos:
            write_float(lay_file, val)
        for val in asset.rot:
            write_float(lay_file, val)
        for val in asset.scale:
            write_float(lay_file, val)

        write_uInt32(lay_file, 0)
        write_uInt32(lay_file, asset.unknownIndex)

        # Null stuff, no idea what they are
        for byte in asset.null1:
            write_byte(lay_file, byte)

        write_uInt32(lay_file, asset.instanceCount)

    print("[>] numAssets:", len(data.assets.assets))

def write_instances(lay_file, data):
    for asset in data.assets.assets:
        for instance in asset.instances:
            for val in instance.pos:
                write_float(lay_file, val)
            for val in instance.rot:
                write_float(lay_file, val)
            for val in instance.scale:
                write_float(lay_file, val)

    print("[>] numInstances:", data.assets.totalInstancesCount)