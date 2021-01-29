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
import get_texture_plates as gtp
import get_skeleton
import hashlib
import image_extractor as imager  # Blender
import copy
import get_shader as shaders


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
        self.fb = None

    def get_file_from_uid(self):
        self.name = gf.get_file_from_hash(self.uid)
        return self.pkg_name

    def get_uid_from_file(self):
        self.uid = gf.get_hash_from_file(self.name)
        return self.pkg_name

    def get_pkg_name(self):
        self.pkg_name = gf.get_pkg_name(self.name)
        return self.pkg_name

    def get_fb(self):
        self.fb = open(f'I:/d2_output_3_0_2_0/{self.pkg_name}/{self.name}.bin', 'rb').read()


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
            if not pkg_name:
                return None
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


test_dir = 'I:/d2_output_3_0_2_0'
bad_files = []

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
    pkg_name = verts_file.pkg_name
    if not pkg_name:
        return None
    ref_file = gf.get_file_from_hash(all_file_info[verts_file.name]['Reference'])
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
        self.skin_buffer_data = []
        self.norm_verts = []
        self.uv_verts = []
        self.vert_colours = []
        self.weights = []
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
    # return verts_data
    all_v = []
    for face in faces_data:
        for v in face:
            all_v.append(v)
    return verts_data[min(all_v):max(all_v)+1]


def get_submeshes(file, index, pos_verts, uv_verts, weights, vert_colours, face_hex, jud_shader, obfuscate):
    # faces_ = faces
    # Getting the submesh table entries
    fbin = open(f'I:/d2_output_3_0_2_0/{gf.get_pkg_name(file)}/{file}.bin', 'rb').read()
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
        entry.GearDyeChangeColourIndex = fbin[i+0x1A]
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
        submesh.material = File(uid=binascii.hexlify(entry.Material).decode().upper())
        submesh.type = entry.PrimitiveType
        submesh.GearDyeChangeColourIndex = entry.GearDyeChangeColourIndex
        submesh.AlphaClip = entry.Flags & 0x8
        submesh.lod_level = entry.LODLevel
        submesh.name = f'{gf.get_hash_from_file(file)}_{i}_{submesh.lod_level}'
        if obfuscate:
            submesh.name = f'{str(hashlib.md5(gf.get_hash_from_file(file).encode()).hexdigest())[:8]}_{i}_{submesh.lod_level}'

        submeshes.append(submesh)

    faces, face_dict = get_faces(submeshes[0], face_hex, stride)

    # Removing duplicate submeshes
    # TODO This will need changing when materials get implemented
    existing = {}
    want_existing = True
    for submesh in list(submeshes):
        if submesh.entry.IndexOffset in existing.keys() and want_existing:
            if submesh.lod_level > existing[submesh.entry.IndexOffset]['LOD']:
                submeshes.remove(submesh)
                continue
            elif submesh.lod_level == existing[submesh.entry.IndexOffset]['LOD']:
                if existing[submesh.entry.IndexOffset]['Material'] == 'FFFFFFFF' and submesh.material.uid != 'FFFFFFFF':
                    # We want to replace the "best" model if the new one has a material and the old does not
                    existing[submesh.entry.IndexOffset]['Material'] = submesh.material.uid
                    submeshes.remove(existing[submesh.entry.IndexOffset]['self'])
                else:
                    submeshes.remove(submesh)
                    continue

        smfaces = get_submesh_faces(submesh, faces, face_dict)
        if not smfaces:
            continue
        submesh.pos_verts = trim_verts_data(pos_verts, smfaces)
        if uv_verts:
            submesh.uv_verts = trim_verts_data(uv_verts, smfaces)
        else:
            submesh.uv_verts = uv_verts

        if weights:
            submesh.weights = trim_verts_data(weights, smfaces)
        else:
            submesh.weights = []

        if vert_colours:
            submesh.vert_colours = trim_verts_data(vert_colours, smfaces)
            # print('Vert colours true')
        elif jud_shader:
            vc = [0, 0, 0, 1]
            if submesh.GearDyeChangeColourIndex == 0:
                vc[0] = 0.333
            elif submesh.GearDyeChangeColourIndex == 1:
                vc[0] = 0.666
            elif submesh.GearDyeChangeColourIndex == 2:
                vc[0] = 0.999
            elif submesh.GearDyeChangeColourIndex == 3:
                vc[1] = 0.333
            elif submesh.GearDyeChangeColourIndex == 4:
                vc[1] = 0.666
            elif submesh.GearDyeChangeColourIndex == 5:
                vc[1] = 0.999

            if submesh.AlphaClip != 0:
                vc[2] = 0.25
            submesh.vert_colours = [vc for x in range(len(submesh.pos_verts))]
            a = 0
        alt = shift_faces_down(smfaces)
        submesh.faces = alt
        # submesh.faces = smfaces
        existing[submesh.entry.IndexOffset] = {'LOD': submesh.lod_level, 'Material': submesh.material.uid, 'self': submesh}

    return submeshes


