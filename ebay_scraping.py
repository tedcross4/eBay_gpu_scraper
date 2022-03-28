#functions for getting data from ebay
import datetime
import os
import pandas as pd
import numpy as np
from scipy.interpolate import make_interp_spline
import statistics
def get_price(soup):
        price = soup.findAll('span', attrs={'class' : 's-item__price'})
        price=[i.text for i in price]
        price.pop(0)
        price=[i.replace("$","") for i in price]
        price=[i.replace(",","") for i in price]
        return price

def get_product(soup):
        product = soup.findAll('h3', attrs={'class': 's-item__title'})
        product.pop(0)
        product=[i.text for i in product]
        return product

def get_date(soup):
    date = soup.findAll('span', attrs={'class' : 'POSITIVE'})
    date=[i.text for i in date]
    date=[i for i in date if 'Sold' in i]
    date=[i.replace("Sold  ","") for i in date]
    date=[i.replace(",","") for i in date]
    date=[datetime.datetime.strptime(i, '%b %d %Y') for i in date]
    return date

def get_link(soup):
    link=soup.findAll('a',{'class':'s-item__link'})
    link=[i.attrs.get("href") for i in link]
    link.pop(0)
    return link

def add_to_csv(gpu, data):
    if os.path.exists('data/'+gpu+".csv"):
        data_previous=pd.read_csv('data/'+gpu+".csv")
        data=pd.concat([data,data_previous])
        data=data.drop_duplicates(subset=["Link"],ignore_index=True)
        data.to_csv('data/'+gpu+".csv", index=False)
    else:
        data.to_csv('data/'+gpu+".csv", index=False)
    return data

def smoothing(moving_average_dates,moving_average_prices):
        moving_average_dates=[i.timestamp() for i in moving_average_dates]
        x_moving_average_smoothed = np.linspace(min(moving_average_dates), max(moving_average_dates), 300)
        gfg = make_interp_spline(moving_average_dates, moving_average_prices, k=3)
        y_moving_average_smoothed = gfg(x_moving_average_smoothed)
        x_moving_average_smoothed=[datetime.datetime.fromtimestamp(i) for i in x_moving_average_smoothed]
        return x_moving_average_smoothed, y_moving_average_smoothed

def remove_outliers(filtered_data,movingAveDays):
        dates=[]
        for i in filtered_data['Dates']:
            dates.append(datetime.datetime.strptime(str(i)[0:10],'%Y-%m-%d'))
        filtered_data['Dates']=dates
        start_date = min(filtered_data.Dates)+datetime.timedelta(days=movingAveDays)
        filtered_data = filtered_data.reset_index()  # make sure indexes pair with number of rows
        
        # for each entry we are going to check that the price does not lie outside the 2 week average+-std
        for i in range(len(filtered_data)):
            #collect dataframe with all sales in the last two weeks
            upper_date=filtered_data.iloc[i].Dates
            lower_date=upper_date-datetime.timedelta(days=movingAveDays)
            target_data=filtered_data.loc[(filtered_data['Dates'] >= lower_date) & (filtered_data['Dates'] <= upper_date)]
            #find mean and stdv of the data from the last x number of weeks (i.e target data)
            mean=statistics.mean([float(i) for i in list(target_data.Prices)])
            stdev=statistics.pstdev([float(i) for i in list(target_data.Prices)])
            if float(filtered_data.iloc[i].Prices)<(mean-stdev) or float(filtered_data.iloc[i].Prices)>(mean+stdev):
                filtered_data.loc[i, 'Filtered'] = True
            #if price lies outside limit set filtered to true
        filtered_data = filtered_data[filtered_data.Filtered == False]
        return filtered_data

def get_moving_average(filtered_data,movingAveDays):
        dates=list(filtered_data.Dates)
        start_date = min(filtered_data.Dates)+datetime.timedelta(days=movingAveDays)
        filtered_data = filtered_data.reset_index()  # make sure indexes pair with number of rows
        moving_average_prices=[]
        moving_average_dates=pd.date_range(start=start_date,end=max(filtered_data.Dates))
        for i in moving_average_dates:
            upper_limit=i
            lower_limit=i-datetime.timedelta(days=movingAveDays)
            pricesInCalc=filtered_data.loc[filtered_data['Dates'] < upper_limit]
            pricesInCalc=pricesInCalc.loc[pricesInCalc['Dates'] > lower_limit]
            pricesInCalc=list(pricesInCalc["Prices"])
            mean=statistics.mean(pricesInCalc)
            moving_average_prices.append(mean)
        return moving_average_dates, moving_average_prices

def save_filtered_data(gpu,gpuSub,filtered_data):
    if not os.path.exists('filtered/'+gpu) and not os.path.exists('filtered/'):
        os.mkdir('filtered/')
        os.mkdir('filtered/'+gpu)
        pd.DataFrame(list()).to_csv('filtered/'+gpu+'/'+gpuSub+'.csv'); #create an empty csv
    elif not os.path.exists('filtered/'+gpu):
        os.mkdir('filtered/'+gpu)
        pd.DataFrame(list()).to_csv('filtered/'+gpu+'/'+gpuSub+'.csv'); #create an empty csv
    elif not os.path.exists('filtered/'+gpu+'/'+gpuSub+'.csv'):
        pd.DataFrame(list()).to_csv('filtered/'+gpu+'/'+gpuSub+'.csv'); #create an empty csv

    filtered_data.to_csv('filtered/'+gpu+'/'+gpuSub+'.csv')