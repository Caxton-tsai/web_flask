import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from decimal import Decimal
import time
import os
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()
MONGO_CLIENT = os.getenv("MONGO_CLIENT")

class MY_STOCK:
    def __init__(self):
        self.client = MongoClient(MONGO_CLIENT)
        self.db = self.client.mywebsite
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8"}

    def get_top100_us_stock(self):
        url = "https://companiesmarketcap.com/usa/largest-companies-in-the-usa-by-market-cap/" 
        response = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(response.text, "html.parser")
        stock_web_elements = soup.select(".company-code")#選擇股票代碼CSS
        stock_collection = [element.text for element in stock_web_elements]
        return stock_collection

    def classify_stock_exchanges(self,stock_collection):
        NASDAQ_collection, NYSE_collection = [] ,[]
        for stock_symbol in stock_collection:
            url_NASDAQ = f"https://www.google.com/finance/quote/{stock_symbol}:NASDAQ"
            response = requests.get(url_NASDAQ, headers=self.headers)
            soup = BeautifulSoup(response.text, "html.parser")
            error_element = soup.select_one(".b4EnYd")
            if error_element:
                NYSE_collection.append(stock_symbol)
            else:  # 否則屬於 NASDAQ
                NASDAQ_collection.append(stock_symbol)

    def get_stock_headlines(self,stock_symbol):
        exchanges_collection = self.db.server_stock.find_one({"name": "exchanges_collection"})
        exchanges_inclusion = exchanges_collection["exchanges_inclusion"]
        url = ""
        for i in exchanges_inclusion:
            if stock_symbol in exchanges_collection[i]:
                url = f"https://www.google.com/finance/quote/{stock_symbol}:{i}"
                break

        response = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(response.text, "html.parser")
        headlines_dic = {}
        articles = soup.select('div.z4rs2b > a')  # 選擇所有相關的標題鏈接
        for idx, article in enumerate(articles, start=1):
            title = article.select_one('div.Tfehrf > div.Yfwt5')  # 標題文字
            url_href = article["href"]  # 提取 href 屬性
            if title and url_href:
                headlines_dic[f"{idx}. {title.text}"] = url_href
        return headlines_dic
        
    def get_stock_price(self,stock_symbol):
        exchanges_collection = self.db.server_stock.find_one({"name": "exchanges_collection"})
        exchanges_inclusion = exchanges_collection["exchanges_inclusion"]
        url = ""
        for i in exchanges_inclusion:
            if stock_symbol in exchanges_collection[i]:
                url = f"https://www.google.com/finance/quote/{stock_symbol}:{i}"
                break
        if url == "":
            return False
        else:
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, "html.parser")

            price_element = soup.select_one(".YMlKec.fxKbKc")
            price = price_element.text
            print(f"{stock_symbol} 股票價格: {price}")
            return price

    def fetch_stock_info(self, stock, exchanges_NASDAQ, headers):
        stock_name = stock["stock_name"].replace("-", ".")  # 處理特殊股票代碼格式
        url = (
            f"https://www.google.com/finance/quote/{stock_name}:NASDAQ"
            if stock_name in exchanges_NASDAQ
            else f"https://www.google.com/finance/quote/{stock_name}:NYSE"
        )

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # 檢查 HTTP 狀態碼是否為 200
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch data from {url}: {e}")
            return stock_name, ["Error", stock["share_number"], round(stock["average_buy_price"], 2), None]

        soup = BeautifulSoup(response.text, "html.parser")
        price_text = soup.select_one(".YMlKec.fxKbKc")
        if price_text is None:
            print(f"此stock無法適用 {stock_name} 網址 {url}")
            return stock_name, ["Error", stock["share_number"], round(stock["average_buy_price"], 2), None]

        try:
            price_element = Decimal(price_text.text.replace(",", "").replace("$", ""))
            average_buy_price = Decimal(stock["average_buy_price"])
            share_number = Decimal(stock["share_number"])
            profit_and_loss_results = round(float((price_element - average_buy_price) * share_number), 2)
            return stock_name, [profit_and_loss_results, stock["share_number"], round(stock["average_buy_price"], 2), price_element]
        except Exception as e:
            print(f"Error calculating profit/loss for {stock_name}: {e}")
            return stock_name, ["Error", stock["share_number"], round(stock["average_buy_price"], 2), None]


    def get_stocks_information(self, user_name):
        start_time = time.time()
        users_stock_result = self.db.users_stock.find_one({"user_name": user_name})
        exchanges = self.db.server_stock.find_one({"name": "exchanges_collection"})
        exchanges_NASDAQ = exchanges["NASDAQ"]

        stock_information = {}
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {executor.submit(self.fetch_stock_info, stock, exchanges_NASDAQ, self.headers): stock for stock in users_stock_result["stocks"]}

            for future in as_completed(futures):
                try:
                    stock_name, result = future.result()
                    if result:
                        stock_information[stock_name] = result
                except Exception as e:
                    print(f"Error processing stock: {e}")

        stock_information = dict(sorted(stock_information.items(), key=lambda item: (item[1][0] if isinstance(item[1][0], (int, float)) else float('-inf'))))
        end_time = time.time() - start_time
        print("花費時間", end_time)
        return stock_information



    def get_stock_movement(self, user_name):
        users_stock_result = self.db.users_stock.find_one({"user_name": user_name})
        exchanges = self.db.server_stock.find_one({"name": "exchanges_collection"})
        stocks = [stock["stock_name"] for stock in users_stock_result["stocks"]]
        print(stocks)

    def test(self):
        print("start")
        
        stocks = self.get_top100_us_stock()
        for i in stocks:
            self.db.users_stock.update_one(
                {"user_name": "only test"},
                {"$push":{
                    "stocks":{
                        "stock_name": i,
                        "share_number": 100,
                        "average_buy_price" :100
                    }
                }}
            )
        print("end")
 
