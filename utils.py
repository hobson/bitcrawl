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
# TODO: DRY-up using replace_in_file
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

TEXTCHARS = ''.join(map(chr, [7,8,9,10,12,13,27] + range(0x20, 0x100)))
is_binary_string = lambda bytes: bool(bytes.translate(None, TEXTCHARS))

def replace_in_file(search_pattern, replacement_pattern, fname,
                    verbose=True, interactive=True, tmp_file_suffix=".tg.utils.replace_in_file.tmp", dry_run=False,binary=False):
    """Replace all occurrences of a search pattern in a single file

    Loosely modeled after ideas from 
    <http://stackoverflow.com/questions/1597649/replace-strings-in-files-by-python>

    >>> replace_in_file('my_password', 'REDACTED_PASSWORD', '~/.bash_history')
    """

    if isinstance(search_pattern, str):
        search_pattern = re.compile(search_pattern)
    if not isinstance(search_pattern, re._pattern_type):
        raise ValueError('Invalid search string regex or re pattern object')
    # first, see if the pattern is even in the file.
    found = 0
    l = 0
    with open(fname) as fin:
        for line in fin:
            l += 1
            if not binary and is_binary_string(line):
                # TODO: raise an exception if appropriate
                return
            if search_pattern.search(line):
                if verbose:
                    print "First found the requested text, "+repr(search_pattern.pattern)+", on line %d " % l
                found = 1
                break
        if not found:
            if verbose:
                print "Search pattern "+repr(search_pattern.pattern)+" not found in file path "+repr(fname)+'.'
            return
    found = 0
    with open(fname) as fin: # like fin.seek(0)
        out_fname = fname + tmp_file_suffix
        # FIXME: use tempfile module or some other means of generating a unique tmp file
        # FIXME: don't overwrite existing file if exists, raise exception
        with open(out_fname, "w") as fout:
            for line in fin:
                if not isinstance(line,(str,unicode)) or is_binary_string(line): # FIXME, currently can't read and write binary strings
                    continue # abort for unicode and binary, for now
                (s,n) = search_pattern.subn(replacement_pattern, line)
                if (verbose or interactive) and n:
                    print 'Found {0} occurences on line {1}'.format(n,l)
                    print '  WAS: '+line
                    print '   IS: '+s
                if interactive:
                    if wait_for_key('Hit [Y] or [y] to replace, [ctrl-C] to cancel, anything else to skip.') in 'Yy':
                        if not dry_run:
                            found += n
                            fout.write(s)
                        else:
                            print 'DRY_RUN set, so no change made'
                            fout.write(line)
                    else:
                        if not dry_run:
                            fout.write(line)
                        else:
                            print 'DRY_RUN set, so no change made'
                            fout.write(line)
                else:
                   if not dry_run:
                       found += n
                       fout.write(s)
                   else:
                       print 'DRY_RUN set, so no change to file.'
                       fout.write(line)
    if found:
        os.rename(out_fname, fname)

# http://stackoverflow.com/questions/434597/open-document-with-default-application-in-python
def start(filepath):
    """NOT IMPLEMENTED, see launch() below"""
    import os,subprocess
    if os.name == 'nt':
        startfile(filepath)
    elif name in ['posix']: # 'mac' doesn't work here because too old a variant of mac OS
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

# based on http://code.activestate.com/recipes/499305-locating-files-throughout-a-directory-tree/
def locate(pattern, basepath='', regex=False, matchpath=False):
    """Locate all files matching pattern below supplied base path.
    
    >>> locate('/tg/utils.py',basepath='/',matchpath=True)
    <generator object ...>
    
    matchpath: Include path string matches in addition to filename matches
    regex: Pattern is interpreted as a regular expression instead of a Unix-style file glob
    
    TODO:
        use posix 'slocate --existing' command if availble for faster results
        update locate or slocate database if it's stale
    """
    import os, fnmatch, re
    basepath = basepath if isinstance(basepath,str) else ''
    basepath = basepath or ''
    # no need to assign to os.curdir or Env.CWD because os.path.abspath('') does so by default
    basepath = basepath if (not basepath=='.' and not basepath=='.'+os.path.sep) else '' #os.curdir
    if basepath == os.path.sep or basepath=='/':
        basepath = os.path.sep
    basepath = os.path.abspath(os.path.normpath(basepath))
    # print 'basepath = '+repr( basepath )
    matcher = fnmatch.fnmatch
    matcher_arg = pattern 
    if not matcher_arg:
        raise ValueError("Can't match a file unless you provide a pattern for locate() to look for!")
    if regex:
        rx = re.compile(pattern) # if weren't using a compiled regex then code less complicated but less efficient
        matcher = rx.search
        matcher_arg = 0 # for re.search() this is the position in the string to start the search
    for path, dirs, files in os.walk(os.path.abspath(basepath)):
        files = files if not matchpath else [os.path.join(path,fn) for fn in files]
        print repr(files)
        fullpaths=[]
        for fp in files:
            if matcher(fp, matcher_arg):
                fullpaths += [fp]
        for fullpath in fullpaths:
            print fullpath
            if fullpath:
                fullpath = fullpath if matchpath else os.path.join(path,fullpath)
                print fullpath
                yield fullpath

