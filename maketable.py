#!/usr/bin/python
# Version 1.0
#
# extract latest indv_*.tar.gz file
# load all the nation*.json
# list all the nations, # of cities and military troops, etc
# make table
# Uses http://www.kryogenix.org/code/browser/sorttable/

# These are used to extract and remove the archive
import os
import glob
import tarfile
import shutil
import time
# These are to play with the json
import json
import datetime

#######
# datafields are the json fields we put in the table
datafields = [ "cities", "score", "soldiers", "tanks", "aircraft", "nationid", "leadername", "minutessinceactive", "nationrank", "ships", "missiles", "nukes", "irondome", "projects", "allianceposition", "color" ]
# newest points to the last file that matches the glob
newest = max(glob.iglob('/var/www/paw/indv_*.tar.gz'), key=os.path.getctime)
# alliance_list is a list of the allianceids we put into the graph
# the data of this alliance must of course be available first
alliance_list = [ 624 ]

days_back = 50

debug = False
now = time.time()

def nationdata():

  nationdict = {}

  newpath = '/tmp/pawtemp' 
  if not os.path.exists(newpath):
      os.makedirs(newpath)

  tar = tarfile.open(newest)
  tar.extractall(path="/tmp/pawtemp")
  tar.close()

  filelist = glob.glob("/tmp/pawtemp/*/*/nation*.json")
  for f in filelist:
    if debug:
      print f
    with open(f) as jsonfile:
      data = json.load(jsonfile)
      name = data["name"]
      alliance_id = int(data["allianceid"])

      if alliance_id in alliance_list:
        nationdict[name] = { "name": data["name"] }
        for field in datafields:
    #      print field
          try: 
  	    nationdict[name].update({ field: data[field] })
          except:
  	    print "update for %s and %s problem" % (name, field)

  shutil.rmtree(newpath)
  return(nationdict)
  
def maketable():

  NATIONS = nationdata()

  now=str(datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S%Z'))

  print "<html>"
  print '<meta name="theme-color" content="green">'
  print "Generated at UTC: %s with data from %s" % (now,newest.split("/")[4])
  print("""
  <style>
  table.sortable tbody tr:nth-child(even) td {
    background-color: #b4e790;
  }
  table.sortable thead {
    background-color:#78AB46;
    color:#000;
    font-weight: bold;
    cursor: default;
  }</style>
  """)

  print '<script src="sorttable.js"></script>'
  print '<table border=0 class="sortable">'

  print "<th> </th>"
  for field in datafields:
    if field == "projects":
      print "<th> <a title='iw + bw + arms + egr + mi + itc + mlp + nrf + irond + vds + cia + ue + pb + cce'>%s</a> </th>" % field
    else:
      print "<th> %s </th>" % field

  for row in NATIONS:
    print " <tr>"
    print "  <td> %s </td>" % row
    for field in datafields:
      if field == "nationid":
        print "  <td> <a href='https://politicsandwar.com/nation/id=%s'> %s </a> </td>" % (NATIONS[row][field],NATIONS[row][field])
      elif field == "allianceposition":
        if NATIONS[row][field] == 1:
          print "  <td> applicant </td>"
        elif NATIONS[row][field] == 2:
          print "  <td> member </td>"
        elif NATIONS[row][field] == 3:
          print "  <td> director </td>"
        elif NATIONS[row][field] == 5:
          print "  <td> triumvir </td>"
        else:
          print "  <td> %s </td>" % NATIONS[row][field]
      else:
        print "  <td> %s </td>" % NATIONS[row][field]
    print " </tr>"
  print "</table>"
  print "</html>"

#####

maketable()
