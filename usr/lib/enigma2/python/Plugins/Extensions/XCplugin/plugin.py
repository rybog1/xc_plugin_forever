#!/usr/bin/python
# -*- coding: utf-8 -*-

# 10.02.2020

# for localized messages
from . import _
# from __future__ import print_function
from Components.AVSwitch import AVSwitch
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.ConfigList import ConfigListScreen
from Components.config import config, ConfigSelection, getConfigListEntry, NoSave, ConfigText, ConfigDirectory, ConfigNumber, ConfigSubsection, ConfigYesNo, ConfigPassword, ConfigSelectionNumber, ConfigClock, configfile
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Components.Pixmap import Pixmap
from Components.ProgressBar import ProgressBar
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Components.Task import Task, Job, job_manager as JobManager
from Plugins.Plugin import PluginDescriptor
from Screens.Console import Console
from Screens.InfoBarGenerics import InfoBarSeek, InfoBarAudioSelection, InfoBarSubtitleSupport, InfoBarServiceNotifications, InfoBarMoviePlayerSummarySupport, InfoBarMenu, InfoBarNotifications
from Screens.LocationBox import LocationBox
from Screens.MessageBox import MessageBox
from Screens.MovieSelection import MovieSelection
from Screens.Screen import Screen
from Screens.TaskView import JobView
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.Standby import Standby
from Tools import ASCIItranslit
from Tools.Directories import fileExists
from Tools.Downloader import downloadWithProgress
from enigma import eTimer, eListboxPythonMultiContent, gFont, getDesktop, eEnv, iPlayableService, ePicLoad, gPixmapPtr, eServiceReference, eAVSwitch, RT_HALIGN_LEFT, RT_HALIGN_CENTER, RT_VALIGN_CENTER, loadPNG
from os import listdir, path, access, X_OK, chmod
from os.path import splitext
from twisted.web.client import downloadPage
from xml.etree.cElementTree import fromstring, ElementTree

from sys import version_info

import base64
import glob
import hashlib
import json
import os
import re
import socket
import sys
# import tempfile
import time
import zlib
# from . import imghdr

global isDreamOS, piclogo, pictmp, skin_path, Path_Tmp, Path_Picons, Path_Movies, Path_Movies2, Path_XML, enigma_path, epgimport_path
global isStream, btnsearch, eserv, infoname, tport, nochange, filtertmdb, STREAMS, re_search, pmovies, series, urlinfo, e2m3upy

_session = " "
version = "XC Forever V.1.5"
re_search = False
pmovies = False
series = False
isStream = False
btnsearch = 0

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
HD = getDesktop(0).size()
plugin_path = os.path.dirname(sys.modules[__name__].__file__)
nochange = True
skin_path = plugin_path
iconpic = plugin_path + "/plugin.png"
filterlist = plugin_path + "/cfg/filterlist.txt"
enigma_path = '/etc/enigma2/'
epgimport_path = '/etc/epgimport/'
Path_Tmp = "/tmp"
pictmp = Path_Tmp + "/poster.jpg"
urlinfo = ""
isDreamOS = False
e2m3upy = plugin_path + '/bouquet/'


# PY3 = sys.version_info.major >= 3
PY3 = version_info[0] == 3
if PY3:
    from urllib.request import urlopen, Request
    from urllib.parse import urlparse
    from urllib.parse import quote_plus

else:
    from urllib2 import urlopen, Request
    from urlparse import urlparse
    from urllib import quote_plus


try:
    from Plugins.Extensions.SubsSupport import SubsSupport, SubsSupportStatus
except ImportError:
    class SubsSupport(object):
        def __init__(self, *args, **kwargs):
            pass

    class SubsSupportStatus(object):
        def __init__(self, *args, **kwargs):
            pass

try:
    from enigma import eMediaDatabase
    isDreamOS = True
except ImportError:
    isDreamOS = False


def checkStr(txt):
    if PY3:
        if isinstance(txt, bytes):
            txt = txt.decode('utf-8')
    else:
        if isinstance(txt, unicode):
            txt = txt.encode('utf-8')
    return txt

try:
    from enigma import eDVBDB
except ImportError:
    eDVBDB = None


def MemClean():
    try:
        os.system("sync")
        os.system("echo 1 > /proc/sys/vm/drop_caches")
        os.system("echo 2 > /proc/sys/vm/drop_caches")
        os.system("echo 3 > /proc/sys/vm/drop_caches")
    except:
        pass


def del_jpg():
    for i in glob.glob(os.path.join(Path_Tmp, "*.jpg")):
        try:
            os.chmod(i, 0o777)
            os.remove(i)
        except OSError:
            pass


def isExtEplayer3Available():
    return os.path.isfile(eEnv.resolve("$bindir/exteplayer3"))


def isGstPlayerAvailable():
    return os.path.isfile(eEnv.resolve("$bindir/gst-launch-1.0"))


modechoices = [("1", _("Dvb(1)")), ("4097", _("IPTV(4097)")), ("eServiceUri", _("eServiceUri(8193)"))]

if os.path.exists("/usr/bin/gstplayer"):
    modechoices.append(("5001", _("Gstreamer(5001)")))

if os.path.exists("/usr/bin/exteplayer3"):
    modechoices.append(("5002", _("Exteplayer3(5002)")))

WGET = ''
if os.path.exists("/var/lib/dpkg/status"):
    WGET = '/usr/bin/wget --no-check-certificate'
else:
    WGET = '/usr/bin/wget'

config.plugins.XCplugin = ConfigSubsection()
config.plugins.XCplugin.data = ConfigYesNo(default=False)
config.plugins.XCplugin.hostaddress = ConfigText(default="exampleserver.com")
config.plugins.XCplugin.port = ConfigNumber(default=8080)
config.plugins.XCplugin.user = ConfigText(default="Enter_Username", visible_width=50, fixed_size=False)
config.plugins.XCplugin.passw = ConfigPassword(default="******", fixed_size=False, censor="*")
config.plugins.XCplugin.panel = ConfigSelection(default="player_api", choices=[("player_api", _("player_api")), ("panel_api", _("panel_api"))])
config.plugins.XCplugin.LivePlayer = ConfigYesNo(default=False)
config.plugins.XCplugin.live = ConfigSelection(default='1', choices=modechoices)
config.plugins.XCplugin.services = ConfigSelection(default="4097", choices=modechoices)
config.plugins.XCplugin.typelist = ConfigSelection(default="Multi Live & VOD", choices=["Multi Live & VOD", "Multi Live/Single VOD", "Combined Live/VOD"])
config.plugins.XCplugin.infoname = NoSave(ConfigText(default="myBouquet"))
config.plugins.XCplugin.timeout = ConfigNumber(default=10)
config.plugins.XCplugin.bouquettop = ConfigSelection(default="Bottom", choices=["Bottom", "Top"])
config.plugins.XCplugin.picons = ConfigYesNo(default=False)
config.plugins.XCplugin.pthpicon = ConfigDirectory(default="/media/hdd/picon")
config.plugins.XCplugin.pthmovie = ConfigDirectory(default="/media/hdd/movie")
config.plugins.XCplugin.pthxmlfile = ConfigDirectory(default="/etc/enigma2/xc")
config.plugins.XCplugin.typem3utv = ConfigSelection(default="MPEGTS to TV", choices=["M3U to TV", "MPEGTS to TV"])
config.plugins.XCplugin.strtmain = ConfigYesNo(default=True)
config.plugins.XCplugin.autobouquetupdate = ConfigYesNo(default=False)
config.plugins.XCplugin.updateinterval = ConfigSelectionNumber(default=24, min=1, max=48, stepwidth=1)
config.plugins.XCplugin.last_update = ConfigText(default="none")
config.plugins.XCplugin.timetype = ConfigSelection(default="interval", choices=[("interval", _("interval")), ("fixed time", _("fixed time"))])
config.plugins.XCplugin.fixedtime = ConfigClock(default=0)
# config.plugins.XCplugin.typedown                      = ConfigSelection(default = "jobmanager", choices = ["jobmanager","downloadpage"])


piclogo = plugin_path + "/skin/fhd/iptvlogo.jpg"
if HD.width() <= 1280:
    CHANNEL_NUMBER = [3, 5, 50, 40, 0]
    CHANNEL_NAME = [65, 5, 900, 40, 1]
    FONT_0 = ("Regular", 20)
    FONT_1 = ("Regular", 20)
    BLOCK_H = 40
    piclogo = plugin_path + "/skin/hd/iptvlogo.jpg"
    if isDreamOS:
        skin_path = plugin_path + "/skin/hd/dreamOs"
        iconpic = "plugin.png"
    else:
        skin_path = plugin_path + "/skin/hd"
elif HD.width() <= 1920:
    CHANNEL_NUMBER = [3, 7, 85, 50, 0]
    CHANNEL_NAME = [90, 7, 1500, 50, 1]
    FONT_0 = ("Regular", 32)
    FONT_1 = ("Regular", 32)
    BLOCK_H = 50
    if isDreamOS:
        skin_path = plugin_path + "/skin/fhd/dreamOs"
        iconpic = "plugin.png"
    else:
        skin_path = plugin_path + "/skin/fhd"


def copy_poster():
    os.system("cd / && cp -f " + piclogo + " " + pictmp)


copy_poster()


pmovies = False
ntimeout = config.plugins.XCplugin.timeout.getValue()
eserv = config.plugins.XCplugin.services.value
infoname = str(config.plugins.XCplugin.infoname.value)
Path_Picons = str(config.plugins.XCplugin.pthpicon.value) + "/"
Path_Movies = config.plugins.XCplugin.pthmovie.getValue() + "/"
xc_list = Path_Tmp + "/xc.txt"
iptvsh = enigma_path + "iptv.sh"
Path_Movies2 = Path_Movies
socket.setdefaulttimeout(ntimeout)

if Path_Movies.endswith("//") is True:
    Path_Movies = Path_Movies[:-1]
Path_XML = str(config.plugins.XCplugin.pthxmlfile.value) + "/"
if Path_XML.endswith("//") is True:
    Path_XML = Path_XML[:-1]
if not os.path.exists(Path_XML):
    os.system("mkdir " + Path_XML)


                    
                    
def check_port(tport):
    url = tport
    line = url.strip()
    protocol = 'http://'
    domain = ''
    port = ''
    if str(config.plugins.XCplugin.port.value) != '8080':
        port = str(config.plugins.XCplugin.port.value)
    else:
        port = 8080
    host = ''
    urlsplit1 = line.split("/")
    protocol = urlsplit1[0] + "//"
    if len(urlsplit1) > 2:
        domain = urlsplit1[2].split(':')[0]
        if len(urlsplit1[2].split(':')) > 1:
            port = urlsplit1[2].split(':')[1]
    host = "%s%s:%s" % (protocol, domain, port)

    if not url.startswith(host):
        url = str(url.replace(protocol + domain, host))
        
        '''test ssl'''
        if url.startswith("https") and sslverify:
            parsed_uri = urlparse(url)
            domain = parsed_uri.hostname
            sniFactory = SNIFactory(domain)
            if PY3 == 3:
                url = url.encode()        
        ''' end test ssl '''
    return url


class xc_config(Screen, ConfigListScreen):
    def __init__(self, session):
        self.session = session
        skin = skin_path + "/xc_config.xml"
        with open(skin, 'r') as f:
            self.skin = f.read()
        Screen.__init__(self, session)
        self.setup_title = _("XtreamCode-Config")
        self.onChangedEntry = []
        self.downloading = False
        self["info2"] = Label("")
        self["playlist"] = Label()
        self["playlist"].setText(infoname)
        self["version"] = Label(version)
        self['statusbar'] = Label()
        self["description"] = Label("")
        self.update_status()
        self["key_red"] = Label(_("Back"))
        self["key_green"] = Label(_("Save"))
        self["key_blue"] = Label(_("Import") + _(" txt"))
        self["key_yellow"] = Label(_("Import") + _(" sh"))
        self["actions"] = HelpableActionMap(self, "XCpluginActions", {
            "home": self.extnok,
            "cancel": self.extnok,
            "left": self.keyLeft,
            "right": self.keyRight,
            "help": self.help,
            "yellow": self.iptv_sh,
            "green": self.cfgok,
            "blue": self.ImportInfosServer,
            "showVirtualKeyboard": self.KeyText,
            "ok": self.ok
        }, -1)
        self.list = []
        ConfigListScreen.__init__(self, self.list, session=self.session, on_change=self.changedEntry)
        self.createSetup()
        self.showhide()
        self.onLayoutFinish.append(self.layoutFinished)

    def iptv_sh(self):
        self.session.openWithCallback(self.importIptv_sh, MessageBox, _("Import Server from /ect/enigma2/iptv.sh?"), type=MessageBox.TYPE_YESNO, timeout=10, default=False)

    def importIptv_sh(self, result):
        if result:
            iptvsh = "/etc/enigma2/iptv.sh"
            if fileExists(iptvsh) and os.stat(iptvsh).st_size > 0:
                with open(iptvsh, 'r+') as f:
                    fpage = f.read()
                regexcat = 'USERNAME="(.*?)".*?PASSWORD="(.*?)".*?url="http://(.*?):(.*?)/get.php.*?'
                match = re.compile(regexcat, re.DOTALL).findall(fpage)
                for usernamesh, passwordsh, urlsh, ports in match:
                    urlsh = urlsh.replace('"', '')
                    usernamesh = usernamesh.replace('"', '')
                    passwordsh = passwordsh.replace('"', '')
                    config.plugins.XCplugin.hostaddress.setValue(urlsh)
                    config.plugins.XCplugin.port.setValue(ports)
                    config.plugins.XCplugin.user.setValue(usernamesh)
                    config.plugins.XCplugin.passw.setValue(passwordsh)
                # port = str(config.plugins.XCplugin.port.value)
                # username = str(config.plugins.XCplugin.user.value)
                # password = str(config.plugins.XCplugin.passw.value)
                filesave = "xc_" + str(config.plugins.XCplugin.user.value) + ".xml"
                filesave = filesave.replace(":", "_")
                filesave = filesave.lower()
                with open(Path_XML + filesave, "w") as t:
                    t.write(str('<?xml version="1.0" encoding="UTF-8" ?>\n' + '<items>\n' + '<plugin_version>' + version + '</plugin_version>\n' + '<xtream_e2portal_url><![CDATA[http://' + urlsh + ']]></xtream_e2portal_url>\n' + '<port>' + ports + '</port>\n' + '<username>' + usernamesh + '</username>\n' + '<password>' + passwordsh + '</password>\n' + '</items>'))
                    t.close()
                self.ConfigText()
            else:
                self.mbox = self.session.open(MessageBox, (_("Missing %s !") % iptvsh), MessageBox.TYPE_INFO, timeout=4)

    def ImportInfosServer(self):
        self.session.openWithCallback(self.importIptv_txt, MessageBox, _("Import Server from /tmp/xc.tx?"), type=MessageBox.TYPE_YESNO, timeout=10, default=False)

    def importIptv_txt(self, result):
        if result:
            if os.path.isfile(xc_list) and os.stat(xc_list).st_size > 0:
                with open(xc_list, 'r') as f:
                    chaine = f.readlines()

                url = chaine[0].replace("\n", "").replace("\t", "").replace("\r", "")
                port = chaine[1].replace("\n", "").replace("\t", "").replace("\r", "").replace(":", "_")
                user = chaine[2].replace("\n", "").replace("\t", "").replace("\r", "").replace(":", "_")
                pswrd = chaine[3].replace("\n", "").replace("\t", "").replace("\r", "")
                filesave = "xc_" + user + ".xml"
                filesave = filesave.replace(":", "_")
                filesave = filesave.lower()
                with open(Path_XML + filesave, "w") as t:
                    t.write(str('<?xml version="1.0" encoding="UTF-8" ?>\n' + '<items>\n' + '<plugin_version>' + version + '</plugin_version>\n' + '<xtream_e2portal_url><![CDATA[http://' + url + ']]></xtream_e2portal_url>\n' + '<port>' + str(port) + '</port>\n' + '<username>' + user + '</username>\n' + '<password>' + pswrd + '</password>\n' + '</items>'))
                    t.close()
                self.mbox = self.session.open(MessageBox, _("File saved to %s !" % filesave), MessageBox.TYPE_INFO, timeout=5)
                config.plugins.XCplugin.hostaddress.setValue(url)
                config.plugins.XCplugin.port.setValue(port)
                config.plugins.XCplugin.user.setValue(user)
                config.plugins.XCplugin.passw.setValue(pswrd)
                self.createSetup()
            else:
                self.mbox = self.session.open(MessageBox, _("File not found %s" % xc_list), MessageBox.TYPE_INFO, timeout=5)

    def update_status(self):
        if config.plugins.XCplugin.autobouquetupdate:
            self['statusbar'].setText(_("Last channel update: %s") % config.plugins.XCplugin.last_update.value)

    def layoutFinished(self):
        self.setTitle(self.setup_title)

    def help(self):
        self.session.open(xc_help)

    def createSetup(self):
        self.editListEntry = None
        self.list = []
        indent = "- "
        self.list.append(getConfigListEntry(_("Link in Main Menu  "), config.plugins.XCplugin.strtmain, (_("Display XCplugin in Main Menu"))))
        self.list.append(getConfigListEntry(_("Data Server Configuration:"), config.plugins.XCplugin.data, (_("Your Server Login and data input"))))
        if config.plugins.XCplugin.data.getValue():
            self.list.append(getConfigListEntry(_("Server URL"), config.plugins.XCplugin.hostaddress, (_("Enter Server Url without 'http://' your_domine"))))
            self.list.append(getConfigListEntry(_("Server PORT"), config.plugins.XCplugin.port, (_("Enter Server Port '8080'"))))
            self.list.append(getConfigListEntry(_("Server Username"), config.plugins.XCplugin.user, (_("Enter Username"))))
            self.list.append(getConfigListEntry(_("Server Password"), config.plugins.XCplugin.passw, (_("Enter Password"))))
        self.list.append(getConfigListEntry(_("Old/New panel"), config.plugins.XCplugin.panel, (_("Panel used"))))
        self.list.append(getConfigListEntry(_("Server Timeout"), config.plugins.XCplugin.timeout, (_("Timeout Server (sec)"))))
        self.list.append(getConfigListEntry(_("Name Bouquet Export"), config.plugins.XCplugin.infoname, (_("Configure name of bouqet exported. Default is myBouquet"))))
        self.list.append(getConfigListEntry(_("Bouquet style "), config.plugins.XCplugin.typelist, (_("Configure the type of conversion in the favorite list"))))
        if config.plugins.XCplugin.typelist.value == "Combined Live/VOD":
            self.list.append(getConfigListEntry(_("Conversion type Output "), config.plugins.XCplugin.typem3utv, (_("Configure type of stream to be downloaded by conversion"))))
        self.list.append(getConfigListEntry(_("Place IPTV bouquets at "), config.plugins.XCplugin.bouquettop, (_("Configure to place the bouquets of the converted lists"))))
        self.list.append(getConfigListEntry(_("Automatic bouquet update (schedule):"), config.plugins.XCplugin.autobouquetupdate, (_("Active Automatic Bouquet Update"))))
        if config.plugins.XCplugin.autobouquetupdate.getValue():
            self.list.append(getConfigListEntry(indent + (_("Schedule type:")), config.plugins.XCplugin.timetype, (_("At an interval of hours or at a fixed time"))))
            if config.plugins.XCplugin.timetype.value == "interval":
                self.list.append(getConfigListEntry(2 * indent + (_("Update interval (hours):")), config.plugins.XCplugin.updateinterval, (_("Configure every interval of hours from now"))))
            if config.plugins.XCplugin.timetype.value == "fixed time":
                self.list.append(getConfigListEntry(2 * indent + (_("Time to start update:")), config.plugins.XCplugin.fixedtime, (_("Configure at a fixed time"))))
        self.list.append(getConfigListEntry(_("LivePlayer Active "), config.plugins.XCplugin.LivePlayer, (_("Live Player for Stream .ts: set No for Record Live"))))
        if config.plugins.XCplugin.LivePlayer.value is True:
            self.list.append(getConfigListEntry(_("Live Services Type"), config.plugins.XCplugin.live, (_("Configure service Reference Dvb-Iptv-Gstreamer-Exteplayer3"))))
        self.list.append(getConfigListEntry(_("Vod Services Type"), config.plugins.XCplugin.services, (_("Configure service Reference Dvb-Iptv-Gstreamer-Exteplayer3"))))
        self.list.append(getConfigListEntry(_("Folder user file .xml"), config.plugins.XCplugin.pthxmlfile, (_("Configure folder containing .xml files\nPress 'OK' to change location."))))
        self.list.append(getConfigListEntry(_("Media Folder "), config.plugins.XCplugin.pthmovie, (_("Configure folder containing movie/media files\nPress 'OK' to change location."))))
        self.list.append(getConfigListEntry(_("Picons IPTV "), config.plugins.XCplugin.picons, (_("Download Picons ?"))))
        if config.plugins.XCplugin.picons.value:
            self.list.append(getConfigListEntry(_("Picons IPTV bouquets to "), config.plugins.XCplugin.pthpicon, (_("Configure folder containing picons files\nPress 'OK' to change location."))))
        self["config"].list = self.list
        self["config"].setList(self.list)

    def changedEntry(self):
        for x in self.onChangedEntry:
            x()

    def getCurrentEntry(self):
        return self["config"].getCurrent()[0]

    def showhide(self):
        pass

    def getCurrentValue(self):
        return str(self["config"].getCurrent()[1].getText())

    def createSummary(self):
        from Screens.Setup import SetupSummary
        return SetupSummary

    def keyLeft(self):
        ConfigListScreen.keyLeft(self)
        self.createSetup()
        self.showhide()

    def keyRight(self):
        ConfigListScreen.keyRight(self)
        self.createSetup()
        self.showhide()

    def ok(self):
        ConfigListScreen.keyOK(self)
        sel = self["config"].getCurrent()[1]
        if sel and sel == config.plugins.XCplugin.pthmovie:
            self.setting = "pthmovie"
            self.openDirectoryBrowser(config.plugins.XCplugin.pthmovie.value)
        if sel and sel == config.plugins.XCplugin.pthxmlfile:
            self.setting = "pthxmlfile"
            self.openDirectoryBrowser(config.plugins.XCplugin.pthxmlfile.value)
        if sel and sel == config.plugins.XCplugin.pthpicon:
            self.setting = "pthpicon"
            self.openDirectoryBrowser(config.plugins.XCplugin.pthpicon.value)
        else:
            pass

    def openDirectoryBrowser(self, path):
        try:
            self.session.openWithCallback(
                self.openDirectoryBrowserCB,
                LocationBox,
                windowTitle=_("Choose Directory:"),
                text=_("Choose directory"),
                currDir=str(path),
                bookmarks=config.movielist.videodirs,
                autoAdd=False,
                editDir=True,
                inhibitDirs=["/bin", "/boot", "/dev", "/home", "/lib", "/proc", "/run", "/sbin", "/sys", "/var"],
                minFree=15)
        except Exception as ex:
            print("openDirectoryBrowser get failed: ", str(ex))

    def openDirectoryBrowserCB(self, path):
        if path is not None:
            if self.setting == "pthmovie":
                config.plugins.XCplugin.pthmovie.setValue(path)
            if self.setting == "pthxmlfile":
                config.plugins.XCplugin.pthxmlfile.setValue(path)
            if self.setting == "pthpicon":
                config.plugins.XCplugin.pthpicon.setValue(path)
        configfile.save()
        return

    def cfgok(self):
        if config.plugins.XCplugin.picons.value and config.plugins.XCplugin.pthpicon.value == "/usr/share/enigma2/picon/":
            if not os.path.exists("/usr/share/enigma2/picon"):
                os.system("mkdir /usr/share/enigma2/picon")
        if config.plugins.XCplugin.pthxmlfile.value == "/media/hdd/xc":
            if not os.path.exists("/media/hdd"):
                self.mbox = self.session.open(MessageBox, _("/media/hdd NOT DETECTED!"), MessageBox.TYPE_INFO, timeout=4)
                return
        if config.plugins.XCplugin.pthxmlfile.value == "/media/usb/xc":
            if not os.path.exists("/media/usb"):
                self.mbox = self.session.open(MessageBox, _("/media/usb NOT DETECTED!"), MessageBox.TYPE_INFO, timeout=4)
                return
        self.save()

    def xml_plugin(self):
        filesave = "xc_" + str(config.plugins.XCplugin.user.value) + ".xml"
        filesave = filesave.replace(":", "_")
        filesave = filesave.lower()
        port = str(config.plugins.XCplugin.port.value)
        with open(Path_XML + filesave, "w") as f:
            f.write(str('<?xml version="1.0" encoding="UTF-8" ?>\n' + '<items>\n' + '<plugin_version>' + version + '</plugin_version>\n' + '<xtream_e2portal_url><![CDATA[http://' + str(config.plugins.XCplugin.hostaddress.value) + ']]></xtream_e2portal_url>\n' + '<port>' + port + '</port>\n' + '<username>' + str(config.plugins.XCplugin.user.value) + '</username>\n' + '<password>' + str(config.plugins.XCplugin.passw.value) + '</password>\n' + '</items>'))
            f.close()

    def save(self):
        global nochange
        nochange = True
        if self["config"].isChanged():
            for x in self["config"].list:
                x[1].save()
            config.plugins.XCplugin.panel.save()
            config.plugins.XCplugin.typem3utv.save()
            config.plugins.XCplugin.pthmovie.save()
            configfile.save()
            self.xml_plugin()
            nochange = False
            self.mbox = self.session.open(MessageBox, _("Settings saved successfully !"), MessageBox.TYPE_INFO, timeout=5)
        self.close()

    def KeyText(self):
        sel = self["config"].getCurrent()
        if sel:
            self.session.openWithCallback(self.VirtualKeyBoardCallback, VirtualKeyBoard, title=self["config"].getCurrent()[0], text=self["config"].getCurrent()[1].value)

    def VirtualKeyBoardCallback(self, callback=None):
        if callback is not None and len(callback):
            self["config"].getCurrent()[1].value = callback
            self["config"].invalidate(self["config"].getCurrent())
        return

    def cancelConfirm(self, result):
        if not result:
            return
        for x in self["config"].list:
            x[1].cancel()
        self.close()

    def extnok(self):
        if self["config"].isChanged():
            self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"))
        else:
            self.close()

    def ConfigText(self):
        STREAMS.read_config()
        STREAMS.get_list(STREAMS.xtream_e2portal_url)


