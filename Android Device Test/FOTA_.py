# -*- coding: utf-8 -*-

"""
Created on 11.9.2019
Updated on 5.10.2020
@author: Terry Lee

Clean version: All library function calls are replaced with pseudocode (eg. CALL _)
helper_sea is a collection of library created by Terry for South East Asia regions
"""

# Library import removed
from datetime import datetime
import re
import json, ast
from Lib.Helpers_SEA.ResultData import *  # customer class created by Terry


class FotaState:
    """
    FOTA state
    """
    WIFI_CONNECTION_ERROR = "WIFI_CONNECTION_ERROR"
    MENU_NOT_FOUND_ERROR = "MENU_NOT_FOUND_ERROR"
    UNKNOWN_ERROR = "UNKOWN ERROR"
    CHECK_UPDATE = "CHECK UPDATE"
    UPDATE_NOT_FOUND = "UPDATE NOT FOUND"
    UPDATE_FOUND = "UPDATE FOUND"
    DOWNLOAD_PAUSED = "DOWNLOAD PAUSED"
    DOWNLOADING = "DOWNLOADING"
    DOWNLOAD_COMPLETED = "DOWNLOAD COMPLETED"
    INSTALL_COMPLETED = "INSTALL COMPLETED"


class FotaKeyword:
    """
    FOTA keyword
    """
    UPDATE_NOT_FOUND = "(?i).*is up to date.*|.*already been installed.*(\s)*.*"
    DOWNLOAD_PAUSED = "(?i).*Download paused.*"
    DOWNLOADING = "(?i).*Downloading update.*"
    ALL = UPDATE_NOT_FOUND + "|" + DOWNLOAD_PAUSED + "|" + DOWNLOADING


class FotaFileName:
    APN = "_apn.json"
    CALL_LOGS = "_call_logs.json"
    SPEED_DIAL = "_speed_dial.json"
    SETTINGS = "_settings.json"


