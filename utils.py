#!/usr/bin/env python
# Filename: tg/os.py
# Copyright (c) 2010-2011 Hobson Lane, dba TotalGood
# All rights reserved.

# Written by Hobson Lane <hobson@totalgood.com>
# OS = Operating System

version = 0.1

#!/usr/bin/python

import os
import re
import sys
from warnings import warn

# TODO: don't read the whole file into memory and write.
#   Do some clever buffering of a MB or so of text at a time.
#   When scan pattern overlaps multiple buffer pages and pattern extent is unknown
#     would have to repeat the search on a large sliding window one line at a time
#   But sliding window approach would dramatically increase unneccessary searches.
#   So pattern must be processed to identify the maximum number of lines it can span or user
#     must specify the number of lines to buffer and number of lines to shift the window.
def multiline_replace_in_file(search_pattern, replacement_pattern, fname):
    """Replace all occurrences of a search pattern in a single file

    BASED ON:
      http://stackoverflow.com/questions/1597649/replace-strings-in-files-by-python

    >>> replace_in_file('my_password', 'REDACTED_PASSWORD', '~/.bash_history')
    """

    with open(fname) as f:
        s = f.read()
        print s
    if not re.search(search_pattern, s, re.MULTILINE):
        return 
    s = re.sub(search_pattern, replacement_pattern, s, re.MULTILINE)
    print s
    with open(fname,'w') as f:
        f.write(s)


def replace_in_file(search_pattern, replacement_pattern, fname):
    """Replace all occurrences of a search pattern in a single file

    BASED ON:
      http://stackoverflow.com/questions/1597649/replace-strings-in-files-by-python

    >>> replace_in_file('my_password', 'REDACTED_PASSWORD', '~/.bash_history')
    """

    # first, see if the pattern is even in the file.
    with open(fname) as f:
        if not any(re.search(search_pattern, line) for line in f):
            return # pattern does not occur in file so we are done.

    # pattern is in the file, so perform replace operation.
    with open(fname) as f:
        out_fname = fname + ".tmp"
        out = open(out_fname, "w")
        for line in f:
            out.write(re.sub(search_pattern, replacement_pattern, line))
        out.close()
        os.rename(out_fname, fname)

# http://stackoverflow.com/questions/434597/open-document-with-default-application-in-python
def start(filepath):
    """NOT IMPLEMENTED, see launch() below"""
    import os,subprocess
    if os.name == 'nt':
        startfile(filepath)
    elif name in ['mac','posix']:
        try:
            #retcode = subprocess.call(('xdg-open if os.name==)+"open" + filename, shell=True)
            retcode = subprocess.call(('xdg-open', filepath))
        except:
            raise
        if retcode < 0:
            print >>sys.stderr, "Child was terminated by signal", -retcode
        else:
            print >>sys.stderr, "Child returned", retcode
    else:
        # registered names in 2.72: ['nt','posix','os2','ce','java','riscos'], 3.2 adds 'mac' and deleetes riscos
        pass

