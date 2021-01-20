import gf
import struct
import fbx
import pyfbx_jo as pfb
import FbxCommon
import scipy.spatial
import numpy as np
import quaternion


class Node:
    def __init__(self):
        self.hash = 0
        self.parent_node_index = 0
        self.first_child_node_index = 0
        self.next_sibling_node_index = 0
        self.dost = DefaultObjectSpaceTransform()
        self.diost = DefaultInverseObjectSpaceTransform()
        self.fbxnode = None


class DefaultObjectSpaceTransform:
    def __init__(self):
        self.rotation = []
        self.location = []
        self.scale = 0


class DefaultInverseObjectSpaceTransform(DefaultObjectSpaceTransform):
    def __init__(self):
        super(DefaultInverseObjectSpaceTransform, self).__init__()


def get_skeleton(file, names):
    """
    Using sequential pathing for ease.
    default_object_space_transforms is dost
    default_inverse_object_space_transforms is diost
    """
    fbin = open(f'I:/d2_output_3_0_2_0/{gf.get_pkg_name(file)}/{file}.bin', 'rb').read()
    offset = fbin.find(b'\x42\x86\x80\x80') - 0x88
    if offset == -0x89:
        raise Exception('Not valid file')
    nodes_size = gf.get_uint32(fbin, offset)
    nodes_offset = gf.get_uint32(fbin, offset + 0x8) + offset + 0x8 + 0x10
    dost_size = gf.get_uint32(fbin, offset + 0x10)
    dost_offset = gf.get_uint32(fbin, offset + 0x18) + offset + 0x18 + 0x10
    diost_size = gf.get_uint32(fbin, offset + 0x20)
    diost_offset = gf.get_uint32(fbin, offset + 0x28) + offset + 0x28 + 0x10

    nodes = []

    # node definitions
    for i in range(nodes_offset, nodes_offset + 0x10 * nodes_size, 0x10):
        node = Node()
        node.hash = str(gf.get_uint32(fbin, i))
        if node.hash in names:
            node.name = names[node.hash]
        else:
            node.name = 'unk_' + node.hash
        node.parent_node_index = gf.get_int32(fbin, i + 0x4)
        node.first_child_node_index = gf.get_int32(fbin, i + 0x8)
        node.next_sibling_node_index = gf.get_int32(fbin, i + 0xC)
        nodes.append(node)

    # default_object_space_transforms
    for a, i in enumerate(range(dost_offset, dost_offset + 0x20 * dost_size, 0x20)):
        node = nodes[a]
        node.dost = DefaultObjectSpaceTransform()
        node.dost.rotation = [struct.unpack('f', fbin[i + j:i + j + 4])[0] for j in range(0, 0x10, 0x4)]
        node.dost.rotation = [node.dost.rotation[0], node.dost.rotation[1], node.dost.rotation[2],
                              node.dost.rotation[3]]
        node.dost.location = [struct.unpack('f', fbin[i + j:i + j + 4])[0] for j in range(0x10, 0x1C, 0x4)]
        node.dost.scale = struct.unpack('f', fbin[i + 0x1C:i + 0x1C + 4])[0]

    # default_inverse_object_space_transforms
    for a, i in enumerate(range(diost_offset, diost_offset + 0x20 * diost_size, 0x20)):
        node = nodes[a]
        node.diost = DefaultInverseObjectSpaceTransform()
        node.diost.rotation = [struct.unpack('f', fbin[i + j:i + j + 4])[0] for j in range(0, 0x10, 0x4)]
        node.diost.location = [struct.unpack('f', fbin[i + j:i + j + 4])[0] for j in range(0x10, 0x1C, 0x4)]
        node.diost.scale = struct.unpack('f', fbin[i + 0x1C:i + 0x1C + 4])[0]

    return nodes


def test_export(file, nodes, name):
    with open(f'I:/skeletons/{file}_{name}.obj', 'w') as f:
        f.write(f'o {file}\n')
        for n in nodes:
            f.write(f'v {-n.diost.location[0]} {n.diost.location[2]} {n.diost.location[1]}\n')
    print(f'Test export complete for {file}_{name}')


