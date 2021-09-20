import json, re, time, os, requests, traceback
from PIL import Image
from io import BytesIO
from lxml import html
from lxml.html.clean import clean_html
import pylatex as tex
from pylatex.utils import NoEscape

# to get weather data, edit the following
# this uses openweathermap, if you don't have an api key for that
# head over to https://openweathermap.org/api and create one (it's free)
# if you don't want weather, just leave the values as they are
api_key = "YOURAPIKEY"          # get on openweathermap.com
lat = "60.001201"               # your latitude
lon = "80.120301"               # your longitude
city_name = "YOURCITYNAME"      # your city
units = "metric"                # preferred unit (metric or imperial)

# select one of the newspapers from the dictionary below
# i.e. "nytimes" (New York Times, US)
#  or  "guardian" (The Guardian, UK/International)
#  or  "cbrtimes" (Canberra Times, AUS)
#  or  "zeitonline" (Die Zeit, GER)
MYNEWSPAPER = "nytimes"


newspapers={"nytimes":{
                "url": "https://www.nytimes.com/",
                "pattern": "https\:\/\/www\.nytimes\.com\/[0-9]+\/[0-9]+\/[0-9]+\/[a-z\-\/]+\.html",
                "title_text": "//h1/text()",
                "title_img": "//picture/img",
                "article_text": "//section/div/div/p",
                "logo": "nytimes.png",
                "sections": ["", "section/world", "section/technology", "section/politics", "section/business", "section/science/space"],
                "numbers_sections" : [10, 5, 5, 2, 2, 2]},
            "guardian":{
                "url": "https://www.theguardian.com/",
                "pattern": "https\:\/\/www\.theguardian\.com\/[a-z]+\/[0-9]+\/[a-z]+\/[0-9]+\/[a-z\-\/]+",
                "title_text": "//h1/text()",
                "title_img": "//picture/img",
                "article_text": "//div[@id='maincontent']/div/p",
                "logo": "guardian.png",
                "sections" : ["", "us-news", "technology", "environment"],
                "numbers_sections": [10, 5, 5, 5]
                },
            "cbrtimes":{
                "url": "https://www.canberratimes.com.au/",
                "pattern": "https\:\/\/www\.canberratimes\.com\.au\/story\/[0-9]+\/[a-z0-9\-\/]+",
                "title_text": "//h1/text()",
                "title_img": "//picture/img",
                "article_text": "//div[@class='assets']/p",
                "logo": "cbrtimes.png",
                "sections" : ["", "news/technology", "news/environment", "news/national"],
                "numbers_sections": [10, 5, 5, 5]
                },
            "zeitonline":{
                "url": "https://www.zeit.de/",
                "pattern": "https\:\/\/www\.zeit\.de\/[a-z0-9\-\/]+\/[0-9]+-[0-9]+\/[a-z0-9\-\/]+",
                "title_text": "//h1/span[contains(@class,'heading__title')]/text()",
                "title_img": "//figure/div/noscript/img",
                "article_text": "//p[contains(@class, 'paragraph')]",
                "logo": "zeit.png",
                "sections" : ["", "wissen", "politik/deutschland", "politik/ausland", "sport"],
                "numbers_sections": [10, 5, 5, 5, 5]
                }
        }


# Want to add your own newspaper? I can't promise the following steps
# work in every case, but maybe they do, so give it a try ;)

# 1. Add a new entry in the newspaper dictionary above. Just follow the
#    format of the first four entries. 
# 2. Open your newspage in a browser and copy the url to "url": "..." in
#    the dict
# 3. Open a few different articles and look at their urls. Can you find a
#    pattern? Then add this pattern (using regex) to "pattern": "..." in
#    the dict. Don't know what regex is? I'm sure you'll find a good tutorial
#    on the Internet
# 4. Open a few different articles again, right-click on their title and click
#    on 'Inspect Element'. Find an xpath to the title and set this xpath in
#    "title_text": "..." in the dict. Don't know what xpath is and don't really
#    want to find out? Then you can try right-clicking on that html element that
#    was highlighted after you clicked 'Inspect Element'. There should be an
#    option like 'Copy' and then 'XPath' somewhere. You can set the "title_text"
#    in the dict to that xpath and add '/text()' behind it, but most likely it
#    won't work perfectly...
# 5. Repeat the same procedure for the title image (just without the '/text()')
#    behind the xpath
# 6. Same for your article_text
# 7. Download the logo image of your newspaper to the "news_icons" folder and
#    add "logo": "name_of_logo_image.png" to the dict
# 8. Go to different sections of your newspage and add the ones you like to
#    the dict
# 9. Finally specify the number of articles for each section
# 10. Set MYNEWSPAPER to your newly added newspaper and run the program.
# 11. Did it work?
#     YES -> Great, congratulations!
#     NO -> Try setting 'show_errors' to 'True' (just a bit below here). When
#           you run the program again, it will output errors, so you can see
#           what went wrong. Mostly it is stuff connected to xpath.
#           Otherwise you'll need to work your way through the code below.
#           Good luck with that ;)









base_url = newspapers[MYNEWSPAPER]["url"]
degrees = "C" if units=="metric" else "F"
# if downloading an article fails, the error is suppressed (not printed)
# unless you set this to true
# this is helpfull when you add a new newspaper and want to find out
# what is failing
show_errors = False






session = requests.session()
get_weather = api_key != "YOURAPIKEY" # don't change this value!

# dict to store everything in
data = {"articles": []}

url_pattern = newspapers[MYNEWSPAPER]["pattern"]
numbers_sections = newspapers[MYNEWSPAPER]["numbers_sections"]

