#!/usr/bin/env python3
import json
import sys
import nbformat
import os
import io
from pprint import pprint
from nbconvert import HTMLExporter


class ConfigManager(object):
    
    def __init__(self, RootDirectory):
        if not RootDirectory:
            raise ValueError("RootDirectory is empty!")
                
        self._RootDirectory = RootDirectory
        self._ConfigSources = {
            "languagenotebookdestination":{"dir":"","content":None},
            "iotatextbooks":{"dir":"","content":None},
            "htmldestination":{"dir":"","content":None},
            "codebaselanguages":{"dir":"","content":None}
            }
        self._SearchForConfigFiles() # are all config files in place?
        nondetected = False
        for key in self._ConfigSources:
            if self._ConfigSources[key]["content"] is None:
                print("Can't load config file for " + key)
                nondetected=True
        if nondetected:
            raise Exception("Some config files can't be loaded...")                                     

    def GetPathAllTextbooks(self):
        out = []
        if self._ConfigSources["iotatextbooks"]["content"] is not None and "activetextbooks" in self._ConfigSources["iotatextbooks"]["content"]:
            for v in self._ConfigSources["iotatextbooks"]["content"]["activetextbooks"]:
                fname = os.path.join(self._ConfigSources["iotatextbooks"]["dir"],v)
                if os.path.exists(fname):
                    out.append(fname)
        return out

    def GetActiveCodeBaseLanguages(self):
        out = []
        if self._ConfigSources["codebaselanguages"]["content"] is not None and "activelanguages" in self._ConfigSources["codebaselanguages"]["content"]:
            for v in self._ConfigSources["codebaselanguages"]["content"]["activelanguages"]:
                fname = os.path.join(self._ConfigSources["codebaselanguages"]["dir"],v["sourcefile"])
                if os.path.exists(fname):
                    out.append({"language":v["language"],
                                "path":fname})
        return out
    
    def GetPathReadmeFile(self):
        out = None
        if self._ConfigSources["iotatextbooks"]["content"] is not None and "readme" in self._ConfigSources["iotatextbooks"]["content"]:
            fname = os.path.join(self._ConfigSources["iotatextbooks"]["dir"],self._ConfigSources["iotatextbooks"]["content"]["readme"])
            if os.path.exists(fname):
                    out=fname
        return out

    def GetPathTargetNotebooks(self):
        if self._ConfigSources["languagenotebookdestination"]["content"] is not None:
            return self._ConfigSources["languagenotebookdestination"]["dir"]
        else:
            return None

    def GetPathTargetHTML(self):
        if self._ConfigSources["htmldestination"]["content"] is not None:
            return self._ConfigSources["htmldestination"]["dir"]
        else:
            return None

    def GetPerex(self):
        if self._ConfigSources["iotatextbooks"]["content"] is not None and "perex" in self._ConfigSources["iotatextbooks"]["content"]:
            return self._ConfigSources["iotatextbooks"]["content"]["perex"]
        else:
            return None
            
    def _SearchForConfigFiles(self):
        for root, dirs, files in os.walk(self._RootDirectory):
            if "config.json" in files:
                content = None
                try:
                    with open(os.path.join(root,"config.json"), 'r') as f:
                        content = json.load(f)
                except Exception as e:
                    pprint(e)
                    print(" at " + root)
                    
                if content is not None:
                    if "configtype" in content and content["configtype"] in self._ConfigSources:
                        self._ConfigSources[content["configtype"]]["dir"] = root
                        self._ConfigSources[content["configtype"]]["content"] = content                        
                                    


class TaskManager(object):
    def MergeNotebooks(self, SourceNotebooks, Perex, ReadmeFile = None):
        if SourceNotebooks is None or len(SourceNotebooks)==0:
            raise ValueError("SourceNotebooks cannot be empty!")
        
        mergednotebook = None
        readmecontent = None
    
        if ReadmeFile!=None and os.path.exists(ReadmeFile):
            readmecontent = open(ReadmeFile, "r").read()
                
        mergednotebook = nbformat.v4.new_notebook()
        perex = Perex
        if readmecontent is not None:
            perex = perex.replace("%%README%%",readmecontent)
                
        mdc = nbformat.v4.new_markdown_cell(perex)
        mergednotebook.cells.append(mdc)
        
        for fname in SourceNotebooks:
            with io.open(fname, 'r', encoding='utf-8') as f:
                nb = nbformat.read(f, as_version=4)
            mergednotebook.cells.extend(nb.cells)

        if not "title" in mergednotebook.metadata:
            mergednotebook.metadata.title = ''
        mergednotebook.metadata.title += "Complete IOTA Developer Essentials Textbook"
        return mergednotebook

    def ConvertNotebook(self, FromNotebook, ToHTML):        
        htmlexporter = HTMLExporter() #default settings
        (body, resources) = htmlexporter.from_filename(FromNotebook)
        
        #replacing link placeholder - to be moved somewhere else since I do not know how many languages ATM
        #body = body.replace("&#182;",u'<img src="https://raw.githubusercontent.com/Hribek25/IOTA101/master/Graphics/link-me-lightgrey.png" style="display:inline; height:20px" />')
        
        with io.open(ToHTML, 'w', encoding='utf-8') as f:
            f.write(body)

    def ReplaceCodeBaseWith(ReplacedNtb, ReplaceWithNtb):
        pass

    
def main():
    try:
        cfg = ConfigManager(r'C:\Users\pzizka\OneDrive\VisualBasicProjects\repos\IOTA101')
    except Exception as e:
        pprint(e)
        return 1   
    print("Searching for config.json files...DONE")
    

    #TODO: clean target directory

    # MERGING
    # Let's merge main Python-based notebook
    print("Merging exercise...Python-based")
    targetdir = cfg.GetPathTargetNotebooks() # where to save combined python notebooks
    print("Target directory: " + targetdir)
    print("Source files")
    pprint(cfg.GetPathAllTextbooks())
        
    tasks = TaskManager()
    
    combinedfile = os.path.join(targetdir,"Allchapters_python.ipynb")
    try:
        merged = tasks.MergeNotebooks(cfg.GetPathAllTextbooks(),
                                      cfg.GetPerex(),
                                      cfg.GetPathReadmeFile())        
        with io.open(combinedfile, 'w', encoding='utf-8') as f:
            nbformat.write(merged,f)
        print("File merged: " + combinedfile)
    except Exception as e :
        pprint(e)
        return 1

    # CONVERTING
    if cfg.GetPathTargetHTML() is not None: 
        try:
            htmlfile = os.path.join(cfg.GetPathTargetHTML(),
                                "Allchapters_python.ipynb.html")
            tasks.ConvertNotebook(combinedfile, htmlfile)    
            print("File converted... " + combinedfile + " -----> " + htmlfile)
        except Exception as e :
            pprint(e)
            return 1
    else:
        print("File NOT converted... due to missing HTML target dir: " + combinedfile )    

    
if __name__ == "__main__":
    sys.exit(int(main() or 0))
