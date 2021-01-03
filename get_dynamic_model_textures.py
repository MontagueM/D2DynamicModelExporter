import pkg_db
from dataclasses import dataclass, fields
import numpy as np
import os
import re
import gf
import fbx
import pyfbx_jo as pfb
import struct
import binascii


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


test_dir = 'I:/d2_output_3_0_1_3'


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
    # flt = get_signed_int(gf.get_flipped_hex(hex_data[j * 4:j * 4 + 4], 4), 16)
    flt = int.from_bytes(binascii.unhexlify(hex_data[j * 4:j * 4 + 4]), 'little', signed=True)
    # if j == 1 and is_uv:
    #     flt *= -1
    flt = 1 + flt / (2 ** 15 - 1)
    return flt


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
    if ref_file_type == "Vertex Data":
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
        # return None
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


class Submesh:
    def __init__(self):
        self.pos_verts = []
        self.adjusted_pos_verts = []
        self.norm_verts = []
        self.uv_verts = []
        self.faces = []
        self.material = None
        self.textures = []
        self.diffuse = None
        self.normal = None
        self.lod_level = 0
        self.name = None
        self.type = None
        self.stride = None
        self.entry = SubmeshEntryProper


# class SubmeshEntry:
#     def __init__(self):
#         self.Material = None
#         self.x4 = None
#         self.five = None
#         self.FaceOffset = None  # x8
#         self.FaceCount = None  # xC
#         self.EndFaceCount = None  # x10
#         self.x14 = None
#         self.x16 = None
#         self.x18 = None
#         self.x1A = None
#         self.LODLevel = None  # x1B
#         self.x1C = None
#         self.x0000 = None
#         self.FFFFFFFF = None


class SubmeshEntryProper:
    def __init__(self):
        self.Material = None
        self.x4 = None
        self.PrimitiveType = None  # x6, 3 indicates triangles, 5 indicates triangle strip
        self.IndexOffset = None  # x8
        self.IndexCount = None  # xC
        self.EndFaceCount = None  # x10
        self.x14 = None
        self.x16 = None
        self.Flags = None  # x18, if flags & 0x8 != 0 it uses alpha clip/test
        self.GearDyeChangeColourIndex = None  # x1A
        self.LODLevel = None  # x1B
        self.x1C = None
        self.x0000 = None
        self.FFFFFFFF = None


def trim_verts_data(verts_data, faces_data):
    all_v = []
    for face in faces_data:
        for v in face:
            all_v.append(v)
    return verts_data[min(all_v)-1:max(all_v)]


def get_submeshes(file, index, pos_verts, uv_verts, face_hex):
    # faces_ = faces
    # Getting the submesh table entries
    fbin = open(f'I:/d2_output_3_0_1_3/{gf.get_pkg_name(file)}/{file}.bin', 'rb').read()
    # offset = fbin.find(b'\xCB\x6E\x80\x80')
    offset = [m.start() for m in re.finditer(b'\xCB\x6E\x80\x80', fbin)][index]
    if offset == -1:
        raise Exception('File contains no submeshes')
    entry_count = gf.get_uint32(fbin, offset-8)
    entries = []
    offset += 8
    stride = 4

    for i in range(offset, offset+0x24*entry_count, 0x24):
        entry = SubmeshEntryProper()
        entry.Material = fbin[i:i+4]
        entry.PrimitiveType = gf.get_uint16(fbin, i+0x6)
        entry.IndexOffset = gf.get_uint32(fbin, i+0x8)
        entry.IndexCount = gf.get_uint32(fbin, i+0xC)
        entry.EndFaceCount = gf.get_uint32(fbin, i+0x10)
        entry.Flags = gf.get_uint32(fbin, i+0x18)
        # if entry.Flags & 0x8 != 0:
        #     print('Model using alpha test')
        entry.LODLevel = fbin[i+0x1B]
        entries.append(entry)

    if len(pos_verts) > 65535:
        stride = 8


    # Making submeshes
    submeshes = []
    for i, entry in enumerate(entries):
        submesh = Submesh()
        # if 'FFFFFFFF' or '00000000' in face_hex:
        #     submesh.stride = 8
        # elif 'FFFF' in face_hex or '0000' in face_hex:
        #     submesh.stride = 4
        submesh.entry = entry
        submesh.name = f'{gf.get_hash_from_file(file)}_{i}_{submesh.lod_level}'
        submesh.material = binascii.hexlify(entry.Material).decode().upper()
        submesh.type = entry.PrimitiveType
        submesh.lod_level = entry.LODLevel

        submeshes.append(submesh)

    # Removing duplicate submeshes
    # This will need changing when materials get implemented
    existing = {}
    for submesh in list(submeshes):
        if submesh.entry.IndexOffset in existing.keys():
            if submesh.lod_level >= existing[submesh.entry.IndexOffset]:
                submeshes.remove(submesh)
                continue
        faces = get_submesh_faces(submesh, face_hex, stride)
        submesh.pos_verts = trim_verts_data(pos_verts, faces)
        if uv_verts:
            submesh.uv_verts = trim_verts_data(uv_verts, faces)
        else:
            submesh.uv_verts = uv_verts
        alt = shift_faces_down(faces)
        submesh.faces = alt
        existing[submesh.entry.IndexOffset] = submesh.lod_level

    return submeshes


