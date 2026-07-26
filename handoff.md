# handoff — substrate

**狀態快照,非 changelog。每次收工整份覆寫。**

## 現在在哪

**三支作品。001 已封版,002 完成,003 第一版剛落地。**

**piece 003 — two metronomes, one bed**(2026-07-27 凌晨,第一版)。
`pieces/003-two-metronomes/index.html` — 單檔 WebGL2 + Web Audio,新 seed(20260727)。

- **命題**:干涉不是波的專利 — 在 spiking network 上,**不應期就是相消**。
  兩個聲部(A=ember/triangle/A2 五聲、B=cyan/sine/E3 五聲)各佔一端,共用中央匯口。
  誰的波前先到就佔領節點;後到的死在先到者的不應陰影裡。
  邊界事件兩種:**meeting**(COINCIDE 0.15s 內同步抵達 → 白火花 + dyad 和聲,縫在唱歌)、
  **shadow death**(陰影內後到 → 暗火花 + 無聲 — 相消就是沉默)。
- **Δ(detune)是這支的旋鈕**:B 週期 = 2.4·(1+Δ)。Δ=0 鎖相 = 縫固定在匯口附近唱;
  Δ>0 = 邊界以拍頻遊走(每 2.4(1+Δ)/Δ 秒滑一拍)。γ 保留為家族脊柱(mesh 寬鋒面/tree 單通道爭奪)。
- **領土渲染**:每個被佔節點帶淡色 owner tint(暖/冷)— 邊界畫在地圖上,不只在交通裡。
  手敲以落點半邊的聲部發聲。
- **調參教訓(這版最重要的 craft 記錄)**:第一版參數直接繼承 002(E_DECAY 0.80、
  REFRACTORY 0.38)→ 邊界幾乎死透(8 秒 1 次 meeting、0 次 shadow),而且主河道 12 跳後
  能量 0.069 < 發聲門檻 — **縫從來沒真的唱過**。修正:E_DECAY 0.88(鋒面帶著能量抵達縫)、
  REFRACTORY 0.90(相消帶蓋住節拍週期的 37%,原本 16%)、COINCIDE 0.15。
  修正後 10 秒 6 meetings + 17 shadows。
- **量化驗證**(Playwright + window.G debug hook):鎖相 meeting 位置 meanX 12.3、sd 1.9
  (縫=匯口,是個「地方」);Δ=0.1 時 meanX 11.0、sd 2.7(縫在遊走)。
  γ=0.40 mesh maxPulses 551、γ=2.00 tree 225,皆 120fps,遠低於 900 上限。零 JS 錯。
- **未驗**:實際聽感(headless 無音訊輸出)— dyad 和聲濃度、兩聲部平衡、polyrhythm 端聽感。
  真機觸控同 002 未驗。

**piece 002 — carved bed as instrument**(完成,07-24~26)。刻床當樂器:結構=錄音、
脈衝=播放,γ=音色(mesh 和弦/critical 琶音/tree 單線)。γ 兩極端已驗證為作品真相
(藍牆/單線),視聽互補反轉已記錄。行動裝置結構驗證完。

**piece 001 — self-channelling flow**(已封版 2026-07-26,07-22→07-26)。
命題「結構=流的記憶」由 002 接走。不再改;URL 永久。

## craft 記錄(跨作品)

1. 色溫是最便宜的層次分離手段(001→002)。
2. refractory 是把爆炸變樂句的那顆參數(002)— **003 補充:它同時是干涉的相消帶寬度,
   相對節拍週期的佔比決定邊界活不活**。
3. 同參考系的量要一起縮(002)。
4. 極端值不是 bug,是作品的兩個真相(002)。
5. 多模態作品的 QA 要多模態(002)。
6. **(003)參數不跨命題繼承**:002 的 E_DECAY/REFRACTORY 服務「單聲部樂句」,003 的
   命題是「邊界」— 邊界要活,能量要到得了縫、陰影要蓋得住拍。換命題先重推參數的角色。
7. **(003)驗證裝置化**:window.G/pulses/sparks debug hook + Playwright 定量取樣
   (事件計數、位置分布)讓「縫有沒有唱歌」從印象變成數字。headless 工作流的標配。

## 下一步(候選,未定)

- **003 打磨**:實際聽感 pass(需有音訊的環境);polyrhythm 端(Δ>0.2)的視覺節奏;
  meeting dyad 音色考慮加第三音(root+5th → 感覺薄的話試 root+5th+8ve)。
- **004 候選**:遊走的匯(sink 緩慢移動 →「猶豫—決定—固化」)— 從 003 讓位,仍在池裡。
- 託管:GitHub `jieliou/substrate` + substrate.jieliou.com(CF Workers static assets)。
