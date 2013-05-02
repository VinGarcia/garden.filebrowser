'''
FileBrowser
======

The :class:`FileBrowser` widget is an advanced file browser.

'''

__all__ = ('FileBrowser', )

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.treeview import TreeViewLabel, TreeView
from kivy.uix.filechooser import FileChooserListView
from kivy.properties import (ObjectProperty, StringProperty, OptionProperty,
                             ListProperty, BooleanProperty)
from kivy.lang import Builder
from kivy.utils import platform as core_platform
import string
from os.path import sep, dirname, expanduser, isdir
from os import walk

platform = core_platform()
if platform == 'win':
    from ctypes import windll, create_string_buffer


def get_drives():
    drives = []
    if platform == 'win':
        bitmask = windll.kernel32.GetLogicalDrives()
        GetVolumeInformationA = windll.kernel32.GetVolumeInformationA
        for letter in string.uppercase:
            if bitmask & 1:
                name = create_string_buffer(64)
                # get name of the drive
                drive = letter + ':'
                res = GetVolumeInformationA(drive + sep, name, 64, None,
                                            None, None, None, 0)
                drives.append((drive, name.value))
            bitmask >>= 1
    elif platform == 'linux':
        drives.append((sep, sep))
        drives.append((expanduser('~'), '~/'))
        mnt = sep + 'mnt'
        if isdir(mnt):
            for drive in walk(mnt).next()[1]:
                drives.append((mnt + sep + drive, drive))
        media = sep + 'media'
        if isdir(media):
            for drive in walk(media).next()[1]:
                drives.append((media + sep + drive, drive))
    elif platform == 'macosx' or platform == 'ios':
        drives.append((expanduser('~'), '~/'))
        vol = sep + 'Volume'
        if isdir(vol):
            for drive in walk(vol).next()[1]:
                drives.append((vol + sep + drive, drive))
    return drives

Builder.load_string('''
#:kivy 1.1.0
#:import metrics kivy.metrics

<TreeLabel>:
    on_touch_down:
        self.parent.browser.current_tab.content.path = self.path if\
        self.collide_point(*args[1].pos) and self.path else\
        self.parent.browser.current_tab.content.path
    on_is_open: self.is_open and self.parent.trigger_populate(self)

<FileBrowser>:
    orientation: 'vertical'
    spacing: 5
    padding: [6, 6, 6, 6]
    select_state: select_button.state
    cancel_state: cancel_button.state
    on_favorites: link_tree.reload_favs(self.favorites)
    selection:
        icon_view.selection if tabbed_browser.current_tab.content == icon_view\
        else list_view.selection
    BoxLayout:
        orientation: 'horizontal'
        spacing: 5
        Splitter:
            sizable_from: 'right'
            size_hint: (.2, 1)
            id: splitter
            ScrollView:
                LinkTree:
                    id: link_tree
                    browser: tabbed_browser
                    size_hint: (None, None)
                    height: self.minimum_height
                    width: max(self.minimum_width, splitter.width)
                    on_parent: self.fill_tree()
                    root_options: {'text': 'Locations', 'no_selection':True}
        TabbedPanel:
            id: tabbed_browser
            size_hint: (.8, 1)
            do_default_tab: True
            default_tab_text: "List View"
            default_tab_content: list_view
            TabbedPanelHeader:
                text: 'Icon View'
                content: icon_view
            FileChooserListView:
                id: list_view
            FileChooserIconView:
                id: icon_view
    GridLayout:
        size_hint: (1, None)
        height: file_text.line_height * 4
        cols: 2
        rows: 2
        spacing: [5]
        TextInput:
            id: file_text
            text:
                root.selection and str(root.selection if\
                tabbed_browser.current_tab.content.multiselect else
                root.selection[0]) or ''
            hint_text: 'Filename'
            multiline: False
        Button:
            id: select_button
            size_hint_x: None
            width: metrics.dp(100)
            text: root.select_string
        TextInput:
            id: filt_text
            hint_text: '*.*'
            on_text_validate:
                list_view.filters = [self.text] if self.text else []
                icon_view.filters = [self.text] if self.text else []
            multiline: False
        Button:
            id: cancel_button
            size_hint_x: None
            width: metrics.dp(100)
            text: root.cancel_string

''')


