import pkg_db
from dataclasses import dataclass, fields
import numpy as np
import os
import re
import gf



@dataclass
class Stride12Header:
    EntrySize: np.uint32 = np.uint32(0)
    StrideLength: np.uint32 = np.uint32(0)
    DeadBeef: np.uint32 = np.uint32(0)

def get_header(file_hex, header):
    # The header data is 0x16F bytes long, so we need to x2 as python reads each nibble not each byte

    for f in fields(header):
        if f.type == np.uint32:
            flipped = "".join(gf.get_flipped_hex(file_hex, 8))
            value = np.uint32(int(flipped, 16))
            setattr(header, f.name, value)
            file_hex = file_hex[8:]
        elif f.type == np.uint16:
            flipped = "".join(gf.get_flipped_hex(file_hex, 4))
            value = np.uint16(int(flipped, 16))
            setattr(header, f.name, value)
            file_hex = file_hex[4:]
    return header


test_dir = 'C:/d2_output'


# def get_referenced_file(file):
#     pkg_name = get_pkg_name(file)
#     if not pkg_name:
#         return None, None, None
#     entries_refpkg = {x: y for x, y in pkg_db.get_entries_from_table(pkg_name, 'FileName, RefPKG')}
#     entries_refid = {x: y for x, y in pkg_db.get_entries_from_table(pkg_name, 'FileName, RefID')}
#     ref_pkg_id = entries_refpkg[file][2:]
#     ref_pkg_name = get_pkg_name(f'{ref_pkg_id}-')
#     if not ref_pkg_name:
#         return None, None, None
#     entries_filetype = {x: y for x, y in pkg_db.get_entries_from_table(ref_pkg_name, 'FileName, FileType')}
#
#     ref_file_name = f'{ref_pkg_id}-0000' + entries_refid[file][2:]
#     return ref_pkg_name, ref_file_name, entries_filetype[ref_file_name]


def get_verts_data(verts_file, all_file_info):
    # TODO deal with this
    pkg_name = gf.get_pkg_name(verts_file)
    if not pkg_name:
        return None
    ref_file = f"{all_file_info[verts_file]['RefPKG'][2:]}-{all_file_info[verts_file]['RefID'][2:]}"
    ref_pkg_name = gf.get_pkg_name(ref_file)
    ref_file_type = all_file_info[ref_file]['FileType']
    # ref_pkg_name, ref_file, ref_file_type = get_referenced_file(verts_file)
    if ref_file_type == "Stride Header":
        header_hex = gf.get_hex_data(f'{test_dir}/{pkg_name}/{verts_file}.bin')
        stride_header = get_header(header_hex, Stride12Header())

        stride_hex = gf.get_hex_data(f'{test_dir}/{ref_pkg_name}/{ref_file}.bin')

        hex_data_split = [stride_hex[i:i + stride_header.StrideLength * 2] for i in
                          range(0, len(stride_hex), stride_header.StrideLength * 2)]
    else:
        print(f'Verts: Incorrect type of file {ref_file_type} for ref file {ref_file} verts file {verts_file}')
        return None


    coords = []
    for hex_data in hex_data_split:
        coord = []
        for j in range(3):
            selection = gf.get_flipped_hex(hex_data[j * 4:j * 4 + 4], 4)
            exp_bitdepth = 0
            mantissa_bitdepth = 15
            bias = 2 ** (exp_bitdepth - 1) - 1
            mantissa_division = 2 ** mantissa_bitdepth
            int_fs = int(selection, 16)
            mantissa = int_fs & 2 ** mantissa_bitdepth - 1
            mantissa_abs = mantissa / mantissa_division
            exponent = (int_fs >> mantissa_bitdepth) & 2 ** exp_bitdepth - 1
            negative = int_fs >> 15
            if exponent == 0:
                flt = mantissa_abs * 2 ** (bias - 1)
            else:
                print('Incorrect file given.')
                return
            if negative:
                flt += -0.35
            coord.append(flt)
        coords.append(coord)
    return coords


