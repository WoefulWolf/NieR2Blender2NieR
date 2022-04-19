from ...util import *
import os
import sys
import struct

def create_wmb_unknownWorldData(wmb_file, data):
    wmb_file.seek(data.unknownWorldData_Offset)

    for unknownWorldData in data.unknownWorldData.unknownWorldData:                # 6 values
        for entry in unknownWorldData:                                  
            wmb_file.write(entry)