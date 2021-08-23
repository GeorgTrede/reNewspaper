if [ $# -eq 0 ]
then
	ip=10.11.99.1
else
	ip=$1
fi

id_of_news_doc=09dc93df-ce0f-4e28-976f-934b2ed5acd5

echo ""
echo "▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄"
echo "█ ▄▄▀█ ▄▄██ ▀██ █ ▄▄█ ███ █ ▄▄█▀▄▄▀█ ▄▄▀█▀▄▄▀█ ▄▄█ ▄▄▀█"
echo "█ ▀▀▄█ ▄▄██ █ █ █ ▄▄█▄▀ ▀▄█▄▄▀█ ▀▀ █ ▀▀ █ ▀▀ █ ▄▄█ ▀▀▄█"
echo "█▄█▄▄█▄▄▄██ ██▄ █▄▄▄██▄█▄██▄▄▄█ ████▄██▄█ ████▄▄▄█▄█▄▄█"
echo "▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀"
echo ""


if ping -c2 -t50 $ip &> /dev/null
then
	echo "Reached reMarkable ip, ready to start"
else
	echo "reMarkable couldn't be reached, make sure it's turned on and you entered the correct IP address!"
	exit
fi

echo "Starting to generate newspaper..."
echo "Fetching articles from website..."
python3 news.py
echo "TeX file generated, trying to generate pdf file now..."


for i in {1..5}
do
	latexmk -f -pdf -silent News.tex &> log_file.txt

	if grep -i "error" log_file.txt &> /dev/null
	then
		if [ $i -eq 5 ]
		then
			echo ""
			echo "An ERROR occured while generating the pdf. It is stored in 'log_file.txt':"
			cat log_file.txt
		else
			echo -en "Attempt $i of 5 failed, trying again...\r"
		fi
	else
		mv News.pdf Newspaper.pdf
		rm News.*
		mv Newspaper.pdf News.pdf
		echo "Done                                  "
		echo "Uploading to reMarkable now..."

		scp News.pdf root@$ip:/home/root/.local/share/remarkable/xochitl/$id_of_news_doc.pdf
		ssh root@$ip "rm /home/root/.local/share/remarkable/xochitl/$id_of_news_doc.thumbnails/*" &> /dev/null
	
		echo "Done"
		echo "Enjoy your day!"
		exit
	fi
done
