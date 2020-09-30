from dataclasses import dataclass, fields, field
import numpy as np
import gf
import pkg_db
from PIL import Image
from typing import List
import texture2ddecoder

"""
Images are a two-part system. The first file is the image header, containing all the important info. The second part
has the actual image data which uses the header data to transcribe that data to an actual image.
"""


@dataclass
class ImageHeader:
    EntrySize: np.uint32 = np.uint32(0)  # 0
    TextureFormat: np.uint32 = np.uint32(0)  # 4
    Field8: np.uint32 = np.uint32(0)
    Cafe: np.uint16 = np.uint16(0)  # 0xCAFE
    Width: np.uint16 = np.uint16(0)  # E
    Height: np.uint16 = np.uint16(0)  # 10
    Field12: np.uint16 = np.uint16(0)
    Field14: np.uint32 = np.uint32(0)
    Field18: np.uint32 = np.uint32(0)
    Field1C: np.uint32 = np.uint32(0)
    Field20: np.uint32 = np.uint32(0)
    LargeTextureHash: np.uint32 = np.uint32(0)  # 24
    TextureFormatDefined: str = ''

# This header includes the magic number, DDS header, and DXT10 DDS header
@dataclass
class DDSHeader:
    MagicNumber: np.uint32 = np.uint32(0)
    dwSize: np.uint32 = np.uint32(0)
    dwFlags: np.uint32 = np.uint32(0)
    dwHeight: np.uint32 = np.uint32(0)
    dwWidth: np.uint32 = np.uint32(0)
    dwPitchOrLinearSize: np.uint32 = np.uint32(0)
    dwDepth: np.uint32 = np.uint32(0)
    dwMipMapCount: np.uint32 = np.uint32(0)
    dwReserved1: List[np.uint32] = field(default_factory=list)  # size 11, [11]
    dwPFSize: np.uint32 = np.uint32(0)
    dwPFFlags: np.uint32 = np.uint32(0)
    dwPFFourCC: np.uint32 = np.uint32(0)
    dwPFRGBBitCount: np.uint32 = np.uint32(0)
    dwPFRBitMask: np.uint32 = np.uint32(0)
    dwPFGBitMask: np.uint32 = np.uint32(0)
    dwPFBBitMask: np.uint32 = np.uint32(0)
    dwPFABitMask: np.uint32 = np.uint32(0)
    dwCaps: np.uint32 = np.uint32(0)
    dwCaps2: np.uint32 = np.uint32(0)
    dwCaps3: np.uint32 = np.uint32(0)
    dwCaps4: np.uint32 = np.uint32(0)
    dwReserved2: np.uint32 = np.uint32(0)
    dxgiFormat: np.uint32 = np.uint32(0)
    resourceDimension: np.uint32 = np.uint32(0)
    miscFlag: np.uint32 = np.uint32(0)
    arraySize: np.uint32 = np.uint32(0)
    miscFlags2: np.uint32 = np.uint32(0)


