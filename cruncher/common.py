# encoding: utf-8
#
# Copyright (C) 2011 Chris Jerdonek.  All rights reserved.
#

import codecs
import logging
import os
import sys

_log = logging.getLogger(__name__)


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
        lines = [self.__err] + self.__stack
        return "\n-->".join([str(line) for line in lines]) + "<--"

    def add(self, message):
        self.__stack.append(message)


