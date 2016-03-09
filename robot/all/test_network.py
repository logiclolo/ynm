# -*- coding: utf-8 -*-

from fixture import *
import requests
import time


@pytest.mark.skipif(True, reason="I can't nail down SSLv3 issue....")
def test_network_https_self_signed_certificate(configer, cam):

    # Test if HTTPS works by self-signed certificate

    # create self-signed certificate

    certificate = "https_method=manual&https_countryname=TW&\
        https_stateorprovincename=Asia&\
        https_localityname=Asia&https_organizationname=VIVOTEK+Inc.&\
        https_unit=VIVOTEK+Inc.&https_commonname=www.vivotek.com&\
        https_validdays=3650&https_status=-3"

    configer.set(certificate)

    publickey_found = False
    for i in range(0, 30):
        # wait for max 300 seconds
        publickey_url = 'http://' + cam.url + '/setup/publickey.cert'
        r = requests.get(publickey_url, auth=(cam.username, cam.password))
        if r.status_code == 200:
            publickey_found = True
            break
        time.sleep(1)

    enable_https = 'https_enable=1'
    configer.set(enable_https)
    time.sleep(5)

    assert publickey_found, "publickey.cert should be generated"

    # try to connect through https
    url = 'https://' + cam.url + '/cgi-bin/sysinfo.cgi'
    mauth = (cam.username, cam.password)
    r = requests.get(url, auth=mauth, verify=False)
    assert r.status_code == 200, "HTTP return code is not 200"
