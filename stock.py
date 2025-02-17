import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from decimal import Decimal
import time
import os
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

load_dotenv()
MONGO_CLIENT = os.getenv("MONGO_CLIENT")
GOOGLE_EMAIL_ID = os.getenv("GOOGLE_EMAIL_ID")
GOOGLE_APP_CODE = os.getenv("GOOGLE_APP_CODE")


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
        print("-----------------------------------------")
        print(headlines_dic)
        print("-----------------------------------------")
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
            price = float(price_element.text.replace("$", "").replace(",", ""))
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

    def check_stock_price_threshold(self):
        stock_notification_scheduler = self.db.server_stock.find_one({"name": "stock_notification_scheduler"}).get("notifications", [])
        stock_names = {stock["stock_name"] for stock in stock_notification_scheduler}
        new_stock_price_dic = {name: self.get_stock_price(name) for name in stock_names}

        comparison_funcs = {
            "greater": lambda current, target: current > target,
            "equal": lambda current, target: current == target,
            "less": lambda current, target: current < target }

        for scheduler_item in stock_notification_scheduler:
            stock_name = scheduler_item["stock_name"]
            current_price = new_stock_price_dic[stock_name]
            target_price = scheduler_item["stock_price"]
            info_type = scheduler_item["info_type"]
            email = scheduler_item["email"]

            if comparison_funcs[info_type](current_price, target_price):
                self.send_gmail("股票價格波動通知信",email,stock_name,info_type,target_price)
                self.db.server_stock.update_one(
                    {"name": "stock_notification_scheduler"},
                    {"$pull": {"notifications": scheduler_item}})

    def send_gmail(self, subject, to_email, stock_name, info_type, target_price):
        info_type = "大於" if info_type == "greater" else "小於" if info_type == "less" else "等於"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h1 style="color:  #ff3342;">股票價格波動通知</h1>
            <p>您好，</p>
            <p>此封信件是通知您購買的股票 <strong>{stock_name}</strong> 已經 <strong>{info_type}</strong> 了目標價 <strong>{target_price}</strong>！</p>
            
            <p>如有任何問題，您可以隨時聯繫我們。</p>
            <p>
            <p>謝謝！<br>團隊敬上</p>
            
        </body>
        </html>
        """
       
        msg = MIMEMultipart("alternative")  #設定郵件內容
        msg["From"] = GOOGLE_EMAIL_ID
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(html_content, "html"))

        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(GOOGLE_EMAIL_ID, GOOGLE_APP_CODE)
                server.sendmail(msg["From"], to_email, msg.as_string())
                print("HTML郵件已成功寄出！")
        except Exception as e:
            print(f"發送郵件失敗: {e}")



