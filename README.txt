DEVELOP
-------

1. Install python
    Linux: `sudo aptitude install python`
    Windows: you're on your own
2. Install git from 
    Linux: `sudo aptitude install git`
    Windows: `http://msysgit.googlecode.com/files/Git-1.7.9-preview20120201.exe`
3. Launch a command prompt
    Linux: <CTRL><ALT>T
    Windows: Start->Run->"Cmd" in Windows
4. `cd directory_where_you_want_to_put_the_source_code`
5. `git clone git@bitbucket.org:hobsonlane/bitpart.git`
6. hack away
7. `git push -u origin master`

INSTALL
-------

1. Download the latest master zip file https://bitbucket.org/hobsonlane/bitpart/get/master.zip
Unzip and place all files in the same directory (preferably within a directory listed in your PYTHONPATH variable).

You may want to edit line 54 in bitcrawl.py default path to point to an appropriate file/path on your computer:

    FILENAME='/home/hobs/Notes/notes_repo/bitcoin trend data.json' # change this to point to a path on your computer that you'd like to use to store data

RUN
---

From the command line (terminal) prompt type:

python bitcrawl.py --path output_file.json --verbose


DOCUMENTATION
-------------

python bitcrawl.py --help

