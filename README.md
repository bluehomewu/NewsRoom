# NewsRoom 新聞中心

NewsRoom 是一個專為發佈合作夥伴新聞稿設計的入口網站。網站託管於 GitHub Pages，並配置自訂網域部署於 `https://edwardwu23.com/NewsRoom/`。

本專案採用 **Jekyll Chirpy 主題** 作為視覺架構，並完全整合 **Microsoft Power Automate** 與 **GitHub Actions**，實現「發送電子郵件即可自動發佈新聞稿」的無程式碼 (No-Code) 發佈管道。

---

## 專案與自動化架構

1. **Jekyll Chirpy 主題**：提供精美的響應式版面、側邊欄導覽、全站即時搜尋、分類/標籤頁面與深淺色模式切換。
2. **自動化發佈管道**：當合作夥伴寄信到 `NewsRoom@edwardwu23.com` 時：
   - Power Automate 會捕捉此信件，將內文轉換為 Markdown，並向本倉庫發送 `Repository Dispatch` 事件。
   - GitHub Actions (`publish_email.yml`) 接收信號，解碼 Base64 內文並將文章寫入 `_posts/` 目錄。
   - 提交 Commit 後，自動觸發 `Build and Deploy` 部署網站。

---

## 目錄結構

```text
NewsRoom/
├── _posts/                    # 新聞稿文章目錄
├── _layouts/                  # Chirpy 佈局範本
├── _includes/                 # Chirpy 網頁組件（含客製動態 og:image 分享縮圖邏輯）
├── _tabs/                     # 側邊欄主要分頁（首頁、關於、分類、標籤、存檔）
├── assets/                    # 靜態資源（Favicon、樣式與 JS）
├── tools/                     # Chirpy 輔助指令碼
├── _config.yml                # Jekyll 設定檔（已設定 baseurl: /NewsRoom 與排除項）
├── Gemfile                    # 專案依賴套件檔
├── README.md                  # 本說明文件
└── POWER_AUTOMATE_GUIDE.md    # Power Automate 設定教學指南
```

---

## 本地開發與預覽

若要在本地環境中啟動並預覽網站，請遵循以下步驟：

### 1. 安裝套件依賴

請在專案根目錄下執行：

```bash
bundle install
```

### 2. 啟動 Jekyll 本地伺服器

執行以下指令啟動 Jekyll 本地開發伺服器：

```bash
bundle exec jekyll serve
```

伺服器啟動後，請在瀏覽器中開啟：
[http://localhost:4000/NewsRoom/](http://localhost:4000/NewsRoom/)

*(注意：由於設定了 `baseurl: "/NewsRoom"`，本地預覽路徑亦會包含 `/NewsRoom` 字樣)*

---

## 自動化工作流設定

關於如何設定 Power Automate 串接電子郵件與 GitHub API 的詳細說明，請參閱：
[POWER_AUTOMATE_GUIDE.md](file:///home/edwardwu/workspace/NewsRoom/POWER_AUTOMATE_GUIDE.md)
