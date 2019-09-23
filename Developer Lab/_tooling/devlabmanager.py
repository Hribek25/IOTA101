#!/usr/bin/env python3

import json
import sys
import nbformat
import os
import io
import re
from pprint import pprint
from nbconvert import HTMLExporter
import shutil
import gistbridge

class ConfigManager(object):
    TplntbFileName = "Allchapters_%s.ipynb"
    TplhtmlFileName = "Allchapters_%s.ipynb.html"
    
    TplhtmlSnipMainLangIco = r"""
<img src='https://raw.githubusercontent.com/Hribek25/IOTA101/master/Graphics/ico_{lang}_small.svg?sanitize=true' style='margin-bottom: 0px; display:inline; width:30px; background-color: rgb(221, 255, 255); border-left-color: rgb(33, 150, 243); border-left-style: solid; border-left-width: 3px; padding:5px' title='{lang} version' /><br />
<a href='{href}#%%%codeid%%%'><img src='https://raw.githubusercontent.com/Hribek25/IOTA101/master/Graphics/ico_link_small.svg?sanitize=true' style='margin-bottom: 0px; display:inline; width:30px; background-color: rgb(221, 255, 255); border-left-color: rgb(33, 150, 243); border-left-style: solid; border-left-width: 3px; padding:5px' title='Direct link to the snippet' /></a><br />
"""
    TplhtmlSnipSecondaryLangIco = r"""
<a href='{href}#%%%codeid%%%'><img src='https://raw.githubusercontent.com/Hribek25/IOTA101/master/Graphics/ico_{lang}_small.svg?sanitize=true' style='display:inline; width:30px; -webkit-filter: grayscale(100%); filter: grayscale(100%);padding:5px;' title='Switch to {lang} version' /></a><br />
"""
    # Gist has to be separated since it is optional and not included with all snippets
    TplhtmlSnipGistLink = r"""
<a href='{href}#%%%codeid%%%'><img src='https://raw.githubusercontent.com/Hribek25/IOTA101/master/Graphics/ico_gist_small.svg?sanitize=true' style='margin-bottom: 0px; display:inline; width:30px; background-color: rgb(221, 255, 255); border-left-color: rgb(33, 150, 243); border-left-style: solid; border-left-width: 3px; padding:5px' title='View @ Gist [%%%codedescription%%%]' /></a><br />
"""
    # if not gist link - so at least make some space
    TplhtmlSnipGap = r"""
<div style='margin-bottom: 3px; margin-left:auto; margin-right:0; display:block; width:30px; height:5px; border-bottom-color: #eeeeee; border-bottom-style: solid; border-bottom-width: 1px;'>&nbsp;</div>
"""

    
    def __init__(self, RootDirectory):
        if not RootDirectory:
            raise ValueError("RootDirectory is empty!")
                
        self._RootDirectory = RootDirectory
        self._ConfigSources = {
            "languagenotebookdestination":{"dir":"","content":None, "optional": False},
            "iotatextbooks":{"dir":"","content":None, "optional": False},
            "htmldestination":{"dir":"","content":None, "optional": False},
            "codebaselanguages":{"dir":"","content":None, "optional": False},
            "gistmap":{"dir":"","content":None, "optional": True}
            }
        self._SearchForConfigFiles() # are all config files in place?
        nondetected = False
        for key in self._ConfigSources:
            if self._ConfigSources[key]["content"] is None:
                if self._ConfigSources[key]["optional"]!=True:
                    print("Could not load config file for " + key)
                    nondetected=True
                else:
                    print("Could not load optional config file for " + key + " but it is OK...")
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
    
    def GetAllLanguages(self):
        out = []
        out.append("python") # master language - always the first one
        
        for l in self.GetActiveCodeBaseLanguages():
            out.append(l["language"])
        
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
            for fn in ["config.json", "gist_map.json"]:  # searching for two potential files
                if fn in files:
                    content = None
                    try:
                        with open(os.path.join(root,fn), 'r') as f:
                            content = json.load(f)
                    except Exception as e:
                        pprint(e)
                        print(" at " + root)
                    
                    if content is not None:
                        if "configtype" in content and content["configtype"] in self._ConfigSources:
                            self._ConfigSources[content["configtype"]]["dir"] = root
                            self._ConfigSources[content["configtype"]]["content"] = content   
                            
    def GetGistMap(self):
        return self._ConfigSources["gistmap"]
                                    
   

