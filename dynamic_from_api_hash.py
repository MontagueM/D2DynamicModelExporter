import gf
import get_dynamic_model_textures as dme
import pkg_db
import re


def get_armour_from_api(api_hash, strinfo, mass=False, byte=False):
    if byte:
        apihsh = api_hash
    else:
        apihsh = bytes.fromhex(gf.get_flipped_hex(gf.fill_hex_with_zeros(hex(api_hash)[2:], 8), 8))
    print(apihsh)
    table = '0279-114A'
    fb = open(f'I:/d2_output_3_0_2_0/{gf.get_pkg_name(table)}/{table}.bin', 'rb').read()
    offset = fb.find(apihsh) + 8
    if offset == 7:
        raise Exception(f'Hash {apihsh} not found in table 1')
    hshs = [fb[offset:offset+4], fb[offset+4:offset+8]]
    for i, hsh in enumerate(hshs):
        table = '020D-12BE'
        fb = open(f'I:/d2_output_3_0_2_0/{gf.get_pkg_name(table)}/{table}.bin', 'rb').read()
        offset = fb.find(hsh) + 4
        if offset == 3:
            raise Exception(f'Hash {hsh} not found in table 2')
        print(fb[offset:offset+4].hex())

        file = gf.get_file_from_hash(fb[offset:offset+4].hex())
        fb = open(f'I:/d2_output_3_0_2_0/{gf.get_pkg_name(file)}/{file}.bin', 'rb').read()
        dyn1 = gf.get_file_from_hash(hash64_table[fb[0x10:0x10+8].hex().upper()])
        if dyn1 == 'FBFF-1FFF':
            print('No dyn1')
            return
        print(f'dyn1 {dyn1}')
        lod_filter = True
        apiname, ret = get_name_from_api(apihsh, strinfo)
        if i == 0:
            apiname += '_male'
        else:
            apiname += '_female'
        if not ret:
            return
        if mass:
            temp_direc = f'apinamed/api_{apiname}'
        else:
            temp_direc = f'api_{apiname}'
        dme.get_model(dyn1, all_file_info, lod_filter, temp_direc=temp_direc, passing_dyn3=False, obfuscate=False, b_apply_textures=True,
                  b_shaders=False, b_textures=True, jud_shader=False, from_api=True, b_skeleton=True)


def get_weapon_from_api(api_hash, strinfo, mass=False, byte=False):
    if byte:
        apihsh = api_hash
    else:
        apihsh = bytes.fromhex(gf.get_flipped_hex(hex(api_hash)[2:], 8))
    print(apihsh)
    table = '0279-114A'
    tableb = '020D-12BE'
    fb = open(f'I:/d2_output_3_0_2_0/{gf.get_pkg_name(table)}/{table}.bin', 'rb').read()
    fbb = open(f'I:/d2_output_3_0_2_0/{gf.get_pkg_name(tableb)}/{tableb}.bin', 'rb').read()
    offset = fb.find(apihsh) + 0x18
    if offset == 0x17:
        raise Exception(f'Hash {apihsh} not found in table 1')
    offset += gf.get_uint32(fb, offset)
    count = gf.get_uint32(fb, offset)
    b_entries = [x + gf.get_uint32(fb, x) + 0x10 for x in range(offset+0x10, offset+0x10+0x8*count, 0x8)]
    for b in b_entries:
        b += gf.get_uint32(fb, b)  # Table offset
        c = gf.get_uint32(fb, b)
        d_entries = [fb[x:x+4] for x in range(b + 0x10, b + 0x10 + 0x4 * c, 0x4)]
        for d in d_entries:
            if d == b'\xC5\x9D\x1C\x81':  # Bogus? idk why it does this
                continue
            off = fbb.find(d) + 4
            if off == 3:
                raise Exception(f'Hash {d} not found in 1F61 table')
            unk_file = gf.get_file_from_hash(fbb[off:off+4].hex())
            fbu = open(f'I:/d2_output_3_0_2_0/{gf.get_pkg_name(unk_file)}/{unk_file}.bin', 'rb').read()
            dyn1 = gf.get_file_from_hash(hash64_table[fbu[0x10:0x10+8].hex().upper()])
            print(f'dyn1 {dyn1}')
            lod_filter = True
            apiname, ret = get_name_from_api(apihsh, strinfo)
            if not ret:
                return
            if mass:
                temp_direc = f'apinamed/api_{apiname}'
            else:
                temp_direc = f'api_{apiname}'
            dme.get_model(dyn1, all_file_info, lod_filter, temp_direc=temp_direc, passing_dyn3=False, obfuscate=True, b_apply_textures=True,
                      b_shaders=False, b_textures=True, from_api=True, jud_shader=True, b_skeleton=True)