def get_faces(submesh: Submesh, faces_hex, stride):
    # 3 is triangles, 5 is triangle strip
    increment = 3
    face_dict = {}
    if stride == 8:
        int_faces_data = [int(gf.get_flipped_hex(faces_hex[i:i + 8], 8), 16) for i in
                           range(0, len(faces_hex), 8)]
    else:
        int_faces_data = [int(gf.get_flipped_hex(faces_hex[i:i + 4], 4), 16) for i in
                           range(0, len(faces_hex), 4)]
    if submesh.type == 5:
        increment = 1

    faces = []
    j = 0
    face_index = 0
    while True:
        if face_index >= len(int_faces_data) - 2 and submesh.type == 5:
            face_dict[face_index] = len(faces) - 1
            if face_index == len(int_faces_data):
                face_dict[face_index+1] = len(faces) - 1
                break
            face_index += 1
            continue
        elif face_index == len(int_faces_data) and submesh.type == 3:
            face_dict[face_index] = len(faces) - 1
            break
        if 65535 in int_faces_data[face_index:face_index+3] or 4294967295 in int_faces_data[face_index:face_index+3]:
            j = 0
            face_dict[face_index] = len(faces) - 1
            face_index += increment
            continue

        if submesh.type == 3 or j % 2 == 0:
            face = int_faces_data[face_index:face_index+3]
        else:
            face = [int_faces_data[face_index+1], int_faces_data[face_index+0], int_faces_data[face_index+2]]
        faces.append(face)
        face_dict[face_index] = len(faces) - 1
        face_index += increment
        j += 1
    return faces, face_dict


def scale_and_repos_pos_verts(verts_data, fbin, dyn2_index):
    scale = struct.unpack('f', fbin[108:108 + 4])[0]
    for i in range(len(verts_data)):
        for j in range(3):
            verts_data[i][j] *= scale

    position_shift = [struct.unpack('f', fbin[96 + 4 * i:96 + 4 * (i + 1)])[0] for i in range(3)]
    for i in range(3):
        for j in range(len(verts_data)):
            if dyn2_index != 0:  # Cloth meshes, stored in sec and tri dyns, have a modified pos shift
                verts_data[j][i] += position_shift[i]
            else:
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


def export_fbx(b_temp_direc_full, model, temp_direc, model_file, obfuscate):
    if obfuscate:
        model_file = str(hashlib.md5(model_file.encode()).hexdigest())[:8]
    if b_temp_direc_full:
        model.export(save_path=f'{temp_direc}/{model_file}.fbx', ascii_format=False)
    else:
        if temp_direc or temp_direc != '':
            gf.mkdir(f'I:/dynamic_models/{temp_direc}/')
        # gf.mkdir(f'P:/old_processed/{version_str}_dynamics/{temp_direc}/{model_file}')
        model.export(save_path=f'I:/dynamic_models/{temp_direc}/{model_file}.fbx', ascii_format=False)
    print(f'Written I:/dynamic_models/{temp_direc}/{model_file}.fbx.')


def add_vert_colours(mesh, name, submesh: Submesh, layer):
    vertColourElement = fbx.FbxLayerElementVertexColor.Create(mesh, f'colour')
    vertColourElement.SetMappingMode(fbx.FbxLayerElement.eByControlPoint)
    vertColourElement.SetReferenceMode(fbx.FbxLayerElement.eDirect)
    # mesh.InitTextureUV()
    for i, p in enumerate(submesh.vert_colours):
        # vertColourElement.GetDirectArray().Add(fbx.FbxColor(p[0], p[1], p[2], 1))
        vertColourElement.GetDirectArray().Add(fbx.FbxColor(p[0], p[1], p[2], p[3]))

    layer.SetVertexColors(vertColourElement)


def add_weights(model, mesh, name, weights_arrs, bones):
    skin = fbx.FbxSkin.Create(model.scene, name)
    bone_cluster = []
    for bone in bones:
        def_cluster = fbx.FbxCluster.Create(model.scene, 'BoneWeightCluster')
        def_cluster.SetLink(bone.fbxnode)
        def_cluster.SetLinkMode(fbx.FbxCluster.eTotalOne)
        bone_cluster.append(def_cluster)

        transform = bone.fbxnode.EvaluateGlobalTransform()
        def_cluster.SetTransformLinkMatrix(transform)

    for i, w in enumerate(weights_arrs):
        indices = w[0]
        weights = w[1]
        for j in range(len(indices)):
            if len(bone_cluster) < indices[j]:
                print('Bone index longer than bone clusters, could not add weights')
                return
            bone_cluster[indices[j]].AddControlPointIndex(i, weights[j])
            # print(f'Adding weight of {weights[j]} to bone {bones[indices[j]].name}')
            # if weights[j] == 176 and bones[indices[j]].name == 'b_pelvis':
            #     a = 0
        # print('\n')

    for c in bone_cluster:
        skin.AddCluster(c)

    mesh.AddDeformer(skin)


