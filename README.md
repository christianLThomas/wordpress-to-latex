# Wordpress XML to LaTeX Parser - WP2LATEX

This code is for parsing exported WordPress files and writing them to a .tex file, allowing for immediate compilation into a LaTeX document.

Credits for the Python Wordpress parser (all of parse.py) go to Ben Demaree: https://github.com/bendemaree/python-wordpressparse

## Usage

wp2latex.parse returns the XML posts and other associated details mostly unchanged. wp2latex.write then handles all of the text-to-LaTeX parts. It writes to a very basic LaTeX [Memoir](https://ctan.org/pkg/memoir?lang=en) format. Any further formatting is up to the user and can easily be added into the final LaTeX document after compiling. 
