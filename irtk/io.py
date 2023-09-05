from .config import *
import imageio
import imageio.v3 as iio
import numpy as np
import torch
from pathlib import Path
import gpytoolbox

# Download necessary imageio plugins. If they already exists they won't be 
# downloaded again. 
imageio.plugins.freeimage.download()

def read_mesh(mesh_path):
    v, f, uv, fuv = gpytoolbox.read_mesh(str(mesh_path), return_UV=True)
    if uv.size == 0:
        uv = np.zeros((0, 2))
        fuv = np.zeros((0, 3))
    return v, f, uv, fuv

def write_mesh(mesh_path, v, f, uv=None, fuv=None):
    v = to_numpy(v)
    f = to_numpy(f)
    if uv is not None: 
        uv = to_numpy(uv)
        if uv.size == 0:
            uv = None
    if fuv is not None: 
        fuv = to_numpy(fuv)
        if fuv.size == 0:
            fuv = None
    gpytoolbox.write_mesh(str(mesh_path), v, f, uv, fuv)

def linear_to_srgb(l):
    s = np.zeros_like(l)
    m = l <= 0.00313066844250063
    s[m] = l[m] * 12.92
    s[~m] = 1.055*(l[~m]**(1.0/2.4))-0.055
    return s

def srgb_to_linear(s):
    l = np.zeros_like(s)
    m = s <= 0.0404482362771082
    l[m] = s[m] / 12.92
    l[~m] = ((s[~m]+0.055)/1.055) ** 2.4
    return l

def to_srgb(image):
    image = to_numpy(image)
    if image.shape[2] == 4:
        image_alpha = image[:, :, 3:4]
        image = linear_to_srgb(image[:, :, 0:3])
        image = np.concatenate([image, image_alpha], axis=2)
    else:
        image = linear_to_srgb(image)
    return np.clip(image, 0, 1)

def to_linear(image):
    image = to_numpy(image)
    if image.shape[2] == 4:
        image_alpha = image[:, :, 3:4]
        image = srgb_to_linear(image[:, :, 0:3])
        image = np.concatenate([image, image_alpha], axis=2)
    else:
        image = srgb_to_linear(image)
    return image

def to_numpy(data):
    if torch.is_tensor(data):
        return data.detach().cpu().numpy()
    else:
        return np.array(data)
    
def to_torch(data, dtype):
    if torch.is_tensor(data):
        return data.to(dtype).to(device).contiguous()
    elif isinstance(data, np.ndarray):
        return torch.from_numpy(data).to(dtype).to(device).contiguous()
    else:
        return torch.tensor(data, dtype=dtype, device=device).contiguous()

def to_torch_f(data):
    return to_torch(data, ftype)

def to_torch_i(data):
    return to_torch(data, itype)

def read_image(image_path, is_srgb=None, remove_alpha=True):
    image_path = Path(image_path)
    
    image_ext = image_path.suffix
    iio_plugins = {
        '.exr': 'EXR-FI',
        '.hdr': 'HDR-FI',
        '.png': 'PNG-FI',
    }
    
    image = iio.imread(image_path, plugin=iio_plugins.get(image_ext))
    image = np.atleast_3d(image)
    
    if remove_alpha and image.shape[2] == 4:
        image = image[:, :, 0:3]

    if image.dtype == np.uint8 or image.dtype == np.int16:
        image = image.astype("float32") / 255.0
    elif image.dtype == np.uint16 or image.dtype == np.int32:
        image = image.astype("float32") / 65535.0

    if is_srgb is None:
        if image_ext in ['.exr', '.hdr', '.rgbe']:
            is_srgb = False
        else:
            is_srgb = True

    if is_srgb:
        image = to_linear(image)

    return image

def write_image(image_path, image, is_srgb=None):
    image_path = Path(image_path)
    
    image_ext = image_path.suffix
    iio_plugins = {
        '.exr': 'EXR-FI',
        '.hdr': 'HDR-FI',
        '.png': 'PNG-FI',
    }
    iio_flags = {
        '.exr': imageio.plugins.freeimage.IO_FLAGS.EXR_NONE,
    }
    hdr_formats = ['.exr', '.hdr', '.rgbe']
    
    image = to_numpy(image)
    image = np.atleast_3d(image)
    if image.shape[2] == 1:
        image = np.repeat(image, 3, axis=2)
        
    if image_ext in hdr_formats:
        is_srgb = False if is_srgb is None else is_srgb
    else:
        is_srgb = True if is_srgb is None else is_srgb
    if is_srgb:
        image = to_srgb(image)
        
    if image_ext in hdr_formats:
        image = image.astype(np.float32)
    else:
        image = (image * 255).astype(np.uint8)
    
    flags = iio_flags.get(image_ext)
    if flags is None: flags = 0
    
    iio.imwrite(image_path, image, 
                flags=flags,
                plugin=iio_plugins.get(image_ext))

def exr2png(image_path, verbose=False):
    image_path = Path(image_path)
    if image_path.is_dir():
        for p in image_path.glob('**/*.exr'):
            if verbose: print(p)
            im = read_image(p)
            write_image(p.with_suffix('.png'), im)
    elif image_path.suffix == '.exr':
        if verbose: print(image_path)
        im = read_image(image_path)
        write_image(image_path.with_suffix('.png'), im)

def write_video(video_path, frames, fps=20, kwargs={}):
    video_path = Path(video_path)
    video_path.parent.mkdir(exist_ok=True, parents=True)
    writer = imageio.get_writer(video_path, fps=fps, **kwargs)
    for frame in frames:
        frame = (to_srgb(to_numpy(frame)) * 255).astype(np.uint8)
        writer.append_data(frame)
    writer.close()