def apply_diffuse(model, submesh, node, name, temp_direc, b_temp_direc_full):
    # print('applying diffuse', tex_name)
    lMaterialName = f'mat texplate_diffuse'
    lMaterial = fbx.FbxSurfacePhong.Create(model.scene, lMaterialName)
    lMaterial.DiffuseFactor.Set(1)
    lMaterial.ShadingModel.Set('Phong')
    node.AddMaterial(lMaterial)

    gTexture = fbx.FbxFileTexture.Create(model.scene, f'Diffuse Texture texplate_diffuse')
    # lTexPath = f'C:/d2_maps/{folder_name}_fbx/textures/{tex_name}.tga'
    if b_temp_direc_full:
        lTexPath = f'{temp_direc}/textures/{submesh.diffuse}.tga'
    else:
        lTexPath = f'I:/dynamic_models/{temp_direc}/textures/{submesh.diffuse}.tga'
    # print('tex path', f'C:/d2_maps/{folder_name}_fbx/textures/{tex_name}.tga')
    gTexture.SetFileName(lTexPath)
    gTexture.SetRelativeFileName(lTexPath)
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


def get_submesh_faces(submesh, faces, face_dict):
    if submesh.type == 5:
        io = face_dict[submesh.entry.IndexOffset]
        ic = face_dict[submesh.entry.IndexOffset+submesh.entry.IndexCount+1]
    elif submesh.type == 3:
        try:
            io = face_dict[submesh.entry.IndexOffset]
            ic = face_dict[submesh.entry.IndexOffset+submesh.entry.IndexCount]
        except KeyError:
            print('KEY ERROR')
            return None
    # a = faces[io:ic]
    # if not a:
    #     k = 0
    return copy.deepcopy(faces[io:ic])


def get_face_hex(faces_file, all_file_info) -> str:
    try:
        ref_file = gf.get_file_from_hash(all_file_info[faces_file.name]['Reference'])
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


def get_verts_faces_files(model_file):
    pos_verts_files = []
    uv_verts_files = []
    faces_files = []
    original_weight_files = []
    skin_buffer_files = []
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
            # if hsh != 'FFFFFFFF':
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
            elif j == 16:
                hf.header = hf.get_header()
                original_weight_files.append(hf)
            elif j == 32:
                faces_files.append(hf)
            elif j == 48:
                skin_buffer_files.append(hf)
                break
    # print(pos_verts_files, uv_verts_files)
    return pos_verts_files, uv_verts_files, faces_files, skin_buffer_files, original_weight_files


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
            faces_data[i][j] -= a_min
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