def scale_and_repos_pos_verts(verts_data, fbin):
    scale = struct.unpack('f', fbin[108:108 + 4])[0]
    for i in range(len(verts_data)):
        for j in range(3):
            verts_data[i][j] *= scale

    position_shift = [struct.unpack('f', fbin[96 + 4 * i:96 + 4 * (i + 1)])[0] for i in range(3)]
    for i in range(3):
        for j in range(len(verts_data)):
            verts_data[j][i] -= (scale - position_shift[i])
    return verts_data


def scale_and_repos_uv_verts(verts_data, fbin):
    # return verts_data
    scales = [struct.unpack('f', fbin[112+i*4:112+(i+1)*4])[0] for i in range(2)]
    position_shifts = [struct.unpack('f', fbin[120+i*4:120+(i+1)*4])[0] for i in range(2)]
    for i in range(len(verts_data)):
        verts_data[i][0] *= scales[0]
        verts_data[i][1] *= -scales[1]

    for j in range(len(verts_data)):
        verts_data[j][0] -= (scales[0] - position_shifts[0])
        verts_data[j][1] += (scales[1] - position_shifts[1] + 1)
    return verts_data


def export_fbx(submeshes, model_file, name, temp_direc, b_textures):
    model = pfb.Model()
    fbin = open(f'I:/d2_output_3_0_1_3/{gf.get_pkg_name(model_file)}/{model_file}.bin', 'rb').read()
    for submesh in submeshes:
        mesh = create_mesh(model, submesh, name)
        if not mesh.GetLayer(0):
            mesh.CreateLayer()
        layer = mesh.GetLayer(0)
        # if shaders:
        #     apply_shader(d2map, submesh, node)
        if submesh.uv_verts:
            create_uv(mesh, model_file, submesh, layer)
        node = fbx.FbxNode.Create(model.scene, submesh.name)
        node.SetNodeAttribute(mesh)
        node.LclScaling.Set(fbx.FbxDouble3(100, 100, 100))

        if b_textures:
            apply_diffuse(model, submesh, node)

        node.SetShadingMode(fbx.FbxNode.eTextureShading)
        model.scene.GetRootNode().AddChild(node)


    if temp_direc or temp_direc != '':
        try:
            os.mkdir(f'I:/dynamic_models/{temp_direc}/')
        except:
            pass
    try:
        os.mkdir(f'I:/dynamic_models/{temp_direc}/{model_file}')
    except:
        pass
    model.export(save_path=f'I:/dynamic_models/{temp_direc}/{model_file}/{name}.fbx', ascii_format=False)
    print(f'Written I:/dynamic_models/{temp_direc}/{model_file}/{name}.fbx.')


