import pkg_db
from dataclasses import dataclass, fields
import numpy as np
import os
import re
import gf
import fbx
import pyfbx_jo as pfb
import struct
import get_dynamic_model_textures as gdmt


def export_all_models(pkg_name, all_file_info):
    entries_type = {x: y for x, y in pkg_db.get_entries_from_table(pkg_name, 'FileName, FileType') if y == 'Dynamic Model Header 1'}
    for file in list(entries_type.keys()):
        fhex = gf.get_hex_data(f'I:/d2_output_3_0_0_4/{gf.get_pkg_name(file)}/{file}.bin')
        offset = int(gf.get_flipped_hex(fhex[24*2:24*2+8], 8), 16)*2
        try:
            mfile = gf.get_file_from_hash(fhex[offset+572*2:offset+572*2+8])
            if mfile in all_file_info.keys():
                if all_file_info[mfile]['FileType'] == 'Dynamic Model Header 2':
                    print(f'Getting file {file}')
                    gdmt.get_model(mfile, all_file_info, temp_direc='europa/' + pkg_name)
                else:
                    print(f'Weird {file} {mfile}')
        except ValueError:
            pass
        # if file == '0156-1EBE':


if __name__ == '__main__':
    pkg_db.start_db_connection('3_0_0_4')
    all_file_info = {x[0]: dict(zip(['RefID', 'RefPKG', 'FileType'], x[1:])) for x in
                     pkg_db.get_entries_from_table('Everything', 'FileName, RefID, RefPKG, FileType')}

    for pkg in pkg_db.get_all_tables():
        if 'europa' in pkg:
            export_all_models(pkg, all_file_info)