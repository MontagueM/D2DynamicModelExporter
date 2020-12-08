import pkg_db
from dataclasses import dataclass, fields
import numpy as np
import os
import re
import gf
import fbx
import pyfbx_jo as pfb
import struct


@dataclass
class Stride12Header:
    EntrySize: np.uint32 = np.uint32(0)
    StrideLength: np.uint16 = np.uint16(0)
    Unk: np.uint16 = np.uint16(0)
    DeadBeef: np.uint32 = np.uint32(0)


class File:
    def __init__(self, name=None, uid=None, pkg_name=None):
        self.name = name
        self.uid = uid
        self.pkg_name = pkg_name


class HeaderFile(File):
    def __init__(self, header=None):
        super().__init__()
        self.header = header

    def get_header(self):
        if self.header:
            print('Cannot get header as header already exists.')
            return
        else:
            if not self.name:
                self.name = gf.get_file_from_hash(self.uid)
            pkg_name = gf.get_pkg_name(self.name)
            header_hex = gf.get_hex_data(f'{test_dir}/{pkg_name}/{self.name}.bin')
            return get_header(header_hex, Stride12Header())


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


test_dir = 'I:/d2_output_3_0_0_4'


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


def get_float16(hex_data, j, is_uv=False):
    flt = get_signed_int(gf.get_flipped_hex(hex_data[j * 4:j * 4 + 4], 4), 16)
    if j == 1 and is_uv:
        flt *= -1
    flt = 1 + flt / (2 ** 15 - 1)
    return flt


def get_signed_int(hexstr, bits):
    value = int(hexstr, 16)
    if value & (1 << (bits-1)):
        value -= 1 << bits
    return value


def get_verts_data(verts_file, all_file_info, is_uv):
    """
    Stride length 48 is a dynamic and physics-enabled object.
    """
    # TODO deal with this
    pkg_name = verts_file.pkg_name
    if not pkg_name:
        return None
    ref_file = f"{all_file_info[verts_file.name]['RefPKG'][2:]}-{all_file_info[verts_file.name]['RefID'][2:]}"
    ref_pkg_name = gf.get_pkg_name(ref_file)
    ref_file_type = all_file_info[ref_file]['FileType']
    # ref_pkg_name, ref_file, ref_file_type = get_referenced_file(verts_file)
    if ref_file_type == "Stride Header":
        stride_header = verts_file.header

        stride_hex = gf.get_hex_data(f'{test_dir}/{ref_pkg_name}/{ref_file}.bin')

        # print(stride_header.StrideLength)
        hex_data_split = [stride_hex[i:i + stride_header.StrideLength * 2] for i in
                          range(0, len(stride_hex), stride_header.StrideLength * 2)]
    else:
        print(f'Verts: Incorrect type of file {ref_file_type} for ref file {ref_file} verts file {verts_file}')
        return None
    # print(verts_file.name)

    if stride_header.StrideLength == 4:
        """
        UV info for dynamic, physics-based objects.
        """
        coords = get_coords_4(hex_data_split)
    elif stride_header.StrideLength == 8:
        """
        Coord info for static and dynamic, non-physics objects.
        ? info for dynamic, physics-based objects.
        """
        coords = get_coords_8(hex_data_split)
    elif stride_header.StrideLength == 12:
        """
        """
        coords = get_coords_12(hex_data_split)
    elif stride_header.StrideLength == 16:
        """
        """
        coords = get_coords_16(hex_data_split)
    elif stride_header.StrideLength == 20:
        """
        UV info for static and dynamic, non-physics objects.
        """
        coords = get_coords_20(hex_data_split)
    elif stride_header.StrideLength == 24:
        """
        UV info for dynamic, non-physics objects gear?
        """
        if is_uv:
            coords = get_coords_24_uv(hex_data_split)
        else:
            coords = get_coords_24(hex_data_split)
    elif stride_header.StrideLength == 28:
        """
        """
        coords = get_coords_28(hex_data_split)
    elif stride_header.StrideLength == 32:
        """
        """
        coords = get_coords_32(hex_data_split)
    elif stride_header.StrideLength == 40:
        """
        """
        return None
        coords = get_coords_40(hex_data_split)
    elif stride_header.StrideLength == 48:
        """
        Coord info for dynamic, physics-based objects.
        """
        # print('Stride 48')
        coords = get_coords_48(hex_data_split)
    else:
        print(f'Need to add support for stride length {stride_header.StrideLength}')
        quit()

    return coords


def get_coords_4(hex_data_split):
    coords = []
    for hex_data in hex_data_split:
        coord = []
        for j in range(2):
            flt = get_float16(hex_data, j, is_uv=True)
            coord.append(flt)
        coords.append(coord)
    return coords


