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

### 2. 圖片自動化發佈設定步驟（OneDrive 暫存 + GitHub Actions 自動下載）

> **原理說明**：GitHub Repository Dispatch 的 `client_payload` 限制僅約 **10 KB**，無法直接傳送圖片的 Base64 資料。因此我們採用以下策略：
> 1. Power Automate 將郵件的圖片附件上傳至 **OneDrive** 暫存（Standard 動作，免費）
> 2. 在 Payload 中只傳送**檔案路徑字串**（幾十 bytes，遠低於限制）
> 3. GitHub Actions 透過 **Microsoft Graph API**（已認證的 OAuth）從 OneDrive 下載實際圖片
>
> **⚠️ 注意**：不要嘗試直接在 Payload 中塞 `contentBytes`（會超過 10KB 限制），也不要使用 OneDrive 分享連結（伺服器端下載會收到 HTML 登入頁面）。

---

#### 事前準備：Azure AD 應用程式註冊（一次性設定，約 5 分鐘）

為了讓 GitHub Actions 能夠安全地從 OneDrive 下載圖片，需要註冊一個 Azure AD 應用程式：

1. 前往 [Azure Portal - 應用程式註冊](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade)
2. 點選 **「新增註冊」**：
   - **名稱**：`NewsRoom-GitHub-Actions`
   - **支援的帳戶類型**：選擇「僅此組織目錄中的帳戶」
   - 點選「註冊」
3. 註冊完成後，記下頁面上的：
   - **應用程式 (用戶端) 識別碼** → 稍後填入 `AZURE_CLIENT_ID`
   - **目錄 (租用戶) 識別碼** → 稍後填入 `AZURE_TENANT_ID`
4. 左側選單 → **憑證與密碼** → **新增用戶端密碼** → 記下密碼值 → 稍後填入 `AZURE_CLIENT_SECRET`
5. 左側選單 → **API 權限** → **新增權限** → **Microsoft Graph** → **應用程式權限** → 搜尋 `Files.Read.All` → 勾選並新增 → 最後點選 **「代表 [組織名稱] 授與管理員同意」**
6. 前往 [Azure AD 使用者列表](https://portal.azure.com/#blade/Microsoft_AAD_IAM/UsersManagementMenuBlade/AllUsers)，找到擁有 OneDrive 的使用者，記下其 **物件識別碼 (Object ID)** 或 **使用者主體名稱 (UPN)** → 稍後填入 `ONEDRIVE_USER_ID`

接著在 GitHub 儲存庫設定 Secrets：
- 前往 GitHub Repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**
- 依序新增：`AZURE_TENANT_ID`、`AZURE_CLIENT_ID`、`AZURE_CLIENT_SECRET`、`ONEDRIVE_USER_ID`

---

#### 1. 調整步驟 1 觸發器
- 點開 `當新電子郵件抵達時 (V3)` 動作。
- 點選最下方的 **「顯示進階選項」**（或進階參數）。
- 將 **「加入附件」** (Include Attachments) 設定為 **「是」** (Yes)。
- 確保 **「僅限包含附件」** (Only with Attachments) 為 **「否」**。

#### 2. 初始化兩個關鍵變數
在觸發器下方，點選 **「+ 新增步驟」**，搜尋 `變數`，並加入兩個 **「初始化變數」** 動作：
- **變數一：PostBaseName** (字串變數)：用來作為圖片在 OneDrive 與 GitHub 中的資料夾名稱。
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

> **⚠️ 重要**：這個條件過濾非常關鍵！它確保只有圖片附件（如 `.jpg`、`.png`）會被處理，`.doc`、`.pdf` 等非圖片檔案會被跳過，避免 Payload 爆量。

#### 4. 在「如果是」 (If yes) 綠色區塊中新增兩個動作
點開條件下方 **「如果是」** 的綠色區塊，在內部依序新增以下動作：

- **動作 A：OneDrive - 建立檔案**：
  - 搜尋 **`OneDrive`**，選擇 **「建立檔案」** (Create file) 動作。
  - **資料夾路徑**：輸入 `/NewsRoom/attachments/@{variables('PostBaseName')}`
  - **檔案名稱**：點選動態內容中的 **「附件名稱」** (即 `@{item()?['name']}`)
  - **檔案內容**：點選動態內容中的 **「附件內容」** (即 `@{item()?['contentBytes']}`)

- **動作 B：變數 - 附加至陣列變數**：
  - 搜尋 **`變數`**，選擇 **「附加至陣列變數」**。
  - **名稱**：選擇 **`ImageAttachments`**。
  - **值**：複製貼上以下 JSON：
    ```json
    {
      "filename": "@{item()?['name']}",
      "contentId": "@{item()?['contentId']}",
      "onedrive_path": "/NewsRoom/attachments/@{variables('PostBaseName')}/@{item()?['name']}"
    }
    ```

> **💡 說明**：`onedrive_path` 只是一段路徑文字字串（幾十 bytes），不包含圖片資料本身。GitHub Actions 會透過 Microsoft Graph API 使用此路徑來下載實際圖片。

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

> **💡 Payload 大小說明**：每個附件僅佔用約 100-200 bytes 的路徑字串，即使有 10 張圖片也僅約 2 KB，完全在 `client_payload` 的 10 KB 限制範圍內。實際圖片資料由 GitHub Actions 在伺服器端透過已認證的 Graph API 直接從 OneDrive 下載，不受 Payload 限制。