def get_faces_data(faces_file, all_file_info):
    ref_file = f"{all_file_info[faces_file]['RefPKG'][2:]}-{all_file_info[faces_file]['RefID'][2:]}"
    ref_pkg_name = gf.get_pkg_name(ref_file)
    ref_file_type = all_file_info[ref_file]['FileType']
    # ref_pkg_name, ref_file, ref_file_type = get_referenced_file(faces_file)
    faces = []
    if ref_file_type == "Faces Header":
        faces_hex = gf.get_hex_data(f'{test_dir}/{ref_pkg_name}/{ref_file}.bin')
        int_faces_data = [int(gf.get_flipped_hex(faces_hex[i:i+4], 4), 16)+1 for i in range(0, len(faces_hex), 4)]
        # Implementing triangle strip
        j = 0
        for i in range(0, len(int_faces_data)):
            if i == len(int_faces_data) - 2:
                return faces
            if j % 2 == 0:
                face = int_faces_data[i:i+3]
            else:
                face = [int_faces_data[i+1], int_faces_data[i], int_faces_data[i+2]]
            if 65536 in face:
                j = 0
            else:
                faces.append(face)
                j += 1
    else:
        print(f'Faces: Incorrect type of file {ref_file_type} for ref file {ref_file} verts file {faces_file}')
        return None


def get_obj_str(verts_data, faces_data):
    verts_str = ''
    for coord in verts_data:
        verts_str += f'v {coord[0]} {coord[2]} {coord[1]}\n'
    faces_str = ''
    for face in faces_data:
        faces_str += f'f {face[0]}// {face[2]}// {face[1]}//\n'
    return verts_str + faces_str


def write_obj(obj_strings, hsh, model_file, temp_direc):
    if temp_direc or temp_direc != '':
        try:
            os.mkdir(f'C:/d2_model_temp/texture_models/{temp_direc}/')
        except:
            pass
    try:
        os.mkdir(f'C:/d2_model_temp/texture_models/{temp_direc}/{model_file}')
    except:
        pass
    with open(f'C:/d2_model_temp/texture_models/{temp_direc}/{model_file}/{hsh}.obj', 'w') as f:
        f.write(obj_strings)
    print('Written to file.')


def get_verts_faces_files(model_file):
    verts_files = []
    faces_files = []
    pkg_name = gf.get_pkg_name(model_file)
    try:
        model_data_hex = gf.get_hex_data(f'{test_dir}/{pkg_name}/{model_file}.bin')
    except FileNotFoundError:
        print(f'No folder found for file {model_file}. Likely need to unpack it or design versioning system.')
        return None, None
    # Always at [400, 672, 944, 1216, 1488, ...]
    num = int(gf.get_flipped_hex(model_data_hex[176*2:180*2], 8), 16)
    for i in range(num):
        rel_hex = model_data_hex[192*2+136*2*i:192*2+136*2*(i+1)]
        for j in range(0, len(rel_hex), 8):
            hsh = rel_hex[j:j+8]
            if hsh != 'FFFFFFFF':
                print(hsh)
                if j == 0:
                    verts_files.append(gf.get_file_from_hash(gf.get_flipped_hex(hsh, 8)))
                elif j == 8:
                    # Verts 20
                    pass
                elif j == 32:
                    faces_files.append(gf.get_file_from_hash(gf.get_flipped_hex(hsh, 8)))
    print(verts_files)
    return verts_files, faces_files


def get_model(model_file, all_file_info, temp_direc=''):
    verts_files, faces_files = get_verts_faces_files(model_file)
    for i, verts_file in enumerate(verts_files):
        faces_file = faces_files[i]
        coords = get_verts_data(verts_file, all_file_info)
        faces_data = get_faces_data(faces_file, all_file_info)
        if not coords:
            print(f'{model_file} not valid')
            continue
        obj_str = get_obj_str(coords, faces_data)
        write_obj(obj_str, gf.get_hash_from_file(verts_file), model_file, temp_direc)


def export_all_models(pkg_name, all_file_info):
    entries_refid = {x: y for x, y in pkg_db.get_entries_from_table(pkg_name, 'FileName, RefID') if y == '0x13A5'}
    entries_refpkg = {x: y for x, y in pkg_db.get_entries_from_table(pkg_name, 'FileName, RefPKG') if y == '0x0003'}
    for file in entries_refid.keys():
        if file in entries_refpkg.keys():
            get_model(file, all_file_info, temp_direc=pkg_name)


if __name__ == '__main__':
    pkg_db.start_db_connection('2_9_2_1_all')
    all_file_info = {x[0]: dict(zip(['RefID', 'RefPKG', 'FileType'], x[1:])) for x in
                     pkg_db.get_entries_from_table('Everything', 'FileName, RefID, RefPKG, FileType')}
    # RefID 0x13A5, RefPKG 0x0003
    parent_file = '020E-0F86'
    # parent_file = get_file_from_hash(get_flipped_hex('1A20EC80', 8))
    # print(parent_file)
    get_model(parent_file, all_file_info)
    # export_all_models('city_tower_d2_0369', all_file_info)