class iptv_streamse():

    def __init__(self):
        global MODUL, iptv_list_tmp, tport
        self.iptv_list = []
        self.plugin_version = ""
        self.list_index = 0
        self.iptv_list_tmp = []
        self.list_index_tmp = 0
        self.playlistname_tmp = ""
        self.video_status = False
        self.server_oki = True
        self.playlistname = ""
        self.next_page_url = ""
        self.next_page_text = ""
        self.prev_page_url = ""
        self.prev_page_text = ""
        self.port = str(config.plugins.XCplugin.port.value)
        self.xtream_e2portal_url = "http://" + str(config.plugins.XCplugin.hostaddress.value) + ':' + self.port
        self.username = str(config.plugins.XCplugin.user.value)
        self.password = str(config.plugins.XCplugin.passw.value)
        self.esr_id = 4097
        self.play_vod = False
        self.play_iptv = False
        self.xml_error = ""
        self.ar_id_start = 3
        self.ar_id_end = 3
        self.ar_id_player = 3
        self.iptv_list_history = []
        self.ar_start = True
        self.clear_url = ""
        self.img_loader = False
        self.trial = ""
        self.banned_text = ""
        self.cont_play = False
        self.systems = ""
        self.playhack = ""
        self.url_tmp = ""
        self.next_page_url_tmp = ""
        self.next_page_text_tmp = ""
        self.prev_page_url_tmp = ""
        self.prev_page_text_tmp = ""
        self.disable_audioselector = False

    def MoviesFolde(self):
        return Path_Movies

    def getValue(self, definitions, default):
        # ret = ""
        Len = len(definitions)
        return Len > 0 and definitions[Len - 1].text or default

    def read_config(self):
        try:
            hosts = "http://" + str(config.plugins.XCplugin.hostaddress.value)  # + ':' + str(config.plugins.XCplugin.port.value)  # + "/enigma2.php"  # panel_api.php" #"
            self.port = str(config.plugins.XCplugin.port.value)
            self.xtream_e2portal_url = hosts + ':' + self.port
            username = str(config.plugins.XCplugin.user.value)
            if username and username != "":
                self.username = username
            password = str(config.plugins.XCplugin.passw.value)
            if password and password != "":
                self.password = password
            plugin_version = version
            print('xtream_e2portal_url = ', self.xtream_e2portal_url)
            print('port = ', self.port)
            print('username = ', self.username)
            print('password = ', self.password)
            print('plugin_version = ', plugin_version)
            print("%s" % version)
            print("-----------CONFIG NEW END----------")
        except Exception as ex:
            print("++++++++++ERROR READ CONFIG+++++++++++++ ")
            print(ex)

    def get_list(self, url=None):
        global stream_live, iptv_list_tmp, stream_url, btnsearch, isStream, next_request
        stream_live = False
        stream_url = ""
        self.xml_error = ""
        self.url = check_port(url)
        self.clear_url = self.url
        self.list_index = 0
        iptv_list_tmp = []
        xml = None
        btnsearch = 0
        next_request = 0
        isStream = False
        try:
            print("!!!!!!!!-------------------- URL %s" % self.url)
            if '&type' in self.url:
                next_request = 1
            elif "_get" in self.url:
                next_request = 2
            xml = self._request(self.url)
            if xml:
                self.next_page_url = ""
                self.next_page_text = ""
                self.prev_page_url = ""
                self.prev_page_text = ""
                self.playlistname = 'no_name'
                playlistname_exists = xml.findtext('playlist_name')
                if playlistname_exists:
                    """
                    self.playlistname = xml.findtext('playlist_name').encode('utf-8')
                self.next_page_url = xml.findtext("next_page_url")
                next_page_text_element = xml.findall("next_page_url")
                if next_page_text_element:
                   self.next_page_text = next_page_text_element[0].attrib.get("text").encode("utf-8")
                self.prev_page_url = xml.findtext("prev_page_url")
                prev_page_text_element = xml.findall("prev_page_url")
                if prev_page_text_element:
                        self.prev_page_text = prev_page_text_element[0].attrib.get("text").encode("utf-8")
                        """
                    self.playlistname = checkStr(xml.findtext('playlist_name'))
                self.next_page_url = checkStr(xml.findtext("next_page_url"))
                next_page_text_element = xml.findall("next_page_url")
                if next_page_text_element:
                    self.next_page_text = checkStr(next_page_text_element[0].attrib.get("text"))
                self.prev_page_url = checkStr(xml.findtext("prev_page_url"))
                prev_page_text_element = xml.findall("prev_page_url")
                if prev_page_text_element:
                    self.prev_page_text = checkStr(prev_page_text_element[0].attrib.get("text"))
                chan_counter = 0
                for channel in xml.findall("channel"):
                    chan_counter = chan_counter + 1
                    title64 = ''
                    name = ''
                    description64 = ''
                    description = ''
                    category_id = ''
                    playlist_url = ''
                    desc_image = ''
                    stream_url = ''
                    piconname = ''
                    ts_stream = ''
                    description4playlist_html = ''
                    title64 = channel.findtext('title')
                    name = base64.b64decode(title64).decode('utf-8')
                    description64 = channel.findtext('description')
                    description = base64.b64decode(description64).decode('utf-8')
                    try:
                        name = ''.join(chr(ord(c)) for c in name).decode('utf8')
                    except:
                        pass
                    try:
                        description = ''.join(chr(ord(c)) for c in description).decode('utf8')
                    except:
                        pass
                    # stream_url = channel.findtext('stream_url')
                    # piconname = channel.findtext("logo")
                    # category_id = channel.findtext('category_id')
                    # ts_stream = channel.findtext("ts_stream")
                    # playlist_url = channel.findtext('playlist_url')
                    # desc_image = channel.findtext('desc_image')
                    stream_url = checkStr(channel.findtext('stream_url'))
                    piconname = checkStr(channel.findtext("logo"))
                    category_id = checkStr(channel.findtext('category_id'))
                    ts_stream = checkStr(channel.findtext("ts_stream"))
                    playlist_url = checkStr(channel.findtext('playlist_url'))
                    desc_image = checkStr(channel.findtext('desc_image'))

                    if desc_image and desc_image != "n/A" and desc_image != "":
                        if desc_image.startswith("https"):
                            desc_image = desc_image.replace("https", "http")
                    if PY3 == 3:
                        desc_image = desc_image.encode()
                    epgnowtitle = ''
                    if stream_url:
                        isStream = True
                    if stream_url and "/live/" in stream_url:
                        print("****** is live stream **** ")
                        stream_live = True
                        # time = ''
                        # starttime = ''
                        # endtime = ''
                        # programme = ''
                        epgnowtitle = ''
                        epgnowtime = ''
                        epgnowdescription = ''
                        epgnexttitle = ''
                        epgnexttime = ''
                        epgnextdescription = ''
                        if len(name.split("[")) > 1:
                            name = name.split("[")[0].strip()
                            if description != '':
                                timematch = re.findall(r'\[(\d\d:\d\d)\]', description)
                                titlematch = re.findall(r'\[\d\d:\d\d\](.*)', description)
                                descriptionmatch = re.findall(r'\n(?s)\((.*?)\)', description)
                                if timematch:
                                    if len(timematch) > 0:
                                        epgnowtime = timematch[0].strip()
                                    if len(timematch) > 1:
                                        epgnexttime = timematch[1].strip()
                                if titlematch:
                                    if len(titlematch) > 0:
                                        epgnowtitle = titlematch[0].strip()
                                    if len(titlematch) > 1:
                                        epgnexttitle = titlematch[1].strip()
                                if descriptionmatch:
                                    if len(descriptionmatch) > 0:
                                        epgnowdescription = descriptionmatch[0].strip()
                                    if len(descriptionmatch) > 1:
                                        epgnextdescription = descriptionmatch[1].strip()
                            description = epgnowtime + ' ' + epgnowtitle + '\n' + epgnowdescription
                            description4playlist_html = epgnexttime + ' ' + epgnexttitle + '\n' + epgnextdescription
                    if stream_url and "/movie/" in stream_url:
                        stream_live = False
                        vodTitle = ''
                        vodDescription = ''
                        # vodVideoType = ''
                        vodDuration = ''
                        vodGenre = ''
                        # vodRating = ''
                        # vodCountry = ''
                        # vodReleaseDate = ''
                        # vodDirector = ''
                        # vodCast = ''
                        vodLines = description.splitlines()
                        vodItems = {}
                        for line in vodLines:
                            vodItems[checkStr(line.partition(": ")[0])] = checkStr(line.partition(": ")[-1])
                        if "NAME" in vodItems:
                            vodTitle = vodItems["NAME"]
                        elif "O_NAME" in vodItems:
                            vodTitle = vodItems["O_NAME"]
                        else:
                            vodTitle = str(name)
                        if "DESCRIPTION" in vodItems:
                            vodDescription = vodItems["DESCRIPTION"]
                        elif "PLOT" in vodItems:
                            vodDescription = vodItems["PLOT"]
                        else:
                            vodDescription = 'TRAMA '
                        if "DURATION" in vodItems:
                            vodDuration = vodItems["DURATION"]
                        else:
                            vodDuration = 'DURATION - NO INFO'
                        if "GENRE" in vodItems:
                            vodGenre = vodItems["GENRE"]
                        else:
                            vodGenre = 'GENRE - NO INFO'
                        epgnowtitle = str(vodTitle)
                        description = str(vodTitle) + '\n\n' + str(vodGenre) + '\n\nDuration: ' + str(vodDuration) + '\n\n' + str(vodDescription)

                        # ### ONLY TEST -- NO WORK
                    if stream_url and "/series/" in stream_url:
                        stream_live = False
                        vodTitle = ''
                        vodDescription = ''
                        # vodVideoType = ''
                        vodDuration = ''
                        vodGenre = ''
                        # vodRating = ''
                        # vodCountry = ''
                        # vodReleaseDate = ''
                        # vodDirector = ''
                        # vodCast = ''
                        vodLines = description.splitlines()
                        vodItems = {}
                        for line in vodLines:
                            vodItems[checkStr(line.partition(": ")[0])] = checkStr(line.partition(": ")[-1])
                        if "NAME" in vodItems:
                            vodTitle = vodItems["NAME"]
                        elif "O_NAME" in vodItems:
                            vodTitle = vodItems["O_NAME"]
                        else:
                            vodTitle = str(name)
                        if "DESCRIPTION" in vodItems:
                            vodDescription = vodItems["DESCRIPTION"]
                        elif "PLOT" in vodItems:
                            vodDescription = vodItems["PLOT"]
                        else:
                            vodDescription = 'TRAMA '
                        if "DURATION" in vodItems:
                            vodDuration = vodItems["DURATION"]
                        else:
                            vodDuration = 'DURATION - NO INFO'
                        if "GENRE" in vodItems:
                            vodGenre = vodItems["GENRE"]
                        else:
                            vodGenre = 'GENRE - NO INFO'
                        epgnowtitle = str(vodTitle)
                        description = str(vodTitle) + '\n\n' + str(vodGenre) + '\n\nDuration: ' + str(vodDuration) + '\n\n' + str(vodDescription)

                    chan_tulpe = (
                        chan_counter,
                        str(name),
                        str(description),
                        piconname,
                        stream_url,
                        playlist_url,
                        str(category_id),
                        desc_image,
                        str(description4playlist_html),
                        ts_stream,
                        epgnowtitle)
                    iptv_list_tmp.append(chan_tulpe)
                    btnsearch = next_request
        except Exception as ex:
            print(ex)
            self.xml_error = ex
        if len(iptv_list_tmp):
            self.iptv_list = iptv_list_tmp
            iptv_list_tmp = self.iptv_list
        else:
            print("ERROR IPTV_LIST_LEN = %s" % len(iptv_list_tmp))
        return

    def _request(self, url):
        if "exampleserver.com" not in config.plugins.XCplugin.hostaddress.value:
            global urlinfo, next_request
            # TYPE_PLAYER= '/player_api.php'
            TYPE_PLAYER = '/enigma2.php'
            url = url.strip(" \t\n\r")
            if next_request == 1:
                url = check_port(url)
                if not url.find(":"):
                    self.port = str(config.plugins.XCplugin.port.value)
                    full_url = self.xtream_e2portal_url + ':' + self.port
                    url = url.replace(self.xtream_e2portal_url, full_url)
                url = url
                next_request = 1
            else:
                url = url + TYPE_PLAYER + "?" + "username=" + self.username + "&password=" + self.password
                next_request = 2
            urlinfo = url
            try:
                req = Request(urlinfo, None, headers=headers)
                if self.server_oki is True:
                    xmlstream = checkStr(urlopen(req, timeout=ntimeout).read())
                res = fromstring(xmlstream)
            except Exception as ex:
                print(ex)
                req.close()
                res = None
                self.xml_error = ex
            return res
        else:
            res = None
            return res


class IPTVInfoBarShowHide():
    """ InfoBar show/hide control, accepts toggleShow and hide actions, might start
    fancy animations. """
    STATE_HIDDEN = 0
    STATE_HIDING = 1
    STATE_SHOWING = 2
    STATE_SHOWN = 3

    def __init__(self):
        self["ShowHideActions"] = ActionMap(["InfobarShowHideActions"], {"toggleShow": self.toggleShow, "hide": self.hide}, 0)
        self.__event_tracker = ServiceEventTracker(screen=self, eventmap={iPlayableService.evStart: self.serviceStarted})
        self.__state = self.STATE_SHOWN
        self.__locked = 0
        self.hideTimer = eTimer()
        self.hideTimer.start(5000, True)
        try:
            self.hideTimer_conn = self.hideTimer.timeout.connect(self.doTimerHide)
        except:
            self.hideTimer.callback.append(self.doTimerHide)
        self.onShow.append(self.__onShow)
        self.onHide.append(self.__onHide)

    def serviceStarted(self):
        if self.execing:
            if config.usage.show_infobar_on_zap.value:
                self.doShow()

    def __onShow(self):
        self.__state = self.STATE_SHOWN
        self.startHideTimer()

    def startHideTimer(self):
        if self.__state == self.STATE_SHOWN and not self.__locked:
            idx = config.usage.infobar_timeout.index
            if idx:
                self.hideTimer.start(idx * 1500, True)

    def __onHide(self):
        self.__state = self.STATE_HIDDEN

    def doShow(self):
        self.show()
        self.startHideTimer()

    def doTimerHide(self):
        self.hideTimer.stop()
        if self.__state == self.STATE_SHOWN:
            self.hide()

    def toggleShow(self):
        if self.__state == self.STATE_SHOWN:
            self.hide()
            self.hideTimer.stop()
        elif self.__state == self.STATE_HIDDEN:
            self.show()

    def lockShow(self):
        self.__locked = self.__locked + 1
        if self.execing:
            self.show()
            self.hideTimer.stop()

    def unlockShow(self):
        self.__locked = self.__locked - 1
        if self.execing:
            self.startHideTimer()

    def debug(obj, text=""):
        print(text + " %s\n" % obj)


