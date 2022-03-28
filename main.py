#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 19 12:03:44 2022

@author: Ted Cross
"""
from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
import time
from numpy import random
import matplotlib.pyplot as plt
import os
import pickle
from datetime import timedelta
import numpy as np
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import ebay_scraping

productsPerPage=60
numberOfPages=15
driver = webdriver.Chrome(os.getcwd()+'/chromedriver')
movingAveDays=21
gpus=["1050","1060","1070","1080","2080","2070","2060","3090","3080","3070","3060"]
gpus=['1050'];  #This is just for debugging
line_colour=[[0.09,0.753,0.77],[0.96,0.13,0.59],[0.64,0.40,0.96]];  #These are the rgb values of the three colours for the lines in the plot
labels=True
smoothness=2; # A factor of how smooth. Must be a positive integer
dot_colour=[[0.08,0.62,0.63],[0.86,0.04,0.49],[0.35,0.05,0.78]]
plt.style.use('https://github.com/dhaitz/matplotlib-stylesheets/raw/master/pitayasmoothie-dark.mplstyle')
plt.figure(figsize = (7,4));    #set figure size

#filtering Parameters. This loads the pickle file that has all the filtering parameters
with open('gpuVariants.pickle', 'rb') as f:
    data_from_pickle=pickle.load(f)
gpu_variants = data_from_pickle[0]
filtering_params = data_from_pickle[1]
####################################################
##################Collect Data######################
####################################################

for gpu in gpus:
    products = []
    prices = []
    dates= []
    links = []
    for i in range(0,numberOfPages):
        print(i)
        driver.get("https://www.ebay.com/sch/i.html?_from=R40&_nkw="+gpu+"&_sacat=0&rt=nc&LH_Sold=1&LH_Complete=1&_pgn="+str(i))
        if i ==0 or i ==1:#This puts a large delay to fill out captcha or a quicker delay
            random_delay=10+(random.rand()*3)
            time.sleep(random_delay)
        else:
            random_delay=1+(random.rand()*2)
            time.sleep(random_delay)
        
        content = driver.page_source
        soup = BeautifulSoup(content, "lxml")
        
        #Collect Name
        product=ebay_scraping.get_product(soup)

        #Collect Price    
        price=ebay_scraping.get_price(soup)
        
        #Collect Date
        date=ebay_scraping.get_date(soup)
        
        #Collect Link
        link=ebay_scraping.get_link(soup)

        #we need to remove the item which has a price range
        indexs_to_be_removed=[]
        for i in range(len(price)):
            if ' to ' in price[i]:
                indexs_to_be_removed.append(i)
        for i in sorted(indexs_to_be_removed, reverse=True):
            price.pop(i); date.pop(i); link.pop(i); product.pop(i)
        
        #if theres an equal number of names, dates, prices and links from this page then add them to main list
        if len(date)==len(price) and len(date)==len(product) and len(date)==len(link):
            print('addding '+str(len(link))+' entries')
            prices=prices+price
            dates=dates+date
            products=products+product
            links=links+link
    
    #convert all prices to float
    prices=[float(i) for i in prices]
    #Form Dataframe
    unfiltered_data=pd.DataFrame(list(zip(products,dates, prices,links)),columns =['Name','Dates', 'Prices','Link'])
    unfiltered_data=unfiltered_data.drop_duplicates(subset=["Link"],ignore_index=True)
    
    #check if a csv file exists and if not create it
    unfiltered_data=ebay_scraping.add_to_csv(gpu,unfiltered_data)
    ####################################################
    ##################Filtering#########################
    ####################################################
    gpuSubs=gpu_variants[gpu]
    colour_counter=0
    y_min_vals_for_limits=[]
    y_max_vals_for_limits=[]
    for gpuSub in gpuSubs:
        words_to_exclude=filtering_params[gpuSub]['dontInclude']
        words_that_must_include=filtering_params[gpuSub]['include1of']
        
        unfiltered_data['Filtered'] = [True]*len(unfiltered_data);    #by default everything is filtered out
        #if contains something from include1of then dont filter
        for i in words_that_must_include:
            unfiltered_data.loc[unfiltered_data['Name'].str.contains('|'.join(i)), 'Filtered'] = False;
        i
        #if contains something from dontInclude then set it back to being filtered
        for i in words_to_exclude:
            unfiltered_data.loc[unfiltered_data['Name'].str.contains(i), 'Filtered'] = True;
        filtered_data = unfiltered_data[unfiltered_data.Filtered == False]
        
        #remove outliers
        filtered_data=ebay_scraping.remove_outliers(filtered_data,movingAveDays)

        #Create folder and file if it does not exist and save data
        ebay_scraping.save_filtered_data(gpu,gpuSub,filtered_data)

        ####################################################
        ###########Smoothing and plotting###################
        ####################################################
        #Find moving average
        moving_average_dates, moving_average_prices=ebay_scraping.get_moving_average(filtered_data, movingAveDays)

        #Plot Scatter
        lc=line_colour[colour_counter]
        dc=dot_colour[colour_counter]
        colour_counter+=1
        y_min_vals_for_limits.append(min(moving_average_prices))
        y_max_vals_for_limits.append(max(moving_average_prices))
        
        #smoothing
        x_moving_average_smoothed,y_moving_average_smoothed=ebay_scraping.smoothing(moving_average_dates,moving_average_prices)
        #Plot Trend
        plt.plot(x_moving_average_smoothed, y_moving_average_smoothed,label=gpuSub, color=lc, zorder=2)
        #Plot scatter
        plt.plot(list(filtered_data.Dates),list(filtered_data.Prices),"o",markersize=1, color=dc, zorder=1)
        
    ax = plt.gca()
    ax.xaxis.set_major_locator(ticker.MultipleLocator(14))
    plt.ylim([(min(y_min_vals_for_limits)-(0.1*(max(y_max_vals_for_limits)-min(y_min_vals_for_limits)))),(max(y_max_vals_for_limits)+(0.1*(max(y_max_vals_for_limits)-min(y_min_vals_for_limits))))])
    plt.ylabel("$")
    formatter = mdates.DateFormatter("%d-%b-%y")
    ax.xaxis.set_major_formatter(formatter)
    plt.tick_params(axis='x', rotation=45)
    plt.legend(loc='upper right')
    plt.grid()
    plt.text(0.085, 0.042,'Ted Cross', ha='center', va='center', transform=ax.transAxes,color=[0.8,0.8,0.8])
    if not os.path.exists('figs/'):
        os.mkdir('figs/')
    plt.savefig('figs/'+gpu+".png",dpi=1200,bbox_inches="tight")
    plt.close()
        
        