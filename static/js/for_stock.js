document.addEventListener("DOMContentLoaded", () => {
    console.log("for_stock.js loaded");

    window.submitStockData = function() {
        const stockName = document.getElementById("stock_name").value;
        const stockShares = document.getElementById("stock_shares").value;
        const stockPrice = document.getElementById("stock_price").value;
        const buy_or_sell = document.getElementById("transaction_type").value;
        const submitButton = document.querySelector("button[onclick='submitStockData()']");

        if(!stockName || !stockShares || !stockPrice) {
            alert("請完整填寫所有欄位");
            return;}
        if(stockShares <=0 || stockPrice <=0){
            alert("股數或價格必須大於零");
            return;}
        submitButton.disabled = true;
        console.log("start to post!");
        // 根據 buy_or_sell 決定要執行的 fetch 路由
        const fetchURL = buy_or_sell === "buy" ? "/for_buy_my_stock" : "/for_sell_my_stock";
        const successMessage = buy_or_sell === "buy" ? "股票資料已成功儲存！" : "賣出股票資料已成功儲存！";

        fetch(fetchURL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                stock_name: stockName,
                stock_shares: parseFloat(stockShares),
                stock_price: parseFloat(stockPrice)
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success ) {
                alert(successMessage);
            } else {
                alert(data.return_message);
            }
        })
        .catch(error => console.error("Error:", error))
        .finally(() => {
            // Re-enable the submit button after response
            submitButton.disabled = false;
        });
    };

    window.select_chart_type = function(){
        const selected_function = document.getElementById("chart_type").value;
        if(selected_function === "stock_allocation_ratio"){
            show_piechart();
        }
        else if(selected_function === "stock_profit_and_loss"){
            show_horizontal_bar_chart();
        }
        else{
            show_stock_movement ();
        }
    }
    let visualization_chart = null;
    window.show_piechart = function() {//圓餅圖
        fetch("/for_get_piechart_data")
            .then(response => response.json())
            .then(data => {
                
                const canvas = document.getElementById("myPieChart");
                canvas.width = 400;  //圓餅圖的寬度
                canvas.height = 400; //圓餅圖的高度

                if (visualization_chart) { //如果已有圖表，先銷毀它
                    visualization_chart.destroy();}
                const ctx = canvas.getContext("2d");
                visualization_chart = new Chart(ctx, {//創建新的圖表實例
                    type: "pie",
                    data: {
                        labels: data.labels, // 類別標籤
                        datasets: [{
                            data: data.values, // 各類別的數據值
                            backgroundColor: ["#FF6384", "#36A2EB", "#FFCE56","#4BC0C0","#9966FF","#FF9F40","#66FF66","#FF66B2","#A6A6A6","#8A2BE2"], // 顏色
                        }]},
                    options: {
                        responsive: false, //不隨視窗大小調整
                        plugins: {
                            tooltip: {
                                enabled: true  //顯示 tooltip
                            }}}});})
            .catch(error => console.error("Error loading chart data:", error));
    };

    window.show_horizontal_bar_chart = function() { // 水平條形圖
        fetch("/for_get_stock_information_form") // 替換為你的後端 API
            .then(response => response.json())
            .then(data => {
                const canvas = document.getElementById("myPieChart");
                canvas.width = 550; // 水平條形圖的寬度
                canvas.height = 300; // 水平條形圖的高度

                if (visualization_chart) { // 如果已有圖表，先銷毀它
                    visualization_chart.destroy();
                }

                const ctx = canvas.getContext("2d");

                // 提取數據中的 labels 和 values
                const labels = Object.keys(data); // 股票名稱
                const values = Object.values(data).map(item => item[0]); // 損益值

                const minValue = -Math.max(...values); // 最小損益值
                const maxValue = Math.max(...values); // 最大損益值

                visualization_chart = new Chart(ctx, { // 創建新的圖表實例
                    type: "bar",
                    data: {
                        labels: labels, // 顯示股票名稱
                        datasets: [{
                            label:labels, // 資料集標籤
                            data: values, // 損益值
                            backgroundColor: values.map(value => 
                                value >= 0 
                                    ? "rgba(244, 67, 54, 0.2)" // 內部顏色較淺
                                    : "rgba(76, 175, 80, 0.2)" // 內部顏色較淺
                            ),
                            borderColor: values.map(value => 
                                value >= 0 
                                    ? "rgba(244, 67, 54, 1)" // 外圍顏色較深
                                    : "rgba(76, 175, 80, 1)" // 外圍顏色較深
                            ),
                            borderWidth: 2, // 設置邊框寬度
                        }]},
                    options: {
                        indexAxis: "y", // 設置為水平條形圖
                        scales: {
                            x: {
                                min: minValue, // 設置 X 軸最小值
                                max: maxValue, // 設置 X 軸最大值
                                beginAtZero: true, // 確保 0 在中間
                                ticks: {
                                    callback: function(value) {
                                        return value; // 顯示損益值
                                    }},
                                grid: {
                                    color:"#e0e0e0",
                                    lineWidth: (context) => context.tick.value === 0 ? 2 : 1, // 中間線粗度
                                }},
                            y: {
                                ticks: {
                                    callback: function(value, index) {
                                        return labels[index]; // 顯示左側的股票名稱
                                    }}}},
                        plugins: {
                            legend:{
                                display: false
                            },
                            tooltip: {
                                enabled: true, // 顯示提示
                                callbacks: {
                                    label: function(tooltipItem) {
                                        // 只顯示數字，並格式化為小數點後兩位
                                        return tooltipItem.raw.toFixed(2); 
                                    }
                                }
                            }},
                        responsive: false // 固定尺寸
                    }});})
            .catch(error => console.error("Error loading chart data:", error));
    };

    window.show_stock_movement = function(){

    };

