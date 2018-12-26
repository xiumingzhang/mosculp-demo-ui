from os.path import dirname, join
import kivy
from kivy.config import Config
from kivy.resources import resource_add_path


kivy.require('1.0.6')

app_name = "MoSculp"

# Window size
Config.set('graphics', 'width', '1080')
Config.set('graphics', 'height', '720')

# Resource directories
app_dir = dirname(__file__)
resource_add_path(join(app_dir, 'cm-unicode-0.7.0'))
resource_add_path(join(app_dir, 'icons'))

results_dir = join(app_dir, 'results')
web_root = 'http://mosculp.csail.mit.edu/demo-ui-data'
tmp_root = '/tmp/mosculp_gui'

clips = ['Ballet-1', 'Ballet-2', 'Olympic', 'Cartwheel', 'Federer']
readable2real = {
    'Ballet-1': 'ballet11-2',
    'Ballet-2': 'ballet11-1',
    'Olympic': 'olympicRunning_cut',
    'Cartwheel': 'as-somersault',
    'Federer': 'federer_cut',
}
real2readable = {v: k for k, v in readable2real.iteritems()}

body_parts = [
    "Body",
    "Left Upper Arm",
    "Left Lower Arm",
    "Right Upper Arm",
    "Right Lower Arm",
    "Left Upper Leg",
    "Left Lower Leg",
    "Right Upper Leg",
    "Right Lower Leg",
]

possible_mats = [
    "Leather",
    "Tarp",
    "Wood",
    "Original",
]

part_mat = {k: possible_mats[0] for k in body_parts}

lights = [
    "Left",
    "Middle",
    "Right",
]

params_default = {
    'clip': 'ballet11-2',
    'mode_3d': 'sculpture',
    'body_parts': ["Right Lower Arm"],
    'part_mat': part_mat,
    'lights': lights,
    'sculp_spec': True,
    'artistic_bg': False,
    'stickfig_density': 0,
    'sculp_transp': 0,
}

myred = (0.52, 0.19, 0.29)
myblue = (0.087, 0.39, 0.52)
mypurple = (0.29, 0, 0.45)
mygreen = (0, 0.40, 0.36)
mylightgreen = (0.47, 0.88, 0)
mylime = (0.86, 0.93, 0.78)
myyellow = (0.46, 0.41, 0.14)

label_color = mylime + (1,)

button_color = myblue + (1,)

togglebutton_colors = {
    '3D Model': myred + (1,),
    'Rendering': myred + (1,),
    'Sculpture Specularity: On': mygreen + (1,),
    'Synthetic\nBackground: On': myyellow + (1,),
}

switchbutton_colors = {
    'Mode: Sculpture': mypurple + (1,),
    'Mode: Collection of Humans': myyellow + (1,),
}
