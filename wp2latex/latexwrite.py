#!/usr/bin/env python
"""
This code contains functions for converting the parsed Wordpress XML into LaTeX-format code,
which is then written directly to file. Most functions take the variable f as open file.

To-dos:
- remove section counting
- fix <span> text options
- add another fig referencing option not requiring figcounter

Author: R. L. Bailey (GitHub bairaelyn), April-May 2020.
"""

import subprocess
import os
import re
from datetime import datetime
import pytz
import logging


logger = logging.getLogger("latexwrite")



try:
    import imagesize
except:
    print("imagesize not installed. Image sizes may not be read correctly.")

nl = "\n"
horizontal_rule = '\\noindent\\rule{\\textwidth}{0.4pt}\\vspace{2.5mm}'

# -------------------------------------------------------------------
# GENERAL LATEX TEXT FUNCTIONS
# -------------------------------------------------------------------

def date_string(date):
    if 4 <= date.day <= 20 or 24 <= date.day <= 30:
        suffix = "th"
    else:
        suffix = ["st", "nd", "rd"][date.day % 10 - 1]
    datef = datetime.strftime(date, "{}{} %b %Y, %H:%M.".format(date.day, suffix))
    datestr = "\\textit{Published on "+datef+"}"+nl

    return datestr


def latex_preamble(f, title, author, abstract):
    """Compiles all the LaTeX preamble with documentclass and packages.
    Also does title, author and abstract.

    Takes f, an open .tex file, and strings for title, author, abstract.
    """

    f.write("\\documentclass[10pt,twoside,openright]{memoir}"+nl)
    f.write("\\usepackage{graphicx}"+nl)
    f.write("\\usepackage{hyperref}"+nl)
    f.write("\\usepackage{eurosym}"+nl)
    f.write("\\usepackage{subcaption}"+nl)
    f.write("\\usepackage{cleveref}"+nl)
    f.write("\\captionsetup[subfigure]{subrefformat=simple,labelformat=simple}"+nl)
    f.write("\\renewcommand\\thesubfigure{(\\alph{subfigure})}"+nl)
    f.write("\\setlrmarginsandblock{0.12\\paperwidth}{*}{1}"+nl)
    f.write("\\setulmarginsandblock{0.15\\paperwidth}{*}{1}"+nl)
    f.write("\\checkandfixthelayout"+nl)
    f.write(nl)
    f.write("\\pagestyle{ruled}"+nl)
    f.write(nl)
    f.write("% Makes a fancier chapter style:"+nl)
    f.write("\\setlength\\midchapskip{10pt}"+nl)
    f.write("  \\makechapterstyle{VZ23}{"+nl)
    f.write("  \\renewcommand\\chapternamenum{}"+nl)
    f.write("  \\renewcommand\\printchaptername{}"+nl)
    f.write("  \\renewcommand\\chapnumfont{\\Huge\\bfseries\\centering}"+nl)
    f.write("  \\renewcommand\\chaptitlefont{\\Huge\\scshape\\centering}"+nl)
    f.write("  \\renewcommand\\afterchapternum{%"+nl)
    f.write("    \\par\\nobreak\\vskip\\midchapskip\\hrule\\vskip\\midchapskip}"+nl)
    f.write("  \\renewcommand\\printchapternonum{%"+nl)
    f.write("    \\vphantom{\\chapnumfont \\thechapter}"+nl)
    f.write("    \\par\\nobreak\\vskip\\midchapskip\\hrule\\vskip\\midchapskip}"+nl)
    f.write("}"+nl)
    f.write("\\chapterstyle{VZ23}"+nl)
    f.write(nl)
    f.write("% Removes section numberings:"+nl)
    f.write("\\setcounter{secnumdepth}{0}"+nl)
    f.write(nl)
    f.write("% Removes abstract title:"+nl)
    f.write("\\renewcommand{\\abstractname}{\\vspace{-\\baselineskip}}"+nl)
    f.write(nl)
    f.write("\\begin{document}"+nl)
    f.write(nl)
    f.write("\\font\\myfont=cmr12 at 35pt"+nl)
    f.write("\\title{{\\myfont "+title+"}}"+nl)
    f.write("\\author{\\textit{"+author+"}}"+nl)
    f.write(nl)
    f.write("\\maketitle"+nl)
    f.write(nl)
    f.write("\\begin{abstract}"+nl)
    f.write(abstract+nl)
    f.write("\\end{abstract}"+nl)
    f.write(nl)
    f.write("\\newpage"+nl)
    f.write("\\tableofcontents"+nl)
    f.write(nl)


