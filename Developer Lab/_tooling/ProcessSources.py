﻿#!/usr/bin/env python3

import json
import sys
import nbformat
import os
import io
import re
from pprint import pprint
from nbconvert import HTMLExporter
#from bs4 import BeautifulSoup
#from jinja2 import DictLoader


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
                print("Could not load config file for " + key)
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
                                    

#class SoapNavigationElements(object):
#    def DivClassCodeCell(self, tag):
#        return tag.name == "div" and tag.has_attr("class") and "code_cell" in tag["class"]

#    def DivClassCodeCellInputPrompt(self, tag):
#        return tag.name == "div" and tag.has_attr("class") and "prompt" in tag["class"] and "input_prompt" in tag["class"]

    

class TaskManager(object):
    def MergeNotebooks(self, SourceNotebooks, Perex, TargetFile, ReadmeFile = None):
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
            mergednotebook.metadata.update(nb.metadata)

        if not "title" in mergednotebook.metadata:
            mergednotebook.metadata.title = ''
        mergednotebook.metadata.title += "Complete IOTA Developer Essentials Textbook"

        with io.open(TargetFile, 'w', encoding='utf-8') as f:
            nbformat.write(mergednotebook,f)
        

    def ConvertNotebook(self, FromNotebook, ToHTML):        
        htmlexporter = HTMLExporter() #default settings
        htmlexporter.template_file="custom.tpl"

        (body, resources) = htmlexporter.from_filename(FromNotebook)
        
        with io.open(ToHTML, 'w', encoding='utf-8') as f:
            f.write(body)

    def ReplaceCodeBaseWith(self,ReplacedNtb, ReplaceWithNtb, TargetNtb, Language=None):
        
        # loading and indexing notebook with codebase
        with io.open(ReplaceWithNtb, 'r', encoding='utf-8') as f:
            inputNtb = nbformat.read(f, as_version=4)
        targetLanguageMetaData = {key: inputNtb["metadata"][key]  for key in inputNtb["metadata"] if key=="kernelspec" or key=="language_info"} # info regarding the target lingo

        commentline = ""
        if targetLanguageMetaData["kernelspec"]["language"]=="javascript":
            commentline = "//%s"
        
        inputBase={} # dictionary for fast acccess codebase based on codeid
        for c in inputNtb.cells:
            if c["cell_type"]=="code" and "iotadev" in c["metadata"] and "codeid" in c["metadata"]["iotadev"]: #yes, it seems it is the correct code snippet
                inputBase[c["metadata"]["iotadev"]["codeid"]] = c #storing whole cell


        # now let's compile new NTB with replaced codebase
        with io.open(ReplacedNtb, 'r', encoding='utf-8') as f:
            OutputNtb = nbformat.read(f, as_version=4)

        for c in OutputNtb.cells:
            if c["cell_type"]=="code" and "iotadev" in c["metadata"] and "codeid" in c["metadata"]["iotadev"]: #yes, it seems to be a code snippet I am looking for
                codeid = c["metadata"]["iotadev"]["codeid"]
                if codeid in inputBase: #if there is a new code base, let's replace it
                    c["outputs"]=inputBase[codeid]["outputs"]
                    c["source"]=inputBase[codeid]["source"]
                    c["execution_count"]=0
                else: #there is not code base to be replaced - and so removing source and outputs and adding some comment line
                    c["outputs"] = []
                    c["source"] = [commentline % (" No code snippet available for the selected language: " + targetLanguageMetaData["kernelspec"]["language"])]
                    c["execution_count"]=0

        #replacing also kernel/language specs
        for k in targetLanguageMetaData:
            OutputNtb["metadata"][k] = targetLanguageMetaData[k]
        
        #pprint(OutputNtb)
        
        #let's save a new one
        with io.open(TargetNtb, 'w', encoding='utf-8') as f:
            nbformat.write(OutputNtb,f)
               
    def PerformHTMLtweaks(self, TargetFile, Language, Chunks):
        if not os.path.exists(TargetFile):
            raise Exception("File can't be found:" + TargetFile)
        
        with open(TargetFile) as fp:
            #soup = BeautifulSoup(fp, "html5lib")
            filecontent = fp.read()

        tplChunks = {"link_me": None,
                     "language_ico": None,
                     "title": None}
        for i in Chunks:
            if i in tplChunks:
                tplChunks[i] = Chunks[i]

        #PRE DOM TWEAKS
        filecontent = filecontent.replace("&#182;",u'%%%link_me%%%') # hopefully will get rid of this step while generating HTML
        
        if tplChunks["language_ico"] is not None: #here I need something special because of codeid within the placeholder
            filecontent = re.sub(pattern=r"%%%language_ico[|]{1}([A-Z0-9]+)%%%",
                                repl=tplChunks["language_ico"].replace("%%%codeid%%%",r"\g<1>"),
                                string=filecontent)
                
        #DOM TWEAKS
        #navsoap = SoapNavigationElements() # helping functions to identify some DOM elements
        #soup = BeautifulSoup(filecontent, "html5lib")
        #soup.title.string="%%%title%%%"
        #for i in soup.find_all(navsoap.DivClassCodeCell): # two phases to be sure it is targetted
        #    for ele in i.find_all(navsoap.DivClassCodeCellInputPrompt): # searching for In [XX]
        #        ele.string = "%%%language_ico%%%"

        #filecontent = str(soup) # getting back to normal string
        #del soup

        # replacing placeholders
        #filecontent = filecontent.format(tpl=tplChunks)
        for i in tplChunks:
            if tplChunks[i] is not None:
                filecontent = filecontent.replace("%%%" + i + "%%%",tplChunks[i])
                
        # saving the file
        with open(TargetFile, 'w') as f:
            f.write(filecontent)
        print("HTML was tweaked: " + TargetFile)


