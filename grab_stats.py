#!/usr/bin/python
# Grab stats from the PAW Alliance, Nation and City APIs as well as scraping the actual website.
import urllib2
import datetime
import time
import json
# for extracting the latest indv
import os
import tarfile
import glob
import shutil
# For parsing a website
from bs4 import BeautifulSoup
# for Argument parsing
import argparse

## The rest of the arg parsing is at the bottom
##
try:
  debug = args.debug
except NameError:
  debug = False

### Some URLs we use
allianceapi = "http://politicsandwar.com/api/alliance/id="
alliancegameurl = "http://politicsandwar.com/alliance/id="
nationapi = "http://politicsandwar.com/api/nation/id="
cityapi = "http://politicsandwar.com/api/city/id="
alliancetop50pages = [ "http://politicsandwar.com/index.php?id=23&keyword=&cat=none&ob=score&od=DESC&backpage=%3C%3C&maximum=50&minimum=0", "http://politicsandwar.com/index.php?id=23&keyword=&cat=none&ob=score&od=DESC&gopage=%3E%3E&maximum=50&minimum=0" ]
top50nationspages = [ "http://politicsandwar.com/index.php?id=15&keyword=&cat=everything&ob=score&od=DESC&maximum=50&minimum=0&search=Go" ]
alliancesapi = "http://politicsandwar.com/api/alliances/"

## Used to add timestamps to the json data
epoch = datetime.datetime.utcfromtimestamp(0)
now=datetime.datetime.utcnow()
now2=str(datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S%Z'))
unix = (now - epoch).total_seconds()
# Counters and lists initialized
alliancedict = {}
nationdict = {}
top50nationsdict = {}
rowcounter = 0
apireqcounter = 0

# Without this header we get Error 403 (thank you stackoverflow)
hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}

# These are qouted numbers in the Alliance API - they end up as strings - but we want them as floats.
makethesefloats = [ "score", "members", "accepting members", "applicants", "gdp", "cities", "soldiers", "tanks", "aircraft", "ships", "missiles", "nukes", "treasures" ]

def getalliancedata():
  """
  Get alliance data and write to JSON
  """
  apireqcounter = 0

  # Get each alliance's data, insert some timestamps
  alliancesdict = getalliances2(100)
  if alliancesdict:
   for alliance in alliancesdict:
      fullallianceurl = allianceapi + str(alliance)
      if debug: print fullallianceurl
      req = urllib2.Request(fullallianceurl, headers=hdr)
      response = urllib2.urlopen(req)
      url = response.read()
      apireqcounter += 1
      try:
        data = json.loads(url)
        alliancename = data["name"]
        rank = alliancesdict[alliance]["rank"]
        avgscore = alliancesdict[alliance]["avgscore"]

        for key in data:
            if key in makethesefloats:
                try:
                  data[key] = float(data[key])
                except TypeError as e:
                  data[key] = float(0)
                  print "TypeError when floating key %s, maybe it is null. Setting to float(0)" % key
                  print "alliance: %s" % fullallianceurl

        data["timestamp"] = unix
        data["timestamp2"] = now2
        data["rank"] = rank
        data["avgscore"] = avgscore
        filename = outdir + "/alliance_" + str(alliance) + "_" + str(unix) + ".json"
        if out_to_json:
          with open(filename, 'a') as outfile:
            json.dump(data, outfile)
        time.sleep(sleeper)
      except ValueError:
        print "Error for alliance %s in getalliancedata()" % fullallianceurl
        continue
   return(0)
  else:
   return(1)


def getalliances2(num_alliances):
  # returns a dict with stats for the top num_alliances
  # {'623': {'avgscore': 1137.99, 'rank': 4, 'acronym': "GPA"}, '622': ... } 

  num_alliances = num_alliances
  req = urllib2.Request(alliancesapi, headers=hdr)
  response = urllib2.urlopen(req)
  url = response.read()
  data = json.loads(url)

  alliancedict = {}

  alliances = data["alliances"]
  for alliance in alliances:
    allianceid = alliance["id"]
    allianceurl = alliancegameurl + str(allianceid)
    rank = alliance["rank"]
    name = alliance["name"]
    try:
      members = alliance["members"]
    except KeyError as e:
      print "No member found for alliance with id %s, setting members to 0 and viewing that alliance to get rid of it" % alliance
      req_mem = urllib2.Request(allianceurl, headers=hdr)
      response_mem = urllib2.urlopen(req_mem)
      url_mem = response.read()
      print url_mem
      members = 0
    try:
      score = alliance["score"]
    except KeyError as e:
      print "No score found for alliance with id %s, setting score to 0 and viewing that alliance page to get rid of it" % alliance
      req_score = urllib2.Request(allianceurl, headers=hdr)
      response_score = urllib2.urlopen(req_score)
      url_score = response.read()
      print url_score
      score = 0
    avgscore = alliance["avgscore"]
    acronym = alliance["acronym"]
    if rank <= num_alliances:
        alliancedict[allianceid] = { "avgscore": avgscore, "rank": rank, "members": members, "score": score, "name": name, "acronym": acronym }

  return(alliancedict)