class TaskManager(object):
    def __init__(self, Configuration):
        self._ConfFiles = Configuration
    
    
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
        

    def ConvertNotebookFromFile(self, FromNotebook, ToHTML):        
        htmlexporter = HTMLExporter() #default settings
        htmlexporter.template_file="custom.tpl"

        (body, resources) = htmlexporter.from_filename(FromNotebook)
        
        with io.open(ToHTML, 'w', encoding='utf-8') as f:
            f.write(body)

    def ConvertNotebookFromNotebook(self, FromNotebook, ToHTML):        
        htmlexporter = HTMLExporter() #default settings
        htmlexporter.template_file="custom.tpl"

        (body, resources) = htmlexporter.from_notebook_node(FromNotebook)
        
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
        if targetLanguageMetaData["kernelspec"]["language"]=="csharp":
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
                    c["metadata"]["iotadev"]["missing"]="true"

        #replacing also kernel/language specs
        for k in targetLanguageMetaData:
            OutputNtb["metadata"][k] = targetLanguageMetaData[k]
        
        #pprint(OutputNtb)
        
        #let's save a new one
        with io.open(TargetNtb, 'w', encoding='utf-8') as f:
            nbformat.write(OutputNtb,f)
    
    def _langIcoReplHelper(self, matchobj):
        codeid = matchobj.group(1) # actual code id
        l = self._lang # active language
        tpl = self._tplLangIco # actual template to deal with
        gistmap = self._ConfFiles.GetGistMap()["content"] #get snippets in gist

        if codeid in gistmap["languages"][l]["snippets"]: # is the given code id among gist snippets?
            tpl = tpl.replace("%%%gist_link%%%",ConfigManager.TplhtmlSnipGistLink.format(href=gistmap["languages"][l]["snippets"][codeid]["html_url"]))
            tpl = tpl.replace("%%%codedescription%%%", gistmap["languages"][l]["snippets"][codeid]["description"])
        else:
            tpl = tpl.replace("%%%gist_link%%%","") #no gist snippet, no gist link

        tpl = tpl.replace("%%%codeid%%%",codeid) # now replace code id placeholder
        return tpl

    def PerformHTMLtweaks(self, TargetFile, Language, Chunks):
        if not os.path.exists(TargetFile):
            raise Exception("File can't be found:" + TargetFile)
        
        with open(TargetFile) as fp:
            filecontent = fp.read()

        tplChunks = {"link_me": None,
                     "language_ico": None,
                     "title": None}
        for i in Chunks:
            if i in tplChunks:
                tplChunks[i] = Chunks[i]

        #PRE DOM TWEAKS
        if tplChunks["link_me"] is not None:
            filecontent = filecontent.replace("&#182;",u'%%%link_me%%%') # hopefully will get rid of this step while generating HTML
        
        if tplChunks["language_ico"] is not None: # Here I need something special because of codeid used within the placeholder. In addtional to that I need to process code id before replace
            self._tplLangIco = tplChunks["language_ico"] # actual template stored
            self._lang = Language

            filecontent = re.sub(pattern=r"%%%language_ico[|]{1}([A-Z0-9]+)%%%",
                                 repl=self._langIcoReplHelper,
                                 string=filecontent)
            
            #re.sub(pattern=r"%%%language_ico[|]{1}([A-Z0-9]+)%%%",
            #                    repl=tplChunks["language_ico"].replace("%%%codeid%%%",r"\g<1>"),
            #                    string=filecontent)


        # replacing placeholders
        #filecontent = filecontent.format(tpl=tplChunks)
        for i in tplChunks:
            if tplChunks[i] is not None:
                filecontent = filecontent.replace("%%%" + i + "%%%",tplChunks[i])
                
        # saving the file
        with open(TargetFile, 'w') as f:
            f.write(filecontent)
        print("HTML was tweaked: " + TargetFile)

    def GenerateCodeBaseStatus(self,FilesToExamine, FileToGenerate, RootHTMLurl):
        # Assumption - main language is the first one

        snippets={} # main storage for snippets and respective language
        langs = []

        statusinfo = r" ![Coverage](https://img.shields.io/badge/Coverage-%%%percent%%%%25-brightgreen.svg) "
        standaloneinfotrue = r"  ![Standalone Snippet](https://img.shields.io/badge/-{}-orange.svg) "
        standaloneinfofalse = r"  ![Standalone Snippet](https://img.shields.io/badge/-{}-lightgrey.svg) "

        for f in FilesToExamine:
            with io.open(f, 'r', encoding='utf-8') as f:
                Ntb = nbformat.read(f, as_version=4)
            lang = Ntb["metadata"]["kernelspec"]["language"]
            langs.append(lang)

            for c in Ntb.cells:
                if c["cell_type"]=="code" and "iotadev" in c["metadata"] and "codeid" in c["metadata"]["iotadev"]: #yes, it seems to be a code snippet I am looking for
                    tit = c["metadata"]["iotadev"]["title"] if "title" in c["metadata"]["iotadev"] else ""
                    codeid =   tit + " <sub>#" + c["metadata"]["iotadev"]["codeid"] + r"</sub>"
                    if not codeid in snippets:
                        snippets[codeid] = {"langs": [],
                                            "standalone": None,
                                            "codeid": c["metadata"]["iotadev"]["codeid"]} #list of identified languages
                        if "standalone" in c["metadata"]["iotadev"]:
                            snippets[codeid]["standalone"] = c["metadata"]["iotadev"]["standalone"]

                    if not "missing" in c["metadata"]["iotadev"]:
                        snippets[codeid]["langs"].append(lang)

        content = ""

        #intro
        content += """
## Language Coverage
The following table indicates what is the language-wise coverage across all snippets described in *IOTA Developer Essentials* and *IOTA Developer Lab*. If the given snippet is available then you can jump directly to it. `Standalone` column indicates whether the given code snippet can be used standalone or whether it is just a fragment of a broader code block.

*Info for contributors: There is an unique ID shown at each snippet. It is the code id that is unique across the whole code base and uniquely identifies the given snippet.*

"""
        coverage={l:0 for l in langs} # storage for language counters
        coverageTotal=0

        for idx,i in enumerate(snippets):
            if idx==0: #table header
                content += "Standalone | Code Base | " + "|".join([v for v in langs]) + "\n"                
                content += "---|--- | " + "|".join([":---:" for _ in langs]) + "\n"
            content += standaloneinfotrue.format(snippets[i]["standalone"]) if snippets[i]["standalone"]=="true" else standaloneinfofalse.format(snippets[i]["standalone"])
            content += "|" + i  # code snippet description
            coverageTotal +=1
            for v in langs:
                if v in snippets[i]["langs"]:
                    content += "|" + r'[<span style="color:green">Yes</span>]({} "Preview")'.format(r"https://hribek25.github.io/IOTA101/" + RootHTMLurl % (v) + "#" + snippets[i]["codeid"])
                    coverage[v] +=1
                else:
                    content += "|" + r"<span style='color:red'>N/A</span>"
            content += "\n"
        # status coverage indication
        content += " &nbsp; | **Current Status:** | " + "|".join([statusinfo.replace("%%%percent%%%", str(int((coverage[v] / coverageTotal) * 100))) for v in langs]) + "\n"

        with io.open(FileToGenerate, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Language coverage was generated: " + FileToGenerate)

    def GenerateDevLabLandingPage(self, SourceFilesPath, HTMLRootPath):
        filestomerge = ["README.md",
                        "COVERAGE.md",
                        "ABOUT.md"]
            
        ntb = nbformat.v4.new_notebook()

        for i in filestomerge:
            file = os.path.join(SourceFilesPath,i)

            if not os.path.exists(file):
                print("File does not exist: " + file)
            else:
                try:
                    mdcontent = open(file, "r").read()
                except Exception as e:
                    pprint(e)
                    return 1
                mdc = nbformat.v4.new_markdown_cell(mdcontent)
                ntb.cells.append(mdc)
        
        #convert to HTML and save
        htmlfile = os.path.join(HTMLRootPath,"devlab.html")        
        self.ConvertNotebookFromNotebook(ntb,htmlfile)

        try:
            self.PerformHTMLtweaks(htmlfile,
                                    None,
                                    {"link_me": r"<img src='https://img.shields.io/badge/link-me-lightgrey.svg' style='display:inline; height:18px' />",
                                    "language_ico": None,
                                    "title": "IOTA Developer Lab"
                                    })
        except Exception as e :
            pprint(e)
            return 1                    
        
        print("DevLab landing page was generated: " + htmlfile)


def main():        
    try:
        rootDir = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               "..%s..%s"%(os.path.sep, os.path.sep))
        cfg = ConfigManager(rootDir)
        TplntbFileName = ConfigManager.TplntbFileName
        TplhtmlFileName = ConfigManager.TplhtmlFileName
    except Exception as e:
        pprint(e)
        return 1   
    print("Searching for config.json files...DONE")
    
    #TODO: clean target directory

    # MERGING
    print("\nBUILDING MASTER NOTEBOOK (PYTHON-BASED)...")
    targetdir = cfg.GetPathTargetNotebooks() # where to save combined python notebooks as a master
    print("Target directory: " + targetdir)
    print("Source files")
    pprint(cfg.GetPathAllTextbooks())
        
    tasks = TaskManager(cfg)
    
    all_prepared_languages = [] # which languages has been processed ?

    # Let's combine MASTER Python-based notebook
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

    # GENERATING NEW CODE BASES from the master merged notebook
    print("\nBUILDING ANY-LANGUAGE-BASED NOTEBOOK(S)...")
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
    
    #UPDATING GISTS
    print("\nUPDATING GISTS...")
    manager = gistbridge.GistBridgeManager(cfg)
    manager.UpdateGists() # let's update/create all gists if needed
    gistmap = cfg.GetGistMap()

    # let's update gist_map.json file - it may be changed
    if os.path.exists(os.path.join(gistmap["dir"],"gist_map.json")):
        open(os.path.join(gistmap["dir"],"gist_map.json"),"w").write(json.dumps(gistmap["content"]))
        print("gist_map.json file was updated...")

    print("\nBUIDLING HTML FILES FROM NOTEBOOKS...")
    # CONVERTING ALL NOTEBOOKS TO HTML AND TWEAKING FINAL LOOK AND FEEL
    if cfg.GetPathTargetHTML() is not None:  # let's convert all combined files
        for idx,l in enumerate(all_prepared_languages):            
                ntbfile = os.path.join(cfg.GetPathTargetNotebooks(), TplntbFileName % (l))
                htmlfile = os.path.join(cfg.GetPathTargetHTML(), TplhtmlFileName % (l))
                
                if os.path.exists(ntbfile):
                    try:
                        tasks.ConvertNotebookFromFile(ntbfile, htmlfile)    
                        print("File converted... " + ntbfile + " --> " + htmlfile)
                    except Exception as e :
                        pprint(e)
                        return 1
                    
                    # HTML Tweaks
                    # language_ico menu - navigation thru all avail languages
                    lang_ico_chunk = ""

                    # main currently visible lang + direct link ico
                    lang_ico_chunk += ConfigManager.TplhtmlSnipMainLangIco.format(lang=l.lower(), href=TplhtmlFileName % (l))
                    
                    #Gist or not Gist - that's the question
                    #lang_ico_chunk += ConfigManager.TplhtmlSnipGistLink.format(href=TplhtmlFileName % (l))
                    lang_ico_chunk += "%%%gist_link%%%"
                    
                    #gap
                    lang_ico_chunk += ConfigManager.TplhtmlSnipGap #gap between main lang and other langs
                    
                    for i in all_prepared_languages: # add reference to other languages below
                        if i!=l: # only for other languages
                            lang_ico_chunk += ConfigManager.TplhtmlSnipSecondaryLangIco.format(lang=i.lower(), href=TplhtmlFileName % (i))
                    
                    try:
                        tasks.PerformHTMLtweaks(htmlfile,
                                                l,
                                                {"link_me": r"<img src='https://img.shields.io/badge/link-{}-lightgrey.svg' style='display:inline; height:18px' />".format(l),
                                                "language_ico": lang_ico_chunk,
                                                "title": "IOTA Developer Essentials for Python and NodeJS"
                                                })
                    except Exception as e :
                        pprint(e)
                        return 1                        
                    # if it is the first HTML file then it becomes index.html
                    if idx==0:
                        shutil.copyfile(src=htmlfile,
                                        dst=os.path.join(cfg.GetPathTargetHTML(), "index.html"))
                        print("Index.html file was replaced with " + htmlfile)

                else:
                    print("Could not find the file to be converted to HTML: " + ntbfile + " Skipping.")

    else:
        print("Files NOT converted... due to missing HTML target dir: " + combinedfile )   

    # GENERATING CODE BASE STATUS AND DEV LANDING PAGE
    print("\nGENERATING LANGUAGE COVERAGE MD FILE...")
    tasks.GenerateCodeBaseStatus(FilesToExamine=[os.path.join(cfg.GetPathTargetNotebooks(), TplntbFileName % (l)) for l in all_prepared_languages],
                                 FileToGenerate=os.path.join(cfg.GetPathTargetNotebooks(),"COVERAGE.md"),
                                 RootHTMLurl=TplhtmlFileName
                                 )
    print("\nGENERATING DEV LAB LANDING PAGE...")
    tasks.GenerateDevLabLandingPage(SourceFilesPath=cfg.GetPathTargetNotebooks(),
                                    HTMLRootPath=cfg.GetPathTargetHTML())
      
    
if __name__ == "__main__":
    sys.exit(int(main() or 0))
