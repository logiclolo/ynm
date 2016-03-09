# -*- coding: utf-8 -*-

import abc
import requests
import re
import os
import json
import sys
import enum
import YNM.utility.bcolors as bcolors
from YNM.utility import utility


def alter_type(in_value):
    if ',' in in_value:
        p_list = list()
        for item in in_value.split(','):
            if item != "":
                if utility.is_digit(item):
                    p_list.append(int(item))
                else:
                    p_list.append(item)
        return p_list
    elif utility.is_digit(in_value):
        return int(in_value)
    else:
        return in_value


class CameraCommandError(Exception):
    pass


class EAuthority(enum.Enum):
    (eViewer, eOperator, eAdmin) = xrange(3)

    def __str__(self):
        return str(self.name[1:].lower())


class EFormat(enum.Enum):
    (eNameValue, eDict) = xrange(2)


class IConfiger:
    __metaclass__ = abc.ABCMeta

    def get(self, config):
        return None

    def set(self, config):
        return None


class CGIGroup (object):
    set = None
    get = None

global_special_prefix_keys = ['c', 's', 'i']
period = {
    "1/4s": '250',
    "1/2s": '500',
    "0.5s": '500',
    "1s": '1000',
    "2s": '2000',
    "3s": '3000',
    "4s": '4000',
}

bitrate = {
    "1mbps": '1000000',
    "2mbps": '2000000',
    "3mbps": '3000000',
    "4mbps": '4000000',
}


class ExtendDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


class Config(ExtendDict):
    def __getattr__(self, item):

        if item in self.keys():
            return self[item]
        else:
            dict.__setitem__(self, item, Config())
            return self[item]

    __setattr__ = dict.__setitem__

    def __getitem__(self, item):
        new_item = item
        if utility.is_digit(item):
            new_item = int(item)
            dict.__setitem__(self, new_item, Config())

        return dict.__getitem__(self, new_item)


