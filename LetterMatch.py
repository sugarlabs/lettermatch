# Copyright (c) 2012, 2013 Walter Bender
# Copyright (c) 2013 Aneesh Dogra <lionaneesh@gmail.com>

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
from sugar.graphics.toolbarbox import ToolbarBox, ToolbarButton
from sugar.activity.widgets import ActivityToolbarButton
from sugar.activity.widgets import StopButton
from sugar.graphics.toolbutton import ToolButton
from sugar.graphics.combobox import ComboBox
from sugar.graphics.toolcombobox import ToolComboBox
from sugar.datastore import datastore
from sugar import profile
from sugar.graphics.objectchooser import ObjectChooser
from sugar import mime
from utils.sprites import Sprites, Sprite

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

    Level1: A letter card and six picture cards appear; the user
    listens to the name of letter and then selects the matching picture.

    Level2: A picture card and six letter cards appear; the user
    listens to the name of the picture and then selects the matching letter.

    Customization toolbar allows loading of new images and sounds.
    '''

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
            self.data_from_journal = json.loads(
                str(self.metadata['data_from_journal']))
        self._setup_toolbars()

        self.canvas = gtk.DrawingArea()
        self.canvas.set_size_request(gtk.gdk.screen_width(),
                                     gtk.gdk.screen_height())
        self.canvas.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("#000000"))
        self.canvas.show()
        self.set_canvas(self.canvas)

        self.mode = 'letter'

        self._page = Page(self.canvas, self._lessons_path,
                          self._images_path, self._sounds_path,
                          parent=self)

    def _setup_toolbars(self):
        ''' Just 0.86+ toolbars '''
        self.max_participants = 1  # no sharing

        toolbox = ToolbarBox()

        activity_button = ActivityToolbarButton(self)
        toolbox.toolbar.insert(activity_button, 0)
        activity_button.show()

        self.set_toolbar_box(toolbox)
        toolbox.show()
        primary_toolbar = toolbox.toolbar
        custom_toolbar = ToolbarBox()

        self.custom_toolbar_button = ToolbarButton(
            icon_name='view-source', page=custom_toolbar)
        self.custom_toolbar_button.connect(
            'clicked', self._customization_toolbar_cb)
        toolbox.toolbar.insert(self.custom_toolbar_button, -1)

        button = radio_factory('letter', primary_toolbar, self._letter_cb,
                               tooltip=_('listen to the letter names'))
        radio_factory('picture', primary_toolbar, self._picture_cb,
                      tooltip=_('listen to the letter names'),
                      group=button)

        self.status = label_factory(primary_toolbar, '', width=300)

        self.letter_entry = None

        self.image_button = button_factory('load_image_from_journal',
                                           custom_toolbar.toolbar,
                                           self._choose_image_from_journal_cb,
                                           tooltip=_("Import Image"))

        self.sound_button = button_factory('load_audio_from_journal',
                                           custom_toolbar.toolbar,
                                           self._choose_audio_from_journal_cb,
                                           tooltip=_("Import Audio"))

        container = gtk.ToolItem()
        self.letter_entry = gtk.Entry()
        self.letter_entry.set_max_length(1)
        self.letter_entry.set_width_chars(3)  # because 1 char looks funny
        self.letter_entry.connect('changed', self._set_letter)
        self.letter_entry.set_sensitive(False)
        self.letter_entry.show()
        container.add(self.letter_entry)
        container.show_all()
        custom_toolbar.toolbar.insert(container, -1)

        self.add_button = button_factory('list-add', custom_toolbar.toolbar,
                                         self._copy_to_journal,
                                         tooltip=_("Add"))
        self.add_button.set_sensitive(False)

        separator_factory(primary_toolbar, True, False)

        stop_button = StopButton(self)
        stop_button.props.accelerator = '<Ctrl>q'
        toolbox.toolbar.insert(stop_button, -1)
        stop_button.show()

    def _set_letter(self, event):
        ''' Process letter in text entry '''
        text = self.letter_entry.get_text().strip()
        if text and len(text) > 0:
            if len(text) != 1:
                text = text[0].upper()
            text = text.upper()
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
        ''' Callback from add button on customization toolbar '''
        # Save data to journal and load it into the card database
        self.metadata['data_from_journal'] = json.dumps(self.data_from_journal)
        self._page.load_from_journal(self.data_from_journal)

        # Reinit the preview, et al. after add
        self.preview_image.hide()
        self._init_preview()
        self.image_id = None
        self.object_id = None
        self.letter_entry.set_text('')
        self.letter_entry.set_sensitive(False)
        self.add_button.set_sensitive(False)

    def _init_preview(self):
        ''' Set up customization toolbar, preview image '''
        w = int(self._page._card_width)
        h = int(self._page._card_height)
        x = int(self._page._grid_x_offset + w + 12)
        y = int(self._page._grid_y_offset + 40)

        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(
            os.path.join(self._images_path,'../drawing.png'), w, h)
        self.status.set_text(
            _('Please chose image and audio objects from the Journal.'))
        self._page._hide_cards()

        if not hasattr(self, 'preview_image'):
            self.preview_image = Sprite(self._page._sprites, 0, 0, pixbuf)
        else:
            self.preview_image.set_image(pixbuf)
        self.preview_image.move((x, y))
        self.preview_image.set_layer(100)
        self._page._canvas.disconnect(self._page.button_press_event_id)
        self._page._canvas.disconnect(self._page.button_release_event_id)
        self._page.button_press_event_id = \
            self._page._canvas.connect('button-press-event',
                                       self._preview_press_cb)
        self._page.button_release_event_id = \
            self._page._canvas.connect('button-release-event',
                                       self._dummy_cb)

    def _customization_toolbar_cb(self, event):        
        ''' Override toolbar button behavior '''
        if self.custom_toolbar_button.is_expanded():
            self._init_preview()
        else:
            if self.mode == 'letter':
                self._letter_cb()
            else:
                self._picture_cb()

    def _preview_press_cb(self, win, event):
        ''' Preview image was clicked '''
        self._choose_image_from_journal_cb(None)

    def _dummy_cb(self, win, event):
        '''Does nothing'''
        return True

    def _choose_audio_from_journal_cb(self, event):
        ''' Create a chooser for audio objects '''
        self.add_button.set_sensitive(False)
        self.letter_entry.set_sensitive(False)
        self.image_button.set_sensitive(False)
        self.sound_button.set_sensitive(False)
        self.audio_id = None
        chooser = ObjectChooser(what_filter=mime.GENERIC_TYPE_AUDIO)
        result = chooser.run()
        if result == gtk.RESPONSE_ACCEPT:
            jobject = chooser.get_selected_object()
            self.audio_id = str(jobject._object_id)
        self.image_button.set_sensitive(True)
        self.sound_button.set_sensitive(True)
        if self.image_id and self.audio_id:
            self.letter_entry.set_sensitive(True)
            self._page._canvas.disconnect(self._page.button_press_event_id)
            self._page.button_press_event_id = \
                self._page._canvas.connect('button-press-event',
                                           self._play_audio_cb)

    def _play_audio_cb(self, win, event):
        ''' Preview audio '''
        if self.audio_id:
            play_audio_from_file(datastore.get(self.audio_id).get_file_path())

    def _choose_image_from_journal_cb(self, event):
        ''' Create a chooser for image objects '''
        self.add_button.set_sensitive(False)
        self.letter_entry.set_sensitive(False)
        self.image_button.set_sensitive(False)
        self.sound_button.set_sensitive(False)
        self.image_id = None
        chooser = ObjectChooser(what_filter=mime.GENERIC_TYPE_IMAGE)
        result = chooser.run()
        if result == gtk.RESPONSE_ACCEPT:
            jobject = chooser.get_selected_object()
            self.image_id = str(jobject._object_id)

            x = self._page._grid_x_offset + self._page._card_width + 12
            y = self._page._grid_y_offset + 40
            w = self._page._card_width
            h = self._page._card_height

            pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(
                jobject.get_file_path(), w, h)
            self.preview_image.set_image(pixbuf)
            self.preview_image.move((x, y))
            self.preview_image.set_layer(100)
        self.image_button.set_sensitive(True)
        self.sound_button.set_sensitive(True)
        if self.image_id and self.audio_id:
            self.letter_entry.set_sensitive(True)
            self._page._canvas.disconnect(self._page.button_press_event_id)
            self._page.button_press_event_id = \
                self._page._canvas.connect('button-press-event',
                                           self._play_audio_cb)

    def _cleanup_preview(self):
        ''' No longer previewing, so hide image and clean up callbacks '''
        if hasattr(self, 'preview_image'):
            self.preview_image.hide()
        self._page._canvas.disconnect(self._page.button_press_event_id)
        self._page._canvas.disconnect(self._page.button_release_event_id)
        self._page.button_press_event_id = \
                self._canvas.connect("button-press-event",
                                     self._page._button_press_cb)
        self._page.button_release_event_id = \
            self._canvas.connect("button-release-event",
                                  self._page._button_release_cb)

    def _letter_cb(self, event=None):
        ''' Click on card to hear the letter name '''
        if self.custom_toolbar_button.is_expanded():
            self.custom_toolbar_button.set_expanded(False)
        self._cleanup_preview()
        self.mode = 'letter'
        self.status.set_text(_('Click on the picture that matches the letter.'))
        if hasattr(self, '_page'):
            self._page.new_page()
        return

    def _picture_cb(self, event=None):
        ''' Click on card to hear the letter name '''
        if self.custom_toolbar_button.is_expanded():
            self.custom_toolbar_button.set_expanded(False)
        self._cleanup_preview()
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
