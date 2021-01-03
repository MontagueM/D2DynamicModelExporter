"""
- Export the full model with the hires texture plates
- Also export a model with the diffuse plate attached in GLTF
"""

import get_dynamic_model_textures as gdmt
import pkg_db
import gf
import os


def get_gltf(direc, dyn1, b_textures):
    gdmt.get_model(dyn1, all_file_info, lod=True, temp_direc=f'I:/d2/web_dyn/{name}', b_temp_direc_full=True,
                   b_textures=b_textures, b_helmet=b_textures, b_apply_textures=b_textures)
    files = [x for x in os.listdir(direc) if '.fbx' in x]
    for file in files:
        os.system(f'fbx2gltf.exe -e -i {direc}/{file} -o {direc}/{file[:-4]}.glb')


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
        get_gltf(f'I:/d2/web_dyn/{name}', file, b_textures=True)
        # gdmt.get_model(file, all_file_info, lod=True, temp_direc=f'I:/d2/web_dyn/{name}', b_temp_direc_full=True,
        #                b_textures=False, b_helmet=False, b_apply_textures=False)  # Textures already pulled out
        break