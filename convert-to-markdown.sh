#!/bin/bash

mkdir -p markdown

ls -1 xml | \
    xargs -I {} basename --suffix=.xml {} | \
    xargs --max-procs=$(nproc) -I {}  ./convert-to-markdown.py xml/{}.xml markdown/{}.md