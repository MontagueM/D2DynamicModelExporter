import gf
import pkg_db
import struct
import pyfbx_jo as pfb
import get_dynamic_model_textures as gdmt
import scipy.spatial
import fbx
import re


class DynamicModel:
    def __init__(self):
        self.location = []
        self.rotation = []
        self.scale = 0
        self.dyn1 = ''


def read_table(table_file):
    fb = open(f'I:/d2_output_3_0_2_0/{gf.get_pkg_name(table_file)}/{table_file}.bin', 'rb').read()
    count = gf.get_uint32(fb, 0x8)
    offset = 0x30
    dyns = []
    for i in range(offset, offset+count*144, 144):
        dyn = DynamicModel()
        dyn.rotation = [struct.unpack('f', fb[i+4*j:i+4*(j+1)])[0] for j in range(4)]
        dyn.location = [struct.unpack('f', fb[0x10+i+4*j:0x10+i+4*(j+1)])[0] for j in range(3)]
        dyn.scale = struct.unpack('f', fb[0x1C+i:0x1C+i+4])[0]
        dyn.dyn1 = gf.get_file_from_hash(hash64_table[fb[i+0x30:i+0x38].hex().upper()])
        dyns.append(dyn)
    return dyns


def get_map(table_file):
    dmap = pfb.Model()
    dyns = read_table(table_file)
    for dyn in dyns:
        dmap = add_model(dmap, dyn)
    export_fbx(dmap, table_file)


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


def get_8E8E8080_table(table_file):
    dic = {}
    mainfb = open(f'I:/d2_output_3_0_2_0/{gf.get_pkg_name(table_file)}/{table_file}.bin', 'rb').read()
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
            fb1 = open(f'I:/d2_output_3_0_2_0/{gf.get_pkg_name(f1)}/{f1}.bin', 'rb').read()
            # Two files here, picking first for testing
            for f2 in [gf.get_file_from_hash(fb1[0x18:0x18+4].hex()), gf.get_file_from_hash(fb1[0x1C:0x1C+4].hex())]:
                fb2 = open(f'I:/d2_output_3_0_2_0/{gf.get_pkg_name(f2)}/{f2}.bin', 'rb').read()
                # Lots of files, picking first for testing
                count = gf.get_uint32(fb2, 0x30)
                for j in range(0x40, 0x40+count*4, 4):
                    f3 = gf.get_file_from_hash(fb2[j:j+4].hex())
                    # print(f3)
                    fb3 = open(f'I:/d2_output_3_0_2_0/{gf.get_pkg_name(f3)}/{f3}.bin', 'rb').read()

                    f4 = gf.get_file_from_hash(fb3[0x20:0x20+4].hex())
                    fb4 = open(f'I:/d2_output_3_0_2_0/{gf.get_pkg_name(f4)}/{f4}.bin', 'rb').read()
                    off1 = gf.get_uint32(fb4, 0x18) + 156
                    off2 = gf.get_uint32(fb4, 0x18) + 112

                    for off in [off1, off2]:
                        f5 = gf.get_file_from_hash(fb4[off:off+4].hex())
                        if f5 in all_file_info.keys() and all_file_info[f5]['FileType'] == 'Dynamic Mapping Data' and f5 not in [x[0] for x in dic[string]]:
                            dic[string].append([f5, len(open(f'I:/d2_output_3_0_2_0/{gf.get_pkg_name(f5)}/{f5}.bin', 'rb').read())])

    [list(x).sort(key=lambda u: u[1]) for x in dic.values()]
    print([print(x, y) for x,y in dic.items()])


if __name__ == '__main__':
    version = '3_0_2_0'

    pkg_db.start_db_connection(f'I:/d2_pkg_db/hash64/{version}.db')
    hash64_table = {x: y for x, y in pkg_db.get_entries_from_table('Everything', 'Hash64, Reference')}
    hash64_table['0000000000000000'] = 'FFFFFFFF'

    pkg_db.start_db_connection(f'I:/d2_pkg_db/{version}.db')
    all_file_info = {x[0]: dict(zip(['Reference', 'FileType'], x[1:])) for x in
                     pkg_db.get_entries_from_table('Everything', 'FileName, Reference, FileType')}

    get_map('02AB-017F')
    # get_8E8E8080_table('02AC-1E10')