#def locate(path_pattern,base_path=''):
#    """Cross platform file find command similar to posix 'locate' command"""
#    if not path_pattern or not isinstance(path_pattern, str):
#        raise ValueError('Unable to recognize the path pattern string in '+repr(path_pattern))
#    is os.name=='posix':
#        if os.base_path=='':
#            subprocess.check_call(['locate', path_pattern], 
#                                      stdin=subprocess.DEVNULL,
#                                      stdout=subprocess.DEVNULL, 
#                                      stderr=subprocess.DEVNULL)
                                  
                            

# from http://docs.python.org/faq/library#how-do-i-get-a-single-keypress-at-a-time
def wait_for_key(message='Hit Y <CTRL-C> to cancel, any other key to continue...',verbose=False):
    import termios, fcntl, sys, os
    print message
    if os.name == 'posix': 
        fd = sys.stdin.fileno()

        oldterm = termios.tcgetattr(fd)
        newattr = termios.tcgetattr(fd)
        newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
        termios.tcsetattr(fd, termios.TCSANOW, newattr)

        oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)
        try:
            while 1:
                try:
                    c = sys.stdin.read(1)
                    if verbose:
                        print "Received character "+repr(c)+" from stdin."
                    return c # TODO: this doesn't bypass the finally section does it?
                except IOError: pass
        finally:
            termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
            fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)
    elif sys.platform.startswith('darwin'):
        # TODO: implement
        raise NotImplementedError("No keyboard input function is implemented for older Mac OS versions.")
    else:
        # TODO: implement
        raise NotImplementedError("No keyboard input function is implemented for your OS.")
    
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
def replace_in_files(search_pattern             , 
                     replacement_pattern        ,
                     dir_name             = './', # FIXME: crossplatform CWD using Env.CWD sys.cwd()?
                     extensions           = '',
                     filename_pattern     = None, 
                     verbose              = True,
                     dry_run              = True,
                     interactive          = False):
    """Replace all occurrences of a search pattern in all files in a directory tree

    BASED ON:
      http://stackoverflow.com/questions/1597649/replace-strings-in-files-by-python

    >>> replace_in_files('your_sensitive_string_to_be_removed', '***REDACTED_TEXT***', '~/bin',['','.txt','.sh'])
    """
    repat = re.compile(search_pattern)
    if filename_pattern:
        fpat  = re.compile(filename_pattern)
    else:
        fpat = None
    done = False
    for dirpath, dirnames, filenames in os.walk(dir_name):
        if done:
            break #TODO: surely there's a better way to break out of a nested loop twice
        for fname in filenames:
            # TODO: allow multiple extensions in a list/set/tuple
            if extensions and not fname.lower().endswith(extensions.lower()): 
                continue
            # TODO: detect whether pattern contains path separators (slashes) and match to fullname if so
            if fpat and not fpat.match(fname):
                continue
            fullname = os.path.join(dirpath, fname)
            if verbose or interactive:
                print 'Looking for pattern '+repr(repat.pattern)+' in '+repr(fullname)+'.'
            key = 'Y'
            if interactive:
                key = wait_for_key('Hit Y to procede, <CTRL-C> to cancel, any other key to skip this file.')
            if key in ['x','X','C','c']:
                done = True
                break
            if key in ['Y','y']:
                replace_in_file(search_pattern, replacement_pattern, fname=fullname,
                    verbose=verbose, interactive=interactive, 
                    tmp_file_suffix=".tg.utils.replace_in_file.tmp",
                    dry_run=dry_run)

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
        with open(filepath,'a+') as fp: # open for reading and writing with pointer at end
            s = fp.write('')
            return filepath
        print 'Unable to create or append the file at ',repr(filepath)

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

