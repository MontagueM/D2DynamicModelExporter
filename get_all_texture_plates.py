import get_texture_plates as gtp
import pkg_db
import gf

pkg_db.start_db_connection('3_0_1_3')
all_file_info = {x: y for x, y in {x[0]: dict(zip(['Reference', 'FileType'], x[1:])) for x in
                                   pkg_db.get_entries_from_table('Everything',
                                                                 'FileName, Reference, FileType')}.items()}
counter = 0
for file in all_file_info.keys():
    # name = gf.get_file_from_hash(file)
    try:
        if '0157' not in file:
            continue
    except TypeError:
        continue
    if all_file_info[file]['FileType'] == 'Texture Plate Set Header':
        print(file)
        texplateset = gtp.TexturePlateSet(file, direct_from_tex=True)
        if not texplateset.plates:  # No tex plate
            print('No texture plate')
            continue
        ret = texplateset.get_plate_set(all_file_info)
        if not ret:  # Is a tex plate but just nothing in it
            print('Nothing in texture plate')
            continue
        gf.mkdir(f'I:/d2/tex_plates_png/{gf.get_pkg_name(file)}/')
        texplateset.export_texture_plate_set(f'I:/d2/tex_plates_png/{gf.get_pkg_name(file)}/{file}', b_helmet=False)
        counter += 1
