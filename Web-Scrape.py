# import necessary modules

import urllib
from bs4 import BeautifulSoup
import requests
import lxml  
from urllib.parse import urlparse,urljoin
import validators
import sys
from pandas import DataFrame
import nltk   
from nltk.corpus import stopwords
from nltk import word_tokenize
from nltk.util import ngrams
from collections import Counter
import re 
import pandas as pd
import csv
from sys import getsizeof
import numpy as np
from tqdm import tqdm

def If_Valid(url):       # Finds if URL is valid
    val=validators.url(url)
    if val==True: 
        print("Url is valid")  
        return True
    else: 
        print("Invalid url")
        return False          # Returns True or False

def Soup(url):          # Returns a BeautifulSoup object for a given input url
    try:
        res = requests.get(url)
        soup = BeautifulSoup(res.text,"lxml")   # Parsing using lxml
    except:
        print("url not available")
    return soup
    


def Find_Homepg(url):     # Finds the home page of a given URL
    c = 0
    l = []
    for s in url:
        l.append(s)
        if s == '/':c = c+1
        if c == 3 :break
    hp = "".join([str(item) for item in l ])    
    
    return(hp)


def Find_URLS(soup,hp):        # Finds all the links in the homepage and classifies whether a link is int or ext
    links = soup.select('a')   # Uses 'a' to get anchor tags
    ic,ec=0,0                  # count of int and ext links
    final_urls = []
    int_urls=[]
    ext_urls=[]
    for i in links:
        try:
            v = validators.url(i.get('href'))          # Using 'href' to get urls
        except:
            continue
        
        if i.get('href')[:len(hp)] == hp:      # check if links contain the homepg url in the beginning
            if v==True and i.get('href') not in final_urls :
                int_urls.append(i.get('href'))
                ic = ic+1
        else: 
            u = validators.url(i.get('href'))
            if u==True and i.get('href') not in final_urls:   # links that do not contain the homepg url
                ec = ec+1
                ext_urls.append(i.get('href'))
            else:
                h = validators.url(hp+i.get('href'))    # links that extend from the homepg
                if h==True and hp+i.get('href') not in final_urls and i.get('href') not in final_urls:
                    int_urls.append(hp+i.get('href'))
                    ic = ic+1
        final_urls = ext_urls+int_urls
    
    return ic+ec, int_urls, ext_urls , final_urls       # Returns count , internal , external and final links

def Title_Extract(final_urls):          # Extract title from top level pages
    final_titles = []
    for url in tqdm(final_urls, "Extracting Titles "):
        try:
            soup = Soup(url)              # Ignores invalid URLs
        except:
            print("url not found")
        try:
            title = soup.find('title').get_text()       # Ignores Pages with no Titles
        except:
            continue
        final_titles.append(title)
    return final_titles


def Metaxtract(final_urls):                          # Extract meta tags from top level pages
    count = 0
    mc = []
    for url in tqdm(final_urls, "Extractig Meta Tags "):    
        count = count + 1
        try:
            soup = Soup(url)
        except:
            continue
        meta = soup.find_all('meta')
        meta_names = []
        for m in meta:
            if m.get("name")!=None : meta_names.append(m.get("name"))   # Creating list of meta names
        content = []
        for  n in meta_names:               # Using list of names to get corresponding content
            for m in meta:
                if m.get("name") == n : content.append([n,m.get("content")])
        for c in content:
            if c not in mc: mc.append(c)         # Removing redundant meta tags
        mc.append(['Page  ', str(count)])
    
    return mc


def Textract(final_urls,stop_words):  # Extracts text from every page of the final list of urls (Top Pages)
    final_txt = []
    unidicts = []
    bidicts = []
    for u in tqdm(final_urls,"Extracting Text "):                                  
        try:
            soup = Soup(u)
        except:
            continue
        text = ' '.join(soup.stripped_strings)           # Removes extra lines and spaces
        filtered_text = Filter_text(text,stop_words)      
        unidict,bidict = unibifreq(filtered_text)
        unidicts.append(unidict)
        bidicts.append(bidict)
        final_txt.append(text)
    
    return unidicts,bidicts,final_txt   # Returns lists of filtered text, most frequent unigrams and bigrams from all top pages

def Filter_text(text,stop_words) :    # Removes stop words , punctuations and converts to lower case 
    tokens = word_tokenize(text)
    filtered_text = [w for w in tokens if w not in stop_words]
    filtered_text  = " ".join([str(item) for item in filtered_text ])
    filtered_text = re.sub(r'[^\w\s]', '',filtered_text )
    filtered_text = filtered_text.lower()

    return filtered_text
 
def unibifreq(filtered_text):        # Finds unigrams and bigrams and the top 20 common frequencies
    unigrams = word_tokenize(filtered_text)
    bigrams = ngrams(unigrams,2)
    unifreq=Counter(unigrams).most_common(20)
    bifreq = Counter(bigrams).most_common(20)
    unidict = [[c , v] for v,c in unifreq]
    bidict =  [[c , v] for v,c in bifreq]
    
    return unidict,bidict

