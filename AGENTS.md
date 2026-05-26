
# AGENTS.md - NewsRoom 開發者與 AI 代理指南 (Power Automate + Actions 混合版)

## 專案概述
「NewsRoom」是一個專門用於發佈合作夥伴新聞稿的入口網站，託管於 GitHub Pages 作為專案網站。它擁有獨立的自訂網域，部署網址為 `https://edwardwu23.com/NewsRoom/`。

本專案的自動化發佈流程由 **Microsoft Power Automate** 與 **GitHub Actions** 共同完成：
1. 當專屬 Exchange 郵箱 `NewsRoom@edwardwu23.com` 收到信件時，Power Automate 會即時透過信號觸發 GitHub 存放庫分派事件（Repository Dispatch）。
2. 本專案的 GitHub Actions 接收到信號後，自動將新聞稿轉換並還原解碼，將文章直接寫入本專案的 `_posts/` 目錄中，啟動自動部署。

---

## 技術堆疊與架構
- **靜態網站產生器 (SSG)**：Jekyll（GitHub Pages 預設）
- **網址配置**：
  - `url`："https://edwardwu23.com"
  - `baseurl`："/NewsRoom"（注意：此項設定非常關鍵，否則網站資源路徑會失效）
- **自動化管道 (Automation Pipeline)**： 
  - **發送端**：Microsoft Power Automate 監聽 `NewsRoom@edwardwu23.com`。
  - **接收端**：GitHub Actions 工作流程（`.github/workflows/publish_email.yml`）。
  - **觸發事件類型**：`new_press_release`
  - **傳輸荷載 (Payload)**：
    - `filename`：`YYYY-MM-DD-filename.md`
    - `content`：Base64 編碼的 Markdown 內文（包含 Jekyll Front Matter 檔頭）。

---

## 目錄結構
```text
NewsRoom/
├── .github/
│   └── workflows/
│       └── publish_email.yml  # 接收 Power Automate 信號並自動發文的 Action 流程
├── _posts/                    # 自動生成的新聞稿文章
├── assets/                    # 靜態資源（CSS、JS、圖片）
├── _config.yml                # Jekyll 網站設定檔
├── AGENTS.md                  # 本檔案（AI 代理引導指南）
├── README.md                  # 給人類閱讀的說明文件
└── POWER_AUTOMATE_GUIDE.md    # 微軟 Power Automate 端的工作流配置教學指南
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

### 階段 2：建立自動發文 Actions 流程 (`.github/workflows/publish_email.yml`)
請在專案中建立一個接收 Power Automate 觸發信號的工作流程。
* 觸發條件為 `repository_dispatch` 且 `types` 為 `[new_press_release]`。
* 此工作流程必須具備 `contents: write` 權限。
* 步驟包含：
  1. 使用官方 `actions/checkout@v4` 簽出專案。
  2. 建立 `_posts/` 資料夾（如果尚未存在）。
  3. 將 `github.event.client_payload.content` 以 Base64 解碼（使用 `base64 --decode`），並儲存為 `_posts/` 底下的 `github.event.client_payload.filename`。
  4. 自動設定 Git 的系統使用者（如 `github-actions[bot]`）並將此檔案 Commit 提交至主要的發佈分支（預設為 `main`），從而觸發 GitHub Pages 的重新部署。

### 階段 3：生成 Power Automate 教學文檔 (`POWER_AUTOMATE_GUIDE.md`)
為了方便人類擁有者在 Power Automate 端進行無程式碼設定，請在專案根目錄生成詳細的 `POWER_AUTOMATE_GUIDE.md` 教學文件，說明如何將收到的信件打包並透過 Repository Dispatch 發送至 GitHub。

---

## 程式碼品質與規則限制
- **純靜態儲存庫**：除了 GitHub 內建的工作流程之外，本專案目錄內不應包含任何用於郵件拉取的 Python 或 Node.js 後端程式碼，保持 Jekyll 專案的純粹性與安全性。
- **嚴格遵循 Baseurl 規則**：網站中的所有內部連結與靜態資源引用，都必須使用 `{{ site.baseurl }}`，以避免在專案子網頁中出現 404 錯誤。
