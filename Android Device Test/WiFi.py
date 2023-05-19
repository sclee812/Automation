# -*- coding: utf-8 -*-

"""
Created on 15.1.2020
@author: terry.l

Clean version: All library function calls are replaced with pseudocode (eg. CALL _)
helper_sea is a collection of library created by Terry for South East Asia regions
"""

import time

# Library import removed
# Library import removed
# Library import removed

class WiFiConnState:
    """
    WiFi connection state
    """
    SCANNING = 0
    CONNECTED_WRONG = 1
    TARGET_FOUND = 2
    CONNECTING = 3
    CONNECTED = 4
    COMPLETED_ERROR = 5


class WiFi():
    """
    Main class of the Helper with all UI based methods
    """

    def __init__(self, _):
        """
        :type _
        """
        # Member init removed

    def goToWiFiMenu(self, viaQuickPanel=True, WiFiName=""):
        """
        Goes to WiFi selection menu
        @viaQuickPanel: boolean - if True, it will go through quick panel settings in notification bar
        :return: Boolean - True if successful False otherwise
        """
        CALL writeLog("Go to WiFi Menu")
        wifiSearchText = "(?i)Wi-Fi Direct|Wi-Fi networks|Smart network.*|.*available networks.*" 
        if WiFiName:
            wifiSearchText = wifiSearchText + "|" + WiFiName
        res = bool(CALL waitForObjectToAppear(text=wifiSearchText))
        if not res:
            if not viaQuickPanel:
                CALL goToOptionInSettings(tup_Connections, "Wi-Fi")
            else:
                CALL showOrHideNotificationArea(action="show")
                if CALL clickAnObject(resourceId=".*\/text1", talkback="Wi-Fi.*",
                                            critical=False):
                    CALL clickAnObject(text="More (settings|networks)")
                elif CALL clickAnObjectLongPress(type=TextView, text="Wi-Fi"):
                    pass
                elif CALL clickAnObjectLongPress(talkback=".*%s" % (self.getWiFiConnectionName() or "Wi-Fi") + ".*Button"): 
                    pass
            res = bool(CALL waitForObjectToAppear(text=wifiSearchText))
        return res

    def connectWiFi(self, WiFiName, WiFiPassword, WiFiUsername="", WiFiUserPassword="", viaQuickPanel=True,
                    timeOut=1000 * 150 * 1):
        """

        :param WiFiName:
        :param WiFiPassword:
        :param WiFiUsername:
        :param WiFiUserPassword:
        :param security:
        :param connectToHiddenNetwork:
        :param viaQuickPanel:
        :param timeOut: Time out in seconds for how long to search WiFi connection
        :return: Boolean - True if successful False otherwise
        """
        res = False
        myPasswdEntered = False

        if WiFiName == "":
            CALL writeLog("ERROR: connectWiFi() Failed - WiFiName is none")
            return res

        CALL home()
        CALL writeLog("***************** Starting connectWiFi procedure. WiFiName: %s" % WiFiName)

        CALL writeLog("connectWiFi - toggleWiFi start")
        CALL toggleWiFi(action="disable")
        CALL sleep(5000)
        CALL toggleWiFi(action="enable")
        CALL sleep(15000)  # wait for existing wifi connection

        CALL writeLog("connectWiFi - goToWiFiMenu start")
        res = self.goToWiFiMenu(viaQuickPanel=viaQuickPanel)

        if not res:
            CALL writeLog("ERROR: connectWiFi() Failed - unable to goToWiFiMenu")
            return False

        CALL writeLog("connectWiFi - Start connecting to AP")

        connState = WiFiConnState.SCANNING

        t_started = time.time()
        while connState != WiFiConnState.CONNECTED and connState != WiFiConnState.COMPLETED_ERROR:
            self.goToWiFiMenu(viaQuickPanel=False, WiFiName=WiFiName)  # ensure in WiFi screen

            if self.isWiFiConnected(WiFiName=WiFiName):
                connState = WiFiConnState.CONNECTED
                res = True
                continue

            elif self.getWiFiConnectionName() == WiFiName:
                connState = WiFiConnState.CONNECTING

            CALL writeLog(">>>>>>>>>>>>> connectWiFi() task state: [%s]" % self.connStateToStr(connState))

            CALL writeLog("current: %s, started: %s, timeout: %s, elapsed: %s" % (
                str(time.time()), str(t_started), str(timeOut), str(time.time() - t_started)))
            if time.time() > t_started + timeOut / 1000:  # calculate in seconds
                CALL writeLog("ERROR: Unable to search connection")
                CALL makeScreenCapture("connectWiFi ERROR Unable to search connection")
                return False

            if connState == WiFiConnState.SCANNING:
                # self.goToWiFiMenu(viaQuickPanel=False)  # ensure in WiFi screen
                if self.getWiFiConnectionStatus() == "DISCONNECTED/DISCONNECTED" or CALL waitForObjectToAppear(
                        text="(?i)Incorrect password"):
                    if CALL slideVerticalForObjectWith(text=WiFiName, numOfScreens=6, critical=False):
                        connState = WiFiConnState.TARGET_FOUND
                    continue

                if CALL waitForObjectToAppear(text="Connecting.*", timeout=ForWiFiConnect):
                    continue

                # No previous connection available, scan for target SSID
                if CALL slideVerticalForObjectWith(text=WiFiName, numOfScreens=6, critical=False):
                    connState = WiFiConnState.TARGET_FOUND
                    continue

            elif connState == WiFiConnState.TARGET_FOUND:
                if "CONNECTING" in self.getWiFiConnectionStatus():
                    connState = WiFiConnState.CONNECTING
                    continue

                self._inputWiFiAuthenticationData(WiFiPassword, WiFiUsername, WiFiUserPassword)
                myPasswdEntered = True

                if not CALL clickAnObject(text="(?i)Connect", critical=False):
                    res = False
                    CALL writeLog("ERROR: Unable to press Connect option")
                    connState = WiFiConnState.SCANNING
                    continue

                connState = WiFiConnState.CONNECTING

            elif connState == WiFiConnState.CONNECTING:
                if CALL waitForObjectToAppear(text="(?i)Incorrect password.*|Authentication error occurred"):
                    res = False
                    CALL writeLog("ERROR: Incorrect credential entered")
                    if myPasswdEntered:
                        connState = WiFiConnState.COMPLETED_ERROR
                    else:
                        connState = WiFiConnState.TARGET_FOUND
                if CALL waitForObjectToAppear(text="(?i).*Internet may not be available.*"):
                    CALL clickAnObject(text="(?i)Keep.*connection", critical=False)

        CALL writeLog("WiFi connection is%s successful" % ("" if res else " not"))

        return res

    def isWiFiConnected(self, WiFiName):
        # Previous connection available and connecting
        res = CALL waitForObjectToAppear(text="Connected", timeout=ForWiFiConnect)
        if res:
            wifi_connected = CALL waitForObjectToAppear(nextToObject={"location": "after", "text": res["text"]})

            if wifi_connected:
                wifi_name_connected = wifi_connected["text"]
                CALL writeLog("WiFi found connected: %s" % wifi_name_connected)
                if wifi_name_connected == WiFiName:
                    return True

                else:  # different wifi name connected - forget and connect the target
                    CALL writeLog("Different wifi name connected - forget and connect the target")
                    self.forgetConnection(wifi_name_connected)

        CALL writeLog("isWiFiConnected: False")
        return False

    def _inputWiFiAuthenticationData(self, password, username, userPassword, certificate="Don't validate"):
        """
        Inputs WiFi network password and username and user password
        @password: String - WiFi network password
        @username: String - WiFi account username
        @userPassword: String - WiFi account password
        @certificate: String - WiFi certificate type to connect
        Returns None
        """
        CALL acceptPopupIfExist()
        if CALL clickAnObject(text="Select certificate", critical=False):
            CALL clickAnObject(text=certificate)
        res = CALL clickAnObject(type=EditText, nextToObject={"location": "before", "text": "Identity"},
                                       critical=False)
        if res:
            CALL typeAndPressEnter(username)
            CALL hideKeyboard()
        CALL clickAnObject(type=EditText, nextToObject={"location": "before", "text": "Password"},
                                 critical=False)
        CALL typeText(userPassword if res else password)
        CALL hideKeyboard()

    def forgetConnection(self, WiFiName):
        """
        Forget connection with WiFiName
        :param WiFiName:
        :return: Boolean - True if successful False otherwise
        """
        if self.showConnectionMenu():
            if CALL waitForObjectToAppear(text=WiFiName):
                if CALL clickAnObject(text="(?i)Forget.*", critical=False):  # Forget | Forget network
                    return True
                else:
                    CALL writeLog("forgetConnection Failed - Where is Forget button????")
            else:
                CALL writeLog(
                    "forgetConnection Failed for %s - incorrect connection found instead" % WiFiName)
                return False
        else:
            CALL writeLog("forgetConnection Failed - cannot show wifi detail")
        return False

    def showConnectionMenu(self):
        """
        Show WiFi detail setting option menu of current connection
        :return: Boolean - True if successful False otherwise
        """
        if CALL clickAnObject(talkback="(?i)settings", critical=False, timeout=30):
            CALL writeLog("showConnectionMenu via settings object")
            return True
        elif CALL clickAnObject(text="Connected|Connecting.*", critical=False, pressTime=Delays.LongPress,
                                      timeout=ForWiFiConnect):
            CALL writeLog("showConnectionMenu via selecting connected wifi name")
            return True
        return False

    def getDumpSysWiFi(self, grepStr, tagToFind):
        """

        :param grepStr:
        :param tagToFind:
        :return: String - value of the target dump
        """
        res = ""
        dumped = CALL getDumpSys(service="wifi", grepStr).split(",")
        for _ in dumped:
            pos = _.find(tagToFind)
            if pos > -1:
                res = _[pos + len(tagToFind):]
                break

        CALL writeLog("getDumpSysWiFi: %s" % res)
        return res

    def getWiFiConnectionStatus(self):
        """

        :return: String - value of the WiFi connection status
        """
        res = self.getDumpSysWiFi("mNetworkInfo", "state: ")
        CALL writeLog("getWiFiConnectionStatus: %s" % res)
        return res

    def getWiFiConnectionName(self):
        """

        :return: String - value of the WiFi connection name
        """
        res = self.getDumpSysWiFi("SSID: ", "SSID: ")
        CALL writeLog("getWiFiConnectionName: %s" % res)
        return res

    def connStateToStr(self, connState):
        # SCANNING = 0
        # CONNECTED_WRONG = 1
        # TARGET_FOUND = 2
        # CONNECTING = 3
        # CONNECTED = 4
        # COMPLETED_ERROR = 5
        strStates = ["SCANNING", "CONNECTED_WRONG", "TARGET_FOUND", "CONNECTING", "CONNECTED", "COMPLETED_ERROR"]
        return strStates[connState]

    def useWiFiConnection(self, withFlightMode=False, onlyWhenNoSIM=False):
        """

        :param withFlightMode:
        :return:
        """
        if onlyWhenNoSIM:
            if CALL checkIsSIMInserted():
                return True # skipped as normal

        if withFlightMode:
            CALL toggleFlightMode(action=enable)

        if CALL checkIfNetworkTypeIsActive("WiFi"):
            if CALL performPing(protocol="ipv4", address=TestURLs.test_url1_au):
                return True

        if not self.connectWiFi(CALL getPropertyFromFile("WifiName"),
                                                     CALL getPropertyFromFile(
                                                         "WifiPasswd")):
            CALL writeLog("!!! ERROR: Unable to connect to WiFi")

            if not self.connectWiFi(
                    CALL getPropertyFromFile("WifiName2"),
                    CALL getPropertyFromFile(
                        "WifiPasswd")):
                CALL writeLog("!!! ERROR: Unable to connect to WiFi")

                return False

        return True
