#!/usr/bin/env python3
import devlabmanager
import pathlib
from pprint import pprint
import sys
import os
import requests
import json
import nbformat
import binascii
import re
import io

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
        #pprint(vars(r))
        if (r.status_code == 200):
            return json.loads(r.text)
        else:
            raise Exception(r.text)

    def DeleteAllGists(self):
        try:
            g = self.ListAllGists()
        except Exception as e :
            pprint (e)
            return
        
        # cycle thru all gists
        print("Found %s Gist items..." % len(g))
        for i in g:
            filename = next(iter(i["files"].values()))["filename"] #first filename
            if filename.startswith("IOTA101"):
                url = '/gists/%s' % i["id"]      

                r = requests.delete('%s%s' % (self.BASE_URL, url),
			    headers=self.header)
                if (r.status_code == 204):
                    #pprint(vars(r))
                    print("Gist was deleted: " + i["description"] + "; " + filename)
                else:
                    print("Gist can't be deleted: " + i["description"] + "; " + filename)
                    pprint(r.text)           

    def GetGist(self, GistID):
        url = '/gists/%s' % GistID        
        r = requests.get('%s%s' % (self.BASE_URL, url),
			headers=self.header)
        if (r.status_code == 200):
            #pprint(vars(r))
            return json.loads(r.text)
        else:
            raise Exception(r.text)

    def CreateGist(self, FileName, Description, Content):
        url = '/gists'
        data = {"description": Description,
                "public": True,
  				"files": {FileName: {"content": Content}
                          }   
  		        }
        r = requests.post('%s%s' % (self.BASE_URL, url),
			data=json.dumps(data),
			headers=self.header)
        if (r.status_code == 201):
            #pprint(vars(r))
            return json.loads(r.text)
        else:
            raise Exception(r.text)

    def EditGist(self, GistID, FileName, Description, Content):
        url = '/gists/%s' % GistID
        data = {"description": Description,
                "public": True,
  				"files": {FileName: {"content": Content}
                          }   
  		        }
        r = requests.patch('%s%s' % (self.BASE_URL, url),
			data=json.dumps(data),
			headers=self.header)
        if (r.status_code == 200):
            #pprint(vars(r))
            return json.loads(r.text)
        else:
            raise Exception(r.text)

