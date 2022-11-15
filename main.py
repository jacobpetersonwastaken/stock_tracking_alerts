import os
from requests import *
from twilio.rest import Client
from dotenv import load_dotenv
from datetime import *
from time import *

load_dotenv('.env')


def check_market_open():
    """Checks api to see if the market is open"""
    fmp_api_key = os.getenv('financialmodelingprep_API_KEY')
    endpoint = 'https://financialmodelingprep.com/api/v3/is-the-market-open'
    parameters = {
        'apikey': fmp_api_key
    }
    r = get(url=endpoint, params=parameters).json()['isTheStockMarketOpen']
    return r



def get_stock_data(ticker):
    """Gets all the stocks data"""
    ALPHA_STOCK_API_KEY = os.getenv('ALPHA_STOCK_API_KEY')
    endpoint = 'https://www.alphavantage.co/query'
    parameters = {
        'function': 'TIME_SERIES_DAILY',
        'symbol': ticker,
        'outputsize': 'compact',
        'datatype': 'json',
        'apikey': ALPHA_STOCK_API_KEY
    }
    r = get(url=endpoint, params=parameters).json()['Time Series (Daily)']
    dates_traded = [i for i in r]

    today_open = float(r[dates_traded[0]]['1. open'])
    today_close = float(r[dates_traded[0]]['4. close'])
    yesterday_close = float(r[dates_traded[1]]['4. close'])

    percent_change_close_to_open = ((today_open - yesterday_close) / yesterday_close) * 100
    percent_change_close_to_close = ((today_close - yesterday_close) / yesterday_close) * 100
    return [percent_change_close_to_open, percent_change_close_to_close, today_open]


def get_news(company: str, date, quantity):
    """gets all the company"""
    NEWS_API_KEY = os.getenv('NEWS_API_KEY')
    endpoint = 'https://newsapi.org/v2/everything'
    parameters = {'q': company,
                  'from': date,
                  'sortBy': 'popularity',
                  'apiKey': NEWS_API_KEY}
    r = get(url=endpoint, params=parameters).json()['articles'][:quantity]
    titles = [i['title'] for i in r]
    urls = [i['url'] for i in r]
    return [titles, urls]


def time_till(day: int, hour: int, minute: int):
    """Returns time till the specified time."""
    utx_timestamp = int(datetime.now().timestamp())
    t1 = (datetime.now() + timedelta(days=day)).replace(hour=hour, minute=minute, microsecond=0, second=0)
    seconds_till_7 = (t1 - datetime.now()).seconds
    return seconds_till_7


def send_text(to, message):
    """Handles all of the text message twillio api"""
    twilio_sid = os.getenv('TWILIO_SID')
    twilio_token = os.getenv('TWILIO_TOKEN')
    sender_phone_num = os.getenv('SENDER_PHONE_NUM')
    client = Client(twilio_sid, twilio_token)
    message_info = client.messages.create(body=message, from_=sender_phone_num, to=f'+1{to}')
    return message_info.sid


def organize_info(company, ticker):
    """Formats all the data into something readable in a text."""
    # news
    news = get_news(company=company, date=datetime.today(), quantity=2)
    news_titles = news[0]
    news_urls = news[1]
    # stock data
    stock_data = get_stock_data(ticker=ticker)
    close_open = round(stock_data[0], 2)
    close_close = round(stock_data[1], 2)
    today_open = stock_data[2]

    open_message = f'\n-----------\n' \
                   f'{company}: {ticker}\n' \
                   f'Open price: ${today_open}\n' \
                   f'% change close to open: {close_open}\n' \
                   'News:\n' \
                   f'{news_titles[0]}\n' \
                   f'{news_urls[0]}\n' \
                   f'-------------\n' \
                   f'{news_titles[1]}\n' \
                   f'{news_urls[0]}'

    close_message = f'\n----------\n' \
                    f'{company}: {ticker}\n' \
                    f'Open price: ${today_open}\n' \
                    f'% change close to close: {close_close}\n' \
                    'News:\n' \
                    f'{news_titles[0]}\n' \
                    f'{news_urls[0]}\n' \
                    f'--------------\n' \
                    f'{news_titles[1]}\n' \
                    f'{news_urls[0]}'
    return [open_message, close_message]


def start():
    """Main script"""
    company = input('What company would you like to search for?')
    ticker = input(f"What is {company}'s stock ticker?")
    PHONE_NUMBER = os.getenv('PHONE_NUMBER')

    while True:
        sleep(time_till(day=1, hour=7, minute=31))
        if check_market_open():
            text_message = organize_info(company=company, ticker=ticker)[0]
            send_text(to=PHONE_NUMBER, message=text_message)
            sleep(time_till(day=0, hour=6, minute=31))
            if not check_market_open():
                text_message = organize_info(company=company, ticker=ticker)[1]
                send_text(to=PHONE_NUMBER, message=text_message)


start()