def write_info_out(file, nodes, name):
    with open(f'I:/skeletons/{file}_{name}.info', 'w') as f:
        for i, n in enumerate(nodes):
            f.write(f'Node {i}:\n')
            f.write(f'name {n.name}\n')
            f.write(f'hash {n.hash}\n')
            f.write(f'first_child_node_index {n.first_child_node_index}\n')
            f.write(f'next_sibling_node_index {n.next_sibling_node_index}\n')
            f.write(f'parent_node_index {n.parent_node_index}\n')
            # f.write(f'default_inverse_object_space_transforms loc {n.diost.location}\n')
            # f.write(f'default_inverse_object_space_transforms rot {n.diost.rotation} {scipy.spatial.transform.Rotation.from_quat(node.dost.rotation).as_euler('xyz', degrees=True)\n')
            # f.write(f'default_inverse_object_space_transforms scale {n.diost.scale}\n')
            f.write(f'default_object_space_transforms loc {n.dost.location}\n')
            f.write(f'default_object_space_transforms rot {[round(x, 2) for x in scipy.spatial.transform.Rotation.from_quat(n.dost.rotation).as_euler("xyz", degrees=True)]} {[round(x, 2) for x in n.dost.rotation]}\n')
            f.write(f'default_inverse_object_space_transforms loc {[round(x, 2) for x in n.diost.location]}\n')
            f.write(f'default_inverse_object_space_transforms rot {[round(x, 2) for x in scipy.spatial.transform.Rotation.from_quat(n.diost.rotation).as_euler("xyz", degrees=True)]} {[round(x, 2) for x in n.diost.rotation]}\n')

            f.write(f'default_object_space_transforms scale {n.diost.scale}\n\n')
    print(f'Info export complete for {file}_{name}')


def get_skeleton_names():
    names = {}
    with open('bone_names.json') as f:
        f = f.readlines()
        for l in f:
            s = l.split(',')
            names[s[0]] = s[1].strip()
    return names


def qmulv(q: fbx.FbxQuaternion, v: fbx.FbxVector4):
    m = (q[1] * v[2] - q[2] * v[1]) + q[3] * v[0]
    n = (q[2] * v[0] - q[0] * v[2]) + q[3] * v[1]
    o = (q[0] * v[1] - q[1] * v[0]) + q[3] * v[2]

    a = (o * q[1] - n * q[2])
    a += a + v[0]
    b = (m * q[2] - o * q[0])
    b += b + v[1]
    c = (n * q[0] - m * q[1])
    c += c + v[2]
    out = fbx.FbxDouble3(a, b, c)

    return out


