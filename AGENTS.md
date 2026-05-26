以下是為您整合好的 `AGENTS.md` 完整內容。您可以直接複製下方區塊中的所有文字，並在您的專案根目錄下儲存為 `AGENTS.md` 檔案：

```markdown
# AGENTS.md - NewsRoom 開發者與 AI 代理指南 (Power Automate 版本)

## 專案概述
「NewsRoom」是一個專門用於發佈合作夥伴新聞稿的入口網站，託管於 GitHub Pages 作為專案網站。它擁有獨立的自訂網域，部署網址為 `https://edwardwu23.com/NewsRoom/`。

本專案的自動化發佈流程由 **Microsoft Power Automate** 驅動。當專屬 Exchange 郵箱 `NewsRoom@edwardwu23.com` 收到信件時，Power Automate 會即時透過 GitHub API 將新聞稿轉換為 Jekyll Markdown 文章，直接 Commit 提交至本專案的 `_posts/` 目錄中。

---

## 技術堆疊與架構
- **靜態網站產生器 (SSG)**：Jekyll（GitHub Pages 預設）
- **網址配置**：
  - `url`："https://edwardwu23.com"
  - `baseurl`："/NewsRoom"（注意：此項設定非常關鍵，否則網站資源路徑會失效）
- **自動化管道 (Automation Pipeline)**： 
  - 本地無程式碼運行，由 Microsoft Power Automate 監聽 `NewsRoom@edwardwu23.com`。
  - 透過 GitHub REST API (`PUT /repos/bluehomewu/NewsRoom/contents/_posts/{filename}.md`) 寫入檔案。
  - 檔名格式：`YYYY-MM-DD-filename.md`

---

## 目錄結構
```text
NewsRoom/
├── _posts/                    # 由 Power Automate 自動寫入的新聞稿
├── assets/                    # 靜態資源（CSS、JS、圖片）
├── _config.yml                # Jekyll 網站設定檔
├── AGENTS.md                  # 本檔案（AI 代理引導指南）
├── README.md                  # 給人類閱讀的說明文件
└── POWER_AUTOMATE_GUIDE.md    # 由 AI 生成，引導人類設定微軟工作流的教學指南
```

---

## 關鍵執行指令
使用以下指令來測試與維護本專案：
- **啟動本地 Jekyll 預覽**：`bundle exec jekyll serve`

---

## 給 Antigravity 的開發指引

### 階段 1：Jekyll 初始化與設定
1. 使用乾淨的 Jekyll 範本初始化此目錄。
2. 編輯 `_config.yml`，確保 `url` 設為 `"https://edwardwu23.com"` 且 `baseurl` 設為 `"/NewsRoom"`。

### 階段 2：生成 Power Automate 設定教學文檔 (`POWER_AUTOMATE_GUIDE.md`)
由於自動化流程移至微軟雲端，Antigravity 必須撰寫一份詳細的 `POWER_AUTOMATE_GUIDE.md` 部署指南，協助人類使用者在 Power Automate 平台中進行無程式碼設定。

此指南內容必須包含：
1. **觸發器設定**：選用 `Office 365 Outlook - 當新電子郵件抵達時 (V3)`，並設定篩選條件。
2. **變數初始化與格式化**：
   - 檔名生成公式：`concat(utcNow('yyyy-MM-dd'), '-', triggerBody()?['subject'], '.md')`
   - 內文 HTML 轉文字（使用內建 `HTML to text` 動作），或保留 HTML 格式寫入 Markdown。
3. **組合 Jekyll Front Matter** 的文字區塊（Compose Action）範本：
   ```yaml
   ---
   layout: post
   title: "郵件主旨"
   date: YYYY-MM-DD HH:MM:SS +0800
   categories: press
   ---
   [郵件內文]
   ```
4. **GitHub API HTTP 動作（HTTP Action）配置**：
   - **Method**: `PUT`
   - **URI**: `https://api.github.com/repos/bluehomewu/NewsRoom/contents/_posts/@{variables('FileName')}`
   - **Headers**:
     - `Authorization`: `Bearer YOUR_GITHUB_PAT`（需提醒使用者在 GitHub 申請 Personal Access Token）
     - `Accept`: `application/vnd.github.v3+json`
   - **Body**: 必須將 Markdown 內容轉換為 Base64。公式說明：`base64(outputs('Compose_Markdown_Body'))`
     ```json
     {
       "message": "Power Automate: 新增新聞稿 - @{triggerBody()?['subject']}",
       "content": "@{base64(outputs('Compose_Markdown_Body'))}"
     }
     ```

---

## 程式碼品質與規則限制
- **無庫存代碼**：專案庫中不應包含任何用於郵件拉取的 Python 或 Node.js 腳本，完全保持 Jekyll 的純粹性。
- **嚴格遵循 Baseurl 規則**：網站中的所有內部連結與靜態資源引用，都必須使用 `{{ site.baseurl }}`，以避免在專案子網頁中出現 404 錯誤。
