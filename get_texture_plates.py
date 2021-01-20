import gf
import binascii
import get_image_png as gip
import pkg_db
from PIL import Image


class TexturePlateSet:
    def __init__(self, dyn_model_1, direct_from_tex):
        self.topfile = dyn_model_1
        self.plates = self.get_plates(direct_from_tex)

    def get_plate_set(self, all_file_info):
        for type, plate in self.plates.items():
            ret = plate.get_plate_data()
            if not ret:
                return False
            plate.get_plate_textures(all_file_info)
        return True

    def get_plates(self, direct_from_tex):
        if not direct_from_tex:
            fb = open(f'I:/d2_output_3_0_2_0/{gf.get_pkg_name(self.topfile)}/{self.topfile}.bin', 'rb').read()
            # This offset is a guess for now
            offset = fb.find(b'\xCD\x9A\x80\x80')+8
            dyn2 = gf.get_file_from_hash(bytes.hex(fb[offset:offset+4]))
            fb = open(f'I:/d2_output_3_0_2_0/{gf.get_pkg_name(dyn2)}/{dyn2}.bin', 'rb').read()
            offset = gf.get_uint16(fb, 0x18) + 712
            platesetfile = gf.get_file_from_hash(bytes.hex(fb[offset:offset+4]))
        else:
            platesetfile = self.topfile
        try:
            fb = open(f'I:/d2_output_3_0_2_0/{gf.get_pkg_name(platesetfile)}/{platesetfile}.bin', 'rb').read()
        except FileNotFoundError:
            return False
        a = TexturePlate(gf.get_file_from_hash(bytes.hex(fb[0x28:0x28+4])), 'diffuse')
        b = TexturePlate(gf.get_file_from_hash(bytes.hex(fb[0x2C:0x2C+4])), 'normal')
        c = TexturePlate(gf.get_file_from_hash(bytes.hex(fb[0x30:0x30+4])), 'gstack')
        d = TexturePlate(gf.get_file_from_hash(bytes.hex(fb[0x34:0x34+4])), 'dyemap')

        return {'diffuse': a, 'normal': b, 'gstack': c, 'dyemap': d}

    def export_texture_plate_set(self, save_dir, b_helmet):
        # We'll append _diffuse.png, _normal.png, _gstack.png to the save_dir per set
        for type, plate in self.plates.items():
            plate.export_plate(f'{save_dir}_{type}.png', b_helmet)


class TexturePlate:
    def __init__(self, platefile, type):
        self.file = platefile
        self.type = type
        self.textures = []

    def get_plate_data(self):
        if self.file == 'FBFF-1FFF':
            return False
        fb = open(f'I:/d2_output_3_0_2_0/{gf.get_pkg_name(self.file)}/{self.file}.bin', 'rb').read()
        file_count = gf.get_uint16(fb, 0x30)
        table_offset = 0x40
        for i in range(table_offset, table_offset+file_count*20, 20):
            tex = Texture()
            tex.tex_header = gf.get_file_from_hash(bytes.hex(fb[i:i+4]).upper())
            tex.platex = gf.get_uint32(fb, i+0x4)
            tex.platey = gf.get_uint32(fb, i+0x8)
            tex.resizex = gf.get_uint32(fb, i+0xC)
            tex.resizey = gf.get_uint32(fb, i+0x10)
            self.textures.append(tex)
        return True

    def get_plate_textures(self, all_file_info):
        for tex in self.textures:
            tex.image = gip.get_image_png(tex.tex_header, all_file_info)

            # Resizing
            tex.image = tex.image.resize([tex.resizex, tex.resizey])

    def export_plate(self, save_dir, b_helmet):
        b_helmet
        if self.type == 'dyemap':
            dimensions = [1024, 1024]
        else:
            dimensions = [2048, 2048]
        if b_helmet:
            dimensions = [int(x/2) for x in dimensions]
        bg_plate = Image.new('RGBA', dimensions, (0, 0, 0, 0))  # Makes a transparent image as alpha = 0
        for tex in self.textures:
            bg_plate.paste(tex.image, [tex.platex, tex.platey])
        bg_plate.save(save_dir)


class Texture:
    def __init__(self):
        self.tex_header = ''
        self.image = None
        self.platex = 0
        self.platey = 0
        self.resizex = 0
        self.resizey = 0


if __name__ == '__main__':
    pkg_db.start_db_connection('3_0_2_0')
    all_file_info = {x: y for x, y in {x[0]: dict(zip(['Reference', 'FileType'], x[1:])) for x in
                                       pkg_db.get_entries_from_table('Everything',
                                                                     'FileName, Reference, FileType')}.items()}

    # Give it dyn1
    file = '0157-07F8'
    texplateset = TexturePlateSet(file, direct_from_tex=False)
    ret = texplateset.get_plate_set(all_file_info)
    if not ret:
        raise Exception('Something wrong')
    texplateset.export_texture_plate_set('imagetests/test')