def write_fbx_skeleton(file, nodes, name):
    lSdkManager, lScene = FbxCommon.InitializeSdkObjects()
    # Adding proper fbx nodes
    rotarray = [[0, 0, 0]]*len(nodes)
    for node in nodes:
        nodeatt = fbx.FbxSkeleton.Create(lSdkManager, node.name)
        if node.parent_node_index == -1:  # At root
            nodeatt.SetSkeletonType(fbx.FbxSkeleton.eRoot)
        elif node.first_child_node_index == -1:  # At end
            nodeatt.SetSkeletonType(fbx.FbxSkeleton.eLimbNode)
        else:  # In the middle somewhere
            nodeatt.SetSkeletonType(fbx.FbxSkeleton.eLimbNode)
        nodeatt.Size.Set(node.dost.scale)
        node.fbxnode = fbx.FbxNode.Create(lSdkManager, node.name)
        node.fbxnode.SetNodeAttribute(nodeatt)
        r = scipy.spatial.transform.Rotation.from_quat(node.dost.rotation).as_euler('xyz', degrees=True)
        rot = r
        if node.name == 'b_spine_2' and False:  # node.parent_node_index > 0:
            n = scipy.spatial.transform.Rotation.from_quat(nodes[node.parent_node_index].dost.rotation).as_euler('xyz',
                                                                                                                 degrees=True)
            k = scipy.spatial.transform.Rotation.from_quat(nodes[node.parent_node_index].dost.rotation)
            rot = [r[i] - n[i] for i in range(3)]
            worldTM = nodes[node.parent_node_index].fbxnode.EvaluateGlobalTransform()
            u = worldTM.GetQ()
            q = quaternion.from_float_array([u[0], u[1], u[2], u[3]]).inverse()
            q = quaternion.as_float_array(q)
            # fbx.FbxVector4(rot[0], rot[1], rot[2])
            # +X Z +Y
            newVector = qmulv(fbx.FbxQuaternion(q[0], q[1], q[2], q[3]), fbx.FbxVector4(0, 0, 45))
            node.fbxnode.LclRotation.Set(newVector)
        elif node.name == 'b_spine_3' and False:
            n = scipy.spatial.transform.Rotation.from_quat(nodes[node.parent_node_index].dost.rotation).as_euler('xyz',
                                                                                                                 degrees=True)
            k = scipy.spatial.transform.Rotation.from_quat(nodes[node.parent_node_index].dost.rotation)
            rot = [r[i] - n[i] for i in range(3)]
            worldTM = nodes[node.parent_node_index].fbxnode.EvaluateGlobalTransform()
            u = worldTM.GetQ()
            q = quaternion.from_float_array([u[0], u[1], u[2], u[3]]).inverse()
            q = quaternion.as_float_array(q)
            # fbx.FbxVector4(rot[0], rot[1], rot[2])
            # +X Z +Y
            newVector = qmulv(fbx.FbxQuaternion(q[0], q[1], q[2], q[3]), fbx.FbxVector4(rot[0], rot[1], rot[2]))
            node.fbxnode.LclRotation.Set(newVector)
        elif node.name == 'b_l_forearm':
            """
            Goal is to singularly make this node the only one affected, and every other node unaffected.
            """
            n = scipy.spatial.transform.Rotation.from_quat(nodes[node.parent_node_index].dost.rotation).as_euler('xyz',
                                                                                                                 degrees=True)
            k = scipy.spatial.transform.Rotation.from_quat(nodes[node.parent_node_index].dost.rotation)
            u = scipy.spatial.transform.Rotation.from_quat(node.dost.rotation).as_rotvec()
            # rot = [r[i] - n[i] for i in range(3)]
            worldTM = nodes[node.parent_node_index].fbxnode.EvaluateGlobalTransform()
            u = worldTM.GetQ()
            q = quaternion.from_float_array([u[0], u[1], u[2], u[3]]).inverse()
            q = quaternion.as_float_array(q)
            # fbx.FbxVector4(rot[0], rot[1], rot[2])
            newVector = qmulv(fbx.FbxQuaternion(q[0], q[1], q[2], q[3]), fbx.FbxVector4(rot[0], rot[1], rot[2]))
            rot = [x*np.pi/180 for x in [150, 90, 45]]
            tosend = scipy.spatial.transform.Rotation.from_rotvec(rot).as_euler('xyz', degrees=True)
            # tosend = [x*180/np.pi for x in scipy.spatial.transform.Rotation.from_quat(node.dost.rotation).as_rotvec()]
            # node.fbxnode.LclRotation.Set(fbx.FbxDouble3(tosend[0], tosend[1], tosend[2]))
            q = node.diost.rotation
            print(node.dost.rotation, node.diost.rotation)
            # node.fbxnode.LclRotation.Set(fbx.FbxQuaternion(q[0], q[1], q[2], q[3]))
            r = scipy.spatial.transform.Rotation.from_quat(node.dost.rotation).as_euler('xyz', degrees=True)
            node.fbxnode.SetGeometricRotation(fbx.FbxNode.eDestinationPivot, fbx.FbxVector4(-r[0], r[1], r[2]))
            # node.fbxnode.LclRotation.Set(fbx.FbxDouble3(-90, 180, 0))
            node.fbxnode.LclRotation.Set(fbx.FbxDouble3(-130 , 90 - rot[1], 90 + rot[2]))
            print(node.name, tosend)
            inv = scipy.spatial.transform.Rotation.from_rotvec(rot).inv().as_euler('xyz', degrees=True)
            inv = [x*180/np.pi for x in scipy.spatial.transform.Rotation.from_quat(node.dost.rotation).inv().as_rotvec()]
            rotarray[nodes.index(node)] = inv
        elif node.parent_node_index > 0:
            # n = scipy.spatial.transform.Rotation.from_quat(nodes[node.parent_node_index].dost.rotation).inv().as_euler('xyz', degrees=True)
            # k = nodes[node.parent_node_index].fbxnode.EvaluateGlobalTransform().GetR()
            k = rotarray[node.parent_node_index]
            # rot = [0 + k[i] for i in range(3)]
            node.fbxnode.LclRotation.Set(fbx.FbxDouble3(k[0], k[1], k[2]))

        # elif node.parent_node_index > 0:
        #     worldTM = nodes[node.parent_node_index].fbxnode.EvaluateGlobalTransform()
        #     u = worldTM.GetQ()
        #     q = quaternion.from_float_array([u[0], u[1], u[2], u[3]]).inverse()
        #     q = quaternion.as_float_array(q)
        #     newVector = qmulv(fbx.FbxQuaternion(q[0], q[1], q[2], q[3]), fbx.FbxVector4(0, 0, 90))
        #     node.fbxnode.LclRotation.Set(newVector)

        # rot = scipy.spatial.transform.Rotation.apply(k, rot, inverse=False)

        node.fbxnode.SetTransformationInheritType(fbx.FbxTransform.eInheritRrs)
        if node.parent_node_index != -1:  # Checking to see if rotation is inherited
            a = 0
            # node.fbxnode.LclRotation.Set(fbx.FbxDouble3(rot[0], rot[1], rot[2]))
            # node.fbxnode.SetGeometricRotation(fbx.FbxNode.eSourcePivot, fbx.FbxVector4(rot[0], rot[1], rot[2]))

        if node.parent_node_index != -1:
            n = scipy.spatial.transform.Rotation.from_quat(nodes[node.parent_node_index].dost.rotation)
            a = nodes[node.parent_node_index].fbxnode.EvaluateGlobalTransform().GetQ()
            # n = scipy.spatial.transform.Rotation.from_quat([a[0], a[1], a[2], a[3]])
            # Fix for inherited translation
            loc = [node.dost.location[i] - nodes[node.parent_node_index].dost.location[i] for i in range(3)]

            if not np.allclose(rotarray[node.parent_node_index], [0, 0, 0]):
                loc = scipy.spatial.transform.Rotation.apply(n, loc, inverse=True)
        else:
            loc = node.dost.location
        node.fbxnode.LclTranslation.Set(fbx.FbxDouble3(loc[0], loc[1], loc[2]))
        # node.fbxnode.LclTranslation.Set(fbx.FbxDouble3(node.dost.location[0], node.dost.location[1], node.dost.location[2]))

    # Building heirachy
    root = None
    for i, node in enumerate(nodes):
        want = [
            'b_pedestal',
            'b_pelvis',
            'b_spine_1',
            'b_spine_2',
            'b_spine_3',
            'b_l_clav',
            'b_r_clav',
            'b_neck_1',
            'b_neck_2'
        ]
        # if i > 10:
        #     break
        # we want the spine to be perfectly straight. When it is, it's likely the rotation is correct.
        # if node.name not in want:
        #     continue

        """
        Notes:
        - looks like incorrect axis of rotation being used for some bits
        """

        if node.parent_node_index != -1:
            nodes[node.parent_node_index].fbxnode.AddChild(node.fbxnode)
            print(f'{nodes[node.parent_node_index].hash} has child {node.hash}')
        else:
            root = node

    if root:
        lScene.GetRootNode().AddChild(root.fbxnode)
        # lScene.GetRootNode().SetRotationActive(True)
        # lScene.GetRootNode().LclRotation(fbx.FbxDouble3(-90, 180, 0))
        lResult = FbxCommon.SaveScene(lSdkManager, lScene, f'I:/skeletons/{file}_{name}.fbx')


if __name__ == '__main__':
    skeleton_file = '0186-138F'
    names = get_skeleton_names()
    nodes = get_skeleton(skeleton_file, names)
    name = 'player'
    test_export(skeleton_file, nodes, name)
    write_info_out(skeleton_file, nodes, name)
    write_fbx_skeleton(skeleton_file, nodes, name)

    """
    Rotation is inherited across the skeleton. This poses (aha) an issue, since the rotations given seem to be per-bone and not inherit based.
    """