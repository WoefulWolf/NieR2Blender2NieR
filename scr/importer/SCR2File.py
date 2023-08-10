import io
import struct

class SCR2File:
    ALIGNMENTS = {
        'wmb': 0x80,
    }

    @staticmethod
    def is_big(f):
        f.seek(0)
        id_value = f.read(4)
        if id_value != b"SCR\0":
            raise ValueError(f"Invalid id {id_value}!")

        a, b = struct.unpack("2H", f.read(4))
        f.seek(0)
        return a > 0 and b > 0

    def get_uint(self):
        return "I>" if self.big else "I<"

    def get_ushort(self):
        return "H>" if self.big else "H<"

    def get_float(self):
        return "f>" if self.big else "f<"

    def get_short(self):
        return "h>" if self.big else "h<"

    def __init__(self, f=None, big=False):
        self.big = big
        if f:
            file_name_input = False
            if not (hasattr(f, 'read') and hasattr(f, 'seek')):
                file_name_input = True
                f = open(f, 'rb')

            self.big = self.is_big(f)

            f.seek(0)
            uint = self.get_uint()
            ushort = self.get_ushort()
            float_fmt = self.get_float()
            short_fmt = self.get_short()

            self.id = f.read(4)
            if self.id != b"SCR\0":
                raise ValueError(f"Invalid id {self.id}!")

            self.unknown, self.num_models = struct.unpack(f"{ushort}2", f.read(4))
            self.offset_offsets_models = struct.unpack(uint, f.read(4))[0]

            f.seek(self.offset_offsets_models)
            self.offsets_models_meta = struct.unpack(f"{uint}{self.num_models}", f.read(4 * self.num_models))
            self.offsets_models = []
            self.sizes_models = []

            self.models_metadata = [None] * self.num_models
            for i in range(self.num_models):
                f.seek(self.offsets_models_meta[i])
                offset = struct.unpack(uint, f.read(4))[0]
                name = f.read(64)
                transform = struct.unpack(f"{float_fmt}9", f.read(4 * 9))
                u_a = struct.unpack(f"{short_fmt}18", f.read(18 * 2))
                self.offsets_models.append(offset)
                self.models_metadata[i] = {
                    'name': name,
                    'transform': transform,
                    'u_a': u_a
                }

            for i in range(self.num_models):
                if i == self.num_models - 1:
                    self.sizes_models.append(f.tell() - self.offsets_models[i])
                else:
                    self.sizes_models.append(self.offsets_models_meta[i + 1] - self.offsets_models[i])

            self.models = [None] * self.num_models
            for i in range(self.num_models):
                f.seek(self.offsets_models[i])
                self.models[i] = io.BytesIO(f.read(self.sizes_models[i]))

            self.total_size = f.tell()
            if file_name_input:
                f.close()
        else:
            self.id = b"SCR\0"
            self.unknown = 0x12
            self.num_models = 0
            self.offsets_models = []
            self.sizes_models = []
            self.models_metadata = []
            self.offsets_models_meta = []
            self.models = []
            self.total_size = 0
            self.offset_offsets_models = 0

    def each_model(self):
        for i in range(self.num_models):
            yield self.models[i]

    def __getitem__(self, i):
        return self.models[i]

    def invalidate_layout(self):
        self.offsets_models = []
        self.total_size = 0
        return self

    def compute_layout(self):
        current_offset = 0x8 + 4 * self.num_models
        self.offsets_models = [0] * self.num_models
        for i in range(self.num_models):
            tmp = align(current_offset, self.ALIGNMENTS["wmb"])
            current_offset = tmp + self.sizes_models[i]
            self.offsets_models[i] = tmp

        self.offset_offsets_models = align(current_offset, self.ALIGNMENTS["wmb"])
        self.total_size = self.offset_offsets_models + 4 * self.num_models
        return self

    def push_model(self, file):
        self.invalidate_layout()
        self.models.append(file)
        self.sizes_models.append(len(file.getvalue()))
        self.num_models += 1
        return self

    def dump(self, name):
        self.compute_layout()
        uint = self.get_uint()
        ushort = self.get_ushort()

        with open(name, "wb") as f:
            f.write(b"\0" * self.total_size)
            f.seek(0)
            f.write(struct.pack("4s", self.id))
            f.write(struct.pack(f"{ushort}2", self.unknown, self.num_models))
            f.write(struct.pack(uint, self.offset_offsets_models))

            for i in range(self.num_models):
                f.seek(self.offset_offsets_models + 4 * i)
                f.write(struct.pack(uint, self.offsets_models[i]))

            for i in range(self.num_models):
                f.seek(self.offsets_models_meta[i])
                f.write(struct.pack(uint, self.offsets_models[i]))
                f.write(self.models_metadata[i]['name'])
                f.write(struct.pack(f"{self.get_float()}9", *self.models_metadata[i]['transform']))
                f.write(struct.pack(f"{self.get_short()}18", *self.models_metadata[i]['u_a']))

            for i in range(self.num_models):
                f.seek(self.offsets_models[i])
                f.write(self.models[i].read())

        return self