## Django project settings loader
#import os
#ROOT_PATH = os.path.dirname(os.path.abspath(__file__))

## You can key the configurations off of anything - I use project path.
#configs = {
#    '/path/to/user1/dev/project': 'user1',
#    '/path/to/user2/dev/project': 'user2',
#    '/path/to/qa/project': 'qa',
#    '/path/to/prod/project': 'prod',
#}

## Import the configuration settings file - REPLACE projectname with your project
#config_module = __import__('config.%s' % configs[ROOT_PATH], globals(), locals(), 'projectname')

## Load the config settings properties into the local scope.
#for setting in dir(config_module):
#    if setting == setting.upper():
#        locals()[setting] = getattr(config_module, setting)

def merge_settings( new, old=None, allcaps=True, doubleunderscore=False, verbose=2, overwrite=True, depth=100):
    """
    Merge two namespaces (modules), optionally ignoring non-ALL-CAPS names
    
    If old is None then this function attempts to use a settings (settings.py)
    module from the python path.
    
    Duplicate keys (variable/atribute names) are recursively merged to 
    deal with nested dictionaries (dict of dict of dict ...)
    
    Lists and tuples are appended/extended.
    Dicts and sets are updated/unioned
    """
    # TODO: check for empty new dicts and either delete or don't update the old dict
    import copy
    if not old:
        warn('no old module supplied, so loading the nearest settings.py')
        import settings as old
    import types
    scalar_type = (str, float, int, bool) # TODO: what about types.ClassType or types.ObjectType or types.StringTypes
    # TODO: check for empty new dicts and either delete or don't update the old dict
    if verbose>=2:
        print('old='+repr(type(old)))
        print('new='+repr(type(new)))
    #print new.__dict__
    if isinstance( old, types.ModuleType):
        dold = old.__dict__
    elif isinstance( old, dict):
        dold = old # can't deepcopy dicts with __new__ method
    else: #unnecessary? 
        dold = copy.deepcopy(dict(old)) # deepcopy should be unnecessary
    if isinstance( new, types.ModuleType):
        dnew = new.__dict__
    elif isinstance( new, dict):
        dnew = new # can't deepcopy dicts with __new__ method
    else: #unnecessary?
        dnew = copy.deepcopy(dict(new)) # deepcopy should be unnecessary
    if isinstance(old, dict) and isinstance(new,dict) and isinstance( dold, dict ) and isinstance( dnew, dict ):
        if verbose>=2:
            print 'merging 2 modules'
        # merge non-allcaps stuff within dicts, because this is likely the second (recursive) call to merge_settings
        merge_iter( dnew, dold, allcaps=False, doubleunderscore=True, verbose=verbose, 
                    overwrite=overwrite, depth=depth)
    elif isinstance( dold, dict ) and isinstance( dnew, dict ):
        if verbose>=2:
            print 'merging 2 modules'
        # when non-dicts are passed to merge_settings, this is a clue that this is the first (nonrecursive) call, so ingnore allcaps (if requested) at the top level
        merge_settings( dnew, dold, allcaps=allcaps, doubleunderscore=True, verbose=verbose, 
                    overwrite=overwrite, depth=depth)
    # FIXME: watch out! you're replacing hidden module elements like __name__ __file__ etc!!!!
    if isinstance( old, types.ModuleType):
        if verbose>=2:
            print 'setting the old module to contain the values from the new merged dict'
        for k,v in dold.items():
            if not ( k.startswith('__') and k.endswith('__') ):
                merge_iter( dnew, dold, allcaps, doubleunderscore, verbose=verbose, 
                            overwrite=overwrite, depth=depth)
        old.__dict__ = dold # is this enough to reset all the values?
    else:
        if verbose>=2:
            print 'setting the old dict to a new merged dict'
        old = dold # no deep copy because a copy was already made
    return old

