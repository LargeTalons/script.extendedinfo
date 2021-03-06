import xbmc
import xbmcaddon
import xbmcgui
from Utils import *
import DialogVideoInfo
homewindow = xbmcgui.Window(10000)
from TheMovieDB import *

addon = xbmcaddon.Addon()
addon_id = addon.getAddonInfo('id')
addon_name = addon.getAddonInfo('name')
addon_version = addon.getAddonInfo('version')
addon_strings = addon.getLocalizedString
addon_path = addon.getAddonInfo('path').decode("utf-8")


class DialogVideoList(xbmcgui.WindowXMLDialog):
    ACTION_PREVIOUS_MENU = [92, 9]
    ACTION_EXIT_SCRIPT = [13, 10]

    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self)
        xbmc.executebuiltin("ActivateWindow(busydialog)")
        self.listitem_list = kwargs.get('listitems')
        self.color = kwargs.get('color', "FFAAAAAA")
        self.type = kwargs.get('type', "movie")
        self.page = 1
        self.sort = kwargs.get('sort', "release_date")
        self.order = kwargs.get('order', "desc")
        self.filters = kwargs.get('filters', {})
        if self.listitem_list:
            self.listitems = CreateListItems(self.listitem_list)
        else:
            self.listitems, self.totalpages = self.fetch_data()
            self.listitems = CreateListItems(self.listitems)
            # Notify(str(self.totalpages))
        xbmc.executebuiltin("Dialog.Close(busydialog)")

    def onInit(self):
        windowid = xbmcgui.getCurrentWindowDialogId()
        xbmcgui.Window(windowid).setProperty("WindowColor", self.color)
        self.getControl(500).addItems(self.listitems)
        xbmc.sleep(200)
        xbmc.executebuiltin("SetFocus(500)")

    def onAction(self, action):
        if action in self.ACTION_PREVIOUS_MENU:
            self.close()
            PopWindowStack()
        elif action in self.ACTION_EXIT_SCRIPT:
            self.close()
        # if xbmc.getCondVisibility("Container(500).Row(1)"):
        #     self.page += 1
        #     self.update_list(add=True)

    def onClick(self, controlID):
        if controlID in [500]:
            AddToWindowStack(self)
            media_id = self.getControl(controlID).getSelectedItem().getProperty("id")
            self.close()
            dialog = DialogVideoInfo.DialogVideoInfo(u'script-%s-DialogVideoInfo.xml' % addon_name, addon_path, id=media_id)
            dialog.doModal()
        elif controlID == 5001:
            self.get_sort_type()
            self.update_list()
        elif controlID == 5002:
            self.get_genre()
            self.update_list()

    def onFocus(self, controlID):
        pass

    def get_sort_type(self):
        sort_list = {"Popularity": "popularity",
                     "Release Date": "release_date",
                     "Revenue": "revenue",
                     "Release Date": "primary_release_date",
                     "Original Title": "original_title",
                     "Vote average": "vote_average",
                     "Vote Count": "vote_count"}
        listitems = []
        sort_strings = []
        for (key, value) in sort_list.iteritems():
            listitems.append(key)
            sort_strings.append(value)
        index = xbmcgui.Dialog().select("Choose Sort Order", listitems)
        if index > -1:
            self.sort = sort_strings[index]

    def set_filter_url(self):
        self.filter_url = ""
        filter_list = []
        for (key, value) in self.filters.iteritems():
            filter_list.append("%s=%s" % (key, value))
        self.filter_url = "&".join(filter_list)


    def get_genre(self):
        response = GetMovieDBData("genre/movie/list?language=%s&" % (addon.getSetting("LanguageID")), 10)
        id_list = []
        label_list = []
        for item in response["genres"]:
            id_list.append(item["id"])
            label_list.append(item["name"])
        index = xbmcgui.Dialog().select("Choose Genre", label_list)
        if index > -1:
            # return "with_genres=" + str(id_list[index])
            self.filters["with_genres"] = str(id_list[index])

    def update_list(self, add=False):
        if add:
            self.old_items = self.listitems
        else:
            self.old_items = []
        self.listitems, self.totalpages = self.fetch_data()
        self.listitems = self.old_items + CreateListItems(self.listitems)
        self.getControl(500).addItems(self.listitems)
        # for item in (self.page - 1) * 2:
        #     xbmc.executebuiltin("Down")

    def fetch_data(self):
        self.set_filter_url()
        sortby = self.sort + "." + self.order
        response = GetMovieDBData("discover/%s?sort_by=%s&%s&language=%s&page=%i&" % (self.type, sortby, self.filter_url, addon.getSetting("LanguageID"), self.page), 10)
    #    prettyprint(response)
        if self.type == "movie":
            return HandleTMDBMovieResult(response["results"], False, None), response["total_pages"]
        else:
            return HandleTMDBTVShowResult(response["results"], False, None), response["total_pages"]



