#Copyright (c) 2012 Walter Bender

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.


import gtk

from sugar.activity import activity
try:
    from sugar.graphics.toolbarbox import ToolbarBox, ToolbarButton
    _HAVE_TOOLBOX = True
except ImportError:
    _HAVE_TOOLBOX = False

if _HAVE_TOOLBOX:
    from sugar.activity.widgets import ActivityToolbarButton
    from sugar.activity.widgets import StopButton


from sugar.graphics.toolbutton import ToolButton
from sugar.graphics.combobox import ComboBox
from sugar.graphics.toolcombobox import ToolComboBox
from sugar.datastore import datastore
from sugar import profile
from sugar.graphics.objectchooser import ObjectChooser
from sugar import mime

from gettext import gettext as _
import os.path

from page import Page
from utils.play_audio import play_audio_from_file
from utils.toolbar_utils import separator_factory, label_factory, \
                                radio_factory, button_factory

import json
import logging
_logger = logging.getLogger('lettermatch-activity')

class LetterMatch(activity.Activity):
    ''' Learning the alphabet. 

    Level1: The alphabet appears and the user has the option to click
    on a letter to listen the name of it and the sound of it.

    Level2: The letters appear randomly and the user must place them
    in the correct order.

    Level3: The laptop says a letter and the user must click on the
    correct one. '''

    def __init__(self, handle):
        ''' Initialize the toolbars and the reading board '''
        super(LetterMatch, self).__init__(handle)

        self.datapath = get_path(activity, 'instance')

        self.image_id = None
        self.audio_id = None

        if 'LANG' in os.environ:
            language = os.environ['LANG'][0:2]
        elif 'LANGUAGE' in os.environ:
            language = os.environ['LANGUAGE'][0:2]
        else:
            language = 'es'  # default to Spanish

        # FIXME: find some reasonable default situation
        language = 'es'
        self.letter = None

        if os.path.exists(os.path.join('~', 'Activities',
                                       'IKnowMyABCs.activity')):
            self._lessons_path = os.path.join('~', 'Activities',
                                              'IKnowMyABCs.activity',
                                              'lessons', language)
        else:
            self._lessons_path = os.path.join('.', 'lessons', language)

        self._images_path = self._lessons_path.replace('lessons', 'images')
        self._sounds_path = self._lessons_path.replace('lessons', 'sounds')
        self.data_from_journal = {}
        if 'data_from_journal' in self.metadata:
            self.data_from_journal = json.loads(str(self.metadata['data_from_journal']))
        self._setup_toolbars()

        # Create a canvas
        canvas = gtk.DrawingArea()
        width = gtk.gdk.screen_width()
        height = int(gtk.gdk.screen_height())
        canvas.set_size_request(width, height)
        canvas.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("#000000"))
        canvas.show()
        self.set_canvas(canvas)

        self.mode = 'letter'

        self._page = Page(canvas, self._lessons_path,
                          self._images_path, self._sounds_path,
                          parent=self)

    def _setup_toolbars(self):
        ''' Setup the toolbars.. '''

        # no sharing
        self.max_participants = 1

        if _HAVE_TOOLBOX:
            toolbox = ToolbarBox()

            # Activity toolbar
            activity_button = ActivityToolbarButton(self)

            toolbox.toolbar.insert(activity_button, 0)
            activity_button.show()

            self.set_toolbar_box(toolbox)
            toolbox.show()
            primary_toolbar = toolbox.toolbar
        else:
            # Use pre-0.86 toolbar design
            primary_toolbar = gtk.Toolbar()
            toolbox = activity.ActivityToolbox(self)
            self.set_toolbox(toolbox)
            toolbox.add_toolbar(_('Page'), primary_toolbar)
            toolbox.show()
            toolbox.set_current_toolbar(1)

            # no sharing
            if hasattr(toolbox, 'share'):
                toolbox.share.hide()
            elif hasattr(toolbox, 'props'):
                toolbox.props.visible = False

        button = radio_factory('letter', primary_toolbar, self._letter_cb,
                               tooltip=_('listen to the letter names'))
        radio_factory('picture', primary_toolbar, self._picture_cb,
                      tooltip=_('listen to the letter names'),
                      group=button)

        self.status = label_factory(primary_toolbar, '', width=300)

        self.letter_entry = None

        if _HAVE_TOOLBOX:
            separator_factory(primary_toolbar, False, True)

            journal_toolbar = ToolbarBox()

            button_factory('letter', journal_toolbar.toolbar,
                           self._choose_from_journal_cb,
                           tooltip=_("Import from journal"))

            container = gtk.ToolItem()
            self.letter_entry = gtk.Entry()
            self.letter_entry.connect('changed', self._set_letter)
            self.letter_entry.set_sensitive(False)
            self.letter_entry.show()
            container.add(self.letter_entry)
            container.show_all()
            journal_toolbar.toolbar.insert(container, -1)

            self.add_button = button_factory('image', journal_toolbar.toolbar,
                                             self._copy_to_journal,
                                             tooltip=_("Add"))
            self.add_button.set_sensitive(False)

            # Add journal toolbar
            journal_toolbar_button = ToolbarButton(icon_name='view-source',
                                                   page=journal_toolbar)
            toolbox.toolbar.insert(journal_toolbar_button, -1)

            separator_factory(primary_toolbar, True, False)

            stop_button = StopButton(self)
            stop_button.props.accelerator = '<Ctrl>q'
            toolbox.toolbar.insert(stop_button, -1)
            stop_button.show()

    def _set_letter(self, event):
        text = self.letter_entry.get_text().strip()
        if text and len(text) > 0:
            if len(text) != 1:
                text = text[0]
                self.letter_entry.set_text(text)
            self.letter = text
            if self.letter in self.data_from_journal:
                self.data_from_journal[self.letter].append(
                                            (self.image_id, self.audio_id))
            else:
                self.data_from_journal[self.letter] = \
                                [(self.image_id, self.audio_id)]
            self.add_button.set_sensitive(True)
        else:
            self.letter = None
            self.add_button.set_sensitive(False)

    def _copy_to_journal(self, event):
        self.metadata['data_from_journal'] = json.dumps(self.data_from_journal)

    def _choose_from_journal_cb(self, event):
        self.add_button.set_sensitive(False)
        self.letter_entry.set_sensitive(False)
        self.image_id = None
        self.audio_id = None
        chooser = ObjectChooser(what_filter=mime.GENERIC_TYPE_IMAGE)
        result = chooser.run()
        if result == gtk.RESPONSE_ACCEPT:
            jobject = chooser.get_selected_object()
            self.image_id = str(jobject._object_id)
            chooser = ObjectChooser(what_filter=mime.GENERIC_TYPE_AUDIO)
            result = chooser.run()
            if result == gtk.RESPONSE_ACCEPT:
                jobject = chooser.get_selected_object()
                self.audio_id = str(jobject._object_id)
        if self.image_id and self.audio_id:
            self.letter_entry.set_sensitive(True)

    def _letter_cb(self, event=None):
        ''' click on card to hear the letter name '''
        self.mode = 'letter'
        self.status.set_text(_('Click on the picture that matches the letter.'))
        if hasattr(self, '_page'):
            self._page.new_page()
        return

    def _picture_cb(self, event=None):
        ''' click on card to hear the letter name '''
        self.mode = 'picture'
        self.status.set_text(_('Click on the letter that matches the picture.'))
        if hasattr(self, '_page'):
            self._page.new_page()
        return

    def write_file(self, file_path):
        ''' Write status to the Journal '''
        if not hasattr(self, '_page'):
            return
        self.metadata['page'] = str(self._page.current_card)

def get_path(activity, subpath):
    """ Find a Rainbow-approved place for temporary files. """
    try:
        return(os.path.join(activity.get_activity_root(), subpath))
    except:
        # Early versions of Sugar didn't support get_activity_root()
        return(os.path.join(
                os.environ['HOME'], ".sugar/default", SERVICE, subpath))