class xc_Main(Screen):

    def __init__(self, session):
        global STREAMS
        global _session
        _session = session
        self.session = session
        skin = skin_path + "/xc_Main.xml"
        with open(skin, 'r') as f:
            self.skin = f.read()
        Screen.__init__(self, session)
        self.channel_list = STREAMS.iptv_list
        self.index = STREAMS.list_index
        global channel_list2, index2
        channel_list2 = self.channel_list
        index2 = self.index
        self.banned = False
        self.banned_text = ""
        self.search = ''
        # re_search = False
        self.downloading = False
        self.filter_search = []
        self.mlist = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
        self.mlist.l.setFont(0, gFont(FONT_0[0], FONT_0[1]))
        self.mlist.l.setFont(1, gFont(FONT_1[0], FONT_1[1]))
        self.mlist.l.setItemHeight(BLOCK_H)
        self["exp"] = Label("")
        self["max_connect"] = Label("")
        self["active_cons"] = Label("")
        self["server_protocol"] = Label("")
        self["timezone"] = Label("")
        self["info"] = Label()
        self["playlist"] = Label()
        self["description"] = StaticText()
        self["state"] = Label("")
        self["version"] = Label(version)
        self["key_red"] = Label(_("Back"))
        self["key_green"] = Label(_("Record Movie"))
        self["key_yellow"] = Label(_("Record Series"))
        self["key_blue"] = Label(_("Search"))
        self["green"] = Pixmap()
        self["yellow"] = Pixmap()
        self["blue"] = Pixmap()
        self["key_green"].hide()
        self["key_yellow"].hide()
        self["key_blue"].hide()
        self["key_text"] = Label(_("2"))
        self.go()
        self.pin = False
        self.icount = 0
        self.errcount = 0
        self.onShown.append(self.show_all)
        self["poster"] = Pixmap()
        self.picload = ePicLoad()
        self.picfile = ""
        self["Text"] = Label("")
        self.update_desc = True
        self.pass_ok = False
        self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
        self["actions"] = HelpableActionMap(self, "XCpluginActions", {
            "cancel": self.exitY,
            "home": self.exitY,
            "tv": self.update_list,
            "green": self.check_download_vod,
            "yellow": self.check_download_ser,
            "blue": self.search_text,
            "ok": self.ok,
            "info": self.show_more_info,
            "epg": self.show_more_info,
            "0": self.show_more_info,
            "showMediaPlayer": self.showMovies,
            "5": self.showMediaPlayer,
            "2": self.taskManager,
            "pvr": self.taskManager,
            "movielist": self.taskManager,
            "help": self.help,
            "power": self.power}, -1)
        self.temp_index = 0
        self.temp_channel_list = None
        self.temp_playlistname = None
        self.url_tmp = None
        self.video_back = False
        self.passwd_ok = False
        self["Text"].setText(infoname)
        global srefInit
        self.initialservice = self.session.nav.getCurrentlyPlayingServiceReference()
        srefInit = self.initialservice
        self["playlist"].setText(STREAMS.playlistname)
        self.onLayoutFinish.append(self.checkinf)

    def search_text(self):
        # if re_search is True:
        # re_search = False
        # text = ''
        self.session.openWithCallback(self.filterChannels, VirtualKeyBoard, title=_("Filter this category..."), text=self.search)

    def filterChannels(self, result):
        if result:
            self.filter_search = []
            # search = result
            self.search = result  # search
            self.filter_search = [channel for channel in self.channel_list if str(result).lower() in channel[1].lower()]
            if len(self.filter_search):
                # re_search = True
                global iptv_list_tmp
                iptv_list_tmp = self.filter_search
                self.mlist.setList(list(map(channelEntryIPTVplaylist, iptv_list_tmp)))
                self.mlist.onSelectionChanged.append(self.update_description)
                self.index = self.mlist.getSelectionIndex()
                self["feedlist"] = self.mlist
            else:
                self.resetSearch()

    def resetSearch(self):
        global re_search
        re_search = False
        self.filter_search = []

    def checkinf(self):
        try:
            TIME_GMT = '%d-%m-%Y %H:%M:%S'
            host = str(config.plugins.XCplugin.hostaddress.value)
            ports = str(config.plugins.XCplugin.port.value)
            panel = str(config.plugins.XCplugin.panel.value)
            user = str(config.plugins.XCplugin.user.value)
            password = str(config.plugins.XCplugin.passw.value)
            self["exp"].setText("")
            self["max_connect"].setText("")
            self["active_cons"].setText("")
            self["exp"].setText("Server Not Responding")
            url_info = 'http://' + host + ':' + ports + '/' + panel + '.php?username=' + user + '&password=' + password + '&action=user&sub=info'
            data = getJsonURL(url_info)
            # message = ''
            user = ''
            status = ''
            create_date = ''
            exp_date = ''
            auth = 'Not Authorised'
            # is_trial = ''
            active_cons = ''
            max_cons = ''
            # formats = ''
            ui = data.get('user_info')
            ux = data.get('server_info')
            if ui:
                # message = ui.get('message', '~')
                user = ui.get('username', '~')
                status = ui.get('status', '~')
                auth = ui.get('auth', '~')
                create_date = ui.get('created_at', None)
                exp_date = ui.get('exp_date', None)
                # is_trial = ui.get('is_trial', '~')
                active_cons = ui.get('active_cons', '~')
                max_cons = ui.get('max_connections', '~')
                # formats = ui.get('allowed_output_formats', '~')
            else:
                print("No info!")
            if create_date:
                create_date = time.strftime(TIME_GMT, time.gmtime(int(create_date)))
            else:
                create_date = '~'
            if exp_date:
                exp_date = time.strftime(TIME_GMT, time.gmtime(int(exp_date)))
            else:
                exp_date = '~'
            if str(auth) == "1":
                if str(status) == "Active":
                    self["exp"].setText("Active")
                elif str(status) == "Banned":
                    self["exp"].setText("Banned")
                elif str(status) == "Disabled":
                    self["exp"].setText("Disabled")
                elif str(status) == "Expired":
                    self["exp"].setText("Expired")
                if str(status) == "Active":
                    try:
                        self["exp"].setText("Exp date:\n" + str(exp_date))
                    except:
                        self["exp"].setText("Exp date:\n--------")
                self["max_connect"].setText("Max Connect: " + str(max_cons))
                self["active_cons"].setText("User Active: " + str(active_cons))
            if ux:
                server_protocol = ux.get('server_protocol', '~')
                timezone = ux.get('timezone', '~')
                self["server_protocol"].setText("Protocol: " + str(server_protocol))
                self["timezone"].setText("Timezone: " + str(timezone))
            else:
                print("No info!")

        except Exception as ex:
            print(ex)

    def mmark(self):
        global iptv_list_tmp
        self.temp_index = 0
        self.temp_channel_list = None
        self.temp_playlistname = None
        self.url_tmp = None
        self.video_back = False
        self.passwd_ok = False
        self.list_index = 0
        iptv_list_tmp = channel_list2
        STREAMS.iptv_list = channel_list2
        STREAMS.list_index = index2
        self.go()
        self.update_channellist()
        self.decodeImage(piclogo)
        MemClean()
        self["playlist"].setText(infoname)

    def exitY(self):
        global btnsearch
        del_jpg()
        MemClean()
        if next_request == 1 and btnsearch == 1:
            btnsearch = 0
            self["key_blue"].hide()
            self["key_green"].hide()
            self["key_yellow"].hide()
            self.mmark()
        elif stream_url and "/live/" in stream_url and btnsearch == 1:
            btnsearch = 0
            self["key_blue"].hide()
            self["key_green"].hide()
            self["key_yellow"].hide()
            self.mmark()
        elif stream_url and "/movie/" in stream_url and btnsearch == 1:
            btnsearch = 0
            self["key_blue"].hide()
            self["key_green"].hide()
            self["key_yellow"].hide()
            self.mmark()
        else:
            del_jpg()
            MemClean()
            # ReloadBouquet()
            self.close()

    def go(self):
        # self.mlist.setList(map(channelEntryIPTVplaylist, self.channel_list))
        self.mlist.setList(list(map(channelEntryIPTVplaylist, self.channel_list)))
        self.mlist.onSelectionChanged.append(self.update_description)
        self["feedlist"] = self.mlist
        self["feedlist"].moveToIndex(0)

    def showMediaPlayer(self):
        try:
            from Plugins.Extensions.MediaPlayer.plugin import MediaPlayer
            self.session.open(MediaPlayer)
            # no_plugin = False
        except:
            self.session.open(MessageBox, _("The MediaPlayer plugin is not installed!\nPlease install it."), type=MessageBox.TYPE_INFO, timeout=10)

    def showMovies(self):
        try:
            self.session.open(MovieSelection)
        except:
            pass

    def help(self):
        self.session.open(xc_help)

    def update_list(self):
        global STREAMS
        STREAMS = iptv_streamse()
        STREAMS.read_config()
        if "exampleserver.com" not in STREAMS.xtream_e2portal_url:
            STREAMS.get_list(STREAMS.xtream_e2portal_url)
            self.update_channellist()
        self.checkinf()

    def taskManager(self):
        self.session.open(xc_StreamTasks)

    def show_more_info(self):
        show_more_info()

    def show_more_info_Title(self, truc):
        show_more_info_Title(truc)

    def check_download_ser(self):
        global titleserie
        titleserie = str(STREAMS.playlistname)
        if self.temp_index > -1:
            self.index = self.temp_index

        if stream_url and "/live/" in stream_url:
            self.mbox = self.session.open(MessageBox, _("This is Category or Live Player is active!!!"), MessageBox.TYPE_INFO, timeout=5)

        elif stream_url and "/movie/" in stream_url:
            self.mbox = self.session.open(MessageBox, _("But Only Series Episodes Allowed!!!\nThis Stream is Movie"), MessageBox.TYPE_INFO, timeout=5)

        elif series is True and btnsearch == 1:
            streamfile = '/tmp/streamfile.txt'
            if os.path.isfile(streamfile) and os.stat(streamfile).st_size > 0:
                self.session.openWithCallback(self.download_series, MessageBox, _("ATTENTION!!!\nDOWNLOAD ALL EPISODES SERIES\nSURE???\n%s?" % titleserie), type=MessageBox.TYPE_YESNO, timeout=5)  # default=False)
                return
        else:
            self.mbox = self.session.open(MessageBox, _("Only Series Episodes Allowed!!!"), MessageBox.TYPE_INFO, timeout=5)

    def download_series(self, result):
        if result:
            global Path_Movies2
            global series
            global pmovies
            self.icount = 0
            try:
                if series is True:
                    pmovies = True
                    title = titleserie.replace(' ', '').replace('[', '').replace(']', '').lower()
                    filename = re.sub(r'[\<\>\:\"\/\\\|\?\*\[\]]', '', title)
                    filename = re.sub(r' ', '_', filename)
                    filename = re.sub(r'_+', '_', filename)
                    filename = filename.replace("(", "").replace(")", "").replace("#", "").replace("+ ", "_").replace("\'", "_").replace("'", "_")
                    filename = checkStr(filename)
                    Path_Movies2 = Path_Movies + filename + '/'
                    if Path_Movies2.endswith("//") is True:
                        Path_Movies2 = Path_Movies2[:-1]
                    if not os.path.exists(Path_Movies2):
                        os.system("mkdir " + Path_Movies2)
                    self["state"].setText("Download SERIES")
                    streamfile = '/tmp/streamfile.txt'
                    f = open(streamfile, "r")
                    read_data = f.read()
                    f.close()
                    # username = str(config.plugins.XCplugin.user.value)
                    # password = str(config.plugins.XCplugin.passw.value)
                    # regexcat = ".*?,'(.*?)'.*?'(.*?)'.*?\\n"
                    regexcat = ".*?,'(.*?)',.*?','(.*?)'.*?\\n"
                    match = re.compile(regexcat, re.DOTALL).findall(read_data)
                    self.downloading = True
                    ext = '.mp4'
                    for name, url in match:
                        if PY3 == 3:
                            url = url.encode()
                        if url[-3] != '.':
                            url = url + ext
                        path = urlparse(url).path
                        ext = splitext(path)[1]
                        if str(ext) != '.mp4' or str(ext) != '.mkv' or str(ext) != '.avi' or str(ext) != '.flv':
                            ext = '.mp4'
                        name = name + ext
                        name = name.replace('..', '.')
                        print('name ======= ', name)
                        self.icount += 1
                        useragentcmd = "--header='User-Agent: QuickTime/7.6.2 (qtver=7.6.2;os=Windows NT 5.1Service Pack 3)'"
                        # JobManager.AddJob(downloadJob(self, "wget -c '%s' -O '%s%s'" % (url, Path_Movies2, name), Path_Movies2 + name, name, self.downloadStop))
                        JobManager.AddJob(downloadJob(self, "wget %s -c '%s' -O '%s%s'" % (useragentcmd, url, Path_Movies2, name), Path_Movies2 + name, name, self.downloadStop))

                else:
                    pmovies = False
                    self.mbox = self.session.open(MessageBox, _("Only Series Episodes Allowed!!!"), MessageBox.TYPE_INFO, timeout=5)
                MemClean()

            except Exception as ex:
                series = False
                pmovies = False
                self.downloading = False
                print(ex)

    def downloadStop(self):
        if hasattr(self, 'icount'):
            self.icount -= 1

    def createMetaFile2(self, name, url):
        try:
            text_clear = ""
            text_clear = re.sub(r'[\<\>\:\"\/\\\|\?\*\[\]]', '_', name)
            serviceref = eServiceReference(0x1001, 0, Path_Movies2 + text_clear)
            metafile = open("%s%s.meta" % (Path_Movies2, text_clear), "w")
            metafile.write("%s\n%s\n%s\n%i\n" % (serviceref.toString(), url.replace("\n", ""), text_clear.replace("\n", ""), time()))
            metafile.close()
        except Exception as ex:
            print(ex)

    def check_download_vod(self):
        global stream_vod
        if btnsearch == 0 or btnsearch == 2:
            self.mbox = self.session.open(MessageBox, _("This is Category or List Channel?"), MessageBox.TYPE_INFO, timeout=5)
            return
        if self.temp_index > -1:
            self.index = self.temp_index
        self.selected_channel = iptv_list_tmp[self.index]
        selected_channel = iptv_list_tmp[self.index]
        stream_vod = str(selected_channel[4])
        # playlist_url = str(selected_channel[5])
        self.title = str(selected_channel[1])
        if PY3 == 3:
            stream_vod = stream_vod.encode()
        if stream_vod is not None and btnsearch == 1:
            self.vod_url = stream_vod
            if self.vod_url.split(".")[-1].lower() != "ts":
                self.session.openWithCallback(self.download_vod, MessageBox, _("DOWNLOAD VIDEO?\n%s" % self.title), type=MessageBox.TYPE_YESNO, timeout=5)  # default=False)
            else:
                if config.plugins.XCplugin.LivePlayer.value is True:
                    self.mbox = self.session.open(MessageBox, _("Live Player Active in Setting: set No for Record Live"), MessageBox.TYPE_INFO, timeout=5)
                    return
        else:
            self.mbox = self.session.open(MessageBox, _("No Video to Download/Record!!"), MessageBox.TYPE_INFO, timeout=5)

    def download_vod(self, result):
        if result:
            try:
                global selected, ext
                ext = '.mkv'
                # selected = ''
                selected = stream_vod
                filename = str(self.selected_channel[1])
                filename = re.sub(r'[\<\>\:\"\/\\\|\?\*\[\]]', '_', self.title)
                filename = re.sub(r' ', '_', filename)
                filename = re.sub(r'_+', '_', filename)
                filename = filename.replace("(", "_").replace(")", "_").replace("#", "").replace("+ ", "_").replace("\'", "_").replace("'", "_")
                filename = checkStr(filename)
                path = urlparse(selected).path
                ext = splitext(path)[1]

                if PY3 == 3:
                    selected = selected.encode()
                if selected[-3] != '.':
                    selected = selected + ext
                filename = filename + ext
                self["state"].setText("Download VOD")
                os.system('sleep 3')
                self.downloading = True
                # downloadPage(selected, Path_Movies  + filename).addErrback(self.eError)
                from .downloader import imagedownloadScreen
                self.session.open(imagedownloadScreen, filename, Path_Movies + filename, selected)
                # downloadPage(stream_vod, Path_Movies  + filename).addErrback(self.eError)
                self.session.open(MessageBox, _('Downloading \n\n' + self.title + "\n\n" + Path_Movies + '\n' + filename), MessageBox.TYPE_INFO)
            except Exception as e:
                print(("download vod error %s" % e))
                self.downloading = False
            except:
                self.session.open(MessageBox, _('Download Failed\n\n' + title + "\n\n" + str(cfg.downloadlocation.getValue()) + str(fileTitle) + str(extension)), MessageBox.TYPE_WARNING)
                self.downloading = False

    """
    def download_vod(self, result):
        if result:
            try:
                self.icount = 0
                global selected, ext
                ext = '.mkv'
                selected = ''
                selected = stream_vod
                filename = str(self.selected_channel[1])
                filename = re.sub(r'[\<\>\:\"\/\\\|\?\*\[\]]', '_', self.title)
                filename = re.sub(r' ', '_', filename)
                filename = re.sub(r'_+', '_', filename)
                filename = filename.replace("(", "_").replace(")", "_").replace("#", "").replace("+ ", "_").replace("\'", "_").replace("'", "_")
                filename = checkStr(filename)
                path = urlparse(selected).path
                ext = splitext(path)[1]
                filename = filename + ext
                self["state"].setText("Download VOD")
                os.system('sleep 3')
                self.downloading = True
                useragentcmd = "--header='User-Agent: QuickTime/7.6.2 (qtver=7.6.2;os=Windows NT 5.1Service Pack 3)'"
                cmd = WGET + " %s -c '%s' -O '%s%s'" % (useragentcmd, stream_vod, Path_Movies, filename)
                # JobManager.AddJob(downloadJob(self, cmd, Path_Movies + filename, self.title))
                self.icount += 1
                JobManager.AddJob(downloadJob(self, cmd, Path_Movies + filename, self.title, self.downloadStop))
                # MemClean()
                self.LastJobView()
                # self.mbox = self.session.open(MessageBox, _("[DOWNLOAD] " + self.title), MessageBox.TYPE_INFO, timeout=5)
            except Exception as ex:
                self.downloading = False
                print(ex)
                """

    def eError(self, error):
        print("----------- %s" % error)
        pass

    def createMetaFile(self, filename):
        try:
            text_clear = filename
            serviceref = eServiceReference(0x1001, 0, Path_Movies + text_clear)
            metafile = open("%s%s.meta" % (Path_Movies, text_clear), "w")
            metafile.write("%s\n%s\n%s\n%i\n" % (serviceref.toString(), selected.replace("\n", ""), text_clear.replace("\n", ""), time()))
            metafile.close()
        except Exception as ex:
            print(ex)

    def LastJobView(self):
        currentjob = None
        for job in JobManager.getPendingJobs():
            currentjob = job
        if currentjob is not None:
            self.session.open(JobView, currentjob)
        else:
            self.downloading = False

    def button_updater(self):
        self["Text"].setText(infoname)
        self["playlist"].setText(STREAMS.playlistname)
        self["green"].hide()
        self["yellow"].hide()
        self["blue"].hide()
        if isStream and btnsearch == 1:
            self["key_blue"].show()
            self["key_green"].show()
            self["key_yellow"].show()
            self["blue"].show()
            self["green"].show()
            self["yellow"].show()

    def decodeImage(self, desc_image):
        if isDreamOS:
            self['poster'].instance.setPixmap(gPixmapPtr())
        else:
            self['poster'].instance.setPixmap(None)
        self['poster'].hide()
        sc = AVSwitch().getFramebufferScale()
        self.picload = ePicLoad()
        size = self['poster'].instance.size()
        self.picload.setPara((size.width(), size.height(), sc[0], sc[1], False, 1, '#FF000000'))

        if not isDreamOS:
            self.picload.startDecode(desc_image, 0, 0, False)
        else:
            self.picload.startDecode(desc_image, False)

        ptr = self.picload.getData()
        if ptr is not None:
            self["poster"].instance.setPixmap(ptr)
            self["poster"].show()
        else:
            del_jpg()
            self.decodeImage(piclogo)

    def image_downloaded(self, data, desc_image):
        if os.path.exists(desc_image):
            try:
                self.decodeImage(desc_image)
            except Exception as ex:
                print(ex)
                pass
            except:
                pass

    #
    def downloadError(self, desc_image):
        try:
            del_jpg()
            self.decodeImage(piclogo)
        except Exception as ex:
            print(ex)

    def update_description(self):
        global selected_channel
        if not len(iptv_list_tmp):
            return
        if not self.resetSearch():
            self.channel_list = iptv_list_tmp
        self.index = self.mlist.getSelectionIndex()
        desc_image = ''
        if self.update_desc:
            try:
                self["info"].setText("")
                self["description"].setText("")
                self['poster'].instance.setPixmapFromFile(piclogo)
                selected_channel = self.channel_list[self.index]
                if selected_channel[7] != "" and selected_channel[7] != "n/A" and selected_channel[7] is not None:
                    if selected_channel[7].find("http") == -1:
                        self.decodeImage(piclogo)
                    else:
                        if selected_channel[7].startswith('https'):
                            desc_image = selected_channel[7] = selected_channel[7].replace('https', 'http')
                            self.decodeImage(desc_image)
                        else:
                            m = hashlib.md5()
                            m.update(selected_channel[7])
                            cover_md5 = m.hexdigest()
                            desc_image = "%s/%s.jpg" % (Path_Tmp, cover_md5)
                            if os.path.exists(desc_image) is False or STREAMS.img_loader is False:
                                desc_image = "%s/%s.jpg" % (Path_Tmp, cover_md5)
                                if PY3 == 3:
                                    desc_image = desc_image.encode()

                                downloadPage(selected_channel[7], desc_image, timeout=5).addCallback(self.image_downloaded, desc_image).addErrback(self.downloadError)
                            else:
                                self.decodeImage(desc_image)
                if selected_channel[2] is not None:
                    if stream_live is True:
                        description = selected_channel[2]
                        description2 = selected_channel[8]
                        description3 = selected_channel[6]
                        description_2 = description3.split(" #-# ")
                        descall = description + '\n\n' + description2
                        if description_2:
                            self["description"].setText(descall)
                            if len(description_2) > 1:
                                self["info"].setText(description_2[1])
                    else:
                        description = selected_channel[2]
                        self["description"].setText(description)
            except Exception as ex:
                print(ex)

    def update_channellist(self):
        if not len(iptv_list_tmp):
            return
        if STREAMS.xml_error != "":
            print(STREAMS.clear_url)
        self.channel_list = STREAMS.iptv_list
        if re_search:
            self.channel_list = iptv_list_tmp
            # selected_channel = self.channel_list[self.mlist.getSelectionIndex()]
        else:
            self.channel_list = STREAMS.iptv_list
        if 'season' or 'series' in stream_url.lower():
            if '.mkv' or '.mp4' in stream_url and "series_id" in stream_url:
                global series
                series = True
                streamfile = '/tmp/streamfile.txt'
                with open(streamfile, 'w') as f:
                    f.write(str(self.channel_list).replace("\t", "").replace("\r", "").replace('None', '').replace("'',", "").replace(' , ', '').replace("), ", ")\n").replace("''", '').replace(" ", ""))
                    f.close()
        self.update_desc = False
        # self.mlist.setList(map(channelEntryIPTVplaylist, self.channel_list))
        self.mlist.setList(list(map(channelEntryIPTVplaylist, self.channel_list)))
        self.mlist.moveToIndex(0)
        self.update_desc = True
        self.update_description()
        self.button_updater()

    def show_all(self):
        try:
            if self.passwd_ok is False:
                if re_search is True:
                    self.channel_list = iptv_list_tmp
                    self.mlist.onSelectionChanged.append(self.update_description)
                    self["feedlist"] = self.mlist
                    self["feedlist"].moveToIndex(0)
                else:
                    self.channel_list = iptv_list_tmp
                self.mlist.moveToIndex(self.index)
                # self.mlist.setList(map(channelEntryIPTVplaylist, self.channel_list))
                self.mlist.setList(list(map(channelEntryIPTVplaylist, self.channel_list)))
                self.mlist.selectionEnabled(1)
                self.button_updater()
        except Exception as ex:
            print(ex)

    def ok(self):
        MemClean()
        if not len(iptv_list_tmp):
            self.session.open(MessageBox, _("No data or playlist not compatible with XCplugin."), type=MessageBox.TYPE_WARNING, timeout=5)
            return
        if STREAMS.xml_error != "":
            print('STREAMS.clear_url--------------------', STREAMS.clear_url)
        else:
            self.index = self.mlist.getSelectionIndex()
            selected_channel = self.channel_list[self.mlist.getSelectionIndex()]
            STREAMS.list_index = self.mlist.getSelectionIndex()
            title = selected_channel[1]
            if selected_channel[0] != "[H]":
                title = ("[-]   ") + selected_channel[1]
            selected_channel_history = (
                "[H]",
                title,
                selected_channel[2],
                selected_channel[3],
                selected_channel[4],
                selected_channel[5],
                selected_channel[6],
                selected_channel[7],
                selected_channel[8],
                selected_channel[9])
            STREAMS.iptv_list_history.append(selected_channel_history)
            self.temp_index = -1
            if selected_channel[9] is not None:
                self.temp_index = self.index
            self.pin = True
            if config.ParentalControl.configured.value:
                a = '+18', 'adult', 'hot', 'porn', 'sex', 'xxx'
                if any(s in str(selected_channel[1] or selected_channel[4] or selected_channel[5] or selected_channel[6]).lower() for s in a):
                    self.allow2()
                else:
                    self.pin = True
                    self.pinEntered2(True)
            else:
                self.pin = True
                self.pinEntered2(True)

    def allow2(self):
        from Screens.InputBox import PinInput
        self.session.openWithCallback(self.pinEntered2, PinInput, pinList=[config.ParentalControl.setuppin.value], triesEntry=config.ParentalControl.retries.servicepin, title=_("Please enter the parental control pin code"), windowTitle=_("Enter pin code"))

    def pinEntered2(self, result):
        if not result:
            self.pin = False
            self.session.open(MessageBox, _("The pin code you entered is wrong."), type=MessageBox.TYPE_ERROR, timeout=5)
        self.ok_checked()

    def ok_checked(self):
        if self.pin is False:
            return
        global stream_tmp, title, selected_channel
        try:
            if self.temp_index > -1:
                self.index = self.temp_index
            selected_channel = STREAMS.iptv_list[self.index]
            stream_tmp = selected_channel[4]
            playlist_url = selected_channel[5]
            if playlist_url is not None:
                STREAMS.get_list(playlist_url)
                self.update_channellist()
                MemClean()
            elif stream_tmp is not None:
                self.set_tmp_list()
                STREAMS.video_status = True
                STREAMS.play_vod = False
                title = str(selected_channel[2])
                self.Entered()
        except Exception as ex:
            print(ex)

    def Entered(self):
        self.pin = True
        if stream_tmp.find(".ts") > 0:
            STREAMS.video_status = True
            STREAMS.play_vod = False
            print("------------------------ LIVE ------------------")
            if config.plugins.XCplugin.LivePlayer.value is False:
                self.session.openWithCallback(self.check_standby, xc_Player)  # vod
            else:
                self.session.openWithCallback(self.check_standby, nIPTVplayer)  # live
        else:
            STREAMS.video_status = True
            STREAMS.play_vod = True
            print("----------------------- MOVIE ------------------")
            self.session.openWithCallback(self.check_standby, xc_Player)

    def check_standby(self, myparam=None):
        debug(myparam, "check_standby")
        if myparam:
            self.power()

    def power(self):
        self.session.nav.stopService()
        self.session.open(Standby)

    def set_tmp_list(self):
        self.index = self.mlist.getSelectionIndex()
        STREAMS.list_index = self.index
        STREAMS.list_index_tmp = STREAMS.list_index
        if re_search:
            STREAMS.iptv_list_tmp = iptv_list_tmp
        else:
            STREAMS.iptv_list_tmp = STREAMS.iptv_list
        STREAMS.playlistname_tmp = STREAMS.playlistname
        STREAMS.url_tmp = STREAMS.url
        STREAMS.next_page_url_tmp = STREAMS.next_page_url
        STREAMS.next_page_text_tmp = STREAMS.next_page_text
        STREAMS.prev_page_url_tmp = STREAMS.prev_page_url
        STREAMS.prev_page_text_tmp = STREAMS.prev_page_text

    def load_from_tmp(self):
        debug("load_from_tmp")
        STREAMS.iptv_list = STREAMS.iptv_list_tmp
        STREAMS.list_index = STREAMS.list_index_tmp
        STREAMS.playlistname = STREAMS.playlistname_tmp
        STREAMS.url = STREAMS.url_tmp
        STREAMS.next_page_url = STREAMS.next_page_url_tmp
        STREAMS.next_page_text = STREAMS.next_page_text_tmp
        STREAMS.prev_page_url = STREAMS.prev_page_url_tmp
        STREAMS.prev_page_text = STREAMS.prev_page_text_tmp
        self.index = STREAMS.list_index

    def back_to_video(self):
        try:
            if STREAMS.video_status:
                self.video_back = False
                self.load_from_tmp()
                self.channel_list = STREAMS.iptv_list
                self.session.open(xc_Player)
        except Exception as ex:
            print(ex)