# define a function to make text latex safe, i.e. add backslash before special char
def latex_safe(t):
    for r in ["$", "%"]:
        t = t.replace(r, "\\"+r)
    t = t.replace(r"&ldquo;", "''")
    t = t.replace(r"&rdquo;", "''")
    return t.replace("\n", " ")

def remove_duplicates(x):
    n = []
    for y in x:
        if y in n: continue
        n.append(y)
    return n

all_urls = []

for i, section in enumerate(newspapers[MYNEWSPAPER]["sections"]):
    # get website and store it in main_tree
    main_tree = html.fromstring(session.get(base_url+section).content)
    # make all links absolute, so that we can find them easier
    main_tree.make_links_absolute(base_url)
    # finally get all links (and remove duplicates)
    links = remove_duplicates(re.findall(url_pattern, str(html.tostring(main_tree))))

    # now loop through all links and store the data in our data dict
    j = 0
    successes = 0
    while successes<min(numbers_sections[i], len(links)):
        link = links[j]
        if link in all_urls:
            j += 1
            continue
        print(f"\rDownloading {sum(numbers_sections[:i])+successes+1} of {sum(numbers_sections)}", end="")
        try:
            tree = html.fromstring(session.get(link).text)
            tree.make_links_absolute(base_url)

            # in case there is always a known article that you don't want
            # (e.g. advertisment) with the same link pattern, skip it here
            # with a known condition
            # here: if the title is " Space for ", then skip
            if tree.xpath(newspapers[MYNEWSPAPER]["title_text"])[0] == " Space for ":
                continue
            data["articles"].append({})
            data["articles"][-1]["url"] = link
            # get the title of the article using xpath
            data["articles"][-1]["title"] = latex_safe(tree.xpath(newspapers[MYNEWSPAPER]["title_text"])[0])

            # check if there is a title image and if there is, download it,
            # convert it to grayscale and save it
            try:
                title_image = tree.xpath(newspapers[MYNEWSPAPER]["title_img"])[0]
                img_url = title_image.attrib["src"]
                img_path = "news_imgs/image_%04d.jpg"%(sum(numbers_sections[:i])+successes)
                r = session.get(img_url, stream=True)
                Image.open(BytesIO(r.content)).convert("L").save(img_path)

                data["articles"][-1]["img_url"] = img_url
                data["articles"][-1]["img_path"] = img_path
                if "alt" in title_image.attrib.keys():
                    data["articles"][-1]["img_caption"] = latex_safe(title_image.attrib["alt"])
                else:
                    data["articles"][-1]["img_caption"] = ""

            except Exception:
                data["articles"][-1]["img_url"] = ""
                data["articles"][-1]["img_path"] = ""
                data["articles"][-1]["img_caption"] = ""

            # now get the article text
            paragraphs = tree.xpath(newspapers[MYNEWSPAPER]["article_text"])
            data["articles"][-1]["text"] = []
            for p in paragraphs:
                data["articles"][-1]["text"].append(latex_safe(p.text_content()))
            successes += 1
            all_urls.append(link)
        except Exception as e:
            if show_errors:
                print("\rSome error occured, skipping link", link)
                traceback.print_exc()
                time.sleep(1)
                print("\n\n")
        j += 1
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

if get_weather:
    weather_url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely,hourly&appid={api_key}&units={units}"
    weather = json.loads(requests.get(weather_url).content)


# add the iconic image of the newspaper as well as a small weather info
title_table_latex = r"""
\begin{table}[H]
    \begin{tabular}{m{2.85cm} m{5cm}}
        \hyperlink{weather}{\includegraphics[width=1cm]{weather_icons/%s.png}
        \raisebox{.35cm}{$%s}} &
        \includegraphics[width=5cm]{news_icons/%s}
    \end{tabular}
\end{table}
\vspace{-.5cm}"""
if get_weather:
    doc.append(NoEscape(title_table_latex % (weather["current"]["weather"][0]["icon"][:2],
                                            str(round(weather["current"]["temp"]))+"^\circ$"+degrees,
                                            newspapers[MYNEWSPAPER]["logo"])))
else:
    doc.append(NoEscape(title_table_latex % ("empty", "", newspapers[MYNEWSPAPER]["logo"])))

# make overview pages (max 12 articles per page)
# the overview consists of a table with alternating rows of images, titles, images, ...
img_str_latex = r"""
\centering
\hyperlink{art%s}{
    \includegraphics[width=0.3\textwidth,
                     height=0.11\textheight,
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
            if path=="": path="news_imgs/empty_image.jpg"
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
if get_weather:
    doc.append(NoEscape(r"""
    \hypertarget{weather}{\section*{Weather %s}}
    \begin{table}[H]
        \centering
        \begin{tabular}{m{.85cm} m{1.5cm} m{2.5cm} m{3.75cm} m{0.75cm}}
        \hline
    """ % city_name))

    weather_str_latex = r"""
    %s & \includegraphics[width=1.5cm]{weather_icons/%s.png} &
    \Large$%s^\circ$%s\small/$%s^\circ$%s & %s &
    \includegraphics[width=4mm]{weather_icons/drop} \small%s\%%\\"""

    # loop through all available days
    for d in weather["daily"]:
        day = time.strftime("%a", time.gmtime(d["dt"]-time.timezone)).upper()
        weatherday = d["weather"][0]
        doc.append(NoEscape(weather_str_latex % (day,
                                                weatherday["icon"][:2],
                                                round(d["temp"]["max"]),
                                                degrees,
                                                round(d["temp"]["min"]),
                                                degrees,
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
    doc.append(NoEscape(r"\begin{textblock}{\pgfmathresult}[1, 0](-35, 0.25) \noindent \hyperlink{page.%d}{OVERVIEW} \end{textblock}"%(i//12+1)))
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
        break
    except:
        pass
        #break
if(i==4):
    print("ERROR: Failed to generate pdf!")
