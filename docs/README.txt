========
bitcrawl
========

Crawl the Internet extracting and logging numbers associated with the keyword "bitcoin" and calculate statistics on that historical data for trendign and forecasting.

Bitcrawl is a coding contest submission for the Udacity CS101 class. See http://udacity.com for free university-level online classes. They are short and sweet and highly-educational, even for experienced coders and robotics engineers. The contest rules can be found at:

    http://www.udacity.com/file?file_key=agpzfnVkYWNpdHl1ckYLEgZDb3Vyc2UiBWNzMTAxDAsSCUNvdXJzZVJldiIHZmViMjAxMgwLEgRVbml0GNEPDAsSDEF0dGFjaGVkRmlsZRj54yUM

Copyright (c) 2012 Hobson Lane and distributed under the [[Creative Commons BY-SA License|http://creativecommons.org/licenses/by-sa/3.0/]]

DEVELOP
=======

1. Launch a command prompt
   
   * Linux: <CTRL><ALT>T
   * Windows: Start->Run->"Cmd" in Windows
   
2. Install python
   * Linux: `sudo aptitude install python`
   * Windows: you're on your own

3. Install git
   
   * Linux: `sudo aptitude install git`
   * Windows: `http://code.google.com/p/msysgit/downloads/list?q=full+installer+official+git`

3.5 Check git from command line -type >git- help

3.6 Generate SSh key from Git Bash console into your local computers .ssh folder

3.7 copy ssh key form local machine and paste it in the Bitbucket web page accounts- ssh keys list
   
4. `cd directory_where_you_want_to_put_the_source_code`

5. `git clone git@bitbucket.org:hobsonlane/bitpart.git`

6. Hack, hack, hack...

7. Update your local repository to record your hack:
   
   `git commit -a -m 'Notes about what you changed'`
   
8. Share your changes with the team:
   
   `git push -u origin master`
   

INSTALL
-------

1. Download the latest master zip file https://bitbucket.org/hobsonlane/bitpart/get/master.zip
2. Unzip and place all files in the same directory (preferably within a directory listed in your PYTHONPATH variable).
3. You may want to edit the FILENAME = ... line in bitcrawl.py to point to an appropriate file/path on your computer:

    `FILENAME=os.path.expanduser('~/bitcrawl_historical_data.json')` # change this to a path you'd like to use to store data

RUN
---

From the command line (terminal) prompt type:

    `python bitcrawl.py`

or

    `python bitcrawl.py --help`

or

    `python bitcrawl.py --path bitpart_historical_data.json --verbose`


DOCUMENTATION
=============

Check out the built-in documentation:
    
    `python bitcrawl.py --help`
    
Or the bitbucket wiki:
    
    https://bitbucket.org/hobsonlane/bitpart/wiki/
    
Or our website (coming soon):

    totalgood.com/bitpart
    
Or this README.txt file (but you already know that)

GOALS
=====

