from .connector import get_connector
import torch 
import numpy as np

import gin

class RenderFunction(torch.autograd.Function):

    @staticmethod
    def forward(ctx, connector, scene, render_options, sensor_ids, integrator_id, device, dtype, *params):
        images = connector.renderC(scene, render_options, sensor_ids=sensor_ids, integrator_id=integrator_id)
        if isinstance(images[0], np.ndarray):
            images = [torch.from_numpy(image) for image in images]
        images = [image.to(device).to(dtype) for image in images]
        images = torch.stack(images, dim=0)

        ctx.connector = connector
        ctx.scene = scene
        ctx.render_options = render_options
        ctx.params = params
        ctx.sensor_ids = sensor_ids
        ctx.integrator_id = integrator_id
        assert(images.sum().isfinite())
        return images

    @staticmethod
    def backward(ctx, grad_out):
        image_grads = [image_grad for image_grad in grad_out]
        options = ctx.scene.bck_options if ctx.scene.bck_options else ctx.render_options
        options['seed'] = ctx.render_options['seed']
        param_grads = ctx.connector.renderD(image_grads, ctx.scene, options, ctx.sensor_ids, ctx.integrator_id)
        return tuple([None] * 7 + param_grads)

@gin.configurable
class Renderer(torch.nn.Module):

    def __init__(self, connector_name, render_options=None):
        super().__init__()
        self.connector = get_connector(connector_name)
        self.render_options = render_options

    def forward(self, scene, sensor_ids=[0], integrator_id=0):
        assert self.render_options is not None, "Please set render options first."
        if torch.is_tensor(sensor_ids):
            sensor_ids = sensor_ids.flatten().tolist()

        params = [scene[param_name].data for param_name in scene.get_requiring_grad()]
        
        images = RenderFunction.apply(self.connector, scene, self.render_options, sensor_ids, integrator_id, scene.device, scene.ftype, *params)
        return images

    def set_render_options(self, render_options, bck_options=None):
        self.render_options = render_options