def get_coords_8(hex_data_split):
    coords = []
    for hex_data in hex_data_split:
        coord = []
        # magic, magic_negative = get_float16(hex_data[12:16], 0)
        for j in range(3):
            flt = get_float16(hex_data, j, is_uv=False)
            coord.append(flt)
        coords.append(coord)
    return coords


def get_coords_12(hex_data_split):
    coords = []
    for hex_data in hex_data_split:
        coord = []
        # magic, magic_negative = get_float16(hex_data[12:16], 0)
        for j in range(3):
            flt = get_float16(hex_data, j, is_uv=False)
            coord.append(flt)
        coords.append(coord)
    return coords


def get_coords_16(hex_data_split):
    coords = []
    for hex_data in hex_data_split:
        coord = []
        # magic, magic_negative = get_float16(hex_data[12:16], 0)
        for j in range(3):
            flt = get_float16(hex_data, j, is_uv=False)
            coord.append(flt)
        coords.append(coord)
    return coords


def get_coords_20(hex_data_split):
    coords = []
    for hex_data in hex_data_split:
        coord = []
        for j in range(2):
            flt = get_float16(hex_data, j, is_uv=True)
            coord.append(flt)
        coords.append(coord)
    return coords


def get_coords_24_uv(hex_data_split):
    coords = []
    for hex_data in hex_data_split:
        coord = []
        for j in range(2):
            flt = get_float16(hex_data, j, is_uv=True)
            coord.append(flt)
        coords.append(coord)
    return coords


def get_coords_24(hex_data_split):
    coords = []
    for hex_data in hex_data_split:
        coord = []
        for j in range(3):
            flt = get_float16(hex_data, j, is_uv=False)
            coord.append(flt)
        coords.append(coord)
    return coords

def get_coords_28(hex_data_split):
    coords = []
    for hex_data in hex_data_split:
        coord = []
        for j in range(3):
            flt = get_float16(hex_data, j, is_uv=False)
            coord.append(flt)
        coords.append(coord)
    return coords


def get_coords_32(hex_data_split):
    coords = []
    for hex_data in hex_data_split:
        hex_data = hex_data[40:]
        coord = []
        for j in range(3):
            flt = get_float16(hex_data, j, is_uv=False)
            coord.append(flt)
        coords.append(coord)
    return coords


def get_coords_40(hex_data_split):
    coords = []
    for hex_data in hex_data_split:
        coord = []
        for j in range(3):
            flt = get_float16(hex_data, j, is_uv=False)
            coord.append(flt)
        coords.append(coord)
    return coords


def get_coords_48(hex_data_split):
    coords = []
    for hex_data in hex_data_split:
        coord = []
        for j in range(3):
            flt = struct.unpack('f', bytes.fromhex(hex_data[j * 8:j * 8 + 8]))[0]
            coord.append(flt)
        coords.append(coord)
    return coords


def get_faces_data(faces_file, all_file_info, lod_0_count=None):
    LOD_ENABLED = False
    try:
        ref_file = f"{all_file_info[faces_file.name]['RefPKG'][2:]}-{all_file_info[faces_file.name]['RefID'][2:]}"
    except KeyError:
        return []
    ref_pkg_name = gf.get_pkg_name(ref_file)
    ref_file_type = all_file_info[ref_file]['FileType']
    # ref_pkg_name, ref_file, ref_file_type = get_referenced_file(faces_file)
    faces = []
    if ref_file_type == "Faces Header":
        faces_hex = gf.get_hex_data(f'{test_dir}/{ref_pkg_name}/{ref_file}.bin')
        int_faces_data = [int(gf.get_flipped_hex(faces_hex[i:i+4], 4), 16)+1 for i in range(0, len(faces_hex), 4)]
        if 'FFFF' in faces_hex:
            # Implementing triangle strip
            number_of_ffs = 0
            j = 0
            offset = 0
            for i in range(0, len(int_faces_data)):
                i += offset
                # print(len(faces), number_of_ffs, number_of_ffs*3 + len(faces), lod_0_count+1)
                # print(ff_encountered, lod_0_count)
                if LOD_ENABLED:
                    if faces_file.name == '0236-1010':
                        print(number_of_ffs)
                        # if number_of_ffs*3 + len(faces) == lod_0_count[0]+1 or number_of_ffs > 0:
                        #     print(number_of_ffs)
                        #     return faces
                    else:
                        if number_of_ffs*3 + len(faces) == lod_0_count[0]+1:
                            return faces
                if i == len(int_faces_data) - 2:
                    return faces
                if j % 2 == 0:
                    face = int_faces_data[i:i+3]
                else:
                    face = [int_faces_data[i+1], int_faces_data[i], int_faces_data[i+2]]
                if 65536 in face:
                    offset += 2
                    number_of_ffs += 1
                    j = 0
                else:
                    # if number_of_ffs < 45000:
                    #     j += 1
                    #     continue
                    faces.append(face)
                    j += 1
        else:
            if len(int_faces_data) % 3 != 0:
                return None
            for i in range(0, len(int_faces_data), 3):
                if LOD_ENABLED:
                    if len(faces) == lod_0_count[1]*3:
                        return faces
                face = []
                for j in range(3):
                    face.append(int_faces_data[i + j])
                faces.append(face)
            return faces
    else:
        print(f'Faces: Incorrect type of file {ref_file_type} for ref file {ref_file} verts file {faces_file}')
        return None


