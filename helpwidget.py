# Main author:
# Copyright (C) 2012, Gonzalo Odiard <godiard@laptop.org>
# Minor changes and maintaining tasks:
# Copyright (C) 2012, Agustin Zubiaga <aguz@sugarlabs.org>
# Copyright (C) 2012, Daniel Francis <francis@sugarlabs.org>
# Copyright (C) 2012, Manuel Kaufmann <humitos@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

# HelpButton widget

from gettext import gettext as _

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject

from sugar3.graphics.toolbutton import ToolButton
from sugar3.graphics.icon import Icon
from sugar3.graphics import style

"""
class HelpButton(Gtk.ToolItem):

    def __init__(self, **kwargs):
        GObject.GObject.__init__(self)

        help_button = ToolButton('toolbar-help')
        help_button.set_tooltip(_('Help'))
        self.add(help_button)

        self._palette = help_button.get_palette()

        sw = Gtk.ScrolledWindow()
        sw.set_size_request(int(Gdk.Screen.width() / 2.8),
                            Gdk.Screen.height() - style.GRID_CELL_SIZE * 3)
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self._max_text_width = int(Gdk.Screen.width() / 3) - 600
        self._vbox = Gtk.Box()
        self._vbox.set_orientation(Gtk.Orientation.VERTICAL)
        self._vbox.set_homogeneous(False)
        self._vbox.set_border_width(10)

        hbox = Gtk.Box()
        hbox.pack_start(self._vbox, False, True, 0)

        sw.add_with_viewport(hbox)

        self._palette.set_content(sw)
        sw.show_all()

        help_button.connect('clicked', self.__help_button_clicked_cb)

    def __help_button_clicked_cb(self, button):
        self._palette.popup(immediate=True)

    def add_section(self, section_text):
        hbox = Gtk.Box()
        label = Gtk.Label()
        label.set_use_markup(True)
        label.set_markup('<b>%s</b>' % section_text)
        label.set_line_wrap(True)
        hbox.pack_start(label, False, False, 0)
        hbox.show_all()
        self._vbox.pack_start(hbox, False, False, padding=5)

    def add_paragraph(self, text, icon=None):
        hbox = Gtk.Box()
        label = Gtk.Label(label=text)
        label.set_justify(Gtk.Justification.LEFT)
        label.set_line_wrap(True)
        hbox.pack_start(label, False, False, 0)
        if icon is not None:
            _icon = Icon(icon_name=icon)
            hbox.add(_icon)
        hbox.show_all()
        self._vbox.pack_start(hbox, False, False, padding=5)
"""

class HelpWidget(Gtk.EventBox):
    def __init__(self, icon_file_func, *args, **kwargs):
        super(HelpWidget, self).__init__(*args, **kwargs)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(vbox)

        self._stages = [
            _HelpStage1(icon_file_func),
            _HelpStage2(icon_file_func),
            _HelpStage3(icon_file_func),
            _HelpStage4(icon_file_func),
            _HelpStage5(icon_file_func),
        ]
        self._stage_index = 0
        self._notebook = Gtk.Notebook()
        self._notebook.set_show_tabs(False)
        for stage in self._stages:
            self._notebook.append_page(stage, None)
        vbox.pack_start(self._notebook, True, True, 0)

        self._reset_current_stage()

    def can_prev_stage(self):
        """Returns True if the help widget can move to the previous stage."""
        return (self._stage_index != 0)

    def can_next_stage(self):
        """Returns True if the help widget can move to the next stage."""
        return (self._stage_index < len(self._stages) - 1)

    def prev_stage(self):
        """Moves the help widget to the previous stage."""
        self._stage_index = max(0, self._stage_index - 1)
        self._reset_current_stage()

    def next_stage(self):
        """Moves the help widget to the next stage."""
        self._stage_index = min(len(self._stages) - 1, self._stage_index + 1)
        self._reset_current_stage()

    def replay_stage(self):
        """Replays the current stage."""
        self._stages[self._stage_index].reset()

    def _reload_clicked_cb(self, source):
        self._reset_current_stage()

    def _reset_current_stage(self):
        self._notebook.set_current_page(self._stage_index)
        self._stages[self._stage_index].reset()


class _HelpStage(Gtk.EventBox):
    # An abstract parent class for objects that represent an animated help
    # screen widget with a description.
    def __init__(self, icon_file_func, *args, **kwargs):
        super(_HelpStage, self).__init__(*args, **kwargs)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.add(hbox)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        hbox.pack_start(vbox, expand=True, fill=True,
                        padding=_DEFAULT_SPACING)

        self.preview = _PreviewWidget(icon_file_func)
        vbox.pack_start(self.preview, expand=True, fill=False,
                        padding=_DEFAULT_PADDING)

        label = Gtk.Label(label=self.get_message())
        label.set_line_wrap(True)
        vbox.pack_start(label, expand=False, fill=False,
                        padding=_DEFAULT_PADDING)

        self.board = None
        self.undo_stack = []

        self.anim = None
        self._actions = []
        self._action_index = 0

        actions = self._get_actions()
        self._actions = _flatten(actions)

    def get_message(self):
        # Implement to return stage message.
        raise Exception()

    def reset(self):
        # Resets the playback of the animation script.
        self._stop_animation()
        self._action_index = 0
        self.preview.set_cursor_visible(True)
        self.preview.set_click_visible(False)
        self.preview.center_cursor()
        self.next_action()

    def set_board(self, board):
        self.board = board.clone()
        self.preview.board_drawer.set_board(self.board)

    def _stop_animation(self):
        if self.anim:
            self.anim.stop()
            self.anim = None

    def next_action(self):
        # Moves the HelpStage animation script to the next action.
        if self._action_index >= len(self._actions):
            self.preview.set_cursor_visible(False)
            return
        #powerd.fake()
        action = self._actions[self._action_index]
        self._action_index += 1
        action(self)

    def _get_actions(self):
        # Implement to return a list stage actions (optionally containing
        # sublists of actions).
        raise Exception()

class _HelpStage1(_HelpStage):

    def __init__(self, *args, **kwargs):
        pass


class _HelpStage2(_HelpStage):

    def __init__(self, *args, **kwargs):
        pass


class _HelpStage3(_HelpStage):

    def __init__(self, *args, **kwargs):
        pass


class _HelpStage4(_HelpStage):

    def __init__(self, *args, **kwargs):
        pass

class _HelpStage5(_HelpStage):

    def __init__(self, *args, **kwargs):
        pass

