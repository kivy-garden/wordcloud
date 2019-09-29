# coding: utf8
from math import cos, sin, pi
from random import choice, gauss
from time import time

from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.factory import Factory
from kivy.clock import Clock, mainthread
from kivy.animation import Animation
from kivy.properties import (
    ListProperty,
    DictProperty,
    ObjectProperty,
    NumericProperty,
)

__version__ = '1.0.0'


Builder.load_string('''
#:import RC kivy.utils.get_random_color
#:import choice random.choice
#:import rgba kivy.utils.rgba

<-CloudLabel>:
    size: self.texture_size
    colors: []
    color: self.colors and rgba(choice(self.colors)) or RC()
    canvas:
        PushMatrix:
        Scale:
            origin: self.center
            xyz: self.zoom, self.zoom, 0
        Rotate:
            origin: self.center
            angle: self.angle
        Translate:
            x: self.offset_x
            y: self.offset_y

        Color:
            rgba: self.tint

        Rectangle:
            pos: self.pos
            size: self.size
            texture: self.texture

    canvas.after:
        PopMatrix:
''')


class CloudLabel(Factory.Label):
    zoom = NumericProperty(1)
    angle = NumericProperty()
    offset_x = NumericProperty(0)
    offset_y = NumericProperty(0)
    tint = ListProperty((1, 1, 1, 1))


class WordCloud(Widget):
    '`words` The list of words to animate'
    words = ListProperty()

    '`label_options` A dict of options to apply to the label'
    label_options = DictProperty()

    '`label_cls` Can be used to override the class of the item'
    label_cls = ObjectProperty('Label')

    '`layout_interval` how much time to wait between two words'
    layout_interval = NumericProperty(0.01)

    '''`angle_increase` manage how much the angle increases each
    iteration'''
    angle_increase = NumericProperty(pi / 100)

    '''`distance_increase` manage how much the distance from center
    increases each iteration.'''
    distance_increase = NumericProperty(.1)

    __events__ = ('on_post_populate', 'on_pre_populate')

    def __init__(self, **kwargs):
        self.cache = {}
        self.bind(pos=self.layout, size=self.layout)
        super(WordCloud, self).__init__(**kwargs)

    def animate_focused_word(self, dt=0):
        '''Override this method to customize the effect on focused word.

        exmaple of possible animations::

            zoom = (
                Animation(zoom=1.1, d=.7, t='out_elastic')
                + Animation(d=.3)
                + Animation(zoom=1, d=.3, t='out_quad')
            )

            bounce = (
                Animation(offset_y=25, d=.1, t='out_quad')
                + Animation(offset_y=0, d=.5, t='out_bounce')
            )

            flash = (
                Animation(tint=(5, 5, 5, 2), d=.1, t='out_quad')
                + Animation(tint=(1, 1, 1, 1), d=.5, t='out_bounce')
            )

        Don't forget to cancel any previous animation of the animated
        properties before starting one, to avoid fighting between
        animations.

        '''
        if self.words:
            lbl = self.cache.get(choice(self.words))
            if lbl:
                Animation.cancel_all(lbl, 'zoom')
                (
                    Animation(zoom=1.1, d=.7, t='out_elastic')
                    + Animation(d=.3)
                    + Animation(zoom=1, d=.3, t='out_quad')
                ).start(lbl)


        Clock.schedule_once(self.animate_focused_word, abs(gauss(.5, .3)))

    def on_post_populate(self, *args):
        pass

    def on_pre_populate(self, *args):
        pass

    def cancel_animate_focused_word(self, *args):
        Clock.unschedule(self.animate_focused_word)

    def layout(self, *args):
        self.clear_widgets()
        if not self.cache:
            return

        self._to_layout = self.words[:]
        self._angle = self._distance = 0
        Clock.unschedule(self._layout)
        Clock.schedule_interval(self._layout, self.layout_interval)

    def _layout(self, dt):
        self._angle = 0
        self._distance = 0
        while self._to_layout:
            w = self._to_layout.pop(0)
            lbl = self.cache.get(w)
            lbl.center = self.center

            while any(
                lbl.collide_widget(x)
                for x in self.children
            ):
                self._angle += self.angle_increase
                self._distance += self.distance_increase

                lbl.center = (
                    self.center_x + cos(self._angle) * self._distance,
                    self.center_y + sin(self._angle) * self._distance
                )

            self.place_label(lbl)
            return True

        if not self._to_layout:
            self.dispatch('on_post_populate')
            return False

    def place_label(self, label):
        self.add_widget(label)
        label.zoom = 0
        Animation(zoom=1, t='out_quad', d=.5).start(label)

    def on_label_options(self, *args):
        for lbl in self.cache.values():
            for key, value in self.label_options.items():
                setattr(lbl, key, value)
        self.layout()

    def on_words(self, *args):
        label_cls = self.label_cls
        if not label_cls:
            return

        if isinstance(label_cls, str):
            label_cls = Factory.get(label_cls)

        for w in self.words:
            if w not in self.cache:
                self.cache[w] = lbl = label_cls(text=w, **self.label_options)

        Clock.schedule_once(self.layout, .1)


if __name__ == '__main__':
    from kivy.base import runTouchApp
    root = Factory.FloatLayout()

    def do_open(*args):
        root.clear_widgets()
        wc = WordCloud(
            angle_increase=pi/100,
            distance_increase=.1,
            label_options=dict(
                font_size=40,
                padding=(1, 1),
            ),
            label_cls='CloudLabel',
            words = (
                'Kivy',
                'Open',
                'source',
                'Python',
                'library',
                'for',
                'rapid',
                'development',
                'of',
                'applications',
                'that',
                'make',
                'use',
                'innovative',
                'user',
                'interfaces',
                'such',
                'as',
                'multi',
                'touch',
                'apps',
            )
        )
        wc.bind(
            on_post_populate=wc.animate_focused_word,
            on_pre_populate=wc.cancel_animate_focused_word,
        )
        root.add_widget(wc)

    root.add_widget(
        Factory.Button(
            text='words',
            size_hint=(None, None),
            pos_hint={'center': (.5, .5)},
            on_press=do_open
        )
    )
    runTouchApp(root)
