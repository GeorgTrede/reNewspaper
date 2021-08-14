import json, re, time, os, requests

from PIL import Image
from io import BytesIO
from lxml import html
from lxml.html.clean import clean_html
import pylatex as tex
from pylatex.utils import NoEscape

#
# In case you just want to read the NYT you just need to edit the following
# things. Otherwise have a look at the rest of the program and work your way
# through it. Either way, I don't guarantee that this works, all I can say is
# it works for me ;)
#

# base url of your news website
base_url = "https://www.nytimes.com/"

# different sections you want to get articles from
# e.g. politics, sports, travel, world etc.
# find the website for these sections and add the path (without
# base url) here. First one "" is to get the articles on the
# main website.
sections = ["", "section/world", "section/technology",
            "section/politics", "section/business"]
# and the numbers of articles you want for each section, same order
# make sure sections and numbers_sections have the same length!
numbers_sections = [20, 10, 10, 5, 5]

# to also get weather data, edit the following
# this uses openweathermap, so head over there and create an api key or app id
# or something like that if you haven't done that already
api_key = "YOURAPIKEY"          # get on openweathermap.com
lat = "60"                      # your latitude
lon = "80"                      # your longitude
city_name = "YOURCITYNAME"      # your city (optional)












session = requests.session()

# dict to store everything in
data = {"articles": []}

# we will use regex to find the links to the articles
# for NYT a typical url looks like this:
# https://www.nytimes.com/2021/08/12/us/politics/supreme-court-new-york-eviction-moratorium.html
# so the regex could be
url_pattern = "https\:\/\/www\.nytimes\.com\/[0-9]+\/[0-9]+\/[0-9]+\/[a-z\-\/]+\.html"

# define a function to make text latex safe, i.e. add backslash before special char
def latex_safe(t):
    for r in ["$", "%"]:
        t = t.replace(r, "\\"+r)
    return t.replace("\n", "")

for i, section in enumerate(sections):
    # get website and store it in main_tree
    main_tree = html.fromstring(session.get(base_url+section).content)
    # make all links absolute, so that we can find them easier
    main_tree.make_links_absolute(base_url)
    # finally get all links (and remove duplicates)
    links = list(set(re.findall(url_pattern, str(html.tostring(main_tree)))))
    
    # now loop through all links and store the data in our data dict

    for j, link in enumerate(links[:numbers_sections[i]]):
        print(f"\rDownloaded {sum(numbers_sections[:i])+j+1} of {sum(numbers_sections)}", end="")
        data["articles"].append({})
        tree = html.fromstring(session.get(link).text)
        data["articles"][-1]["url"] = link
        # get the title of the article using xpath
        # for NYT it is the first h1
        data["articles"][-1]["title"] = latex_safe(tree.xpath("//h1/text()")[0])

        # check if there is a title image and if there is, download it
        # and convert it to grayscale
        # for NYT this is in //picture/img
        try:
            title_image = tree.xpath("//picture/img")[0]
            img_url = title_image.attrib["src"]
            img_path = ".news_imgs/image_%04d.jpg"%(sum(numbers_sections[:i])+j)
            r = session.get(img_url, stream=True)
            Image.open(BytesIO(r.content)).convert("L").save(img_path)

            data["articles"][-1]["img_url"] = img_url
            data["articles"][-1]["img_path"] = img_path
            if "alt" in title_image.attrib.keys():
                data["articles"][-1]["img_caption"] = title_image.attrib["alt"]
            else:
                data["articles"][-1]["img_caption"] = ""

        except IndexError:
            data["articles"][-1]["img_url"] = ""
            data["articles"][-1]["img_path"] = ""
            data["articles"][-1]["img_caption"] = ""
        
        # now get the article text
        # for NYT the <p> elements are here:
        paragraphs = tree.xpath("//section/div/div/p")
        data["articles"][-1]["text"] = []
        for p in paragraphs:
            data["articles"][-1]["text"].append(p.text_content())
print()
# that was the scraping part

# now comes the LaTeX part, i.e. making the actual document

# firstly create a document and set margins and other options
doc = tex.Document(geometry_options={"tmargin":"1cm",
                                     "lmargin":"1cm",
                                     "rmargin":"1cm",
                                     "bmargin":"1cm"},
                   page_numbers=False, document_options="a5paper")

# add a bunch of packages
doc.packages.append(tex.Package("graphicx"))
doc.packages.append(tex.Package("array"))
doc.packages.append(tex.Package("hyperref"))
doc.packages.append(tex.Package("caption"))
doc.packages.append(tex.Package("pgf"))
doc.packages.append(tex.Package("float"))
doc.packages.append(tex.Package("textpos", options="absolute, overlay"))
# do some stuff for the "back to overview" button
doc.preamble.append(NoEscape(r"""\setlength{\TPHorizModule}{2.0 pt}
\textblockorigin{\paperwidth}{1.0 pt}"""))
doc.preamble.append(NoEscape(r'\pgfmathwidth{"Overview and""}'))


