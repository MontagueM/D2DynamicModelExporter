import gf
import os
import time
import shutil
import struct
import re
import pkg_db


class File:
    def __init__(self, name=None, uid=None, pkg_name=None):
        self.name = name
        self.uid = uid
        self.pkg_name = pkg_name
        self.fb = None

    def get_file_from_uid(self):
        self.name = gf.get_file_from_hash(self.uid)
        return self.pkg_name

    def get_uid_from_file(self):
        self.uid = gf.get_hash_from_file(self.name)
        return self.pkg_name

    def get_pkg_name(self):
        self.pkg_name = gf.get_pkg_name(self.name)
        return self.pkg_name

    def get_bin_data(self):
        if not self.pkg_name:
            self.get_pkg_name()
        if not self.name:
            self.get_file_from_uid()
        self.fb = open(f'I:/d2_output_3_0_1_3/{gf.get_pkg_name(material)}/{material}.bin', 'rb').read()
        return self.fb


def get_decompiled_hlsl(shader_ref, custom_dir):
    gf.mkdir(custom_dir)
    pkg_name = gf.get_pkg_name(shader_ref)


    os.system(f'start hlsl/decomp.exe -D I:/d2_output_3_0_1_3/{pkg_name}/{shader_ref}.bin')
    num = len(os.listdir(f'I:/d2_output_3_0_1_3/{pkg_name}/'))
    while True:
        if num != len(os.listdir(f'I:/d2_output_3_0_1_3/{pkg_name}/')):
            time.sleep(0.1)
            break

    shutil.move(f'I:/d2_output_3_0_1_3/{pkg_name}/{shader_ref}.hlsl', f'{custom_dir}/{shader_ref}.hlsl')
    print(f'Decompiled and moved shader {shader_ref}.hlsl to {custom_dir}')


def convert_hlsl(material, textures, cbuffer_offsets, shader_ref, custom_dir, all_file_info, name=None):
    print(f'Material {material}')
    lines_to_write = []

    # Getting info from material
    fb = open(f'I:/d2_output_3_0_1_3/{gf.get_pkg_name(material)}/{material}.bin', 'rb').read()
    cbuffers = get_all_cbuffers_from_file(fb, cbuffer_offsets, all_file_info)


    # Getting info from hlsl file
    with open(f'{custom_dir}/{shader_ref}.hlsl', 'r') as h:
        text = h.readlines()
        instructions = get_instructions(text)
        cbuffer_text = get_cbuffer_text(cbuffers, text)
        inputs, outputs = get_in_out(text, instructions)
        input_append1, input_append2 = get_inputs_append(inputs)
        texs = get_texs(text)
        params, params_end = get_params(texs)
        # tex_comments = get_tex_comments(textures)
        lines_to_write.append('#pragma once\n')
        # lines_to_write.append(tex_comments)
        lines_to_write.append(cbuffer_text)
        # lines_to_write.append(f'static float4 cb0[{cbuffer_length}] = \n' + '{\n' + f'{cbuffer1}\n' + '};\n')
        lines_to_write.append(input_append1)
        lines_to_write.append('\n\nstruct shader {\nfloat4 main(\n')
        lines_to_write.append(params)
        lines_to_write.append(input_append2)
        lines_to_write.append(f'    float4 {",".join(outputs)};\n')
        lines_to_write.append(instructions)
        lines_to_write.append('}\n};\n\nshader s;\n\n' + f'return s.main({params_end}, tx);')

    # Change to 3 for all outputs, currently just want base colour
    for i in range(3):
        if name:
            open_dir = f'{custom_dir}/{name}_{shader_ref}_o{i}.usf'
        else:
            open_dir = f'{custom_dir}/{material}_o{i}.usf'
        with open(open_dir, 'w') as u:
        # with open(f'hlsl/.usf', 'w') as u:
            # TODO convert to an array write, faster
            for line in lines_to_write:
                if 'return' in line:
                    line = line.replace('return;', f'return o{i};')
                u.write(line)
            print(f'Wrote to usf {open_dir}')
        print('')


def get_cbuffer_text(cbuffers, text):
    ret = ''
    # This all assumes there won't be two cbuffers of the same length
    cbuffer_to_write = {}
    text_cbuffers = {}
    read = False
    for line in text:
        if 'cbuffer' in line:
            read = True
        if read:
            if 'register' in line:
                name = line.split(' ')[1]
            elif 'float4' in line:
                size = int(line.split('[')[1].split(']')[0])
            elif '}' in line:
                text_cbuffers[size] = name
                read = False
    for length, data in cbuffers.items():
        if length in text_cbuffers.keys():
            name = text_cbuffers[length]
            cbuffer_to_write[name] = [data, length]

    # As we don't know where to find cb12 yet
    if 'cb7' in text_cbuffers.values():
        cbuffer_to_write['cb7'] = ['float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),', 63]


    if 'cb12' in text_cbuffers.values():
        cbuffer_to_write['cb12'] = ['float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),', 8]

    if 'cb13' in text_cbuffers.values():
        cbuffer_to_write['cb13'] = ['float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),float4(1,1,1,1),', 8]


    for name, packed in cbuffer_to_write.items():
        data = packed[0]
        length = packed[1]
        ret += f'static float4 {name}[{length}] = \n' + '{\n' + f'{data}\n' + '};\n'

    return ret


def get_tex_comments(textures):
    comments = ''
    comments += f'//{textures}\n'
    for i, t in enumerate(textures):
        comments += f'// t{i} is {t}\n'
    return comments


