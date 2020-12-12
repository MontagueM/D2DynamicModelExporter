import gf
import struct


class Node:
    def __init__(self):
        self.hash = 0
        self.parent_node_index = 0
        self.first_child_node_index = 0
        self.next_sibling_node_index = 0
        self.dost = DefaultObjectSpaceTransform
        self.diost = DefaultInverseObjectSpaceTransform


class DefaultObjectSpaceTransform:
    def __init__(self):
        self.rotation = []
        self.location = []
        self.scale = 0
        

class DefaultInverseObjectSpaceTransform(DefaultObjectSpaceTransform):
    def __init__(self):
        super(DefaultInverseObjectSpaceTransform, self).__init__()


def get_skeleton(file):
    """
    Using sequential pathing for ease.
    default_object_space_transforms is dost
    default_inverse_object_space_transforms is diost
    """
    fbin = open(f'I:/d2_output_3_0_1_0/{gf.get_pkg_name(file)}/{file}.bin', 'rb').read()
    offset = fbin.find(b'\x42\x86\x80\x80') - 0x88
    if offset == -0x89:
        raise Exception('Not valid file')
    nodes_size = gf.get_uint32(fbin, offset)
    nodes_offset = gf.get_uint32(fbin, offset+0x8) + offset+0x8 + 0x10
    dost_size = gf.get_uint32(fbin, offset+0x10)
    dost_offset = gf.get_uint32(fbin, offset+0x18) + offset+0x18 + 0x10
    diost_size = gf.get_uint32(fbin, offset+0x20)
    diost_offset = gf.get_uint32(fbin, offset+0x28) + offset+0x28 + 0x10

    nodes = []

    # node definitions
    for i in range(nodes_offset, nodes_offset+0x10*nodes_size, 0x10):
        node = Node()
        node.hash = gf.get_uint32(fbin, i)
        node.parent_node_index = gf.get_int32(fbin, i+0x4)
        node.first_child_node_index = gf.get_int32(fbin, i+0x8)
        node.next_sibling_node_index = gf.get_int32(fbin, i+0xC)
        nodes.append(node)

    # default_object_space_transforms
    for a, i in enumerate(range(dost_offset, dost_offset+0x20*dost_size, 0x20)):
        node = nodes[a]
        node.dost = DefaultObjectSpaceTransform()
        node.dost.rotation = [struct.unpack('f', fbin[i + j:i+j+4])[0] for j in range(0, 0x10, 0x4)]
        node.dost.location = [struct.unpack('f', fbin[i + j:i+j+4])[0] for j in range(0x10, 0x1C, 0x4)]
        node.dost.scale = struct.unpack('f', fbin[i+0x1C:i+0x1C+4])[0]

    # default_inverse_object_space_transforms
    for a, i in enumerate(range(diost_offset, diost_offset+0x20*diost_size, 0x20)):
        node = nodes[a]
        node.diost = DefaultInverseObjectSpaceTransform()
        node.diost.rotation = [struct.unpack('f', fbin[i + j:i+j+4])[0] for j in range(0, 0x10, 0x4)]
        node.diost.location = [struct.unpack('f', fbin[i + j:i+j+4])[0] for j in range(0x10, 0x1C, 0x4)]
        node.diost.scale = struct.unpack('f', fbin[i+0x1C:i+0x1C+4])[0]

    return nodes


def test_export(file, nodes):
    with open(f'test_skel/{file}.obj', 'w') as f:
        f.write(f'o {file}\n')
        for n in nodes:
            f.write(f'v {n.dost.location[0]} {n.dost.location[1]} {n.dost.location[2]}\n')
    print(f'Test export complete for {file}')


if __name__ == '__main__':
    skeleton_file = '0148-0982'
    nodes = get_skeleton(skeleton_file)
    test_export(skeleton_file, nodes)
