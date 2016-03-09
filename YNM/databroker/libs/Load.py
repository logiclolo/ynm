#!/usr/bin/python

from ctypes import *
CDLL('/usr/lib/x86_64-linux-gnu/libboost_chrono.so.1.54.0', mode=RTLD_GLOBAL)
CDLL('libPBEngine.so', mode=RTLD_GLOBAL)
CDLL('libosisolate.so', mode=RTLD_GLOBAL)
CDLL('libencrypt_md5.so', mode=RTLD_GLOBAL)
CDLL('libcommon.so', mode=RTLD_GLOBAL)
CDLL('libnetutility.so', mode=RTLD_GLOBAL)
CDLL('libsipua.so', mode=RTLD_GLOBAL)
CDLL('librtprtcp.so', mode=RTLD_GLOBAL)
CDLL('libsdpdecoder.so', mode=RTLD_GLOBAL)
CDLL('libencrypt_vivostrcodec.so', mode=RTLD_GLOBAL)
CDLL('libActiveDirectoryClient.so', mode=RTLD_GLOBAL)
CDLL('libntlm.so', mode=RTLD_GLOBAL)
CDLL('libDataBroker.so', mode=RTLD_GLOBAL)



