from PIL import Image
import gf
import texture2ddecoder
import binascii


class ImageHeader:
    def __init__(self):
        self.TextureFormat = None
        self.Width = None
        self.Height = None
        self.LargeTextureHash = None


with open('dxgi.format') as f:
    DXGI_FORMAT = f.readlines()


def get_image_from_data(header, dimensions, data_hex):
    img = None
    if 'R8G8B8A8' in DXGI_FORMAT[header.TextureFormat]:
        try:
            img = Image.frombytes('RGBA', dimensions, data_hex)
        except ValueError:
            return 'Invalid'
    elif 'BC1' in DXGI_FORMAT[header.TextureFormat]:
        dec = texture2ddecoder.decode_bc1(data_hex, header.Width, header.Height)
        img = Image.frombytes('RGBA', dimensions, dec, 'raw', ("BGRA"))
    elif 'BC2' in DXGI_FORMAT[header.TextureFormat]:
        raise Exception('BC2 image, failed.')
        # dec = texture2ddecoder.decode_bc2(data_hex), header.Width, header.Height)
        # img = Image.frombytes('RGBA', dimensions, dec, 'raw', ("BGRA"))
    elif 'BC3' in DXGI_FORMAT[header.TextureFormat]:
        dec = texture2ddecoder.decode_bc3(data_hex, header.Width, header.Height)
        img = Image.frombytes('RGBA', dimensions, dec, 'raw', ("BGRA"))
    elif 'BC4' in DXGI_FORMAT[header.TextureFormat]:
        dec = texture2ddecoder.decode_bc4(data_hex, header.Width, header.Height)
        img = Image.frombytes('RGBA', dimensions, dec, 'raw', ("BGRA"))
    elif 'BC5' in DXGI_FORMAT[header.TextureFormat]:
        dec = texture2ddecoder.decode_bc5(data_hex, header.Width, header.Height)
        img = Image.frombytes('RGBA', dimensions, dec, 'raw', ("BGRA"))
    elif 'BC6' in DXGI_FORMAT[header.TextureFormat]:
            dec = texture2ddecoder.decode_bc6(data_hex, header.Width, header.Height)
            img = Image.frombytes('RGBA', dimensions, dec, 'raw', ("BGRA"))
    elif 'BC7' in DXGI_FORMAT[header.TextureFormat]:
        dec = texture2ddecoder.decode_bc7(data_hex, header.Width, header.Height)
        img = Image.frombytes('RGBA', dimensions, dec, 'raw', ("BGRA"))
    else:
        print(f'Image not supported type {header.TextureFormatDefined}')
    return img


def get_image_png(tex_header, all_file_info):  # Tex Header must be a hash
    name = gf.get_file_from_hash(tex_header)
    fb = open(f'I:/d2_output_3_0_1_3/{gf.get_pkg_name(name)}/{name}.bin', 'rb').read()
    header = ImageHeader()
    header.Width = gf.get_int16(fb, 0x22)
    header.Height = gf.get_int16(fb, 0x24)
    header.TextureFormat = gf.get_int32(fb, 0x4)
    header.LargeTextureHash = binascii.hexlify(fb[0x3C:0x3C+4])
    ref_file = gf.get_file_from_hash(all_file_info[tex_header]['Reference'])
    if header.LargeTextureHash != b'ffffffff':
        ref_file = gf.get_file_from_hash(all_file_info[header.LargeTextureHash]['Reference'])
    fb = open(f'I:/d2_output_3_0_1_3/{gf.get_pkg_name(ref_file)}/{ref_file}.bin', 'rb').read()
    return get_image_from_data(header, [header.Width, header.Height], fb)
