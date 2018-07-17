#!/usr/bin/env python3
# Note, updated version of 
# https://github.com/ipython/ipython-in-depth/blob/master/tools/nbmerge.py

"""
usage:

python nbmerge.py A.ipynb B.ipynb C.ipynb > merged.ipynb
or
python nbmerge.py --DIR ./somedir/
"""

import io
import os
import sys
import nbformat
readmefile=""

def merge_notebooks(filenames):
    global readmefile
    merged = None
    readme = None
    if readmefile!="":
        readme = open(readmefile, "r").read()
        #print (readme)
        merged = nbformat.v4.new_notebook()
        rc = nbformat.v4.new_markdown_cell("> *This textbook was generated automatically from a [GitHub Repo](https://github.com/Hribek25/IOTA101). Visit the repo for more information.* \n\n" + readme + "\n\n--- \n")
        merged.cells.append(rc)
        #print (merged)
        #sys.exit(1)

    for fname in filenames:
        with io.open(fname, 'r', encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)
        if merged is None:
            merged = nb
        else:
            # TODO: add an optional marker between joined notebooks
            # like an horizontal rule, for example, or some other arbitrary
            # (user specified) markdown cell)
            merged.cells.extend(nb.cells)
    if not hasattr(merged.metadata, 'title'):
        merged.metadata.title = ''
    merged.metadata.title += "Complete IOTA Developer Essentials Textbook"
    print(nbformat.writes(merged))

if __name__ == '__main__':
    if len(sys.argv)>1 and sys.argv[1]=="--DIR":
        notebooks = list()
        if len(sys.argv)>2:
            dir = sys.argv[2]
            if os.path.isdir(dir):
                readmefile=os.path.join(dir,"README.md")
                if os.path.exists(readmefile)==False:
                    readmefile=""
                for file in os.listdir(dir):
                    if file.endswith(".ipynb"):
                        notebooks.append(os.path.join(dir,file))
                #print(notebooks)
    else:
        notebooks = sys.argv[1:]

    if not notebooks or len(notebooks)==0:
        print(__doc__, file=sys.stderr)
        sys.exit(1)
    
    merge_notebooks(notebooks)