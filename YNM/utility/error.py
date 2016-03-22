# -*- coding: utf-8 -*-

class LoadDBRKLibError(Exception):
    pass


class DBRKHandleIsNotCreatedError(Exception):
    pass


class CameraOptionIsNotSetError(Exception):
    pass


class ConnHandleIsNotCreatedError(Exception):
    pass


class ISOMParserHandleIsNotCreateError(Exception):
    pass


class DBRKConnectError(Exception):
    pass


class DBRKDisconnectError(Exception):
    pass


class PlatformError(Exception):
    pass


class DBRKReleaseError(Exception):
    pass


class DBRKCreateConnectionError(Exception):
    pass


class DBRKDeleteConnectionError(Exception):
    pass


class DBRKSetConnectionOptionError(Exception):
    pass


class DBRKSetConnectionUrlsExtraError(Exception):
    pass


class DBRKSetConnectionExtraOptionError(Exception):
    pass


class CallbackFunIsNoneError(Exception):
    pass


class ApplicationDataCompareFailed(Exception):
    pass


class InvalidExtData(Exception):
    pass


class LoadLibError(Exception):
    pass
