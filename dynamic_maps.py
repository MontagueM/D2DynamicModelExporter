import gf
import pkg_db
import struct
import pyfbx_jo as pfb
import get_dynamic_model_textures as gdmt
import scipy.spatial
import fbx
import re
import zipfile
import os
import shutil


class DynamicModel:
    def __init__(self):
        self.location = []
        self.rotation = []
        self.scale = 0
        self.dyn1 = ''


def read_table(table_file):
    fb = open(f'I:/d2_output_3_1_0_0/{gf.get_pkg_name(table_file)}/{table_file}.bin', 'rb').read()
    count = gf.get_uint32(fb, 0x8)
    offset = 0x30
    dyns = []
    for i in range(offset, offset+count*144, 144):
        dyn = DynamicModel()
        dyn.rotation = [struct.unpack('f', fb[i+4*j:i+4*(j+1)])[0] for j in range(4)]
        dyn.location = [struct.unpack('f', fb[0x10+i+4*j:0x10+i+4*(j+1)])[0] for j in range(3)]
        dyn.scale = struct.unpack('f', fb[0x1C+i:0x1C+i+4])[0]
        if fb[i+0x30:i+0x38].hex().upper() == 'C59D1C81C59D1C81':
            continue
        try:
            dyn.dyn1 = gf.get_file_from_hash(hash64_table[fb[i+0x30:i+0x38].hex().upper()])
        except KeyError:
            print('Missing dynamic, skipping')
            continue
        dyns.append(dyn)
    return dyns


def get_map(table_file):
    dmap = pfb.Model()
    dyns = read_table(table_file)
    for dyn in dyns:
        dmap = add_model(dmap, dyn)
    export_fbx(dmap, table_file)


def export_dynamic_custom(table_file, name_arr, index):
    dyns = read_table(table_file)
    with open('I:/dynamic_models/mass_named_enemies/glb/data.txt', 'a') as q:
        for dyn in dyns:
            gdmt.get_model(dyn.dyn1, all_file_info, hash64_table, temp_direc=f'mass_named_enemies/{index}_{"_".join(name_arr)}', lod=True, b_textures=True,
                      b_apply_textures=False, b_shaders=False, passing_dyn3=False, b_skeleton=True,
                      obfuscate=True, b_collect_extra_textures=True)
            # with open(f'I:/dynamic_models/mass_named_enemies/{index}_{"_".join(name_arr)}/data.txt', 'w') as f:
            #     for x in name_arr:
            #         f.write(x)
            # Web-export

            # TODO CANNOT HAVE COLONS IN NAME
            direc = f'I:/dynamic_models/mass_named_enemies/{index}_{"_".join(name_arr)}'
            files = [x for x in os.listdir(direc) if '.fbx' in x]
            with zipfile.ZipFile(f'{direc}/{index}_{"_".join(name_arr)}.zip', 'w', zipfile.ZIP_DEFLATED) as myzip:
                for f in [x for x in os.listdir(direc) if '.tga' in x or '.fbx' in x]:
                    myzip.write(f'{direc}/{f}', f)
                for f in [x for x in os.listdir(direc + '/textures') if '.tga' in x or '.txt' in x]:
                    myzip.write(f'{direc + "/textures"}/{f}', 'textures/' + f)
                if os.path.isdir(direc + "/unk_textures"):
                    for f in [x for x in os.listdir(direc + "/unk_textures") if '.tga' in x or '.fbx' in x]:
                        myzip.write(f'{direc + "/unk_textures"}/{f}', 'unk_textures/' + f)
            for file in files:
                os.system(f'fbx2gltf.exe -e -i "{direc}/{file}" -o "{direc}/{file[:-4]}.glb" --compute-normals never --keep-attribute position')
                shutil.copyfile(f"{direc}/{file[:-4]}.glb", f"I:/dynamic_models/mass_named_enemies/glb/{index}_{'_'.join(name_arr)}.glb")
            [os.remove(f'{direc}/{x}') for x in os.listdir(direc) if '.tga' in x or '.fbx' in x]
            shutil.rmtree(f'{direc}/textures')
            if os.path.isdir(direc + "/unk_textures"):
                shutil.rmtree(f'{direc}/unk_textures')
            q.write(f"{index}_{'_'.join(name_arr)}.glb\n")



def rotate_verts(submesh, rotations, inverse=False):
    r = scipy.spatial.transform.Rotation.from_quat(rotations)
    if len(submesh.pos_verts) == 3:
        quat_rots = scipy.spatial.transform.Rotation.apply(r, submesh.pos_verts, inverse=inverse)
    else:
        quat_rots = scipy.spatial.transform.Rotation.apply(r, [[x[0], x[1], x[2]] for x in submesh.pos_verts], inverse=inverse)
    submesh.pos_verts = quat_rots.tolist()