def apply_diffuse(model, submesh, node):
    # print('applying diffuse', tex_name)
    lMaterialName = f'mat {submesh.material}'
    lMaterial = fbx.FbxSurfacePhong.Create(model.scene, lMaterialName)
    lMaterial.DiffuseFactor.Set(1)
    lMaterial.ShadingModel.Set('Phong')
    node.AddMaterial(lMaterial)


    gTexture = fbx.FbxFileTexture.Create(model.scene, f'Diffuse Texture {submesh.material}')
    # lTexPath = f'C:/d2_maps/{folder_name}_fbx/textures/{tex_name}.png'
    lTexPath = tex_path
    # print('tex path', f'C:/d2_maps/{folder_name}_fbx/textures/{tex_name}.png')
    gTexture.SetFileName(lTexPath)
    gTexture.SetTextureUse(fbx.FbxFileTexture.eStandard)
    gTexture.SetMappingType(fbx.FbxFileTexture.eUV)
    gTexture.SetMaterialUse(fbx.FbxFileTexture.eModelMaterial)
    gTexture.SetSwapUV(False)
    gTexture.SetTranslation(0.0, 0.0)
    gTexture.SetScale(1.0, 1.0)
    gTexture.SetRotation(0.0, 0.0)

    if lMaterial:
        lMaterial.Diffuse.ConnectSrcObject(gTexture)
    else:
        raise RuntimeError('Material broken somewhere')


def get_submesh_faces(submesh: Submesh, faces_hex, stride):
    # if submesh.name == '80bc5114_1_0':
    #     a = 0
    # 3 is triangles, 5 is triangle strip
    increment = 3
    start = submesh.entry.IndexOffset
    count = submesh.entry.IndexCount
    if stride == 8:
        int_faces_data = [int(gf.get_flipped_hex(faces_hex[i:i + 8], 8), 16) + 1 for i in
                           range(0, len(faces_hex), 8)]
    else:
        int_faces_data = [int(gf.get_flipped_hex(faces_hex[i:i + 4], 4), 16) + 1 for i in
                           range(0, len(faces_hex), 4)]
    if submesh.type == 5:
        increment = 1
        count -= 2

    faces = []
    j = 0
    for i in range(0, count, increment):
        face_index = start + i

        if 65536 in int_faces_data[face_index:face_index+3] or 4294967296 in int_faces_data[face_index:face_index+3]:
            j = 0
            continue

        if submesh.type == 3 or j % 2 == 0:
            face = int_faces_data[face_index:face_index+3]
        else:
            # face = int_faces_data[face_index:face_index+3][::-1]
            face = [int_faces_data[face_index+1], int_faces_data[face_index+0], int_faces_data[face_index+2]]
        if face == []:
            a = 0
        faces.append(face)
        j += 1
    return faces


def get_face_hex(faces_file, all_file_info) -> str:
    try:
        ref_file = f"{all_file_info[faces_file.name]['RefPKG'][2:]}-{all_file_info[faces_file.name]['RefID'][2:]}"
    except KeyError:
        return ''
    ref_pkg_name = gf.get_pkg_name(ref_file)
    ref_file_type = all_file_info[ref_file]['FileType']
    if ref_file_type == "Faces Data":
        faces_hex = gf.get_hex_data(f'{test_dir}/{ref_pkg_name}/{ref_file}.bin')
        return faces_hex
    return ''