def get_inputs_append(inputs):
    input_append1 = ''
    input_append2 = ''
    for inp in inputs:
        inps = inp.split(' ')
        if 'TEXCOORD' in inp:
            if 'float4' in inp:
                write = f'\nstatic {inps[2]} {inps[3]} = ' + '{1, 1, 1, 1};\n'
            elif 'float3' in inp:
                write = f'\nstatic {inps[2]} {inps[3]} = ' + '{1, 1, 1};\n'
            input_append2 += f'    {inps[3]}.xy = {inps[3]}.xy * tx;\n'
        elif 'SV_isFrontFace0' in inp:
            write = f'\nstatic {inps[2]} {inps[3]} = 1;\n'
        else:
            raise Exception('Input not recognised.')
        input_append1 += write
    return input_append1, input_append2


def get_params(texs):
    params = ''
    params_end = ''
    texs = texs[::-1]
    for t in texs:
        if texs[-1] == t:
            params += f'  float4 {t},\n   float2 tx)\n' + '{\n'
            params_end += t
        else:
            params += f'  float4 {t},\n'
            params_end += f'{t}, '
    print('')
    return params, params_end


def get_texs(text):
    texs = []
    for line in text:
        if 'Texture2D<float4>' in line:
            texs.append(line.split(' ')[1])
    return texs


def get_instructions(text):
    instructions = []
    care = False
    read = False
    for line in text:
        if read:
            if 'Sample' in line:
                equal = line.split('=')[0]
                to_sample = [x for x in line.split(' ') if x != ''][2].split('.')[0]
                samplestate = int(line.split('(')[1][1])
                uv = line.split(', ')[1].split(')')[0]
                dot_after = line.split(').')[1]
                line = f'{equal}= Material_Texture2D_{to_sample[1:]}.SampleLevel(Material_Texture2D_{samplestate-1}Sampler, {uv}, 0).{dot_after}'
            elif 'LevelOfDetail' in line:
                equal = line.split('=')[0]
                line = f'{equal}= 0;'
            instructions.append('  ' + line)
            if 'return;' in line:
                ret = ''.join(instructions)
                # cmp seems broken
                ret = ret.replace('cmp', '')
                # discard doesnt work in ue4 hlsl
                ret = ret.replace('discard', '{ o0.w = 0; }')
                # just in case theres some stupid other texture calls
                return ret
        elif 'void main(' in line:
            care = True
        elif care and '{' in line:
            read = True


def get_in_out(text, instructions):
    inputs = []
    outputs = []
    read = False
    for line in text:
        if 'void main(' in line:
            read = True
            continue
        if read:
            if 'out' in line:
                outputs.append(line.split(' ')[4])
            elif '{' in line:
                return inputs, outputs
            else:
                inp = line.split(' ')[3]
                if inp in instructions:
                    inputs.append(line[:-1])


def get_all_cbuffers_from_file(fb, cbuffer_offsets, all_file_info):
    cbuffers = {}
    # Read cbuffer from file if there
    # if bytes.hex(fb[0x34C:0x34C+4]) != 'FFFFFFFF':
    #     cbuffer_header = File(uid=bytes.hex(fb[0x34C:0x34C+4]))
    #     cbuffer_header.get_file_from_uid()
    #     cbuffer_ref = File(name=f"{all_file_info[cbuffer_header.name]['RefPKG'][2:]}-{all_file_info[cbuffer_header.name]['RefID'][2:]}")
    #     cbuffer_ref.get_bin_data()
    #     data, length = process_cbuffer_data(cbuffer_ref.fb)
    #     cbuffers[length] = data

    # Reading from mat file as well in case there's more cbuffers
    # offsets = [m.start() for m in re.finditer('90008080', material.fhex)]
    # If cbuffer is a real cbuffer we'll read it and output it
    for offset in cbuffer_offsets:
        offset += 8
        count = gf.get_uint32(fb, offset-8)
        if count != 1:
            data, length = process_cbuffer_data(fb[offset+8:offset+8+16*count])
            cbuffers[length] = data
        # else:
            # raise Exception('No cbuffer found.')
    return cbuffers


def process_cbuffer_data(fb, direct=False):
    cbuffer_out = []
    cbuffer = [struct.unpack('f', fb[i:i + 4])[0] for i in
               range(0, len(fb), 4)]
    for i in range(0, len(cbuffer), 4):
        cbuffer_out.append(f'   float4({cbuffer[i]}, {cbuffer[i + 1]}, {cbuffer[i + 2]}, {cbuffer[i + 3]}),')
    if direct:
        return ''.join(cbuffer_out)
    else:
        return '\n'.join(cbuffer_out), int(len(cbuffer) / 4)


if __name__ == '__main__':
    pkg_db.start_db_connection('3_0_1_3')
    all_file_info = {x[0]: dict(zip(['Reference', 'FileType'], x[1:])) for x in
                     pkg_db.get_entries_from_table('Everything', 'FileName, Reference, FileType')}

    shader = '0157-1A3C'
    # get_decompiled_hlsl(shader, 'hlsl/')
    material = '0157-1A39'
    # convert_hlsl(material, [], [0x480, 0x630], shader, 'hlsl/', all_file_info)
    cb = '01E6-1475'
    print(process_cbuffer_data(open(f'I:/d2_output_3_0_1_3/{gf.get_pkg_name(cb)}/{cb}.bin', 'rb').read(), direct=True))
