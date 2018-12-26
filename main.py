# pylint: disable=R0903,W0201,E0102,R0201

from sys import argv
from copy import deepcopy
from os import makedirs, remove
from os.path import join, exists
from shutil import rmtree
import tarfile
from kivy.app import App
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import Screen
from app_config import app_name, clips, body_parts, part_mat, \
    button_color, label_color, lights, params_default, web_root, tmp_root, \
    possible_mats, switchbutton_colors, readable2real, real2readable
from my import FloatSlider, FloatTextInput, MyDropdown, MyButton, \
    MyCheckbox, MyLabel, MySwitchButton, MyTitleLabel, MyToggleButton
from composite_online import main as composite, MyURLopener


class ModelScreen(Screen):
    tab = ObjectProperty(None)
    viewer = ObjectProperty(None)
    menu = ObjectProperty(None)
    clip_button = ObjectProperty(None)

    def build(self):
        for k, v in params_default.iteritems():
            setattr(self, k, deepcopy(v))
        self._update_params()

        # Tabs for switching screens
        self.tab.build()

        self.viewer.show(self.obj_file)

        # Clip selecting
        b = MyButton(
            text="Clip: " + real2readable[params_default['clip']],
            background_color=button_color,
        )
        dd = MyDropdown(clips, button_color)
        dd.set_button_height(0.7 * b.height)
        def f(b=b):
            dd.open(b)
        b.bind(on_release=f)
        dd.bind(on_select=self._switch_clip)
        self.menu.add_widget(b)
        self.clip_button = b

        # Switching between all-mesh collection and sculpture
        t_on = "Mode: Collection of Humans"
        t_off = "Mode: Sculpture"
        self.menu.add_widget(
            MySwitchButton(
                text_on=t_on,
                text_off=t_off,
                bgcolor_on=switchbutton_colors[t_on],
                bgcolor_off=switchbutton_colors[t_off],
                on_release=self._switch_mode,
            )
        )

    def _switch_clip(self, _, clip_name):
        setattr(self.clip_button, 'text', "Clip: " + clip_name)
        self.clip = readable2real[clip_name]
        # Update screen with new clip
        self._update_params()
        self.viewer.show(self.obj_file)

    def _switch_mode(self, button):
        if button.text.endswith(': Sculpture'):
            self.mode_3d = 'sculpture'
        elif button.text.endswith(': Collection of Humans'):
            self.mode_3d = 'all-mesh'
        else:
            raise ValueError(button.text)
        # Update screen with new clip
        self._update_params()
        self.viewer.show(self.obj_file)

    def _update_params(self):
        folder = join(self.clip, 'obj')
        if not exists(join(tmp_root, folder)):
            makedirs(join(tmp_root, folder))
        # Load sculpture RGB
        remote_f = join(web_root, folder, self.mode_3d + '.obj')
        local_f = join(tmp_root, folder, self.mode_3d + '.obj')
        MyURLopener().lazy_retrieve(remote_f, local_f)
        self.obj_file = local_f


