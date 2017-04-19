# -*- coding: utf-8 -*-
import time
from functools import wraps
import logging

logger = logging.getLogger(__file__)

def fn_timer(function):
    @wraps(function)
    def function_timer(*args, **kwargs):
        t0 = time.time()
        result = function(*args, **kwargs)
        t1 = time.time()
        logger.info("Total time running %s(%s): %s seconds" %
               (function.func_name, str(args), str(t1 - t0)))
        return result
    return function_timer

@fn_timer
def test(a):
    import time
    time.sleep(1)


if __name__ == "__main__":
    test("ssss")