def get_obj_str(verts_data, faces_data, vts):
    verts_str = ''
    for coord in verts_data:
        verts_str += f'v {coord[0]} {coord[1]} {coord[2]}\n'
    faces_str = ''
    for coord in vts:
        if coord:
            verts_str += f'vt {coord[0]} {coord[1]}\n'
    for face in faces_data:
        faces_str += f'f {face[0]}/{face[0]}/ {face[1]}/{face[1]}/ {face[2]}/{face[2]}/\n'
    return verts_str + faces_str


def write_fbx(faces_data, verts_data, hsh, model_file, temp_direc):
    controlpoints = [fbx.FbxVector4(x[0], x[1], x[2]) for x in verts_data]
    # manager = Manager()
    # manager.create_scene(name)
    fb = pfb.FBox()
    fb.create_node()

    mesh = fbx.FbxMesh.Create(fb.scene, hsh)

    # for vert in verts_data:
        # fb.create_mesh_controlpoint(vert[0], vert[1], vert[2])
    controlpoint_count = len(controlpoints)
    mesh.InitControlPoints(controlpoint_count)
    for i, p in enumerate(controlpoints):
        mesh.SetControlPointAt(p, i)
    for face in faces_data:
        mesh.BeginPolygon()
        mesh.AddPolygon(face[0]-1)
        mesh.AddPolygon(face[1]-1)
        mesh.AddPolygon(face[2]-1)
        mesh.EndPolygon()

    node = fbx.FbxNode.Create(fb.scene, '')
    node.SetNodeAttribute(mesh)
    fb.scene.GetRootNode().AddChild(node)
    if temp_direc or temp_direc != '':
        try:
            os.mkdir(f'I:/dynamic_models/{temp_direc}/')
        except:
            pass
    try:
        os.mkdir(f'I:/dynamic_models/{temp_direc}/{model_file}')
    except:
        pass
    fb.export(save_path=f'I:/dynamic_models/{temp_direc}/{model_file}/{hsh}.fbx', ascii_format=False)
    print(f'Written I:/dynamic_models/{temp_direc}/{model_file}/{hsh}.fbx.')


def write_obj(obj_strings, hsh, model_file, temp_direc):
    # return
    if temp_direc or temp_direc != '':
        try:
            os.mkdir(f'I:/dynamic_models/{temp_direc}/')
        except:
            pass
    try:
        os.mkdir(f'I:/dynamic_models/{temp_direc}/{model_file}')
    except:
        pass
    with open(f'I:/dynamic_models/{temp_direc}/{model_file}/{hsh}.obj', 'w') as f:
        f.write(obj_strings)
    print(f'Written {temp_direc}/{model_file}/{hsh} to obj.')


def get_verts_faces_files(model_file):
    pos_verts_files = []
    uv_verts_files = []
    faces_files = []
    pkg_name = gf.get_pkg_name(model_file)
    try:
        model_data_hex = gf.get_hex_data(f'{test_dir}/{pkg_name}/{model_file}.bin')
    except FileNotFoundError:
        print(f'No folder found for file {model_file}. Likely need to unpack it or design versioning system.')
        return None, None, None
    # Always at [400, 672, 944, 1216, 1488, ...]
    num = int(gf.get_flipped_hex(model_data_hex[176*2:180*2], 8), 16)
    for i in range(num):
        rel_hex = model_data_hex[192*2+136*2*i:192*2+136*2*(i+1)]
        for j in range(0, len(rel_hex), 8):
            hsh = rel_hex[j:j+8]
            if hsh != 'FFFFFFFF':
                hf = HeaderFile()
                hf.uid = hsh
                hf.name = gf.get_file_from_hash(hf.uid)
                hf.pkg_name = gf.get_pkg_name(hf.name)
                if j == 0:
                    hf.header = hf.get_header()
                    print(f'Position file {hf.name} stride {hf.header.StrideLength}')
                    pos_verts_files.append(hf)
                elif j == 8:
                    hf.header = hf.get_header()
                    print(f'UV file {hf.name} stride {hf.header.StrideLength}')
                    uv_verts_files.append(hf)
                elif j == 32:
                    faces_files.append(hf)
                    break
    # print(pos_verts_files, uv_verts_files)
    return pos_verts_files, uv_verts_files, faces_files


