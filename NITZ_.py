# -*- coding: utf-8 -*-

"""
Created on 19.11.2020
@author: terry.l

Clean version: All library function calls are replaced with pseudocode (eg. CALL _)
helper_sea is a collection of library created by Terry for South East Asia regions
"""

import time
from datetime import datetime

from Lib.Helpers_SEA.ResultData import *
# Library import removed


class NITZ():
    NITZ_AUTO_OPTION_NAME = "(?i).*Automatic date.*time"
    # new devices have seperate menu outside of Automatic data and time menu
    NITZ_AUTO_TIME_ZONE = "(?i).*Automatic time.*zone"

    def __init__(self, _):
        """
        :type _
        """
        # Member init removed

    def goToDateAndTimeSetMenu(self):
        """
        Go to date and time menu if not already in the menu
        :return: Bool - True if successfully entered the menu, otherwise False
        """
        for _ in xrange(2):
            if self.isInDateAndTimeSetMenu():
                return True

            CALL helpers_sea.device_config.goBackHome()
            if not CALL helpers_sea.device_config.walkThroughMenuTree("Settings", ["(?i)General.*management",
                                                                                       "(?i)Date.*time"]):
                CALL writeLog("!!!ERROR - Unable to find menu - Date and time")

        return False

    def isInDateAndTimeSetMenu(self):
        """
        Check if currently in the date and time menu
        :return: Bool - True if in the menu, otherwise False
        """
        if CALL waitForObjectToAppear(text=self.NITZ_AUTO_OPTION_NAME):
            return True

        return False

    def toggleNITZ(self, action=Action.enable):
        """
        Toggle automatic date and time option
        :param action: String - "enable" / "disable"
        :return: Bool - True if successfully toggled, otherwise False
        """
        if not self.goToDateAndTimeSetMenu():
            return False
        if CALL waitForObjectToAppear(text=self.NITZ_AUTO_TIME_ZONE):
            self.toggleTimeZone(action=action)

        res = CALL toggleButton(name=self.NITZ_AUTO_OPTION_NAME, action=action)

        return bool(res)

    def toggleTimeZone(self, action=Action.enable):
        """
        Toggle automatic Time zone
        :param action: String - "enable" / "disable"
        :return: Bool - True if successfully toggled, otherwise False
        """
        if not self.goToDateAndTimeSetMenu():
            return False
        res = CALL toggleButton(name=self.NITZ_AUTO_TIME_ZONE, action=action)

        return bool(res)

    def changeTimeZone(self):
        """
        Change time zone to a random from the list
        :return: Bool - True if successfully changed, otherwise False
        """
        if not self.goToDateAndTimeSetMenu():
            return False

        if CALL clickAnObject(text="(?i).*Select.*time.zone", critical=False):
            CALL clickAnObject(text="(?i).*Region", critical=False)  # Android 7 don't have this

            tz_name = CALL helpers_sea.device_config.selectRandomItemFromListInCurrentScreen()  # can be country or city
            if CALL slideVerticalForObjectWith(text=tz_name):
                return True

        CALL writeLog("!!!ERROR - Unable to change time zone")
        return False

    def isAutomaticDateAndTimeOn(self):
        """
        Check if automatic date and time is enabled
        :return: Bool - True if enabled, otherwise False
        """
        if not self.goToDateAndTimeSetMenu():
            return False

        res = CALL helpers_sea.device_config.getCheckableObjectStatus(name=self.NITZ_AUTO_OPTION_NAME)
        if res == "true":
            return True
        return False

    def changeDate(self, date_yyyymmdd="20200101"):
        """
        Change the current date manually
        :param date_yyyymmdd: String - target date in format of YYYYMMDD
        :return: Bool - True if changed, otherwise False
        """
        if not self.goToDateAndTimeSetMenu():
            return False

        CALL clickAnObject(text="Set date")

        tgt_yyyymm = date_yyyymmdd[:-2]
        cur_yyyymm = ""  # init - unknown

        while cur_yyyymm != tgt_yyyymm:
            CALL writeLog("target: %s, current: %s" % (tgt_yyyymm, cur_yyyymm))
            # res = CALL waitForObjectToAppear(resourceId=com.android.settings:id/sesl_date_picker_calendar_header")
            # res = CALL waitForObjectToAppear(resourceId="android:id/sem_datepicker_calendar_header")
            res = CALL waitForObjectToAppear(resourceId="(?i).*date.*picker.*calendar_header.*", type=TextView)
            if not res:
                CALL writeLog("!!!ERROR - Unable to change date: datepicker object not found")
                return False

            cur_month_title = res["text"]
            cur_yyyymm = self.monthYearTitleToYYYYMM(month_year_title=cur_month_title)
            CALL writeLog("Current month year title: %s -> %s" % (cur_month_title, cur_yyyymm))

            move_to = ""
            if tgt_yyyymm < cur_yyyymm:
                move_to = ".*prev_button"
            elif tgt_yyyymm > cur_yyyymm:
                move_to = ".*next_button"

            CALL writeLog("moving direction is: %s" % move_to)
            if move_to:
                CALL clickAnObject(resourceId=move_to)

        try:
            s_date = ".* %d .*" % int(date_yyyymmdd[-2:])
            CALL clickAnObject(talkback=s_date)
        except:
            CALL writeLog("!!!ERROR - Unable to select date: %s, check if the date is valid" % date_yyyymmdd)
            return False

        CALL sleep(5 * 1000)
        CALL clickAnObject(text="Done", type=Button)
        return True

    def changeTime(self, time_hhmmss):
        """
        Change the current time manually
        :param time_hhmmss: target time in the format of hhmmss
        :return: Bool - True if changed, otherwise False
        """
        if not self.goToDateAndTimeSetMenu():
            return False

        try:
            CALL writeLog("target time: %s" % time_hhmmss)
            CALL clickAnObject(text="Set time")
            CALL clickAnObject(type=EditText)
            if not CALL clickAnObject(type=EditText, text="(?i).*Hour.*", critical=False):
                CALL clickAnObject(type=EditText, last=False)
            hour = int(time_hhmmss[:2])
            if CALL waitForObjectToAppear(text="(?i).*(pm|am).*"):
                if hour > 12:
                    hour = hour - 12
                    CALL clickAnObject(text="(?i).*pm.*", type=TextView + "|" + Button)
                else:
                    CALL clickAnObject(text="(?i).*am.*", type=TextView + "|" + Button)

            CALL typeText(str(hour))
            if not CALL clickAnObject(type=EditText, text="(?i).*Minute.*", critical=False):
                CALL clickAnObject(type=EditText, last=True)
            CALL typeText(time_hhmmss[2:4])
            CALL clickAnObject(text="Done", type=Button)
        except:
            return False

        cur_time = self.getTimeFromDevice(backToAuto=False).replace(":", "")
        CALL writeLog("Current time after change: %s, expected: %s" %(cur_time, time_hhmmss[0:4]))
        if cur_time == time_hhmmss[0:4]:
            return True

        return False

    def changeDateToRandom(self):
        """
        Change the current date to a random date
        :return: Bool - True is successfully selected an item, False otherwise
        """
        if not self.goToDateAndTimeSetMenu():
            return False

        CALL clickAnObject(text="Set date", critical=False)
        try:
            selected = CALL helpers_sea.device_config.selectRandomDateFromDatePicker()
        except:
            selected = False

        return selected

    def monthYearTitleToYYYYMM(self, month_year_title):
        """
        Convert month year from the calendar title to date format of YYYYMM
        :param month_year_title: String - target date to be converted. (eg. NOVEMBER 2020)
        :return: String - date in the format of YYYYMM (eg. 202011)
        """
        tmp_val = month_year_title.split(" ")

        month_name = {"JANUARY": "01", "FEBRUARY": "02", "MARCH": "03", "APRIL": "04", "MAY": "05", "JUNE": "06",
                      "JULY": "07", "AUGUST": "08", "SEPTEMBER": "09", "OCTOBER": "10", "NOVEMBER": "11",
                      "DECEMBER": "12"}
        res = tmp_val[1] + month_name[tmp_val[0].upper()]
        return res

    def getDateOf(self, order, day, ofMonth, inYear):
        """
        Find the date of the particular day of the week occurring at certain order in given specific month/year
            eg. day light saving time starts in every first Sunday of October every year - what's the date for year 2021?
            order=1 (first), day=6 (sunday), month=10 (oct), year=2021
        :param order: Integer - order of occurrence
        :param day: Integer - day of the week (Monday == 0 ... Sunday == 6)
        :param ofMonth: Integer - Target month
        :param inYear: Integer - Target year
        :return: String - date represented by the given condition in YYYYMMDD format
        """
        i = 1
        cur_order = 0
        d_s = ""

        while (1):
            try:
                d = datetime(inYear, ofMonth, i)
                d_s = d.strftime("%Y%m%d")
                # print("current date: %s (%d)" % (d_s, d.weekday()))

                if d.weekday() == day:
                    cur_order = cur_order + 1
                    # print("weekday found: %d at %s with order: %d" %(day, d_s, cur_order))
                    if cur_order == order:
                        CALL writeLog(
                            "Match found !!!! [order: %d, day: %d, ofMonth: %d, inYear: %d] -> [%s]" % (
                                order, day, ofMonth, inYear, d_s))
                        break
                i = i + 1
            except:
                break

        return d_s

    def getNitzInfoFromDevice(self, title, backToAuto=False):
        """
        Read the current set value for the NITZ
        :param title: String - title of the field (eg. timezone, date or time)
        :param backToAuto: Bool - set it back to Auto if set to True, leave it disabled if set to False
        :return: Bool - True if successully read, otherwise False
        """
        self.toggleNITZ(action=Action.disable)
        try:
            res = CALL helpers_sea.device_config.readValueFromMenu(app_name="Settings",
                                                                       menu_tree=["General management",
                                                                                  "Date and time"],
                                                                       field_name=title)
        except:
            res = ""

        if backToAuto:
            self.toggleNITZ(action=Action.enable)
        return res

    def getTimeZoneOffsetFromDevice(self, backToAuto=False):
        """
        Get time zone offset from device
        :return: String - time zone offset
        """
        tz_str = self.getNitzInfoFromDevice(title="(?i)Select.*time.*zone", backToAuto=backToAuto)
        # eg. GMT+10:30 Australian Central Daylight Savings Time
        tz_str = tz_str.split(" ")[0].replace("GMT", "")  # eg. "+10:30"
        l = tz_str.split(":")
        return str(int(l[0]) + int(l[1]) / 60)  # eg. 10.5

    def getDateFromDevice(self, backToAuto=False):
        """
        Get the date from device
        :return: String - date in YYYY-MM-DD format
        """
        date_str = self.getNitzInfoFromDevice(title="(?i)Set.*date", backToAuto=backToAuto)
        date_time_obj = datetime.strptime(date_str, "%d %B %Y")
        return str(date_time_obj.date())

    def getTimeFromDevice(self, backToAuto=False):
        """
        Get the time from device
        :return: String - time in hh:mm format
        """
        time_str = self.getNitzInfoFromDevice(title="(?i)Set.*time", backToAuto=backToAuto)
        date_time_obj = None
        for _ in xrange(2):
            if date_time_obj != None:
                break

            time_format = "%I:%M %p" if _ == 0 else "%H:%M"
            try:
                date_time_obj = datetime.strptime(time_str, time_format)
            except:
                CALL writeLog("Exception handled - time data does not match format %s" %time_format)

        if not date_time_obj:
            return "Error reading time info"
        return str(date_time_obj.time().strftime("%H:%M"))

    def getTimeZoneOffsetFromPC(self):
        """
        Get current time zone offset from PC
        :return: String - time zone offset
        """
        offset = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
        offset = offset / 60 / 60 * -1
        return str(offset)

    def getDateFromPC(self):
        """
        Get current date from PC
        :return: String - current date in YYYY-MM-DD format
        """
        return str(datetime.now().date())

    def getTimeFromPC(self):
        """
        Get current time from PC
        :return: String - current time in hh:mm format
        """
        return str(datetime.now().time().strftime("%H:%M"))

    def compareNitzInfoBetweenDeviceAndPC(self):
        """
        Compare the date in the device and the date from the PC to check if device date is correct
        :return: Bool - True if they are within acceptable difference, False if they are different
        """
        tz_device = self.getTimeZoneOffsetFromDevice(backToAuto=False)
        date_device = self.getDateFromDevice(backToAuto=False)
        time_device = self.getTimeFromDevice(backToAuto=False)
        CALL writeLog("** DEVICE TIME INFO - time zone offset: %s, date: %s, time: %s"
                                 % (str(tz_device), str(date_device), str(time_device)))
        tz_pc = self.getTimeZoneOffsetFromPC()
        date_pc = self.getDateFromPC()
        time_pc = self.getTimeFromPC()
        CALL writeLog("** PC TIME INFO - time zone offset: %s, date: %s, time: %s"
                                 % (str(tz_pc), str(date_pc), str(time_pc)))

        if tz_device != tz_pc:
            CALL writeLog("time zone are different")
            return False

        if not self.compareDate(date1=date_device, date2=date_pc):
            CALL writeLog("dates are different")
            return False

        if not self.compareTime(time1=time_device, time2=time_pc):
            CALL writeLog("time are different")
            return False

        return True

    def compareDate(self, date1, date2):
        """
        Compare two dates to see if they are same or within reasonable boundaries
        :param date1:
        :param date2:
        :return: True if same, otherwise False
        """
        date_obj1 = datetime.strptime(date1, "%Y-%m-%d")
        date_obj2 = datetime.strptime(date2, "%Y-%m-%d")
        delta = date_obj1 - date_obj2
        if abs(delta.days) <= 1:
            return True

        return False

    def compareTime(self, time1, time2):
        """
        Compare two time values to see if they are same or within reasonable boundaries
        :param time1:
        :param time2:
        :return: True if same, otherwise False
        """
        date_obj1 = datetime.strptime(time1, "%H:%M")
        date_obj2 = datetime.strptime(time2, "%H:%M")
        delta = date_obj1 - date_obj2
        if abs(delta.days) <= 1:
            return True

        return False