DXGI_FORMAT = [
  "DXGI_FORMAT_UNKNOWN",
  "DXGI_FORMAT_R32G32B32A32_TYPELESS",
  "DXGI_FORMAT_R32G32B32A32_FLOAT",
  "DXGI_FORMAT_R32G32B32A32_UINT",
  "DXGI_FORMAT_R32G32B32A32_SINT",
  "DXGI_FORMAT_R32G32B32_TYPELESS",
  "DXGI_FORMAT_R32G32B32_FLOAT",
  "DXGI_FORMAT_R32G32B32_UINT",
  "DXGI_FORMAT_R32G32B32_SINT",
  "DXGI_FORMAT_R16G16B16A16_TYPELESS",
  "DXGI_FORMAT_R16G16B16A16_FLOAT",
  "DXGI_FORMAT_R16G16B16A16_UNORM",
  "DXGI_FORMAT_R16G16B16A16_UINT",
  "DXGI_FORMAT_R16G16B16A16_SNORM",
  "DXGI_FORMAT_R16G16B16A16_SINT",
  "DXGI_FORMAT_R32G32_TYPELESS",
  "DXGI_FORMAT_R32G32_FLOAT",
  "DXGI_FORMAT_R32G32_UINT",
  "DXGI_FORMAT_R32G32_SINT",
  "DXGI_FORMAT_R32G8X24_TYPELESS",
  "DXGI_FORMAT_D32_FLOAT_S8X24_UINT",
  "DXGI_FORMAT_R32_FLOAT_X8X24_TYPELESS",
  "DXGI_FORMAT_X32_TYPELESS_G8X24_UINT",
  "DXGI_FORMAT_R10G10B10A2_TYPELESS",
  "DXGI_FORMAT_R10G10B10A2_UNORM",
  "DXGI_FORMAT_R10G10B10A2_UINT",
  "DXGI_FORMAT_R11G11B10_FLOAT",
  "DXGI_FORMAT_R8G8B8A8_TYPELESS",
  "DXGI_FORMAT_R8G8B8A8_UNORM",
  "DXGI_FORMAT_R8G8B8A8_UNORM_SRGB",
  "DXGI_FORMAT_R8G8B8A8_UINT",
  "DXGI_FORMAT_R8G8B8A8_SNORM",
  "DXGI_FORMAT_R8G8B8A8_SINT",
  "DXGI_FORMAT_R16G16_TYPELESS",
  "DXGI_FORMAT_R16G16_FLOAT",
  "DXGI_FORMAT_R16G16_UNORM",
  "DXGI_FORMAT_R16G16_UINT",
  "DXGI_FORMAT_R16G16_SNORM",
  "DXGI_FORMAT_R16G16_SINT",
  "DXGI_FORMAT_R32_TYPELESS",
  "DXGI_FORMAT_D32_FLOAT",
  "DXGI_FORMAT_R32_FLOAT",
  "DXGI_FORMAT_R32_UINT",
  "DXGI_FORMAT_R32_SINT",
  "DXGI_FORMAT_R24G8_TYPELESS",
  "DXGI_FORMAT_D24_UNORM_S8_UINT",
  "DXGI_FORMAT_R24_UNORM_X8_TYPELESS",
  "DXGI_FORMAT_X24_TYPELESS_G8_UINT",
  "DXGI_FORMAT_R8G8_TYPELESS",
  "DXGI_FORMAT_R8G8_UNORM",
  "DXGI_FORMAT_R8G8_UINT",
  "DXGI_FORMAT_R8G8_SNORM",
  "DXGI_FORMAT_R8G8_SINT",
  "DXGI_FORMAT_R16_TYPELESS",
  "DXGI_FORMAT_R16_FLOAT",
  "DXGI_FORMAT_D16_UNORM",
  "DXGI_FORMAT_R16_UNORM",
  "DXGI_FORMAT_R16_UINT",
  "DXGI_FORMAT_R16_SNORM",
  "DXGI_FORMAT_R16_SINT",
  "DXGI_FORMAT_R8_TYPELESS",
  "DXGI_FORMAT_R8_UNORM",
  "DXGI_FORMAT_R8_UINT",
  "DXGI_FORMAT_R8_SNORM",
  "DXGI_FORMAT_R8_SINT",
  "DXGI_FORMAT_A8_UNORM",
  "DXGI_FORMAT_R1_UNORM",
  "DXGI_FORMAT_R9G9B9E5_SHAREDEXP",
  "DXGI_FORMAT_R8G8_B8G8_UNORM",
  "DXGI_FORMAT_G8R8_G8B8_UNORM",
  "DXGI_FORMAT_BC1_TYPELESS",
  "DXGI_FORMAT_BC1_UNORM",
  "DXGI_FORMAT_BC1_UNORM_SRGB",
  "DXGI_FORMAT_BC2_TYPELESS",
  "DXGI_FORMAT_BC2_UNORM",
  "DXGI_FORMAT_BC2_UNORM_SRGB",
  "DXGI_FORMAT_BC3_TYPELESS",
  "DXGI_FORMAT_BC3_UNORM",
  "DXGI_FORMAT_BC3_UNORM_SRGB",
  "DXGI_FORMAT_BC4_TYPELESS",
  "DXGI_FORMAT_BC4_UNORM",
  "DXGI_FORMAT_BC4_SNORM",
  "DXGI_FORMAT_BC5_TYPELESS",
  "DXGI_FORMAT_BC5_UNORM",
  "DXGI_FORMAT_BC5_SNORM",
  "DXGI_FORMAT_B5G6R5_UNORM",
  "DXGI_FORMAT_B5G5R5A1_UNORM",
  "DXGI_FORMAT_B8G8R8A8_UNORM",
  "DXGI_FORMAT_B8G8R8X8_UNORM",
  "DXGI_FORMAT_R10G10B10_XR_BIAS_A2_UNORM",
  "DXGI_FORMAT_B8G8R8A8_TYPELESS",
  "DXGI_FORMAT_B8G8R8A8_UNORM_SRGB",
  "DXGI_FORMAT_B8G8R8X8_TYPELESS",
  "DXGI_FORMAT_B8G8R8X8_UNORM_SRGB",
  "DXGI_FORMAT_BC6H_TYPELESS",
  "DXGI_FORMAT_BC6H_UF16",
  "DXGI_FORMAT_BC6H_SF16",
  "DXGI_FORMAT_BC7_TYPELESS",
  "DXGI_FORMAT_BC7_UNORM",
  "DXGI_FORMAT_BC7_UNORM_SRGB",
  "DXGI_FORMAT_AYUV",
  "DXGI_FORMAT_Y410",
  "DXGI_FORMAT_Y416",
  "DXGI_FORMAT_NV12",
  "DXGI_FORMAT_P010",
  "DXGI_FORMAT_P016",
  "DXGI_FORMAT_420_OPAQUE",
  "DXGI_FORMAT_YUY2",
  "DXGI_FORMAT_Y210",
  "DXGI_FORMAT_Y216",
  "DXGI_FORMAT_NV11",
  "DXGI_FORMAT_AI44",
  "DXGI_FORMAT_IA44",
  "DXGI_FORMAT_P8",
  "DXGI_FORMAT_A8P8",
  "DXGI_FORMAT_B4G4R4A4_UNORM",
  "DXGI_FORMAT_P208",
  "DXGI_FORMAT_V208",
  "DXGI_FORMAT_V408",
  "DXGI_FORMAT_SAMPLER_FEEDBACK_MIN_MIP_OPAQUE",
  "DXGI_FORMAT_SAMPLER_FEEDBACK_MIP_REGION_USED_OPAQUE",
  "DXGI_FORMAT_FORCE_UINT"
]