class xc_Player(Screen, InfoBarBase, IPTVInfoBarShowHide, InfoBarSeek, InfoBarAudioSelection, InfoBarSubtitleSupport, SubsSupportStatus, SubsSupport):
    STATE_IDLE = 0
    STATE_PLAYING = 1
    STATE_PAUSED = 2
    ENABLE_RESUME_SUPPORT = True
    ALLOW_SUSPEND = True

    def __init__(self, session, recorder_sref=None):
        self.session = session
        global _session
        _session = session
        self.recorder_sref = None
        skin = skin_path + "/xc_Player.xml"
        with open(skin, 'r') as f:
            self.skin = f.read()
        Screen.__init__(self, session)
        InfoBarBase.__init__(self, steal_current_service=True)
        IPTVInfoBarShowHide.__init__(self)
        InfoBarSeek.__init__(self, actionmap="InfobarSeekActions")
        InfoBarAudioSelection.__init__(self)
        InfoBarSubtitleSupport.__init__(self)
        SubsSupport.__init__(self, searchSupport=True, embeddedSupport=True)
        SubsSupportStatus.__init__(self)
        self.service = None
        # service = None
        self["state"] = Label("")
        self["cont_play"] = Label("")
        self["key_record"] = Label("Record")
        self.cont_play = STREAMS.cont_play
        self["poster"] = Pixmap()
        global vod_url, title, descr
        vod_url = None
        if not isDreamOS:
            self.picload = ePicLoad()
        self.picfile = ""
        if recorder_sref:
            self.recorder_sref = recorder_sref
            self.session.nav.playService(recorder_sref)
        else:
            selected_channel = iptv_list_tmp[STREAMS.list_index]
            vod_url = selected_channel[4]
            vod_url = check_port(vod_url)
            title = selected_channel[1]
            descr = selected_channel[2]
            self.cover = selected_channel[3]
        self.__event_tracker = ServiceEventTracker(screen=self, eventmap={iPlayableService.evSeekableStatusChanged: self.__seekableStatusChanged, iPlayableService.evStart: self.__serviceStarted, iPlayableService.evEOF: self.__evEOF})
        self["actions"] = HelpableActionMap(self, "XCpluginActions", {
            "info": self.show_more_info,
            "0": self.show_more_info,
            "back": self.exit,
            "home": self.exit,
            "cancel": self.exit,
            "up": self.prevVideo,
            "down": self.nextVideo,
            "next": self.nextVideo,
            "previous": self.prevVideo,
            "channelUp": self.prevAR,
            "channelDown": self.nextAR,
            "instantRecord": self.record,  # rec
            "tv": self.stopnew,
            "blue": self.timeshift_autoplay,
            "2": self.restartVideo,
            "help": self.help,
            "power": self.power_off}, -1)
        self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
        self.onFirstExecBegin.append(self.play_vod)
        self.onShown.append(self.setCover)
        self.onPlayStateChanged.append(self.__playStateChanged)
        self.state = self.STATE_PLAYING
        self.timeshift_url = None
        self.timeshift_title = None
        self.onShown.append(self.show_info)
        self.error_message = ""

    def setCover(self):
        try:
            global selected_channel
            desc_image = ''
            self.decodeImage(piclogo)
            selected_channel = iptv_list_tmp[STREAMS.list_index]
            if selected_channel[7] != "" and selected_channel[7] != "n/A" and selected_channel[7] is not None:
                if selected_channel[7].find("http") == -1:
                    self.decodeImage(piclogo)
                else:
                    if STREAMS.img_loader is False:
                        m = hashlib.md5()
                        m.update(selected_channel[7])
                        cover_md5 = m.hexdigest()
                        desc_image = "%s/%s.jpg" % (Path_Tmp, cover_md5)
                        if os.path.exists(desc_image) is False or STREAMS.img_loader is False:
                            desc_image = "%s/%s.jpg" % (Path_Tmp, cover_md5)
                            if PY3 == 3:
                                desc_image = desc_image.encode()
                            downloadPage(selected_channel[7], desc_image, timeout=3).addCallback(self.image_downloaded, desc_image).addErrback(self.downloadError)
                        else:
                            self.decodeImage(desc_image)
        except Exception as ex:
            print(ex)
            self.decodeImage(piclogo)
            print("update COVER")

    def decodeImage(self, desc_image):
        if isDreamOS:
            self["poster"].instance.setPixmap(gPixmapPtr())
        else:
            self["poster"].instance.setPixmap(None)
        self["poster"].hide()
        sc = AVSwitch().getFramebufferScale()
        self.picload = ePicLoad()
        size = self["poster"].instance.size()
        self.picload.setPara((size.width(), size.height(), sc[0], sc[1], False, 1, '#FF000000'))
        if not isDreamOS:
            self.picload.startDecode(desc_image, 0, 0, False)
        else:
            self.picload.startDecode(desc_image, False)
        ptr = self.picload.getData()
        if ptr is not None:
            self["poster"].instance.setPixmap(ptr)
            self["poster"].show()
        else:
            self.decodeImage(piclogo)
        return

    def image_downloaded(self, data, desc_image):
        if os.path.exists(desc_image):
            try:
                self.decodeImage(desc_image)
            except Exception as ex:
                print("* error ** %s" % ex)
                pass
            except:
                pass

    def downloadError(self, desc_image):
        try:
            del_jpg()
            self.decodeImage(piclogo)
        except Exception as ex:
            print(ex)

    def showAfterSeek(self):
        if isinstance(self, IPTVInfoBarShowHide):
            self.doShow()

    def timeshift_autoplay(self):
        if self.timeshift_url:
            try:
                eserv = int(config.plugins.XCplugin.services.value)
                self.reference = eServiceReference(eserv, 0, self.timeshift_url)
                self.reference.setName(self.timeshift_title)
                self.session.nav.playService(self.reference)
            except Exception as ex:
                print(ex)
        else:
            if self.cont_play:
                self.cont_play = False
                self["cont_play"].setText("Auto Play OFF")
            else:
                self.cont_play = True
                self["cont_play"].setText("Auto Play ON")
            STREAMS.cont_play = self.cont_play

    def timeshift(self):
        if self.timeshift_url:
            try:
                eserv = int(config.plugins.XCplugin.services.value)
                self.reference = eServiceReference(eserv, 0, self.timeshift_url)
                self.reference.setName(self.timeshift_title)
                self.session.nav.playService(self.reference)
            except Exception as ex:
                print(ex)

    def autoplay(self):
        if self.cont_play:
            self.cont_play = False
            self["cont_play"].setText("Auto Play OFF")
            self.session.open(MessageBox, "Auto Play OFF", type=MessageBox.TYPE_INFO, timeout=3)
        else:
            self.cont_play = True
            self["cont_play"].setText("Auto Play ON")
            self.session.open(MessageBox, "Auto Play ON", type=MessageBox.TYPE_INFO, timeout=3)
        STREAMS.cont_play = self.cont_play

    def show_info(self):
        if STREAMS.play_vod is True:
            self["state"].setText(" PLAY     >")
        self.hideTimer.start(5000, True)
        if self.cont_play:
            self["cont_play"].setText("Auto Play ON")
        else:
            self["cont_play"].setText("Auto Play OFF")

    def help(self):
        self.session.open(xc_help)

    def restartVideo(self):
        try:
            index = STREAMS.list_index
            video_counter = len(iptv_list_tmp)
            if index < video_counter:
                if iptv_list_tmp[index][4] is not None:
                    STREAMS.list_index = index
                    self.player_helper()
        except Exception as ex:
            print(ex)

    def nextVideo(self):
        try:
            index = STREAMS.list_index + 1
            video_counter = len(iptv_list_tmp)
            if index < video_counter:
                if iptv_list_tmp[index][4] is not None:
                    STREAMS.list_index = index
                    self.player_helper()
        except Exception as ex:
            print(ex)

    def prevVideo(self):
        try:
            index = STREAMS.list_index - 1
            if index > -1:
                if iptv_list_tmp[index][4] is not None:
                    STREAMS.list_index = index
                    self.player_helper()
        except Exception as ex:
            print(ex)

    def player_helper(self):
        self.show_info()
        global title, vod_url, descr, selected_channel
        selected_channel = iptv_list_tmp[STREAMS.list_index]
        if selected_channel:
            selected_channel = iptv_list_tmp[STREAMS.list_index]
            vod_url = selected_channel[4]

            vod_url = check_port(vod_url)

            title = selected_channel[1]
            descr = selected_channel[2]
        STREAMS.play_vod = False
        STREAMS.list_index_tmp = STREAMS.list_index
        self.setCover()
        self.play_vod()

    def record(self):
        try:
            if STREAMS.trial != "":
                self.session.open(MessageBox, "Trialversion dont support this function", type=MessageBox.TYPE_INFO, timeout=10)
            else:
                selected_channel = iptv_list_tmp[STREAMS.list_index]
                vod_url = selected_channel[4]
                vod_url = check_port(vod_url)
                title = selected_channel[1]
                # descr = selected_channel[2]
                self.session.open(MessageBox, (_("BLUE = START PLAY RECORDED VIDEO")), type=MessageBox.TYPE_INFO, timeout=5)
                self.session.nav.stopService()
                self["state"].setText("RECORD")
                useragentcmd = "--header='User-Agent: QuickTime/7.6.2 (qtver=7.6.2;os=Windows NT 5.1Service Pack 3)'"
                path = urlparse(vod_url).path
                ext = splitext(path)[1]
                title_translit = cyr2lat(title)
                filename = ASCIItranslit.legacyEncode(title_translit)
                filename = filename.replace("(", "_").replace(")", "_").replace("#", "").replace("+ ", "_").replace("\'", "_").replace("'", "_")
                filename = checkStr(filename)
                filename = filename + "." + ext
                cmd = WGET + " %s -c '%s' -O '%s%s'" % (useragentcmd, vod_url, Path_Movies, filename)
                JobManager.AddJob(downloadJob(self, cmd, Path_Movies + filename, title))
                self.timeshift_url = Path_Movies + filename
                self.timeshift_title = "[REC] " + title
                self.LastJobView()
        except Exception as ex:
            print(ex)

    def createMetaFile(self, filename):
        try:
            text_clear = filename
            serviceref = eServiceReference(0x1001, 0, Path_Movies + text_clear)
            metafile = open("%s%s.meta" % (Path_Movies, text_clear), "w")
            metafile.write("%s\n%s\n%s\n%i\n" % (serviceref.toString(), selected.replace("\n", ""), text_clear.replace("\n", ""), time()))
            metafile.close()
        except Exception as ex:
            print(ex)

    def LastJobView(self):
        currentjob = None
        for job in JobManager.getPendingJobs():
            currentjob = job
        if currentjob is not None:
            self.session.open(JobView, currentjob)

    def __evEOF(self):
        if self.cont_play:
            self.restartVideo()

    def __seekableStatusChanged(self):
        print("seekable status changed!")

    def __serviceStarted(self):
        self["state"].setText(" PLAY     >")
        self["cont_play"].setText("Auto Play OFF")
        self.state = self.STATE_PLAYING

    def doEofInternal(self, playing):
        if not self.execing:
            return
        if not playing:
            return
        print("doEofInternal EXIT OR NEXT")
        self.session.open(MessageBox, "NO VIDEOSTREAM FOUND", type=MessageBox.TYPE_INFO, timeout=3)
        self.close()

    def stopnew(self):
        if STREAMS.playhack == "":
            self.session.nav.stopService()
            STREAMS.play_vod = False
        self.exit()

    def power_off(self):
        self.close(1)

    def exit(self):
        if STREAMS.playhack == "":
            self.session.nav.stopService()
            STREAMS.play_vod = False
            self.session.nav.playService(self.oldService)
        self.close()

    def nextAR(self):
        message = nextAR()
        self.session.open(MessageBox, message, type=MessageBox.TYPE_INFO, timeout=3)

    def prevAR(self):
        message = prevAR()
        self.session.open(MessageBox, message, type=MessageBox.TYPE_INFO, timeout=3)

    def show_more_info(self):
        show_more_info()

    def show_more_info_Title(self, truc):
        show_more_info_Title(truc)

    def __playStateChanged(self, state):
        self.hideTimer.start(5000, True)
        print("self.seekstate[3] " + self.seekstate[3])
        text = " " + self.seekstate[3]
        if self.seekstate[3] == ">":
            text = " PLAY     >"
        if self.seekstate[3] == "||":
            text = "PAUSE   ||"
        if self.seekstate[3] == ">> 2x":
            text = "        x2         >>"
        if self.seekstate[3] == ">> 4x":
            text = "        x4         >>"
        if self.seekstate[3] == ">> 8x":
            text = "        x8         >>"
        self["state"].setText(text)

    def play_vod(self):
        try:
            if vod_url != "" and vod_url is not None:
                print("------------------------ MOVIE ------------------")
                print('--->' + vod_url + '<------')
                self.session.nav.stopService()
                eserv = int(config.plugins.XCplugin.services.value)
                self.reference = eServiceReference(eserv, 0, vod_url)
                print("self.reference: ", self.reference)
                self.reference.setName(title)
                self.session.nav.playService(self.reference)
            else:
                if self.error_message:
                    self.session.open(MessageBox, self.error_message, type=MessageBox.TYPE_INFO, timeout=3)
                else:
                    self.session.open(MessageBox, "NO VIDEOSTREAM FOUND", type=MessageBox.TYPE_INFO, timeout=3)
                self.close()
        except Exception as ex:
            print(ex)