def get_obj_str(verts_data, faces_data, vts):
    verts_str = ''
    for coord in verts_data:
        verts_str += f'v {coord[0]*100} {coord[1]*100} {coord[2]*100}\n'
    faces_str = ''
    for coord in vts:
        if coord:
            verts_str += f'vt {coord[0]} {coord[1]}\n'
    for face in faces_data:
        faces_str += f'f {face[0]}// {face[1]}// {face[2]}//\n'
    return verts_str + faces_str


    # def write_fbx(faces_data, verts_data, hsh, model_file, temp_direc):
    #     controlpoints = [fbx.FbxVector4(x[0], x[1], x[2]) for x in verts_data]
    #     # manager = Manager()
    #     # manager.create_scene(name)
    #     fb = pfb.Model()
    #     mesh = fbx.FbxMesh.Create(fb.scene, hsh)
    #
    #     # for vert in verts_data:
    #         # fb.create_mesh_controlpoint(vert[0], vert[1], vert[2])
    #     for i, p in enumerate(controlpoints):
    #         mesh.SetControlPointAt(p, i)
    #     for face in faces_data:
    #         mesh.BeginPolygon()
    #         mesh.AddPolygon(face[0])
    #         mesh.AddPolygon(face[1])
    #         mesh.AddPolygon(face[2])
    #         mesh.EndPolygon()
    #
    #     node = fbx.FbxNode.Create(fb.scene, '')
    #     node.SetNodeAttribute(mesh)
    #     fb.scene.GetRootNode().AddChild(node)
    #     if temp_direc or temp_direc != '':
    #         try:
    #             os.mkdir(f'I:/dynamic_models/{temp_direc}/')
    #         except:
    #             pass
    #     try:
    #         os.mkdir(f'I:/dynamic_models/{temp_direc}/{model_file}')
    #     except:
    #         pass
    #     fb.export(save_path=f'I:/dynamic_models/{temp_direc}/{model_file}/{hsh}.fbx', ascii_format=False)
    #     print(f'Written I:/dynamic_models/{temp_direc}/{model_file}/{hsh}.fbx.')
    #
    #
    # def write_obj(obj_strings, hsh, model_file, temp_direc):
    #     # return
    #     if temp_direc or temp_direc != '':
    #         try:
    #             os.mkdir(f'I:/dynamic_models/{temp_direc}/')
    #         except:
    #             pass
    #     try:
    #         os.mkdir(f'I:/dynamic_models/{temp_direc}/{model_file}')
    #     except:
    #         pass
    #     with open(f'I:/dynamic_models/{temp_direc}/{model_file}/{hsh}.obj', 'w') as f:
    #         f.write(obj_strings)
    #     print(f'Written {temp_direc}/{model_file}/{hsh} to obj.')


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
        rel_hex = model_data_hex[192*2+128*2*i:192*2+128*2*(i+1)]
        for j in range(0, len(rel_hex), 8):
            hsh = rel_hex[j:j+8]
            if hsh != 'FFFFFFFF':
                hf = HeaderFile()
                hf.uid = hsh
                hf.name = gf.get_file_from_hash(hf.uid)
                hf.pkg_name = gf.get_pkg_name(hf.name)
                if j == 0:
                    hf.header = hf.get_header()
                    # print(f'Position file {hf.name} stride {hf.header.StrideLength}')
                    pos_verts_files.append(hf)
                elif j == 8:
                    hf.header = hf.get_header()
                    # print(f'UV file {hf.name} stride {hf.header.StrideLength}')
                    uv_verts_files.append(hf)
                elif j == 32:
                    faces_files.append(hf)
                    break
    # print(pos_verts_files, uv_verts_files)
    return pos_verts_files, uv_verts_files, faces_files


# def get_lod_0_faces(model_file, num):
#     pkg_name = gf.get_pkg_name(model_file)
#     f_hex = gf.get_hex_data(f'{test_dir}/{pkg_name}/{model_file}.bin')
#     offset = [m.start() for m in re.finditer('7E738080', f_hex)]
#     if len(offset) != num:
#         print('ERROR: Fix this, means one model has no LODs or something.')
#         return None
#     lod_0_faces = []
#     for i in range(num):
#         lod_0_faces.append([])
#         # Triangle strip
#         lod_0_faces[-1].append(int(gf.get_flipped_hex(f_hex[offset[i]+40:offset[i]+48], 8), 16))
#         # Normal
#         lod_0_faces[-1].append(int(gf.get_flipped_hex(f_hex[offset[i]+48:offset[i]+56], 8), 16))
#     return lod_0_faces


def shift_faces_down(faces_data):
    a_min = faces_data[0][0]
    for f in faces_data:
        for i in f:
            if i < a_min:
                a_min = i
    for i, f in enumerate(faces_data):
        for j, x in enumerate(f):
            faces_data[i][j] -= a_min - 1
    return faces_data