def new_chapter(f, title):
    """Parameters f, and open .tex file and the string title for new chapter."""

    f.write("\\chapter{"+title+"}"+nl)
    f.write(nl)

# -------------------------------------------------------------------
# CONVERTING XML TO LATEX
# -------------------------------------------------------------------

def html_tags_to_latex(textbody):
    """Replaces HTML tags with LaTeX equivalents within textbody.
    """
    for s in re.finditer('<em>(.+?)</em>', textbody):
        emphstr = s.group(0)
        textbody = textbody.replace(emphstr, "\\textit{"+s.group(1)+"}")
    for s in re.finditer('<i>(.+?)</i>', textbody):
        emphstr = s.group(0)
        textbody = textbody.replace(emphstr, "\\emph{"+s.group(1)+"}")
    for s in re.finditer('<strong>(.+?)</strong>', textbody):
        boldstr = s.group(0)
        textbody = textbody.replace(boldstr, "\\textbf{"+s.group(1)+"}")
    for s in re.finditer('<li>(.+?)</li>', textbody):
        itemstr = s.group(0)
        textbody = textbody.replace(itemstr, "\\item "+s.group(1))
    for s in re.finditer('<span(.+?)</span>', textbody):
        itemstr = s.group(0)
        textbody = textbody.replace(itemstr, '')

    return textbody


