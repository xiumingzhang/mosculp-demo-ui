# pylint: disable=W0108,R0903,W0201,W0212,E1003,E0632,E0203

from app_config import togglebutton_colors
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Callback, Color, Mesh, PopMatrix, PushMatrix, \
    RenderContext, Rotate, Scale, Translate, UpdateNormalMatrix
from kivy.graphics.opengl import GL_DEPTH_TEST, glDisable, glEnable
from kivy.graphics.transformation import Matrix
from kivy.logger import Logger
from kivy.properties import ListProperty, NumericProperty, ObjectProperty, \
    StringProperty
from kivy.resources import resource_find
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.dropdown import DropDown
from kivy.uix.widget import Widget
from objloader import ObjFile


class ScreenTab(BoxLayout):

    def build(self):
        self.model_tab_text = "3D Model"
        self.render_tab_text = "Rendering"
        self.add_widget(
            MyToggleButton(
                halign='center',
                text=self.model_tab_text,
                group='screen',
                allow_no_selection=False,
                on_release=lambda b: self._switch_screen(b),
            )
        )
        self.add_widget(
            MyToggleButton(
                halign='center',
                text=self.render_tab_text,
                group='screen',
                state='normal',
                allow_no_selection=False,
                on_release=lambda b: self._switch_screen(b),
            )
        )

    def _switch_screen(self, button):
        sm = self.parent.parent.parent
        sm.transition.duration = 0
        if button.text == self.model_tab_text:
            screen_id = 'model_screen'
        else:
            screen_id = 'render_screen'
        s = sm.ids[screen_id]
        clip = sm.current_screen.clip
        sm.current = s.name  # switch
        # Ensure the corresponding button is on
        for b in s.ids.tab.children:
            if b.text == button.text:
                b.state = 'down'
            else:
                b.state = 'normal'
        # Refresh viewers to avoid switching clips
        s.clip = clip
        if screen_id == 'model_screen':
            s._update_params()
            s.viewer.show(s.obj_file)
        else:
            s._update_params()
            s.viewer.show(s.img_file)


class Interactive(BoxLayout):
    renderer = ObjectProperty(None)

    def show(self, obj_file):
        self.renderer.render(obj_file)