def export_fbx(dmap, name):
    dmap.export(save_path=f'I:/dynamic_maps/{name}.fbx', ascii_format=False)


def get_map_scaled_verts(submesh, map_scaler):
    for i in range(len(submesh.pos_verts)):
        for j in range(3):
            submesh.pos_verts[i][j] *= map_scaler


def get_map_moved_verts(submesh, location):
    for i in range(len(submesh.pos_verts)):
        for j in range(3):
            submesh.pos_verts[i][j] += location[j]


def add_model(dmap, dyn):
    a = 0
    all_submeshes = gdmt.get_model(dyn.dyn1, all_file_info, hash64_table, temp_direc='NaeNae', lod=True, b_textures=False, b_apply_textures=False, b_shaders=False, passing_dyn3=False, b_skeleton=False, obfuscate=False, custom_export=dmap)
    if not all_submeshes:
        print('No submeshes')
        return dmap
    for x in all_submeshes:
        if not x:
            print('Submesh broken')
            continue
        # Modify the posvert stuff here
        for y in x:
            if not y:
                print('Submesh inner broken')
                continue
            if not y.pos_verts:
                print('No verts')
                continue
            rotate_verts(y, dyn.rotation)
            get_map_scaled_verts(y, dyn.scale)
            get_map_moved_verts(y, dyn.location)
            print(f'Added {dyn.dyn1} to map verts len {len(y.pos_verts)} loc {dyn.location}')
        # Add to fbx
        print(dmap.scene.GetRootNode().GetChildCount())
        # gdmt.add_to_fbx(dmap, [], x, dyn.dyn1 + str(random.randint(10, 999999)), dyn.dyn1 + str(random.randint(10, 999999)), 'NaeNae',
        #            False, False, False, '', False, {}, False,
        #            all_file_info, False, hash64_table)
        add_to_fbx(dmap, x)
    return dmap

def add_to_fbx(dmap, submeshes):
    for submesh in submeshes:
        mesh = create_mesh(dmap, submesh, 'blalal', '')
        if not mesh.GetLayer(0):
            mesh.CreateLayer()
        layer = mesh.GetLayer(0)
        node = fbx.FbxNode.Create(dmap.scene, submesh.name)
        node.SetNodeAttribute(mesh)
        node.LclScaling.Set(fbx.FbxDouble3(100, 100, 100))
        # if submesh.uv_verts:
        #     gdmt.create_uv(mesh, 'blala', submesh, layer)
        dmap.scene.GetRootNode().AddChild(node)


def create_mesh(model, submesh, name, skel_file):
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


def get_8E8E8080_table(table_file, export=False):
    dic = {}
    mainfb = open(f'I:/d2_output_3_1_0_0/{gf.get_pkg_name(table_file)}/{table_file}.bin', 'rb').read()
    find = [m.start() for m in re.finditer(b'\x48\x89\x80\x80', mainfb)]
    for o in find:
        count = gf.get_uint32(mainfb, o-8)
        # print('o', o-8, count, mainfb[o-8:o-4])
        o += 8
        for i in range(o, o+count*0x20, 0x20):
            # Getting string
            stroffset = gf.get_uint32(mainfb, i)
            string = ''
            k = 0
            while True:
                char = mainfb[i + stroffset + k]
                if char == 0:
                    break
                else:
                    string += chr(char)
                    k += 1
            dic[string] = []
            # Getting dynamic map
            f1 = gf.get_file_from_hash(mainfb[i+0x1C:i+0x1C+4].hex())
            print(string, f1)
            if string == 'enc_s13_presage_secret_start':
                a = 0
            fb1 = open(f'I:/d2_output_3_1_0_0/{gf.get_pkg_name(f1)}/{f1}.bin', 'rb').read()
            # Two files here, picking first for testing
            for f2 in [gf.get_file_from_hash(fb1[0x18:0x18+4].hex()), gf.get_file_from_hash(fb1[0x1C:0x1C+4].hex())]:
                fb2 = open(f'I:/d2_output_3_1_0_0/{gf.get_pkg_name(f2)}/{f2}.bin', 'rb').read()
                # Lots of files, picking first for testing
                count = gf.get_uint32(fb2, 0x30)
                for j in range(0x40, 0x40+count*4, 4):
                    f3 = gf.get_file_from_hash(fb2[j:j+4].hex())
                    # print(f3)
                    fb3 = open(f'I:/d2_output_3_1_0_0/{gf.get_pkg_name(f3)}/{f3}.bin', 'rb').read()

                    f4 = gf.get_file_from_hash(fb3[0x20:0x20+4].hex())
                    fb4 = open(f'I:/d2_output_3_1_0_0/{gf.get_pkg_name(f4)}/{f4}.bin', 'rb').read()
                    off1 = gf.get_uint32(fb4, 0x18) + 156
                    off2 = gf.get_uint32(fb4, 0x18) + 112
                    off3 = gf.get_uint32(fb4, 0x18) + 376
                    for off in [off1, off2, off3]:
                        if off+4 > len(fb4):
                            continue
                        f5 = gf.get_file_from_hash(fb4[off:off+4].hex())
                        if f5 in all_file_info.keys() and all_file_info[f5]['FileType'] == 'Dynamic Mapping Data' and f5 not in [x[0] for x in dic[string]]:
                            dic[string].append([f5, len(open(f'I:/d2_output_3_1_0_0/{gf.get_pkg_name(f5)}/{f5}.bin', 'rb').read())])

                    off1 = gf.get_uint32(fb4, 0x18) + 536
                    for off in [off1]:
                        if off+4 > len(fb4):
                            continue
                        h = fb4[off:off+8].hex().upper()
                        if h not in hash64_table:
                            continue
                        f5 = gf.get_file_from_hash(hash64_table[h])
                        if f5 in all_file_info.keys() and all_file_info[f5]['FileType'] == 'Dynamic Mapping Data' and f5 not in [x[0] for x in dic[string]]:
                            dic[string].append([f5, len(open(f'I:/d2_output_3_1_0_0/{gf.get_pkg_name(f5)}/{f5}.bin', 'rb').read())])

    [list(x).sort(key=lambda u: u[1]) for x in dic.values()]
    print([print(x, y) for x,y in dic.items()])
    if export:
        for x in dic[export]:
            get_map(x[0])





