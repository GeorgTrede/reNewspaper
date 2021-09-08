echo ""
echo "▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄"
echo "█ ▄▄▀█ ▄▄██ ▀██ █ ▄▄█ ███ █ ▄▄█▀▄▄▀█ ▄▄▀█▀▄▄▀█ ▄▄█ ▄▄▀█"
echo "█ ▀▀▄█ ▄▄██ █ █ █ ▄▄█▄▀ ▀▄█▄▄▀█ ▀▀ █ ▀▀ █ ▀▀ █ ▄▄█ ▀▀▄█"
echo "█▄█▄▄█▄▄▄██ ██▄ █▄▄▄██▄█▄██▄▄▄█ ████▄██▄█ ████▄▄▄█▄█▄▄█"
echo "▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀"
echo ""


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
		echo "Uploading to reMarkable cloud now..."

		rmapi rm News
		rmapi put News.pdf
	
		echo "Done"
		echo "Enjoy your day!"
		exit
	fi
done
