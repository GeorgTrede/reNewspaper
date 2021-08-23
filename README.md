# reNewspaper

![reNewspaper](https://user-images.githubusercontent.com/38717655/129438940-f853c106-e55b-4cf6-a3b2-ff79114fd6d3.jpg)


Scrape articles from a newspaper website and stuff them into a pdf file suitable for the reMarkable tablet (including clicky pdf links). It works for the NYT, The Guardian, Canberra Times und Die Zeit newspages, but if you want a different newspaper, the files kind of help guiding you the way to get there, too. The provided run.sh program also allows to update the News.pdf on the reMarkable to save the step of uploading the generated and deleting the old file manually.

## Who can use it?
Basically everyone who owns a reMarkable (or comparable device) and a computer. You should also be confident using the terminal.

Personally, I only tested it using a MacBook and I'm quite certain it works on Linux just as well, but I'm not sure about Windows, so sorry for that. You have to try and see on your own.

## Requirements
The news website is scraped using a python script, so obviously you'll need `python` installed. I tested it only using version 3.9.5, but I guess any version 3+ should work without problems. Versions below 3 _might_ run into errors though, try for yourself.

As for python-packages, you'll need `lxml`, `Pillow` and `pylatex`. Simply install them with this command:

`pip install lxml Pillow pylatex`


Next, you need to have some kind of latex installed. Just search for "Install LaTeX on YOUR OS NAME" if you haven't installed it anyway. Apart from the usual installation, I used `latexmk` to make my life easier, so make sure this is installed as well. [Here](https://mg.readthedocs.io/latexmk.html) is a guideline for that. An error with `pdftexcmds` was reported, which was solved by installing `sudo apt-get install texlive-latex-extra` (or using your package manager of choice).

And that's all you need.

## What do I need to do before I run it?
1. Download this repo and move the folder "News" wherever you want it.
2. Upload the News.pdf file included in the "News" folder to your reMarkable. I just used the official reMarkable desktop client for that.
3. ssh into your reMarkable. In case you don't know how, follow [these instructions](https://remarkablewiki.com/tech/ssh).
4. Navigate to `/home/root/.local/share/remarkable/xochitl/`
5. Find the unique id of the News file by executing `grep -i news *.metadata`. The result should look something like this:
```
root@reMarkable:~/.local/share/remarkable/xochitl# grep -i news *.metadata
09dc93df-ce0f-4e28-976f-934b2ed5acd5.metadata:    "visibleName": "News"
```
6. Write down the id, which would be `09dc93df-ce0f-4e28-976f-934b2ed5acd5` here. What if there is more than one result showing up? To solve this, make sure the uploaded News.pdf file is the only file (including Trash) that is called "News" and try step 5 again.
7. Back on your computer, navigate to the downloaded News folder.
8. Open the `run.sh` file, find the line starting with `id_of_news=` and replace the id here with the one you just wrote down.
9. While you are editing this file anyway, you can also edit the default used ip address of your reMarkable. If you usually connect your tablet via cable, just leave it as it is, otherwise find the local network ip and replace the `10.11.99.1` with it.
10. Lastly, open the `news.py` file and follow the comments in there.

## How do I run it?
Open your terminal and navigate to this "News" folder. Make sure your reMarkable is on and either connected to wifi or to your computer via cable. Then execute `bash run.sh REMARKABLEIPADDRESSHERE`. If you added your ip address in the steps above, you can also just run `bash run.sh`.

To make your life easier you could make an alias or something, but that's of course up to you.

## I like the NYT/Guardian/... but want more sports articles!
No problem! Just follow these steps:
1. Head over to the website of your newspaper and go to the section that you want articles from.
2. Check the url and copy the part behind the base url part (e.g. for `https://nytimes.com/section/sports` it would be `section/sports`).
3. Open the `news.py` file and find the part `sections = ["", ...]` in the `newspapers` dictionary. Make sure you're in the line corresponding to your chosen newspaper.
4. Add your new section (e.g. `section/sports`) to this list and remove sections you don't want. You can also change the order of the sections. The empty string `""` is the main page, so probably you want to keep that one.
5. Edit the line `numbers_sections = [20, 10, ...]` just below. This sets how many article for the according section are downloaded. So if you want more articles from the first section (or the main page), just make that number higher. Make sure that the length of this list matches with the length of the sections, otherwise you'll run into problems! Also if the numbers you enter are too high, there might be problems as well (beside the fact that your pdf file will blow up in size).

## I want to have a completely different newspaper!
Well no problem again! Just this time, you have to fully do it yourself ;)

I outlined the way to go in the `news.py` file, so I hope that this helps if you want to scrape a different newspage. Good luck!
