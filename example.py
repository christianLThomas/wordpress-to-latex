#!/usr/bin/env python

import os
from wp2latex import extract_blog_from_XML, latexwrite

# Path to export directly from wordpress.com:
filename = "Data/short-2.xml"
media_archive = "/home/clt/Projects/Blog2Book/wp-content/"

# Parse file into Python objects (download not supported):
tree, namespaces, blogs, authors, tags, posts, attachments = extract_blog_from_XML(filename, download=False)

# Open LaTeX file:
if not os.path.exists('texOutput'): os.mkdir('texOutput')
filename = "texOutput/Blog.tex"
f = open(filename, 'w')

# Define title and author:
abstract = "Carrots are devine... You get a dozen for a dime, It's maaaa-gic!"
latexwrite.latex_preamble(f, "This is my Blog Title", "by Bugs Bunny", abstract)

latexwrite.new_chapter(f, "First Chapter")

# Start writing to file:
figcounter = 1	# has to be set to one if you want continuous fig numbering throughout
for post in posts:
    print(figcounter)
    figcounter += 1
    #post.adjust_paths(attachments=attachments, prefix='http://assets.mysite.com/img/')
    print(post.title)
    figcounter = latexwrite.post_to_latex(f, post, posts, attachments, figcounter, media_archive=media_archive)

# Close LaTeX:
f.write("\\end{document}"+'\\n')
f.close()
