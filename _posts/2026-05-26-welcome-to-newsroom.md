---
layout: post
title: "歡迎來到 NewsRoom 合作夥伴新聞中心！"
date: 2026-05-26 12:00:00 +0800
categories: press
published: false
---

這是我們的新聞中心首頁。**NewsRoom** 是一個專門用於發佈合作夥伴新聞稿的入口網站，託管於 GitHub Pages 作為專案網站。

本專案的自動化發佈流程由 **Microsoft Power Automate** 驅動。當專屬 Exchange 郵箱 `NewsRoom@edwardwu23.com` 收到信件時，Power Automate 會即時透過 GitHub API 將新聞稿轉換為 Jekyll Markdown 文章，直接 Commit 提交至本專案的 `_posts/` 目錄中。

## 系統特色

1. **無伺服器架構 (Serverless)**：利用 GitHub Pages 進行靜態網站託管，無須額外的伺服器維護成本。
2. **無程式碼後端 (No-Code)**：藉由 Power Automate 雲端工作流監聽電子郵件並串接 GitHub API，無須編寫或維護複雜的拉取腳本。
3. **極致的視覺美學**：採用現代感十足的深色背景、漸層主題色與玻璃帷幕 (Glassmorphism) 卡片設計，並整合前端即時搜尋功能。

> 本篇新聞稿為系統初始化時自動產生的範例文件。後續所有新聞稿均可透過發送電子郵件至 `NewsRoom@edwardwu23.com` 來自動發佈。
