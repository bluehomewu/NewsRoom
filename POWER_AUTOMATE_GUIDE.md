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

### 2. 圖片自動化發佈設定步驟（直接傳送附件 Base64 內容）

> **原理說明**：Power Automate 的郵件觸發器會自動將附件以 Base64 格式提供（`contentBytes`）。我們只需要將這些 Base64 資料打包進 GitHub Repository Dispatch 的 `client_payload` 中，由 GitHub Actions 端的 Python 腳本自動解碼並儲存為圖片檔案。
>
> **⚠️ 注意：不要使用 OneDrive 分享連結方式！** OneDrive 的 `webUrl` 分享連結在伺服器端無法直接下載（會收到 HTML 登入頁面而非圖片），因此本流程直接傳送附件內容。

#### 1. 調整步驟 1 觸發器
- 點開 `當新電子郵件抵達時 (V3)` 動作。
- 點選最下方的 **「顯示進階選項」**（或進階參數）。
- 將 **「加入附件」** (Include Attachments) 設定為 **「是」** (Yes)。
- 確保 **「僅限包含附件」** (Only with Attachments) 為 **「否」**。

#### 2. 初始化兩個關鍵變數
在觸發器下方，點選 **「+ 新增步驟」**，搜尋 `變數`，並加入兩個 **「初始化變數」** 動作：
- **變數一：PostBaseName** (字串變數)：用來作為圖片在 GitHub 中的資料夾名稱。
  - **名稱**：`PostBaseName`
  - **類型**：`字串`
  - **值**（點選右側「運算式 Expression」輸入，然後按確定）：
    ```text
    concat(utcNow('yyyy-MM-dd'), '-', replace(replace(triggerBody()?['subject'], ' ', '_'), ':', '_'))
    ```
- **變數二：ImageAttachments** (陣列變數)：用來收集圖片附件資訊。
  - **名稱**：`ImageAttachments`
  - **類型**：`陣列`
  - **值**：保持空白，什麼都不用填。

#### 3. 新增套用到每個與條件過濾
- 在 `Compose_Markdown_Body` 步驟之前，新增動作 `控制 - 套用到每個` (Apply to each)。
- **選取前一個步驟的輸出**：點選輸入框，從動態內容中搜尋並選取 **「附件」** 陣列。
- 在迴圈 **內部**，點選「新增動作」，搜尋 `控制` 並選擇 **「條件」** (Condition)：
  - **左邊第一個格子**：選取動態內容中的 **「附件內容類型」** (ContentType)。
  - **中間選單**：選擇 **「包含」** (contains)。
  - **右邊第三個格子**：手動輸入文字 **`image/`**。

#### 4. 在「如果是」 (If yes) 綠色區塊中新增動作
點開條件下方 **「如果是」** 的綠色區塊，在內部新增以下動作：

- **動作：變數 - 附加至陣列變數**：
  - 搜尋 **`變數`**，選擇 **「附加至陣列變數」**。
  - **名稱**：選擇 **`ImageAttachments`**。
  - **值**：複製貼上以下 JSON：
    ```json
    {
      "filename": "@{item()?['name']}",
      "contentId": "@{item()?['contentId']}",
      "contentBytes": "@{item()?['contentBytes']}"
    }
    ```

> **⚡ 與之前的差異**：不再需要 OneDrive「建立檔案」和「建立共用連結」動作！直接將 `contentBytes`（附件的 Base64 編碼內容）放入陣列中即可。如果您的流程中有 OneDrive 相關動作，可以安全地刪除它們。

#### 5. 更新最後的「建立存放庫分派事件」
1. 找到最下方的 **「建立存放庫分派事件」** 動作展開。
2. 將事件裝載 (client_payload) 修改為以下內容：
   ```json
   {
     "filename": "@{variables('FileName')}",
     "content": "@{base64(outputs('Compose_Markdown_Body'))}",
     "post_base_name": "@{variables('PostBaseName')}",
     "attachments": @{variables('ImageAttachments')}
   }
   ```
   *(在 `"attachments":` 的值，直接使用動態內容中的 **`ImageAttachments`** 陣列變數，不要加雙引號)*

---

> **💡 大小限制說明**：GitHub Repository Dispatch 的 Payload 上限為 **25 MB**。一般新聞稿附件的圖片（經過郵件壓縮後通常每張 100KB-2MB）完全在此限制範圍內。若單封郵件的圖片附件總量超過 25 MB，建議將部分大圖改為外部連結。