def get_name_from_api(api_hash, strinfo):
    table = '0279-1129'
    fb = open(f'I:/d2_output_3_0_2_0/{gf.get_pkg_name(table)}/{table}.bin', 'rb').read()
    offset = fb.find(api_hash) + 0x10
    if offset == 0xF:
        print(f'Hash {api_hash} not found in text table')
        return str(int.from_bytes(api_hash, byteorder='little', signed=False)), False
    tfile = gf.get_file_from_hash(fb[offset:offset+4].hex())
    fb = open(f'I:/d2_output_3_0_2_0/{gf.get_pkg_name(tfile)}/{tfile}.bin', 'rb').read()
    stringhsh = fb[0x84:0x84+0x8].hex().upper()
    if stringhsh not in strinfo.keys():
        print(f'{stringhsh} not in text db.')
        return str(int.from_bytes(api_hash, byteorder='little', signed=False)), False
    print(f'Got api name {strinfo[stringhsh]}')
    return re.sub('[^A-Za-z0-9]+', '', strinfo[stringhsh]), True


def mass_export(strinfo):
    table = '0279-114A'
    fb = open(f'I:/d2_output_3_0_2_0/{gf.get_pkg_name(table)}/{table}.bin', 'rb').read()
    # for i in range(0x40, 4301*0x20, 0x20):
    for i in range(4301 * 0x20, 0x40, -0x20):
        bhsh = fb[i:i+4]
        print(f'\nGetting {bhsh.hex()}...\n')
        if fb[i+0x18:i+0x18+4] != b'\x00\x00\x00\x00':
            get_weapon_from_api(bhsh, strinfo, mass=True, byte=True)
        else:
            get_armour_from_api(bhsh, strinfo, mass=True, byte=True)


if __name__ == '__main__':
    version = '3_0_2_0'
    pkg_db.start_db_connection(version=f'C:/Users\monta\OneDrive\Destiny 2 Datamining\TextExtractor\db/{version}.db')
    strinfo = {x: y for x, y in pkg_db.get_entries_from_table('Everything', 'Hash, String')}

    pkg_db.start_db_connection(f'I:/d2_pkg_db/hash64/{version}.db')
    hash64_table = {x: y for x, y in pkg_db.get_entries_from_table('Everything', 'Hash64, Reference')}

    pkg_db.start_db_connection(f'I:/d2_pkg_db/{version}.db')
    all_file_info = {x[0]: dict(zip(['Reference', 'FileType'], x[1:])) for x in
                     pkg_db.get_entries_from_table('Everything', 'FileName, Reference, FileType')}

    # Moonfang cloak 2701727616 (cloaks dont get exported)
    # Moonfang crown 2288398391
    api_hash = 2702372534
    get_armour_from_api(api_hash, strinfo)

    # Trials auto 1909527966
    # Ace of spades 347366834
    # Eystein-D (lots of sights) 1291586825
    # Cold denial 1216130969

    # api_hash = 1650442173
    # get_weapon_from_api(api_hash, strinfo)

    api_hash = 1839565992
    # get_weapon_from_api(api_hash, strinfo)

    # mass_export(strinfo)
