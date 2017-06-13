"""
Contains useful functions and utilities that are not neccessarily only useful
for this module. But are also used in differing modules insidide the same
project, and so do not belong to anything specific.
"""


import os
import logging
import imp
import sys
from dateutil import parser, tz
from datetime import datetime
import inspect
from cloghandler import ConcurrentRotatingFileHandler

local_zone = tz.tzlocal()
utc_zone = tz.tzutc()

def get_date(timestr=None):
    """
    Always parses the time to be in the UTC time zone; or returns
    the current date (with UTC timezone specified)
    
    :param: timestr
    :type: str or None
    
    :return: datetime object with tzinfo=tzutc()
    """
    if timestr is None:
        return datetime.utcnow().replace(tzinfo=utc_zone)
    
    if isinstance(timestr, datetime):
        date = timestr
    else:
        date = parser.parse(timestr)
    
    if 'tzinfo' in repr(date): #hack, around silly None.encode()...
        date = date.astimezone(utc_zone)
    else:
        # this depends on current locale, for the moment when not 
        # timezone specified, I'll treat them as UTC (however, it
        # is probably not correct and should work with an offset
        # but to that we would have to know which timezone the
        # was created) 
        
        #local_date = date.replace(tzinfo=local_zone)
        #date = date.astimezone(utc_zone)
        
        date = date.replace(tzinfo=utc_zone)
        
    return date


    

def load_config(proj_home=None):
    """
    Loads configuration from config.py and also from local_config.py
    
    :param: proj_home - str, location of the home - we'll always try
        to load config files from there. If the location is empty,
        we'll inspect the caller and derive the location of its parent
        folder.
    
    :return dictionary
    """
    conf = {}
    
    if proj_home is not None:
        proj_home = os.path.abspath(proj_home)
        if not os.path.exists(proj_home):
            raise Exception('{proj_home} doesnt exist'.format(proj_home=proj_home))
    else:
        frame = inspect.stack()[1]
        module = inspect.getsourcefile(frame[0])
        if not module:
            raise Exception("Sorry, wasnt able to guess your location. Let devs know this issue.")
        proj_home = os.path.abspath(os.path.join(os.path.dirname(module), '..'))
        
        
    if proj_home not in sys.path:
        sys.path.append(proj_home)
            
    conf['PROJ_HOME'] = proj_home
    
    conf.update(load_module(os.path.join(proj_home, 'config.py')))
    conf.update(load_module(os.path.join(proj_home, 'local_config.py')))
    
    return conf


def load_module(filename):
    """
    Loads module, first from config.py then from local_config.py
    
    :return dictionary
    """
    
    filename = os.path.join(filename)
    d = imp.new_module('config')
    d.__file__ = filename
    try:
        with open(filename) as config_file:
            exec(compile(config_file.read(), filename, 'exec'), d.__dict__)
    except IOError as e:
        pass
    res = {}
    from_object(d, res)
    return res


def setup_logging(name_, level='WARN', proj_home=None):
    """
    Sets up generic logging to file with rotating files on disk

    :param: name_: the name of the logfile (not the destination!)
    :param: level: the level of the logging DEBUG, INFO, WARN
    :param: proj_home: optional, starting dir in which we'll 
            check for (and create) 'logs' folder and set the 
            logger there
    :return: logging instance
    """

    level = getattr(logging, level)

    logfmt = u'%(levelname)s\t%(process)d [%(asctime)s]:\t%(message)s'
    datefmt = u'%m/%d/%Y %H:%M:%S'
    formatter = logging.Formatter(fmt=logfmt, datefmt=datefmt)
    logging_instance = logging.getLogger(name_)
    
    if proj_home:
        proj_home = os.path.abspath(proj_home)
        fn_path = os.path.join(proj_home, 'logs')
    else:
        frame = inspect.stack()[1]
        module = inspect.getsourcefile(frame[0])
        if not module:
            raise Exception("Sorry, wasnt able to guess your location. Let devs know this issue.")
        fn_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(module), '../..')), 'logs')
        
    if not os.path.exists(fn_path):
        os.makedirs(fn_path)

    fn = os.path.join(fn_path, '{0}.log'.format(name_.split('.log')[0]))
    rfh = ConcurrentRotatingFileHandler(filename=fn,
                                        maxBytes=2097152,
                                        backupCount=5,
                                        mode='a',
                                        encoding='UTF-8')  # 2MB file
    rfh.setFormatter(formatter)
    logging_instance.handlers = []
    logging_instance.addHandler(rfh)
    logging_instance.setLevel(level)

    return logging_instance


def from_object(from_obj, to_obj):
    """Updates the values from the given object.  An object can be of one
    of the following two types:

    Objects are usually either modules or classes.
    Just the uppercase variables in that object are stored in the config.

    :param obj: an import name or object
    """
    for key in dir(from_obj):
        if key.isupper():
            to_obj[key] = getattr(from_obj, key)


def overrides(interface_class):
    """
    To be used as a decorator, it allows the explicit declaration you are
    overriding the method of class from the one it has inherited. It checks that
     the name you have used matches that in the parent class and returns an
     assertion error if not
    """
    def overrider(method):
        """
        Makes a check that the overrided method now exists in the given class
        :param method: method to override
        :return: the class with the overriden method
        """
        assert(method.__name__ in dir(interface_class))
        return method

    return overrider


    