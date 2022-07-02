from .col_colTreeNodes import write_col_colTreeNodes
from .col_generate_data import COL_Data
from .col_header import write_col_header
from .col_meshes import write_col_meshes
from .col_namegroups import write_col_namegroups


def main(filepath, generateColTree):
    data = COL_Data(generateColTree)

    print('Creating col file: ', filepath)
    col_file = open(filepath, 'wb')

    print("Writing Header:")
    write_col_header(col_file, data)

    print("Writing NameGroups:")
    write_col_namegroups(col_file, data)

    print("Writing Meshes & Batches...")
    write_col_meshes(col_file, data)
    data.boneMap.writeToFile(data.offsetBoneMap, col_file)
    data.boneMap2.writeToFile(data.offsetBoneMap2, col_file)

    print("Writing ColTreeNodes...")
    write_col_colTreeNodes(col_file, data)

    print("Finished exporting", filepath, "\nGood luck! :S")

    col_file.flush()
    col_file.close()
