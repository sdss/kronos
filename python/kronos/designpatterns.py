#!/usr/bin/python

''' This file collects classes that implement useful design patterns in Python. '''


# used by memoize
import collections
import functools
import traceback

from .msg import errMsg

#
# Taken from: http://wiki.python.org/moin/PythonDecoratorLibrary#Memoize
#
class memoize(object):
    '''Decorator. Caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned
    (not reevaluated).
    '''
    def __init__(self, func):
        self.func = func
        self.cache = {}
    def __call__(self, *args):
        if not isinstance(args, collections.Hashable):
            # uncacheable. a list, for instance.
            # better to not cache than blow up.
            return self.func(*args)
        if args in self.cache:
            return self.cache[args]
        else:
            value = self.func(*args)
            self.cache[args] = value
            return value
    def __repr__(self):
        '''Return the function's docstring.'''
        return self.func.__doc__
    def __get__(self, obj, objtype):
        '''Support instance methods.'''
        return functools.partial(self.__call__, obj)

#
# See also: http://wiki.python.org/moin/PythonDecoratorLibrary#Singleton
#
def singleton(cls):
    '''
    This function implements the singleton design pattern in Python.
    To use it, simply import this file:

    from singleton import singleton

    and declare your class as such:

    @singleton
    class A(object):
        pass
    '''
    instance_container = []
    def getinstance():
        if not len(instance_container):
            instance_container.append(cls())
        return instance_container[0]
    return getinstance

# cacher is very similar to memoize
# except the cached value is stored on the
# class to which the method belongs
# this is useful for clearing/modifying cached values
# from anywhere in the object instance.
class Cacher(object):
    """A decorator that will go get or compute the value ONLY if the property is accessed,
     and will cache the result on the decorated method's object instance,
    so no db calls or computations are ever repeated.
    Intended to be used with the decorator @property
    """
    def __init__(self, f):
        """@param[in] f the method to be decorated
        """
        # cacheAttrName is the attribute under which the cached value
        # is stored (is simply _<methodname>) on the class where the decorated method resides.
        self.cacheAttrName = "_"+f.func_name
        self.f = f

    def __call__(self, cls):
        """@param[in] cls: the class to which the method stored at self.f belongs. Passed automatically
        via decoration. Note, must be decorated with @property too!
        """
        if not hasattr(cls, self.cacheAttrName):
            # the value has not been cached, go get and cache it.
            # value = self.f(cls) # debug! un/comment this to force exceptions to not be silently handled
            try:
                # call the decorated method, get the value
                value = self.f(cls)
            except Exception:
                # eventually log (the presumably db/schema related) error
                errMsg(traceback.format_exc())
                value = None
            # cache the value on the decorated method's class instance
            # it will be available under cls._<methodname>
            setattr(cls, self.cacheAttrName, value)
        # get the cached value
        return getattr(cls, self.cacheAttrName)
