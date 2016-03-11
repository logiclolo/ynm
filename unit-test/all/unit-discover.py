# -*- coding: utf-8 -*-

import YNM.camera.discovery as d
from fixture import *


def test_discovery_http_ping(configs):
    pingable_ip = configs['ip']
    not_pingable_ip = '172.16.0.0'

    assert d.http_ping(pingable_ip), "Camera %s should be http-pingable" % \
        pingable_ip
    assert d.http_ping(not_pingable_ip) is False, "Camera %s should NOT be\
           http-pingable" % not_pingable_ip


def test_discovery_wait_to_http_rechable(configs):
    pingable_ip = configs['ip']
    not_pingable_ip = '172.16.0.0'

    assert d.http_ping(pingable_ip), "Camera %s should be http-pingable" % \
        pingable_ip
    assert d.http_ping(not_pingable_ip) is False, "Camera %s should NOT be\
           http-pingable" % not_pingable_ip


def test_discovery_wait_to_http_unreachable(configs):
    pingable_ip = configs['ip']
    not_pingable_ip = '172.16.0.0'

    assert d.http_ping(pingable_ip), "Camera %s should be http-pingable" % \
        pingable_ip
    assert d.http_ping(not_pingable_ip) is False, "Camera %s should NOT be\
           http-pingable" % not_pingable_ip