def get_model(parent_file, all_file_info, hash64_table, temp_direc='', lod=True, b_textures=False, b_temp_direc_full=False, obfuscate=False, b_apply_textures=False, passing_dyn3=False, b_skeleton=False, from_api=False, b_shaders=False, jud_shader=False, custom_export=False):
    b_verbose = True
    if custom_export:
        model = custom_export
    else:
        model = pfb.Model()
    model_files = []
    existing_mats = {}
    all_submeshes = []
    if passing_dyn3:
        model_file = parent_file
        skel_file = ''
        fbdyn3 = open(f'I:/d2_output_3_0_2_0/{gf.get_pkg_name(model_file)}/{model_file}.bin', 'rb').read()
        # print(f'Parent file {model_file}')
        gf.mkdir(f'I:/dynamic_models/{temp_direc}/')
        gf.mkdir(f'I:/dynamic_models/{temp_direc}/textures/')
        pos_verts_files, uv_verts_files, faces_files, skin_buffer_files, og_weight_files = get_verts_faces_files(
            model_file)

        if skel_file:
            bones = add_skeleton(model, skel_file)
        else:
            bones = []

        for i, pos_vert_file in enumerate(pos_verts_files):
            weights = []
            vert_colours = []
            uv_verts = []
            faces_file = faces_files[i]
            pos_verts = get_verts_data(pos_vert_file, all_file_info, is_uv=False)

            pos_verts = scale_and_repos_pos_verts(pos_verts, fbdyn3, None)
            if uv_verts_files[i].uid != 'FFFFFFFF':
                uv_verts = get_verts_data(uv_verts_files[i], all_file_info, is_uv=True)
                uv_verts = scale_and_repos_uv_verts(uv_verts, fbdyn3)

            if og_weight_files[i].uid != 'FFFFFFFF':
                weights = get_og_weights(all_file_info, og_weight_files[i])
            elif skin_buffer_files[i].uid != 'FFFFFFFF':
                weights = parse_skin_buffer(pos_vert_file, all_file_info, skin_buffer_files[i])
            else:
                if b_verbose:
                    print('No weights')


            face_hex = get_face_hex(faces_file, all_file_info)
            submeshes = get_submeshes(model_file, i, pos_verts, uv_verts, weights, vert_colours, face_hex, jud_shader, obfuscate)
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
                else:
                    submeshes_to_write.append(submesh)
            if not custom_export:
                if lod:
                    add_to_fbx(model, bones, submeshes_to_write, parent_file, pos_vert_file.uid.upper(), temp_direc,
                               b_temp_direc_full, b_apply_textures, b_textures, skel_file, obfuscate, existing_mats,
                               b_shaders, all_file_info, b_verbose, hash64_table)
                else:
                    add_to_fbx(model, bones, submeshes_to_write, parent_file, pos_vert_file.uid.upper(), temp_direc,
                               b_temp_direc_full, b_apply_textures, b_textures, skel_file, obfuscate, existing_mats,
                               b_shaders, all_file_info, b_verbose, hash64_table)
        model_files.append(model_file)
    else:
        fbdyn1 = open(f'I:/d2_output_3_0_2_0/{gf.get_pkg_name(parent_file)}/{parent_file}.bin', 'rb').read()
        skel_file = gf.get_file_from_hash(bytes.hex(fbdyn1[0xB0:0xB0+4]))
        dyn2_primary = gf.get_file_from_hash(bytes.hex(fbdyn1[0xBC:0xBC + 4]))
        skel = open(f'I:/d2_output_3_0_2_0/{gf.get_pkg_name(skel_file)}/{skel_file}.bin', 'rb').read()
        if b'\x42\x86\x80\x80' not in skel:  # Using default player skeleton
            dyn2_primary = skel_file
            skel_file = '0186-138F'
        if not b_skeleton:
            skel_file = ''

        if from_api:
            dyn2_secondary = gf.get_file_from_hash(bytes.hex(fbdyn1[0xBC:0xBC+4]))  # Do we need to modify dyn2_prim as its the same here for api stuff?
        else:
            dyn2_secondary = ''
        dyn2_ternary = gf.get_file_from_hash(bytes.hex(fbdyn1[0xC8:0xC8+4]))

        gf.mkdir(f'I:/dynamic_models/{temp_direc}/')
        gf.mkdir(f'I:/dynamic_models/{temp_direc}/textures/')
        for d, dyn2 in enumerate([dyn2_primary, dyn2_secondary, dyn2_ternary]):
            if not dyn2 or dyn2 not in all_file_info.keys() or dyn2 == '0400-0000':
                if b_verbose:
                    print('Model file empty')
                continue
            fbdyn2 = open(f'I:/d2_output_3_0_2_0/{gf.get_pkg_name(dyn2)}/{dyn2}.bin', 'rb').read()
            offset = gf.get_uint16(fbdyn2, 0x18) + 572
            if offset+4 > len(fbdyn2):
                if b_verbose:
                    print('Model file empty')
                continue
            model_file = gf.get_file_from_hash(bytes.hex(fbdyn2[offset:offset + 4]))
            if model_file not in all_file_info.keys() or model_file == '0400-0000':
                if b_verbose:
                    print('Model file empty')
                continue
            if all_file_info[model_file]['FileType'] != 'Dynamic Model Header 3':
                if b_verbose:
                    print('Model file empty')
                continue
            fbdyn3 = open(f'I:/d2_output_3_0_2_0/{gf.get_pkg_name(model_file)}/{model_file}.bin', 'rb').read()
            if b_verbose:
                print(f'Dyn3 {model_file}')
            pos_verts_files, uv_verts_files, faces_files, skin_buffer_files, og_weight_files = get_verts_faces_files(model_file)

            if skel_file:
                bones = add_skeleton(model, skel_file)
            else:
                bones = []

            for i, pos_vert_file in enumerate(pos_verts_files):
                weights = []
                vert_colours = []
                uv_verts = []
                faces_file = faces_files[i]
                pos_verts = get_verts_data(pos_vert_file, all_file_info, is_uv=False)

                pos_verts = scale_and_repos_pos_verts(pos_verts, fbdyn3, d)
                if uv_verts_files[i].uid != 'FFFFFFFF':
                    uv_verts = get_verts_data(uv_verts_files[i], all_file_info, is_uv=True)
                    uv_verts = scale_and_repos_uv_verts(uv_verts, fbdyn3)

                if og_weight_files[i].uid != 'FFFFFFFF':
                    weights = get_og_weights(all_file_info, og_weight_files[i])
                elif skin_buffer_files[i].uid != 'FFFFFFFF':
                    weights = parse_skin_buffer(pos_vert_file, all_file_info, skin_buffer_files[i])
                else:
                    if b_verbose:
                        print('No weights')

                face_hex = get_face_hex(faces_file, all_file_info)
                submeshes = get_submeshes(model_file, i, pos_verts, uv_verts, weights, vert_colours, face_hex, jud_shader, obfuscate)
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
                    elif any([x.lod_level == 1 for x in submeshes]):
                        if submesh.lod_level == 1:
                            submeshes_to_write.append(submesh)
                    else:
                        submeshes_to_write.append(submesh)
                # if d == dyn2_secondary:  #  TODO implement
                #     merge_submeshes()
                if not custom_export:
                    if lod:
                        add_to_fbx(model, bones, submeshes_to_write, parent_file, pos_vert_file.uid.upper(), temp_direc, b_temp_direc_full, b_apply_textures, b_textures, skel_file, obfuscate, existing_mats, b_shaders, all_file_info, b_verbose, hash64_table)
                    else:
                        add_to_fbx(model, bones, submeshes_to_write, parent_file, pos_vert_file.uid.upper(), temp_direc, b_temp_direc_full, b_apply_textures, b_textures, skel_file, obfuscate, existing_mats, b_shaders, all_file_info, b_verbose, hash64_table)
                all_submeshes.append(submeshes_to_write)
            model_files.append(model_file)
    if model_files:
        # if b_collect_extra_textures:
        #     if b_verbose:
        #         print('Collecting extra textures...')
        #     collect_extra_textures(open(f'I:/d2_output_3_0_2_0//{gf.get_pkg_name(dyn2_primary)}/{dyn2_primary}.bin', 'rb').read(), temp_direc, b_verbose)
        if not custom_export:
            export_fbx(b_temp_direc_full, model, temp_direc, parent_file, obfuscate)
        else:
            return all_submeshes