class xc_StreamTasks(Screen):

    def __init__(self, session):
        self.session = session
        skin = skin_path + "/xc_StreamTasks.xml"
        with open(skin, 'r') as f:
            self.skin = f.read()
        Screen.__init__(self, session)
        self["shortcuts"] = ActionMap(["OkCancelActions", "ColorActions"], {
            "ok": self.keyOK,
            "esc": self.keyClose,
            "exit": self.keyClose,
            "green": self.message1,
            "red": self.keyClose,
            "cancel": self.keyClose}, -1)
        self["movielist"] = List([])
        self["key_green"] = Label(_("Remove"))
        self["key_red"] = Label(_("Close"))
        global srefInit
        self.initialservice = self.session.nav.getCurrentlyPlayingServiceReference()
        srefInit = self.initialservice
        self.Timer = eTimer()
        try:
            self.Timer_conn = self.Timer.timeout.connect(self.TimerFire)
        except:
            self.Timer.callback.append(self.TimerFire)
        self.onLayoutFinish.append(self.layoutFinished)
        self.onClose.append(self.__onClose)

    def __onClose(self):
        del self.Timer

    def layoutFinished(self):
        self.Timer.startLongTimer(2)

    def TimerFire(self):
        self.Timer.stop()
        self.rebuildMovieList()

    def rebuildMovieList(self):
        if os.path.exists(Path_Movies):
            self.movielist = []
            self.getTaskList()
            self.getMovieList()
            self["movielist"].setList(self.movielist)
            self["movielist"].updateList(self.movielist)
        else:
            message = "The Movie path not configured or path not exist!!!"
            web_info(message)
            self.close()

    def getTaskList(self):
        for job in JobManager.getPendingJobs():
            self.movielist.append((
                job,
                job.name,
                job.getStatustext(),
                int(100 * job.progress / float(job.end)),
                str(100 * job.progress / float(job.end)) + "%"))
        if len(self.movielist) >= 1:
            self.Timer.startLongTimer(10)

    def getMovieList(self):
        global filelist, filelist2, file1, file2
        file1 = False
        file2 = False
        if os.path.isdir(Path_Movies):
            filelist = listdir(Path_Movies)
        if os.path.isdir(Path_Movies2):
            filelist2 = listdir(Path_Movies2)
        if filelist is not None:
            file1 = True
            filelist.sort()
            for filename in filelist:
                if path.isfile(Path_Movies + filename) and filename.endswith(".meta") is False:
                    if ".m3u" in filename:
                        continue
                    self.movielist.append(("movie", filename, _("Finished"), 100, "100%"))
        if pmovies is True and filelist2 is not None:
            file2 = True
            for filename2 in filelist2:
                if path.isfile(Path_Movies2 + filename2) and filename2.endswith(".meta") is False:
                    if ".m3u" in filename:
                        continue
                    self.movielist.append(("movie", filename2, _("Finished"), 100, "100%"))

    def keyOK(self):
        global file1, file2
        #eserv = int(config.plugins.XCplugin.services.value)
        current = self["movielist"].getCurrent()
        ptch = Path_Movies
        if current:
            if current[0] == "movie":
                if file1 is True:
                    ptch = Path_Movies
                elif file2 is True:
                    ptch = Path_Movies2
                url = ptch + current[1]
                name = current[1]
                print('name -- mov ', name)
                file1 = False
                file2 = False
                self.session.open(M3uPlayMovie, name, url)
            else:
                job = current[0]
                self.session.openWithCallback(self.JobViewCB, JobView, job)

    def JobViewCB(self, why):
        pass

    def keyClose(self):
        if STREAMS.playhack == "":
            self.session.nav.stopService()
            self.session.nav.playService(srefInit)
        self.close()

    def message1(self):
        current = self["movielist"].getCurrent()
        sel = Path_Movies + current[1]
        sel2 = Path_Movies2 + current[1]
        dom = sel
        dom2 = sel2
        if pmovies is True and filelist2 is not None:
            self.session.openWithCallback(self.callMyMsg1, MessageBox, _("Do you want to remove %s ?") % dom2, MessageBox.TYPE_YESNO, timeout=15, default=False)
        else:
            self.session.openWithCallback(self.callMyMsg1, MessageBox, _("Do you want to remove %s ?") % dom, MessageBox.TYPE_YESNO, timeout=15, default=False)

    def callMyMsg1(self, result):
        if result:
            current = self["movielist"].getCurrent()
            sel = str(Path_Movies + current[1])
            sel2 = str(Path_Movies2 + current[1])
            if fileExists(sel):
                cmd = 'rm -f ' + sel
                os.system(cmd)
                self.session.open(MessageBox, sel + " Movie has been successfully deleted\nwait time to refresh the list...", MessageBox.TYPE_INFO, timeout=5)
            elif pmovies is True and fileExists(sel2):
                cmd = 'rm -f ' + sel2
                os.system(cmd)
                self.session.open(MessageBox, sel2 + " Movie has been successfully deleted\nwait time to refresh the list...", MessageBox.TYPE_INFO, timeout=5)
            else:
                self.session.open(MessageBox, "The movie not exist!\nwait time to refresh the list...", MessageBox.TYPE_INFO, timeout=5)
            self.onShown.append(self.rebuildMovieList)


class xc_help(Screen):
    def __init__(self, session):
        self.session = session
        skin = skin_path + "/xc_help.xml"
        with open(skin, 'r') as f:
            self.skin = f.read()
        Screen.__init__(self, session)
        self["version"] = Label(version)
        self["key_red"] = Label(_("Back"))
        self["key_green"] = Label(_("Config"))
        self["key_yellow"] = Label(_("Main"))
        self["key_blue"] = Label(_("Player"))
        self["helpdesc"] = Label()
        self["helpdesc2"] = Label()
        self['actions'] = ActionMap(['SetupActions', 'ColorActions'], {
            "red": self.exit,
            "green": self.green,
            "yellow": self.yellow,
            "blue": self.blue,
            "ok": self.exit,
            "cancel": self.exit}, -1)
        self.onLayoutFinish.append(self.finishLayout)

    def finishLayout(self):
        helpdesc = self.homecontext()
        helpdesc2 = self.homecontext2()
        self["helpdesc"].setText(helpdesc)
        self["helpdesc2"].setText(helpdesc2)

    def homecontext(self):
        conthelp = "%s\n" % version
        conthelp += "original code by Dave Sully, Doug Mackay\n"
        conthelp += "Modded by Lululla\n\n"
        conthelp += "Skin By: Mmark - Info e2skin.blogspot.it\n"
        conthelp += "______________________________________\n\n"
        conthelp += "Please reports bug or info to forums:\n"
        conthelp += "    Corvoboys - linuxsat-support - dream-elite\n\n"
        conthelp += "Special thanks to:\n"
        conthelp += "    MMark, Pcd, KiddaC\n"
        conthelp += "    aime_jeux, Support, Enigma1969, MasterG\n"
        conthelp += "    and all those i forgot to mention.\n\n"
        return conthelp

    def homecontext2(self):
        conthelp = "\n\n\n\nCURRENT CONFIGURATION\n"
        conthelp += "Current Service Type: %s\n" % config.plugins.XCplugin.services.value
        conthelp += "LivePlayer Active %s\n" % config.plugins.XCplugin.LivePlayer.value
        conthelp += "Config Folder file xml %s\n" % config.plugins.XCplugin.pthxmlfile.value
        conthelp += "Config Media Folder %smovie/\n" % config.plugins.XCplugin.pthmovie.value
        conthelp += _("Current configuration for creating the bouquet\n    > %s Conversion %s\n\n") % (config.plugins.XCplugin.typem3utv.getValue(), config.plugins.XCplugin.typelist.getValue())
        return conthelp

    def yellow(self):
        helpdesc = self.yellowcontext()
        self["helpdesc"].setText(helpdesc)

    def yellowcontext(self):
        conthelp = "HOME - MAIN\n"
        conthelp += _("    (TV BUTTON):\n")
        conthelp += _("            Reload Channels from Playlist\n")
        conthelp += _("    (MENU BUTTON):\n")
        conthelp += _("            Config Setup Options\n")
        conthelp += _("    (5 BUTTON):\n")
        conthelp += _("            MediaPlayer\n")
        conthelp += _("    (9/Help BUTTON):\n")
        conthelp += _("            Help\n")
        conthelp += _("    (PVR/FILELIST/2 BUTTON):\n")
        conthelp += _("            Open Movie Folder\n")
        conthelp += _("    (EPG/INFO/0 BUTTON):\n")
        conthelp += _("            Epg guide or imdb/tmdb\n")
        conthelp += _("    (GREEN BUTTON):\n ")
        conthelp += _("            Start Download or Record Selected Channel:\n")
        conthelp += _("            Set 'Live Player Active' in Setting:\n")
        conthelp += _("            Set 'No' for Record Live\n")
        conthelp += _("    (YELLOW BUTTON):\n")
        conthelp += _("            Start Download All Episodes Series\n")
        conthelp += _("    (BLUE BUTTON):\n")
        conthelp += _("            Search !!!\n")
        return conthelp

    def green(self):
        helpdesc = self.greencontext()
        helpdesc2 = self.homecontext2()
        self["helpdesc"].setText(helpdesc)
        self["helpdesc2"].setText(helpdesc2)

    def greencontext(self):
        conthelp = "MENU CONFIG\n\n"
        conthelp += _("    (YELLOW BUTTON):\n")
        conthelp += _("            If you have a file format:\n")
        conthelp += _("            /etc/enigma2/iptv.sh\n")
        conthelp += _("            USERNAME='xxxxxxxxxx'\n")
        conthelp += _("            PASSWORD='yyyyyyyyy'\n")
        conthelp += _("            url='http://server:port/xxyyzz'\n")
        conthelp += _("            Import with Yellow Button this file\n")
        conthelp += "        ___________________________________\n\n"
        conthelp += _("    (BLUE BUTTON):\n")
        conthelp += _("            If you have a file format:\n")
        conthelp += _("            /tmp/xc.txt\n")
        conthelp += _("            host\t(host without http:// )\n")
        conthelp += _("            port\n")
        conthelp += _("            user\n")
        conthelp += _("            password\n")
        conthelp += _("            Import with Blue Button this file")
        return conthelp

    def blue(self):
        helpdesc = self.bluecontext()
        helpdesc2 = self.homecontext2()
        self["helpdesc"].setText(helpdesc)
        self["helpdesc2"].setText(helpdesc2)

    def bluecontext(self):
        conthelp = "PLAYER M3U\n"
        conthelp += _("    (OK BUTTON):\n")
        conthelp += _("            Open file from list\n")
        conthelp += _("    (GREEN BUTTON):\n")
        conthelp += _("            Remove file from list\n")
        conthelp += _("    (YELLOW BUTTON):\n")
        conthelp += _("            Export file m3u to Bouquet .tv\n")
        conthelp += _("    (BLUE BUTTON):\n")
        conthelp += _("            Download file m3u from current server\n\n")
        conthelp += _("OPEN FILE M3U:\n")
        conthelp += _("    When opening an .m3u file instead:\n")
        conthelp += _("   (GREEN BUTTON):\n")
        conthelp += _("           Reload List\n")
        conthelp += _("   (YELLOW BUTTON):\n")
        conthelp += _("           Download VOD selected channel\n")
        conthelp += _("   (BLUE BUTTON):\n")
        conthelp += _("           Search for a title in the list\n")
        return conthelp

    def exit(self):
        self.close()


class xc_Epg(Screen):

    def __init__(self, session, text_clear):
        self.session = session
        skin = skin_path + "/xc_epg.xml"
        with open(skin, 'r') as f:
            self.skin = f.read()
        Screen.__init__(self, session)
        text_clear = text_clear
        self["key_red"] = Label(_("Back"))
        self["text_clear"] = StaticText()
        self["text_clear"].setText(text_clear)
        self['actions'] = ActionMap(['SetupActions', 'ColorActions'], {
            "red": self.exit,
            "cancel": self.exit,
            "ok": self.exit}, -1)

    def exit(self):
        self.close()


class OpenServer(Screen):
    def __init__(self, session):
        self.session = session
        skin = skin_path + "/xc_OpenServer.xml"
        with open(skin, 'r') as f:
            self.skin = f.read()
        Screen.__init__(self, session)
        self.list = []
        self["list"] = xcM3UList([])
        self["version"] = Label(version)
        self["playlist"] = Label("")
        self["key_red"] = Label(_("Back"))
        self["key_green"] = Label(_("Rename"))
        self["key_yellow"] = Label(_("Remove"))
        self["live"] = Label("")
        self["live"].setText("")
        # nochange = True
        self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
        self["actions"] = HelpableActionMap(self, "XCpluginActions", {
            "ok": self.selectlist,
            "yellow": self.message1,
            "home": self.close,
            "cancel": self.close,
            "green": self.rename,
            "help": self.help}, -1)
        self.onLayoutFinish.append(self.openList)

    def openList(self):
        self.names = []
        for root, dirs, files in os.walk(Path_XML):
            files.sort()
            for name in files:
                if ".xml" not in name:
                    continue
                    pass
                name = name.replace('.xml', '')
                self.names.append(name)
        pass
        m3ulistxc(self.names, self["list"])
        self["live"].setText(str(len(self.names)) + " Team")
        self["playlist"].setText(infoname)

    def Start_iptv_player(self):
        global STREAMS
        STREAMS = iptv_streamse()
        STREAMS.read_config()
        if "exampleserver.com" not in STREAMS.xtream_e2portal_url:
            STREAMS.get_list(STREAMS.xtream_e2portal_url)
            self.session.openWithCallback(check_configuring, xc_Main)
        else:
            self.session.openWithCallback(check_configuring, xc_Main)

    def selectlist(self):
        idx = self["list"].getSelectionIndex()
        if idx == -1 or None:
            return
        else:
            try:
                idx = self["list"].getSelectionIndex()
                dom = Path_XML + self.names[idx]
                dom = dom + '.xml'
                tree = ElementTree()
                xml = tree.parse(dom)
                host = xml.findtext("xtream_e2portal_url")
                self.host = host
                port = xml.findtext("port")
                self.port = port
                self.username = ''
                self.password = ''
                host = self.host.replace("http://", "")
                username = xml.findtext("username")
                if username and username != "":
                    self.username = username
                password = xml.findtext("password")
                if password and password != "":
                    self.password = password
                config.plugins.XCplugin.hostaddress.setValue(host)
                config.plugins.XCplugin.port.setValue(self.port)
                config.plugins.XCplugin.user.setValue(self.username)
                config.plugins.XCplugin.passw.setValue(self.password)
                # nochange = False
                self.Start_iptv_player()
            except IOError as e:
                print(e)

    def message1(self):
        idx = self["list"].getSelectionIndex()
        if idx == -1 or None:
            return
        else:
            idx = self["list"].getSelectionIndex()
            dom = Path_XML + self.names[idx]
            dom = dom + '.xml'
            self.session.openWithCallback(self.removeXml, MessageBox, _("Do you want to remove: %s ?") % dom, MessageBox.TYPE_YESNO, timeout=15, default=False)

    def removeXml(self, result):
        if result:
            idx = self["list"].getSelectionIndex()
            dom = Path_XML + self.names[idx]
            dom = dom + '.xml'
            if fileExists(dom):
                os.remove(dom)
                self.session.open(MessageBox, dom + "   has been successfully deleted\nwait time to refresh the list...", MessageBox.TYPE_INFO, timeout=5)
                del self.names[idx]
            else:
                self.session.open(MessageBox, dom + "   not exist!\nwait time to refresh the list...", MessageBox.TYPE_INFO, timeout=5)
            m3ulistxc(self.names, self["list"])

    def rename(self):
        idx = self["list"].getSelectionIndex()
        if idx == -1 or None:
            return
        else:
            dom = Path_XML + self.names[idx]
            dom = dom + '.xml'
            dim = self.names[idx]
            dim = dim + '.xml'
            if dom is None:
                return
            else:
                global NewName
                NewName = str(dim)
                self.session.openWithCallback(self.newname, VirtualKeyBoard, text=str(dim))
            return

    def newname(self, word):
        if not word:
            pass
        else:
            oldfile = Path_XML + NewName
            newfile = Path_XML + word
            newnameConf = "mv " + "'" + oldfile + "'" + " " + "'" + newfile + "'"
            self.session.open(Console, _("XCplugin Console Rename: %s") % oldfile, ["%s" % newnameConf], closeOnSuccess=True)
            self.onShown.append(self.openList)

    def help(self):
        self.session.open(xc_help)


class nIPTVplayer(Screen, InfoBarBase, IPTVInfoBarShowHide, InfoBarAudioSelection, InfoBarSubtitleSupport, InfoBarServiceNotifications, InfoBarSeek, InfoBarMoviePlayerSummarySupport):

    def __init__(self, session):
        self.session = session
        global _session
        _session = session
        skin = skin_path + "/xc_iptv_player.xml"
        with open(skin, 'r') as f:
            self.skin = f.read()
        Screen.__init__(self, session)
        InfoBarBase.__init__(self, steal_current_service=True)
        IPTVInfoBarShowHide.__init__(self)
        InfoBarMoviePlayerSummarySupport.__init__(self)
        InfoBarServiceNotifications.__init__(self)
        InfoBarSeek.__init__(self)
        InfoBarAudioSelection.__init__(self)
        InfoBarSubtitleSupport.__init__(self)
        self.InfoBar_NabDialog = Label("")
        self.service = None
        # service = None
        self["channel_name"] = Label("")
        self["poster"] = Pixmap()
        if not isDreamOS:
            self.picload = ePicLoad()
        self.picfile = ""
        self["programm"] = Label("")
        self.channel_list = iptv_list_tmp
        self.index = STREAMS.list_index
        STREAMS.play_vod = False
        self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
        self.onFirstExecBegin.append(self.play_channel)
        self["actions"] = HelpableActionMap(self, "XCpluginActions", {
            "info": self.show_more_info,
            "0": self.show_more_info,
            "home": self.exit,
            "cancel": self.exit,
            "help": self.help,
            "up": self.prevChannel,
            "down": self.nextChannel,
            "next": self.nextChannel,
            "previous": self.prevChannel,
            "channelUp": self.nextAR,
            "channelDown": self.prevAR,
            "power": self.power_off}, -1)

    def nextAR(self):
        message = nextAR()
        self.session.open(MessageBox, message, type=MessageBox.TYPE_INFO, timeout=3)

    def prevAR(self):
        message = prevAR()
        self.session.open(MessageBox, message, type=MessageBox.TYPE_INFO, timeout=3)

    def exit(self):
        self.session.nav.stopService()
        self.session.nav.playService(self.oldService)
        self.close()

    def power_off(self):
        self.close(1)

    def play_channel(self):
        try:
            selected_channel = iptv_list_tmp[self.index]
            self["channel_name"].setText(selected_channel[1])
            text = re.compile("<[\\/\\!]*?[^<>]*?>")
            text_clear = ""
            if selected_channel[2] is not None:
                text = str(selected_channel[10])
                text2 = str(selected_channel[2])
                text_clear = text + '\n' + text2
            eserv = 4097
            if config.plugins.XCplugin.LivePlayer.value is True:
                eserv = int(config.plugins.XCplugin.live.value)
            self["programm"].setText(text_clear)
            try:
                desc_image = ''
                if selected_channel[3] != "" and selected_channel[3] != "n/A" and selected_channel[3] is not None:
                    if 'http' not in selected_channel[3]:
                        self.decodeImage(piclogo)
                    else:
                        if STREAMS.img_loader is False:
                            m = hashlib.md5()
                            m.update(selected_channel[3])
                            cover_md5 = m.hexdigest()
                            desc_image = "%s/%s.jpg" % (Path_Tmp, cover_md5)
                        if os.path.exists(desc_image) is False or STREAMS.img_loader is False:
                            desc_image = "%s/%s.jpg" % (Path_Tmp, cover_md5)
                            if PY3 == 3:
                                desc_image = desc_image.encode()
                            downloadPage(selected_channel[3], desc_image, timeout=3).addCallback(self.image_downloaded, desc_image).addErrback(self.downloadError)
                        else:
                            self.decodeImage(desc_image)
            except Exception as ex:
                print(ex)
            try:
                eserv = 4097
                if config.plugins.XCplugin.LivePlayer.value is True:
                    eserv = int(config.plugins.XCplugin.live.value)
                print('eserv ----++++++play channel nIPTVplayer 2+++++---', eserv)
                url = selected_channel[4]
                url = check_port(url)
                self.session.nav.stopService()
                if url != "" and url is not None:
                    sref = eServiceReference(eserv, 0, url)
                    sref.setName(str(selected_channel[10]))
                    try:
                        print("playService: ", sref)
                        self.session.nav.playService(sref)
                    except Exception as ex:
                        print(ex)
            except Exception as ex:
                print(ex)
        except Exception as ex:
            print(ex)

    def nextChannel(self):
        index = self.index
        index += 1
        if index == len(self.channel_list):
            index = 0
        if self.channel_list[index][4] is not None:
            self.index = index
            STREAMS.list_index = self.index
            STREAMS.list_index_tmp = self.index
            self.play_channel()

    def prevChannel(self):
        index = self.index
        index -= 1
        if index == -1:
            index = len(self.channel_list) - 1
        if self.channel_list[index][4] is not None:
            self.index = index
            STREAMS.list_index = self.index
            STREAMS.list_index_tmp = self.index
            self.play_channel()

    def help(self):
        self.session.open(xc_help)

    def show_more_info(self):
        show_more_info()

    def show_more_info_Title(self, truc):
        show_more_info_Title(truc)

    def decodeImage(self, desc_image):
        if isDreamOS:
            self["poster"].instance.setPixmap(gPixmapPtr())
        else:
            self["poster"].instance.setPixmap(None)
        self["poster"].hide()
        sc = AVSwitch().getFramebufferScale()
        self.picload = ePicLoad()
        size = self["poster"].instance.size()
        self.picload.setPara((size.width(), size.height(), sc[0], sc[1], False, 1, '#FF000000'))
        if not isDreamOS:
            self.picload.startDecode(desc_image, 0, 0, False)
        else:
            self.picload.startDecode(desc_image, False)
        ptr = self.picload.getData()
        if ptr is not None:
            self["poster"].instance.setPixmap(ptr)
            self["poster"].show()
        else:
            print('no cover.. error')
        return

    def image_downloaded(self, data, desc_image):
        if os.path.exists(desc_image):
            try:
                self.decodeImage(desc_image)
            except Exception as ex:
                print("* error ** %s" % ex)
                pass
            except:
                pass

    def downloadError(self, desc_image):
        try:
            del_jpg()
            self.decodeImage(piclogo)
        except Exception as ex:
            print(ex)