def getalliances():
  # Returns a dict of dicts, with key alliance IDs and rank and avgscore inside. 
  # Use getalliances2 function instead - it uses the API while this getalliances() scrapes the website
  # Parsed from http://politicsandwar.com/index.php?id=23&keyword=&cat=none&ob=score&od=DESC&backpage=%3C%3C&maximum=100&minimum=0
  # {'623': {'avgscore': 1137.99, 'rank': 4}, '622': ... } 

  for page in alliancetop50pages:
    req = urllib2.Request(page, headers=hdr)
    response = urllib2.urlopen(req)
    url = response.read()
    soup = BeautifulSoup(url)
    rowcounter = 0

    nationtable = soup('table')[0]
    table_rows = nationtable.findChildren('tr')
    for row in table_rows:
      rowcounter += 1
      cellcounter = 0
      cells = row.findChildren('td')
      for cell in cells:
         cellcounter += 1
         value = cell.string
         value = cell.string
         if cellcounter == 1:
           # RANK)
           rank = int(value.strip(")"))
         if cellcounter == 2:
           link = cell.find_all('a')
           URL = link[0].get('href')
           allianceid = URL.split('=')
         if cellcounter == 7:
           # Because American numbers..
           avgscore = float(value.replace(',', ''))
           try:
             alliancedict[allianceid[1]] = { "rank" : rank, "avgscore" : avgscore }
           except:
             print "could not add alliance with rank %s in getalliances()" % rank

  return(alliancedict)

def getmemberlist(alliancename):
  # takes the name of an alliance as argument and returns a dict of the ids of the nations in that alliance
  # looks in the first page and if there are more than 50 nations also read second page
  # https://politicsandwar.com/index.php?id=15&memberview=true&keyword=green+protection+agency&cat=alliance&ob=score&od=DESC&gopage=%3E%3E&maximum=50&minimum=0

  page1 = "http://politicsandwar.com/index.php?id=15&memberview=true&keyword=" + alliancename + "&cat=alliance&ob=score&od=DESC&backpage=%3C%3C&maximum=50&minimum=50"
  page2 = "http://politicsandwar.com/index.php?id=15&memberview=true&keyword=" + alliancename + "&cat=alliance&ob=score&od=DESC&gopage=%3E%3E&maximum=50&minimum=0"
  page3 = "http://politicsandwar.com/index.php?id=15&memberview=true&keyword=" + alliancename + "&cat=alliance&ob=score&od=DESC&gopage=%3E%3E&maximum=50&minimum=50"
  pages2 = [ page1, page2 ]
  pages3 = [ page1, page2, page3 ]
  whichpages = page1
  req = urllib2.Request(page1, headers=hdr)
  response = urllib2.urlopen(req)
  url = response.read()
  soup = BeautifulSoup(url)

  # <p style="text-align:center;">Showing 0-50 of 59 Nations</p>
  # make this an int, find all paragraphs, get the paragraph with index 2, get contents, split on of, second item, split on Nations, first item
  alliancemembers = int(soup.find_all('p')[2].string.split("of")[1].split("Nations")[0])
  if debug: print "%s members in %s" % (alliancemembers, alliancename)

  if alliancemembers > 100:
    whichpages = pages3
  elif alliancemembers > 50 and alliancemembers <= 100:
    whichpages = pages2
  else:
    whichpages = [ page1 ]

  if debug: print "whichpages: %s" % whichpages
  for page in whichpages:
    req = urllib2.Request(page, headers=hdr)
    response = urllib2.urlopen(req)
    url = response.read()
    soup = BeautifulSoup(url)

    rowcounter = 0

    nationtable = soup('table')[0]
    table_rows = nationtable.findChildren('tr')
    for row in table_rows:
      rowcounter += 1
      cellcounter = 0
      cells = row.findChildren('td')
      for cell in cells:
         cellcounter += 1
         value = cell.string
         if cell.string != None:
           value = cell.string
           if cellcounter == 1:
             # RANK)
             alliancerank = int(value.strip(")"))
             if debug: print alliancerank
         else:
           if cellcounter == 2:
             link = cell.find_all('a')
             URL = link[0].get('href')
             nationid = URL.split('=')[1]
             nationname = link[0].text
           if cellcounter == 7:
             # of defensive slots is in the title attribute of an image in the 7th and last column
             # Here we also populate the dictionary
             try:
               img = cell.find_all('img')
               try:
                 defslots = img[0].get('title').split(" ")[0]
               except IndexError:
                 defslots = 0
               nationdict[nationid] = { "defslots" : defslots, "alliancerank" : alliancerank, "name": nationname }
               #if debug: print defslots
             except:
               defslots = 0
               alliancerank = 0
               nationdict[nationid] = { "defslots" : defslots, "alliancerank" : alliancerank, "name": nationname }
               print "Could not find defensive slots or rank for %s, setting them to 0 - getmemberlist()" % URL

  return(nationdict)