class Renderer(Widget):

    def __init__(self, **kwargs):
        super(Renderer, self).__init__(**kwargs)
        self.canvas = RenderContext(compute_normal_mat=True)
        self.canvas.shader.source = resource_find('simple.glsl')
        self._touches = []

    def render(self, obj_file):
        self.canvas.clear()
        self.scene = ObjFile(obj_file)
        with self.canvas:
            self.cb = Callback(
                lambda args: glEnable(GL_DEPTH_TEST)
            )
            PushMatrix()
            self._setup_scene()
            PopMatrix()
            self.cb = Callback(
                lambda args: glDisable(GL_DEPTH_TEST)
            )
        Clock.schedule_interval(self._update_glsl, 1 / 60.)

    def _update_glsl(self, *_):
        p = self.parent.parent
        asp = float(p.width) / p.height * p.size_hint_y / p.size_hint_x
        proj = Matrix().view_clip(-asp, asp, -1, 1, 1, 100, 1)
        self.canvas['projection_mat'] = proj
        self.canvas['diffuse_light'] = (1.0, 1.0, 0.8)
        self.canvas['ambient_light'] = (0.1, 0.1, 0.1)

    def _setup_scene(self):
        for mi, m in enumerate(self.scene.objects.values()):
            Color(1, 1, 1, 1)
            PushMatrix()
            Translate(0, -0.3, -1.8)
            setattr(self, 'mesh%03d_rotx' % mi, Rotate(180, 1, 0, 0))
            setattr(self, 'mesh%03d_roty' % mi, Rotate(0, 0, 1, 0))
            setattr(self, 'mesh%03d_scale' % mi, Scale(1))
            UpdateNormalMatrix()
            mesh = Mesh(
                vertices=m.vertices,
                indices=m.indices,
                fmt=m.vertex_format,
                mode='triangles',
            )
            setattr(self, 'mesh%03d' % mi, mesh)
            PopMatrix()

    def _angle_from_touch(self, touch):
        x_angle = (touch.dx / self.width) * 360
        y_angle = -1 * (touch.dy / self.height) * 360
        return x_angle, y_angle

    def on_touch_down(self, touch):
        self._touch = touch
        touch.grab(self)
        self._touches.append(touch)

    def _scale_objects(self, scale):
        objs = self.scene.objects.values()
        for mi in range(len(objs)):
            mesh_scale = getattr(self, 'mesh%03d_scale' % mi)
            xyz = mesh_scale.xyz
            if scale != 0:
                mesh_scale.xyz = tuple(p + scale for p in xyz)

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            scale_factor = 0.01
            self._update_glsl()
            if touch in self._touches:
                if len(self._touches) == 1:
                    ax, ay = self._angle_from_touch(touch)
                    for mi in range(len(self.scene.objects.values())):
                        rot = getattr(self, 'mesh%03d_rotx' % mi)
                        rot.angle += ay
                        rot = getattr(self, 'mesh%03d_roty' % mi)
                        rot.angle -= ax
                elif len(self._touches) == 2:
                    # Use two touches to determine if we need scale
                    touch1, touch2 = self._touches
                    old_pos1 = (touch1.x - touch1.dx, touch1.y - touch1.dy)
                    old_pos2 = (touch2.x - touch2.dx, touch2.y - touch2.dy)
                    old_dx = old_pos1[0] - old_pos2[0]
                    old_dy = old_pos1[1] - old_pos2[1]
                    old_distance = old_dx ** 2 + old_dy ** 2
                    s = "old_distance = %s; " % old_distance
                    new_dx = touch1.x - touch2.x
                    new_dy = touch1.y - touch2.y
                    new_distance = new_dx ** 2 + new_dy ** 2
                    s += "new_distance = %s -> " % new_distance
                    if new_distance > old_distance:
                        scale = scale_factor
                        s += "scale up"
                    elif new_distance == old_distance:
                        scale = 0
                    else:
                        scale = -1 * scale_factor
                        s += "scale down"
                    Logger.debug(s)
                    self._scale_objects(scale)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            self._touches.remove(touch)


class HorizontalMenu(BoxLayout):
    pass


class VerticalMenu(BoxLayout):
    pass


class Picture(BoxLayout):
    img = ObjectProperty(None)

    def show(self, img_file):
        self.img.source = img_file  # local or online


class MyButton(Button):
    pass


class MyDropdownButton(Button):
    pass


class MyDropdown(DropDown):

    def __init__(self, button_suffices, base_color, **kwargs):
        super(self.__class__, self).__init__(**kwargs)
        n_buttons = len(button_suffices)
        for i, b_suffix in enumerate(button_suffices):
            c = list(base_color)
            c[3] = float(i + 1) / (n_buttons + 1) # varying transparency
            b = MyDropdownButton(
                text=b_suffix,
                background_color=c,
            )
            b.bind(on_release=lambda b: self.select(b.text))
            self.add_widget(b)

    def set_button_height(self, height):
        for c in self.children:
            for gc in c.children:
                gc.height = height


class MyLabel(Label):
    pass


class MyTitleLabel(MyLabel):
    pass


class MyToggleButton(ToggleButton):

    def on_state(self, _, value):
        # Toggle text, if necessary
        t = self.text
        if value == 'down' and t.endswith(': Off'):
            self.text = t.replace(': Off', ': On')
        elif value != 'down' and t.endswith(': On'):
            self.text = t.replace(': On', ': Off')
        # Toggle color
        t = self.text
        if t.endswith(': Off'):
            t = t.replace(': Off', ': On')
        c = togglebutton_colors[t]
        if value == 'normal':
            c = c[:3] + (0,)  # transparent, so will take background color
        self.background_color = c