def xcm3ulistEntry(download):
    res = [download]
    white = 16777215
    blue = 79488
    col = 16777215
    # backcol = 1.923232
    if HD.width() > 1280:
        res.append(MultiContentEntryText(pos=(0, 0), size=(1200, 40), text=download, color=col, color_sel=white, backcolor_sel=blue))
    else:
        res.append(MultiContentEntryText(pos=(0, 0), size=(1000, 30), text=download, color=col, color_sel=white, backcolor_sel=blue))
    return res


def m3ulistxc(data, list):
    icount = 0
    mlist = []
    for line in data:
        name = data[icount]
        mlist.append(xcm3ulistEntry(name))
        icount = icount + 1
    list.setList(mlist)


class xcM3UList(MenuList):
    def __init__(self, list):
        MenuList.__init__(self, list, True, eListboxPythonMultiContent)
        if HD.width() > 1280:
            self.l.setItemHeight(50)
            # textfont = int(32)
            self.l.setFont(0, gFont("Regular", 32))
        else:
            self.l.setItemHeight(50)
            # textfont = int(18)
            self.l.setFont(0, gFont("Regular", 18))


class xc_Play(Screen):
    def __init__(self, session):

        self.session = session
        skin = skin_path + "/xc_M3uLoader.xml"
        with open(skin, 'r') as f:
            self.skin = f.read()
        Screen.__init__(self, session)
        self.list = []
        self["list"] = xcM3UList([])
        global srefInit
        self.initialservice = self.session.nav.getCurrentlyPlayingServiceReference()
        srefInit = self.initialservice
        self.name = Path_Movies
        self["path"] = Label(_("Put .m3u Files in Folder %s") % Path_Movies)
        self["version"] = Label(version)
        self['progress'] = ProgressBar()
        self['progresstext'] = StaticText()
        self["progress"].hide()
        self.downloading = False
        self["key_red"] = Label(_("Back"))
        self["key_green"] = Label(_("Remove"))
        self["key_yellow"] = Label(_("Export") + _(" Bouquet"))
        self["key_blue"] = Label(_("Download") + _(" M3u"))
        self["actions"] = HelpableActionMap(self, "XCpluginActions", {
            "home": self.cancel,
            "green": self.message1,
            "yellow": self.message2,
            "blue": self.message3,
            "cancel": self.cancel,
            "ok": self.runList}, -2)

        self.onFirstExecBegin.append(self.openList)
        self.onLayoutFinish.append(self.layoutFinished)

    def openList(self):
        self.names = []
        self.Movies = []
        AA = [".m3u"]
        try:
            if os.path.exists(Path_Movies):
                for root, dirs, files in os.walk(Path_Movies):
                    for name in files:
                        if '.meta' in name:
                            continue
                        for x in AA:
                            if x not in name:
                                continue
                                pass
                            self.names.append(name)
                            self.Movies.append(root + "/" + name)
                m3ulistxc(self.names, self["list"])
            # else:
                # self.session.open(MessageBox, "The Movie path not configured or path not exist!!!", MessageBox.TYPE_INFO, timeout=5)
                # self.close()
        except Exception as e:
            print (e)
            self.session.open(MessageBox, "The Movie path not configured or path not exist!!!", MessageBox.TYPE_INFO, timeout=5)
            self.close()
            
    def layoutFinished(self):
        pass
                
    def refreshmylist(self):
        self.names = []
        self.list = self.names
        self.names[:] = [0, 0]
        self.openList()

    def runList(self):
        idx = self["list"].getSelectionIndex()
        path = self.Movies[idx]
        if idx == -1 or None:
            return
        else:
            name = path
            if ".m3u" in name:
                self.session.open(xc_M3uPlay, name)
                return
            else:
                name = self.names[idx]
                sref = eServiceReference(4097, 0, path)
                sref.setName(name)
                self.session.openWithCallback(self.backToIntialService, xc_Player, sref)

    def backToIntialService(self, ret=None):
        self.session.nav.stopService()
        self.session.nav.playService(self.initialservice)

    def cancel(self):
        self.close()

    def message1(self):
        idx = self["list"].getSelectionIndex()
        if idx == -1 or None:
            return
        else:
            idx = self["list"].getSelectionIndex()
            dom = self.name + self.names[idx]
            self.session.openWithCallback(self.callMyMsg1, MessageBox, _("Do you want to remove: %s ?") % dom, MessageBox.TYPE_YESNO, timeout=15, default=False)

    def callMyMsg1(self, result):
        if result:
            idx = self["list"].getSelectionIndex()
            dom = self.name + self.names[idx]
            if fileExists(dom):
                os.remove(dom)
                self.session.open(MessageBox, dom + "   has been successfully deleted\nwait time to refresh the list...", MessageBox.TYPE_INFO, timeout=5)
                del self.names[idx]
                m3ulistxc(self.names, self["list"])
            else:
                self.session.open(MessageBox, dom + "   not exist!", MessageBox.TYPE_INFO, timeout=5)

    def message3(self):
        if self.downloading is True:
            self.session.open(MessageBox, "Wait... downloading in progress ...", MessageBox.TYPE_INFO, timeout=5)
            return
        elif "exampleserver.com" not in STREAMS.xtream_e2portal_url:
            self.session.openWithCallback(self.dowM3u1, MessageBox, _("Download M3u File?"), MessageBox.TYPE_YESNO, timeout=15, default=False)
        else:
            self.refreshmylist()

    def dowM3u1(self, result):
        if result:
            self.downloading = False
            if "exampleserver.com" not in STREAMS.xtream_e2portal_url:
                self.m3u_url = urlinfo.replace("enigma2.php", "get.php")
                self.m3u_url = self.m3u_url + '&type=m3u_plus&output=ts'
                self.m3ulnk = ('wget %s -O ' % self.m3u_url)
                self.name_m3u = str(config.plugins.XCplugin.user.value)
                self.pathm3u = Path_Movies + self.name_m3u + '.m3u'
                if os.path.exists(self.pathm3u):
                    cmd = 'rm -f ' + self.pathm3u
                    os.system(cmd)
                try:
                    self.downloading = True
                    self.download = downloadWithProgress(self.m3u_url, self.pathm3u)
                    self.download.addProgress(self.downloadProgress)
                    self.download.start().addCallback(self.check).addErrback(self.showError)
                except Exception as ex:
                    print(ex)
            else:
                self.session.open(MessageBox, _('No Server Configured to Download!!!'), MessageBox.TYPE_WARNING)
                pass

    def downloadProgress(self, recvbytes, totalbytes):
        self["progress"].show()
        self['progress'].value = int(100 * recvbytes / float(totalbytes))
        self['progresstext'].text = '%d of %d kBytes (%.2f%%)' % (recvbytes / 1024, totalbytes / 1024, 100 * recvbytes / float(totalbytes))

    def check(self, fplug):
        checkfile = self.pathm3u
        if os.path.exists(checkfile):
            self['progresstext'].text = ''
            self.progclear = 0
            self['progress'].setValue(self.progclear)
            self.downloading = False
            self.refreshmylist()

    def showError(self, error):
        self.downloading = False
        self.session.open(MessageBox, _('Download Failed!!!'), MessageBox.TYPE_WARNING)
        self.refreshmylist()

    def message2(self):
        idx = self["list"].getSelectionIndex()
        dom = self.names[idx]
        path = self.Movies[idx]
        name = path
        if idx == -1 or None:
            return
        if ".m3u" in name:
            idx = self["list"].getSelectionIndex()
            self.session.openWithCallback(self.convert, MessageBox, _("Do you want to Convert %s to favorite .tv ?") % dom, MessageBox.TYPE_YESNO, timeout=15, default=False)
        else:
            return

    def convert(self, result):
        # idx = self["list"].getSelectionIndex()
        if result:
            # name = self.names[idx]
            self.convert_bouquet()
            return
        else:
            return

    def convert_bouquet(self):
        idx = self["list"].getSelectionIndex()
        if idx == -1 or None:
            return
        else:
            name = Path_Movies + self.names[idx]
            namel = self.names[idx]
            xcname = "userbouquet.%s.tv" % namel.replace(".m3u", "").replace(" ", "")
            # self.iConsole = iConsole()
            # desk_tmp = hls_opt = ""
            desk_tmp = ""
            in_bouquets = 0
            if os.path.isfile("/etc/enigma2/%s" % xcname):
                os.remove("/etc/enigma2/%s" % xcname)
            with open("/etc/enigma2/%s" % xcname, "w") as outfile:
                outfile.write("#NAME %s\r\n" % namel.replace(".m3u", "").replace(" ", "").capitalize())
                for line in open("%s" % name):
                    # for line in open("%s" % name.encode("utf-8")):
                    if line.startswith("http://") or line.startswith("https://"):
                        outfile.write('#SERVICE 4097:0:1:0:0:0:0:0:0:0:%s' % line.replace(':', '%3a'))
                        outfile.write("#DESCRIPTION %s" % desk_tmp)
                    elif line.startswith("#EXTINF"):
                        desk_tmp = "%s" % line.split(",")[-1]
                    elif "<stream_url><![CDATA" in line:
                        outfile.write('#SERVICE 4097:0:1:0:0:0:0:0:0:0:%s\r\n' % line.split("[")[-1].split("]")[0].replace(":", "%3a"))
                        outfile.write("#DESCRIPTION %s\r\n" % desk_tmp)
                    elif "<title>" in line:
                        if "<![CDATA[" in line:
                            desk_tmp = "%s\r\n" % line.split("[")[-1].split("]")[0]
                        else:
                            desk_tmp = "%s\r\n" % line.split("<")[1].split(">")[1]
                outfile.close()
                self.mbox = self.session.open(MessageBox, _("Check on favorites lists..."), MessageBox.TYPE_INFO, timeout=5)
            if os.path.isfile("/etc/enigma2/bouquets.tv"):
                for line in open("/etc/enigma2/bouquets.tv"):
                    if xcname in line:
                        in_bouquets = 1
                if in_bouquets == 0:
                    if os.path.isfile("/etc/enigma2/%s" % xcname) and os.path.isfile("/etc/enigma2/bouquets.tv"):
                        remove_line("/etc/enigma2/bouquets.tv", xcname)
                        with open("/etc/enigma2/bouquets.tv", "a") as outfile:
                            outfile.write('#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "%s" ORDER BY bouquet\r\n' % xcname)
                outfile.close()
            self.mbox = self.session.open(MessageBox, _("Reload Playlists in progress...") + "\n\n\n" + _("wait please..."), MessageBox.TYPE_INFO, timeout=8)
            ReloadBouquet()


class xc_M3uPlay(Screen):
    def __init__(self, session, name):
        self.session = session
        skin = skin_path + "/xc_M3uPlay.xml"
        with open(skin, 'r') as f:
            self.skin = f.read()
        Screen.__init__(self, session)
        self.list = []
        self["list"] = xcM3UList([])
        self["version"] = Label(version)
        self["key_red"] = Label(_("Back"))
        self["key_green"] = Label(_("Reload"))
        self["key_yellow"] = Label(_("Download"))
        self["key_blue"] = Label(_("Search"))
        self['progress'] = ProgressBar()
        self['progresstext'] = StaticText()
        self["progress"].hide()
        self.downloading = False
        global search_ok
        self.search = ''
        search_ok = False
        self["actions"] = HelpableActionMap(self, "XCpluginActions", {
            "home": self.cancel,
            "ok": self.runChannel,
            "blue": self.search_m3u,
            "yellow": self.runRec,
            "rec": self.runRec,
            "instantRecord": self.runRec,
            "ShortRecord": self.runRec,
            "green": self.playList,
            "cancel": self.cancel}, -2)
        self["live"] = Label("")
        self["live"].setText("")
        self.name = name
        self.onLayoutFinish.append(self.playList)

    def search_m3u(self):
        # text = ''
        self.session.openWithCallback(
            self.filterM3u,
            VirtualKeyBoard,
            title=("Filter this category..."),
            text=self.search)

    def filterM3u(self, result):
        if result:
            self.names = []
            self.urls = []
            search = result
            try:
                if fileExists(self.name):
                    f1 = open(self.name, "r+ ")
                    fpage = f1.read()
                    regexcat = "EXTINF.*?,(.*?)\\n(.*?)\\n"
                    match = re.compile(regexcat, re.DOTALL).findall(fpage)
                    for name, url in match:
                        if str(search).lower() in name.lower():
                            global search_ok
                            search_ok = True
                            url = url.replace(" ", "")
                            url = url.replace("\\n", "")
                            self.names.append(name)
                            self.urls.append(url)
                    if search_ok is True:
                        m3ulistxc(self.names, self["list"])
                        self["live"].setText(str(len(self.names)) + " Stream")
                    else:
                        search_ok = False
                        self.playList()
            except:
                pass
        else:
            self.playList()

    def playList(self):
        global search_ok
        search_ok = False
        self.names = []
        self.urls = []
        try:
            if fileExists(self.name):
                f1 = open(self.name, "r+ ")
                fpage = f1.read()
                regexcat = "EXTINF.*?,(.*?)\\n(.*?)\\n"
                match = re.compile(regexcat, re.DOTALL).findall(fpage)
                for name, url in match:
                    url = url.replace(" ", "")
                    url = url.replace("\\n", "")
                    self.names.append(name)
                    self.urls.append(url)
                m3ulistxc(self.names, self["list"])
                self["live"].setText(str(len(self.names)) + " Stream")
        except Exception as ex:
            print(ex)

    def runChannel(self):
        idx = self["list"].getSelectionIndex()
        if idx == -1 or None:
            return
        else:
            name = self.names[idx]
            url = self.urls[idx]
            self.session.open(M3uPlay2, name, url)
            return

    def runRec(self):
        global urlm3u, namem3u
        idx = self["list"].getSelectionIndex()
        namem3u = self.names[idx]
        urlm3u = self.urls[idx]
        if idx == -1 or None:
            return
        else:
            if '.mp4' in urlm3u or '.mkv' in urlm3u or '.flv' in urlm3u:
                self.downloading = True
                self.session.openWithCallback(self.download_m3u, MessageBox, _("DOWNLOAD VIDEO?\n%s" % namem3u), type=MessageBox.TYPE_YESNO, timeout=10, default=False)
            else:
                self.session.open(MessageBox, _("Only VOD Movie allowed!!!"), MessageBox.TYPE_INFO, timeout=5)

    def download_m3u(self, result):
        if result:
            global in_tmp
            if self.downloading is True:
                # selection = str(self['list'].getCurrent())
                idx = self["list"].getSelectionIndex()
                namem3u = self.names[idx]
                urlm3u = self.urls[idx]
                if PY3 == 3:
                    urlm3u = urlm3u.encode()
                fileTitle = re.sub(r'[\<\>\:\"\/\\\|\?\*\[\]]', '_', namem3u)
                fileTitle = re.sub(r' ', '_', fileTitle)
                fileTitle = re.sub(r'_+', '_', fileTitle)
                fileTitle = fileTitle.replace("(", "_").replace(")", "_").replace("#", "").replace("+ ", "_").replace("\'", "_").replace("'", "_")
                fileTitle = fileTitle.lower() + '.mkv'
                in_tmp = Path_Movies + fileTitle
                self.download = downloadWithProgress(urlm3u, in_tmp)
                self.download.addProgress(self.downloadProgress)
                self.download.start().addCallback(self.check).addErrback(self.showError)
            else:
                self.session.open(MessageBox, _('Download Failed!!!'), MessageBox.TYPE_WARNING)
                pass

    def downloadProgress(self, recvbytes, totalbytes):
        self["progress"].show()
        self['progress'].value = int(100 * recvbytes / float(totalbytes))
        self['progresstext'].text = '%d of %d kBytes (%.2f%%)' % (recvbytes / 1024, totalbytes / 1024, 100 * recvbytes / float(totalbytes))

    def check(self, fplug):
        checkfile = in_tmp
        if os.path.exists(checkfile):
            self['progresstext'].text = ''
            self.progclear = 0
            self['progress'].setValue(self.progclear)
            MemClean()

    def showError(self, error):
        self.downloading = False
        print("download error =", error)
        self.session.open(MessageBox, _('Download Failed!!!'), MessageBox.TYPE_WARNING)

    def cancel(self):
        if search_ok is True:
            self.playList()
        else:
            self.session.nav.stopService()
            self.session.nav.playService(srefInit)
            self.close()