class RenderScreen(Screen):
    tab = ObjectProperty(None)
    side_menu = ObjectProperty(None)
    viewer = ObjectProperty(None)
    menu = ObjectProperty(None)

    def build(self):
        for k, v in params_default.iteritems():
            setattr(self, k, deepcopy(v))
        self._update_params()

        # Tabs for switching screens
        self.tab.build()

        self.viewer.show(self.img_file)

        # Body part menu
        self._add_vplaceholder()
        list_name = "Body Parts"
        self.side_menu.add_widget(
            MyTitleLabel(
                text=list_name,
                color=label_color,
            )
        )
        for p in body_parts:
            b = MyCheckbox(
                label_kwargs={'text': "%s (%s)" % (p, part_mat[p])},
                checkbox_kwargs={
                    'state': 'down' if p in self.body_parts else 'normal'
                },
            )
            def f(b=b):  # force early binding
                self._on_check(b)
            b.ids.checkbox.on_release = f
            self.side_menu.add_widget(b)

        # Material menu
        self._add_vplaceholder()
        list_name = "Part Material: %s" % self.body_parts[0]
        mat_title = MyTitleLabel(
            text=list_name,
            color=label_color,
        )
        self.mat_title = mat_title
        self.side_menu.add_widget(mat_title)
        for m in possible_mats:
            if m == part_mat[body_parts[0]]:
                state = 'down'
            else:
                state = 'normal'
            b = MyCheckbox(
                label_kwargs={'text': m},
                checkbox_kwargs={
                    'group': 'mat',
                    'state': state,
                },
            )
            def f(b=b):  # force early binding
                self._on_check(b)
            b.ids.checkbox.on_release = f
            self.side_menu.add_widget(b)

        # Lighting menu
        self._add_vplaceholder()
        list_name = "Lighting"
        self.side_menu.add_widget(
            MyTitleLabel(
                text=list_name,
                color=label_color,
            )
        )
        for l in lights:
            b = MyCheckbox(
                label_kwargs={'text': l},
                checkbox_kwargs={
                    'state': 'down' if l in self.lights else 'normal'
                },
            )
            def f(b=b):  # force early binding
                self._on_check(b)
            b.ids.checkbox.on_release = f
            self.side_menu.add_widget(b)

        # Slider for density of stick figures
        self._add_vplaceholder()
        s_den = FloatSlider(
            id='density',
            screen=self,
            size_hint_x=0.2,
        )
        t_den = FloatTextInput(slider=s_den)
        t_den.bind(text=t_den.on_text)  # if text changes, update slider
        s_den.textinput = t_den
        s_den.bind(value=s_den.on_slide)  # if value changes, update text box
        self.menu.add_widget(
            MyLabel(
                text="Keyframe Density",
                halign='right',
                size_hint_x=0.25,
            )
        )
        self.menu.add_widget(t_den)
        self.menu.add_widget(s_den)

        # Slider for sculpture transparency
        s_transp = FloatSlider(
            id='transp',
            screen=self,
            size_hint_x=0.2,
            max=0.8,
        )
        t_transp = FloatTextInput(slider=s_transp)
        t_transp.bind(text=t_transp.on_text)
        s_transp.textinput = t_transp
        s_transp.bind(value=s_transp.on_slide)
        self.menu.add_widget(
            MyLabel(
                text="Sculpture Transparency",
                halign='right',
                size_hint_x=0.25,
            )
        )
        self.menu.add_widget(t_transp)
        self.menu.add_widget(s_transp)

        # Specularity toggle
        self._add_hplaceholder()
        self.menu.add_widget(
            MyToggleButton(
                id='spec',
                text="Sculpture Specularity: On",
                on_release=self._on_toggle,
                size_hint_x=0.4,
            )
        )

        # Synthetic background toggle
        self.menu.add_widget(
            MyToggleButton(
                id='artbg',
                text="Synthetic\nBackground: Off",
                state='normal',
                on_release=self._on_toggle,
                size_hint_x=0.4,
            )
        )

    def _on_toggle(self, button):
        if button.id == 'spec':
            self.sculp_spec = button.state == 'down'
        else:
            self.artistic_bg = button.state == 'down'
        self._update_params()
        self.viewer.show(self.img_file)

    def _on_check(self, mycheckbox_ins):
        checkbox = mycheckbox_ins.ids.checkbox
        label = mycheckbox_ins.ids.label.text
        label = label.split(' (')[0]

        # Forbid the deselection if this is the only part selected
        if ((len(self.body_parts) == 1 and label in self.body_parts) \
                or (len(self.lights) == 1 and label in self.lights)) \
                and checkbox.state == 'normal':
            checkbox.state = 'down'
            return

        if label in body_parts:
            if checkbox.state == 'down' and label not in self.body_parts:
                self.body_parts.append(label)
            elif checkbox.state == 'normal' and label in self.body_parts:
                self.body_parts.remove(label)
            # Update part material title
            title_text = self.mat_title.text
            self.mat_title.text = title_text.replace(
                title_text[title_text.index(':'):],
                ": " + label,
            )
            # Update material selection
            mat = self.part_mat[label]
            for child in self.side_menu.children:
                if 'checkbox' in child.ids:
                    if child.ids['checkbox'].group == 'mat':
                        if child.ids['label'].text == mat:
                            child.ids['checkbox'].state = 'down'
                        else:
                            child.ids['checkbox'].state = 'normal'
        elif label in lights:
            if checkbox.state == 'down' and label not in self.lights:
                self.lights.append(label)
            elif checkbox.state == 'normal' and label in self.lights:
                self.lights.remove(label)
        elif label in possible_mats:
            i = self.mat_title.text.index(':')
            curr_part = self.mat_title.text[(i + 2):]
            self.part_mat[curr_part] = label
            # Update material name besides body part names
            for child in self.side_menu.children:
                if 'checkbox' in child.ids:
                    text = child.ids['label'].text
                    if ' (' in text:
                        part_name = text.split(' (')[0]
                        child.ids['label'].text = "%s (%s)" % (part_name, self.part_mat[part_name])
        else:
            raise ValueError(label)
        self._update_params()
        self.viewer.show(self.img_file)

    def _update_params(self):
        self.img_file = composite(
            {
                'clip': self.clip,
                'density': self.stickfig_density,
                'lights': self.lights,
                'transp': self.sculp_transp,
                'spec': self.sculp_spec,
                'part': self.body_parts,
                'mat': {
                    k.replace(' ', ''): v
                    for k, v in self.part_mat.iteritems()
                },
            },
            self.artistic_bg,
            cache=True,
        )

    def _add_hplaceholder(self):
        self.menu.add_widget(
            MyLabel(
                size_hint_x=0.05,
            )
        )

    def _add_vplaceholder(self):
        self.side_menu.add_widget(
            MyLabel(
                size_hint_y=0.3,
            )
        )


class MyApp(App):

    def build(self):
        self.title = app_name
        sm = self.root
        for s in sm.ids.values():
            s.build()
        sm.current = sm.ids.model_screen.name

    def on_pause(self):
        return True


def main():
    # Predownload data to be real-time responsive (optional)
    folders = [
        'obj',
        'frames_for-ui-resp',
        'composite_enum_idxmap_for-ui-resp',
        'render_enum_for-ui-resp',
    ]
    if len(argv) > 1:
        # One or more clips given for pre-downloading
        for clip_name in argv[1:]:
            clip_name = readable2real[clip_name]
            for folder in folders:
                remote_folder = join(web_root, clip_name, folder)
                local_folder = join(tmp_root, clip_name, folder)
                local_zip = local_folder + '.tar.gz'
                MyURLopener().lazy_retrieve(remote_folder + '.tar.gz', local_zip)
                h = tarfile.open(local_zip, "r:gz")
                if exists(local_folder):
                    rmtree(local_folder)
                makedirs(local_folder)
                h.extractall(join(local_folder, '..'))
                h.close()
        # Update default clip to the final pre-downloaded clip
        params_default['clip'] = clip_name

    MyApp().run()


if __name__ == '__main__':
    main()
