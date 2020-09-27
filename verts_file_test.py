import gf
import pkg_db
import get_dynamic_model_textures as gdm
import struct


def get_verts_data(verts_file, all_file_info):
    """
    Stride length 48 is a dynamic and physics-enabled object.
    """
    # TODO deal with this
    pkg_name = gf.get_pkg_name(verts_file)
    if not pkg_name:
        return None
    ref_file = f"{all_file_info[verts_file]['RefPKG'][2:]}-{all_file_info[verts_file]['RefID'][2:]}"
    ref_pkg_name = gf.get_pkg_name(ref_file)
    ref_file_type = all_file_info[ref_file]['FileType']
    # ref_pkg_name, ref_file, ref_file_type = get_referenced_file(verts_file)
    if ref_file_type == "Stride Header":
        header_hex = gf.get_hex_data(f'{gdm.test_dir}/{pkg_name}/{verts_file}.bin')
        stride_header = gdm.get_header(header_hex, gdm.Stride12Header())

        stride_hex = gf.get_hex_data(f'{gdm.test_dir}/{ref_pkg_name}/{ref_file}.bin')

        # print(stride_header.StrideLength)
        hex_data_split = [stride_hex[i:i + stride_header.StrideLength * 2] for i in
                          range(0, len(stride_hex), stride_header.StrideLength * 2)]
    else:
        print(f'Verts: Incorrect type of file {ref_file_type} for ref file {ref_file} verts file {verts_file}')
        return None
    print(verts_file)
    coords = []
    for hex_data in hex_data_split:
        coord = []
        # print(hex_data)
        # print(hex_data[12:16])
        w, w_negative = gdm.get_float16(hex_data[12:16], 0)
        for j in range(3):
            flt, negative = gdm.get_float16(hex_data, j)
            flt *= (-1)**negative
            print(flt)
            # if negative:
            #     flt *= (-1)**negative * (-1)**w_negative * (1/w)
            # if negative:
            #     flt += -0.35
            flt = struct.unpack('f', bytes.fromhex(hex_data[j*8:j*8+8]))[0]
            coord.append(flt)
        coords.append(coord)
    return coords


def write_obj():
    with open(f'test_verts/test.obj', 'w') as f:
        for coord in coords:
            f.write(f'v {coord[0]} {coord[1]} {coord[2]}\n')
    print(f'Written to file.')


if __name__ == '__main__':
    pkg_db.start_db_connection('2_9_2_1_all')
    all_file_info = {x[0]: dict(zip(['RefID', 'RefPKG', 'FileType'], x[1:])) for x in
                     pkg_db.get_entries_from_table('Everything', 'FileName, RefID, RefPKG, FileType')}
    coords = get_verts_data('0234-16AF', all_file_info)
    write_obj()