def get_og_weights(all_file_info, og_weight_file):
    weights_pairs = []
    ref_file = gf.get_file_from_hash(all_file_info[og_weight_file.name]['Reference'])
    fb = open(f'I:/d2_output_3_0_2_0/{gf.get_pkg_name(ref_file)}/{ref_file}.bin', 'rb').read()
    for i in range(0, len(fb), 8):
        weights = [x/255 for x in fb[i:i+4]]
        weight_indices = [x for x in fb[i+4:i + 8] if x != 254]
        weights = weights[:len(weight_indices)]
        weights_pairs.append([weight_indices, weights])
    return weights_pairs


def add_to_fbx(model, bones, submeshes, parent_file, name, temp_direc, b_temp_direc_full, b_apply_textures, b_textures, skel_file, obfuscate, existing_mats, b_shaders, all_file_info, b_verbose, hash64_table):
    if obfuscate:
        name = str(hashlib.md5(name.encode()).hexdigest())[:8]

    if b_textures:
        save_texture_plates(parent_file, all_file_info, temp_direc, b_temp_direc_full, submeshes, obfuscate, b_verbose, b_apply_textures)


    for submesh in submeshes:
        mesh = create_mesh(model, submesh, name, skel_file)
        if not mesh.GetLayer(0):
            mesh.CreateLayer()
        layer = mesh.GetLayer(0)
        node = fbx.FbxNode.Create(model.scene, submesh.name)
        node.SetNodeAttribute(mesh)
        node.LclScaling.Set(fbx.FbxDouble3(100, 100, 100))

        if submesh.uv_verts:
            create_uv(mesh, parent_file, submesh, layer)
        if submesh.vert_colours:
            add_vert_colours(mesh, parent_file, submesh, layer)

        if submesh.material.uid != 'FFFFFFFF':
            if b_shaders or b_textures:
                try_get_material_textures(submesh, temp_direc, b_apply_textures, hash64_table, all_file_info)

            if b_shaders:
                apply_shader(existing_mats, model, submesh, node, temp_direc, all_file_info)
                print(f'submesh {name} has mat file {submesh.material.name} with textures {submesh.textures}')
                get_shader_info(submesh, temp_direc)

            if b_textures and submesh.diffuse:
                apply_diffuse(model, submesh, node, name, temp_direc, b_temp_direc_full)
                node.SetShadingMode(fbx.FbxNode.eTextureShading)

        model.scene.GetRootNode().AddChild(node)

        if skel_file and submesh.weights and bones:
            add_weights(model, mesh, name, submesh.weights, bones)


def apply_shader(existing_mats, model, submesh: Submesh, node, temp_direc, all_file_info):
    submesh.material.get_file_from_uid()
    lMaterialName = submesh.material.name
    if lMaterialName in existing_mats.keys():
        node.AddMaterial(existing_mats[lMaterialName])
        return
    lMaterial = fbx.FbxSurfacePhong.Create(model.scene, lMaterialName)
    existing_mats[lMaterialName] = lMaterial
    lMaterial.ShadingModel.Set('Phong')
    node.AddMaterial(lMaterial)


def get_shader_info(submesh, temp_direc):
        cbuffer_offsets, texture_offset = get_mat_tables(submesh.material)
        if not texture_offset:
            return
        shaders.get_shader_from_mat(submesh.material, submesh.textures, cbuffer_offsets, all_file_info, f'I:/dynamic_models/{temp_direc}/shaders/')


def get_material_textures(material, texture_offset, hash64_table, all_file_info, custom_dir):
    material.get_pkg_name()
    material.get_fb()
    texture_offset += 8
    if texture_offset == 15:
        return []
    count = gf.get_uint32(material.fb, texture_offset-8)
    # Arbritrary
    if count < 0 or count > 100:
        return []
    # image_indices = [gf.get_file_from_hash(material.fhex[texture_offset+16+8*(2*i):texture_offset+16+8*(2*i)+8]) for i in range(count)]
    images = [gf.get_file_from_hash(hash64_table[material.fb[texture_offset+8+0x10+24*i:texture_offset+8+0x10+24*i+8].hex().upper()]) for i in range(count)]
    if len(images) == 0:
        return []
    for img in images:
        if custom_dir:
            gf.mkdir(f'{custom_dir}/')
            if not os.path.exists(f'{custom_dir}/{img}.tga'):
                if img == 'FBFF-1FFF':
                    continue
                imager.get_image_from_file(f'I:/d2_output_3_0_2_0/{gf.get_pkg_name(img)}/{img}.bin', all_file_info, f'{custom_dir}/')
    return images


