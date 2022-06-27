from . import generate_wta_wtp_data


def main(context, export_filepath):
    identifiers_array, texture_paths_array, albedo_indexes = generate_wta_wtp_data.generate(context)

    if None in [identifiers_array, texture_paths_array, albedo_indexes]:
        print("WTP Export Failed! :{")
        return

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