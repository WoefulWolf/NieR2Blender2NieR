from ....utils.ioUtils import write_Int32, write_uInt32


def create_wmb_batches(wmb_file, data):
    wmb_file.seek(data.batches_Offset)

    for batch in data.batches.batches:
        write_uInt32(wmb_file, batch.vertexGroupIndex)                  # vertexGroupIndex
        write_Int32(wmb_file, batch.boneSetIndex)                       # boneSetIndex
        write_uInt32(wmb_file, batch.vertexStart)                       # vertexStart
        write_uInt32(wmb_file, batch.indexStart)                        # indexStart
        write_uInt32(wmb_file, batch.numVertexes)                       # numVertexes
        write_uInt32(wmb_file, batch.numIndexes)                        # numIndexes
        write_uInt32(wmb_file, batch.numPrimitives)                     # numPrimitives