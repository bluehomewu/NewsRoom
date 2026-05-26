# Power Automate 自動化發佈工作流設定指南 (GitHub Actions 混合版)

本指南旨在引導您於 **Microsoft Power Automate** 平台中建立一個無程式碼（No-Code）的雲端工作流。

當有新的電子郵件寄送至 `NewsRoom@edwardwu23.com` 時，此工作流會將郵件標題與內文封裝，並向 GitHub 專案發送一個 **Repository Dispatch** 事件信號。接著，專案的 GitHub Actions 接收到信號後會自動將內容解碼，寫入 `_posts/` 並進行發佈。

---

## 事前準備

1. **GitHub 個人存取權杖 (Personal Access Token, PAT)**：
   - 請前往 GitHub 帳號設定：`Settings` -> `Developer settings` -> `Personal Access Tokens` -> `Tokens (classic)`。
   - 產生一個新的 Token（勾選 `repo` 權限範圍），並安全地保存該權權杖。
2. **Microsoft 365 / Office 365 帳戶**：
   - 用於收發 `NewsRoom@edwardwu23.com` 信箱的電子郵件。

---

## 工作流建置步驟

請登入 [Power Automate 平台](https://make.powerautomate.com/)，建立一個**自動化雲端流程 (Automated cloud flow)**。

### 步驟 1：建立觸發器 (Trigger)

- **動作名稱**：`Office 365 Outlook - 當新電子郵件抵達時 (V3)` (When a new email arrives (V3))
- **參數設定**：
  - **資料夾** (Folder)：`Inbox`
  - **收件者** (To)：`NewsRoom@edwardwu23.com`
  - **敏感度** (Importance)：`任何`
  - **僅限含附件的郵件** (Only with Attachments)：`否`

---

### 步驟 2：初始化變數與格式化

為了將郵件標題轉換成符合 Jekyll 規範的 Markdown 檔案名稱（格式：`YYYY-MM-DD-filename.md`），請新增以下動作：

1. **新增動作**：`變數 - 初始化變數` (Initialize variable)
   - **名稱**：`FileName`
   - **類型**：`字串` (String)
   - **值**（使用 Power Automate 運算式 Expression）：
     ```json
     concat(utcNow('yyyy-MM-dd'), '-', triggerBody()?['subject'], '.md')
     ```
     *(說明：此公式會自動取得今日的 UTC 日期，並加上郵件主旨作為檔名)*

2. **新增動作**：`內容轉換 - HTML 轉文字` (HTML to text)
   - **內容** (Content)：選擇動態內容中的 `郵件本文` (Body)。
   - *(說明：將 HTML 格式的郵件本文轉換為純文字 Markdown 格式)*

---

### 步驟 3：組合 Jekyll Front Matter 內容

Jekyll 文章需要特定的 Front Matter（YAML 標頭）才能正常被解析。我們使用 Compose 動作來組裝它：

- **新增動作**：`資料操作 - 組合` (Data Operation - Compose)
- **動作重新命名**：`Compose_Markdown_Body`
- **輸入** (Inputs)：
  ```yaml
  ---
  layout: post
  title: "@{triggerBody()?['subject']}"
  date: @{utcNow('yyyy-MM-dd HH:mm:ss')} +0800
  categories: press
  ---
  @{outputs('Html_to_text')?['body']}
  ```
  *(說明：此步驟會自動產生 Jekyll 文章格式，並將步驟 2 轉換後的純文字郵件內容填入下方。)*

---

### 步驟 4：發送 Repository Dispatch 請求 (HTTP Action)

最後，我們需要將檔名與組合好的 Markdown 內容（進行 Base64 編碼），透過 GitHub API 發送給 GitHub 專案。

- **新增動作**：`HTTP` (HTTP)
- **參數設定**：
  - **Method** (方法)：`POST`
  - **URI** (網址)：
    ```text
    https://api.github.com/repos/bluehomewu/NewsRoom/dispatches
    ```
  - **Headers** (標頭)：
    | 索引鍵 (Key) | 值 (Value) |
    | :--- | :--- |
    | `Authorization` | `Bearer YOUR_GITHUB_PAT` *(請替換為事前準備申請的 PAT)* |
    | `Accept` | `application/vnd.github.v3+json` |
    | `User-Agent` | `Power-Automate-NewsRoom` |
  - **Body** (本文)：
    ```json
    {
      "event_type": "new_press_release",
      "client_payload": {
        "filename": "@{variables('FileName')}",
        "content": "@{base64(outputs('Compose_Markdown_Body'))}"
      }
    }
    ```
    *(說明：`content` 欄位運算式公式為 `base64(outputs('Compose_Markdown_Body'))`。)*

---

## 測試您的工作流

1. 儲存並啟用 Power Automate 工作流。
2. 發送電子郵件至 `NewsRoom@edwardwu23.com`。
   - **主旨**：`test-release-from-email`
   - **內文**：這是一篇透過電子郵件與 GitHub Actions 自動發佈的新聞稿測試內容！
3. 等待約 2-3 分鐘，檢查 GitHub Actions 中的 `Publish Press Release Email` 工作流，確認執行成功。
4. 此工作流會自動將該文章 Commit 提交至 `master` 分支，並觸發 `Build and Deploy` 重新部署網站，隨後即可在新聞首頁看到該文章！

---

## 進階：保留粗體樣式與圖片

本專案的 Python 清洗腳本已內建強大的 **HTML-to-Markdown 自動轉換器**。如果您希望在發佈的新聞稿中保留郵件原本的 **粗體（Bold）樣式** 以及 **嵌入圖片（Images）**，請依照以下步驟調整 Power Automate 的工作流設定：

### 1. 修改 Power Automate 資料傳送格式
1. 在 **步驟 2** 中，您可以選擇 **跳過（刪除）** `HTML 轉文字` 動作。
2. 在 **步驟 3** (Compose_Markdown_Body) 中，直接將 `Html_to_text` 的輸出替換為郵件的原始 HTML 本文：
   ```yaml
   ---
   layout: post
   title: "@{triggerBody()?['subject']}"
   date: @{utcNow('yyyy-MM-dd HH:mm:ss')} +0800
   categories: press
   ---
   @{triggerBody()?['body']}
   ```
   *(這會使 Power Automate 直接將郵件的原始 HTML 傳送給 GitHub Actions，由 GitHub 端的 Python 解析器自動轉換成 Markdown 粗體 `**文字**` 與圖片語法)*

### 2. 圖片自動化上傳設定步驟（將 GitHub 儲存庫當成圖床）
若要完全自動化處理郵件中的圖片附件，我們需要將圖片以 Base64 格式打包成陣列，隨同 HTTP 請求傳送給 GitHub Actions：

1. **調整步驟 1 觸發器**：
   - 點開 `Office 365 Outlook - 當新電子郵件抵達時 (V3)` 動作。
   - 點選右上角「顯示進階選項」。
   - 將 **「包含附件」** (Include Attachments) 設定為 **「是」** (Yes)。

2. **新增動作：初始化附件陣列變數**：
   - 新增動作 `變數 - 初始化變數` (Initialize variable)。
   - **名稱**：`ImageAttachments`
   - **類型**：`陣列` (Array)
   - **值**：保持空白。

3. **新增動作：遍歷附件並過濾圖片**：
   - 在 `Compose_Markdown_Body` 步驟之前，新增動作 `控制 - Apply to each` (套用到每個)。
   - **選取前一個步驟的輸出** (Select an output from previous steps)：選擇動態內容中的 **「附件」** (Attachments) 陣列。
   - **在迴圈中新增一個「條件」** (Condition) 動作：
     - 設定條件為：`附件內容類型` (Attachment Content-Type) **包含** `image/`。
     - *(說明：這會過濾出所有的圖片附件，排除非圖片檔案)*
   - **如果為是** (If yes) 的區塊中，新增動作 `變數 - 附加至陣列變數` (Append to array variable)：
     - **名稱**：選擇 `ImageAttachments`。
     - **值** (Value)：輸入以下 JSON：
       ```json
       {
         "filename": "@{items('Apply_to_each')?['name']}",
         "contentBytes": "@{items('Apply_to_each')?['contentBytes']}",
         "contentType": "@{items('Apply_to_each')?['contentType']}",
         "contentId": "@{items('Apply_to_each')?['contentId']}"
       }
       ```
       *(注意：若介面為新版設計，可以直接在動態內容中選擇對應的「附件名稱」、「附件內容」、「附件內容類型」與「附件內容識別碼」)*

4. **更新步驟 4：HTTP 請求 Body**：
   - 修改最後 HTTP 動作的 **Body** 內容，將打包好的圖片陣列傳入 `attachments` 欄位：
     ```json
     {
       "event_type": "new_press_release",
       "client_payload": {
         "filename": "@{variables('FileName')}",
         "content": "@{base64(outputs('Compose_Markdown_Body'))}",
         "attachments": @{variables('ImageAttachments')}
       }
     }
     ```
     *(注意：這裡的 `@{variables('ImageAttachments')}` 無需加雙引號，Power Automate 會自動將陣列變數序列化為 JSON 陣列帶入)*

這樣一來，GitHub 端的 Python 清理腳本就會自動在 `assets/img/posts/` 底下建立該文章的專屬目錄，將圖片解碼儲存，並自動將內文中的 `cid:` 連結改寫為相對於 Jekyll 網站的圖片路徑！您完全不需要手動上傳圖片到任何外部圖床。
