if [ $# -eq 0 ]
then
	ip=10.11.99.1
else
	ip=$1
fi

if ping -c2 -t50 $ip &> /dev/null
then
	echo "Reached reMarkable, ready to start"
else
	echo "reMarkable couldn't be reached, make sure it's turned on and you entered the correct IP address!"
	exit
fi

echo "Starting to generate newspaper..."
echo ""
echo "Fetching articles from website..."
python3 news.py
echo "TeX file generated, generating pdf file now..."
latexmk -f -pdf -silent News.tex &> /dev/null
mv News.pdf Newspaper.pdf
rm News.*
mv Newspaper.pdf News.pdf
echo "Done"
echo "Uploading to reMarkable now..."

id_of_news_doc=09dc93df-ce0f-4e28-976f-934b2ed5acd5

scp News.pdf root@$ip:/home/root/.local/share/remarkable/xochitl/$id_of_news_doc.pdf
ssh root@$ip "rm /home/root/.local/share/remarkable/xochitl/$id_of_news_doc.thumbnails/*" &> /dev/null

echo "Done"
echo "Enjoy your day!"
