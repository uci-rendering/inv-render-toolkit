# run from ./inv-render-toolkit with `python -m examples.0_introduction.code`

import irtk
from irtk.scene import *
from irtk.renderer import Renderer
from irtk.io import write_image

scene = Scene()
scene.set('armadillo', Mesh.from_file('./examples/data/meshes/armadillo.obj', mat_id='blue'))
scene.set('blue', DiffuseBRDF((0.2, 0.2, 0.9)))
# scene.set('envlight', EnvironmentLight.from_file('./examples/data/envmaps/factory.exr'))
scene.set('sensor', PerspectiveCamera.from_lookat(fov=40, origin=(-1.5, 1.5, 1.5), target=(0, 0, 0), up=(0, 1, 0)))
scene.set('film', HDRFilm(width=512, height=512))
# scene.set('integrator', Integrator(type='path', config={
#     'max_depth': 1,
#     'hide_emitters': False
# }))
scene.set('integrator', Integrator(type='collocated', config={
    'intensity': 10
}))

render = Renderer('psdr_jit', render_options={
    'spp': 128,
    'sppe': 0,
    'sppse': 0,
    'log_level': 0,
    'npass': 1
})
# image = render(scene)[0]
scene.set('sphere', Mesh.from_file('./examples/data/meshes/sphere.obj', mat_id='blue'))
image = render(scene)[0]

write_image('output/0_introduction/armadillo_psdr.png', image)