def get_all_named_maps(export):
    select = {x[0]: dict(zip(['Reference', 'FileType'], x[1:])) for x in
                     pkg_db.get_entries_from_table('sr_globals_011a', 'FileName, Reference, FileType')}
    name_dict = {}

    banned_words = [
        'Xander 99-40',
        'Petra Venj',
        'Cayde-6',
        'Ikora Rey',
        'Incoming Patrol…',
        'The Speaker',
        'To Tower Hangar',
        'Eva Levante',
        'Disciple of Osiris',
        'Dead Orbit',
        'Walker',
        'X\x19ûr'
    ]

    for file, data in select.items():
        if data['FileType'] != 'Dynamic Mapping Data':
            continue
        fb = open(f'I:/d2_output_3_1_0_0/{gf.get_pkg_name(file)}/{file}.bin', 'rb').read()
        possible_str = fb[0xEC:0xEC+4].hex().upper()
        if possible_str == '' or possible_str == '00000000' or possible_str == 'FFFFFFFF':
            continue
        for x, y in strings.items():
            if possible_str == x[8:]:
                # print(x, y, possible_str, file)
                # pkg_name = gf.get_pkg_name(gf.get_file_from_hash(x[:8]))
                # if pkg_name:
                #     if 'client_startup' not in pkg_name:
                #         continue
                # print(f'{possible_str} {y}: {file}')
                y = y.strip()
                if y in banned_words or y == '':
                    continue
                if file not in name_dict.keys():
                    name_dict[file] = set()
                name_dict[file].add(y)

    if export:
        c = 0
        for x, y in name_dict.items():
            export_dynamic_custom(x, y, c)
            c += 1
    else:
        [print(f'{x}: {y}') for x, y in name_dict.items()]


if __name__ == '__main__':
    version = '3_1_0_0'

    pkg_db.start_db_connection(f'C:/Users\monta\OneDrive\Destiny 2 Datamining\TextExtractor/db/{version}.db')
    strings = {x[0]: x[1] for x in pkg_db.get_entries_from_table('Everything', 'Hash, String')}

    pkg_db.start_db_connection(f'I:/d2_pkg_db/hash64/{version}.db')
    hash64_table = {x: y for x, y in pkg_db.get_entries_from_table('Everything', 'Hash64, Reference')}
    hash64_table['0000000000000000'] = 'FFFFFFFF'

    pkg_db.start_db_connection(f'I:/d2_pkg_db/{version}.db')
    all_file_info = {x[0]: dict(zip(['Reference', 'FileType'], x[1:])) for x in
                     pkg_db.get_entries_from_table('Everything', 'FileName, Reference, FileType')}

    # get_all_named_maps(export=False)
    get_map('02E6-0C7D')
    # get_8E8E8080_table('02E6-019B')#, export='enc_s13_presage_secret_start')
