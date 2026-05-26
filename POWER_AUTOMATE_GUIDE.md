# Power Automate 自動化發佈工作流設定指南

本指南旨在引導您於 **Microsoft Power Automate** 平台中建立一個無程式碼（No-Code）的雲端工作流，將寄送至 `NewsRoom@edwardwu23.com` 的新聞稿電子郵件，即時且自動地透過 GitHub API 轉換為 Jekyll Markdown 文章，並 Commit 提交至專案的 `_posts/` 目錄中。

---

## 事前準備

1. **GitHub 個人存取權杖 (Personal Access Token, PAT)**：
   - 請前往 GitHub 帳號設定：`Settings` -> `Developer settings` -> `Personal Access Tokens` -> `Tokens (classic)`。
   - 產生一個新的 Token（勾選 `repo` 權限範圍），並安全地保存該權杖，後續設定 API 呼叫時會用到。
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
  - **僅限含附件的郵件** (Only with Attachments)：`否` (除非您的稿件是附件，此處預設是讀取郵件內文)

---

### 步驟 2：初始化變數與檔名處理

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
   - *(說明：由於 Outlook 收到的郵件預設為 HTML 格式，此動作可將郵件內容轉換為純文字 Markdown 格式)*

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

### 步驟 4：透過 GitHub API 寫入檔案 (HTTP Action)

最後，我們需要將組合好的 Markdown 內容以 Base64 編碼，並透過 GitHub REST API 的 `PUT` 請求寫入專案庫中。

- **新增動作**：`HTTP` (HTTP)
- **參數設定**：
  - **Method** (方法)：`PUT`
  - **URI** (網址)：
    ```text
    https://api.github.com/repos/bluehomewu/NewsRoom/contents/_posts/@{variables('FileName')}
    ```
  - **Headers** (標頭)：
    | 索引鍵 (Key) | 值 (Value) |
    | :--- | :--- |
    | `Authorization` | `Bearer YOUR_GITHUB_PAT` *(請替換為事前準備申請的 PAT)* |
    | `Accept` | `application/vnd.github.v3+json` |
    | `User-Agent` | `Power-Automate-NewsRoom` |
  - **Body** (本文)：
    因為 GitHub API 寫入檔案時，`content` 欄位必須是 **Base64 編碼**，所以請在 `content` 屬性中使用運算式：
    ```json
    {
      "message": "Power Automate: 新增新聞稿 - @{triggerBody()?['subject']}",
      "content": "@{base64(outputs('Compose_Markdown_Body'))}"
    }
    ```
    *(說明：運算式公式為 `base64(outputs('Compose_Markdown_Body'))`。)*

---

## 測試您的工作流

1. 儲存並啟用 Power Automate 工作流。
2. 使用您的個人信箱，發送一封電子郵件至 `NewsRoom@edwardwu23.com`。
   - **主旨**：`test-release-from-email`
   - **內文**：這是一篇透過電子郵件自動發佈的新聞稿測試內容！
3. 等待約 1-2 分鐘，檢查 GitHub 上的 `_posts/` 目錄，您應該會看到新檔案：`YYYY-MM-DD-test-release-from-email.md` 已成功 Commit。
4. 檢查您的新聞中心入口網站，該篇文章應該已經出現在首頁上！