weather_url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely,hourly&units=metric&appid={api_key}"
weather = json.loads(requests.get(weather_url).content)


# add the iconic image of the newspaper as well as a small weather info
title_table_latex = r"""
\begin{table}[H]
    \begin{tabular}{m{2.85cm} m{5cm}}
        \hyperlink{weather}{\includegraphics[width=1cm]{weather_icons/%s.png}
        \raisebox{.35cm}{$%s^\circ$C}} &
        \includegraphics[width=5cm]{news.png}
    \end{tabular}
\end{table}
\vspace{-.5cm}"""
doc.append(NoEscape(title_table_latex % (weather["current"]["weather"][0]["icon"][:2],
                                         round(weather["current"]["temp"]))))

# make overview pages (max 12 articles per page)
# the overview consists of a table with alternating rows of images, titles, images, ...
img_str_latex = r"""
\centering
\hyperlink{art%s}{
    \includegraphics[width=0.3\textwidth,
                     height=0.12\textheight,
                     keepaspectratio]
                     {%s}
} &"""
title_str_latex = r"\hyperlink{art%s}{%s} &"
for j in range(0, len(data["articles"]), 12):
    # begin table
    doc.append(NoEscape(r"""
    {\renewcommand{\arraystretch}{1.3}
    \begin{table}[H]
    	\centering
    	\begin{tabular}{ | m{0.3\textwidth} | m{0.3\textwidth} | m{0.3\textwidth} |m{0.001\textwidth} }
    	\hline"""))
    # loop through the rows for the current page
    for i in range(j,min(j+12,len(data["articles"])),3):
        add_str = ""
        # loop through the article of the current row, once for image,
        # once for the title
        art_remaining = 3
        while(i+art_remaining > len(data["articles"])):
            art_remaining -= 1
        for n in range(art_remaining):
            path = data["articles"][i+n]["img_path"]
            if path=="": path=".news_imgs/empty_image.jpg"
            add_str += img_str_latex % (i+n, path)
        add_str += r" \\ "
        doc.append(NoEscape(add_str))
        add_str = ""
        for n in range(art_remaining):
            add_str += title_str_latex % (i+n, data["articles"][i+n]["title"])
        add_str += r" \\ "
        doc.append(NoEscape(add_str))
        # add hline to separate from next "image & title" row
        doc.append(NoEscape(r"\hline"))
    # end table for this page and add pagebreak
    doc.append(NoEscape(r"""\end{tabular}
                            \end{table}"""))
    doc.append(NoEscape(r"\newpage"))

# add weather page
doc.append(NoEscape(r"""
\hypertarget{weather}{\section*{Weather %s}}
\begin{table}[H]
    \centering
    \begin{tabular}{m{.85cm} m{1.5cm} m{2.5cm} m{3.75cm} m{0.75cm}}
    \hline
""" % city_name))

weather_str_latex = r"""
%s & \includegraphics[width=1.5cm]{weather_icons/%s.png} &
\Large$%s^\circ$C\small/$%s^\circ$C & %s &
\includegraphics[width=4mm]{weather_icons/drop} \small%s\%%\\"""

# loop through all available days
for d in weather["daily"]:
    day = time.strftime("%a", time.gmtime(d["dt"]-time.timezone)).upper()
    weatherday = d["weather"][0]
    doc.append(NoEscape(weather_str_latex % (day,
                                             weatherday["icon"][:2],
                                             round(d["temp"]["max"]),
                                             round(d["temp"]["min"]),
                                             weatherday["description"].capitalize(),
                                             round(d["pop"]*100))))
    doc.append(NoEscape(r"""\hline"""))
doc.append(NoEscape(r"""\end{tabular}\end{table}\newpage"""))

# now add all the real newspaper part, i.e. all the articles

article_img_latex = r"""
\begin{figure}[H]
    \centering
    \includegraphics[width=0.85\linewidth]{%s}
    \captionsetup{labelformat=empty}
    \caption{\textit{%s}}
\end{figure}"""

for i, article in enumerate(data["articles"]):
    # add section, i.e. title with link target
    doc.append(NoEscape(r"\section*{%s} \hypertarget{art%s}{ }" % (article["title"], i)))
    # add "Overview" button in top right corner
    doc.append(NoEscape(r"\begin{textblock}{\pgfmathresult}[1, 0](-35, 0.25) \noindent \hyperlink{page.%d}{OVERVIEW} \end{textblock}"%(i//12)))
    # if there is an image present, add it now
    if article["img_path"]!= "":
        doc.append(NoEscape(article_img_latex%(article["img_path"],article["img_caption"])))
    doc.append(NoEscape(r"\noindent"))
    for text in article["text"]:
        doc.append(text)
        doc.append(NoEscape(r"\\\\"))
    doc.append(NoEscape(r"\newpage"))

for i in range(5):
    try:
        x = doc.generate_tex("News")
        #os.system("rm .news_imgs/image*.jpg")
        break
    except:
        pass
        #break
if(i==4):
    print("ERROR: Failed to generate pdf!")