def adjust_faces_data(faces_data, max_vert_used):
    new_faces_data = []
    all_v = []
    for face in faces_data:
        for v in face:
            all_v.append(v)
    starting_face_number = min(all_v) -1
    all_v = []
    for face in faces_data:
        new_face = []
        for v in face:
            new_face.append(v - starting_face_number + max_vert_used)
            all_v.append(v - starting_face_number + max_vert_used)
        new_faces_data.append(new_face)
    return new_faces_data, max(all_v)


def get_model(model_file, all_file_info, lod, temp_direc='', b_textures=False):
    # print(f'Parent file {model_file}')
    pos_verts_files, uv_verts_files, faces_files = get_verts_faces_files(model_file)
    # lod_0_faces = get_lod_0_faces(model_file, len(pos_verts_files))
    # if not lod_0_faces:
    #     return
    fbin = open(f'I:/d2_output_3_0_1_3/{gf.get_pkg_name(model_file)}/{model_file}.bin', 'rb').read()
    for i, pos_vert_file in enumerate(pos_verts_files):
        faces_file = faces_files[i]
        pos_verts = get_verts_data(pos_vert_file, all_file_info, is_uv=False)
        # if len(pos_verts) <= 65535:
        #     continue
        # else:
        #     print(model_file, f'is larger!!!! {len(pos_verts)}')
        pos_verts = scale_and_repos_pos_verts(pos_verts, fbin)
        if i < len(uv_verts_files):
            uv_verts = get_verts_data(uv_verts_files[i], all_file_info, is_uv=True)
            uv_verts = scale_and_repos_uv_verts(uv_verts, fbin)
        else:
            uv_verts = []
        # scaled_pos_verts = scale_verts(coords, model_file)
        face_hex = get_face_hex(faces_file, all_file_info)
        submeshes = get_submeshes(model_file, i, pos_verts, uv_verts, face_hex)
        first_mat = None
        submeshes_to_write = []
        for submesh in submeshes:
            # break
            if not first_mat:
                first_mat = submesh.material
            # if first_mat != submesh.material:
            #     break
            if any([x.lod_level == 0 for x in submeshes]):
                if submesh.lod_level == 0:
                    submeshes_to_write.append(submesh)
                    # write_submesh_fbx(submesh, temp_direc, model_file)
            else:
                submeshes_to_write.append(submesh)
        if lod:
            export_fbx(submeshes_to_write, model_file, pos_vert_file.uid, temp_direc, b_textures)
        else:
            export_fbx(submeshes, model_file, pos_vert_file.uid, temp_direc, b_textures)


# def scale_verts(verts_data, model_file):
#     return verts_data
#     pkg_name = gf.get_pkg_name(model_file)
#     model_hex = gf.get_hex_data(f'{test_dir}/{pkg_name}/{model_file}.bin')
#     # TODO fix this, this isn't correct but it is needed.
#     model_scale = [struct.unpack('f', bytes.fromhex(model_hex[j:j + 8]))[0] for j in range(0x70*2, (0x70+12)*2, 8)]
#
#     for i in range(len(verts_data)):
#         for j in range(3):
#             verts_data[i][j] *= model_scale[j]
#
#     return verts_data


def create_mesh(model, submesh: Submesh, name):
    mesh = fbx.FbxMesh.Create(model.scene, name)
    controlpoints = [fbx.FbxVector4(-x[0], x[2], x[1]) for x in submesh.pos_verts]
    for i, p in enumerate(controlpoints):
        mesh.SetControlPointAt(p, i)
    for face in submesh.faces:
        mesh.BeginPolygon()
        mesh.AddPolygon(face[0]-1)
        mesh.AddPolygon(face[1]-1)
        mesh.AddPolygon(face[2]-1)
        mesh.EndPolygon()

    # node = fbx.FbxNode.Create(d2map.fbx_model.scene, name)
    # node.SetNodeAttribute(mesh)

    return mesh