def get_lod_0_faces(model_file, num):
    pkg_name = gf.get_pkg_name(model_file)
    f_hex = gf.get_hex_data(f'{test_dir}/{pkg_name}/{model_file}.bin')
    offset = [m.start() for m in re.finditer('7E738080', f_hex)]
    if len(offset) != num:
        print('ERROR: Fix this, means one model has no LODs or something.')
        return None
    lod_0_faces = []
    for i in range(num):
        lod_0_faces.append([])
        # Triangle strip
        lod_0_faces[-1].append(int(gf.get_flipped_hex(f_hex[offset[i]+40:offset[i]+48], 8), 16))
        # Normal
        lod_0_faces[-1].append(int(gf.get_flipped_hex(f_hex[offset[i]+48:offset[i]+56], 8), 16))
    return lod_0_faces


def get_model(model_file, all_file_info, temp_direc=''):
    print(f'Parent file {model_file}')
    pos_verts_files, uv_verts_files, faces_files = get_verts_faces_files(model_file)
    # lod_0_faces = get_lod_0_faces(model_file, len(pos_verts_files))
    # if not lod_0_faces:
    #     return
    for i, pos_vert_file in enumerate(pos_verts_files):
        faces_file = faces_files[i]
        coords = get_verts_data(pos_vert_file, all_file_info, is_uv=False)
        faces_data = get_faces_data(faces_file, all_file_info)
        if not faces_data:
            print('No faces data')
            return
        print(len(faces_data))
        if len(uv_verts_files) == len(pos_verts_files):
            uv_data = get_verts_data(uv_verts_files[i], all_file_info, is_uv=True)
        else:
            uv_data = []
        if not coords or not faces_data:
            print(f'{pos_vert_file.uid} not valid')
            continue

        scaled_pos_verts = scale_verts(coords, model_file)
        # TODO update this so fbx has uvs
        # obj_str = get_obj_str(scaled_pos_verts, faces_data, uv_data)
        # write_obj(obj_str, pos_vert_file.uid, model_file, temp_direc)
        write_fbx(faces_data, scaled_pos_verts, pos_vert_file.uid, model_file, temp_direc)


def scale_verts(verts_data, model_file):
    pkg_name = gf.get_pkg_name(model_file)
    model_hex = gf.get_hex_data(f'{test_dir}/{pkg_name}/{model_file}.bin')
    # TODO fix this, this isn't correct but it is needed.
    model_scale = [struct.unpack('f', bytes.fromhex(model_hex[j:j + 8]))[0] for j in range(0x70*2, (0x70+12)*2, 8)]

    for i in range(len(verts_data)):
        for j in range(3):
            verts_data[i][j] *= model_scale[j]

    return verts_data


def export_all_models(pkg_name, all_file_info):
    entries_type = {x: y for x, y in pkg_db.get_entries_from_table(pkg_name, 'FileName, FileType') if y == 'Dynamic Model Header 2'}
    for file in list(entries_type.keys()):
        if file == '01B5-1666':
            a = 0
        print(f'Getting file {file}')
        get_model(file, all_file_info, temp_direc='combatants/' + pkg_name)


if __name__ == '__main__':
    pkg_db.start_db_connection('3_0_0_4')
    all_file_info = {x[0]: dict(zip(['RefID', 'RefPKG', 'FileType'], x[1:])) for x in
                     pkg_db.get_entries_from_table('Everything', 'FileName, RefID, RefPKG, FileType')}
    # RefID 0x13A5, RefPKG 0x0003
    # parent_file = '023A-1DE0'
    # parent_file = '0234-16B2'
    # parent_file = '03B8-047B'
    parent_file = '01EB-19B2'
    parent_file = gf.get_file_from_hash('17B8B580')
    # get_model(parent_file, all_file_info)
    # parent_file = '0361-0012'
    # parent_file = '020E-1F9C'l
    # parent_file = '01FE-054A'
    # parent_file = get_file_from_hash(get_flipped_hex('1A20EC80', 8))
    # print(parent_file)
    # parent_file = '0378-03E5'
    get_model(parent_file, all_file_info)
    quit()
    for pkg in pkg_db.get_all_tables():
        if 'cinematic' in pkg:
            # if pkg not in os.listdir('C:/d2_model_temp/texture_models/tower'):
                export_all_models(pkg, all_file_info)
