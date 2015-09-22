from __future__ import print_function
from bs4 import BeautifulSoup
import requests
import time
from collections import OrderedDict
'''
How the data is formatted:

Basic info is spread out over multiple lines labeled with the itemprop name
by formatting and splitting on \n and removing all lines that are blank we get the text
back cleanly

Price information is in its own span labeled with the class r-title-price. One of these
classes has multiple lines and that is the one I choose to eliminate duplicates

Mileage information does not have it's own nice label. so we have to search for all table
elements with the label 'val'. To do this I have to iterate through and only grab the
element if it contains Miles in the text.

Finally the links are by far the ugliest. There are two types of links by the looks 
of it, external and internal. There are duplicate links and there doesn't seem to be 
a better way of finding them than searching all hrefs for the word 'detail'.

If the link is an internal link we have to add the base url to it. If the link is an 
external link we can just save it as is.

How this could fail: 
- website drops the convention of including Miles in every link named miles
- website does not include 2 miles tag per every car
- website changes their link methods
- there is an issue where the count of miles, information, prices and links stops lining up
'''



def get_next_page(url):
	'''find the link which will go to the next page and return it'''
	r = requests.get(url)
	soup = BeautifulSoup(r.text)
	pages = soup.findAll('a',{'class':'j-singlepage'},href=True)
	for val in pages:
		if 'Next' in val.get_text():
			return(val['href'])
	return None

def remove_blanks(list):
	'''remove blank strings from a list'''
	return [field for field in list if field]

def clean_up_soup(text):
	'''do basic text formatting to text returned from soup'''
	return text.replace(' ','').replace('Miles','').encode('utf-8','ignore').split('\n')

def parse_url(url):
	'''extract relevant data from a url'''
	information_list = []
	price_list = []
	mile_list = []
	links_list = []
	r = requests.get(url)
	soup = BeautifulSoup(r.text)

	#get a list of each element we are interested in
	information = soup.findAll(itemprop="name")
	prices = soup.findAll('span',{'class':'r-title-price'})
	milage = soup.findAll('span',{'class':'val'})
	links = soup.findAll('a',href=True)


	#extract relevant data and clean it up for each element we are interested in
	for val in milage:
		if 'Miles' in val.get_text():
			data = clean_up_soup(val.get_text())
			data = remove_blanks(data)
			mile_list.append(data[0])

	for item in information:
		data = clean_up_soup(item.get_text())
		data = remove_blanks(data)
		information_list.append('|'.join(data))

	for item in prices:
		data = clean_up_soup(item.get_text())
		if len(data) > 1:
			data = remove_blanks(data)
			price_list.append(data[0])
	
	for item in links:
		link = item['href']
		if 'detail' in link:
			if '==' in link:
				link = link[:link.find('==')]
			if 'http:' not in link:
				link = 'http://www.vast.com'+link
			links_list.append(link)

	#remove duplicates from lists which contain them
	links_list = list(OrderedDict.fromkeys(links_list))
	mile_list = mile_list[::2]

	return (mile_list,price_list,information_list,links_list)

def write_url(url):
	'''given a url write relevant information to file'''
	miles,prices,information,links = parse_url(url)
	with open('database.txt','at') as f:
		for i in range(len(miles)):
			print('{info}\t{price}\t{miles}\t{link}'.format(info=information[i],
				price=prices[i],miles=miles[i],link=links[i]),file=f)

def build_db(make,model,zip,verbose=True):
	'''
	driver function:

	Given make, model, and location write price, mileage ,basic information and 
	a csv.
	'''
	base_url = 'http://www.vast.com'
	url = base_url+'/cars/make-{make}/model-{model}/location-{zip}'
	url = url.format(make=make,model=model,zip=zip) #zip can also be a city like 'Minneapolis'
	write_url(url)
	next_url = get_next_page(url)
	while(next_url is not None):
		if verbose:
			print(base_url+next_url)
		write_url(base_url+next_url)
		next_url = get_next_page(base_url+next_url)
		time.sleep(10)

if __name__=='__main__':
	build_db('Volkswagen','Golf','Chicago')







