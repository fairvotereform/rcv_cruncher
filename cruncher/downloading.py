# encoding: utf-8
#
# Copyright (C) 2011 Chris Jerdonek.  All rights reserved.
#

import logging
import urllib
import os

from .common import reraise
from .common import Error


_log = logging.getLogger(__name__)


def download(url, target_path):
    """
    Download the file at the given URL to the given target path.

    """
    _log.info("Downloading %s to %s..." % (url, target_path))
    try:
        urllib.urlretrieve(url, target_path)
    except Exception, ex:
        err = Error(ex)
        err.add("Error downloading url: %s" % url)
        reraise(err)

    info = os.stat(target_path)
    _log.info("Downloaded bytes: %s" % info.st_size)