def getnationdata(grabcitiesdata):
  """
  Get nation data out of all the nations in the alliance(s) chosen and write to JSON
  This function calls other functions, for example the getmemberlist() and getcitiesdata()
  Also add some values to the json, such as timestamp, timestamp2, projects, lowrange, toprange and defslots
  """
  apireqcounter = 0
  grabcitiesdata = grabcitiesdata

  # Taken from --alliance "alliance+name"
  for alli in chosen_alliance:
    if debug: print alli
    # TODO: There is _some_ inefficiency here. If chosen_alliance contains say two alliances, when it prints lenationdict the second time it contains the nations from both alliances.
    # Couldn't find why, and with file open append this caused the first alliance to have two json trees in one file. So changed file open to write instead..
    lenationdict = getmemberlist(alli)
    if lenationdict:
     if debug: print lenationdict
     for nation in lenationdict:
        fullnationurl = nationapi + str(nation)
        if debug: print fullnationurl
        req = urllib2.Request(fullnationurl, headers=hdr)
        response = urllib2.urlopen(req)
        url = response.read()
        apireqcounter += 1
        try:
          data = json.loads(url)
          nationname = data["name"]
          cityids = data["cityids"]
          score = float(data["score"])
          lowrange = score * 0.75
          toprange = score * 1.75
          try:
            iw = data["ironworks"]
            bw = data["bauxiteworks"]
            arms = data["armsstockpile"]
            egr = data["emgasreserve"]
            mi = data["massirrigation"]
            itc = data["inttradecenter"]
            mlp = data["missilelpad"]
            nrf = data["nuclearresfac"]
            irond = data["irondome"]
            vds = data["vitaldefsys"]
            cia = data["cenintagncy"]
            ue = data["uraniumenrich"]
            pb = data["propbureau"]
            cce = data["cenciveng"]
            data["projects"] = iw + bw + arms + egr + mi + itc + mlp + nrf + irond + vds + cia + ue + pb + cce
          except:
            print "could not sum projects for %s " % fullnationurl
            data["projects"] = 0

          data["timestamp"] = unix
          data["timestamp2"] = now2
          data["defslots"] = lenationdict[nation]["defslots"]
          # only two decimals
          data["lowrange"] = float("{0:.2f}".format(lowrange))
          data["toprange"] = float("{0:.2f}".format(toprange))

          filename = outdir + "/nation_" + str(nation) + "_" + str(unix) + ".json"
          if out_to_json:
            with open(filename, 'w') as outfile:
              json.dump(data, outfile)
          else:
            print data
          time.sleep(sleeper)
          if grabcitiesdata:
            getcitiesdata(cityids, nation)
        # ValueError: No JSON object could be decoded
        except ValueError as e:
          print "Some ValueError went wrong with nation %s in getnationdata() - %s" % (fullnationurl, e)
          continue
        except KeyError as e:
          print "Some KeyError went wrong with nation %s in getnationdata() - %s" % (fullnationurl, e)
          continue
     #return(apireqcounter)
     continue
    else:
     return(1)

