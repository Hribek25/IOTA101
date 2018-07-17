#!/bin/bash
cd /opt/iota101repo/IOTA101
git fetch origin
git reset --hard origin/master
git clean -f

cd /opt/iota101repo
python3 nbmerge.py --DIR ./IOTA101/ > 'IOTA101 Complete.ipynb'
jupyter nbconvert 'IOTA101 Complete.ipynb' --stdout > 'complete.html'
sed -i 's/&#182;/<img src="https:\/\/raw.githubusercontent.com\/Hribek25\/IOTA101\/master\/Graphics\/link-me-lightgrey.png" style="display:inline; height:15px" \/>/g' 'complete.html'
cp 'complete.html' ./IOTA101/docs/index.html
cd /opt/iota101repo/IOTA101
git add 'docs/index.html'
git commit 'docs/index.html' -m 'New combined version' --no-edit
git push
