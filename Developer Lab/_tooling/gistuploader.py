#!/usr/bin/env python3
import devlabmanager
import pathlib
from pprint import pprint
import sys
import os
import requests
import json

class GistManager(object):
    def __init__(self, ConfigManager):
        home = str(pathlib.Path.home()) #home directory
        tokenlocation = os.path.join(home,".gist.token")
        if os.path.exists(tokenlocation):
            token = open(tokenlocation,"r").read()
        else:
            raise Exception("Can't find the token file at " + tokenlocation)
        
        self.username = "Hribek25"
        self.token = token
        self.BASE_URL = 'https://api.github.com'
        self.GIST_URL = 'https://gist.github.com'
        self.header = { 'X-Github-Username': self.username,
						'Content-Type': 'application/json',
						'Authorization': 'token %s' % self.token
					  }
            

    def ListAllGists(self):
        r = requests.get('%s/users/%s/gists' % (self.BASE_URL, self.username),
			headers=self.header)
        pprint(vars(r))
        return json.loads(r.text)

    def CreateGist(self):
        url = '/gists'
        data = {"description": "some description",
                "public": True,
  				"files": {"IOTA101_dtergsasdfdfg345234.js": {"content": "//some ssdgsfgource code"},
                          "IOTA101_asfsafasfd.js": {"content": "//some fgsdgsdgsource code"}
                          }   
  		        }
        r = requests.post('%s%s' % (self.BASE_URL, url),
			data=json.dumps(data),
			headers=self.header)
        if (r.status_code == 201):
            pprint(vars(r))
            return json.loads(r.text)
        else:
            pprint(vars(r))

def main():
    try:
        rootDir = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               "..%s..%s" % (os.path.sep, os.path.sep))
        cfg = devlabmanager.ConfigManager(rootDir)
        
    except Exception as e:
        pprint(e)
        return 1   
    print("Searching for config.json files...DONE")

    gm = GistManager(cfg)
    #pprint(gm.ListAllGists())
    pprint(gm.CreateGist())
        

if __name__ == "__main__":
    sys.exit(int(main() or 0))
   

