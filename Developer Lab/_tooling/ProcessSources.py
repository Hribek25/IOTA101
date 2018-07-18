#!/usr/bin/env python3
import json
import sys
import nbformat
import os
from pprint import pprint


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
        self.SearchForConfigFiles() # are all config files in place?
        nondetected = False
        for key in self._ConfigSources:
            if self._ConfigSources[key]["content"] is None:
                print("Can't load config file for " + key)
                nondetected=True
        if nondetected:
            raise Exception("Some config files can't be loaded...")                                     

    def SearchForConfigFiles(self):
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


            

def main():
    try:
        cfg = ConfigManager(r'C:\Users\pzizka\OneDrive\VisualBasicProjects\repos\IOTA101')
    except Exception as e:
        pprint(e)
        return 1   
    
if __name__ == "__main__":
    sys.exit(int(main() or 0))
