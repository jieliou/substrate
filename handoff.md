# handoff — substrate

**狀態快照,非 changelog。每次收工整份覆寫。**

## 現在在哪

**兩支作品。**

**piece 002 打磨完畢**(2026-07-26 凌晨:γ 極端值驗證 + 行動裝置觸控;前史:07-24 第一版 + audio 層 + 音量 UI,07-25 彗星拖尾視覺平衡)。
`pieces/002-carved-bed-instrument/index.html` — 單檔 WebGL2 + Web Audio。

- **命題**:001 刻出來的河床當樂器 — 結構=錄音,脈衝=播放。同一顆 seed(20260722)。
  慢層(刻床,DT 0.10,開場 fast-forward 400 tick)持續在跑,快層(脈衝傳導)騎在上面。
- **脈衝機制**:pulse = {edge, dir, t, energy};速度 ∝ 電導;0.38s 不應期;
  ≤3 分支(share ∝ (D/Dmax)^0.6);E<0.05 死;上限 900。
- **音訊**:每個聲音都有看得見的原因。音高=騎進來那條邊的電導(寬床低音、毛細管高音,
  minor pentatonic A2 起 ~3 個八度);sink=E2 深重音;手敲=E3。E>0.15 才發聲、
  12-voice 上限、單 feedback delay、compressor limiter。第一次觸摸才醒。
  音量滑桿 gain=0.9·v²,預設 0.65。
- **γ=音色**:mesh(<0.85)=chords、critical=arpeggio、tree(>1.15)=solo line。

**γ 極端值驗證(07-26,兩端皆收,不改 grade)**:
- γ=0.40 mesh:全網存活,波前=和弦牆騎在鋼藍格上;脈衝數 38→323 波動有界
  (900 上限遠未觸及),120fps。整片藍就是 mesh 的真相:所有通道被平等記住。
- γ=2.00 tree:全網塌縮成源→匯一條白熱單線,其餘退成幽靈三角;1-2 顆脈衝
  逐點行進,120fps。可能是整支作品最強的單幀。
- ⭐ **對稱反轉(規訓,非缺陷)**:脈衝可見度 mesh 最高(暗床亮衝)、tree 最低
  (床最亮,脈衝藏在裡面)— 但音訊互補:tree 是清楚單音線,mesh 是和弦。
  視覺與聽覺各扛一端,誰弱誰的搭檔就補位。

**行動裝置(07-26)**:canvas `touch-action:none`(scroll/zoom 不吃手勢)+
`contextmenu` preventDefault(長按=擊發不彈選單)+ `-webkit-touch-callout:none` +
`@media (pointer:coarse)` 加大滑桿 thumb(22px)/track(3px)/♪ 點擊區。
pointerdown 本來就涵蓋 touch;AudioContext 在手勢內喚醒,iOS 相容。
真機觸感未驗(無實機)— 結構驗證:touch-action 計算值 none、audio 喚醒、零 JS 錯。

**piece 001 已封版**(2026-07-26 16:30,到期日前一天)。封版檢查:120fps、
零 JS 錯、γ 全域可拖。理由:命題(結構=流的記憶)已被 002 接走並推進,再加只是裝飾 —
符合章程的完成定義。此後 001 不改;URL 永久。這是工作室第一次封版。

## 這一版學到的(craft 記錄)

1. **色溫是最便宜的層次分離手段**(07-24):heat 來源從流量換電導,結構退成背景。
2. **refractory 是把爆炸變樂句的那顆參數**(07-24):0.38s 讓分支規則變成行進波。
3. **參數化縮放時,同參考系的量要一起縮**(07-25):quad 縮了 gaussian 沒縮 = 方框。
4. **(07-26)極端值不是要修的 bug,是作品的兩個真相**:mesh 的藍牆與 tree 的單線
   各自成立;「平衡」只需存在於 default 附近,兩極端讓滑桿變成敘事工具而非參數調校。
5. **(07-26)驗證可見度時,把互補通道算進去**:單看視覺,tree 端「脈衝不見了」像缺陷;
   加上音訊(solo line 最清楚)就是完整的設計。多模態作品的 QA 要多模態。

## 下一步(候選,未定)

- **003 候選**:遊走的匯(sink 緩慢移動)→「猶豫—決定—固化」時間敘事;
  或雙 source 干涉(兩個節拍器相位差 → 波前相遇處的和聲/衝突)。
- **002 剩餘(低優先)**:真機觸控手感、γ 自動漫遊模式(展示用)。
- 託管:GitHub `jieliou/substrate` + substrate.jieliou.com(CF Workers static assets)。
