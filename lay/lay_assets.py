from unicodedata import name
import bpy
from ..util import *

class Asset:
    def __init__(self, bObj):
        self.name = bObj.name
        
        self.pos = bObj.location
        self.rot = bObj.rotation_euler
        self.scale = bObj.scale

        self.unknownIndex = bObj["unknownIndex"]

        self.instances = getInstances(bObj)
        self.instanceCount = len(self.instances)

class Instance:
    def __init__(self, bObj):
        self.pos = bObj.location
        self.rot = bObj.rotation_euler
        self.scale = bObj.scale

class Assets:
    def __init__(self):
        self.assets = []
        for obj in bpy.data.objects['Root_layAsset'].children:
            self.assets.append(Asset(obj))
        self.structSize = len(self.assets) * 112

        self.totalInstancesCount = 0
        for asset in self.assets:
            self.totalInstancesCount += asset.instanceCount
        
def getInstances(assetObj):
    instances = []
    for obj in bpy.data.objects['Root_layInstance'].children:
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
        write_uInt32(lay_file, 2399141888)
        write_uInt32(lay_file, 32768)
        write_uInt32(lay_file, 0)
        write_uInt32(lay_file, 536870912)
        write_uInt32(lay_file, 0)
        write_uInt32(lay_file, 0)
        write_uInt32(lay_file, 0)
        write_uInt32(lay_file, 0)

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