def Get_Size(final_urls):   # Returns sizes of all top pages
    sizes = []
    for u in final_urls:
        res = requests.get(u)
        ch_size = getsizeof(res.text)    # text size
        img_sizes = Get_imgsizes(u)      # image size
        fin_img_size = 0
        for i in img_sizes:
            fin_img_size = fin_img_size + i
        total_size = fin_img_size + ch_size    # total size
        sizes.append(total_size)
    return sizes

def Get_imgsizes(url):              # Extracts images from a given url
    urls = []
    soup = Soup(url)
    for img in tqdm(soup.find_all("img"), "Extracting images"):
        imgurl = img.attrs.get("src")
        if not imgurl: continue
        imgurl = urljoin(url, imgurl)    # creates complete image url
        try:
            pos = imgurl.index("?")    
            imgurl = imgurl[:pos]
        except:
            pass
        urls.append(imgurl)        # list of all images in a page
    img_sizes = []
    for url in urls:
        try:
            response = requests.get(url, stream=True)
            file_size = int(response.headers.get("Content-Length", 0))
            img_sizes.append(file_size)          # list of all image sizes
        except:
            continue
    return img_sizes

url = input("Enter a valid URL : ")
stop_words = set(stopwords.words('english'))
If_Valid(url)
hp = Find_Homepg(url)
soup = Soup(url)

print('Home Page of the url is : ' + hp + "\n")
c,int_urls, ext_urls , final_urls =  Find_URLS(soup,hp)
print("Total no. of urls on home page / No. of Top pages : " + str(c))
print("Total no. of internal links : " + str(len(int_urls)))
print("Total no. of external links : " + str(len(ext_urls)))

print("\n\nInternal Links : \n")
for i in int_urls:
    print(i)

print("\n\nExternal Links : \n")
for i in ext_urls:
    print(i)

final_titles = Title_Extract(final_urls)

print("\n\nTitles of all Top Pages : \n")
for t in final_titles:
    try:
        print(t)
    except:
        print("No Title")

mc = Metaxtract(final_urls)
print("\n\n Meta Tags : \n")
for i in range(len(mc)):
    try:
        print(mc[i][0]+ " : " + mc[i][1] + '\n')
    except:
        continue


unidicts,bidicts,final_txt=Textract(final_urls,stop_words)

c=0
print("\n\nMost Frequent Unigrams in Top Pages : \n")
for u in unidicts:
    print('Page '+ str(c) + " : \n")
    for i in range(len(u)):
        try:
            print(str(u[i][1]) + ' : ' + str(u[i][0]) + '\n')
        except:
            print("undefined")
            
    print("\n\n")
    c = c+1

c=0
print("\n\nMost Frequent Bigrams in Top Pages : \n")
for u in bidicts:
    print('Page '+ str(c) + " : \n")
    for i in range(len(u)):
        try:
            print(str(u[i][1]) + ' : ' + str(u[i][0]) + '\n')
        except:
            print("undefined")
    print("\n\n")
    c = c+1

# Writing the output in text files

meta_dict = {}
f = open("D:\\W-Output\\FinalOutputSVCE.txt", "x")
f.write("No. of top level pages : " + str(c) + '\n\n')
f.write("TITLES OF TOP LEVEL PAGES :" + '\n\n')
for i in range(len(final_titles)):
    f = open("D:\\W-Output\\FinalOutputSVCE.txt", "a")
    try:
        f.write(str(final_titles[i])+'\n')
    except:
        f.write(str(final_titles[i].encode("utf-8"))+'\n')
f.write('\n' + 'Internal Links : ' + '\n\n')
for i in range(len(int_urls)):
    f.write(str(int_urls[i]) + '\n')
f.write(' \n '+'External Links : ' + '\n\n')
for i in range(len(ext_urls)):
    f.write(str(ext_urls[i]) + '\n')
f.write('\n'+ 'Meta Tags : ' + '\n\n')
for i in range(len(mc)):
    try:
        f.write(mc[i][0]+ " : " + mc[i][1] + '\n')
        meta_dict[mc[i][0]] = mc[i][1]
    except:
        continue

c = 0
f = open("D:\\W-Output\\FreqUnigramsSVCE.txt", "x")
f.write("Most Frequent Unigrams in Top Pages")
for u in unidicts:
    f.write('Page '+ str(c) + " : ")
    for i in range(len(u)):
        try:
            f.write(str(u[i][1]) + ' : ' + str(u[i][0]) + '\n')
        except:
            #print("undefined")
            continue
    f.write("\n\n")
    c = c+1

c = 0
f = open("D:\\W-Output\\FreqBigramsSVCE.txt", "x")
f.write("Most Frequent Bigrams in Top Pages")
for u in bidicts:
    f.write('Page '+ str(c) + " : ")
    for i in range(len(u)):
        try:
            f.write(str(u[i][1]) + ' : ' + str(u[i][0]) + '\n')
        except:
            continue
    f.write("\n\n")
    c = c+1

# Calculating page size
sizes = Get_Size(final_urls)
print("Maximum Size : " + str(max(sizes)))
print("Minimum Size : " + str(min(sizes)))
sizes = np.array(sizes)
avg = sum(sizes)/len(sizes)
print("Average Size : " + str(avg))     