///////////////////////////////////////////////////////////////////////////////////////

    window.select_other_function_type = function(){ //跑右邊功能，決定哪一個功能
        const selected_function = document.getElementById("other_function_type").value;
        if(selected_function === "show_headlines") {
            show_headlines();
        }else if(selected_function === "show_informatin_form") {
            show_informatin_form();
        }
    }

    window.show_headlines = function() {// 向Flask後端請求資料並文字超連結
        const user_input = prompt("請輸入選擇的股票代號:");
         //查找 onclick 屬性設定為 submitStockData() 的 <button> 元素，並返回找到的第一個匹配的元素。
        const submitButton = document.querySelector("button[onclick='submitStockData()']"); 
        //submitButton.disabled = true; // 鎖住按鍵
        if(!user_input){
            alert("請完整填寫所有欄位");
            return;}
        console.log("start to post!");

        fetch("/for_get_headlines_data", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                stock_name: user_input,
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log(data);
            if (data.success === false) {
                alert(data.return_message)}
            else{
                const headlinesDiv = document.getElementById("headlines_or_informationform");
                headlinesDiv.innerHTML = ""; // 清空過去的內容
    
                // 遍歷 JSON 資料並生成超連結
                Object.keys(data).forEach((title, index) => {
                    const link = document.createElement("a");
                    link.href = data[title]; // 將對應的超連結設置為 href
                    link.textContent = title; // 設置顯示的文字
                    link.target = "_blank"; // 新窗口打開
                    //link.style.textDecoration = "none"; // 去掉底線
                    link.style.color = "black";
                    headlinesDiv.appendChild(link);
        
                    // 添加換行
                    headlinesDiv.appendChild(document.createElement("br"));
                    headlinesDiv.appendChild(document.createElement("br"));
                });
            }
        })
        .catch(error => console.error("Error:", error))
        .finally(() => {
            submitButton.disabled = false;// 打開按鍵
        });}
    
    window.show_informatin_form = function() {
        alert("需要時間搜尋資料，請稍等～");
        fetch('/for_get_stock_information_form')
            .then(response => response.json())
            .then(data => {
                const tableContainer = document.getElementById('headlines_or_informationform');
                tableContainer.innerHTML = "";
                const table = document.createElement('table');// 創建表格元素
                table.style.borderCollapse = 'collapse';
                table.style.width = '50%';
                
                const headers = ['股票名稱', '損益', '購買股數', '平均購買價格','最新股價'];// 表頭資料
                const headerRow = document.createElement('tr');
                headers.forEach(headerText => {
                    const header = document.createElement('th');
                    header.textContent = headerText;
                    header.style.border = '1px solid #000';
                    header.style.padding = '5px';
                    header.style.textAlign = 'center';
                    header.style.color = "black"
                    headerRow.appendChild(header);
                });
                table.appendChild(headerRow);

                Object.keys(data).forEach(stockName => { //遍歷數據並生成表格行
                    const row = document.createElement('tr');
                    const nameCell = document.createElement('td');// 股票名稱
                    nameCell.textContent = stockName;
                    nameCell.style.border = '1px solid #000';
                    nameCell.style.padding = '1px';
                    nameCell.style.textAlign = 'center';
                    row.appendChild(nameCell);
                    data[stockName].forEach((value, index) => {
                        const cell = document.createElement('td');
                        cell.textContent = value;
                        cell.style.border = '1px solid #000';
                        cell.style.padding = '5px';
                        cell.style.textAlign = 'center';
                        if (index === 0) {// 設定損益顏色，在第一個
                            cell.style.color = value >= 0 ? "red" : "green";
                        }
                        row.appendChild(cell);
                    });
                    table.appendChild(row);
                });
                tableContainer.appendChild(table);// 將生成的表格添加到容器中
            })
            .catch(error => console.error('Error:', error));
    };
});
