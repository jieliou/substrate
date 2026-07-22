# handoff — substrate

**狀態快照,非 changelog。每次收工整份覆寫。**

## 現在在哪

**piece 001 完成第一版**(2026-07-22 上午,Jie 10:30 開綠燈後動工)。
`pieces/001-self-channelling-flow/index.html` — 單檔 WebGL2,無建置,`python3 -m http.server` 即看。

- **機制**:Tero physarum 網路模型。抖動三角網格(24×17,~1.1k 邊),節點壓力 Gauss-Seidel
  暖啟動求解(26 sweeps/frame),邊電導以 saturating 適應 `f(Q)=Q^γ/(1+Q^γ)` 演化。
  單源(左,ember 色)單匯(右,藍)。120fps。
- **形式 = 07-22 晨的設計判斷直接落地**:γ 滑桿當「軸」(0.4–2.0,mesh↔tree),
  preserveDrawingBuffer + 半透明黑 fade 讓拖動時的重組留下漸暗痕跡(滑桿+持久痕跡)。
- **視覺**:寬度=電導(河床被刻多寬),亮度=流量(現在跑多少水)。兩者不一致的邊
  (寬而轉冷)= 正在被推翻的決定,是這件作品真正的敘事單元。
- 代表幀在 `shots/`(mesh / critical / tree 三格)。

## 這一版學到的(craft 記錄)

1. **p95 正規化在 mostly-dead 分布下反轉**:樹 regime 95% 邊在地板,參考值塌成雜訊,
   全畫面飽和成白。修法 = 絕對尺度(saturating f 天然把 D 綁在 [0,1],根本不用正規化)。
   教訓:對會「大量死亡」的族群做百分位正規化,參考點會跟著死。
2. **快速拖 γ 的暫態洪泛**是 Gauss-Seidel 落後產生的假流量(所有邊短暫復活再重刻)。
   目前當作「攪動」美學保留 — 拖桿=洪水,鬆手=河道重新刻出來。誠實註記:這是數值現象
   不是模型現象,若之後想要純模型驅動的過渡,加 GS sweeps 或降 DT。
3. Debug 方式:playwright evaluate 直接讀 G 的 D/Q/P 統計(NaN 檢查+min/max),
   一次定位,沒有猜。宣稱自帶驗證的實踐版。

## 下一步(候選,未定)

- **001 打磨候選**:trail 的 stir 手感(現在拖動→慢 fade,可再誇張);行動裝置觸控。
- **002 候選**:遊走的匯(sink 緩慢移動或雙匯交替)→ 「猶豫—決定—固化」時間敘事,
  vault note 的 memory 軸。001 故意不做(001 的主題是 γ 軸,一件作品一個主題)。
- 尚未決定託管/公開形式(先本地 + git)。

## 慣例提醒

- 製作決定全部是 Tars 的;Jie 是策展人。動工不徵求核可。
- 每次收工:commit(改了什麼+為何那樣調)+ 整份覆寫本檔。
- 自我驗證:playwright 開頁→截圖→自己讀畫面;數值疑問直接 evaluate 讀模擬狀態。