class Configer (IConfiger):

    def __init__(self, cam):
        self._camera = cam
        self._auth = (self._camera.username, self._camera.password)
        self.viewer = CGIGroup()
        self.viewer.get = '/cgi-bin/viewer/getparam.cgi'
        self.viewer.set = '/cgi-bin/viewer/setparam.cgi'
        self.operator = CGIGroup()
        self.operator.get = '/cgi-bin/operator/getparam.cgi'
        self.operator.set = '/cgi-bin/operator/setparam.cgi'
        self.admin = CGIGroup()
        self.admin.get = '/cgi-bin/admin/getparam.cgi'
        self.admin.set = '/cgi-bin/admin/setparam.cgi'

    def load_conf_file(self, tfile):
        fileType = os.path.splitext(tfile)[-1]
        if fileType == '.json':
            try:
                with open(tfile) as confile:
                    return json.load(confile)
            except ValueError:
                print bcolors.BAD + "wrong format json file." + bcolors.NORMAL


    def _supported_dict(self, value):
        if value is dict or \
           value is Config or \
           value is ExtendDict:
            return True
        else:
            return False

    def _compose_dict(self, group, config):
        param_groups = group.split('_')
        result = Config()
        p_result = result
        for i in range(len(param_groups)):
            if i != len(param_groups)-1:
                p_result[param_groups[i]] = ExtendDict()
            else:
                p_result[param_groups[i]] = config
            p_result = p_result[param_groups[i]]
        return result

    def _compose_cmd(self, group, config):
        cmd = ""
        for key, value in config.items():
            tValue = type(value)
            if self._supported_dict(tValue):
                if group is None:
                    new_group = key
                else:
                    new_group = "%s_%s" % (group, key)
                cmd += self._compose_cmd(new_group, value)
            elif tValue is str or tValue is unicode or tValue is int:
                cmd += "&%s_%s=%s" % (group, key, value)

        # replace c_<X> & s_<X> i_<X> to cX & sX & iX
        for word in global_special_prefix_keys:
            cmd = cmd.replace("_" + word + "_", "_" + word)

        return cmd

    def get(self, config, output=EFormat.eDict, level='admin'):
        request_url = "http://" + self._camera.url + self.admin.get
        r = requests.get(request_url, params=config, auth=self._auth)

        if output == EFormat.eNameValue:
            return r.text
        elif output == EFormat.eDict:
            content = r.text.replace("\r", "")
            lines = re.findall('.+=.+', content)

            # regs = ['('+a+')[0-9]{1,3}' for a in global_special_prefix_keys]
            result = ExtendDict()
            for line in lines:
                line = line.strip()
                param, value = line.split('=')
                params = param.split('_')
                value = value[1:-1]     # remove signal quote
                p_result = result
                for i in range(len(params)):

                    # deal with special_word
                    regex = ""
                    found = False
                    for word in global_special_prefix_keys:
                        regex = '^(' + word + ')[0-9]{1,3}$'
                        res = re.search(regex, params[i])
                        if res:
                            found = True
                            break

                    if found:
                        if word not in p_result.keys():
                            p_result[word] = ExtendDict()
                        p_result = p_result[word]
                        key = int(params[i][len(word):])
                    else:
                        key = params[i]

                    # to establish a corresponding dict
                    if key not in p_result.keys():
                        if i != len(params)-1:
                            p_result[key] = ExtendDict()
                        else:
                            p_result[key] = alter_type(value)
                    p_result = p_result[key]

            return result

    def get_value(self, config):
        content = self.get(config, EFormat.eNameValue)
        exec(content)
        result = None
        try:
            result = eval(config)
        except TypeError:
            print bcolors.BAD, \
                sys._getframe().f_code.co_name, \
                "function don't support more than one parameter", \
                bcolors.NORMAL
        return alter_type(result)

    def _set(self, config):
        request_url = "http://" + self._camera.url + self.admin.set
        r = requests.get(request_url, params=config, auth=self._auth)
        content = r.text
        if r.status_code != 200:
            raise CameraCommandError()
        return content

    def set(self, config, level='admin'):
        cmd = ""
        typ = type(config)
        if typ is str or typ is unicode:
            cmd = config
            self._set(cmd)
        elif self._supported_dict(typ):
            cmd = self._compose_cmd(None, config)
            self._set(cmd)
        else:
            print bcolors.WARNING +\
                "Configer.set don't support ", typ, bcolors.NORMAL


    def set_group(self, group, config):
        dict_conf = self._compose_dict(group, config)
        cmd = self._compose_cmd(None, dict_conf)
        self._set(cmd)

    def set_videoin(self, config):
        videoin = 'videoin'
        cmd = ""

        if 'channel' in config.keys():
            channel = config['channel']
        else:
            channel = '0'

        if 'stream' in config.keys():
            stream = config['stream']
        else:
            stream = '0'

        if 'codec' in config.keys():
            codec = config['codec']
        else:
            param = "%s_c%s_s%s_codectype" % (videoin, channel, stream)
            print "not setting codec, get %s from camera" % param
            codec = self.get_value(param)

        # video setting
        setting = ['resolution', 'enableeptz']
        cx_sx = videoin + '_c' + channel + '_s' + stream
        for key in setting:
            if key in config.keys():
                cmd = cmd + '&' + cx_sx + '_' + key + '=' + config[key]

        # video setting under codectype
        setting = [
            'ratecontrolmode',
            'dintraperiod_enable',
            'quant',
            'qvalue',
            'qpercent',
            'cbr_quant',
            'cbr_qpercent',
            'maxframe',
            'profile',
            'prioritypolicy',
            'maxvbrbitrate',
            'smartstream_mode',
            'smartstream_foreground_quant',
            'smartstream_background_quant',
            'smartstream_maxbitrate',
            'smartstream_win_i0_enable',
            'smartstream_win_i0_home',
            'smartstream_win_i0_size',
            'smartstream_win_i1_enable',
            'smartstream_win_i1_home',
            'smartstream_win_i1_size',
            'smartstream_win_i2_enable',
            'smartstream_win_i2_home',
            'smartstream_win_i2_size',
            ]
        cx_sx_codec = cx_sx + '_' + codec

        for key in setting:
            if key in config.keys():
                cmd = cmd + '&' + cx_sx_codec + '_' + key + '=' + config[key]

        if 'intraperiod' in config.keys():
            skey = config['intraperiod'].lower()
            if skey in period.keys():
                value = period[skey]
                cmd = cmd + '&' + cx_sx_codec + '_intraperiod=' + value
            else:
                print bcolors.WARNING +\
                    "can't identify intraperiod (%s)" % config['intraperiod'] +\
                    bcolors.NORMAL

        if 'bitrate' in config.keys():
            skey = config['bitrate'].lower()
            if skey in bitrate.keys():
                value = bitrate[skey]
                cmd = cmd + '&' + cx_sx_codec + '_bitrate=' + value
            else:
                cmd = cmd + '&' + cx_sx_codec + '_bitrate=' + config['bitrate']
                print cmd

        self.set(cmd)


IConfiger.register(Configer)
