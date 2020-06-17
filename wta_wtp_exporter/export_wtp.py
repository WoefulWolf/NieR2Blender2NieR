import bpy
import os
from . import generate_wta_wtp_data
from .wta_wtp_utils import *

def main(context, export_filepath):
    identifiers_array, texture_paths_array, albedo_indexes = generate_wta_wtp_data.generate(context)

    # Make sure DDS are padded
    #pad_dds_files(texture_paths_array)

    wtp_fp = open(export_filepath,'wb')

    for i in range(len(texture_paths_array)):
        dds_fp = open(texture_paths_array[i],'rb')
        content = dds_fp.read()
        #print("-Writing dds: " + texture_paths_array[i] + " to file: " + export_filepath + " at position: " + str(i))
        wtp_fp.write(content)
        dds_fp.close()
        
    wtp_fp.close()
    print('WTP Export Complete. :}')