class MySwitchButton(ToggleButton):
    text_on = StringProperty('')
    text_off = StringProperty('')
    bgcolor_on = ListProperty([])
    bgcolor_off = ListProperty([])

    def __init__(self, **kwargs):
        super(self.__class__, self).__init__(**kwargs)
        self.text_on = kwargs.get('text_on', '')
        self.text_off = kwargs.get('text_off', '')
        self.bgcolor_on = kwargs.get('bgcolor_on', (1, 1, 1, 1))
        self.bgcolor_off = kwargs.get('bgcolor_off', (1, 1, 1, 1))
        # Simulate switching to ensure start text/color correct
        self.state = 'normal'
        self.state = 'down'
        self.state = kwargs.get('state', 'normal')

    def on_state(self, _, value):
        if value == 'down':
            self.text = self.text_on
            self.background_color = self.bgcolor_on
        else:
            self.text = self.text_off
            self.background_color = self.bgcolor_off


class MyTextInput(TextInput):
    pass


class MyCheckbox(BoxLayout):

    def __init__(self, **kwargs):
        super(self.__class__, self).__init__(**kwargs)
        for k, v in kwargs.get('label_kwargs', {}).iteritems():
            setattr(self.ids.label, k, v)
        for k, v in kwargs.get('checkbox_kwargs', {}).iteritems():
            setattr(self.ids.checkbox, k, v)


class FloatSlider(Slider):
    screen = ObjectProperty(None)
    textinput = ObjectProperty(None)

    def on_slide(self, instance, value):
        """
        Update text input box
        """
        self.textinput.text = str(value)
        s = self.screen
        if instance.id == 'density':
            s.stickfig_density = value
        elif instance.id == 'transp':
            s.sculp_transp = value
        else:
            raise ValueError(instance.id)
        s._update_params()
        s.viewer.show(s.img_file)


class FrameSlider(Slider):
    textinput = ObjectProperty(None)
    viewer = ObjectProperty(None)
    img_paths = ListProperty([])
    is_good = ListProperty([])

    def on_slide(self, _, value):
        """
        Update text input box
        """
        v = int(value)  # 1-indexed
        self.textinput.text = str(v)
        self.viewer.show(self.img_paths[v - 1])
        if self.is_good[v - 1]:
            self.good_siwtch.state = 'down'
        else:
            self.good_siwtch.state = 'normal'


class FloatTextInput(MyTextInput):
    slider = ObjectProperty(None)
    density = NumericProperty(0)

    def on_text(self, _, value):
        """
        Bound text input and update slider
        """
        try:
            v = float(value)
        except ValueError:
            Logger.warn("Failed to convert '%s' to float" % value)
            v = None
        if v is not None:
            v = min(max(v, 0), 1)
            self.slider.value = v
            self.value = v
            self.text = str(v)


class FrameTextInput(MyTextInput):
    slider = ObjectProperty(None)

    def on_text(self, _, value):
        """
        Bound text input and update slider
        """
        try:
            v = int(value)
        except ValueError:
            Logger.warn("Failed to convert '%s' to int" % value)
            v = None
        if v is not None:
            v = int(min(max(v, 1), self.slider.max))
            self.slider.value = v
            self.value = v
            self.text = str(v)


# Zoom in/out on mouse wheel scrolling
def on_motion(win, etype, motionevent):
    # Prevent weakref from getting garbage-collected
    if not hasattr(win, 'renderer'):
        sm = win.children[0]
        renderer = sm.ids.model_screen.ids.viewer.ids.renderer
        setattr(win, 'renderer', renderer)  # make it an attribute
    # If user dictionary empty, not scrolling on filechooser, but on renderer
    if etype == 'end' and motionevent.ud == {}:
        scale_factor = 0.05
        b = motionevent.button
        if b == 'scrollup':
            win.renderer._scale_objects(scale_factor)
        elif b == 'scrolldown':
            win.renderer._scale_objects(-scale_factor)
Window.bind(on_motion=on_motion)
