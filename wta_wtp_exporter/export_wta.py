import bpy
import os
from . import generate_wta_wtp_data
from .wta_wtp_utils import *

def main(context, export_filepath):
    wta_fp = open(export_filepath,'wb')

    # Assign data and check if valid
    identifiers_array, texture_paths_array, albedo_indexes = generate_wta_wtp_data.generate(context)
    if identifiers_array == None:
        return

    # Assign some shit
    unknown04 = 3
    textureCount = len(texture_paths_array)
    paddingAmount = ((textureCount + 7) // 8) * 8	#rounds up to the nearest 8th integer
    textureOffsetArrayOffset = 32
    textureSizeArrayOffset = textureOffsetArrayOffset + (paddingAmount * 4)
    unknownArrayOffset1 = textureSizeArrayOffset + (paddingAmount * 4)
    textureIdentifierArrayOffset = unknownArrayOffset1 + (paddingAmount * 4)
    unknownArrayOffset2 = textureIdentifierArrayOffset + (paddingAmount * 4)
    wtaTextureOffset = [0] * textureCount
    wtaTextureSize = [0] * textureCount
    wtaTextureIdentifier = [0] * textureCount
    unknownArray1 = [0] * textureCount
    unknownArray2 = []
    paddingAmountArray = []

    # Pad the DDS files
    #pad_dds_files(texture_paths_array)

    current_wtaTextureOffset = 0

    # Open every DDS texture
    for i in range(textureCount):
        dds_fp = open(texture_paths_array[i], 'rb')
        dds_paddedSize = os.stat(texture_paths_array[i]).st_size

        #checks dds dxt and cube map info
        dds_fp.seek(84)
        dxt = dds_fp.read(4)
        dds_fp.seek(112)
        cube = dds_fp.read(4)

        #finds how much padding bytes are added to a dds
        dds_padding = 0
        if i != len(texture_paths_array)-1:
            dds_fp.seek(dds_paddedSize-4)
            dds_padding = to_int(dds_fp.read(4))
        paddingAmountArray.append(dds_padding)

        #wtaTextureOffset
        if i+1 in range(len(wtaTextureSize)):
            """
            if dds_paddedSize < 12289:
                wtaTextureOffset[i+1] = wtaTextureOffset[i] + 12288
            elif dds_paddedSize < 176129:
                wtaTextureOffset[i+1] = wtaTextureOffset[i] + 176128
            elif dds_paddedSize < 352257:
                wtaTextureOffset[i+1] = wtaTextureOffset[i] + 352256
            elif dds_paddedSize < 528385:
                wtaTextureOffset[i+1] = wtaTextureOffset[i] + 528384
            elif dds_paddedSize < 700417:
                wtaTextureOffset[i+1] = wtaTextureOffset[i] + 700416
            elif dds_paddedSize < 2797569:
                wtaTextureOffset[i+1] = wtaTextureOffset[i] + 2797568
            else:
                wtaTextureOffset[i+1] = dds_paddedSize
            """
            wtaTextureOffset[i+1] = current_wtaTextureOffset + dds_paddedSize
        current_wtaTextureOffset += dds_paddedSize
        #wtaTextureSize
        wtaTextureSize[i] = dds_paddedSize# - dds_padding
        #wtaTextureIdentifier
        wtaTextureIdentifier[i] = identifiers_array[i]
        #unknownArray1
        if i in albedo_indexes:
            unknownArray1[i] = 637534240
        else:
            unknownArray1[i] = 570425376
        #unknownArray2
        if dxt == b'DXT1':
            unknownArray2.append(71)
            unknownArray2.append(3)
            if cube == b'\x00\xfe\x00\x00':
                unknownArray2.append(4)
            else:
                unknownArray2.append(0)
            unknownArray2.append(1)
            unknownArray2.append(0)
        if dxt == b'DXT3':
            unknownArray2.append(74)
            unknownArray2.append(3)
            if cube == b'\x00\xfe\x00\x00':
                unknownArray2.append(4)
            else:
                unknownArray2.append(0)
            unknownArray2.append(1)
            unknownArray2.append(0)
        if dxt == b'DXT5':
            unknownArray2.append(77)
            unknownArray2.append(3)
            if cube == b'\x00\xfe\x00\x00':
                unknownArray2.append(4)
            else:
                unknownArray2.append(0)
            unknownArray2.append(1)
            unknownArray2.append(0)
        dds_fp.close()

    # Write everything
    padding = b''
    for i in range(paddingAmount - textureCount):
        padding += b'\x00\x00\x00\x00'

    wta_fp.write(b'WTB\x00')
    wta_fp.write(to_bytes(unknown04))
    wta_fp.write(to_bytes(textureCount))
    wta_fp.write(to_bytes(textureOffsetArrayOffset))
    wta_fp.write(to_bytes(textureSizeArrayOffset))
    wta_fp.write(to_bytes(unknownArrayOffset1))
    wta_fp.write(to_bytes(textureIdentifierArrayOffset))
    wta_fp.write(to_bytes(unknownArrayOffset2))
    for i in range(textureCount):
        wta_fp.write(to_bytes(wtaTextureOffset[i]))
    wta_fp.write(padding)
    for i in range(textureCount):
        wta_fp.write(to_bytes(wtaTextureSize[i]))
    wta_fp.write(padding)
    for i in range(textureCount):
        wta_fp.write(to_bytes(unknownArray1[i]))
    wta_fp.write(padding)
    for i in range(textureCount):
        wta_fp.write(to_bytes(wtaTextureIdentifier[i]))
    wta_fp.write(padding)
    for i in range(textureCount):
        wta_fp.write(to_bytes(unknownArray2[(i*5)]))
        wta_fp.write(to_bytes(unknownArray2[(i*5)+1]))
        wta_fp.write(to_bytes(unknownArray2[(i*5)+2]))
        wta_fp.write(to_bytes(unknownArray2[(i*5)+3]))
        wta_fp.write(to_bytes(unknownArray2[(i*5)+4]))
    wta_fp.write(padding)

    wta_fp.close()
    print('WTA Export Complete. :]')