from ...utils.ioUtils import read_uint32, to_uint


class WTA(object):
    def __init__(self, wta_fp):
        super(WTA, self).__init__()
        self.magicNumber = wta_fp.read(4)
        if self.magicNumber == b'WTB\x00':
            self.unknown04 = read_uint32(wta_fp)
            self.textureCount = read_uint32(wta_fp)
            self.textureOffsetArrayOffset = read_uint32(wta_fp)
            self.textureSizeArrayOffset = read_uint32(wta_fp)
            self.unknownArrayOffset1 = read_uint32(wta_fp)
            self.textureIdentifierArrayOffset = read_uint32(wta_fp)
            self.unknownArrayOffset2 = read_uint32(wta_fp)
            
            self.wtaTextureOffset = [0] * self.textureCount
            self.wtaTextureSize = [0] * self.textureCount
            self.wtaTextureIdentifier = [0] * self.textureCount
            self.unknownArray1 = [0] * self.textureCount
            self.unknownArray2 = []
            print(self.textureCount)
            for i in range(self.textureCount):
                wta_fp.seek(self.textureOffsetArrayOffset + i * 4)
                self.wtaTextureOffset[i] = read_uint32(wta_fp)
                wta_fp.seek(self.textureSizeArrayOffset + i * 4)
                self.wtaTextureSize[i] =  read_uint32(wta_fp) 
                wta_fp.seek(self.textureIdentifierArrayOffset + i * 4)
                self.wtaTextureIdentifier[i] = "%08x"%read_uint32(wta_fp)
                wta_fp.seek(self.unknownArrayOffset1 + i * 4)
                self.unknownArray1[i] = "%08x"%read_uint32(wta_fp)
                print()
                print("TEXTURE DATA YEAH BABY")
                print("Texture pointer:", hex(self.wtaTextureOffset[i]))
                print("Texture size:", hex(self.wtaTextureSize[i]))
                print("Texture identifier:", self.wtaTextureIdentifier[i])
                print("Un fucking known:", self.unknownArray1[i])
            wta_fp.seek(self.unknownArrayOffset2 )
            unknownval =  (wta_fp.read(4))
            while unknownval:
                self.unknownArray2.append(to_uint(unknownval))
                unknownval =  (wta_fp.read(4))
            self.pointer2 = hex(wta_fp.tell())    
    def getTextureByIndex(self, texture_index, texture_fp):
        texture_fp.seek(self.wtaTextureOffset[texture_index])
        texture = texture_fp.read(self.wtaTextureSize[texture_index])
        return texture

    def getTextureByIdentifier(self, textureIdentifier, texture_fp):
        for index in range(self.textureCount):
            if self.wtaTextureIdentifier[index] == textureIdentifier:
                return self.getTextureByIndex(index,texture_fp)
        return False