def image_to_latex(textbody, media_archive, figcounter, fws=['0.5','0.4'], layout='optimal', wp_blocks=False):
    """Replaces image references in textbody with LaTeX figure/subfigure code.
    Original image string looks like this:
    <img class="alignnone size-full wp-image-24" src="http://assets.mysite.com/img/dsc04657-edited.jpg" 
    alt="DSC04657 - Edited.jpg" width="4912" height="3264" />

    Parameters
    -----------
    textbody : str
        Text from parsed XML.
    media_archive : str
        Path to exported blog image files. Download not supported.
    figcounter : int
        Counter for figures to keep track of references.
    figwidths : list, default=['0.5','0.4']
        Provides in x*\textwidth the width of landscape, then portrait.
    layout : str
        String defining how the figures should be fitted into the text.
        Options for layout:
            - 'single': images are included individually, size determined by figwidth.
                The benefit is this should work without issues, but the figures take up a lot of space.
            - 'paired': images are paired into subplots if they match in orientation, but not otherwise
            - 'optimal': occasionally buggy approach that does the same as 'paired', then
                afterwards matches up the images that haven't been paired.

    Returns
    --------
    textbody, figcounter : str, int
        Textbody with LaTeX figures replaced, current figcounter to continue to next post.
    """

    img_paths = []
    # r=root, d=directories, f= files
    for r, d, f in os.walk(media_archive):
        for file in f:
            img_paths.append(os.path.join(r, file))

    landscape = [-1]
    replacestr = {}
    allimgstr, fignums, figpaths, figcaptions, orient = [], [], [], [], []
    str_fig, figpath, figcaption = '', '', ''
    lastimgstr = '----'
    figsetup = []
    if wp_blocks == False:
        re_img_str = '<img(.+?)>'
    else:
        re_img_str = '<!-- wp:image (.+?)-->\n(.+?)\n<!-- /wp:image -->'

    for s in re.finditer(re_img_str, textbody):
        laststr, lastfigpath, lastfigcaption = str_fig, figpath, figcaption
        img_exists = False
        try:
            n = re.search('src="(.+?)"', s.group(0)).group(1)
            nfile = os.path.split(n)[-1].split('?')[0]
            figpath = [x for x in img_paths if nfile in x][0]
            img_exists = True
        except:
            print("ERROR finding image regex: {}".format(s.group(0)))
            replacestr[s.group(0)] = ""
        if img_exists:
            allimgstr.append(s.group(0))
            fignums.append(figcounter)
            figpaths.append(figpath)
            try:
                figwidth, figheight = imagesize.get(figpath)
            except:
                figwidth, figheight = jpeg_res(figpath)
            #try:
                #     figcaption = re.search('<figcaption>(.+?)</figcaption>', s.group(0)).group(1)
            #except: # no captions
                figcaption = ''
            figcaptions.append(figcaption)

            # SINGLE FIGURE LAYOUT
            # --------------------
            if layout == 'single':
                if figwidth > figheight:
                    sfigtw = fws[0]
                else:
                    sfigtw = fws[1]
                str_fig = _include_figure(figpath, figcounter, figcaption, figwidth=sfigtw)
                figsetup.append(1)

            # OPTIMAL/PAIRED FIGURE LAYOUT
            # ----------------------------
            if layout in ['optimal', 'paired']:
                if figwidth > figheight:
                    landscape.append(True)
                    orient.append(True)
                else:
                    landscape.append(False)
                    orient.append(False)

                if landscape[-2] == landscape[-1]:
                    if orient[-1] == True:
                        figtw = '0.45'
                    else:
                        figtw = fws[1]
                    str_fig = _include_subfigures(lastfigpath, figpath, figcounter-1, figcounter,
                                                  lastfigcaption, figcaption, figtw, figtw)
                    landscape[-1] = -1
                    if nl+nl+lastimgstr in textbody:
                        replacestr[nl+nl+lastimgstr] = " [\\ref{fig:"+str(figcounter-1)+"}]"
                    else:
                        replacestr[lastimgstr] = " [\\ref{fig:"+str(figcounter-1)+"}]"
                    figsetup[-1] = 0
                    figsetup.append(2)
                else:
                    if landscape[-1] == True:
                        sfigtw = fws[0]
                    else:
                        sfigtw = fws[1]
                    str_fig = _include_figure(figpath, figcounter, figcaption, figwidth=sfigtw)
                    figsetup.append(1)

            # Defining the fig strings to replace img strings with:
            lastimgstr = s.group(0)
            if nl+nl+lastimgstr in textbody:
                replacestr[nl+nl+lastimgstr] = " [\\ref{fig:"+str(figcounter)+"}]"+nl+nl+str_fig
            else:
                replacestr[lastimgstr] = " [\\ref{fig:"+str(figcounter)+"}]"+nl+nl+str_fig
            #print('-------------'+str(figcounter)+'-'+str(figsetup[-1]))
            #print(str_fig)
            figcounter = figcounter + 1

    # This is the last fix to pair up leftover images in optimal:
    if layout == 'optimal':
        if len(replacestr) != 0:
            loopfigs = figsetup+[-1]
            for ifig, fignum in enumerate(loopfigs):
                if loopfigs[ifig] == 1 and loopfigs[ifig+1] == 1:
                    if orient[ifig] == True:
                        figtw1, figtw2 = fws[0], fws[1]
                    else:
                        figtw1, figtw2 = fws[1], fws[0]
                    #print('********', fignum, figpaths[ifig], figpaths[ifig+1], fignums[ifig], ifig)
                    str_fig = _include_subfigures(figpaths[ifig], figpaths[ifig+1], fignums[ifig], fignums[ifig+1],
                                                  figcaptions[ifig], figcaptions[ifig+1], figtw1, figtw2)
                    if nl+nl+lastimgstr in textbody:
                        replacestr[nl+nl+allimgstr[ifig]] = " [\\ref{fig:"+str(fignums[ifig])+"}]"
                    else:
                        replacestr[allimgstr[ifig]] = " [\\ref{fig:"+str(fignums[ifig])+"}]"
                    replacestr[nl+nl+allimgstr[ifig+1]] = " [\\ref{fig:"+str(fignums[ifig+1])+"}]"+nl+nl+str_fig
                    loopfigs[ifig] = 0
                    loopfigs[ifig+1] = 2
                elif ((len(loopfigs) == (ifig+1))  or ( loopfigs[ifig+1] == -1)): 
                    break

    for key in replacestr:
        textbody = textbody.replace(key, replacestr[key])

    if len(replacestr) != 0:
        # Correct labels that have ended up beneath figures rather in in textbody:
        for s in re.finditer('end{figure} \\[\\\\ref{fig:(.+?)}\\]', textbody):
            num = s.group(1)
            textbody = textbody.replace('[\\ref{fig:'+str(int(num)-1)+'}]', 
                                '[\\ref{fig:'+str(int(num)-1)+'}] ' + '[\\ref{fig:'+str(int(num))+'}] ')
            textbody = textbody.replace('[\\ref{fig:'+str(int(num))+'}]', '')

        for s in re.finditer('end{figure}\\n \\[\\\\ref{fig:(.+?)}\\]', textbody):
            num = s.group(1)
            textbody = textbody.replace('[\\ref{fig:'+str(int(num)-1)+'}]', 
                                '[\\ref{fig:'+str(int(num)-1)+'}] ' + '[\\ref{fig:'+str(int(num))+'}] ')
            textbody = textbody.replace('[\\ref{fig:'+str(int(num))+'}]', '')

    return textbody, figcounter