def get_header(file_hex):
    img_header = ImageHeader()
    for f in fields(img_header):
        if f.type == np.uint32:
            flipped = "".join(gf.get_flipped_hex(file_hex, 8))
            value = np.uint32(int(flipped, 16))
            setattr(img_header, f.name, value)
            file_hex = file_hex[8:]
        elif f.type == np.uint16:
            flipped = "".join(gf.get_flipped_hex(file_hex, 4))
            value = np.uint16(int(flipped, 16))
            setattr(img_header, f.name, value)
            file_hex = file_hex[4:]
    return img_header


def export_image_from_file(file, temp_dir, model_file):
    pkg_db.start_db_connection('2_9_2_1_all')
    # To get the actual image data we need to pull this specific file's data from the database as it references its file
    # in its RefID.
    pkg = gf.get_pkg_name(file)
    entries = pkg_db.get_entries_from_table(pkg, 'FileName, RefID, RefPKG, FileType')
    this_entry = [x for x in entries if x[0] == file][0]
    ref_file = f'{this_entry[2][2:]}-{gf.fill_hex_with_zeros(this_entry[1][2:], 4)}'
    if this_entry[-1] == 'Texture Header':
        ref_pkg = gf.get_pkg_name(ref_file)
        header_hex = gf.get_hex_data(f'C:/d2_output/{pkg}/{file}.bin')
        data_hex = gf.get_hex_data(f'C:/d2_output/{ref_pkg}/{ref_file}.bin')
    elif this_entry[-1] == 'Texture Data':
        print('Only pass through header please, cba to fix this.')
        return
    else:
        print(f"File given is not texture data or header of type {this_entry[-1]}")
        return

    header = get_header(header_hex)
    dimensions = [header.Width, header.Height]
    header.TextureFormatDefined = DXGI_FORMAT[header.TextureFormat]
    img = get_image_from_data(header, dimensions, data_hex)
    if img:
        img.save(f'C:/d2_model_temp/texture_models/{temp_dir}/{model_file}/{file}.png')
        # img.show()
    else:
        print(f'Could not save file {file}')


