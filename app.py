from flask import *
from pymongo import MongoClient
import aip
from flask_cors import CORS
import bcrypt
import hashlib
import base64
import numpy as np
import os
from dotenv import load_dotenv
from stock import MY_STOCK
from google.oauth2 import id_token
from google.auth.transport import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

load_dotenv()
MONGO_CLIENT = os.getenv("MONGO_CLIENT")
client = MongoClient(MONGO_CLIENT)
db = client.mywebsite #選db
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")


app = Flask(
    __name__,
    #static file的folder和url
    static_folder="static", #對應的資料夾名稱
    static_url_path="/" #如果修改static為abc，則url就是abc
)
CORS(app)
app.secret_key="any string but secret"
app.config['JSON_SORT_KEYS'] = False

@app.route("/") #註冊帳號頁面
def index():
    return render_template("signup.html")

@app.route("/login") #登入帳號頁面
def login():
    return render_template("login.html")

@app.route("/config/google-client-id", methods=["GET"])
def for_get_google_client_id():
    return jsonify({"google_client_id": GOOGLE_CLIENT_ID})


@app.route("/google_login", methods=['POST'])
def for_google_login():
    token = request.form.get('token')
    id_info = id_token.verify_oauth2_token(
        token, requests.Request(), GOOGLE_CLIENT_ID, clock_skew_in_seconds=5)
    email = id_info.get('email')
    name = id_info.get('name')

    if id_info:
        result = db.users.find_one({"email":email})
        if result == None:
            db.users.insert_one({
                "name": name,
                "email": email,
                "password": None,
                "phone": None})
        session["name"] = name
        session["email"] = email
        return redirect("/my_cv")
    else:
        return redirect("/login", error_message="google帳號登入失敗")


@app.route("/my_cv") #cv頁面
def my_cv():
    if "name" in session:
        return render_template("my_cv.html")
    else:
        return redirect("/login")

@app.route("/my_aip",methods = ["GET","POST"]) 
def my_aip():
    if "name" in session:
        return render_template("my_aip.html")
    else:
        return redirect("/login")

@app.route("/image",methods =['POST']) #處理輸入照片
def for_load_img():
    file = request.files['file']
    if file:
        npimg = np.frombuffer(file.read(), np.uint8)
        gray_img = aip.img_to_gray(npimg) #照片
        result = db.users_createphoto.find_one({"name" : session["name"]})
        if result is None: 
            db.users_createphoto.insert_one({
                "name" : session["name"],
                "gray_img" : gray_img})
        else:
            db.users_createphoto.update_one(
                {"name" : session["name"]},     # 查找條件
                {"$set": {"gray_img": gray_img }})  # 更新操作
        return jsonify({"gray_img": gray_img}), 200
    else:
        return jsonify(success=False), 400

@app.route("/aip_image",methods=['POST'])
def for_load_aip_img():
    updatetype = request.form.get('updatetype') #選處理方式
    img = db.users_createphoto.find_one({"name" : session["name"]})
    
    if img is not None:
        gray_img = img.get("gray_img")
        update_functions = {
            "histogram": aip.img_to_histogram,
            "gaussion_noise": aip.img_to_gaussion_noise,
            "haar_wavelet": aip.img_to_haar_wavelet,
            "histogram_equalization": aip.img_to_histogram_equalization}
        update_img = update_functions[updatetype](gray_img)# 確保 updatetype 一定存在於 update_functions 中
        db.users_createphoto.update_one(
            {"name": session["name"]},           # 查找條件
            {"$set": { updatetype : update_img}})  # 使用 $set 新增資料到 photo 欄位
        return jsonify({updatetype : update_img}), 200
    return jsonify(success = False), 400


@app.route("/for_signup",methods=["POST"]) #處理註冊
def signup():
    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]
    phone = request.form["phone"]
    #加密密碼
    salt = hashlib.sha256(email.encode('utf-8')).digest()
    salt = base64.b64encode(salt).decode('utf-8')

    # 將Base64字串中的+/替換為bcrypt允許的字符，並截斷至22字符長度
    salt = salt.replace('+', '.').replace('/', '.')[:22]
    salt = f"$2b$12${salt}"
    password = bcrypt.hashpw(password.encode('utf-8'), salt.encode('utf-8'))  # 雜湊密碼
    result = db.users.find_one({
        "email":email})
    if result != None:
        return redirect("/error?message=信箱被註冊過了～")
    else:
        db.users.insert_one({
            "name": name,
            "email":email,
            "password":password,
            "phone":phone
        })
        return redirect("/login")