def get_mat_tables(material):
    if material.name == 'FBFF-1FFF':
        return None, None
    material.get_pkg_name()
    material.get_fb()
    cbuffers = []
    textures = -1

    texture_offset = 0x2A8
    table_offset = texture_offset + gf.get_uint32(material.fb, texture_offset)
    # table_count = int(gf.get_flipped_hex(material.fhex[table_offset:table_offset+8], 8), 16)
    table_type = material.fb[table_offset + 8:table_offset + 12]
    if table_type == b'\xCF\x6D\x80\x80':
        textures = table_offset

    start_offset = 0x2C0
    for i in range(6):
        current_offset = start_offset + 16*i
        table_offset = current_offset + gf.get_uint32(material.fb, current_offset)
        # table_count = int(gf.get_flipped_hex(material.fhex[table_offset:table_offset+8], 8), 16)
        table_type = material.fb[table_offset+8:table_offset+12]
        if table_type == b'\x90\x00\x80\x80':
            cbuffers.append(table_offset)

    # if textures == -1:
    #     raise Exception('Texture offset incorrect')

    return cbuffers, textures



def try_get_material_textures(submesh, temp_direc, b_apply_textures, hash64_table, all_file_info):
    if submesh.material.uid == 'FFFFFFFF':
        with open(f'I:/dynamic_models/{temp_direc}/textures/tex.txt', 'a') as f:
            f.write(f'Submesh {submesh.name} textures: no material\n')
        return
    submesh.material.get_file_from_uid()
    submesh.material.get_pkg_name()
    submesh.material.get_fb()

    file = submesh.material.name
    offset = submesh.material.fb.find(b'\xCF\x6D\x80\x80')

    if offset == -1:
        with open(f'I:/dynamic_models/{temp_direc}/textures/tex.txt', 'a') as f:
            f.write(f'Submesh {submesh.name} textures: no textures in material\n')
        return
    count = gf.get_uint32(submesh.material.fb, offset-8)
    # Arbritrary
    if count <= 0 or count > 100:
        return
    if b'\xFF\xFF\xFF\xFF' in submesh.material.fb[offset+0x10:offset+0x10+24*count]:  # Uses new texture system
        submesh.textures = [x for x in [gf.get_file_from_hash(hash64_table[submesh.material.fb[offset + 8 + 0x10 + 24 * i:offset + 8 + 0x10 + 24 * i + 8].hex().upper()]) for i in range(count)] if x != 'FBFF-1FFF']
    else:
        submesh.textures = [x for x in [gf.get_file_from_hash(submesh.material.fb[offset + 0x10 + 24 * i:offset + 0x10 + 24 * i + 4].hex().upper()) for i in range(count)] if x != 'FBFF-1FFF']

    # image_indices = [gf.get_file_from_hash(submesh.material.fhex[offset+16+8*(2*i):offset+16+8*(2*i)+8]) for i in range(count)]
    with open(f'I:/dynamic_models/{temp_direc}/textures/tex.txt', 'a') as f:
        f.write(f'Submesh {submesh.name} textures: {submesh.textures}\n')
    # if not submesh.diffuse:  # Not sure on this, causes a lot of things to break
    if b_apply_textures:
        submesh.diffuse = submesh.textures[0]
    for img in submesh.textures:
        if img == 'FBFF-1FFF':
            continue
        # if not os.path.exists(f'I:/dynamic_models/{temp_direc}/textures/{img}.dds'):
        if not os.path.exists(f'I:/dynamic_models/{temp_direc}/textures/{img}.tga'):
        # imager.get_image_from_file(f'I:/d2_output_3_0_2_0//{gf.get_pkg_name(img)}/{img}.bin', all_file_info, f'I:/dynamic_models/{temp_direc}/textures/{img}.dds')
            imager.get_image_from_file(f'I:/d2_output_3_0_2_0//{gf.get_pkg_name(img)}/{img}.bin', all_file_info, f'I:/dynamic_models/{temp_direc}/textures/')