def create_uv(mesh, name, submesh: Submesh, layer):
    uvDiffuseLayerElement = fbx.FbxLayerElementUV.Create(mesh, f'diffuseUV {name}')
    uvDiffuseLayerElement.SetMappingMode(fbx.FbxLayerElement.eByControlPoint)
    uvDiffuseLayerElement.SetReferenceMode(fbx.FbxLayerElement.eDirect)
    # mesh.InitTextureUV()
    for i, p in enumerate(submesh.uv_verts):
        uvDiffuseLayerElement.GetDirectArray().Add(fbx.FbxVector2(p[0], p[1]))
    layer.SetUVs(uvDiffuseLayerElement, fbx.FbxLayerElement.eTextureDiffuse)
    return layer

# #
#
# def create_uv(mesh, name, submesh: met.Submesh, layer):
#     uvDiffuseLayerElement = fbx.FbxLayerElementUV.Create(mesh, f'diffuseUV {name}')
#     uvDiffuseLayerElement.SetMappingMode(fbx.FbxLayerElement.eByControlPoint)
#     uvDiffuseLayerElement.SetReferenceMode(fbx.FbxLayerElement.eDirect)
#     # mesh.InitTextureUV()
#     for i, p in enumerate(submesh.uv_verts):
#         uvDiffuseLayerElement.GetDirectArray().Add(fbx.FbxVector2(p[0], p[1]))
#     layer.SetUVs(uvDiffuseLayerElement, fbx.FbxLayerElement.eTextureDiffuse)
#     return layer


def export_all_models(pkg_name, all_file_info, select, lod):
    entries_type = {x: y for x, y in pkg_db.get_entries_from_table(pkg_name, 'FileName, FileType') if y == 'Dynamic Model Header 3'}
    for file in list(entries_type.keys()):
        # if file == '01B5-1666':
        #     a = 0
        print(f'Getting file {file}')
        get_model(file, all_file_info, lod, temp_direc=f'{select}/' + pkg_name)


if __name__ == '__main__':
    pkg_db.start_db_connection('3_0_1_3')
    all_file_info = {x[0]: dict(zip(['RefID', 'RefPKG', 'FileType'], x[1:])) for x in
                     pkg_db.get_entries_from_table('Everything', 'FileName, RefID, RefPKG, FileType')}
    # RefID 0x13A5, RefPKG 0x0003
    # parent_file = '023A-1DE0'
    # parent_file = '0234-16B2'
    # parent_file = '03B8-047B'
    # parent_file = '0157-04AA'  # Moonfang Grips
    # parent_file = '0157-06A4'  # Moonfang rig
    # parent_file = '0156-1E0A'  # Cinderpinion bios
    parent_file = '01B6-0C48'  # Wyvern
    # parent_file = '0148-08A0'  # Uldren cinematic
    # parent_file = '01BC-17FB'  # Vex harpy
    parent_file = '01E2-1347'  # type 3 stride 4
    parent_file = '01E2-1335'  # type 3 stride 8
    parent_file = '01E5-16A5'  # splicer vandaal thing
    parent_file = '0157-048E'  # mask of bakris
    parent_file = '0157-0801'  # cinderpinion vest
    # parent_file = gf.get_file_from_hash('17B8B580')
    # get_model(parent_file, all_file_info)
    # parent_file = '0361-0012'
    # parent_file = '020E-1F9C'l
    # parent_file = '01FE-054A'
    # parent_file = get_file_from_hash(get_flipped_hex('1A20EC80', 8))
    # print(parent_file)
    # parent_file = '0378-03E5'
    get_model(parent_file, all_file_info, lod=True, textures=True)
    quit()
    select = 'combatants'
    folder = select
    # folder = 'gambit'
    gf.mkdir(f'I:/dynamic_models/{folder}')
    for pkg in pkg_db.get_all_tables():
        if select in pkg:
            # if pkg not in os.listdir('C:/d2_model_temp/texture_models/tower'):
                export_all_models(pkg, all_file_info, folder, lod=True)