class GistBridgeManager(object):
    def __init__(self, ConfigManager):
        self._cfg = ConfigManager

    def UpdateGists(self):
        TplDescription = "The snippet is a part of the IOTA Developer Essentials project. You can reach it at https://hribek25.github.io/IOTA101/"
        TplReference = "Complete description and story behind the snippet is available at: %s"
        baseurl = "https://hribek25.github.io/IOTA101/"
        TplntbFileName = devlabmanager.ConfigManager.TplntbFileName
        TplhtmlFileName = devlabmanager.ConfigManager.TplhtmlFileName
        TplGistFileName = "IOTA101_%s"
        TplNoCodeSnippet = "No code snippet available for the selected language"
    
        gistmap = self._cfg.GetGistMap() # the full gist mapping and storage
        if gistmap["content"] is None:
            print("Configuration gist_map.json file is needed!")
            return 1
    
        notebooksdir = self._cfg.GetPathTargetNotebooks()    
        languages = self._cfg.GetAllLanguages()
        gistMan = GistManager(self._cfg)

        #gistMan.DeleteAllGists()
        #return 1

        CodeSnippetTitles = {} #storage for all code snippet titles


        for l in languages:
            p = os.path.join(notebooksdir,TplntbFileName % l)
            if os.path.exists(p): # I found a notebook
                with io.open(p, 'r', encoding='utf-8') as f:
                    inputNtb = nbformat.read(f, as_version=4) # reading the given notebook                
                NotebookLanguageMetaData = {key: inputNtb["metadata"][key]  for key in inputNtb["metadata"] if key=="kernelspec" or key=="language_info"} # info regarding the target lingo
        
            commentline = None
            extension = None
            language = NotebookLanguageMetaData["kernelspec"]["language"]
            print("Processing... " + p + " for " + language)

            if language=="javascript":
                commentline = "// %s"
                extension = ".js"
            if language=="python":
                commentline = "# %s"
                extension = ".py"

            if commentline is None or extension is None:
                print("Can't find a comment pattern / extension for the given language: " + NotebookLanguageMetaData["kernelspec"]["language"])
                return 1
        

            for c in inputNtb.cells: #let's go thru the notebook code cells
                # is it the correct code snippet? - only standalone ones of course
                if c["cell_type"]=="code" and "iotadev" in c["metadata"] and "codeid" in c["metadata"]["iotadev"] and "standalone" in c["metadata"]["iotadev"] and c["metadata"]["iotadev"]["standalone"]=="true": 
                    codeid = c["metadata"]["iotadev"]["codeid"]
                    rawcode = "".join(c["source"])                
                    requirements = "" # those are requirements generated based on the source code
                
                    # DESCRIPTION
                    requirements += commentline % TplDescription + os.linesep #let's move some detailed description as a part of the code

                    # REFERENCE
                    reference = baseurl + TplhtmlFileName % language + "#" + codeid
                    reference = TplReference % reference
                    requirements += commentline % reference + os.linesep

                    title = ""
                    # TITLE
                    if "title" in c["metadata"]["iotadev"]:
                        title = c["metadata"]["iotadev"]["title"]
                        if not codeid in CodeSnippetTitles: #let's store code title  for all languages
                            CodeSnippetTitles[codeid] = title
                    else: # title is not in metadata
                        if codeid in CodeSnippetTitles: #title is in temp storage for titles
                            title = CodeSnippetTitles[codeid]
                
                    for r in gistmap["content"]["languages"][language]["requirements"]:
                        if re.search(pattern=r["regexp"], string=rawcode): # if it matches then let's include some requirements
                            requirements += r["content"] + os.linesep

                    if requirements!="":
                        rawcode = requirements + os.linesep + rawcode
                    checksum = str(binascii.crc32(bytearray(rawcode, "utf-8"))) #let's calculate checksum to check whether there are changes or not
                
                    gistfilename = TplGistFileName % codeid + extension
                    gistdescription = title
                
                    # was it already created in gist?
                    if rawcode.find(TplNoCodeSnippet) == -1: # no valid snippet here - skipping
                        if codeid in gistmap["content"]["languages"][language]["snippets"]: # yes, it should be already in Gist
                            # check whether it was the same code - based on content and description
                            if gistmap["content"]["languages"][language]["snippets"][codeid]["checksum"]!=checksum or gistmap["content"]["languages"][language]["snippets"][codeid]["description"]!=gistdescription : # it seems it has been changed
                                # EDITING GIST
                                try:
                                    gistMan.EditGist(GistID=gistmap["content"]["languages"][language]["snippets"][codeid]["gistid"],
                                                 FileName=gistfilename,
                                                 Description=gistdescription,
                                                 Content=rawcode)
                                    # let's update also local storage
                                    gistmap["content"]["languages"][language]["snippets"][codeid] = {"gistid":gistmap["content"]["languages"][language]["snippets"][codeid]["gistid"],
                                                                                                "checksum": checksum,
                                                                                                "html_url": gistmap["content"]["languages"][language]["snippets"][codeid]["html_url"],
                                                                                                "description": gistdescription}
                                    print("Already published Gist was updated: " + gistfilename)

                                except Exception as e :
                                    print("Something went wrong while editing Gist: " + gistfilename)
                                    pprint(e)                                                  
                        
                        
                            else: # it should be already in Gist and nothing has changed - checksum is the same
                                print("Published Gist was skipped - no changes: " + gistfilename) # TODO: be paranoid and doublecheck the snippet is really there
                        else: # it does not seem the code is in Gist
                            # CREATING GIST
                            try:
                                created = gistMan.CreateGist(FileName=gistfilename,
                                                        Description=gistdescription,
                                                        Content = rawcode)
                                print("New gist was created: " + gistfilename)
                                # let's add the snippet to the main storage
                                gistmap["content"]["languages"][language]["snippets"][codeid] = {"gistid":created["id"],
                                                                                                "checksum": checksum,
                                                                                                "html_url": created["html_url"],
                                                                                                "description": gistdescription}
                            except Exception as e :
                                print("Something went wrong while creating Gist: " + codeid + " for " + language)
                                pprint(e)
                    else:
                        print("Snippet was skipped - probably N/A: " + gistfilename)


def main():
    # Running it as a standalone app
    try:
        rootDir = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               "..%s..%s" % (os.path.sep, os.path.sep))
        cfg = devlabmanager.ConfigManager(rootDir)        
    except Exception as e:
        pprint(e)
        return 1   
    print("Searching for config.json files...DONE")
    
    manager = GistBridgeManager(cfg)
    manager.UpdateGists()

    gistmap = cfg.GetGistMap()

    # let's update gist_map.json file - it has been probably changed
    if os.path.exists(os.path.join(gistmap["dir"],"gist_map.json")):
        open(os.path.join(gistmap["dir"],"gist_map.json"),"w").write(json.dumps(gistmap["content"]))
        print("gist_map.json file was updated...")
           

    #gm = GistManager(cfg)
    #pprint(gm.ListAllGists())
    #pprint(gm.CreateGist())
        

if __name__ == "__main__":
    sys.exit(int(main() or 0))
   