def _include_figure(figpath, fignum, figcaption, figwidth=0.5):
    """Fills LaTeX code for figure/image inclusion."""
    str_fig =  "\\begin{figure}"+nl
    str_fig += "    \\centering"+nl
    str_fig += "    \\includegraphics[width="+str(figwidth)+"\\textwidth]{"+figpath+"}"+nl
    str_fig += "    \\caption{"+figcaption+"}"+nl
    str_fig += "    \\label{fig:"+str(fignum)+"}"+nl
    str_fig += "\\end{figure}"

    return str_fig


def _include_subfigures(figpath1, figpath2, fignum1, fignum2, figcaption1, figcaption2, fw1, fw2):
    """Fills LaTeX code for figure with two subfigures."""
    str_fig =  "\\begin{figure}[htbp!]"+nl
    str_fig += "  \\centering"+nl
    str_fig += "  \\begin{subfigure}[t]{"+fw1+"\\textwidth}"+nl
    str_fig += "    \\includegraphics[width=\\textwidth]{"+figpath1+"}"+nl
    str_fig += "    \\caption{"+figcaption1+"}"+nl
    str_fig += "    \\label{fig:"+str(fignum1)+"}"+nl
    str_fig += "  \\end{subfigure}"+nl
    str_fig += "  \\begin{subfigure}[t]{"+fw2+"\\textwidth}"+nl
    str_fig += "    \\includegraphics[width=\\textwidth]{"+figpath2+"}"+nl
    str_fig += "    \\caption{"+figcaption2+"}"+nl
    str_fig += "    \\label{fig:"+str(fignum2)+"}"+nl
    str_fig += "  \\end{subfigure}"+nl
    str_fig += "  \\caption{"+nl
    str_fig += "  \\label{fig:"+str(fignum1)+"-"+str(fignum2)+"}"+nl
    str_fig += "  }"+nl
    str_fig += "\\end{figure}"+nl

    return str_fig