# designed for django settings.py files, but should work with any namespace merging of only all-caps variables
def merge_iter( new, old, allcaps=True, doubleunderscore=False, verbose=2, overwrite=True, depth=100):
    """
    Merge two namespaces or dictionaries, optionally ignoring non-ALL-CAPS names
    
    Duplicate keys (variable/atribute names) are recursively merged to 
    deal with nested dictionaries (dict of dict of dict ...)
    
    Lists are appended/extended.

    TODO:
        mimic the Yii associative array merge function, including specification of prefixes and suffixes to skip
    """
    import types,copy
    scalar_type   = (str, float, int, bool, types.MethodType) # TODO: what about types.ClassType or types.ObjectType or types.StringTypes
    iterable_type = (list,tuple,set)
    if isinstance( old, types.ModuleType ) or isinstance( new, types.ModuleType ):
        print 'aborting merge of 2 modules'
        return old
    elif isinstance( old, dict ) and isinstance( new, dict ):
        if verbose>=2:
            print 'merging two dicts'
        for k,v in new.items():
            if verbose>=2:
                print 'merging key ',k
            # problem with this is that when inside a dict we WANT to merge non-allcaps stuff
            if (not allcaps or k==k.upper()) and ( doubleunderscore or not ( k.startswith('__') and k.endswith('__') )):
                if k in old:
                    if depth>0:
                        old[k] = merge_iter( new[k], old[k], allcaps, doubleunderscore,
                                             verbose=verbose, overwrite=overwrite, depth=depth)
                    elif overwrite:
                        old[k] = copy.deepcopy(new[k])
                else:
                    # FIXME: deepcopy faults on objects with unsafe attributes like __new__!
                    old[k] = copy.deepcopy(new[k]) # deepcopy in case the element is an object/dict, 
            elif verbose>=2:
                print 'key value ignored because it looks like a protected or non-user object'
                # don't do anythin with double underscore or mixed-case variables if not flagged to merge them
    # merge lists by unioning -- don't add duplicates
    elif isinstance( old, list ) and isinstance( new, iterable_type ): # and not isinstance( new, (str,unicode)):
        if isinstance(new,tuple):
            print 'merging a tuple into a list. list ='+repr(old)
            
        #TODO: convert to sets, append, then convert back to list?
        for i,v in enumerate(new):
            if verbose>=2:
                print 'merging list item',i
            # FIXME: the exact same object instance (e.g. dict) might not exist in the old
            #        but you still want to merge dicts rather than append a new dict
            if not v in old:
                if verbose>=2:
                    print 'appending list item',i
                old.append(v)
        if isinstance(new,tuple):
            print 'merged tuple into a list. list ='+repr(old)
    elif isinstance( old, tuple ) and isinstance( new, iterable_type ): # and not isinstance( new, (str,unicode)):
        #TODO: convert to sets, append, then convert back to list?
        print 'old tuple'+repr(old)
        for i,v in enumerate(new):
            if verbose>=2:
                print 'merging tuple item',i #,' value '+repr(v)
            # FIXME: the exact same object instance (e.g. dict) might not exist in the old
            #        but you still want to merge dicts rather than append a new dict
            #print type(new)
            if not v in old:
                if verbose>=2:
                    print 'appending the value'
                tmp = old + (v,) # WARN: tuple(v) would turn a str into a tuple of chars
                old = tmp
        print 'new tuple'+repr(old)
    # TODO: 4 DRY-up oportunities below
    elif isinstance( old, tuple) and isinstance( new, scalar_type ): # even though strings are a tuple of characters this shouldn't mess up
        if verbose>=2:
            print 'appending a scalar '+repr(v)+' to a tuple'
        #TODO: convert to sets, append, then convert back to list?
        tmp = old + (new,) # WARN: don't use tuple(new) because converts str to a tuple of chars, but parentheses (with comma) do not
        old = tmp
    elif isinstance( old, list ) and isinstance( new, scalar_type ):
        if verbose>=2:
            print 'appending a scalar to a list'
        #TODO: convert to sets, append, then convert back to list?
        old.append(new)
    elif isinstance( old, set ) and isinstance( new, scalar_type ):
        if verbose>=2:
            print 'adding a scalar to a set'
        #TODO: convert to sets, append, then convert back to list?
        old.add(new)
    elif isinstance( old, scalar_type ) and isinstance( new, scalar_type ):
        if verbose>=2:
            print 'replacing value '+repr(old)+' with value ' +repr(new)
        old = new # TODO: is it OK to change the old type in addition to its value?
    # FIXME: mismatched schemas (new and old elements not the same type and structure) may result in no change
    #print 'returning value '+repr(old)
    return old
 

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