class M3uPlay2(Screen, InfoBarMenu, InfoBarBase, InfoBarSeek, InfoBarNotifications, InfoBarAudioSelection, IPTVInfoBarShowHide, InfoBarSubtitleSupport):
    STATE_IDLE = 0
    STATE_PLAYING = 1
    STATE_PAUSED = 2
    ENABLE_RESUME_SUPPORT = True
    ALLOW_SUSPEND = True

    def __init__(self, session, name, url):
        Screen.__init__(self, session)
        self.skinName = 'MoviePlayer'
        # title = 'Play Stream'
        self['list'] = MenuList([])
        InfoBarMenu.__init__(self)
        InfoBarNotifications.__init__(self)
        InfoBarBase.__init__(self, steal_current_service=True)
        IPTVInfoBarShowHide.__init__(self)
        InfoBarSubtitleSupport.__init__(self)
        InfoBarAudioSelection.__init__(self)
        self['actions'] = ActionMap([
            'WizardActions',
            'MoviePlayerActions',
            'MovieSelectionActions',
            'MediaPlayerActions',
            'EPGSelectActions',
            'MediaPlayerSeekActions',
            'SetupActions',
            'ColorActions',
            'InfobarShowHideActions',
            'InfobarActions',
            'InfobarSeekActions'],
            {'leavePlayer': self.cancel,
                'epg': self.showIMDB,
                'info': self.showIMDB,
                'stop': self.leavePlayer,
                'cancel': self.cancel,
                'back': self.cancel}, -1)
        self.allowPiP = False
        InfoBarSeek.__init__(self, actionmap='InfobarSeekActions')
        url = url.replace(':', '%3a')
        self.url = url
        self.name = name
        self.srefOld = self.session.nav.getCurrentlyPlayingServiceReference()
        self.state = self.STATE_PLAYING
        self.openPlay()
        self.onClose.append(self.cancel)

    def showIMDB(self):
        if '.mp4' in self.url or '.mkv' in self.url or '.flv' in self.url or '.avi' in self.url:
            if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/TMBD/plugin.pyo"):
                from Plugins.Extensions.TMBD.plugin import TMBD
                text_clear = self.name
                text = charRemove(text_clear)
                self.session.open(TMBD, text, False)
            elif os.path.exists("/usr/lib/enigma2/python/Plugins/Extensions/IMDb/plugin.pyo"):
                from Plugins.Extensions.IMDb.plugin import IMDB
                text_clear = self.name
                text = charRemove(text_clear)
                HHHHH = text
                self.session.open(IMDB, HHHHH)
            else:
                text_clear = self.name
                self.session.open(xc_Epg, text_clear)
        else:
            self.session.open(MessageBox, _('Only VOD Movie allowed!!!'), MessageBox.TYPE_WARNING)

    def openPlay(self):
        url = str(self.url)
        if ".ts" or ".mp4" or ".avi" or ".mkv" in self.url:
            url = url.replace(':', '%3a')
            ref = '4097:0:1:0:0:0:0:0:0:0:' + url
        else:
            if config.plugins.TivuStream.services.value == 'Gstreamer':
                ref = '5001:0:1:0:0:0:0:0:0:0:' + url
            elif config.plugins.TivuStream.services.value == 'Exteplayer3':
                ref = '5002:0:1:0:0:0:0:0:0:0:' + url
            elif config.plugins.TivuStream.services.value == 'StreamLink':
                ref = '5002:0:1:0:0:0:0:0:0:0:http%3a//127.0.0.1%3a8088/' + url
            else:
                ref = '4097:0:1:0:0:0:0:0:0:0:' + url
        sref = eServiceReference(ref)
        sref.setName(self.name)
        self.session.nav.stopService()
        self.session.nav.playService(sref)

    def cancel(self):
        self.session.nav.stopService()
        self.session.nav.playService(srefInit)
        self.close()

    def keyLeft(self):
        self["text"].left()

    def keyRight(self):
        self["text"].right()

    def leavePlayer(self):
        self.close()

    def showVideoInfo(self):
        if self.shown:
            self.hideInfobar()
        if self.infoCallback is not None:
            self.infoCallback()
        return

    def showAfterSeek(self):
        if isinstance(self, IPTVInfoBarShowHide):
            self.doShow()


def menu(menuid, **kwargs):
    if menuid == "mainmenu":
        return [("XCplugin", main, "XCplugin", 4)]
    return []


def main(session, **kwargs):
    global STREAMS
    STREAMS = iptv_streamse()
    STREAMS.read_config()
    if "exampleserver.com" not in STREAMS.xtream_e2portal_url:
        STREAMS.get_list(STREAMS.xtream_e2portal_url)
        session.openWithCallback(check_configuring, xc_home)
    else:
        session.openWithCallback(check_configuring, xc_home)


_session = None
autoStartTimer = None


class AutoStartTimer:

    def __init__(self, session):
        self.session = session
        self.timer = eTimer()
        self.timer.start(50, 1)
        try:
            self.timer.callback.append(self.on_timer)
        except:
            self.timer_conn = self.timer.timeout.connect(self.on_timer)
        self.update()

    def get_wake_time(self):
        if config.plugins.XCplugin.autobouquetupdate.value:
            if config.plugins.XCplugin.timetype.value == "interval":
                interval = int(config.plugins.XCplugin.updateinterval.value)
                nowt = time.time()
                return int(nowt) + interval * 60 * 60
            if config.plugins.XCplugin.timetype.value == "fixed time":
                ftc = config.plugins.XCplugin.fixedtime.value
                now = time.localtime(time.time())
                fwt = int(time.mktime((now.tm_year,
                                       now.tm_mon,
                                       now.tm_mday,
                                       ftc[0],
                                       ftc[1],
                                       now.tm_sec,
                                       now.tm_wday,
                                       now.tm_yday,
                                       now.tm_isdst)))
                return fwt
        else:
            return -1

    def update(self, constant=0):
        self.timer.stop()
        wake = self.get_wake_time()
        nowt = time.time()
        now = int(nowt)
        if wake > 0:
            if wake < now + constant:
                if config.plugins.XCplugin.timetype.value == "interval":
                    interval = int(config.plugins.XCplugin.updateinterval.value)
                    wake += interval * 60 * 60
                elif config.plugins.XCplugin.timetype.value == "fixed time":
                    wake += 86400
            next = wake - now
            self.timer.startLongTimer(next)
        else:
            wake = -1
        return wake

    def on_timer(self):
        self.timer.stop()
        now = int(time.time())
        wake = now
        constant = 0
        if config.plugins.XCplugin.timetype.value == "fixed time":
            wake = self.get_wake_time()
        if wake - now < 60:
            try:
                self.startMain()
                self.update()
                localtime = time.asctime(time.localtime(time.time()))
                config.plugins.XCplugin.last_update.value = localtime
                config.plugins.XCplugin.last_update.save()
            except Exception as ex:
                print(ex)
        self.update(constant)

    def startMain(self):
        from Plugins.Extensions.XCplugin.plugin import iptv_streamse
        global STREAMS
        STREAMS = iptv_streamse()
        STREAMS.read_config()
        STREAMS.get_list(STREAMS.xtream_e2portal_url)
        if str(config.plugins.XCplugin.typelist.value) == "Combined Live/VOD":
            save_old()
        else:
            createCfg_xml()


def check_configuring():
    """Check for new config values for auto start
    """
    global autoStartTimer
    if autoStartTimer is not None:
        autoStartTimer.update()
    return


def autostart(reason, session=None, **kwargs):
    global autoStartTimer
    global _session
    if reason == 0 and _session is None:
        if session is not None:
            _session = session
            if autoStartTimer is None:
                autoStartTimer = AutoStartTimer(session)
    return


def get_next_wakeup():
    return -1


mainDescriptor = PluginDescriptor(name="XCplugin Forever", description=version, where=PluginDescriptor.WHERE_MENU, fnc=menu)


def Plugins(**kwargs):
    result = [PluginDescriptor(name="XCplugin Forever", description=version, where=[PluginDescriptor.WHERE_AUTOSTART, PluginDescriptor.WHERE_SESSIONSTART], fnc=autostart, wakeupfnc=get_next_wakeup),
              PluginDescriptor(name="XCplugin", description=version, where=PluginDescriptor.WHERE_PLUGINMENU, icon=iconpic, fnc=main)]  # fnc=Start_iptv_player)]
    if config.plugins.XCplugin.strtmain.value:
        result.append(mainDescriptor)
    return result

# JobManager.AddJob(downloadJob(self, "wget %s -c '%s' -O '%s%s'" % (useragentcmd, url, Path_Movies2, name), Path_Movies2 + filetitle, filetitle, self.downloadStop))


class downloadJob(Job):

    def __init__(self, toolbox, cmdline, filename, filetitle, downloadStop):
        Job.__init__(self, "%s" % filetitle)
        self.filename = filename
        self.toolbox = toolbox
        self.retrycount = 0
        downloadTask(self, cmdline, filename, downloadStop)

    def retry(self):
        self.retrycount += 1
        MemClean()
        self.restart()

    def cancel(self):
        self.abort()


class downloadTask(Task):
    ERROR_CORRUPT_FILE, ERROR_RTMP_ReadPacket, ERROR_SEGFAULT, ERROR_SERVER, ERROR_UNKNOWN = range(5)

    def __init__(self, job, cmdline, filename, downloadStop):
        Task.__init__(self, job, _("Downloading ..."))
        self.setCmdline(cmdline)
        self.filename = filename
        self.toolbox = job.toolbox

        self.downloadStop = downloadStop

        self.error = None
        self.lasterrormsg = None

    def processOutput(self, data):
        try:
            if data.endswith("%)"):
                startpos = data.rfind("sec (") + 5
                if startpos and startpos != -1:
                    self.progress = int(float(data[startpos:-4]))
            elif data.find("%") != -1:
                tmpvalue = data[:data.find("%")]
                tmpvalue = tmpvalue[tmpvalue.rfind(" "):].strip()
                tmpvalue = tmpvalue[tmpvalue.rfind("(") + 1:].strip()
                self.progress = int(float(tmpvalue))
                MemClean()
            else:
                Task.processOutput(self, data)
        except Exception as errormsg:
            print("Error processOutput: " + str(errormsg))
            self.downloadStop()
            Task.processOutput(self, data)

    def afterRun(self):
        if self.getProgress() == 0 or self.getProgress() == 100:
            self.downloadStop()
            # pmovies = False
            MemClean()
            self.downloading = False
            message = "Movie successfully transfered to your HDD!" + "\n" + self.filename
            web_info(message)


VIDEO_ASPECT_RATIO_MAP = {
    0: "4:3 Letterbox",
    1: "4:3 PanScan",
    2: "16:9",
    3: "16:9 Always",
    4: "16:10 Letterbox",
    5: "16:10 PanScan",
    6: "16:9 Letterbox"}

VIDEO_FMT_PRIORITY_MAP = {"38": 1, "37": 2, "22": 3, "18": 4, "35": 5, "34": 6}


def nextAR():
    try:
        STREAMS.ar_id_player += 3
        if STREAMS.ar_id_player > 6:
            STREAMS.ar_id_player = 3
        eAVSwitch.getInstance().setAspectRatio(STREAMS.ar_id_player)
        print("STREAMS.ar_id_player NEXT %s" % VIDEO_ASPECT_RATIO_MAP[STREAMS.ar_id_player])
        return VIDEO_ASPECT_RATIO_MAP[STREAMS.ar_id_player]
    except Exception as ex:
        print(ex)
        return "nextAR ERROR %s" % ex


def prevAR():
    try:
        STREAMS.ar_id_player -= 3
        if STREAMS.ar_id_player == -1:
            STREAMS.ar_id_player = 3
        eAVSwitch.getInstance().setAspectRatio(STREAMS.ar_id_player)
        print("STREAMS.ar_id_player PREV %s" % VIDEO_ASPECT_RATIO_MAP[STREAMS.ar_id_player])
        return VIDEO_ASPECT_RATIO_MAP[STREAMS.ar_id_player]
    except Exception as ex:
        print(ex)
        return "prevAR ERROR %s" % ex


def channelEntryIPTVplaylist(entry):
    menu_entry = [
        entry,
        (eListboxPythonMultiContent.TYPE_TEXT, CHANNEL_NUMBER[0], CHANNEL_NUMBER[1], CHANNEL_NUMBER[2], CHANNEL_NUMBER[3], CHANNEL_NUMBER[4], RT_HALIGN_CENTER, "%s" % entry[0]),
        (eListboxPythonMultiContent.TYPE_TEXT, CHANNEL_NAME[0], CHANNEL_NAME[1], CHANNEL_NAME[2], CHANNEL_NAME[3], CHANNEL_NAME[4], RT_HALIGN_LEFT, entry[1])]
    return menu_entry


def web_info(message):
    try:
        message = quote_plus(str(message))
        cmd = "wget -qO - 'http://127.0.0.1/web/message?type=2&timeout=10&text=%s' 2>/dev/null &" % message
        debug(cmd, "CMD -> Console -> WEBIF")
        os.popen(cmd)
    except:
        print("web_info ERROR")


def debug(obj, text=""):
    print("%s" % text + " %s\n" % obj)


conversion = {
    str("\xd0\xb0"): "a",
    str("\xd0\x90"): "A",
    str("\xd0\xb1"): "b",
    str("\xd0\x91"): "B",
    str("\xd0\xb2"): "v",
    str("\xd0\x92"): "V",
    str("\xd0\xb3"): "g",
    str("\xd0\x93"): "G",
    str("\xd0\xb4"): "d",
    str("\xd0\x94"): "D",
    str("\xd0\xb5"): "e",
    str("\xd0\x95"): "E",
    str("\xd1\x91"): "jo",
    str("\xd0\x81"): "jo",
    str("\xd0\xb6"): "zh",
    str("\xd0\x96"): "ZH",
    str("\xd0\xb7"): "z",
    str("\xd0\x97"): "Z",
    str("\xd0\xb8"): "i",
    str("\xd0\x98"): "I",
    str("\xd0\xb9"): "j",
    str("\xd0\x99"): "J",
    str("\xd0\xba"): "k",
    str("\xd0\x9a"): "K",
    str("\xd0\xbb"): "l",
    str("\xd0\x9b"): "L",
    str("\xd0\xbc"): "m",
    str("\xd0\x9c"): "M",
    str("\xd0\xbd"): "n",
    str("\xd0\x9d"): "N",
    str("\xd0\xbe"): "o",
    str("\xd0\x9e"): "O",
    str("\xd0\xbf"): "p",
    str("\xd0\x9f"): "P",
    str("\xd1\x80"): "r",
    str("\xd0\xa0"): "R",
    str("\xd1\x81"): "s",
    str("\xd0\xa1"): "S",
    str("\xd1\x82"): "t",
    str("\xd0\xa2"): "T",
    str("\xd1\x83"): "u",
    str("\xd0\xa3"): "U",
    str("\xd1\x84"): "f",
    str("\xd0\xa4"): "F",
    str("\xd1\x85"): "h",
    str("\xd0\xa5"): "H",
    str("\xd1\x86"): "c",
    str("\xd0\xa6"): "C",
    str("\xd1\x87"): "ch",
    str("\xd0\xa7"): "CH",
    str("\xd1\x88"): "sh",
    str("\xd0\xa8"): "SH",
    str("\xd1\x89"): "sh",
    str("\xd0\xa9"): "SH",
    str("\xd1\x8a"): "",
    str("\xd0\xaa"): "",
    str("\xd1\x8b"): "y",
    str("\xd0\xab"): "Y",
    str("\xd1\x8c"): "j",
    str("\xd0\xac"): "J",
    str("\xd1\x8d"): "je",
    str("\xd0\xad"): "JE",
    str("\xd1\x8e"): "ju",
    str("\xd0\xae"): "JU",
    str("\xd1\x8f"): "ja",
    str("\xd0\xaf"): "JA"}


def cyr2lat(text):
    i = 0
    text = text.strip(" \t\n\r")
    text = str(text)
    retval = ""
    bukva_translit = ""
    bukva_original = ""
    while i < len(text):
        bukva_original = text[i]
        try:
            bukva_translit = conversion[bukva_original]
        except:
            bukva_translit = bukva_original
        i = i + 1
        retval += bukva_translit
    return retval


def ReloadBouquet():
    try:
        eDVBDB.getInstance().reloadServicelist()
        eDVBDB.getInstance().reloadBouquets()
    except:
        os.system('wget -qO - http://127.0.0.1/web/servicelistreload?mode=2 > /dev/null 2>&1 &')


def uninstaller():
    """Clean up routine to remove any previously made changes
    """
    try:
        for fname in os.listdir(enigma_path):
            if 'userbouquet.suls_iptv_' in fname:
                os.remove(os.path.join(enigma_path, fname))
            elif 'bouquets.tv.bak' in fname:
                os.remove(os.path.join(enigma_path, fname))
        if os.path.isdir(epgimport_path):
            for fname in os.listdir(epgimport_path):
                if 'suls_iptv_' in fname:
                    os.remove(os.path.join(epgimport_path, fname))
        os.rename(os.path.join(enigma_path, 'bouquets.tv'), os.path.join(enigma_path, 'bouquets.tv.bak'))
        tvfile = open(os.path.join(enigma_path, 'bouquets.tv'), 'w+')
        bakfile = open(os.path.join(enigma_path, 'bouquets.tv.bak'))
        for line in bakfile:
            if '.suls_iptv_' not in line:
                tvfile.write(line)
        bakfile.close()
        tvfile.close()
    except Exception as ex:
        print(ex)
        raise


def OnclearMem():
    os.system("sync")
    os.system("echo 3 > /proc/sys/vm/drop_caches")


def remove_line(filename, what):
    if os.path.isfile(filename):
        file_read = open(filename).readlines()
        file_write = open(filename, "w")
        for line in file_read:
            if what not in line:
                file_write.write(line)
        file_write.close()


if os.path.isfile(filterlist):
    global filtertmdb
    try:
        with open(filterlist) as f:
            lines = [line.rstrip("\n") for line in open(tmdblist)]
            start = ('": ' + '"' + '",' + ' "')
            mylist = start.join(lines)
            end = ('{"' + mylist + '": ' + '"' + '"' + "}")
            dict = eval(filtertmdb)
            filtertmdb = "".join(end.splitlines())
            filtertmdb = dict
    except:
        filtertmdb = {"x264": "", "1080p": "", "1080i": "", "720p": "", "VOD": "", "vod": "", "Ac3-evo": "", "Hdrip": "", "Xvid": ""}


def charRemove(text):
    char = ["1080p",
            "2018",
            "2019",
            "2020",
            "480p",
            "4K",
            "720p",
            "ANIMAZIONE",
            "APR",
            "AVVENTURA",
            "BIOGRAFICO",
            "BDRip",
            "BluRay",
            "CINEMA",
            "COMMEDIA",
            "DOCUMENTARIO",
            "DRAMMATICO",
            "FANTASCIENZA",
            "FANTASY",
            "FEB",
            "GEN",
            "GIU",
            "HDCAM",
            "HDTC",
            "HDTS",
            "LD",
            "MAFIA",
            "MAG",
            "MARVEL",
            "MD",
            "ORROR",
            "NEW_AUDIO",
            "POLIZ",
            "R3",
            "R6",
            "SD",
            "SENTIMENTALE",
            "TC",
            "TEEN",
            "TELECINE",
            "TELESYNC",
            "THRILLER",
            "Uncensored",
            "V2",
            "WEBDL",
            "WEBRip",
            "WEB",
            "WESTERN",
            "-",
            "_",
            ".",
            "+",
            "[",
            "]"]
    myreplace = text
    for ch in char:
        myreplace = myreplace.replace(ch, "").replace("  ", " ").replace("       ", " ").strip()
    return myreplace


class xc_home(Screen):

    def __init__(self, session):
        self.session = session
        skin = skin_path + "/xc_home.xml"
        with open(skin, 'r') as f:
            self.skin = f.read()
        Screen.__init__(self, session)
        self.setup_title = ('Home XCplugin Forever')
        Screen.__init__(self, session)
        self.list = []
        self["Text"] = Label("XCplugin Forever")
        self["version"] = Label(version)
        self['text'] = xcList([])
        self["key_red"] = Label(_("Exit"))
        self["key_green"] = Label(_("Playlist"))
        self["key_yellow"] = Label(_("Movie"))
        self["key_blue"] = Label(_("Loader M3U"))
        self["actions"] = HelpableActionMap(self, "XCpluginActions", {
            "cancel": self.exitY,
            "back": self.exitY,
            "home": self.exitY,
            "showMediaPlayer": self.showMovies,
            "pvr": self.showMovies,
            "2": self.showMovies,
            "menu": self.config,
            "help": self.help,
            "green": self.Team,
            "yellow": self.taskManager,
            "movielist": self.taskManager,
            "blue": self.xcPlay,
            "ok": self.button_ok,
            "info": self.aboutxc}, -1)
        # self.onFirstExecBegin.append(self.check_dependencies)
        self.onLayoutFinish.append(self.updateMenuList)

    def check_dependencies(self):
        dependencies = True
        if PY3:
            if not os.path.exists("/usr/lib/python3.8/site-packages/requests"):
                dependencies = False
        else:
            if not os.path.exists("/usr/lib/python2.7/site-packages/requests"):
                dependencies = False
        if dependencies is False:
            if not access("/usr/lib/enigma2/python/Plugins/Extensions/XCplugin/dependencies.sh", X_OK):
                chmod("/usr/lib/enigma2/python/Plugins/Extensions/XCplugin/dependencies.sh", 0o0755)
            cmd1 = ". /usr/lib/enigma2/python/Plugins/Extensions/XCplugin/dependencies.sh"
            self.session.openWithCallback(self.start, Console, title="Checking Python 2 Dependencies", cmdlist=[cmd1], closeOnSuccess=False)
        else:
            self.start()

    def start(self):
        OnclearMem()

    def config(self):
        self.session.open(xc_config)

    def button_ok(self):
        self.keyNumberGlobalCB(self['text'].getSelectedIndex())

    def exitY(self):
        ReloadBouquet()
        self.close()

    def Team(self):
        self.session.open(OpenServer)

    def aboutxc(self):
        about = self.getabout()
        self.session.open(MessageBox, about, type=MessageBox.TYPE_INFO)

    def help(self):
        self.session.open(xc_help)

    def taskManager(self):
        self.session.open(xc_StreamTasks)

    def xcPlay(self):
        self.session.open(xc_Play)

    def showMovies(self):
        try:
            self.session.open(MovieSelection)
        except:
            pass

    def OpenList(self):
        global STREAMS
        STREAMS = iptv_streamse()
        STREAMS.read_config()
        if "exampleserver.com" not in STREAMS.xtream_e2portal_url:
            STREAMS.get_list(STREAMS.xtream_e2portal_url)
            self.session.openWithCallback(check_configuring, xc_Main)
        else:
            message = (_("First Select the list or enter it in Config"))
            web_info(message)

    def updateMenuList(self):
        self.menu_list = []
        for x in self.menu_list:
            del self.menu_list[0]
        list = []
        idx = 0
        for x in Panel_list:
            list.append(menuListEntry(x, idx))
            self.menu_list.append(x)
            idx += 1
        self['text'].setList(list)

    def keyNumberGlobalCB(self, idx):
        sel = self.menu_list[idx]
        if sel == ('HOME'):
            self.OpenList()
        elif sel == ('PLAYLIST'):
            self.session.open(OpenServer)
        elif sel == ('MAKER BOUQUET'):
            self.session.open(xc_maker)
        elif sel == ('CONFIG'):
            self.session.open(xc_config)
        elif sel == ('MOVIE'):
            self.taskManager()
        elif sel == ('M3U LOADER'):
            if PY3:
                message = (_("PY3 Not Supported!!!"))
                web_info(message)
            else:
                self.session.open(xc_Play)
        elif sel == ('XC HELP'):
            self.session.open(xc_help)
        elif sel == ('ABOUT'):
            self.aboutxc()

    def getabout(self):
        conthelp = "%s\n\n" % version
        conthelp += "original code by Dave Sully, Doug Mackay\n\n"
        conthelp += "Modded by Lululla\n\n"
        conthelp += "Skin By: Mmark - Info e2skin.blogspot.it\n\n"
        conthelp += "*************************************\n\n"
        conthelp += "Please reports bug or info to forums:\n\n"
        conthelp += "Corvoboys - linuxsat-support - dream-elite\n\n"
        conthelp += "Special thanks to:\n"
        conthelp += "MMark, Pcd, KiddaC\n"
        conthelp += "aime_jeux, Support, Enigma1969, MasterG\n"
        conthelp += "and all those i forgot to mention."
        return conthelp


