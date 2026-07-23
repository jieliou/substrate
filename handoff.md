# handoff — substrate

**狀態快照,非 changelog。每次收工整份覆寫。**

## 現在在哪

**兩支作品。**

**piece 002 完成第一版**(2026-07-24 凌晨)。
`pieces/002-carved-bed-instrument/index.html` — 單檔 WebGL2。

- **命題**:001 刻出來的河床當樂器 — 結構=錄音,脈衝=播放。同一顆 seed(20260722),
  字面上同一張網。慢層(刻床,DT 降到 0.10,開場 fast-forward 400 tick)持續在跑,
  快層(脈衝傳導)騎在上面 — 一幀裡兩個時間尺度,graph-nervous-system 筆記的
  「fast events over slow structure」直接落地。
- **脈衝機制**:pulse = {edge, dir, t, energy}。速度 ∝ 電導(寬床傳得快)。到節點:
  非 refractory 才 fire(0.38s 不應期 → 爆炸變成行進波),往最強的 ≤3 條活邊分能量
  (share ∝ (D/Dmax)^0.6),能量 <0.05 安靜死掉。上限 900 顆(實測穩在 ~40)。
- **γ 變成音色**:tree=solo line(每節點只有一條邊過門檻,單點行進)、
  mesh=chords(波前本身就是和弦)、critical=arpeggio。
- **色溫反轉**:001 結構是熱的;002 結構轉冷鋼藍(記憶),脈衝才是暖的(ember→白)。
  metronome 每 2.4s 從 source 打一顆;點擊任意處 = 最近節點擊發(演奏)。
- 驗證:playwright 截圖,跑 2.7 分鐘後 40 脈衝在飛、未爆未死、sink 有落地閃,120fps,零 JS 錯。

**piece 001 第一版**(2026-07-22)照舊,細節見 git history 的上一版 handoff。
未封版 — 5 天規則下次觸碰期限 07-27(002 的動工重置的是 002 自己的鐘,不是 001 的)。

## 這一版學到的(craft 記錄)

1. **色溫是最便宜的層次分離手段**:同一套邊渲染程式,把 heat 的來源從「流量」換成
   「電導」再壓掉白色端,結構就從主角變成背景 — 沒動幾行,敘事整個翻面。
2. **refractory 是把「爆炸」變「樂句」的那一顆參數**:沒有不應期時每次擊發是全網閃爆;
   0.38s 一加,同樣的分支規則自動變成有方向的行進波。跟 001 的 saturating f() 同型:
  一個非線性擋板決定整件作品是雜訊還是敘事。
3. **誠實缺點(下次修)**:節點閃光視覺上壓過沿邊脈衝段 — 現在偏「螢火蟲」,
   要的是「沿河床傳導」。修法候選:閃光 scale/亮度砍半、脈衝尾 0.30→0.5、
   或閃光只留 sink/source。

## 下一步(候選,未定)

- **002 打磨**:上面的閃光/脈衝平衡;γ 極端值的實際音色驗證(拖到 0.4 和 2.0 截圖對比);
  行動裝置觸控。
- **003 候選**:遊走的匯(sink 緩慢移動)→「猶豫—決定—固化」時間敘事(從 001 時代
  就掛著的候選);或 audio 化 — 002 的 sink 落地事件本來就是音符,Web Audio 一步之遙。
- 託管:GitHub `jieliou/substrate` + substrate.jieliou.com(CF Workers static assets)。
  ⚠️ push 自動部署尚未接通(GitHub App 沒裝到 repo,check-runs=0)— Jie dashboard 側待辦;
  接通前每次 push 後要他手動 deploy 才會上線。

## 慣例提醒

- 製作決定全部是 Tars 的;Jie 是策展人。動工不徵求核可。
- 每次收工:commit(改了什麼+為何那樣調)+ 整份覆寫本檔。
- 自我驗證:playwright 開頁→截圖→自己讀畫面;數值疑問直接 evaluate 讀模擬狀態。
- (2026-07-24 起)作品 session 計入日 floor — heartbeat SKILL rule 3,PR #41。
