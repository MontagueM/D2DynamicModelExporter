"""
- Export the full model with the hires texture plates
- Also export a model with the diffuse plate attached in GLTF
"""

import get_dynamic_model_textures as gdmt
import pkg_db
import gf
import os


def get_all_to_gltf(direc, b_textures):
    files = [x for x in os.listdir(direc) if '.fbx' in x]
    for file in files:
        os.system(f'fbx2gltf.exe --input {direc}/{file} --output {direc}/{file[:-4]}.glb')


if __name__ == '__main__':
    pkg_db.start_db_connection('3_0_1_3')
    all_file_info = {x[0]: dict(zip(['Reference', 'FileType'], x[1:])) for x in
                     pkg_db.get_entries_from_table('Everything', 'FileName, Reference, FileType')}

    helmets = {
        'bakris': '0157-0487',
        '': '',
    }

    for name, file in helmets.items():
        gf.mkdir(f'I:/d2/web_dyn/{name}')
        gdmt.get_model(file, all_file_info, lod=True, temp_direc=f'I:/d2/web_dyn/{name}', b_temp_direc_full=True,
                       b_textures=True, b_helmet=True)
        get_all_to_gltf(f'I:/d2/web_dyn/{name}', b_textures=True)
        break