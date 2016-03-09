# -*- coding: utf-8 -*-

def parse_vivotek_response (input_string):
    resp = {}

    if type(input_string) == type('str'):
        name_value_pairs = input_string.split('&')
        for pair in name_value_pairs:
            if pair:
                name, value = pair.split('=')
                resp[name] = value

    return resp