class FOTA():
    """
    Main class of the Helper with all UI based methods
    """

    def __init__(self, _):
        """
        :type _
        """
        # Member init removed
        self.download_time_left = 0
        self.swVerBeforeFota = ""

    def goToFotaMenu(self):
        """
        Go to FOTA menu if not already in the menu
        :return: True if come to FOTA menu, False otherwise
        """
        CALL goHomeScreenByPressingBackKeys()
        if CALL helpers_sea.device_config.walkThroughMenuTree("Settings", ["(?i)Software update.*",
                                                                               "(?i)Download.*(install|update).*"]):

            CALL clickAnObject(text="Continue", type=Button, critical=False)

            CALL waitForObjectToDisappear(type=ProgressBar, timeout=Delays.NetworkReaction)
            if CALL waitForObjectToAppear(text="(?i).*(up to date|Download updates|Update your|ready to install).*"):
                return True

            if CALL waitForObjectToAppear(text="(?i)(Download|Install.*)", type=Button):
                return True

        CALL writeLog("!!! ERROR: goToFotaMenu is failed, check the menu again")
        return False

    def connectWiFiForFota(self):
        """
        Establish WiFi connection before FOTA update
        :return:
        """
        for _ in xrange(2):
            if not CALL checkIfNetworkTypeIsActive("WiFi"):
                if CALL helpers_sea.wifi.connectWiFi(CALL  getProperty("WifiName"),CALL  getProperty("WifiPasswd")):
                    return True
                CALL goHomeScreenByPressingBackKeys()

        CALL writeLog("!!! ERROR: Unable to connect to WiFi")
        return False

    def checkFotaStatus(self, wifi_only=False, install_dummy=True):
        """
        Check the FOTA status
        :return:
        """
        if not self.goToFotaMenu():
            return FotaState.MENU_NOT_FOUND_ERROR

        if CALL waitForObjectToAppear(text="(?i).*Failed to update.*"):
            CALL clickAnObject(text="(?i)OK", type=Button, critical=False)
            self.goToFotaMenu()

        CALL writeLog("checking the FOTA status.. ")

        CALL sleep(2000)
        CALL waitForObjectToDisappear(type=ProgressBar, timeout=Delays.NetworkReaction)

        if CALL waitForObjectToAppear(text="(?i)Download", type=Button):
            sw_ver = str(self.getSwVersionForNextUpdate())
            if (not install_dummy and ".DM" in sw_ver) or (install_dummy and not ".DM" in sw_ver):
                CALL writeLog("Update is NOT found, install_dummy: %s, sw_ver: %s" %(install_dummy, sw_ver))
                return FotaState.UPDATE_NOT_FOUND
            CALL writeLog("Update is found, install_dummy: %s, sw_ver: %s" %(install_dummy, sw_ver))
            return FotaState.UPDATE_FOUND

        if CALL waitForObjectToAppear(text="(?i)Install Now", type=Button):
            return FotaState.DOWNLOAD_COMPLETED

        res = CALL waitForObjectToAppear(text=FotaKeyword.ALL)
        if CALL waitForObjectToAppear(package="(?i).*chrome") or CALL waitForObjectToAppear(package="(?i).*sbrowser"):
            CALL back()
        if res:
            if re.match(FotaKeyword.UPDATE_NOT_FOUND, res["text"]):
                CALL writeLog("No update found")
                return FotaState.UPDATE_NOT_FOUND
            elif re.match(FotaKeyword.DOWNLOAD_PAUSED, res["text"]):
                return FotaState.DOWNLOAD_PAUSED
            elif re.match(FotaKeyword.DOWNLOADING, res["text"]):
                self.download_time_left = self.getDownloadTime()
                return FotaState.DOWNLOADING

        return FotaState.UNKNOWN_ERROR

    def getSwVersionForNextUpdate(self):
        """
        Get the sw version of the next available update
        :return: String - sw version (AP / CSC / CP)
        """
        sw_ver = ""
        if CALL slideUpDownToFindObject(type=TextView, text="Software update information",
                                               critical=False, startY=0.5, stopY=0.2,
                                               numOfScreens=10):
            try:
                res = CALL slideUpDownToFindObject(text="(?i).*Version:.*",
                                                          critical=False, startY=0.5, stopY=0.2,
                                                          numOfScreens=10)
                sw_ver = res["text"]
            except:
                CALL writeLog("!!! ERROR: retrieving software information failed")

        CALL writeLog("SW VER FOUND: %s" %sw_ver)
        return sw_ver

    def getFotaInformation(self):
        """
        Get FOTA information eg s/w version, binary size etc
        :return:
        """
        CALL writeLog("getFotaInformation from FOTA screen")
        self.takeFotaScreenshotTopToBottom("BEFORE_DOWNLOAD")

        if CALL slideUpDownToFindObject(type=TextView, text="Software update information",
                                               critical=False, startY=0.5, stopY=0.2,
                                               numOfScreens=10):
            info_text = ""
            try:
                res = CALL slideUpDownToFindObject(text=".*Version:.*",
                                                          critical=False, startY=0.5, stopY=0.2,
                                                          numOfScreens=10)
                info_text = res["text"]
                res = CALL slideUpDownToFindObject(text=".*Size:.*",
                                                          critical=False, startY=0.5, stopY=0.2,
                                                          numOfScreens=10)
                info_text = info_text + ", " + res["text"]
                res = CALL slideUpDownToFindObject(text=".*Security patch level:.*",
                                                          critical=False, startY=0.5, stopY=0.2,
                                                          numOfScreens=10)
                info_text = info_text + ", " + res["text"]
            except:
                CALL writeLog("!!! ERROR: retrieving software information failed")

            CALL writeLog("BINARY INFO: %s" % info_text)

    def getCurrentSwDetailFromDevice(self, reset=False, isDummy=False):
        """
        Get the detail of the current s/w in the device - take screenshots of IMEISV, SWVER, Settings - About,
        Update FOTA summary file
        :return:
        """
        for _ in xrange(2):
            try:
                CALL helpers.calls.goPhoneAndInputNumber(key_str_imei, viaADB=True)
                self.takeFotaScreenshot("DBGSCR_IMEI_SV")
                break
            except:
                CALL writeLog("!! Error occurred (key_str_imei): Trying again..")
            finally:
                CALL clickAnObject(text="OK", critical=False)
                CALL goHomeScreenByPressingBackKeys()

        for _ in xrange(2):
            try:
                CALL helpers.calls.goPhoneAndInputNumber(key_str_swver, viaADB=True)
                self.takeFotaScreenshot("DBGSCR_SWVER")
                break
            except:
                CALL writeLog("!! Error occurred (key_str_swver): Trying again..")
            finally:
                CALL goHomeScreenByPressingBackKeys()

        for _ in xrange(2):
            if CALL helpers_sea.device_config.walkThroughMenuTree("Settings", ["(?i)About (phone|tablet).*",
                                                                                   "(?i)Software information.*"]):
                self.takeFotaScreenshotTopToBottom("ABOUT_PHONE")
                break
            else:
                CALL goHomeScreenByPressingBackKeys()

        if not CALL checkIfNetworkTypeIsActive("WiFi"):
            for _ in xrange(2):
                if CALL helpers_sea.device_config.walkThroughMenuTree("Settings", ["(?i).*Connections.*",
                                                                                       "(?i).*Data usage.*"]):
                    self.takeFotaScreenshot("DATA_USAGE")
                    break
                else:
                    CALL goHomeScreenByPressingBackKeys()

        self.updateFotaSummaryFile(reset=reset, isDummy=isDummy)
        return True

    def downloadUpdate(self):
        """
        Download the update
        :param wifi_only: Download the update under WiFi connection only
        :return:
        """

        if not self.goToFotaMenu():
            CALL writeLog("!!! ERROR: Unable to go to Software update menu")
            # return FotaState.UNKNOWN_ERROR
            return FotaState.MENU_NOT_FOUND_ERROR

        CALL sleep(3000)

        if not CALL waitForObjectToAppear(text="(?i)Download", type=Button):
            CALL writeLog("!!! ERROR: Nothing to download")
            return FotaState.UPDATE_NOT_FOUND

        for _ in range(2):  # try download one more time, in case first attempt is failed
            # if new update is available, or existing download was paused
            if not CALL clickAnObject(text="(?i)Download", type=Button, critical=False):
                continue

            if CALL waitForObjectToAppear(text=FotaKeyword.DOWNLOADING):
                self.download_time_left = self.getDownloadTime()
                return FotaState.DOWNLOADING

            if CALL waitForObjectToAppear(text="[((?i)unable to update.*)((?i).*error occurred.*)]"):
                CALL clickAnObject(text="(?i).*OK.*", critical=False)

            if CALL waitForObjectToAppear(text="(?i).*could\'t download.*"):
                CALL clickAnObject(text="(?i).*OK.*", critical=False)

            self.goToFotaMenu()

        return self.checkFotaStatus()  # if seems like an error, check the status again

    def getDownloadTime(self):
        """
        Get the remaining download time if downloading is in progress
        :return: Time in milli-second if downloading is in progress, otherwise False
        """
        # if not CALL waitForObjectToAppear(text="(?i).*Downloading update.*"):
        if not CALL slideUpDownToFindObject(text=FotaKeyword.DOWNLOADING, critical=False):
            return False

        res = CALL waitForObjectToAppear(text="Time left:.*")
        try:
            info_text = res["text"]
            CALL writeLog("Downloading now.. [%s]" % info_text)
            info_text = info_text.replace('Time left: ', '')
            l = info_text.split(':')
            time_left = (int(l[0]) * 60 * 60 + int(l[1]) * 60 + int(l[2])) * 1000  # in milli-second
            return time_left
        except:
            CALL writeLog("Remaining download time not found")
            return False

    def installUpdate(self):
        """
        Install downloaded update
        :return:
        """
        CALL writeLog(">>>>>>>>>>>>>>>>>>>>>>>>>>> FOTA Installation starts.. >>>>>>>>>>>>>>>>>>>>>>>>>>>")
        self.takeFotaScreenshotTopToBottom("BEFORE_INSTALL")

        CALL clickAnObject(type=Button, text="(?i).*Install now.*")
        CALL writeLog("Device will be rebooted automatically during the installation")
        CALL sleep(5 * 60 * 1000)  # device will be rebooted during this sleep time

        CALL waitForDevice(timeout=Delays.Reboot * 5)  # 5min x 5

        critical = "PIN" in CALL runAdbGetPropCommand("gsm.sim.state",
                                                        getFromAllSIMS=True)  # clicks are only critical if sim card is pin locked
        if critical:
            CALL unlockPIN()
        CALL home()  # MTP Pop-up handling
        CALL writeLog("<<<<<<<<<<<<<<<<<<<<<<<<<< FOTA Installation completed.. <<<<<<<<<<<<<<<<<<<<<<<<<<")
        CALL sleep(10 * 1000)
        if CALL waitForObjectToAppear(text="(?i).*has been updated.*"):
            CALL writeLog("Installation successful!")
            return True

        return False

    def performFotaDownloadTest(self, wifi_only=True, install_dummy=True, multiple_updates=False):
        """
        Perform FOTA download, starting with checking if update is available, complete installation after downloading the update
        :param wifi_only: Download the update under WiFi connection only
        :return: ResultData (ResType, ResMsg) :
            ResType.TRUE | FALSE | ERROR - TRUE if FOTA update is successful, FALSE if not successful, ERROR for unexpected error
            ResMsg: String - addition information or message to be notified to user
        """
        if wifi_only:
            if not CALL helpers_sea.fota.connectWiFiForFota():
                return ResultData(ResType.FALSE, FotaState.WIFI_CONNECTION_ERROR)

        num_install_completed = 0
        self.swVerBeforeFota = CALL helpers_sea.device_config.getSwVersion()

        res = self.checkFotaStatus(wifi_only=wifi_only, install_dummy=install_dummy)
        if res == FotaState.UPDATE_NOT_FOUND:
            CALL writeLog("No update found")
            return ResultData(ResType.FALSE, str(num_install_completed))
        elif "ERROR" in res:
            return ResultData(ResType.ERROR, res)

        if wifi_only:
            if not self.connectWiFiForFota():
                return ResultData(ResType.ERROR, FotaState.WIFI_CONNECTION_ERROR)

        res = FotaState.CHECK_UPDATE
        self.getCurrentSwDetailFromDevice(reset=True, isDummy=install_dummy)

        while "ERROR" not in res and res != FotaState.UPDATE_NOT_FOUND:
            CALL writeLog("Current state: %s" % str(res))

            if res == FotaState.UPDATE_FOUND or res == FotaState.DOWNLOAD_PAUSED:
                if res == FotaState.UPDATE_FOUND:
                    self.getFotaInformation()
                res = self.downloadUpdate()
                continue

            while res == FotaState.DOWNLOADING:
                try:
                    CALL writeLog("Download time left: %s seconds" % int(self.download_time_left / 1000))
                except:
                    CALL writeLog("Could not get download time..")

                CALL writeLog("downloadUpdate result: %s" % str(res))

                # if downloading is halted and a prompt is preventing from downloading further. Should click Continue
                remaining = self.download_time_left
                check_interval = 20*1000
                while remaining >= 0:
                    CALL sleep(check_interval)
                    CALL clickAnObject(text="Continue", type=Button, critical=False, timeout=Delays.Wait2)
                    remaining = remaining - check_interval
                    CALL writeLog("Remaining download time: %d" %remaining)

                # check if more time left
                more_left = self.getDownloadTime()
                CALL writeLog("more time left: %d" %more_left)
                CALL sleep(more_left)

                res = self.checkFotaStatus(wifi_only=wifi_only, install_dummy=install_dummy)

            CALL writeLog("Current state: %s" % str(res))
            if res == FotaState.DOWNLOAD_COMPLETED:
                CALL writeLog("Number of installed updates so far: %d, multiple updates: %s" % (
                    num_install_completed, multiple_updates))
                self.installUpdate()
                self.getCurrentSwDetailFromDevice(isDummy=install_dummy)
                num_install_completed = num_install_completed + 1

                if not multiple_updates:
                    break

            # res = self.checkFotaStatus(wifi_only=wifi_only, install_dummy=install_dummy)
            for _ in xrange(2):
                res = self.checkFotaStatus(wifi_only=wifi_only, install_dummy=install_dummy)
                if res != FotaState.UNKNOWN_ERROR:
                    break
                CALL back()

        if num_install_completed == 0 and "ERROR" in res:
            return ResultData(ResType.ERROR, res)

        if CALL helpers_sea.device_config.getSwVersion() == self.swVerBeforeFota:
            return ResultData(ResType.ERROR,
                              "FOTA not completed - SW version has not changed: %s" % self.swVerBeforeFota)

        CALL writeLog("Total installation completed: %d" % num_install_completed)
        return ResultData(ResType.TRUE, str(num_install_completed))

    def takeFotaScreenshot(self, file_name):
        """
        Take the screenshot of the current screen
        :param file_name: String
        :return: None
        """
        CALL sleep(3 * 1000)
        f_name = "FOTA_" + CALL deviceId + "_" + datetime.today().strftime('%Y%m%d_%H%M%S') + "_" + file_name
        CALL helpers_sea.device_config.captureCurrentScreenInfo(screenshot=f_name)

    def takeFotaScreenshotTopToBottom(self, file_name):
        """
        Take the screenshots from top of the screen and scroll down to bottom
        :param file_name: String
        :return: None
        """
        f_name = "FOTA_" + CALL deviceId + "_" + datetime.today().strftime('%Y%m%d_%H%M%S') + "_" + file_name
        CALL helpers_sea.device_config.takeScreenShotsTopToBottom(file_name=f_name)

    def getFotaFileName(self, file_name, with_swver=False):
        """
        Create a file name for storing FOTA information
        :param file_name:
        :return:
        """
        sw_info = ""
        model = str(CALL runAdbGetPropCommand(propName="ro.product.model")).split("-")[1]
        if with_swver:
            apver = str(CALL runAdbGetPropCommand(propName="ro.build.PDA"))[-4:]
            cpver = str(CALL runAdbGetPropCommand(propName="ril.sw_ver"))[-4:]
            cscver = str(CALL runAdbGetPropCommand(propName="ril.official_cscver"))[-4:]  # or ro.omc.build.version
            sw_info = "_" + "_".join([apver, cpver, cscver])

        res = "FOTA_%s_%s%s%s" %(model, CALL deviceId[-4:], sw_info, file_name)
        CALL writeLog(res)

        return res

    def updateFotaSummaryFile(self, reset=False, isDummy=False):
        """
        Update FOTA summary in a file (json) - first load file into memory, then update data and overwrite to file
        The contents of summary is a list of software detail - version, IMEI SVN, Android patch level and OS
        :return:
        """
        dict_current = CALL helpers_sea.device_config.getSwDetailViaADB()

        f_name = "FOTA_" + CALL deviceId + "_summary%s.json" % ("_dummy" if isDummy else "")

        CALL writeLog("file name: %s" % f_name)
        l_data = []
        if not reset:
            l_data = CALL helpers_sea.device_config.loadDeviceSettingFromFile(
                file_name=f_name)  # if no file, then will be an empty list []
        l_data.append(dict_current)
        if not CALL helpers_sea.device_config.saveDeviceSettingToFile(l_data=l_data,
                                                                          file_name=f_name):  # overwrite file
            CALL writeLog("Update FOTA summary failed - current s/w: %s" % str(dict_current))
            return False

        CALL writeLog("Update FOTA summary completed")
        return True

    def checkImeiFromFotaSummary(self, dummy = False):
        """
        Check if the IMEI SVN is correctly incremented for normal MR.
        Approved s/w (before FOTA) info is saved in FOTA_summmary.json
        :return: (bool, String) -
            True if IMEI SVN is correct, False otherwise.
            Message string value for information such as error message
        """

        msg = ""
        f_name = "FOTA_" + CALL deviceId + "_summary%s.json" % "_dummy" if dummy else ""
        l_data = CALL helpers_sea.device_config.loadDeviceSettingFromFile(file_name=f_name)
        CALL writeLog(str(l_data))
        if not l_data:
            return False, "SKIP: No FOTA summary found"

        target_sw = ""
        target_sw_full = ""
        target_imei = 0
        for item in l_data:
            if ".DM" in item["SW version"]:
                continue

            CALL writeLog("item: %s" % str(item))
            cur_sw = "_".join([i[-4:] for i in item["SW version"].split('/')])
            # change the format of sw version (eg "N950FXXSDDTJ6/N950FXXSDDTJ1/N950FOLNDDTI3" -> "DTJ6_DTJ1_DTI3")
            # because SMR (XXS) is always smaller than NMR (XXU)

            if target_sw == "" or target_sw < cur_sw:
                target_sw = cur_sw
                target_sw_full = item["SW version"]
                target_imei = int(item["IMEI SV"])
        if target_imei == 0:
            return False, "SKIP: No IMEI SVN found for this device"

        prev_sw = ""
        prev_sw_full = ""
        prev_imei = 0
        for item in l_data:
            if ".DM" in item["SW version"]:
                continue

            CALL writeLog("item: %s" % str(item))
            cur_sw = "_".join([i[-4:] for i in item["SW version"].split('/')])

            if prev_sw == "" or (prev_sw < cur_sw and cur_sw < target_sw):
                prev_sw = cur_sw
                prev_sw_full = item["SW version"]
                prev_imei = int(item["IMEI SV"])

        CALL writeLog("target s/w: %s, imei: %d" % (target_sw_full, target_imei))
        CALL writeLog("prev s/w: %s, imei: %d" % (prev_sw_full, prev_imei))

        if target_sw_full == prev_sw_full:
            return True, "Same s/w versions after FOTA (eg. dummy)"

        isPureSMR = False
        model = str(CALL runAdbGetPropCommand(propName="ro.product.model")).split("-")[1]
        CALL writeLog(
            "model: %s, target_sw: %s, smr idicator: %s" % (model, target_sw_full, target_sw.replace(model, "")[:2]))

        if target_sw_full.replace(model, "")[2] == 'S':
            isPureSMR = True

        msg = "Is pure SMR: %s, IMEI SV: %d -> %d" % (str(isPureSMR), prev_imei, target_imei)
        if isPureSMR:
            CALL writeLog("The s/w is pure SMR - IMEI should not be incremented")
            return (target_imei == prev_imei), msg

        CALL writeLog("The s/w is normal MR - IMEI should be incremented")
        return (target_imei > prev_imei), msg