def main():
    TplntbFileName = "Allchapters_%s.ipynb"
    TplhtmlFileName = "Allchapters_%s.ipynb.html"

    try:
        rootDir = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               "..%s..%s"%(os.path.sep, os.path.sep))
        cfg = ConfigManager(rootDir)
        
    except Exception as e:
        pprint(e)
        return 1   
    print("Searching for config.json files...DONE")
    

    #TODO: clean target directory

    # MERGING
    print("Merging exercise...Python-based")
    targetdir = cfg.GetPathTargetNotebooks() # where to save combined python notebooks as a master
    print("Target directory: " + targetdir)
    print("Source files")
    pprint(cfg.GetPathAllTextbooks())
        
    tasks = TaskManager()
    
    all_prepared_languages = [] # which languages has been processed ?

    # Let's merge MASTER Python-based notebook
    lang="python"
    combinedfile = os.path.join(targetdir,TplntbFileName % (lang))
    try:
        merged = tasks.MergeNotebooks(cfg.GetPathAllTextbooks(),
                                      cfg.GetPerex(),
                                      combinedfile,
                                      cfg.GetPathReadmeFile())        
        
        print("File merged: " + combinedfile)
        all_prepared_languages.append(lang)
    except Exception as e :
        pprint(e)
        return 1

    # REPLACING CODE BASES - GENERATING NEW CODE BASES 
    for i in cfg.GetActiveCodeBaseLanguages():
        try:
            f = os.path.join(cfg.GetPathTargetNotebooks(),TplntbFileName % (i["language"]))
            tasks.ReplaceCodeBaseWith(combinedfile,
                                  i["path"],
                                  f,
                                  i["language"])
            all_prepared_languages.append(i["language"])
            print("New language-specific file generated... " + f)
        except Exception as e:
            pprint(e)
            return 1 # All or nothing
        

    # CONVERTING TO HTML AND TWEAKING
    if cfg.GetPathTargetHTML() is not None:  # let's convert all combined files
        for l in all_prepared_languages:            
                ntbfile = os.path.join(cfg.GetPathTargetNotebooks(), TplntbFileName % (l))
                htmlfile = os.path.join(cfg.GetPathTargetHTML(), TplhtmlFileName % (l))
                
                if os.path.exists(ntbfile):
                    try:
                        tasks.ConvertNotebook(ntbfile, htmlfile)    
                        print("File converted... " + ntbfile + " -----> " + htmlfile)
                    except Exception as e :
                        pprint(e)
                        return 1
                    
                    # HTML Tweaks
                    # language_ico menu - navigation thru all avail languages
                    lang_ico_chunk = ""

                    # main currently visible lang is the first one - and no hyperlink
                    lang_ico_chunk += r"<a href='{href}#%%%codeid%%%'><img src='https://raw.githubusercontent.com/Hribek25/IOTA101/master/Graphics/ico_{lang}.svg?sanitize=true' style='margin-bottom: 12px; display:inline; width:50px; background-color: rgb(221, 255, 255); border-left-color: rgb(33, 150, 243); border-left-style: solid; border-left-width: 3px; padding:5px' title='{lang}' /></a>".format(lang=l.lower(), href=TplhtmlFileName % (l))
                    for i in all_prepared_languages:
                        if i!=l: # only for other languages
                            lang_ico_chunk += r"<br /><a href='{href}#%%%codeid%%%'><img src='https://raw.githubusercontent.com/Hribek25/IOTA101/master/Graphics/ico_{lang}.svg?sanitize=true' style='display:inline; width:50px; -webkit-filter: grayscale(100%); filter: grayscale(100%);padding:5px;' title='{lang}' /></a>".format(lang=i.lower(), href=TplhtmlFileName % (i))
                    try:
                        tasks.PerformHTMLtweaks(htmlfile,
                                                l,
                                                {"link_me": r"<img src='https://img.shields.io/badge/link-{}-lightgrey.svg' style='display:inline; height:18px' />".format(l),
                                                "language_ico": lang_ico_chunk,
                                                "title": "IOTA Developer Essentials for " + l
                                                })
                    except Exception as e :
                        pprint(e)
                        return 1                        

                else:
                    print("Could not find the file to be converted to HTML: " + ntbfile + " Skipping.")

    else:
        print("Files NOT converted... due to missing HTML target dir: " + combinedfile )   
    
    
    
if __name__ == "__main__":
    sys.exit(int(main() or 0))