class TreeLabel(TreeViewLabel):
    path = StringProperty('')
    '''Full path to the location this node points to.

    :class:`~kivy.properties.StringProperty`, defaults to ''
    '''


class LinkTree(TreeView):
    # link to the favorites section of link bar
    _favs = ObjectProperty(None)

    def fill_tree(self):
        if platform == 'win':
            user_path = dirname(expanduser('~')) + sep
        else:
            user_path = expanduser('~') + sep
        self._favs = self.add_node(TreeLabel(text='Favorites', is_open=True,
                                             no_selection=True))
        self.reload_favs([])

        libs = self.add_node(TreeLabel(text='Libraries', is_open=True,
                                       no_selection=True))
        if isdir(user_path + 'Documents'):
            self.add_node(TreeLabel(text='Documents', path=user_path +
                                    'Documents'), libs)
        if isdir(user_path + 'Music'):
            self.add_node(TreeLabel(text='Music', path=user_path +
                                    'Music'), libs)
        if isdir(user_path + 'Pictures'):
            self.add_node(TreeLabel(text='Pictures', path=user_path +
                                    'Pictures'), libs)
        if isdir(user_path + 'Videos'):
            self.add_node(TreeLabel(text='Videos', path=user_path +
                                    'Videos'), libs)

        comp = self.add_node(TreeLabel(text='Computer', is_open=True,
                                       no_selection=True))
        for path, name in get_drives():
            if platform == 'win':
                text = ('%s ' % name if name else '') + '(%s)' % path
            else:
                text = name
            self.add_node(TreeLabel(text=text, path=path + sep), comp)

    def reload_favs(self, fav_list):
        if platform == 'win':
            user_path = dirname(expanduser('~')) + sep
        else:
            user_path = expanduser('~') + sep
        favs = self._favs
        for node in self.iterate_all_nodes(favs):
            if node != favs:
                self.remove_node(node)
        if isdir(user_path + 'Desktop'):
            self.add_node(TreeLabel(text='Desktop', path=user_path +
                                    'Desktop'), favs)
        if isdir(user_path + 'Downloads'):
            self.add_node(TreeLabel(text='Downloads', path=user_path +
                                    'Downloads'), favs)
        for path, name in fav_list:
            self.add_node(TreeLabel(text=name, path=path), favs)

    def trigger_populate(self, node):
        if not node.path or node.nodes:
            return
        parent = node.path
        next = walk(parent).next()
        if next:
            for path in next[1]:
                self.add_node(TreeLabel(text=path, path=parent + sep + path),
                              node)


class FileBrowser(BoxLayout):
    '''FileBrowser class, see module documentation for more information.
    '''

    select_state = OptionProperty('normal', options=('normal', 'down'))
    '''State of the 'select' button, must be one of 'normal' or 'down'.
    The state is 'down' only when the button is currently touched/clicked,
    otherwise 'normal'. This button functions as the typical Ok/Select/Save
    button.

    :data:`select_state` is an :class:`~kivy.properties.OptionProperty`.
    '''
    cancel_state = OptionProperty('normal', options=('normal', 'down'))
    '''State of the 'cancel' button, must be one of 'normal' or 'down'.
    The state is 'down' only when the button is currently touched/clicked,
    otherwise 'normal'. This button functions as the typical cancel button.

    :data:`cancel_state` is an :class:`~kivy.properties.OptionProperty`.
    '''

    select_string = StringProperty('Ok')
    '''Label of the 'select' button.

    :data:`select_string` is an :class:`~kivy.properties.StringProperty`,
    defaults to 'Ok'.
    '''

    cancel_string = StringProperty('Cancel')
    '''Label of the 'cancel' button.

    :data:`cancel_string` is an :class:`~kivy.properties.StringProperty`,
    defaults to 'Cancel'.
    '''

    selection = ListProperty([])
    '''A list of the currently selected files.

    :data:`selection` is an :class:`~kivy.properties.ListProperty`,
    defaults to '[]'.
    '''

    favorites = ListProperty([])
    '''A list of the paths added to the favorites link bar. Each element
    is a tuple where the first element is a string containing the full path
    to the location, while the second element is a string with the name of
    path to be displayed.

    :data:`favorites` is an :class:`~kivy.properties.ListProperty`,
    defaults to '[]'.
    '''


if __name__ == '__main__':
    from kivy.app import App

    class TestApp(App):

        def build(self):
            return FileBrowser()

    TestApp().run()