def parse_skin_buffer(verts_file, all_file_info, skin_file):
    if not skin_file:# or True:
        return

    out_weights = []
    ref_file = gf.get_file_from_hash(all_file_info[verts_file.name]['Reference'])
    verts_fb = open(f'I:/d2_output_3_0_2_0/{gf.get_pkg_name(ref_file)}/{ref_file}.bin', 'rb').read()
    verts_w = [int.from_bytes(verts_fb[i:i + 2], byteorder='little', signed=True) for i in
               range(0, len(verts_fb), 2) if i % 24 == 6]

    ref_file = gf.get_file_from_hash(all_file_info[skin_file.name]['Reference'])
    skin_fb = open(f'I:/d2_output_3_0_2_0/{gf.get_pkg_name(ref_file)}/{ref_file}.bin', 'rb').read()
    skin_data = {}
    k = 0
    if skin_fb and any([x & 0xf800 != 0 for x in verts_w]):  # Checking if the whole file is just a header or not
        is_header = False
        past_header = False
        chunk_weight = 0
        weight_offset = 0
        for i in range(0, len(skin_fb), 4):
            skin_vertex = gf.get_uint32(skin_fb, i)

            index0 = skin_vertex & 0xff
            index1 = (skin_vertex >> 8) & 0xff
            weight0 = (skin_vertex >> 16) & 0xff
            weight1 = (skin_vertex >> 24) & 0xff

            if chunk_weight == 0:
                weight_offset = i

            chunk_index = int(weight_offset / 4)
            stride_index = int(i / 4)

            if stride_index not in skin_data.keys():
                skin_data[stride_index] = {
                    'index': k,
                    'stride_index': stride_index,
                    'count': 0,
                    'indices': [],
                    'weights': [],
                }
            chunk_data = skin_data[chunk_index]

            if is_header and i % 32 != 0 and not past_header:
                continue
            if (index0 == weight0 or index1 == weight1) and not past_header:
                is_header = True
                continue
            else:
                past_header = True
            # if is_header:
            #     skin_header = [index0, index1, weight0, weight1]  # We want to skip ahead 8 here as its useless
            #     # k += 1
            #     # continue
            if skin_vertex == 0:
                pass
            else:
                for w in [weight0, weight1]:
                    if w > 0:
                        chunk_data['count'] += 1
                    chunk_weight += w

                if not chunk_data['indices']:
                    chunk_data['indices'] = [index0, index1]
                    chunk_data['weights'] = [weight0/255, weight1/255]
                else:
                    chunk_data['indices'].extend([index0, index1])
                    chunk_data['weights'].extend([weight0/255, weight1/255])
                if chunk_weight == 255:
                    chunk_weight = 0
                    k += 1
                elif chunk_weight > 255:  # We're in the header. We re-enable the header check.
                    raise Exception('Weights > 255')

    # with open('skeltdyn.txt', 'w') as f:
    #     for x, y in skin_data.items():
    #         f.write(f'{y}\n')

    last_blend_value = 0
    last_blend_count = 0
    for i, w in enumerate(verts_w):
        indices = [0, 0, 0, 0]
        weights = [1, 0, 0, 0]

        blend_index = w & 0x7ff
        blend_flags = w & 0xf800

        buffer_size = 0

        if blend_flags & 0x8000:
            blend_index = abs(w) - 2048
            buffer_size = 4
        elif blend_flags == 0x800:
            buffer_size = 2
        elif blend_flags & 0x1000:
            buffer_size = 2
            blend_index = abs(w) - 2048
        elif blend_flags == 0:
            indices[0] = blend_index
        else:
            raise Exception('Unk flag used in skin buffer')
            # raise Exception('Incorrect skin data')

        blend_count = 0
        if buffer_size > 0:
            if last_blend_value != blend_index:
                last_blend_count = 0
            last_blend_value = blend_index

            blend_data = skin_data[blend_index * 8 + last_blend_count]
            while blend_data['count'] == 0:
                last_blend_count += 1
                blend_data = skin_data[blend_index * 8 + last_blend_count]

            total_bones = blend_data['count']
            for i in range(blend_data['count']):
                indices[i] = blend_data['indices'][i]
                weights[i] = blend_data['weights'][i]

            if total_bones > 2:
                blend_count = 2
            else:
                blend_count = 1

        last_blend_count += blend_count

        out_weights.append([[x for x in indices if x != 0], [x for x in weights if x != 0]])

    return out_weights


def add_skeleton(model, skel_file):
    # skel_file = '01E4-1283'
    names = get_skeleton.get_skeleton_names()
    nodes = get_skeleton.get_skeleton(skel_file, names)
    if not nodes:
        return
    bone_nodes = []
    # Write fbx skeleton bit
    for node in nodes:
        nodeatt = fbx.FbxSkeleton.Create(model.scene, node.name)
        if node.parent_node_index == -1:  # At root
            nodeatt.SetSkeletonType(fbx.FbxSkeleton.eRoot)
        elif node.first_child_node_index == -1:  # At end
            nodeatt.SetSkeletonType(fbx.FbxSkeleton.eLimbNode)
        else:  # In the middle somewhere
            nodeatt.SetSkeletonType(fbx.FbxSkeleton.eLimbNode)
        nodeatt.Size.Set(node.dost.scale)
        node.fbxnode = fbx.FbxNode.Create(model.scene, node.name)
        node.fbxnode.SetNodeAttribute(nodeatt)
        if node.parent_node_index != -1:  # To account for inheritance
            loc = [node.dost.location[i] - nodes[node.parent_node_index].dost.location[i] for i in range(3)]
        else:
            loc = node.dost.location
        node.fbxnode.LclTranslation.Set(fbx.FbxDouble3(-loc[0]*100, loc[2]*100, loc[1]*100))

        bone_nodes.append(node)
    # Building heirachy
    root = None
    for i, node in enumerate(nodes):
        if node.parent_node_index != -1:
            nodes[node.parent_node_index].fbxnode.AddChild(node.fbxnode)
            # print(f'{nodes[node.parent_node_index].hash} has child {node.hash}')
        else:
            root = node
        if root:
            model.scene.GetRootNode().AddChild(root.fbxnode)
    return bone_nodes