def post_to_latex(f, post, posts, attachments, figcounter, media_archive='', fig_layout='optimal', show_image_refs=True, end_document=False):
    """Puts the main text body through all the conversions it should
    need to successfully write to a .tex file that can be compiled
    without any further editing.

    ... Hopefully.

    Parameters
    -----------
    f : open file
        .tex file containing all LaTeX code.
    post : parse.Post
        Post object containing all data for one post.
    figcounter : int
        Counter for figures to continue number through till end of file.
    media_archive : str, default=''
        Path to Wordpress-exported media archive.
    fig_layout : str, default='optimal'
        See image_to_latex for explanation of different options: 'single', 'paired', 'optimal'
    end_document : bool, default=False
        If True, will write end document command in f.

    Returns
    --------
    figcounter : int
        As above, updated to new figure count.
    """

    newbody = post.body
    # Replace new lines:
    newbody = newbody.replace('<br>', nl)
    if '<br>' in newbody:
        print("Something's gone very wrong. Be worried, be very worried.")
    # Replace horizontal rules
    newbody = newbody.replace('<hr />', '')
    newbody = newbody.replace('<hr>', horizontal_rule)
    wp_blocks = False
    if '<!-- wp:paragraph -->' in newbody:
        wp_blocks = True
        newbody = wp_blocks_to_latex(newbody)
    # Fix references to images:
    # gallery ????

    newbody = unpack_gallery(newbody, attachments, figcounter)

    if not media_archive == '':
        newbody, figcounter = image_to_latex(newbody, media_archive, figcounter, layout=fig_layout, wp_blocks=wp_blocks)
    # Fix URLs and symbols:
    newbody = urls_to_latex(newbody)
    newbody = symbols_to_latex(newbody)
    # Replace HTML tags:
    newbody = html_tags_to_latex(newbody)
    # print(newbody)
    newbody = hideImageRefs(newbody, False)
    #print(newbody)
    # Update lists:
    newbody = newbody.replace("<ul>", "\\begin{itemize}")
    newbody = newbody.replace("</ul>", "\\end{itemize}")
    # Remove excessive newlines, but never less than two:
    newbody = newbody.replace(3*nl, 2*nl).replace(3*nl, 2*nl).replace(3*nl, 2*nl)
    # Fix single-line picture references:
    newbody = newbody.replace(nl+nl+'[\\ref{fig', '[\\ref{fig')
    

    # Finally write the adjusted text body:
    f.write("\\section{"+post.title+"}"+nl)

    # Add the publication date at the end of the post:
    datestr = date_string(post.post_date)
    f.write(nl+'\\noindent '+datestr)

    f.write(nl)
    f.write(newbody+nl)

    #IPython.embed()

    f.write(nl)

    if end_document:
        f.write("\\end{document}"+nl)

    return figcounter

def unpack_gallery(textbody, attachments, fignumber):
    matches = re.findall("\\[gallery.*\\]", textbody)
    for match in matches:
        print("====== " + match + " ======")
        numberMatches = re.findall('[0-9]+', match)
        imageIds = [int(x) for x in numberMatches]
        replacement = ""
        imagePaths = []
        for id in imageIds:
            post = findImagePostByID(attachments, id)
            if (post != "") :
                imagePaths.append(attachment2ImagePath(post))
            else:
                logger.warning("Could not find post %s", id)
        n = len(imagePaths) 
        i=0
        while (i < n):
            if (n-i > 1): 
                replacement += _include_subfigures(imagePaths[i], imagePaths[i+1], fignumber, fignumber + 1,
                                                  "", "", "0.45", "0.45") 
                i +=2
                fignumber += 2
            else:
                replacement += _include_figure(imagePaths[i], fignumber, "")
                fignumber = fignumber + 1

        textbody = textbody.replace(match, replacement)       
    return textbody

def findImagePostByID(posts, id):
    idStr = str(id)
    for post in posts:
        if (post.id == idStr):
            return post 
    return ""

