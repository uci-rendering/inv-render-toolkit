import torch 

def normalize(vector):
    return vector / torch.norm(vector)

def lookat(origin, target, up):
    device = origin.device
    dtype = origin.dtype 

    origin = origin
    dir = normalize(target - origin)
    left = normalize(torch.cross(up, dir))
    new_up = normalize(torch.cross(dir, left))

    to_world = torch.eye(4).to(device).to(dtype)
    to_world[:3, 0] = left
    to_world[:3, 1] = new_up
    to_world[:3, 2] = dir
    to_world[:3, 3] = origin

    return to_world

def translate(t_vec):
    device = t_vec.device
    dtype = t_vec.dtype 

    to_world = torch.eye(4).to(device).to(dtype)
    to_world[:3, 3] = t_vec

    return to_world

def rotate(axis, angle, use_degree=True):
    device = axis.device
    dtype = axis.dtype 

    to_world = torch.eye(4).to(device).to(dtype)
    axis = normalize(axis).reshape(3, 1)
    if use_degree:
        angle = torch.deg2rad(torch.tensor(angle))

    sin_theta = torch.sin(angle)
    cos_theta = torch.cos(angle)

    cpm = torch.zeros((3, 3)).to(device).to(dtype)
    cpm[0, 1] = -axis[2]
    cpm[0, 2] =  axis[1]
    cpm[1, 0] =  axis[2]
    cpm[1, 2] = -axis[0]
    cpm[2, 0] = -axis[1]
    cpm[2, 1] =  axis[0]

    R = cos_theta * torch.eye(3).to(device).to(dtype)
    R += sin_theta * cpm
    R += (1 - cos_theta) * (axis @ axis.T)

    to_world[:3, :3] = R

    return to_world

def scale(size):
    device = size.device
    dtype = size.dtype 

    to_world = torch.eye(4).to(device).to(dtype)
    to_world[:3, :3] = torch.diag(size).to(device).to(dtype)

    return to_world