class xc_maker(Screen):

    def __init__(self, session):
        self.session = session
        skin = skin_path + "/xc_maker.xml"
        with open(skin, 'r') as f:
            self.skin = f.read()
        Screen.__init__(self, session)
        self.setup_title = ('XCplugin Forever')
        Screen.__init__(self, session)
        self.list = []
        self["Text"] = Label("XCplugin Forever")
        self["version"] = Label(version)
        self["description"] = Label("")
        self.picfile = ""
        self["key_red"] = Label(_("Back"))
        self["key_green"] = Label(_("Make"))
        self["key_yellow"] = Label(_("Remove"))
        self["actions"] = HelpableActionMap(self, "XCpluginActions", {
            "cancel": self.exitY,
            "back": self.exitY,
            "home": self.exitY,
            "menu": self.config,
            "help": self.help,
            "green": self.maker,
            "yellow": self.remove}, -1)
        self.onLayoutFinish.append(self.updateMenuList)

    def config(self):
        self.session.open(xc_config)

    def exitY(self):
        self.close()

    def help(self):
        self.session.open(xc_help)

    def updateMenuList(self):
        self["description"].setText(self.getabout())

    def maker(self):
        if str(config.plugins.XCplugin.typelist.value) == "Multi Live & VOD":
            dom = "Multi Live & VOD"
            self.session.openWithCallback(self.createCfgxml, MessageBox, _("Convert Playlist to:      %s ?") % dom, MessageBox.TYPE_YESNO, timeout=10)  # default=False)
        elif str(config.plugins.XCplugin.typelist.value) == "Multi Live/Single VOD":
            dom = "Multi Live/Single VOD"
            self.session.openWithCallback(self.createCfgxml, MessageBox, _("Convert Playlist to:      %s ?") % dom, MessageBox.TYPE_YESNO, timeout=10)  # default=False)

        elif str(config.plugins.XCplugin.typelist.value) == "Combined Live/VOD":
            dom = "Combined Live/VOD"
            self.session.openWithCallback(self.save_tv, MessageBox, _("Convert Playlist to:  %s ?") % dom, MessageBox.TYPE_YESNO, timeout=10)  # default=False)
        else:
            return

    def save_tv(self, result):
        if result:
            save_old()
            self.mbox = self.session.open(MessageBox, _("Reload Playlists in progress...") + "\n\n\n" + _("wait please..."), MessageBox.TYPE_INFO, timeout=8)

    def createCfgxml(self, result):
        if result:
            createCfg_xml()
            ReloadBouquet()

    def remove(self):
        self.session.openWithCallback(self.removelistok, MessageBox, _("Remove all XC Plugin bouquets?"), MessageBox.TYPE_YESNO, timeout=15)  # default = True)

    def removelistok(self, result):
        if result:
            uninstaller()
            ReloadBouquet()

    def getabout(self):
        conthelp = _("GREEN BUTTON:\n ")
        conthelp += _("   Create XC Live/VOD Bouquets\n")
        conthelp += _("    You need to configure the type of output\n")
        conthelp += _("    in the config menu\n\n")
        conthelp += _("YELLOW BUTTON:\n")
        conthelp += _("    Removes all the bouquets that have been\n")
        conthelp += _("    created with XCplugin\n\n")
        conthelp += _("HELP BUTTON:\n")
        conthelp += _("    Go to Help info plugin\n\n")
        conthelp += _("Current configuration for creating the bouquet\n>>>>%s Conversion %s\n\n") % (config.plugins.XCplugin.typem3utv.getValue(), config.plugins.XCplugin.typelist.getValue())  # config.plugins.XCplugin.typem3utv.value
        conthelp += "Time is what we want most,\n"
        conthelp += "    but what we use worst.(William Penn)"
        return conthelp


Panel_list = [
    ('HOME'),
    ('PLAYLIST'),
    ('MAKER BOUQUET'),
    ('CONFIG'),
    ('MOVIE'),
    ('M3U LOADER'),
    ('XC HELP'),
    ('ABOUT')
]

pngl = plugin_path + '/skin/fhd/xcselh.png'
png2 = plugin_path + '/skin/hd/xcsel.png'


class xcList(MenuList):
    def __init__(self, list):
        MenuList.__init__(self, list, False, eListboxPythonMultiContent)
        self.l.setFont(0, gFont('Regular', 20))
        self.l.setFont(1, gFont('Regular', 22))
        self.l.setFont(2, gFont('Regular', 24))
        self.l.setFont(3, gFont('Regular', 26))
        self.l.setFont(4, gFont('Regular', 28))
        self.l.setFont(5, gFont('Regular', 30))
        self.l.setFont(6, gFont('Regular', 32))
        self.l.setFont(7, gFont('Regular', 34))
        self.l.setFont(8, gFont('Regular', 36))
        self.l.setFont(9, gFont('Regular', 50))
        if HD.width() > 1280:
            self.l.setItemHeight(60)
        else:
            self.l.setItemHeight(60)


def menuListEntry(name, idx):

    res = [name]
    if HD.width() > 1280:
        res.append(MultiContentEntryPixmapAlphaTest(pos=(10, 10), size=(70, 40), png=loadPNG(pngl)))
        res.append(MultiContentEntryText(pos=(100, 4), size=(1200, 50), font=6, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    else:
        res.append(MultiContentEntryPixmapAlphaTest(pos=(10, 5), size=(70, 40), png=loadPNG(png2)))
        res.append(MultiContentEntryText(pos=(100, 2), size=(1000, 50), font=5, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    return res


def show_more_info():
    text_clear = ""
    if "exampleserver.com" not in STREAMS.xtream_e2portal_url:
        text = re.compile("<[\\/\\!]*?[^<>]*?>")
        if stream_live:
            text2 = selected_channel[2]
            text3 = selected_channel[8]
            text_clear = str(text2) + '\n\n' + str(text3)
            _session.open(xc_Epg, text_clear)
        else:
            if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/TMBD/plugin.pyo"):
                from Plugins.Extensions.TMBD.plugin import TMBD
                text_clear = str(selected_channel[10])
                text = charRemove(text_clear)
                _session.open(TMBD, text, False)
            elif os.path.exists("/usr/lib/enigma2/python/Plugins/Extensions/IMDb/plugin.pyo"):
                from Plugins.Extensions.IMDb.plugin import IMDB
                text_clear = str(selected_channel[10])
                text = charRemove(text_clear)
                HHHHH = text
                _session.open(IMDB, HHHHH)
            else:
                text_clear = str(selected_channel[2])
                _session.open(xc_Epg, text_clear)
    else:
        message = (_("Please enter correct parameters in Config\n no valid list "))
        web_info(message)


def show_more_info_Title(truc):
    text_clear_1 = ""
    try:
        if truc[1] is not None:
            descr = truc
            text = re.compile("<[\\/\\!]*?[^<>]*?>")
            AAA = descr[2].split("]")[1:][0]
            BBB = AAA.split("(")[:1][0]
            text_clear_1 = text.sub("", BBB).replace(" ", " ").replace("\n", " ").replace("\t", " ").replace("\r", " ")
        else:
            text_clear_1 = "No Even"
    except Exception as ex:
        print(ex)
        text_clear_1 = "mkach"
    return text_clear_1


def save_old():
    fldbouquet = "/etc/enigma2/bouquets.tv"
    namebouquet = checkStr(STREAMS.playlistname).lower()
    tag = "suls_iptv_"
    xc12 = urlinfo.replace("enigma2.php", "get.php")
    in_bouquets = 0
    # desk_tmp = hls_opt = ''
    desk_tmp = ''
    if config.plugins.XCplugin.typem3utv.value == 'MPEGTS to TV':
        xc2 = '&type=dreambox&output=mpegts'
        if os.path.isfile('%suserbouquet.%s%s_.tv' % (enigma_path, tag, namebouquet)):
            os.remove('%suserbouquet.%s%s_.tv' % (enigma_path, tag, namebouquet))
        try:
            urlX = xc12 + xc2
            webFile = urlopen(urlX, timeout=ntimeout)
            localFile = open(('%suserbouquet.%s%s_.tv' % (enigma_path, tag, namebouquet)), 'w')
            localFile.write(checkStr(webFile.read()))
            os.system('sleep 5')
            localFile.close()
            webFile.close()

        except Exception as ex:
            print(ex)
        xcname = 'userbouquet.%s%s_.tv' % (tag, namebouquet)
    else:
        xc2 = '&type=m3u_plus&output=ts'
        if os.path.isfile(Path_Movies + namebouquet + ".m3u"):
            os.remove(Path_Movies + namebouquet + ".m3u")
        try:
            urlX = xc12 + xc2
            webFile = urlopen(urlX, timeout=ntimeout)
            localFile = open(('%s%s.m3u' % (Path_Movies, namebouquet)), 'w')
            localFile.write(checkStr(webFile.read()))
            os.system('sleep 5')
            localFile.close()
            webFile.close()
        except Exception as ex:
            print(ex)
        namebouquet = Path_Movies + '%s.m3u' % namebouquet
        name = namebouquet.replace('.m3u', '').replace(Path_Movies, '')
        xcname = 'userbouquet.%s%s_.tv' % (tag, name)
        # iConsole = iConsole()
        if os.path.isfile('/etc/enigma2/%s' % xcname):
            os.remove('/etc/enigma2/%s' % xcname)
        with open('/etc/enigma2/%s' % xcname, 'w') as outfile:
            outfile.write('#NAME %s\r\n' % name.capitalize())
            for line in open(Path_Movies + '%s.m3u' % name):
                if line.startswith('http://') or line.startswith('https://'):
                    outfile.write('#SERVICE 4097:0:1:0:0:0:0:0:0:0:%s' % line.replace(':', '%3a'))
                    outfile.write('#DESCRIPTION %s' % desk_tmp)
                elif line.startswith('#EXTINF'):
                    desk_tmp = '%s' % line.split(',')[-1]
                elif '<stream_url><![CDATA' in line:
                    outfile.write('#SERVICE 4097:0:1:0:0:0:0:0:0:0:%s\r\n' % line.split('[')[-1].split(']')[0].replace(':', '%3a'))
                    outfile.write('#DESCRIPTION %s\r\n' % desk_tmp)
                elif '<title>' in line:
                    if '<![CDATA[' in line:
                        desk_tmp = '%s\r\n' % line.split('[')[-1].split(']')[0]
                    else:
                        desk_tmp = '%s\r\n' % line.split('<')[1].split('>')[1]
            outfile.close()
    if os.path.isfile(fldbouquet):
        for line in open(fldbouquet):
            if xcname in line:
                in_bouquets = 1
        if in_bouquets == 0:
            new_bouquet = open("/etc/enigma2/new_bouquets.tv", "w")
            file_read = open(fldbouquet).readlines()
            if config.plugins.XCplugin.bouquettop.value == "Top":
                new_bouquet.write('#NAME User - bouquets (TV)\n')
                new_bouquet.write('#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "%s" ORDER BY bouquet\r\n' % xcname)
                for line in file_read:
                    if line.startswith("#NAME"):
                        continue
                    new_bouquet.write(line)
                new_bouquet.close()
            else:
                for line in file_read:
                    new_bouquet.write(line)
                new_bouquet.write('#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "%s" ORDER BY bouquet\r\n' % xcname)
                new_bouquet.close()
            os.system('cp -rf /etc/enigma2/bouquets.tv /etc/enigma2/backup_bouquets.tv')
            os.system('mv -f /etc/enigma2/new_bouquets.tv /etc/enigma2/bouquets.tv')
    ReloadBouquet()


def createCfg_xml():
    # path = tempfile.gettempdir()
    global e2m3upy, n1
    e2m3u2bouquet = e2m3upy + "e2m3u2bouquetpy2.py"
    n1 = 'e2m3u2bouquetpy2.py'
    if PY3:
        e2m3u2bouquet = e2m3upy + "e2m3u2bouquetpy3.py"
        n1 = 'e2m3u2bouquetpy3.py'
    if not os.path.exists("/etc/enigma2/e2m3u2bouquet"):
        os.system("mkdir /etc/enigma2/e2m3u2bouquet")
    configfile = ("/etc/enigma2/e2m3u2bouquet/config.xml")
    if os.path.exists(configfile):
        os.remove(configfile)
    cmd1 = "cp -rf " + e2m3u2bouquet + " /tmp"
    os.system(cmd1)
    os.system("cd /tmp")
    cmd2 = "chmod -R 777 " + n1
    os.system(cmd2)

    username = str(config.plugins.XCplugin.user.value)
    password = str(config.plugins.XCplugin.passw.value)
    all_bouquet = "0"
    iptv_types = "0"
    if config.plugins.XCplugin.typelist.value == "Multi Live & VOD":
        multi_vod = "1"
    else:
        multi_vod = "0"
    if config.plugins.XCplugin.bouquettop.value and config.plugins.XCplugin.bouquettop.value == "Top":
        bouquet_top = "1"
    else:
        bouquet_top = "0"
    streamtype_tv = config.plugins.XCplugin.live.value
    streamtype_vod = config.plugins.XCplugin.services.value
    if config.plugins.XCplugin.picons.value:
        picons = "1"
    else:
        picons = "0"
    m3u_url = urlinfo.replace("enigma2.php", "get.php")
    epg_url = urlinfo.replace("enigma2.php", "xmltv.php")
    # indent = "      "
    with open(configfile, 'w') as f:

        configtext = '<config>\r\n'
        configtext += '\t<supplier>\r\n'
        configtext += '\t\t<name>' + infoname + '</name>\r\n'
        configtext += '\t\t<enabled>1</enabled>\r\n'
        configtext += '\t\t<m3uurl><![CDATA[' + m3u_url + '&type=m3u_plus&output=ts' + ']]></m3uurl>\r\n'
        configtext += '\t\t<epgurl><![CDATA[' + epg_url + ']]></epgurl>\r\n'
        configtext += '\t\t<username><![CDATA[' + username + ']]></username>\r\n'
        configtext += '\t\t<password><![CDATA[' + password + ']]></password>\r\n'
        configtext += '\t\t<iptvtypes>' + iptv_types + '</iptvtypes>\r\n'
        configtext += '\t\t<streamtypetv>' + streamtype_tv + '</streamtypetv>\r\n'
        configtext += '\t\t<streamtypevod>' + streamtype_vod + '</streamtypevod>\r\n'
        configtext += '\t\t<multivod>' + multi_vod + '</multivod>\r\n'
        configtext += '\t\t<allbouquet>' + all_bouquet + '</allbouquet>\r\n'
        configtext += '\t\t<picons>' + picons + '</picons>\r\n'
        configtext += '\t\t<iconpath>' + Path_Picons + '</iconpath>\r\n'
        configtext += '\t\t<xcludesref>0</xcludesref>\r\n'
        configtext += '\t\t<bouqueturl></bouqueturl>\r\n'
        configtext += '\t\t<bouquetdownload>0</bouquetdownload>\r\n'
        configtext += '\t\t<bouquettop>' + bouquet_top + '</bouquettop>\r\n'
        configtext += '\t</supplier>\r\n'
        configtext += '</config>\r\n'

        f.write(configtext)

    dom = str(STREAMS.playlistname)
    com = ("python /tmp/%s") % n1
    _session.open(Console, _("Conversion %s in progress: ") % dom, ["%s" % com], closeOnSuccess=True)


class M3uPlayMovie(Screen, InfoBarMenu, InfoBarBase, InfoBarSeek, InfoBarNotifications, IPTVInfoBarShowHide):

    def __init__(self, session, name, url):
        Screen.__init__(self, session)
        self.skinName = 'MoviePlayer'
        # title = 'Play'
        self['list'] = MenuList([])
        InfoBarMenu.__init__(self)
        InfoBarNotifications.__init__(self)
        InfoBarBase.__init__(self, steal_current_service=True)
        IPTVInfoBarShowHide.__init__(self)
        self['actions'] = ActionMap(['WizardActions', 'MoviePlayerActions', 'EPGSelectActions', 'MediaPlayerSeekActions', 'ColorActions', 'InfobarShowHideActions', 'InfobarActions'], {
            'leavePlayer': self.cancel,
            'back': self.cancel
        }, -1)
        self.allowPiP = False
        InfoBarSeek.__init__(self, actionmap='MediaPlayerSeekActions')
        self.url = url
        self.name = name
        self.srefOld = self.session.nav.getCurrentlyPlayingServiceReference()
        self.onLayoutFinish.append(self.openTest)

    def openTest(self):
        url = self.url
        # pass
        # eserv = int(config.plugins.XCplugin.live.value)
        # ref = eserv + ':0:1:0:0:0:0:0:0:0:' + url        
        # ref = '4097:0:1:0:0:0:0:0:0:0:' + url
        # sref = eServiceReference(ref)
        sref = eServiceReference(4097, 0, url)
        sref.setName(self.name)
        self.session.nav.stopService()
        self.session.nav.playService(sref)

    def cancel(self):
        if os.path.exists('/tmp/hls.avi'):
            os.remove('/tmp/hls.avi')
        self.session.nav.stopService()
        self.session.nav.playService(self.srefOld)
        self.close()

    def keyLeft(self):
        self['text'].left()

    def keyRight(self):
        self['text'].right()

    def keyNumberGlobal(self, number):
        self['text'].number(number)


def getJsonURL(url):
    # request = urllib2.Request(url)
    request = Request(url)
    request.add_header('User-Agent', 'XC Forever')
    request.add_header('Accept-Encoding', 'gzip')
    response = urlopen(request, timeout=ntimeout)
    # response = checkStr(urlopen(request, timeout=ntimeout))
    gzipped = response.info().get('Content-Encoding') == 'gzip'
    data = ''
    dec_obj = zlib.decompressobj(16 + zlib.MAX_WBITS)
    while True:
        res_data = response.read()
        if not res_data:
            break
        if gzipped:
            """
            data += dec_obj.decompress(res_data)
        else:
            data += res_data
            """
            data += checkStr(dec_obj.decompress(res_data))
        else:
            data += checkStr(res_data)
    return json.loads(data)


# ===================Time is what we want most, but what we use worst===================
#
# Time is the best author. It always writes the perfect ending (Charlie Chaplin)
#
# by Lululla & MMark -thanks my friend PCD and aime_jeux and other friends
# thank's to Linux-Sat-support forum - MasterG
# thanks again to KiddaC for all the tricks we exchanged, and not just the tricks ;)
# -------------------------------------------------------------------------------------
# for convertion bouquet credits
# Thanks to @author: Dave Sully, Doug Mackay
# for use e2m3u2bouquet.e2m3u2bouquet -- Enigma2 IPTV m3u to bouquet parser
# @copyright:  2017 All rights reserved.
# @license:        GNU GENERAL PUBLIC LICENSE version 3
# @deffield
# CONVERT TEAM TO ALL FAVORITES LIST MULTIVOD + EPG
# Open the epgimporter plugin via extension's menu.
# Press the blue button to select the sources.
# Select the entry e2m3uBouquet and press the OK button
# Save it with the green button
# Run a manual import using the yellow button manual.
# Save the input with the green button.
# After a while should you the events imported.
# It takes a while so be patient.
# #######################################
# ===================Skin by Mmark Edition for Xc Plugin Infinity please don't copy o remove this
# send credits to autor   ;)
