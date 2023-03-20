import io
import struct

class Alignment:
    @staticmethod
    def align(value, alignment):
        return ((value + alignment - 1) // alignment) * alignment

class Endianness:
    def get_uint(self):
        return 'I' if self.big else 'i'

    def get_float(self):
        return 'f' if self.big else 'f'

    def get_short(self):
        return 'H' if self.big else 'h'

class SCRFile(Alignment, Endianness):
    ALIGNMENTS = {
        'wmb': 0x20,
        'wtb': 0x1000,
    }
    
    def read_uint32(file):
        return struct.unpack("<I", file.read(4))[0]
    # Or just import the read/write functions from, uh, wherever it is in the tool. .../utils/util.py?

    @staticmethod
    def is_big(file):
        file.seek(0)
        id_value = file.read(4)
        if id_value != b"SCR\0":
            raise ValueError(f"Invalid id {id_value}!")

        big = SCRFile.read_uint32(file)
        file.seek(0)
        small = SCRFile.read_uint32(file)
        if not (big ^ small):
            raise Exception("Invalid data!")
        return big > small

    @staticmethod
    def is_bayo2(file):
        file.seek(0)
        id = file.read(4)
        if id != b"SCR\0":
            raise Exception(f"Invalid id {id}!")
        a, b = struct.unpack("HH", file.read(4))
        file.seek(0)
        return a > 0 and b > 0

    @staticmethod
    def load(file):
        if isinstance(file, str):
            with open(file, "rb") as f:
                return SCRFile.load(f)

        if SCRFile.is_bayo2(file):
            raise Exception("This is a Bayonetta 2 SCR file. Please use SCR2File class.")
        else:
            return SCRFile(file)

    def __init__(self, file=None, big=False):
        self.big = big
        if file:
            if isinstance(file, str):
                with open(file, "rb") as f:
                    self.__init__(f)
                return

            self.big = SCRFile.is_big(file)

            file.seek(0)
            uint = self.get_uint()
            flt = self.get_float()
            sh = self.get_short()

            self.id = file.read(4)
            if self.id != b"SCR\0":
                raise Exception(f"Invalid id {self.id}!")

            self.num_models = SCRFile.read_uint32(file)
            self.offset_texture = SCRFile.read_uint32(file)
            self.unknown = file.read(4)

            self.models_metadata = []
            self.offsets_models = []
            self.sizes_models = []

            for _ in range(self.num_models):
                pos = file.tell()
                name = file.read(16)
                offset = SCRFile.read_uint32(file)
                transform = struct.unpack(f"{flt * 9}", file.read(4 * 9))
                data = file.read(42 * 2)
                if len(data) != 84:
                    raise Exception(f"Expected 84 bytes, but received {len(data)} bytes.")
                u_a = struct.unpack(f"{sh * 42}", data)
                self.offsets_models.append(pos + offset)
                self.models_metadata.append({
                    'name': name,
                    'transform': transform,
                    'u_a': u_a
                })

            for i in range(self.num_models):
                if i == (self.num_models - 1):
                    self.sizes_models.append(self.offset_texture - self.offsets_models[i])
                else:
                    self.sizes_models.append(self.offsets_models[i + 1] - self.offsets_models[i])

            self.size_textures = file.seek(0, io.SEEK_END) - self.offset_texture
            self.models = []

            for i in range(self.num_models):
                file.seek(self.offsets_models[i])
                self.models.append(io.BytesIO(file.read(self.sizes_models[i])))

            file.seek(self.offset_texture)
            self.textures = io.BytesIO(file.read(self.size_textures))
            self.total_size = file.tell()

        else:
            self.id = b"SCR\0"
            self.num_models = 0
            self.offset_texture = 0
            self.size_textures = 0
            self.unknown = b"\1\0\0\0"
            self.offsets_models = []
            self.sizes_models = []
            self.models_metadata = []
            self.models = []
            self.textures = None
            self.total_size = 0

    def each_model(self):
        if not self.models:
            return []
        return self.models

    def __getitem__(self, i):
        return self.models[i]

    def invalidate_layout(self):
        self.offsets_models = []
        self.offset_texture = 0
        self.total_size = 0
        return self

    def compute_layout(self):
        current_offset = 0x10 + 0x8c * self.num_models
        self.offsets_models = [self.align(current_offset + i * self.ALIGNMENTS["wmb"], self.ALIGNMENTS["wmb"]) for i in range(self.num_models)]
        self.offset_texture = self.align(self.offsets_models[-1] + self.sizes_models[-1], self.ALIGNMENTS["wtb"])
        self.total_size = self.offset_texture + self.size_textures
        return self

    def push_model(self, file):
        self.invalidate_layout()
        self.models.append(file)
        self.sizes_models.append(len(file.getbuffer()))
        self.num_models += 1
        return self

    def set_textures(self, file):
        self.invalidate_layout()
        self.textures = file
        self.size_textures = len(file.getbuffer())
        return self

    def get_textures(self):
        return self.textures

    textures = property(get_textures, set_textures)

    def dump(self, name):
        self.compute_layout()
        uint = self.get_uint()

        with open(name, "wb") as f:
            f.write(b"\0" * self.total_size)
            f.seek(0)
            f.write(struct.pack("4s", self.id))
            f.write(struct.pack(uint, self.num_models))
            f.write(struct.pack(uint, self.offset_texture))
            f.write(struct.pack("4s", self.unknown))

            for i in range(self.num_models):
                pos = f.tell()
                f.write(struct.pack("16s", self.models_metadata[i]['name']))
                f.write(struct.pack(uint, self.offsets_models[i] - pos))
                f.write(struct.pack(f"{self.get_float()}9", *self.models_metadata[i]['transform']))
                f.write(struct.pack(f"{self.get_short()}42", *self.models_metadata[i]['u_a']))

            for i, off in enumerate(self.offsets_models):
                f.seek(off)
                self.models[i].seek(0)
                f.write(self.models[i].read())

            f.seek(self.offset_texture)
            self.textures.seek(0)
            f
            f.seek(self.offset_texture)
            self.textures.seek(0)
            f.write(self.textures.read())
        return self