def save_texture_plates(dyn1, all_file_info, temp_direc, b_temp_direc_full, submeshes, obfuscate, b_verbose, b_apply_textures):
    texplateset = gtp.TexturePlateSet(dyn1, direct_from_tex=False)
    if not texplateset.plates:  # No tex plate
        print('No texture plate')
        return
    ret = texplateset.get_plate_set(all_file_info)
    if not ret:  # Is a tex plate but just nothing in it
        print('Nothing in texture plate')
        return

    if obfuscate:
        sn = str(hashlib.md5(dyn1.encode()).hexdigest())[:8]
    else:
        sn = gf.get_flipped_hex(gf.get_hash_from_file(dyn1), 8).upper()

    if b_verbose:
        print(texplateset.topfile, texplateset.plates['diffuse'].file, 'getting texplates')
    if b_temp_direc_full:
        texplateset.export_texture_plate_set(f'{temp_direc}/textures/')
    else:
        texplateset.export_texture_plate_set(f'I:/dynamic_models/{temp_direc}/textures/', altname=sn)

    if b_apply_textures:
        for s in submeshes:
            s.diffuse = f'{sn}_diffuse'


def create_mesh(model, submesh: Submesh, name, skel_file):
    mesh = fbx.FbxMesh.Create(model.scene, name)
    if skel_file:
        controlpoints = [fbx.FbxVector4(-x[0] * 100, x[2] * 100, x[1] * 100) for x in submesh.pos_verts]
    else:
        controlpoints = [fbx.FbxVector4(-x[0], x[2], x[1]) for x in submesh.pos_verts]
    for i, p in enumerate(controlpoints):
        mesh.SetControlPointAt(p, i)
    for face in submesh.faces:
        mesh.BeginPolygon()
        mesh.AddPolygon(face[0])
        mesh.AddPolygon(face[1])
        mesh.AddPolygon(face[2])
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


def export_all_models(pkg_name, all_file_info, select, lod_filter, b_textures, b_skeleton):
    entries_type = {x: y for x, y in pkg_db.get_entries_from_table(pkg_name, 'FileName, FileType') if y == 'Dynamic Model Header 1'}
    for file in list(entries_type.keys()):
        # if file == '01B5-1666':
        #     a = 0
        # if file + '.fbx' in os.listdir('I:/dynamic_models/activities'):
        #     continue
        print(f'Getting file {file}')
        get_model(file, all_file_info, hash64_table, lod=lod_filter, temp_direc=pkg_name, passing_dyn3=False, obfuscate=False,
                  b_apply_textures=b_textures,
                  b_shaders=False, b_textures=b_textures, b_skeleton=b_skeleton)


if __name__ == '__main__':
    version = '3_0_2_0'
    pkg_db.start_db_connection(f'I:/d2_pkg_db/hash64/{version}.db')
    hash64_table = {x: y for x, y in pkg_db.get_entries_from_table('Everything', 'Hash64, Reference')}
    hash64_table['0000000000000000'] = 'FFFFFFFF'

    pkg_db.start_db_connection(f'I:/d2_pkg_db/{version}.db')
    all_file_info = {x[0]: dict(zip(['Reference', 'FileType'], x[1:])) for x in
                     pkg_db.get_entries_from_table('Everything', 'FileName, Reference, FileType')}
    # Only dynamic model 1

    parent_file = '0157-0487'  # Bakris
    parent_file = '0170-0B97'  # Activity sword
    parent_file = '01B8-08C6'  # Atraks

    # parent_file = '0157-04BB'  # skel file 0186-138F moonfang grips
    parent_file = '01B8-08C6'  # skel file 0158-004C or maybe its 01B8-08D6 atraks
    parent_file = '0190-0AEB'  # frostreach

    parent_file = '01B8-0118'  # Riven

    # parent_file = '01B8-08C6'

    parent_file = '01B6-0C3A'  # wyvern, skel file 01C2-0AF7  ? 01B6-0C47

    parent_file = '0157-04BB'  # broken drifter (fixed)
    parent_file = '0159-0CB7'  # variks broken 4096
    parent_file = '01B5-10DB'  # unstoppable ogre broken 4096, old file is, skel file is '01B6-09D9' new,
    # parent_file = '01B5-14DA'  # unstoppable incendior cabal dude broken 4096, old file is
    # parent_file = '01B5-1602'  # barrier knight broken 4096
    # parent_file = '01B6-02A5'  # incendior shield with the broken back and '01B6-02A8' and 02b7 02ba 02dd
    # parent_file = '0158-052A'  # eris broken, new is 0158-052A dyn1, old is prob 0938-00B9

    parent_file = '01EA-1508'
    get_model(parent_file, all_file_info, hash64_table, temp_direc=parent_file, lod=True, b_textures=True, b_apply_textures=True, b_shaders=False, passing_dyn3=False, b_skeleton=False, obfuscate=False)
    quit()

    select = '0159'
    folder = select
    for pkg in pkg_db.get_all_tables():
        if select in pkg:
            gf.mkdir(f'I:/dynamic_models/{pkg}')
            # if pkg not in os.listdir('C:/d2_model_temp/texture_models/tower'):
            export_all_models(pkg, all_file_info, folder, lod_filter=True, b_textures=True, b_skeleton=True)

    print(bad_files)