def extract_members(extract_here,grabcitiesdata):
  """
  Gets the last indv_ file which we assume contain one alliance's members nation/city data and
  extract this to extract_here
  """

  grabcitiesdata = grabcitiesdata

  # newest points to the last file that matches the glob
  newest = max(glob.iglob('/var/www/paw/indv_*.tar.gz'), key=os.path.getctime)

  if not os.path.exists(extract_here):
    print "uh, %s does not exist" % extract_here
    return(128)

  tar = tarfile.open(newest)
  tar.extractall(path=extract_here)
  tar.close()

  # at this stage they are in extract_here/tmp/tmp.randomstring/*.json
  # move them to extract_here
  temp_gpa_path="%s/tmp/tmp.*/*.json" % extract_here
  if debug: print temp_gpa_path
  for filename in glob.glob(temp_gpa_path):
    # if --cities then do not move alliance_ files
    if grabcitiesdata:
      if "alliance_" not in filename:
        if debug: print filename
        shutil.move(filename, extract_here)
    else:
    # if --cities is not passed, only move nation_ files
      if "nation_" in filename:
        if debug: print filename
        shutil.move(filename, extract_here)

  return(127)


def getcitiesdata(cityids, nationid):
  """
  Take cityids and nationid in a list as input and writes cities data to JSON for those cities
  Also makes a copy of the data.citydata called data.nationdata - easier to do filtering if one can just say data.nationdata.leadername
  """
  cityids = cityids
  nationid = nationid
  apireqcounter = 0

  for cityid in cityids:
   fullcityurl = cityapi + str(cityid)
   req = urllib2.Request(fullcityurl, headers=hdr)
   try:
     response = urllib2.urlopen(req)
   except urllib2.HTTPError, error:
     #print "ERROR trying again: ", error.read()
     print "ERROR: error grabbing http in getcitiesdata() for city %s trying again" % fullcityurl
     response = urllib2.urlopen(req)
   url = response.read()
   apireqcounter += 1
   try:
     data = json.loads(url)
# 20160109 the citydata or data was removed
     data["timestamp"] = unix
     data["timestamp2"] = now2
     data["nationid"] = nationid
     filename = outdir + "/city_" + str(cityid) + "_" + str(nationid) + "_" + str(unix) + ".json"
#     data["nationdata"] = data["citydata"]
     if out_to_json:
       with open(filename, 'a') as outfile:
            json.dump(data, outfile)
     time.sleep(sleeper)
   except ValueError:
     print "Something wrong with json data for city %s in getcitiesdata()" % fullcityurl
     continue
  return(apireqcounter)

def gettop50nations():
  # Returns a dict of dicts, with key nation IDs : ranks and defslots
  # Parsed from top50nationspages = [ "https://politicsandwar.com/index.php?id=15&keyword=&cat=everything&ob=score&od=DESC&maximum=50&minimum=0&search=Go" ]
  # {'8360': {'defslots': '3', 'rank': 33}, '3805': {'defslots': '3', 'rank': 34},  ...

  for page in top50nationspages:
    if debug: print "TOP50"
    req = urllib2.Request(page, headers=hdr)
    response = urllib2.urlopen(req)
    url = response.read()
    soup = BeautifulSoup(url)
    rowcounter = 0

    nationtable = soup('table')[0]
    table_rows = nationtable.findChildren('tr')
    for row in table_rows:
      rowcounter += 1
      cellcounter = 0
      cells = row.findChildren('td')
      for cell in cells:
         cellcounter += 1
         value = cell.string
         value = cell.string
         if cellcounter == 1:
           # RANK)
           rank = int(value.strip(")"))
         if cellcounter == 2:
           link = cell.find_all('a')
           URL = link[0].get('href')
           nationid = URL.split('=')
         if cellcounter == 7:
           img = cell.find_all('img')
           try:
             defslots = img[0].get('title').split(" ")[0]
           except IndexError:
             # no image if there are no free defslots..
             defslots = 0
           try:
               top50nationsdict[nationid[1]] = { "rank" : rank, "defslots" : defslots, "url": URL }
           except:
             print "could not add nation with rank %s to top50" % rank

  nationids = []
  for id in top50nationsdict:
    nationids.append(id)

  return(top50nationsdict)


