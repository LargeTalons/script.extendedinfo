import xbmc
import xbmcaddon
import xbmcgui
from Utils import *
from TheMovieDB import *
from YouTube import *
import DialogActorInfo
import DialogVideoList
from ImageTools import *
# import threading
homewindow = xbmcgui.Window(10000)
selectdialog = xbmcgui.Window(12000)
busydialog = xbmcgui.Window(10138)

addon = xbmcaddon.Addon()
addon_id = addon.getAddonInfo('id')
addon_name = addon.getAddonInfo('name')
addon_version = addon.getAddonInfo('version')
addon_strings = addon.getLocalizedString
addon_path = addon.getAddonInfo('path').decode("utf-8")


class DialogVideoInfo(xbmcgui.WindowXMLDialog):
    ACTION_PREVIOUS_MENU = [92, 9]
    ACTION_EXIT_SCRIPT = [13, 10]

    def __init__(self, *args, **kwargs):
        self.movieplayer = VideoPlayer(popstack=True)
        xbmc.executebuiltin("ActivateWindow(busydialog)")
        xbmcgui.WindowXMLDialog.__init__(self)
        self.monitor = SettingsMonitor()
        tmdb_id = kwargs.get('id')
        self.dbid = kwargs.get('dbid')
        imdb_id = kwargs.get('imdbid')
        self.logged_in = checkLogin()
        if tmdb_id:
            self.MovieId = tmdb_id
        elif self.dbid and (int(self.dbid) > -1):
            self.MovieId = GetImdbIDFromDatabase("movie", self.dbid)
            log("IMDBId from local DB:" + str(self.MovieId))
        elif imdb_id:
            self.MovieId = GetMovieDBID(imdb_id)
        elif self.name:
            self.MovieId = search_movie(kwargs.get('name'))
        else:
            self.MovieId = ""
        if self.MovieId:
            self.movie = GetExtendedMovieInfo(self.MovieId, self.dbid)
            if not self.movie["general"]:
                self.close()
            log("Blur image %s with radius %i" % (self.movie["general"]["Thumb"], 25))
            image, imagecolor = Filter_Image(self.movie["general"]["Thumb"], 25)
            self.movie["general"]['ImageFilter'] = image
            self.movie["general"]['ImageColor'] = imagecolor
            self.youtube_vids = GetYoutubeSearchVideosV3(self.movie["general"]["Label"] + " " + self.movie["general"]["Year"] + ", movie", "", "relevance", 15)
            self.set_listitems = []
            self.setinfo = {}
            if self.movie["general"]["SetId"]:
                self.set_listitems, self.setinfo = GetSetMovies(self.movie["general"]["SetId"])
            id_list = []
            for item in self.set_listitems:
                id_list.append(item["ID"])
            self.movie["similar"] = [item for item in self.movie["similar"] if item["ID"] not in id_list]
            id_list = []
            for item in self.movie["videos"]:
                id_list.append(item["key"])
            self.youtube_vids = [item for item in self.youtube_vids if item["youtube_id"] not in id_list]
            self.crew_list = []
            id_list = []
            for item in self.movie["crew"]:
                if item["id"] not in id_list:
                    id_list.append(item["id"])
                    self.crew_list.append(item)
                else:
                    index = id_list.index(item["id"])
                    self.crew_list[index]["job"] = self.crew_list[index]["job"] + " / " + item["job"]
        else:
            Notify("No ID found")
            self.close()
        xbmc.executebuiltin("Dialog.Close(busydialog)")

    def onInit(self):
        homewindow.setProperty("movie.ImageColor", self.movie["general"]["ImageColor"])
        self.windowid = xbmcgui.getCurrentWindowDialogId()
        xbmcgui.Window(self.windowid).setProperty("tmdb_logged_in", self.logged_in)
        passDictToSkin(self.setinfo, "movie.set.", False, False, self.windowid)
        passDictToSkin(self.movie["general"], "movie.", False, False, self.windowid)
        self.getControl(1000).addItems(CreateListItems(self.movie["actors"], 0))
        self.getControl(150).addItems(CreateListItems(self.movie["similar"], 0))
        self.getControl(250).addItems(CreateListItems(self.set_listitems, 0))
        self.getControl(450).addItems(CreateListItems(self.movie["lists"], 0))
        self.getControl(550).addItems(CreateListItems(self.movie["studios"], 0))
        self.getControl(650).addItems(CreateListItems(self.movie["releases"], 0))
        self.getControl(750).addItems(CreateListItems(self.crew_list, 0))
        self.getControl(850).addItems(CreateListItems(self.movie["genres"], 0))
        self.getControl(950).addItems(CreateListItems(self.movie["keywords"], 0))
        self.getControl(1050).addItems(CreateListItems(self.movie["reviews"], 0))
        self.getControl(1150).addItems(CreateListItems(self.movie["videos"], 0))
        self.getControl(1250).addItems(CreateListItems(self.movie["images"], 0))
        self.getControl(1350).addItems(CreateListItems(self.movie["backdrops"], 0))
        self.getControl(350).addItems(CreateListItems(self.youtube_vids, 0))
        self.UpdateStates(False)


    def onAction(self, action):
        if action in self.ACTION_PREVIOUS_MENU:
            self.close()
            PopWindowStack()
        elif action in self.ACTION_EXIT_SCRIPT:
            self.close()

    def UpdateStates(self, forceupdate=True):
        if forceupdate:
            xbmc.sleep(2000)
            self.movie = GetExtendedMovieInfo(self.MovieId, self.dbid, 0)
        if self.movie["account_states"]:
            xbmcgui.Window(self.windowid).setProperty("favorite", str(self.movie["account_states"]["favorite"]))
            if self.movie["account_states"]["rated"]:
                xbmcgui.Window(self.windowid).setProperty("rated", str(self.movie["account_states"]["rated"]["value"]))
            else:
                xbmcgui.Window(self.windowid).setProperty("rated", "")
            xbmcgui.Window(self.windowid).setProperty("watchlist", str(self.movie["account_states"]["watchlist"]))
            # Notify(str(self.movie["account_states"]["rated"]["value"]))

    def onClick(self, controlID):
        # selectdialog.setProperty("WindowColor", xbmc.getInfoLabel("Window(home).Property(movie.ImageColor)"))
        # busydialog.setProperty("WindowColor", xbmc.getInfoLabel("Window(home).Property(movie.ImageColor)"))
        if controlID in [1000, 750]:
            actorid = self.getControl(controlID).getSelectedItem().getProperty("id")
            AddToWindowStack(self)
            dialog = DialogActorInfo.DialogActorInfo(u'script-%s-DialogInfo.xml' % addon_name, addon_path, id=actorid)
            self.close()
            dialog.doModal()
        elif controlID in [150, 250]:
            movieid = self.getControl(controlID).getSelectedItem().getProperty("id")
            self.close()
            AddToWindowStack(self)
            dialog = DialogVideoInfo(u'script-%s-DialogVideoInfo.xml' % addon_name, addon_path, id=movieid)
            dialog.doModal()
        elif controlID in [1250, 1350]:
            image = self.getControl(controlID).getSelectedItem().getProperty("Poster")
            dialog = SlideShow(u'script-%s-SlideShow.xml' % addon_name, addon_path, image=image)
            dialog.doModal()
        elif controlID in [350, 1150]:
            AddToWindowStack(self)
            self.close()
            listitem =xbmcgui.ListItem ('Trailer')
            listitem.setInfo('video', {'Title': 'Trailer', 'Genre': 'Youtube Video'})
            youtube_id = self.getControl(controlID).getSelectedItem().getProperty("youtube_id")
            if youtube_id:
                self.movieplayer.playYoutubeVideo(youtube_id, self.getControl(controlID).getSelectedItem(), True)
                self.movieplayer.WaitForVideoEnd()
            else:
                Notify("No trailer found")
        elif controlID in [8]:
            AddToWindowStack(self)
            self.close()
            listitem = CreateListItems([self.movie["general"]])[0]
            self.movieplayer.play(item=self.movie["general"]['FilenameAndPath'], listitem=listitem)
            self.movieplayer.WaitForVideoEnd()
            Notify("here2")
        elif controlID == 550:
            xbmc.executebuiltin("ActivateWindow(busydialog)")
            xbmc.executebuiltin("Dialog.Close(busydialog)")
            filters = {"with_companies": self.getControl(controlID).getSelectedItem().getProperty("id")}
            self.OpenVideoList(None, filters)
        elif controlID == 1050:
            author = self.getControl(controlID).getSelectedItem().getProperty("author")
            text = "[B]" + author + "[/B][CR]" + cleanText(self.getControl(controlID).getSelectedItem().getProperty("content"))
            w = TextViewer_Dialog('DialogTextViewer.xml', addon_path, header="Review", text=text, color=self.movie["general"]['ImageColor'])
            w.doModal()
        elif controlID == 950:
            xbmc.executebuiltin("ActivateWindow(busydialog)")
            filters = {"with_keywords": self.getControl(controlID).getSelectedItem().getProperty("id")}
            self.OpenVideoList(None, filters)
            xbmc.executebuiltin("Dialog.Close(busydialog)")
        elif controlID == 850:
            xbmc.executebuiltin("ActivateWindow(busydialog)")
            genreid = self.getControl(controlID).getSelectedItem().getProperty("id")
            xbmc.executebuiltin("Dialog.Close(busydialog)")
            filters = {"with_genres": genreid}
            self.OpenVideoList(None, filters)
        elif controlID == 650:
            xbmc.executebuiltin("ActivateWindow(busydialog)")
            country = self.getControl(controlID).getSelectedItem().getProperty("iso_3166_1")
            certification = self.getControl(controlID).getSelectedItem().getProperty("certification")
            list_items = GetMoviesWithCertification(country, certification)
            xbmc.executebuiltin("Dialog.Close(busydialog)")
            self.OpenVideoList(list_items, {})
        elif controlID == 450:
            xbmc.executebuiltin("ActivateWindow(busydialog)")
            list_items = GetMoviesFromList(self.getControl(controlID).getSelectedItem().getProperty("id"))
            xbmc.executebuiltin("Dialog.Close(busydialog)")
            self.OpenVideoList(list_items, {})
        elif controlID == 6001:
            ratings = []
            for i in range(0, 21):
                ratings.append(str(float(i * 0.5)))
            rating = xbmcgui.Dialog().select("Enter Rating", ratings)
            if rating > -1:
                rating = float(rating) * 0.5
                RateMovie(self.MovieId, rating)
                self.UpdateStates()
        elif controlID == 6002:
            listitems = ["Favourites", "Rated Movies"]
            account_lists = GetAccountLists()
            for item in account_lists:
                listitems.append("%s (%i)" % (item["name"], item["item_count"]))
            index = xbmcgui.Dialog().select("Choose List", listitems)
            if index == -1:
                pass
            elif index == 0:
                xbmc.executebuiltin("ActivateWindow(busydialog)")
                list_items = GetFavItems("movies")
                xbmc.executebuiltin("Dialog.Close(busydialog)")
                self.OpenVideoList(list_items, {})
            elif index == 1:
                self.ShowRatedMovies()
            else:
                xbmc.executebuiltin("ActivateWindow(busydialog)")
                list_items = GetMoviesFromList(account_lists[index - 2]["id"])
                xbmc.executebuiltin("Dialog.Close(busydialog)")
                self.OpenVideoList(list_items, {})
        elif controlID == 132:
            w = TextViewer_Dialog('DialogTextViewer.xml', addon_path, header="Plot", text=self.movie["general"]["Plot"], color=self.movie["general"]['ImageColor'])
            w.doModal()
        elif controlID == 6003:
            ChangeFavStatus(self.movie["general"]["ID"], "movie", "true")
            self.UpdateStates()
        elif controlID == 6006:
            self.ShowRatedMovies()
        elif controlID == 6005:
            xbmc.executebuiltin("ActivateWindow(busydialog)")
            listitems = ["New List.."]
            account_lists = GetAccountLists()
            for item in account_lists:
                listitems.append("%s (%i)" % (item["name"], item["item_count"]))
            xbmc.executebuiltin("Dialog.Close(busydialog)")
            index = xbmcgui.Dialog().select("Choose List", listitems)
            if index == 0:
                listname = xbmcgui.Dialog().input("Enter List Name", type=xbmcgui.INPUT_ALPHANUM)
                if listname:
                    list_id = CreateList(listname)
                    xbmc.sleep(1000)
                    AddItemToList(list_id, self.MovieId)
            elif index > 0:
                AddItemToList(account_lists[index - 1]["id"], self.MovieId)
                self.UpdateStates()

    def onFocus(self, controlID):
        pass

    def ShowRatedMovies(self):
        xbmc.executebuiltin("ActivateWindow(busydialog)")
        list_items = GetRatedMovies()
        self.close()
        AddToWindowStack(self)
        dialog = DialogVideoList.DialogVideoList(u'script-%s-VideoList.xml' % addon_name, addon_path, listitems=list_items, color=self.movie["general"]['ImageColor'])
        xbmc.executebuiltin("Dialog.Close(busydialog)")
        dialog.doModal()

    def OpenVideoList(self, listitems, filters):
        AddToWindowStack(self)
        self.close()
        dialog = DialogVideoList.DialogVideoList(u'script-%s-VideoList.xml' % addon_name, addon_path, listitems=listitems, color=self.movie["general"]['ImageColor'], filters=filters)
        dialog.doModal()


class SettingsMonitor(xbmc.Monitor):

    def __init__(self):
        xbmc.Monitor.__init__(self)

    def onSettingsChanged(self):
        xbmc.sleep(300)

