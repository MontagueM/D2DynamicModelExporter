"""
- Export the full model with the hires texture plates
- Also export a model with the diffuse plate attached in GLTF
"""

import get_dynamic_model_textures as gdmt
import pkg_db
import gf
import os
import zipfile


def get_gltf(direc, name, dyn1, b_textures):
    gdmt.get_model(dyn1, all_file_info, lod=True, temp_direc=f'I:/d2/web_dyn/{name}', b_temp_direc_full=True,
                   b_textures=b_textures, b_helmet=b_textures, b_apply_textures=b_textures)
    files = [x for x in os.listdir(direc) if '.fbx' in x]
    for file in files:
        os.system(f'fbx2gltf.exe -e -i {direc}/{file} -o {direc}/{file[:-4]}.glb')
    with zipfile.ZipFile(f'{direc}/{name}_tex.zip', 'w') as myzip:
        for f in [x for x in os.listdir(direc) if '.png' in x]:
            myzip.write(f'{direc}/{f}', f)


if __name__ == '__main__':
    pkg_db.start_db_connection('3_0_1_3')
    all_file_info = {x[0]: dict(zip(['Reference', 'FileType'], x[1:])) for x in
                     pkg_db.get_entries_from_table('Everything', 'FileName, Reference, FileType')}

    helmets = {
        'bakris': '0157-0487',
        'warlock_soa': '0157-016E',
        'dawn_chorus': '0157-0147',
        'lucent_night_cover': '0157-1D0D',
        'canis_luna_mask': '0157-0846',
        'solstice_mask_majestic': '0157-0434',
    }

    for name, file in helmets.items():
        # if '016E' not in file:
        #     continue
        gf.mkdir(f'I:/d2/web_dyn/{name}')
        get_gltf(f'I:/d2/web_dyn/{name}', name, file, b_textures=True)
        # gdmt.get_model(file, all_file_info, lod=True, temp_direc=f'I:/d2/web_dyn/{name}', b_temp_direc_full=True,
        #                b_textures=False, b_helmet=False, b_apply_textures=False)  # Textures already pulled out
        # break