@app.route("/for_signin",methods=["POST"]) #處理登入
def signin():
    email = request.form['username']  # 獲取用戶輸入的帳號
    password = request.form['password']  # 獲取用戶輸入的密碼
    
    #加密密碼
    salt = hashlib.sha256(email.encode('utf-8')).digest()
    salt = base64.b64encode(salt).decode('utf-8')

    # 將Base64字串中的+/替換為bcrypt允許的字符，並截斷至22字符長度
    salt = salt.replace('+', '.').replace('/', '.')[:22]
    salt = f"$2b$12${salt}"
    password = bcrypt.hashpw(password.encode('utf-8'), salt.encode('utf-8'))  # 雜湊密碼
    collection = db.users #使用user database
    result = collection.find_one({
        "$and":[
            {"email":email},
            {"password":password}]
    })
    #看是否有找到會員資料
    if result != None:
        session["name"] = result["name"]
        session["email"] = result["email"]
        return redirect("/my_cv")
    return render_template('login.html', error_message="帳號密碼錯誤")

@app.route("/error") #錯誤訊息回傳
def error():
    message = request.args.get("msg" , "發生錯誤")
    return render_template("error.html",message = message)

@app.route("/for_signout")
def signout():
    if session["name"]:
        del session["name"]
    return redirect("/login")

@app.route("/signup")
def for_signup():
    return render_template("signup.html")

@app.route("/forgot_password")
def forgot_password():
    return render_template("forgot_password.html")

@app.route("/for_forgot_password",methods=["POST"])
def get_password():
    email = request.form["email"]
    phone = request.form["phone"]
    collection = db.users #使用user database
    result = collection.find_one({
        "$and":[
            {"email":email},
            {"phone":phone}]
    })
    if result != None:
        return render_template('forgot_password.html', password_message="password is : "+ result["password"])
    else:
        return render_template('forgot_password.html', password_message="不存在帳號或電話")

@app.route("/my_stock")
def my_stock():
    if "name" in session:
        return render_template("my_stock.html")
    else:
        return redirect("/login")

@app.route("/stock/buy", methods=["POST"])
def for_buy_my_stock():
    data = request.json
    user_name = session["name"]
    stock_name = data.get("stock_name")
    stock_shares = data.get("stock_shares")
    stock_price = data.get("stock_price")
    my_stock = MY_STOCK()
    if my_stock.get_stock_price(stock_name) == 0: #當輸入的股票未找到
        return jsonify({"success": False,"return_message":"請確認股票名稱輸入是否正確！"}), 400
    user_stock_record = db.users_stock.find_one({"user_name": user_name})
    if user_stock_record:
        stock_record = next((stock for stock in user_stock_record['stocks'] if stock['stock_name'] == stock_name), None)
        
        if stock_record:  #有購買紀錄，更新
            current_total_shares = stock_record['share_number']
            current_average_price = stock_record['average_buy_price']
            updated_average_price = ((current_total_shares * current_average_price) + (stock_shares * stock_price)) / (current_total_shares + stock_shares)
            
            db.users_stock.update_one( #更新該股票的資訊
                {"user_name": user_name, "stocks.stock_name": stock_name},
                {"$set": {
                    "stocks.$.share_number": current_total_shares + stock_shares,
                    "stocks.$.average_buy_price": updated_average_price}})

        else:  #有買過股票但沒買過該股票
            db.users_stock.update_one(
                {"user_name": user_name},
                {"$push": {
                    "stocks": {
                        "stock_name": stock_name,
                        "share_number": stock_shares,
                        "average_buy_price": stock_price}}})

    else:  #使用者從沒買過
        db.users_stock.insert_one({
            "user_name": user_name,
            "profit_status": 0,  #初始化總損益
            "stocks": [{
                "stock_name": stock_name,
                "share_number": stock_shares,
                "average_buy_price": stock_price}]})

    return jsonify({"success": True}), 200

