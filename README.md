# Wordpress XML to LaTeX Parser - WP2LATEX

This code is for parsing exported WordPress files and writing them to a .tex file, allowing for immediate compilation into a LaTeX document. It's mainly intended for taking travel blogs (with mostly text and images, no complex formatting) and putting them into a readable book-like PDF format with LaTeX.

Credits for the Python Wordpress parser (all of parse.py) go to Ben Demaree: https://github.com/bendemaree/python-wordpressparse

## Usage

### Dependencies:

See requirements.txt.

Also uses get_image_size from https://github.com/scardine/image_size.git to determine image sizes and optimal LaTeX layout.

### Application

wp2latex.parse returns the XML posts and other associated details mostly unchanged. wp2latex.write then handles all of the text-to-LaTeX parts. It writes to a very basic LaTeX [Memoir](https://ctan.org/pkg/memoir?lang=en) format. Any further formatting is up to the user and can easily be added into the final LaTeX document after compiling. 

### Notes

- Works with blog posts made using the old Wordpress Editor and the newest blog posts made with the Wordpress Block Editor.
- Supports parsing of most basic blog building blocks: text/paragraphs, images, lists, videos, URLs, horizontal rules, bold/italic font.
- Does not support parsing of: galleries, most other things. Unsupported sections will appear in the LaTeX document mostly unchanged in XML, so can still be replaced later.
