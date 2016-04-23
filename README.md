pawstats
--------

Game URL: https://politicsandwar.com/

grab_stats.py
-------------

 - grab_stats.py #
  - grab data from the game's API or web servers and store in .json files 
  - inject some useful stuff into the files like timestamps for when they were gathered

Arguments:
<pre>
$ python grab_stats.py --help
usage: grab_stats.py [-h] [--version] --outdir out [out ...] [--cities]
                     --sleep sleep [sleep ...] [--top50] [--debug]
                     [--alliance chosen_alliance [chosen_alliance ...]]
                     [--extract] [--merge] [--json]

Make JSON from PAW

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --outdir out [out ...]
                        Where to store the JSON
  --cities              Grab cities data
  --sleep sleep [sleep ...]
                        How long to sleep between requests
  --top50               Grab the top50 too
  --debug               Enable Debug?
  --alliance chosen_alliance [chosen_alliance ...]
                        Which alliance to get all the member details from.
                        Like alliance1,alliance+with+spaces
  --extract             Extract members to outdir too
  --merge               Merge
  --json                Set this to false to not write to .json files
</pre>

Example usage - put this in a bash script:
<pre>
#!/bin/bash
scriptdir="$HOME/pawstats"
tmpdir=$(mktemp -d)
python $scriptdir/grab_stats.py --outdir $tmpdir --cities --sleep 1.00 --top50 --alliance "your+alliance+name+here" --json
</pre>

Then go look in $tmpdir - there will be lots of json files.

Author Information
------------------
