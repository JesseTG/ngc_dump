#!/bin/bash

mkdir -p markdown

ls -1 xml | \
    parallel -v -j$(nproc) --noswap 'python3 -OO convert-to-markdown.py --front-matter xml/{} markdown/{/.}.md'