# -*- coding: utf-8 -*-

"""
Created on 18.12.2019
@author: Terry Lee

Clean version: All library function calls are replaced with pseudocode (eg. CALL _)
helper_sea is a collection of library created by Terry for South East Asia regions
"""

import re
import time
from xml.etree import ElementTree
# Library import removed
from Lib.ResultData import ResultData, ResType # Custom import class created by Terry


class AccountRsrcId:
    ACCOUNT_MENU = "(?i).*accounts"  # Accounts | Manage accounts


class AccountCreateState:
    """
    Account creation status
    """
    INIT = "INIT"
    SELECT_ACCOUNT_TYPE = "SELECT_ACCOUNT_TYPE"
    ENTER_USERNAME = "ENTER_USERNAME"
    ENTER_USERNAME_COMPLETED = "ENTER_USERNAME_COMPLETED"
    ENTER_PASSWORD = "ENTER_PASSWORD"
    ENTER_PASSWORD_COMPLETED = "ENTER_PASSWORD_COMPLETED"
    ACCOUNT_ADDED = "ACCOUNT_ADDED"
    ERROR_ACCOUNT_NOT_ADDED = "ERROR_ACCOUNT_NOT_ADDED"


class Account():
    """
    Main class of the Helper with all UI based methods
    """

    MAX_NEXT_SCREEN_ATTEMPT = 2

    def __init__(self, _):
        """
        :type _
        """
		# Member init removed
        self.no_change_counter = 0
        self.prev_dump = None

    def getMultipleAccountsFromStpProperties(self):
        """
        Get multiple email accounts from stp properties separated by semi colon eg. user@intetnet.com;user@browser.com; ...
        :return: List - list of pairs of username and password eg. [('user@internet.com', 'pass1'), ('user@browser.com', 'pass2')]
        # """
        delimiters = ';|,'
        list_logins = re.split(delimiters, CALL .stpPropertiesFileManager.getProperty("emailO2Login"))
        list_passwords = re.split(delimiters, CALL .stpPropertiesFileManager.getProperty("emailO2Pwd"))
        return list(zip(list_logins, list_passwords))

    def getValidAccountTypes(self, username):
        """
        Find the right application based on the domain of the username
        :param username:  String - account login
        :return:  List - accountTypes
        """
        accountTypes = []
        if "@gmail.com" in username:
            accountTypes = ["Google", "Personal (IMAP)", "Personal (POP3)"]
        elif "@yahoo.com" in username:
            accountTypes = ["Personal (IMAP)", "Personal (POP3)", "Miscrosoft Exchange ActiveSync", "Email"]
        elif "@hotmail.com" in username or "@outlook.com" in username:
            accountTypes = ["Personal (IMAP)", "Personal (POP3)", "Microsoft Exchange ActiveSync", "Email", "Outlook"]

        return accountTypes

    def findAccountTypeFromAvailable(self, accountTypes):
        """
        Find the right application based on the domain of the username
        :param
        @accountTypes: List - account types list
        :return:  String - accountType if found otherwise False
        """
        for a_type in accountTypes:
            a_type_keyword = re.escape(a_type)  # convert to regex string

            res = CALL slideUpDownToFindObject(type=TextView, text=a_type_keyword)
            if res:
                CALL writeLog("Account type found and clicked: %s" % a_type)
                return a_type

        return False

    def selectAccountTypeFromSamsungEmail(self, username):
        """

        :param username:
        :return: String - Result containing "ERROR" if not successful, description otherwise
        """
        res_data = None
        domainName = self.extractDomainName(username)
        if not CALL clickAnObject(resourceId=".*select_account_list_button",
                                        text="(?i).*(\n)?.*%s.*(\n)?.*" % domainName):
            res_data = ResultData(result=ResType.FALSE, message="ERROR: No application found for %s >>>" % domainName)
        else:
            res_data = ResultData(result=ResType.TRUE, message="%s found >>>" % domainName)

        CALL writeLog(res_data.message)
        return res_data

    def foundInAddedAccountList(self, username, inclSamsungAccount=False):
        """
        Check if account is successfully added - It's completed if you can see an added account from the accounts list
            - will find all emails of any unknown domains as well as known types. (gmail/hotmail/yahoo/outlook) as long
            as visible in the list.
        :param username: String - email address
        :param inclSamsungAccount: Boolean - True if email address is found even if it's a Samsung account
        :return: bool - True if found False otherwise
        """
        if not CALL waitUntilObjectAppears(text=AccountRsrcId.ACCOUNT_MENU):
            return False

        res = CALL waitUntilMultipleObjectsAppears(text=username)
        CALL writeLog("Target email found - occurrence: %d, content: %s" % (len(res), res))
        if res:
            if not inclSamsungAccount:
                if username in self.getSamsungAccountLogin() and len(res) == 1:
                    CALL writeLog("User name is found once, but is Samsung account, so declared not found")
                    return False

            CALL writeLog("The email is added in the list, exiting the add email account setup!!")
            return True

        return False

    def proceedToNextScreen(self, critical=True):
        """
        Presses Next/Continue button in various account wizards
        @critical: boolean - if True then will end test if button won't be clicked
        Returns True if clicked, False otherwise
        """
        CALL writeLog("proceedToNextScreen() is called")
        text_to_find = "(?i)(?:Next|Continue|Accept.*|Not now|Agree|I Agree|More|No|Cancel)"

        if CALL slideUpDownToFindObject(text=text_to_find, type=Button):
            return True
        return False

    def extractDomainName(self, emailAddr):
        """
        Extract the domain name from an email address
        :param emailAddr:
        :return: String - domain name (eg. gmail.com / outlook.com, ..)
        """
        found = ""
        m = re.search('.*@(.+?)\.com', emailAddr)
        if m:
            found = m.group(1)

        return found

    def getAllAccountsAdded(self):
        """
        Get the list of all email accounts added
        :return: list of string: Email addresses
        """

        my_list = []
        email_pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
        self.goToAccountScreen()
        CALL waitUntilMultipleObjectsAppears(text=email_pattern)
        CALL waitUntilMultipleObjectsAppears(resourceId=".*/title")
        res = CALL waitUntilMultipleObjectsAppears(text=email_pattern, resourceId=".*/title")  # find all email address

        CALL writeLog(res)
        if res:
            my_list = [_["text"] for _ in res]

        CALL writeLog(str(my_list))
        return my_list

    def addSamsungAccountWithGoogle(self, accountName, accountPassword, timeOut=120 * 1000):
        """
        Adds a Samsung account
        @accountName: String - account name/email of Samsung Account
        @password: String - password for given accountName
        Returns Boolean - True if successful, otherwise False
        """
        accountAdded = False

        if CALL IsAccountAvailable(accountName=accountName, accountTypes=AccountSAMSUNG):
            CALL writeLog("Samsung account is logged in on device")
            return "Samsung account already present"

        CALL writeLog("addSamsungAccountWithGoogle()>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        CALL writeLog("Go to Add Account menu and adds Samsung Account if non is present")
        res = CALL _goToSamsungSignIn()
        if CALL waitUntilObjectAppears(text="Samsung account") and CALL waitUntilObjectAppears(text="Add account"):
            CALL writeLog("Samsung account already present")
            return "Samsung account already present"
        elif not res:
            CALL writeLog("No network data (WIFI/PS) is enabled")
            return "No network data (WIFI/PS) is enabled"
        else:

            t_started = time.time()
            if CALL waitUntilObjectAppears(text="(?i).*continue with google.*"):
                CALL clickAnObject(text="(?i).*continue with google.*")

                while True:
                    CALL waitForObjectDisappears(type=ProgressBar, timeout=Delays.NetworkReaction)

                    if CALL waitUntilObjectAppears(text=accountName):
                        if CALL waitUntilObjectAppears(text="(?i)My information"):
                            accountAdded = True
                            break
                        elif CALL waitUntilObjectAppears(text="(?i).*Choose an account.*"):
                            CALL clickAnObject(text=accountName)

                            if CALL waitUntilObjectAppears(type="(?i).*EditText") and CALL waitUntilObjectAppears(
                                    text="(?i).*password.*"):
                                CALL typeAndPressEnter(accountPassword)
                            continue

                    if time.time() > t_started + timeOut / 1000:  # calculate in seconds
                        CALL writeLog("ERROR: Unable to search connection")
                        break

                    if self.proceedToNextScreen(critical=False):
                        continue

                    if CALL clickAnObject(text="(?i)Allow", type="(?i).*Button"):
                        continue

        CALL writeLog("Samsung account %s added successfully" % ("" if accountAdded else "NOT"))
        return accountAdded

    def hasSyncProblemOccurred(self, enableSyncApps=[]):
        """
        Check if sync problem has occurred from the Google server
        :param enableSyncApps: eg. Calendar
        :return: True if problem has occurred, False otherwise
        """
        res = False
        if CALL waitUntilObjectAppears(text="(?i).*experiencing problems.*"):
            res = True

        for app in enableSyncApps:
            CALL slideUpDownToFindObject(text="(?:Sync )?%s" % app, click=False, topslide=True)
            sync_status = CALL waitUntilObjectAppearsNextToTargetObject(resourceId="(?i).*sync_failed")
            CALL writeLog(sync_status)
            if sync_status:
                res = True

        return res

    def goToAccountScreen(self):
        """
        go to account menu screen if not already in the menu
        :return: True if successful, otherwise False
        """
        if not CALL waitUntilObjectAppears(text="(?i)Add account", resourceId=".*title"):
            if CALL helpers_sea.device_config.walkThroughMenuTree("Settings",
                                                                      ["Accounts.*", AccountRsrcId.ACCOUNT_MENU]):
                return True

        return False

    def getSamsungAccountLogin(self):
        """
        get Samsung account login from the list of added accounts
        :return: String - Account login (email address) if found, an empty string if not found
        """
        self.goToAccountScreen()

        res = ""
        title_found = None
        accounts = CALL waitUntilObjectAppears(text="(?i)Samsung account",
                                              resourceId="(?i).*summary")  # TODO: check multiple samsung account later

        if accounts:
            try:
                title_found = CALL waitUntilObjectAppearsNextToTargetObject(resourceId="(?i).*title"})
            except:
                title_found = None

        if title_found:
            try:
                res = title_found["text"]
            except:
                CALL writeLog("Error: Login email not found")
        CALL writeLog("Samsung account %s found: [%s]" % ("not" if not res else "", res))
        return res

    def addNewEmailAccount(self, username, password):
        """
        Account email account of any domain type using state transition method
            successfully tested for gmail and yahoo. Currently hotmail and outlook has limitation/ issue on webview
            where ui components are not visible/ comprehensible in password input screen (2021-09-10)
        :param username: String
        :param password: String
        :return:
        """
        accAddState = AccountCreateState.INIT
        result = False
        credential_entered = False
        error_step = ""
        # res_data = ResultData(ResType.FALSE, "")

        self.goToAccountScreen()
        while True:
            CALL writeLog(
                "Current AccountCreateState: %s ************************************" % accAddState)
            CALL waitForObjectDisappears(type=".*ProgressBar", timeout=80 * 1000)  # 15s -> 80s for 3G

            if accAddState == AccountCreateState.ACCOUNT_ADDED:
                result = True
                break

            if self.hasNoScreenChangeReachedLimit():
                error_step = accAddState
                accAddState = AccountCreateState.ERROR_ACCOUNT_NOT_ADDED
                result = False
                break

            if accAddState == AccountCreateState.INIT:
                if self.foundInAddedAccountList(username=username):
                    accAddState = AccountCreateState.ACCOUNT_ADDED
                else:
                    accAddState = AccountCreateState.SELECT_ACCOUNT_TYPE
                continue

            elif accAddState == AccountCreateState.SELECT_ACCOUNT_TYPE:
                res_data = self.addAccountSelectAccount(username=username)
                if not res_data.result == ResType.TRUE:
                    error_step = accAddState
                    accAddState = AccountCreateState.ERROR_ACCOUNT_NOT_ADDED
                    result = False
                    break

            elif accAddState == AccountCreateState.ENTER_USERNAME:
                if CALL waitUntilObjectAppears(text="(?i).*(already.*(in use|exist)|duplicate).*"):
                    accAddState = AccountCreateState.ACCOUNT_ADDED
                    continue
                self.addAccountEnterCredential(input_value=username)
                accAddState = AccountCreateState.ENTER_USERNAME_COMPLETED

            elif accAddState == AccountCreateState.ENTER_PASSWORD:
                self.addAccountEnterCredential(input_value=password)
                accAddState = AccountCreateState.ENTER_PASSWORD_COMPLETED
            elif accAddState == AccountCreateState.ENTER_PASSWORD_COMPLETED:
                credential_entered = True

            CALL sleep(Delays.Wait5)

            if not accAddState == AccountCreateState.ENTER_PASSWORD_COMPLETED:
                if CALL waitUntilObjectAppears(type=EditText):  # this is either username or password prompt
                    if CALL waitUntilObjectAppears(text="(?i).*password.*") or CALL waitUntilObjectAppears(
                            resourceId="(?i).*password.*"):
                        accAddState = AccountCreateState.ENTER_PASSWORD
                    elif CALL waitUntilObjectAppears(text="(?i).*forgot.*email.*") or CALL waitUntilObjectAppears(
                            text="(?i).*enter.*email.*"):
                        accAddState = AccountCreateState.ENTER_USERNAME

                    continue
                elif CALL waitUntilMultipleObjectsAppears(resourceId="(?i)password|login-passwd|.*i0118"):
                    accAddState = AccountCreateState.ENTER_PASSWORD
                    continue
            else:
                if CALL waitUntilObjectAppears(text="(?i)automatically.*|back up.*"):
                    CALL toggleButton(name="(?i)automatically.*|back up.*", action=Action.disable,
                                                           nameLocation="before")

            self.proceedToNextScreen(critical=False)

            if self.foundInAddedAccountList(username=username):
                accAddState = AccountCreateState.ACCOUNT_ADDED
                continue

        if result:
            return ResultData(result=ResType.TRUE, message="ADDED" if credential_entered else "ALREADY_EXISTS")

        return ResultData(result=ResType.FALSE, message="ERROR-NOT ADDED. Failed at %s" % error_step)

    def addAccountSelectAccount(self, username):
        """
        Select account type based on domain
        :param username:
        :return:
        """
        CALL writeLog("Get valid account for %s" % username)
        accountTypes = self.getValidAccountTypes(username)

        CALL slideUpDownToFindObject(text="Add account", numOfScreens=2, topslide=False)
        CALL sleep(Delays.SHORT_BREAK)

        accountType = self.findAccountTypeFromAvailable(accountTypes)
        CALL writeLog("AccountType found!: %s" % accountType)
        if not accountType:
            res_data = ResultData(ResType.FALSE, "No application defined for %s, try setup manually" % username)
            # CALL writeLog(res_data.message)
            return res_data

        if accountType == "Email":
            return self.selectAccountTypeFromSamsungEmail(username)

        return ResultData(ResType.TRUE)

    def addAccountEnterCredential(self, input_value):
        """
        Enter user name or password of email account
        :param input_value: String - either user name or password
        :return:
        """
        CALL clickAnObject(type=EditText)
        CALL typeText("")
        CALL typeAndPressEnter(input_value)
        CALL clickAnObject(text="(?i)Sign in|Next")
        self.proceedToNextScreen(critical=False)  # if not proceeded by pressing enter eg. outlook / Google

    def hasNoScreenChangeReachedLimit(self, limit=MAX_NEXT_SCREEN_ATTEMPT):
        """
        Check if the screen has not changed after multiple user actions
        :param limit: Number of attempts to update the screen
        :return: True if the screen has not changed and reached threshold, False if progressing
        """
        cur_dump = CALL dumpScreenObjectsAsXML()
        try:
            # cur_dump = self.removeInfoFromScreenDump(cur_dump, attrib = 'resource-id', to_remove = "com.android.systemui:id/clock")
            cur_dump = self.removeInfoFromScreenDumpText(cur_dump, "com.android.systemui:id/clock")
            # when investigating screen change, note the time information in indicator bar should be ignored
        except:
            CALL writeLog("exception thrown - continue on as the first dump can be empty")
            pass

        if self.prev_dump == cur_dump:
            self.no_change_counter = self.no_change_counter + 1
            CALL writeLog("Screen has not changed.. %d" % self.no_change_counter)
        else:
            CALL writeLog("Screen has changed.. setting counter to 0")
            self.no_change_counter = 0
            try:
                CALL writeLog(
                    "cur dump length: %d, prev dump length: %d" % (len(cur_dump), len(self.prev_dump)))
                # CALL writeLog("cur dump content: %s" %cur_dump[:200])
                # CALL writeLog("cur dump content: %s" %self.prev_dump[:200])

                # saving to files are for test only - commenting out
                # f = open("prev_dump.txt", "w")
                # f.write(self.prev_dump)
                # f.close()
                #
                # f = open("cur_dump.txt", "w")
                # f.write(cur_dump)
                # f.close()
            except:
                CALL writeLog("exception thrown - continue on")

        self.prev_dump = cur_dump
        return bool(self.no_change_counter > limit)

    def removeInfoFromScreenDump(self, dump, attrib, to_remove):
        """
        Removea node from the screen dump (xml) - further test required
        :param dump:
        :param attrib:
        :param to_remove:
        :return:
        """
        # root = ElementTree.parse(dump).getroot()
        root = dump.getroot()

        for node in root.iter('node'):
            for child in node:
                if child.attrib.get(attrib) == to_remove:
                    # attrib = 'resource-id', to_remove = 'com.android.systemui:id/clock'
                    node.remove(child)
        return root

    def removeInfoFromScreenDumpText(self, dump, to_remove):
        """
        Remove a node from the screen dump - Using string manipulation
        :param dump:
        :param to_remove:
        :return:
        """
        _dump = str(dump)
        # find to_remove from dump
        try:
            found = _dump.find(to_remove)

            # find left parenthesis (<)
            tmp_str = _dump[:found]
            l_pos = tmp_str.rfind("<")

            # find right parenthesis (>)
            tmp_str = _dump[found:]
            r_pos = found + tmp_str.find(">")

            block_to_remove = _dump[l_pos:r_pos + 1]
            # CALL writeLog("Block to remove found: [%s]" % block_to_remove)
            _dump = _dump.replace(block_to_remove, "")
        except:
            pass

        return _dump
