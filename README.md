# 個人網站

## 介紹

本網站結合個人履歷管理、圖像處理、股票管理與分析等多項功能，旨在提供一個多功能的個人平台。

## 主要功能

*   **個人履歷管理**: 使用者可以輕鬆建立、編輯和管理個人履歷。
*   **圖像處理**: 提供多種圖像處理功能，如灰階轉換、直方圖、高斯雜訊、哈爾小波轉換、直方圖等化。
*   **股票管理與分析**: 追蹤和分析股票數據，提供即時股價資訊、新聞標題、損益計算等功能。
*   **股價變動通知系統**: 設定股票價格提醒，當股價達到預設值時，系統將自動發出通知。

## 技術架構

*   **後端**: Python (Flask, OpenCV, BeautifulSoup, APScheduler, pymongo, bcrypt, Flask-CORS, python-dotenv, google-auth-httplib2, google-auth-oauthlib, concurrent.futures, smtplib)
*   **資料庫**: MongoDB
*   **前端**: HTML, CSS, JavaScript (具體使用的前端框架或函式庫未在程式碼中體現，請在此處補充)

## API 端點

*   `/`: 首頁 (註冊頁面)
*   `/login`: 登入頁面
*   `/for_get_google_client_id`: 獲取 Google Client ID
*   `/google_login`: Google 登入處理
*   `/my_cv`: 個人履歷頁面
*   `/my_aip`: 圖像處理頁面
*   `/for_load_img`: 處理上傳的圖片
*   `/for_load_aip_img`: 處理圖像處理請求
*   `/for_signup`: 處理註冊請求
*   `/for_signin`: 處理登入請求
*   `/error`: 錯誤訊息回傳
*   `/for_signout`: 登出
*   `/signup`: 註冊頁面
*   `/forgot_password`: 忘記密碼頁面
*   `/for_forgot_password`: 處理忘記密碼請求
*   `/my_stock`: 股票管理頁面
*   `/for_buy_my_stock`: 處理購買股票請求
*   `/for_sell_my_stock`: 處理賣出股票請求
*   `/for_get_piechart_data`: 獲取圓餅圖資料
*   `/for_get_headlines_data`: 獲取新聞標題資料
*   `/for_get_stock_information_form`: 獲取股票資訊
*   `/for_stock_price_change_notification`: 設定股價變動通知

## 環境變數設定

以下為應用程式所需的環境變數，請在 `.env` 檔案中設定：

*   `MONGO_CLIENT`: MongoDB 連線字串 
*   `GOOGLE_CLIENT_ID`: Google Client ID (請至 Google Cloud Console 取得)
*   `GOOGLE_EMAIL_ID`:  用於發送郵件的 Google 郵箱 ID
*   `GOOGLE_APP_CODE`: 用於發送郵件的 Google 應用程式密碼 (建議使用應用程式專用密碼，並注意安全性)

**請注意：**  請勿將這些敏感資訊直接寫在程式碼中，而是使用 `.env` 檔案和 `python-dotenv` 套件來管理。

## 安裝步驟

1.  複製專案
2.  建立 `.env` 檔案，並在其中設定環境變數。
3.  安裝相依套件：`pip install -r requirements.txt` (請參考下方 `requirements.txt` 檔案內容)
4.  執行應用程式：`python app.py`

