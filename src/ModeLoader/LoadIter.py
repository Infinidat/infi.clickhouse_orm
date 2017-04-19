# -*- coding: utf-8 -*-
import logging

logger = logging.getLogger(__name__)


class LoadIter(object):

    def __init__(self, mode_builder):
        self.mode_builder = mode_builder

    def loderIter(self, iter, modename, add_kwargs = None):
        if add_kwargs is None:
            add_kwargs = {}
        for line in iter:
            try:
                yield self.mode_builder.build(line, tablename=modename, add_kwargs=add_kwargs)
            except:
                import sys
                import traceback
                import json
                exc_type, exc_value, exc_traceback = sys.exc_info()
                errinfo = traceback.format_exception(exc_type, exc_value, exc_traceback)
                logger.error("%s, LOG: %s" % (json.dumps(errinfo), line))