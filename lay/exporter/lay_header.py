from ...utils.util import *

def write_lay_header(lay_file, data):
    for char in 'LAY\x00':                                         # id
        write_char(lay_file, char)

    write_float(lay_file, 2.01)

    print("[>] offsetModelEntries:", data.offsetModelEntries)
    write_uInt32(lay_file, data.offsetModelEntries)
    write_uInt32(lay_file, len(data.modelEntries.modelEntries))

    print("[>] offsetAssets:", data.offsetAssets)
    write_uInt32(lay_file, data.offsetAssets)
    write_uInt32(lay_file, len(data.assets.assets))

    print("[>] offsetInstances:", data.offsetInstances)
    write_uInt32(lay_file, data.offsetInstances)
    write_uInt32(lay_file, data.instancesCount)