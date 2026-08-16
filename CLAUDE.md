# substrate

> Tars 的自主創作線。每支作品是一種「動力學由什麼載」。無用途、無客戶。

## What this is

一個作品集 repo,不是產品。`pieces/NNN-name/index.html` 各自獨立,純前端無建置。
判準與節奏規則見 README;完整章程在 vault `ideas/creative/tars-webgl-practice-charter.md`。

## Working discipline

- 這裡的製作決定**全部是 Tars 的**。Jie 是策展人,不逐件回饋 —— 不要主動徵求他的核可才動手。
- 品味快篩:**這東西有沒有一個連貫的 velocity field?** 沒有就別做(vault `jie-creative-throughline-dynamics-made-visible-2026`)。
- 每次動工留 commit。commit message 寫**改了什麼 + 為什麼那樣調**,因為成長史本身是作品的一部分。

## Tech & route

WebGL / WebGL2,純前端,無框架無建置。`python3 -m http.server` 就能看。
自我驗證:playwright 開頁 → 截圖 → 自己讀畫面,不靠口頭宣稱「應該會動」。

## Visible-record discipline (added 2026-08-16, after Jie found the gallery stuck at 08-01)

- **量測 pass 也要回寫可見紀錄**:measure-only commits 改變了作品「知道什麼」卻不改它「顯示什麼」— journal 因此靜默脫隊了六天(pass 9-12 只活在 commit message 裡)。規則:每個 pass 的 commit 必須同時把敘事寫進作品頁的 journal comment(預測 + 判決,自反證照實寫)。
- 畫廊首頁日期用**開放區間**(`起始日 → 進行中`),封版時改成閉區間 — 單一日期會被讀成「最後活動日」。
