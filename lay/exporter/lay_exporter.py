from .lay_assets import write_assets, write_instances
from .lay_generate_data import LAY_Data
from .lay_header import write_lay_header
from .lay_modelEntries import write_modelEntries


def main(filepath):
    data = LAY_Data()

    print('Creating lay file: ', filepath)
    lay_file = open(filepath, 'wb')

    print("Writing Header:")
    write_lay_header(lay_file, data)

    print("Writing ModelEntries:")
    write_modelEntries(lay_file, data)

    print("Writing Assets:")
    write_assets(lay_file, data)

    print("Writing Instances:")
    write_instances(lay_file, data)

    print("Finished exporting", filepath, "\nGoodluck! :V")

    lay_file.flush()
    lay_file.close()