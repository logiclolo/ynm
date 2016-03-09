# -*- coding: utf-8 -*-

from fixture import *
import time
from YNM.utility.utility import is_grayscale, is_color


def test_system_daylight_saving_time_simple(configer, cam, request):

    # Test enable daylight saving time and switch into timezone which uses
    # daylight saving time

    def fin():
        configer.set("system_timezoneindex=320&system_daylight_enable=0")
        # use NTP server to sync time
        configer.set("system_updateinterval=3600")
        time.sleep(5)

    request.addfinalizer(fin)

    # we uses New York City to run day light saving time
    dst = "system_timezoneindex=-200&system_daylight_enable=1&system_updateinterval=0"

    configer.set(dst)
    time.sleep(5)

    # New York City enters daylight saving time at 2016/03/13 02:00:00
    enters_dst = "system_datetime=031301592016.58"
    configer.set(enters_dst)
    time.sleep(1)

    # get camera time to see if time really configured
    c = configer.get('system')
    hour, _, _ = c.system.time.split(':')
    assert int(hour) == 1, "Camera time doesn't get configured correctly"

    time.sleep(5)

    # Camera should enters DST, get its time to check
    c = configer.get('system')
    hour, _, _ = c.system.time.split(':')

    assert int(hour) == 3, "Camera should enters daylight saving time"


@pytest.mark.slow
def test_system_ircut_schedule_mode(configer, cam, snapshot, request):

    # Test if camera's ircut schedule mode works

    def fin():
        configer.set('ircutcontrol_mode=auto')
        configer.set('ircutcontrol_daymodebegintime=08:00')
    request.addfinalizer(fin)

    def helper_ircut_control_is_day(image):
        return is_color(image)

    def helper_ircut_control_is_night(image):
        return is_grayscale(image)

    caps = cam.capability
    if caps.daynight.c[0].ircutfilter <= 0:
        pytest.skip("This device doesn't support true day/night")

    # get current time
    c = configer.get('system')
    hour, minute, second = c.system.time.split(':')
    year, month, day = c.system.date.split('/')

    minute = int(minute)
    minute += 1
    minute = str(minute)

    expected_minute = minute

    configer.set('ircutcontrol_mode=schedule')
    ircut_schedule = 'ircutcontrol_daymodebegintime=%s:%s' % (hour, minute)
    configer.set(ircut_schedule)
    time.sleep(3)

    success, image = snapshot.take()
    assert success, "Unable to take snapshot successfully"
    assert helper_ircut_control_is_night(image), "IRCut status should be night \
        mode"
    print "IRCut enters NIGHT mode ok"

    schedule_entered = False
    print ""
    for i in range(0, 60):
        c = configer.get('system')
        hour, minute, second = c.system.time.split(':')
        if minute == expected_minute:
            schedule_entered = True
            break
        time.sleep(1)

    assert schedule_entered, "Schedule doesn't match exp: %s, act %s" % \
        (ircut_schedule, c.system.time)

    time.sleep(3)
    success, image = snapshot.take()
    assert success, "Unable to take snapshot successfully"
    assert helper_ircut_control_is_day(image), "IRCut status should be day mode"
    print "IRCut enters DAY mode ok"
