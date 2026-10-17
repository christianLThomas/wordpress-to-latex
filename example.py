#!/usr/bin/env python

import os
from wp2latex import extract_blog_from_XML, latexwrite

# Path to export directly from wordpress.com:
filename = "Data/outofthemiryblog.WordPress-to-July-2014.xml"
media_archive = "/home/clt/Projects/Blog2Book/wp-content/"

# Parse file into Python objects (download not supported):
tree, namespaces, blogs, authors, tags, posts, attachments, captions = extract_blog_from_XML(filename, download=False)

# Open LaTeX file:
if not os.path.exists('texOutput'): os.mkdir('texOutput')
filename = "texOutput/Blog.tex"
f = open(filename, 'w')

# Define title and author:
abstract = ""
latexwrite.latex_preamble(f, "Out of the Miry Blog", "by Tess and Christian Thomas", abstract)

latexwrite.new_chapter(f, "Before Kids")

# Start writing to file:
figcounter = 1	# has to be set to one if you want continuous fig numbering throughout
for post in posts:
    print(str(figcounter) +": "+str(post.title))
    figcounter += 1
    #post.adjust_paths(attachments=attachments, prefix='http://assets.mysite.com/img/')
    figcounter = latexwrite.post_to_latex(f, post, posts, attachments, figcounter, captions, media_archive=media_archive)

# Close LaTeX:
f.write("\\end{document}"+'\\n')
f.close()
