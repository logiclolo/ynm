# -*- coding: utf-8 -*-

from fixture import *
from time import sleep as sleep
from YNM.camera.discovery import DRM
from YNM.camera.discovery import wait_to_http_rechable, wait_to_http_unrechable
from textwrap import wrap


@pytest.mark.upgrade
@pytest.mark.reboot
@pytest.mark.slow
def test_firmware_upgrade(cam, configer, configs):

    # Test if camera is able to upgrade firmware

    platform = configs['platform']

    supported_dailybuilds = [
        'hisillicon-standard',
        'hissilicon-speeddome',
        'rossini-standard'
    ]
    if platform not in supported_dailybuilds:
        pytest.skip("We don't have %s daily build right now" % platform)

    c = configer.get('system_info_serialnumber')
    macaddress = c.system.info.serialnumber
    macaddress = ':'.join(wrap(macaddress, 2))

    r = cam.upgrade('http://rd1-ci1.vivotek.tw/~ci/%s/latest.pkg' % platform)
    if r is not None:
        print r.text

    upgrade_success = False
    for i in range(0, 3):
        d = DRM()
        d.refresh()
        if len(d.search(macaddress)) > 0:
            upgrade_success = True
        else:
            sleep(60)

    assert upgrade_success, "Camera (%s) missing after firmware upgrade" % macaddress


@pytest.mark.slow
@pytest.mark.reboot
@pytest.mark.restore
def test_system_restore_all(configs):

    # Test if camera is able to restore and see if we are able to discover it by
    # DRM after system restore

    if 'mac' not in configs:
        pytest.skip("Hardware MAC address is not provided. Skip this test")

    d = DRM()
    d.refresh()
    matches = d.search(configs['mac'])

    assert len(matches) <= 1, "Multiple devices with same MAC address(%s) found.\
           Test Fail" % (configs['mac'])

    match = matches[0]

    camera_configs = {'ip': match['ip'], 'user': 'root', 'passwd': ''}
    configer = Configer(Camera(camera_configs))

    print "Restoring camera"
    configer.set('system_restore=1')
    sleep(5)

    assert wait_to_http_unrechable(match['ip']), "Camera (%s) unable to restore"\
        % match['ip']

    if wait_to_http_rechable(match['ip']):
        # camera comes back again
        camera_config = {'ip': match['ip'], 'user': 'root', 'passwd': ''}
        cam = Camera(camera_config)
        configer = Configer(cam)
        c = configer.get('system')
        if ':'.join(wrap(c.system.info.serialnumber, 2)) == match['mac']:
            # camera with same mac found, test successful
            return

    # camera with same mac not found, try to discover camera again with mac
    # address
    for i in range(0, 3):
        d.refresh()
        matches = d.search(configs['mac'])

        print "%d matches found" % len(matches)

        if len(matches) == 1:
            try:
                camera_config = {'ip': matches[0]['ip'], 'user': 'root',
                                 'passwd': ''}
                cam = Camera(camera_config)
                # camera with same mac found, test successful
                return
            except:
                assert False, "Unable to connect with camera (%s, %s)" % \
                    (matches[0]['ip'], configs['mac'])

        assert len(matches) <= 1, "Multiple devices with same MAC address(%s) \
            after system restore. Test Fail. %s" % (configs['mac'], matches)

    assert False, "Camera(%s) missing after system restore" % (configs['mac'])


@pytest.mark.reboot
@pytest.mark.restore
def test_system_restore_except_network(cam):
    pass


@pytest.mark.reboot
@pytest.mark.restore
def test_system_restore_except_daylight_saving_time(cam):
    pass


@pytest.mark.reboot
@pytest.mark.restore
def test_system_restore_except_focus(cam):
    pass


@pytest.mark.reboot
@pytest.mark.restore
def test_system_restore_except_vadp(cam):
    pass


@pytest.mark.reboot
@pytest.mark.restore
def test_system_restore_except_custom(cam):
    pass


@pytest.mark.slow
@pytest.mark.reboot
def test_system_reboot(cam, configer, configs):

    # Test to reboot camera and see if it is still reachable after reboot

    c = configer.get('system&network')
    mac = c.system.info.serialnumber
    ip = c.network.ipaddress

    configer.set('system_reboot=1')
    sleep(3)

    if wait_to_http_rechable(ip):
        cam = Camera(configs)
        configer = Configer(cam)
        c = configer.get('system')
        if mac == c.system.info.serialnumber:
            # device with same mac and IP address found again
            return

    # device IP may be changed, use DRM to scan if device is working
    d = DRM()
    d.refresh()

    mac_separated = ':'.join(wrap(mac, 2))
    matched = d.search(mac_separated)
    assert len(matched) <= 1, "Multiple devices with same MAC address(%s) after\
        system reboot" % mac_separated
    assert matched, "Device with MAC address(%s) missing after system reboot" % \
        mac_separated
