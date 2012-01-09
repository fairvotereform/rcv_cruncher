# encoding: utf-8
#
# Copyright (C) 2011 Chris Jerdonek.  All rights reserved.
#

import calendar
import codecs
from datetime import datetime
import logging
import os
import sys
import time
import yaml


_log = logging.getLogger(__name__)


DEFAULT_ENCODING_OUTPUT = 'utf-8'
ENCODING_INTERNAL = 'utf-8'

INFO_FILE_NAME = 'INFO.yaml'


def utc_datetime_to_local_datetime(utc_datetime):
    utc_tuple = utc_datetime.utctimetuple()
    timestamp = calendar.timegm(utc_tuple)
    local_datetime = datetime.fromtimestamp(timestamp)

    return local_datetime


def utc_datetime_to_local_datetime_tzname(utc_datetime):
    local_datetime = utc_datetime_to_local_datetime(utc_datetime)
    local_tzname = "/".join(time.tzname) if time.tzname else ""

    return local_datetime, local_tzname


def unserialize_yaml_file(path, encoding=ENCODING_INTERNAL):
    """
    Deserialize a value from disk.

    """
    with codecs.open(path, "r", encoding=encoding) as stream:
        data = yaml.load(stream)

    return data


def yaml_serialize(instance):
    """
    Serialize an object instance to a unicode YAML document.

    """
    return yaml.dump(instance.__dict__,  encoding=None, default_flow_style=False)


def ensure_dir(path):
    if os.path.isdir(path):
        return
    _log.info("Creating directory at: %s" % path)
    os.mkdir(path)


def write_to_file(s, path, encoding=None):
    """
    Write a unicode string to a file.

    """
    if not isinstance(s, unicode):
        raise Exception("The argument is not a unicode string.")

    if encoding is None:
        encoding = DEFAULT_ENCODING_OUTPUT

    _log.info("Creating file at: %s" % path)
    with codecs.open(path, "w", encoding=encoding) as f:
        f.write(s)


def reraise(ex):
    raise ex, None, sys.exc_info()[2]


class Error(Exception):

    def __init__(self, err, *args):
        """
        err is the main error (e.g. string message or exception instance).

        """
        super(Error, self).__init__(err)
        self.__err = err
        self.__stack = list(args)

    def __type_name(self):
        return self.__class__.__name__

    def __repr__(self):
        stack = " stack=%s," % repr(self.__stack)
        return "%s(%s,%s)" % (self.__type_name(), repr(self.__err), stack)

    def __str__(self):
        lines = [repr(self.__err)] + self.__stack
        return "\n-->".join([str(line) for line in lines]) + "<--"

    def add(self, message):
        self.__stack.append(message)


