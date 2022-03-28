# eBay GPU Scraper


![3080 Example](https://github.com/tedcross4/eBay_gpu_scraper/blob/cb9efa75f9eb1e813c1bdcf498be3cf51bcd8dac/figs/3080.png?raw=true)

This code is free to use and modify. If you have anything to ask me or would simply like to share what you have used this code for, please put your comments in the discussion section.

eBay has a captcha. If this appears you should simply fill it out. There should be adequate time to fill it out.

## Installation instructions
* Install python3.8, pip, venv and google chrome
* Install packages in requirements.txt
* Run main.py

[This script was used to create the graphs for this TechRadar article](https://www.techradar.com/uk/deals/looking-for-a-gpu-dont-buy-yet-graphics-card-prices-are-falling-rapidly)

### Notes
* If you have a more recent version of chrome than me you may need to get a more recent version of the webdriver.
* I had issues installing scipy on my computer if you also have issues try this pip command `pip install --pre -i https://pypi.anaconda.org/scipy-wheels-nightly/simple scipy`
* Set the `numberOfPages=15` to set the number of pages of ebay data you want to take. I advise going for over 15 as to allow you to get a moving average graph to have a decent chance.
* Note that eBay will only allow you to collect 90 days worth of data at a time. The script will store the data and then update (i.e. if you ran the script and ran the script again 20 days later you would then have 110 days worth of data)