def getdatafromlistofnations():

  """
  Takes a dict of nations (with id as keys)
  """

  nationdict = gettop50nations()
  apireqcounter = 0

  if debug: print nationdict

  if nationdict:
   for nation in nationdict:
      fullnationurl = nationapi + str(nation)
      #if debug: print fullnationurl
      req = urllib2.Request(fullnationurl, headers=hdr)
      response = urllib2.urlopen(req)
      url = response.read()
      apireqcounter += 1
      try:
        data = json.loads(url)
        nationname = data["name"]
        cityids = data["cityids"]
        score = float(data["score"])
        lowrange = score * 0.75
        toprange = score * 1.75
        try:
          iw = data["ironworks"]
          bw = data["bauxiteworks"]
          arms = data["armsstockpile"]
          egr = data["emgasreserve"]
          mi = data["massirrigation"]
          itc = data["inttradecenter"]
          mlp = data["missilelpad"]
          nrf = data["nuclearresfac"]
          irond = data["irondome"]
          vds = data["vitaldefsys"]
          cia = data["cenintagncy"]
          ue = data["uraniumenrich"]
          pb = data["propbureau"]
          cce = data["cenciveng"]
          data["projects"] = iw + bw + arms + egr + mi + itc + mlp + nrf + irond + vds + cia + ue + pb + cce
        except:
          print "could not sum projects for %s " % fullnationurl
          data["projects"] = 0

        data["timestamp"] = unix
        data["timestamp2"] = now2
        data["defslots"] = nationdict[nation]["defslots"]
        # only two decimals
        data["lowrange"] = float("{0:.2f}".format(lowrange))
        data["toprange"] = float("{0:.2f}".format(toprange))

        filename = outdir + "/nation_" + str(nation) + "_" + str(unix) + ".json"
        if out_to_json:
          with open(filename, 'a') as outfile:
            json.dump(data, outfile)
        else:
          print data
        time.sleep(sleeper)
        if grabcitiesdata:
          getcitiesdata(cityids, nation)
      # ValueError: No JSON object could be decoded
      except ValueError as e:
        print "Some ValueError went wrong with nation %s in getnationdata() - %s" % (fullnationurl, e)
        continue
      # except KeyError as e:
      #   print "Some KeyError went wrong with nation %s in getnationdata() - %s" % (fullnationurl, e)
      #   continue

  return(apireqcounter)

############################

if __name__ == "__main__":

  ## arg parsing
  parser = argparse.ArgumentParser(description='Make JSON from PAW')
  parser.add_argument('--version', action='version', version='%(prog)s 1.0')
  parser.add_argument('--outdir', metavar='out', type=str, nargs='+',
                     help='Where to store the JSON', required=True)
  parser.add_argument('--cities', action='store_true',
                     help='Grab cities data', required=False, default=False)
  parser.add_argument('--sleep', metavar='sleep', type=float, nargs='+',
                     help='How long to sleep in seconds between requests', required=True)
  parser.add_argument('--top50', action='store_true',
                     help='Grab the top50 too', required=False, default=False)
  parser.add_argument('--debug', action='store_true',
                     help='Enable Debug?', required=False, default=False)
  parser.add_argument('--alliance', metavar='chosen_alliance', type=str, nargs='+',
                     help='Which alliance(s) to get all the member details from. Like alliance1,alliance+with+spaces', required=False)
  parser.add_argument('--extract', action='store_true',
                     help='Extract last tar ball with json from /var/www/paw/indv_*.tar.gz to outdir too', required=False, default=False)
  parser.add_argument('--merge', action='store_true',
                     help='Merges extracted and newly gathered data', required=False, default=False)
  parser.add_argument('--json', action='store_true',
                     help='Set this to false to not write to .json files', required=False, default=False)

  args = parser.parse_args()
  outdir = args.outdir[0]
  grabcitiesdata = args.cities
  sleeper = args.sleep[0]
  debug = args.debug
  if debug: print "debug: %s" % debug
  top50 = args.top50
  if debug: print "top50: %s" % top50
  # This is because we assume the syntax is --alliance "alliance1,alliance+with+spaces"
  # argparse makes it one entry in a list
  if args.alliance:
    chosen_alliance = args.alliance[0].split(",")
  else:
    chosen_alliance = ""
  extract = args.extract
  merge = args.merge
  out_to_json = args.json


  if debug:
  #   print getmemberlist("Some+other+alliance")
  #   extract_members("/tmp/path/")
    getnationdata(grabcitiesdata)
    extract_members(outdir,grabcitiesdata)
  #  print getalliances()
#    print getalliancedata()
  #  print getalliances2(100)
  #   print getcitiesdata(["10614"], 674)
  #   print getdatafromlistofnations()

  # python grab_stats.py --outdir /tmp/one_and_other_alliances --cities --sleep 0.1 --alliance "not+gpa,also+not+gpa" --merge --extract
  elif chosen_alliance == "" and top50:
    getdatafromlistofnations()
  elif merge:
    getnationdata(grabcitiesdata)
    extract_members(outdir,grabcitiesdata)

  else:
    if top50:
      getalliancedata()
    getnationdata(grabcitiesdata)
else:
  chosen_alliance = "Alliance+of+Admins+and+Mods"
