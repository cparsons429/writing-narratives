import requests
from bs4 import BeautifulSoup

ticker = input("Enter the stock you want to check out: ")
# this scrapes for the stock
r = requests.get("https://finance.yahoo.com/quote/%s?p=%s" % (ticker, ticker))

soup = BeautifulSoup(r.content, "html5lib")

# this retrieves the stock title as a string
string = str(soup.title)
init_title = string.replace("<title>%s : Summary for " % (ticker), "")
fin_title = init_title.replace(" - Yahoo Finance</title>", "")

print("The company is: " + fin_title)