def attachment2ImagePath(attachment):
    imageFile = str(attachment.url).replace("https://www.outofthemiryblog.com/wordpress/", "/home/clt/Projects/Blog2Book/")
    return imageFile

def symbols_to_latex(textbody):
    """Replaces common punctuation and currency symbols with LaTeX equivalents.
    Note: definitely not an exhaustive list.
    """

    textbody = textbody.replace('€', '\\euro')
    textbody = textbody.replace('¥', ' yen')
    textbody = textbody.replace('$', '\\$')
    textbody = textbody.replace('°', '$^\\circ$')
    textbody = textbody.replace('&lt;', '$<$')
    textbody = textbody.replace('#', '\\#')
    textbody = textbody.replace('%', '\\%')
    textbody = textbody.replace('&', '\\&')

    return textbody


def urls_to_latex(textbody):
    """Replaces HTML-type URLs with LaTeX-friendly format.
    """

    for s in re.finditer('<a href=(.+?)/a>', textbody):
        url = re.search('"(.+?)"', s.group(0)).group(1)
        des = re.search('>(.*)<', s.group(0)).group(1)
        #str_url = "\\begin{center}"+nl+"\\href{"+url+"}{"+des+"}"+nl+"\\end{center}"+nl
        if (len(des) == 0) :
            des = url
        str_url = "\\href{"+url+"}{"+des+"}"+nl
        textbody = textbody.replace(s.group(0), str_url)
    return textbody

def hideImageRefs(textbody, show_image_refs):
        if (show_image_refs):
            return textbody
        textbody = re.sub("<a href=\"https:.*jpg\">","", textbody)
        textbody = re.sub("</a>", "", textbody)
        textbody = re.sub("\\[\\\\ref{.*}\\]","", textbody)
        textbody = re.sub("\\\\&nbsp;", "", textbody)
        return textbody

def hideHtml(textbody):
        textbody = re.sub("\\[\\\\ref{.*}\\]","", textbody)
        return textbody
        

def wp_blocks_to_latex(textbody):

    # Paragraph block:
    textbody = textbody.replace('<!-- wp:paragraph -->\n<p></p>\n<!-- /wp:paragraph -->', '')
    for s in re.finditer('<!-- wp:paragraph(.+?)-->\n<(.+?)>(.+?)</p>\n<!-- /wp:paragraph -->', textbody):
        parstr = s.group(0)
        textbody = textbody.replace(parstr, s.group(3))
    # List:
    for s in re.finditer('<!-- wp:list(.+?)-->\n(.+?)\n<!-- /wp:list -->', textbody):
        liststr = s.group(0)
        textbody = textbody.replace(liststr, s.group(2))
    # Horizontal rule:
    textbody = textbody.replace('<!-- wp:separator -->\n<hr class="wp-block-separator" />\n<!-- /wp:separator -->',
                                horizontal_rule)
    # Video block:
    for s in re.finditer('<!-- wp:video(.+?)-->\n(.+?)\n<!-- /wp:video -->', textbody):
        link = re.search('src="(.+?)"', s.group(0)).group(1)
        str_url = "\\href{"+link+"}{Link to Video.}"+nl
        textbody = textbody.replace(s.group(0), str_url)

    return textbody


# -------------------------------------------------------------------
# OTHER USEFUL FUNCTIONS
# -------------------------------------------------------------------

def jpeg_res(filename):
   """"This function prints the resolution of the jpeg image file passed into it
   """

   # open image for reading in binary mode
   with open(filename,'rb') as img_file:
       # height of image (in 2 bytes) is at 164th position
       img_file.seek(163)
       # read the 2 bytes
       a = img_file.read(2)
       # calculate height
       height = (a[0] << 8) + a[1]
       # next 2 bytes is width
       a = img_file.read(2)
       # calculate width
       width = (a[0] << 8) + a[1]

   return width, height