@app.route("/stock/sell",methods=["POST"])
def for_sell_my_stock():
    data = request.json
    user_name = session["name"]
    stock_name = data.get("stock_name")
    stock_shares = data.get("stock_shares")
    stock_price = data.get("stock_price")
    user_stock_record = db.users_stock.find_one({"user_name": user_name})
    
    if not user_stock_record:
        return jsonify({"success": False ,"return_message":"無購買該股票紀錄！"}), 400
        
    user_stock_record = next((stock for stock in user_stock_record['stocks'] if stock['stock_name'] == stock_name), None)
    if not user_stock_record:
        return jsonify({"success": False ,"return_message":"無購買該股票紀錄！"}), 400
    elif user_stock_record["share_number"] < stock_shares:
        return jsonify({"success": False ,"return_message":"購買股數小於輸入股數！"}), 400
    else:
        average_buy_price = db.users_stock.find_one({"user_name": user_name, "stocks.stock_name": stock_name})["stocks"][0]["average_buy_price"]
        profit_status = stock_shares * stock_price - stock_shares * average_buy_price
        db.users_stock.update_one(
            {"user_name": user_name},
            {"$inc": {
                "profit_status": profit_status,
                "stocks.$[elem].share_number": -stock_shares}},
            array_filters=[{"elem.stock_name": stock_name}]) #過濾stocks陣列中的指定元素

        db.users_stock.update_one(
            {"user_name": user_name},
            {"$pull": {
                "stocks": {"stock_name": stock_name, "share_number": 0}}})
        return jsonify({"success": True}), 200

@app.route("/piechart_data")
def for_get_chart_data(): #圓餅圖
    user_name = session["name"]
    user_stock_record = db.users_stock.find_one({"user_name": user_name})
    stock_labels, stock_values = [], []
    for i in user_stock_record['stocks']:
        stock_labels.append(i["stock_name"])
        stock_values.append(i["share_number"] * i["average_buy_price"])

    data = {"labels": stock_labels, "values": stock_values}
    return jsonify(data)

@app.route("/headlines_data", methods=["POST"])
def for_get_headlines_data():
    data = request.json
    stock_name = data.get("stock_name")
    my_stock = MY_STOCK()
    if my_stock.get_stock_price(stock_name) == False:
        return jsonify({"success": False ,"return_message":"請確認股票名稱輸入正確！"})
    stock_headlines_dic = my_stock.get_stock_headlines(stock_name)
    return jsonify(stock_headlines_dic)

@app.route("/stock/information")
def for_get_stock_information_form():
    my_stock = MY_STOCK()
    stock_information = my_stock.get_stocks_information(session["name"])
    return jsonify(stock_information)

@app.route("/stock/price/notification",methods=["POST"])
def for_stock_price_change_notification():
    data = request.json
    stock_name = data.get("stock_name")
    set_stock_price = float(data.get("set_stock_price"))
    info_type = data.get("info_type")
    
    my_stock = MY_STOCK()
    stock_price = my_stock.get_stock_price(stock_name)
    if stock_price == False:
        return jsonify({"success": False})
    else:  # 加入排程
        db.server_stock.update_one(
            {"name": "stock_notification_scheduler"},
            {
                "$push": {
                    "notifications": {
                        "stock_name": stock_name,
                        "email": session["email"],
                        "stock_price": set_stock_price,
                        "info_type": info_type}}},
            upsert=True ) # 如果找不到，會自動插入新文檔
        return jsonify({"success": True})

def start_scheduler():
    my_stock = MY_STOCK()
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=my_stock.check_stock_price_threshold,  # 不加括號，確保傳入函式參考
        trigger=IntervalTrigger(seconds=1),
        id="check_stock_price_job",
        name="檢查股價",
        replace_existing=True
    )
    scheduler.start()
    return scheduler  # 返回 scheduler 物件，方便管理

if __name__ == "__main__":
    scheduler = start_scheduler() #要先啟動排程，不然會被app.run() block
    app.run(port=3000) 