# proposed for Python 3.3 with help from Python development team
def launch(path, operation='open', gui=True, fallback=True):
    """Open file with the application that the OS associates with the file-type
    
    `path` is the path to the file or directory to open
    
    `operation` is the desired application action. Only 'open' is fully 
    supported. For Windows (and any OS that implements os.startfile), 
    'edit', 'print', 'explore', are supported. The operation 'find' is 
    supported on Windows if `path` is to a directory. If not, the containing 
    folder/directory for the path is used for the os.startfile 'find' operation.
    
    `gui` indicates the caller's preference for launching a GUI application 
    rather than an application with a command-line interface. NOT IMPLEMENTED
    
    Fallback controls whether launch() falls back gracefully to less prefered
    application options--to a nonGUI application if no GUI application
    is found, or to a viewer application if no edit application can be found.
    
    On Windows, calls os.startfile(), and attempts to call it first, 
    irrespective of os.name or system.platform.
    
    On Mac OS X, uses the ```open <https://developer.apple.com/library/mac/#documentation/Darwin/Reference/ManPages/man1/open.1.html>`_`` command.
    
    On non-Mac Unix, uses the ```xdg-open <http://portland.freedesktop.org/xdg-utils-1.0/xdg-open.html>`_`` command and fails
    if it can't be run (e.g., when it's not installed).
    
    :raises NotImplementedError: on non-Mac Unix when ``xdg-open`` fails
    :raises IOError: with *:attr:`errno` = :data:`errno.ENOENT`*, when path doesn't exist
    :raises OSError: with *:attr:`errno` = :data:`errno.ENOSYS`*, when OS cannot find an appropriate application association
    
    :returns: None
    
    Example:
    >>> import os.path
    >>> launch(os.path.realpath(__file__),'open')
    """
    
    # FIXME: Is OSError(errno.ENOSYS) the right error to raise?
    # TODO: Utilize best-practices from Mercurial project:
    #    http://selenic.com/repo/hg-stable/file/2770d03ae49f/mercurial/ui.py
    #    http://selenic.com/repo/hg-stable/file/2770d03ae49f/mercurial/util.py
    
    import sys, os, subprocess, errno

    # Ensure cross-platform path (Windows-friendly)
    path = os.path.normpath(path)
    
    # Guess user's desired operation (Windows verb)
    operation = operation or 'open'
    # Force case and padding to comply with Windows verb specification
    operation = operation.strip().lower()
    # Too presumptive, and wouldn't help for most typos ???
    # operation = operation[:min(len(operation),7]

    # if os.name == 'nt' or sys.platform.startswith('win32') ???
    if hasattr(os,'startfile') and hasattr(os.startfile, '__call__'):
        os.startfile(path, operation)
    elif sys.platform.startswith('darwin'): # or os.name == 'mac' ???
        # https://developer.apple.com/library/mac/#documentation/Darwin/Reference/ManPages/man1/open.1.html
        proc = subprocess.Popen( ['open', path], stderr=subprocess.PIPE, 
                                 stdin=subprocess.DEVNULL, 
                                 stdout=subprocess.DEVNULL)
        _, stderr_output = proc.communicate()
        if proc.returncode:
            if stderr_output.endswith("does not exist."):
                # exception chaining (...from err) not possible in Python < 3.0
                raise IOError(errno.ENOENT, "The path %s does not exist" %
                                              repr(path), path) # from err 
            elif stderr_output.startswith("No application can open"):
                raise OSError(errno.ENOSYS, 
                              "No application associated with file type in",
                              path) # from err
    elif os.name == 'posix':
        try:
            subprocess.check_call(['xdg-open', path], 
                                  stdin=subprocess.DEVNULL,
                                  stdout=subprocess.DEVNULL, 
                                  stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as err:
            # http://portland.freedesktop.org/xdg-utils-1.0/xdg-open.html manpage for return code meanings
            if err.returncode == 2:
                raise IOError(errno.ENOENT, "Path %s does not exist" % repr(path), path) # from err
            elif err.returncode == 3:
                raise OSError(errno.ENOSYS, 
                              "No application associated with file type in",
                              path) # from err
            else:
                raise
        except EnvironmentError as err:
            if err.errno == errno.ENOENT: # xdg-open not installed/accessible
                raise NotImplementedError # from err 
            else:
                raise



# TODO: reuse this script in "/home/hobs/bin/securehist" to search widely for passwords to delete
# TODO: use the os.path functions to parse the filename and compare the extension 
#      (so that an empty extension can be matched, as in the examples)
## Quick and dirty way to turn this module file into an executable script
#if 5 < len(sys.argv) < 4:
#	sys.stderr.write("Usage: replace_in_files <string_before> <string_after> <dir_name> <file_extension> \n")
#	sys.exit(1)
#if len(sys.argv) == 5:
#	replace_in_files(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
#else:
#	replace_in_files(sys.argv[1], sys.argv[2], sys.argv[3])
def replace_in_files(search_pattern, relacement_pattern, dir_name='./', extensions=None):
    """Replace all occurrences of a search pattern in all files in a directory tree

    BASED ON:
      http://stackoverflow.com/questions/1597649/replace-strings-in-files-by-python

    >>> replace_in_files('your_sensitive_string_to_be_removed', '***REDACTED_TEXT***', '~/bin',['','.txt','.sh'])
    """
    repat = re.compile(search_pattern)
    for dirpath, dirnames, filenames in os.walk(dir_name):
        for fname in filenames:
            if extensions and not fname.lower().endswith(replace_extensions):
                continue
            fullname = os.path.join(dirpath, fname)
            replace_in_file(fullname, repat, replacement_pattern)

def containing_folder(filepath=os.getcwd()):
    return os.path.split(os.path.dirname(filepath).strip(os.sep))[-1]

    
class Env:
    """Finds user information and user file system directory
    
    Example Usage:
    >>> e = Env()
    >>> e.home # doctest: +SKIP
    >>> e.user # doctest: +SKIP
    >>> e.cwd  # doctest: +SKIP
    """
    def __init__(self,username='hobs'):
        self.cwd   = os.path.normpath(os.getcwd())
        if not self.cwd:
            self.cwd   = os.path.abspath('.') # FIXME: this just calls os.getcwd() anyway
        self.home  = os.path.expanduser('~')
        if self.home == '~':
            self.home=os.path.normpath(os.getenv('HOME'))
        if self.home:
            self.user=os.path.normpath(os.path.dirname(self.home))
        else:
            self.user=os.getenv('USER')
            if self.user:
                self.home=os.path.normpath(os.path.join(os.path.sep+'home',self.user))
            else:
                self.home=os.path.normpath(os.path.join(os.path.sep+'home',user))
                self.user=containing_folder(self.home)
        # TODO: check for existence and read/writabiltiy of home path
        # TODO: if still no home path do a filesystem search in common places including cwd
        #       then fall back to a /tmp folder or cwd/tmp
        try:
            self.module_path=os.path.realpath(__file__)
            self.module_dir =os.path.dirname(self.module_path)
            self.work_dir   =os.path.split(self.module_dir)[0]
        except NameError:
            # py2exe
            self.module_path=sys.argv[0]
            self.module_dir =os.path.dirname(self.module_path)
            self.work_dir   =self.module_path
    def __repr__(self):
        return "USER='"+self.user+"' && HOME='"+self.home+"'"

# FIXME: does this point cwd to the module directory and name?
env = Env()

# FIXME: does this name the tmp file after the utils module?
DEFAULT_TMP_FILENAME = str(__name__)+'.tmp.txt'
def find_nearby_file(filename=None, defaultname=DEFAULT_TMP_FILENAME, alternate_ext=['.txt','','.tmp']):
    """
    Looks in $CWD and $HOME for indicated file(s), returning the full path
    
    Returns the first valid absolute, normalized path found where the file
    is readable by the current process.
    
    TODO: 
    1. Read and write mode check
    2. Check alternate file name extensions
    3. Check alternate file names with stemming (read-only)
    4. Discriminate between a file that needs to be new and empty vs. existing
    5. Date-wise creation of a tmp filename while checking uniqueness
    >>> find_nearby_file('README')
    """
    filepath = filename or os.path.abspath(defaultname) # looks in cwd
    if not os.path.isfile(filepath):
        filepath= os.path.join(env.home,defaultname)
    if os.path.isfile(filepath):
        with open(filepath,'+w') as fp:
        with 
        with open(filepath,'w') as fp:
            s = fp.write('')
            return filepath
        print 'Unable to create a file at ',repr(filepath)

def android_path():
    # any android devices mounted in "usb storage" mode and return a list of paths to their sdcard root
    # not currently implemented
    return '/media/83E2-0FEC' # this just happens to be the label for my android t-mobile G2 flashed with cyanogen mod

def user_home():
    ue = Env()
    return(ue.user,ue.home)

def path_here():
    en = Env()
    return(en.module_path,en.module_dir,en.work_dir)

# not real sure why you can't just call 'assert expected==actual, message'
# http://stackoverflow.com/questions/1179096/suggestions-for-python-assert-function
def validate(expected, actual=True, type='==', message='', trans=(lambda x: x)):
    m = { '==': (lambda e, a: e == a),
          '!=': (lambda e, a: e != a),
          '<=': (lambda e, a: e <= a),
          '>=': (lambda e, a: e >= a), }
    assert m[type](trans(expected), trans(actual)), 'Expected: %s, Actual: %s, %s' % (expected, actual, message)
def validate_str(expected, actual=True, type='', message=''):
    assert_validation(expected, actual, type, message, trans=str)

def basic_arguments(p):
    from optparse import OptionParser
    if p and isinstance(p,OptionParser):
        p.add_option('-v', '--verbose',
            dest='verbose', default=True,
            action='store_true',
            help='Print status messages.', )
        p.add_option('--debug',
            dest='debug', default=False,
            action='store_true',
            help='Print debug information.', )
        p.add_option('-q', '--quiet',
            dest='verbose', default=True,
            action='store_false', 
            help="Don't print status messages.")
        return p
    else:
        warn('Basic options (arguments) were not added to the OptionParser object because no object named "p" exists in the local namespace.')

def zero_if_none(x):
    return x or 0
#	if not x:
#		return 0
#	return x


def running_as_root(quiet=False):
    if os.geteuid() == 0:
        return True
    if not quiet:
        msg = "{0}:{1}:\n  Insufficient priveledges--need admin (root). Rerun this script using sudo or equivalent.".format(__file__,__name__)
        warn(msg)
    return False

# unlike math.copysign, this may return +1 for -0.0 (on systems that have negative zero)
def sign(f):
    s = type(f)(1)
    if f<0:
        s *= -1
    return s

def make_same_type_as(obj1,obj2):
  return type(obj2)(obj1)

import collections
# accepted answer http://stackoverflow.com/questions/2158395/flatten-an-irregular-list-of-lists-in-python/2158532#215853
def flatten(list_o_lists):
    """Flatten all dimensions of a multi-dimensional iterable (list/array, tuple, dict, etc) to 1-D, except for member strings.

    BASED ON:
      http://stackoverflow.com/questions/2158395/flatten-an-irregular-list-of-lists-in-python/2158532#215853

    >>> l1 = list(flatten(UNIT_CONVERSIONS))
    >>> [(s in l1) for s in ('inches','m','furlongs','stone')]
    [True, True, False, False]
    """
    for el in list_o_lists:
        if isinstance(el, collections.Iterable) and not isinstance(el, basestring):
            for subel in flatten(el):
                yield subel
        else:
            yield el

# more complicated "flatten", but effective answer (doesn't seem like it would work for other iterables like dict and set, but seems to
# http://stackoverflow.com/questions/2158395/flatten-an-irregular-list-of-lists-in-python/2158532#215853
flatten_lists = lambda *n: (e for a in n
    for e in (flatten(*a) if isinstance(a, (tuple, list)) else (a,)))

 

## TODO: there should be a clever way to do this with a recursive function and a static variable to hold the accumulated list of dimensions
#def __size__(x): 
#  l = nlp.has_len(x)
#  TG_NLP_SIZE_DIMENSION_LIST[-1]=max(TG_NLP_SIZE_DIMENSION_LIST[-1],l)
#  
#  for x0 in x:
#    l=max(nlp.has_len(x),l)
#  
#def size(x):
#  """Calculate the shape (size) of a multi-dimensional list"""
#  HL_SIZE_DIMENSION_LIST = [0] # reset the dimension list
#  return __size__(x)