def get_image_from_data(header, dimensions, data_hex):
    img = None
    if 'RGBA' in header.TextureFormatDefined:
        try:
            img = Image.frombytes('RGBA', dimensions, bytes.fromhex(data_hex))
        except ValueError:
            return 'Invalid'
    elif 'BC1' in header.TextureFormatDefined:
        try:
            img = Image.frombytes('RGBA', dimensions, bytes.fromhex(data_hex), 'bcn', (1,))
        except ValueError:
            # bc1_decomp(header, data_hex)
            try:
                dec = texture2ddecoder.decode_bc1(bytes.fromhex(data_hex), header.Width, header.Height)
                img = Image.frombytes('RGBA', dimensions, dec, 'raw', ("BGRA"))
            except ValueError:
                return 'Invalid'
    elif 'BC3' in header.TextureFormatDefined:
        try:
            img = Image.frombytes('RGBA', dimensions, bytes.fromhex(data_hex), 'bcn', (3,))
        except ValueError:
            try:
                dec = texture2ddecoder.decode_bc3(bytes.fromhex(data_hex), header.Width, header.Height)
                img = Image.frombytes('RGBA', dimensions, dec, 'raw', ("BGRA"))
            except ValueError:
                return 'Invalid'
    elif 'BC4' in header.TextureFormatDefined:
        try:
            img = Image.frombytes('RGBA', dimensions, bytes.fromhex(data_hex), 'bcn', (4,))
        except ValueError:
            try:
                dec = texture2ddecoder.decode_bc4(bytes.fromhex(data_hex), header.Width, header.Height)
                img = Image.frombytes('RGBA', dimensions, dec, 'raw', ("BGRA"))
            except ValueError:
                return 'Invalid'
    elif 'BC5' in header.TextureFormatDefined:
        try:
            img = Image.frombytes('RGBA', dimensions, bytes.fromhex(data_hex), 'bcn', (5,))
        except ValueError:
            try:
                dec = texture2ddecoder.decode_bc5(bytes.fromhex(data_hex), header.Width, header.Height)
                img = Image.frombytes('RGBA', dimensions, dec, 'raw', ("BGRA"))
            except ValueError:
                return 'Invalid'
    elif 'BC6' in header.TextureFormatDefined:
        # bc6h_decomp(header, data_hex)
        try:
            img = Image.frombytes('RGBA', dimensions, bytes.fromhex(data_hex), 'bcn', (6,))
        except ValueError:
            try:
                dec = texture2ddecoder.decode_bc6(bytes.fromhex(data_hex), header.Width, header.Height)
                img = Image.frombytes('RGBA', dimensions, dec, 'raw', ("BGRA"))
            except ValueError:
                return 'Invalid'
    elif 'BC7' in header.TextureFormatDefined:
        # print('Size', int(len(data_hex)/2), '|', header.TextureFormatDefined, dimensions)
        try:
            img = Image.frombytes('RGBA', dimensions, bytes.fromhex(data_hex), 'bcn', (7,))
        except ValueError:
            # bc7_decomp(header, data_hex)
            try:
                dec = texture2ddecoder.decode_bc7(bytes.fromhex(data_hex), header.Width, header.Height)
                img = Image.frombytes('RGBA', dimensions, dec, 'raw', ("BGRA"))
            except ValueError:
                return 'Invalid'
    else:
        print(f'Image not supported type {header.TextureFormatDefined}')
    return img


def get_model_textures(file, model_file, temp_dir=''):
    # file = gf.get_file_from_hash(gf.get_flipped_hex(model_hash, 8))
    pkg = gf.get_pkg_name(file)
    mf1_hex = gf.get_hex_data(f'C:/d2_output/{pkg}/{file}.bin')
    offset = (int(gf.get_flipped_hex(mf1_hex[48:56], 8), 16)+608)*2
    file = gf.get_file_from_hash(gf.get_flipped_hex(mf1_hex[offset:offset+8], 8))
    pkg = gf.get_pkg_name(file)
    print(f'tf C:/d2_output/{pkg}/{file}.bin')
    tf_hex = gf.get_hex_data(f'C:/d2_output/{pkg}/{file}.bin')
    texture_count = int(gf.get_flipped_hex(tf_hex[32*2:36*2], 8), 16)
    texture_entries = []
    for i in range(texture_count):
        texture_entries.append(gf.get_file_from_hash(gf.get_flipped_hex(tf_hex[36*2+8*i:36*2+8*(i+1)], 8)))
    for tex in texture_entries:
        pkg = gf.get_pkg_name(tex)
        tex_hex = gf.get_hex_data(f'C:/d2_output/{pkg}/{tex}.bin')
        tex = gf.get_file_from_hash(gf.get_flipped_hex(tex_hex[64*2:68*2], 8))
        export_image_from_file(tex, temp_dir, model_file)


if __name__ == '__main__':
    # The file needed is the one above the main model file.
    # get_model_textures('0361-0013', '0361-0012')
    get_model_textures('020E-1FA2', '020E-1F9C')
