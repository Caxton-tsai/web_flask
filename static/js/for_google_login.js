
// 初始化 Google API 並渲染按鈕
window.onload = async function () {
    //async/await保證fetch完成之後才進行google.accounts.id.initialize動作。
    const response = await fetch("/for_get_google_client_id");
    const clientId = await response.text();  // 獲取 client_id

    google.accounts.id.initialize({
        client_id : clientId, 
        callback: handle_credential_response //處理登入回應放function名字不用括號
    });

    google.accounts.id.renderButton(
        document.getElementById("google_login_button"), // 按鈕容器
        {
            theme: "outline", // 按鈕主題
            size: "large",    // 按鈕大小
            type: "standard", // 按鈕類型
            shape: "rectangular", // 按鈕形狀
            text: "signin_with", // 顯示文字
            logo_alignment: "left", // Logo 對齊方式
        }
    );
};

// 接收 Google 回傳的憑證並透過表單提交到後端
function handle_credential_response(response) {
    // 設定隱藏欄位的值
    const tokenInput = document.getElementById("google-token");
    tokenInput.value = response.credential;
    document.getElementById("google_login_form").submit();
}
