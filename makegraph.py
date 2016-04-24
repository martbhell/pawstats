#!/usr/bin/python

# extract latest indv_*.tar.gz file
# 2
# load all the alliance*.json
# list top 20 alliances and each soldiers/tanks/aircrafts over time
# make graph

# These are used to extract and remove the archive
import os
import glob
import tarfile
import shutil
# These are to play with the json
import json
import datetime
# Because dicts are unordered
import collections
# Because we only grab last x days files
import time

#######
version = "1.0"
datafields = [ "cities", "score", "soldiers", "tanks", "aircraft", "allianceid", "members", "ships", "missiles", "nukes", "treasures" ]
files = glob.glob('/var/www/paw/indv_*.tar.gz')
newpath = '/tmp/pawtempgraph' 

debug = False

days_back = 50
now = time.time()

def setup_cleanup():
  # call this function before and after
  if not os.path.exists(newpath):
      os.makedirs(newpath)

  # clean it out
  shutil.rmtree(newpath)

def extract_the_files():
  # call this after cleaning up
  counter = 0
  for file in files:
    # if file is older than days_back then skip
    if os.stat(file).st_mtime < now - days_back * 86400:
        continue
    counter += 1
    #if counter % 10 == 0:
    if counter % 2 == 0:
      if debug: print file
      tar = tarfile.open(file)
      tar.extractall(path=newpath)
      tar.close()

def alliancedata():

  alliancedict = {}
  sorted_alliancedict = {}
  onlyallianceandscore = {}
  top20data = {}
  #counter = 0

  filelist = glob.glob("/tmp/pawtempgraph/*/*/alliance*.json")
  for f in filelist:
    #print f
# so over time the JSON API Has changed x times
    with open(f) as jsonfile:
      data = json.load(jsonfile)
#      print data
      try:
        name = data["data"]["alliancedata"]["name"]
      except KeyError:
        try:
          name = data["alliancedata"]["name"]
        except KeyError:
          name = data["name"]
      try:
        score = int(data["data"]["alliancedata"]["score"])
      except KeyError:
        try:
          score = int(data["alliancedata"]["score"])
        except KeyError:
          score = int(data["score"])
       # timestamp can be in 3 places..
      try:
        timestamp = data["timestamp2"]
      except:
        try: 
          timestamp = data["data"]["timestamp2"]
        except:
          if debug:
            print "data: %s" % data
            print "file: %s" % f
          timestamp = data["data"]["alliancedata"]["timestamp2"]

      ##
      # first make a dict with all the alliances and each score
      # make an ordereddict of the top 20 alliances - sort by score
      onlyallianceandscore.update({ name: score })
      sorted_alliances = collections.OrderedDict(sorted(onlyallianceandscore.items(), key=lambda t: t[1]))
      ##
      """ 3rd attempt at data organization:
      { "soldiers":  
         { "gpa": 
            { "2015-11-01": 123, "2015-11-02": 22 },   
           "upn":  
           { "2015-11-02": 44, "2015-11-03": 45 } },
       "tanks":  
         { "gpa": 
            { "2015-11-01": 12 }, 
           "upn": 
            { "2015-11-02": 125 } } }
      """
      ##
      try:
        for field in datafields:
          try:
            alliancedict[field][name].update({ timestamp: data[field] })
          except:
            try: 
              alliancedict[field][name].update({ timestamp: data["alliancedata"][field] })
            except:
              try: 
                alliancedict[field][name].update({ timestamp: data["data"]["alliancedata"][field] })
              except:
                try:
                  alliancedict[field][name].update({ timestamp: data["data"][field] })
                except KeyErrors as e:
                  if debug:
                    print "errors abound!!: %s" % e
                    print "data: %s" % data
                    print "field: %s name: %s" % (field,name)
            #this for loop turns into this: alliancedict["cities"]["Green Protection Agency"].update({ timestamp: data["alliancedata"]["cities"] })
      except:
        try:
          alliancedict[field][name] = {}
        except:
          alliancedict[field] = {}

  if debug: print "alliancedict:"
  if debug: print alliancedict

  # Sort it and put only top20 alliances based on score
  top20_alliances=sorted(sorted_alliances, key=sorted_alliances.get, reverse=True)[:20]

  for field in datafields:
     top20data[field] = collections.OrderedDict()
#     print field
     for alliance in top20_alliances:
       top20data[field][alliance] = collections.OrderedDict()
#       print alliancedict[field]
       data = alliancedict[field][alliance]
       if alliance in top20_alliances:
         top20data[field][alliance] = collections.OrderedDict(sorted(data.items()))

  return(top20data)

###
  
def makejson(thefield):

  top20data = alliancedata()
  alliancelist = []
  fivealliances = []

  outdir = "/var/www/paw_alliance/"

  data = []

  now=str(datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S%Z'))

  num_alliances = len(top20data[thefield])
  max_five = 0
  counter = 0
  
  for alliance in top20data[thefield]:
      #print max_five - more than 5 plots in one graph makes the graph hard to read
      if max_five <= 5:
        data2 = []
        alliance_no_spaces = alliance.replace(" ", "_")
        if alliance_no_spaces not in alliancelist:
           alliancelist.append(alliance_no_spaces)
           fivealliances.append({ max_five : alliance_no_spaces })
        for date in top20data[thefield][alliance]:
           data2.append({ "date": date, "value": top20data[thefield][alliance][date], "alliance": alliance_no_spaces })
        data.append(data2)
      max_five += 1
      if max_five == 5:
	filename = outdir + thefield + "_" + str(counter) + ".json"
	with open(filename, 'w') as outfile:
	    json.dump(data, outfile)
        # also save which alliances are in this file
	filename = outdir + thefield + "_" + str(counter) + "_alliances" ".json"
	with open(filename, 'w') as outfile:
	    json.dump(fivealliances, outfile)
        #### if we arrive here, reset
        data = []
        fivealliances = []
        max_five = 0
        counter += 1
          

def writegraphs():

  # call this after extract
  for field in datafields:
     makejson(field)

####################

setup_cleanup()
extract_the_files()
writegraphs()
setup_cleanup()
