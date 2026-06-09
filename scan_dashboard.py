"""scan_dashboard.py — 스캔 결과를 자동 새로고침 HTML 대시보드로 생성

- 한국식 색상: 상승/매수 = 빨강, 하락/매도 = 파랑
- 한국/미국 시장 전환 토글
- 티커 + 회사명, 다음 마감가 예측(+과거 방향 적중률), 매수세/매도세 차트
"""
from __future__ import annotations
import json


def build_html(meta: dict, markets: dict, reload_seconds: int) -> str:
    payload = json.dumps({"meta": meta, "markets": markets}, ensure_ascii=False)
    return (_TEMPLATE
            .replace("/*__DATA__*/", payload)
            .replace("__RELOAD__", str(int(reload_seconds))))


_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Market Scanner</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  /* 한국식 색상: 상승/매수=빨강(--up), 하락/매도=파랑(--down) */
  :root{--bg:#0d1117;--panel:#161b22;--panel2:#1c2330;--border:#2a3340;
    --text:#e6edf3;--muted:#8b949e;--up:#f23645;--down:#3b82f6;--blue:#58a6ff;
    --amber:#d29922;--accent:#7c3aed;}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--text);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Malgun Gothic",sans-serif;}
  header{padding:20px 26px;border-bottom:1px solid var(--border);
    background:linear-gradient(135deg,#161b22,#1c2330);display:flex;
    justify-content:space-between;align-items:flex-end;flex-wrap:wrap;gap:10px}
  header h1{margin:0;font-size:19px}
  header .sub{color:var(--muted);font-size:12.5px;margin-top:6px}
  .clock{text-align:right;font-size:12px;color:var(--muted)}
  .clock b{color:var(--blue)}
  .wrap{max-width:1240px;margin:0 auto;padding:18px 26px 60px}
  .mkrow{display:flex;gap:8px;margin:16px 0 4px}
  .mkbtn{padding:9px 18px;border-radius:10px;border:1px solid var(--border);
    background:var(--panel);color:var(--muted);cursor:pointer;font-size:14px;font-weight:600}
  .mkbtn.active{background:var(--accent);border-color:var(--accent);color:#fff}
  .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
    gap:12px;margin:14px 0 22px}
  .card{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:14px 16px}
  .card .k{color:var(--muted);font-size:12px}
  .card .v{font-size:22px;font-weight:700;margin-top:5px}
  .tabs{display:flex;gap:6px;border-bottom:1px solid var(--border);margin-bottom:14px;flex-wrap:wrap}
  .tab{padding:9px 15px;cursor:pointer;color:var(--muted);border-bottom:2px solid transparent;font-size:13.5px}
  .tab.active{color:var(--text);border-bottom-color:var(--accent)}
  .view{display:none}.view.active{display:block}
  .hint{color:var(--muted);font-size:12px;margin:0 0 8px}
  table{width:100%;border-collapse:collapse;font-size:15px}
  th,td{padding:12px 12px;text-align:right;border-bottom:1px solid var(--border);white-space:nowrap}
  th:first-child,td:first-child,th.l,td.l{text-align:left}
  th{color:var(--muted);font-weight:600;font-size:11.5px}
  tbody tr{cursor:pointer}
  tbody tr:hover td{background:var(--panel2)}
  .rank{color:var(--muted);width:26px}
  .tk{font-weight:700;color:var(--text)}
  .nm{color:var(--muted);font-size:12.5px;margin-left:6px}
  .pos{color:var(--up)}.neg{color:var(--down)}
  .badge{padding:4px 12px;border-radius:20px;font-size:13px;font-weight:700}
  .b-buy{background:rgba(242,54,69,.15);color:var(--up)}
  .b-sell{background:rgba(59,130,246,.18);color:var(--down)}
  .b-hold{background:rgba(139,148,158,.15);color:var(--muted)}
  .hot{background:rgba(210,153,34,.18);color:var(--amber);border-radius:6px;padding:1px 6px;font-size:10.5px;margin-left:5px}
  .reason{text-align:left;color:var(--muted);font-size:11px;white-space:normal;max-width:240px}
  svg.spark{vertical-align:middle}
  .overlay{position:fixed;inset:0;background:rgba(0,0,0,.6);display:none;
    align-items:center;justify-content:center;z-index:50;padding:20px}
  .overlay.open{display:flex}
  .modal{background:var(--panel);border:1px solid var(--border);border-radius:14px;
    width:min(840px,96vw);max-height:92vh;overflow:auto;padding:20px 22px}
  .modal h2{margin:0;font-size:18px}
  .modal .mh{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}
  .close{cursor:pointer;color:var(--muted);font-size:22px;line-height:1;border:none;background:none}
  .pressure{display:flex;gap:10px;align-items:center;margin:10px 0 4px;flex-wrap:wrap}
  .bar{flex:1;min-width:200px;height:16px;border-radius:8px;overflow:hidden;
    background:var(--down);display:flex}
  .bar .buy{height:100%;background:var(--up)}
  .pl{font-size:12px;color:var(--muted)}
  .mstat{display:grid;grid-template-columns:repeat(auto-fit,minmax(90px,1fr));gap:8px;margin:12px 0}
  .mstat .k{font-size:11px;color:var(--muted)}.mstat .v{font-size:15px;font-weight:700;margin-top:2px}
  .chartbox{background:var(--panel2);border-radius:10px;padding:12px;margin-top:12px}
</style>
</head>
<body>
<header>
  <div><h1>🛰️ Market Scanner</h1><div class="sub" id="subline"></div></div>
  <div class="clock">마지막 갱신: <b id="updated"></b><br/>다음 새로고침: <span id="countdown"></span></div>
</header>
<div class="wrap">
  <div class="mkrow" id="mkToggle"></div>
  <div class="cards" id="cards"></div>
  <div class="tabs">
    <div class="tab active" data-v="recommend">⭐ 기술적 추천</div>
    <div class="tab" data-v="gainers">📈 급등 TOP</div>
    <div class="tab" data-v="losers">📉 급락 TOP</div>
    <div class="tab" data-v="vol_surge">🔊 거래량 급증</div>
    <div class="tab" data-v="volatile">⚡ 변동성 상위</div>
  </div>
  <p class="hint">💡 종목을 누르면 상세 차트가 열려요. 상승=<span class="pos">빨강</span>·하락=<span class="neg">파랑</span>. &nbsp; ※ 등락은 직전 <b>정규장 종가 기준</b>(프리장 제외) · 예측마감은 참고용 추정치예요.</p>
  <div id="panes"></div>
</div>
<div class="overlay" id="overlay">
  <div class="modal">
    <div class="mh"><h2 id="mTitle"></h2><button class="close" id="mClose">&times;</button></div>
    <div class="pl" id="mSub"></div>
    <div class="pressure"><span class="pl">매수세</span>
      <div class="bar"><div class="buy" id="mBar"></div></div>
      <span class="pl">매도세</span><span class="pl" id="mBuyPct"></span></div>
    <div class="mstat" id="mStats"></div>
    <div class="chartbox"><canvas id="mPrice" height="150"></canvas></div>
    <div class="chartbox"><canvas id="mFlow" height="150"></canvas></div>
    <p class="pl">막대=일별 거래량(빨강 매수우위/파랑 매도우위), 선=누적 매수세(매수-매도 거래량 누적).</p>
  </div>
</div>
<script>
const DATA = /*__DATA__*/;
const RELOAD = __RELOAD__;
const M = DATA.meta, MK = DATA.markets;
const MK_LABEL = {US:'🇺🇸 미국', KR:'🇰🇷 한국'};
const CUR = {US:'$', KR:'₩'};
const UP='#f23645', DOWN='#3b82f6';
let curMarket = M.market_order[0];
let curTab = 'recommend';
const fmt = n => (n==null?'-':Number(n).toLocaleString());
const cls = v => v>0?'pos':v<0?'neg':'';
const sgC = s => s==='BUY'?'b-buy':s==='SELL'?'b-sell':'b-hold';
const RK = () => MK[curMarket].ranked;
document.getElementById('updated').textContent = M.generated;
document.getElementById('mkToggle').innerHTML = M.market_order.map(mk=>
  `<button class="mkbtn ${mk===curMarket?'active':''}" data-mk="${mk}">${MK_LABEL[mk]||mk}</button>`).join('');
document.querySelectorAll('.mkbtn').forEach(b=>{
  b.onclick=()=>{ curMarket=b.dataset.mk;
    document.querySelectorAll('.mkbtn').forEach(x=>x.classList.toggle('active',x.dataset.mk===curMarket));
    renderMarket(); };
});
function spark(arr){
  if(!arr||arr.length<2) return '';
  const w=70,h=20,mn=Math.min(...arr),mx=Math.max(...arr),rng=(mx-mn)||1;
  const pts=arr.map((v,i)=>`${(i/(arr.length-1)*w).toFixed(1)},${(h-(v-mn)/rng*h).toFixed(1)}`).join(' ');
  const up=arr[arr.length-1]>=arr[0];
  return `<svg class="spark" width="${w}" height="${h}"><polyline fill="none" stroke="${up?UP:DOWN}" stroke-width="1.3" points="${pts}"/></svg>`;
}
const sgT = s => s==='BUY'?'매수':s==='SELL'?'매도':'관망';
function row(r,i,mode){
  const cy=CUR[curMarket]||'';
  const hotMove = Math.abs(r.day_change)>=M.big_move?'<span class="hot">급변동</span>':'';
  const hotVol = r.vol_ratio>=M.vol_surge?'<span class="hot">거래량↑</span>':'';
  let ex = mode==='vol_surge'?`<td>${r.vol_ratio}x</td>`
         : mode==='volatile'?`<td>${r.atr_pct}%</td>`
         : mode==='recommend'?`<td>${r.score}/5</td>`
         : `<td>${r.rsi}</td>`;
  return `<tr data-mode="${mode}" data-idx="${i}">
    <td class="rank">${i+1}</td>
    <td class="l"><span class="tk">${r.ticker}</span><span class="nm">${r.name||''}</span>${(mode==='gainers'||mode==='losers')?hotMove:''}${mode==='vol_surge'?hotVol:''}</td>
    <td>${cy}${fmt(r.close)}</td>
    <td class="${cls(r.day_change)}">${r.day_change>0?'+':''}${r.day_change}%</td>
    <td>${cy}${fmt(r.pred_close)} <span class="${cls(r.pred_chg)}" style="font-size:11px">(${r.pred_chg>0?'+':''}${r.pred_chg}%)</span></td>
    <td><span class="badge ${sgC(r.signal)}">${sgT(r.signal)}</span></td>
    ${ex}
    <td>${spark(r.spark)}</td>
  </tr>`;
}
function headFor(mode){
  const exh = mode==='vol_surge'?'거래량':mode==='volatile'?'변동성':mode==='recommend'?'점수':'RSI';
  return `<tr><th class="rank">#</th><th class="l">종목</th><th>현재가</th><th>등락</th><th>예측마감</th><th>신호</th><th>${exh}</th><th>추세</th></tr>`;
}
function pane(mode,rows){
  const body = rows.length? rows.map((r,i)=>row(r,i,mode)).join('')
    : '<tr><td colspan="8" style="text-align:center;color:var(--muted);padding:24px">해당 조건 종목 없음</td></tr>';
  return `<div class="view ${mode===curTab?'active':''}" id="${mode}">
    <table><thead>${headFor(mode)}</thead><tbody>${body}</tbody></table></div>`;
}
function renderMarket(){
  const info = MK[curMarket], rk = info.ranked;
  document.getElementById('subline').textContent =
    `${MK_LABEL[curMarket]} · 유니버스 ${info.universe} (${info.universe_size}종목) · 분석성공 ${info.n_analyzed}개 · MA${M.fast}/${M.slow}`;
  const g0=rk.gainers[0], l0=rk.losers[0];
  const cards=[['추천(BUY)',rk.recommend.length+'개'],
    ['급등 1위', g0? g0.ticker+' +'+g0.day_change+'%':'-'],
    ['급락 1위', l0? l0.ticker+' '+l0.day_change+'%':'-'],
    ['데이터', info.data_mode]];
  document.getElementById('cards').innerHTML = cards.map(c=>
    `<div class="card"><div class="k">${c[0]}</div><div class="v">${c[1]}</div></div>`).join('');
  document.getElementById('panes').innerHTML =
    ['recommend','gainers','losers','vol_surge','volatile'].map(m=>pane(m,rk[m])).join('');
}
document.querySelectorAll('.tab').forEach(t=>{
  t.onclick=()=>{ curTab=t.dataset.v;
    document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('active',x.dataset.v===curTab));
    document.querySelectorAll('.view').forEach(x=>x.classList.toggle('active',x.id===curTab));
  };
});
let priceChart, flowChart, modalOpen=false;
const overlay=document.getElementById('overlay');
function openModal(mode, idx){
  const r = RK()[mode][idx]; if(!r||!r.detail) return;
  const d=r.detail, cy=CUR[curMarket]||''; modalOpen=true;
  document.getElementById('mTitle').textContent = `${r.ticker}  ${r.name||''}`;
  document.getElementById('mSub').textContent =
    `현재가 ${cy}${fmt(r.close)} · 등락 ${r.day_change>0?'+':''}${r.day_change}% · RSI ${r.rsi} · 신호 ${sgT(r.signal)}`;
  const buyPct = r.buy_ratio!=null? r.buy_ratio : 50;
  document.getElementById('mBar').style.width = buyPct+'%';
  document.getElementById('mBuyPct').textContent = `(매수 ${buyPct}% · 매도 ${(100-buyPct).toFixed(1)}%, 최근20일)`;
  const stats=[
    ['예측 마감', `${cy}${fmt(r.pred_close)} (${r.pred_chg>0?'+':''}${r.pred_chg}%)`],
    ['예측 범위', `${cy}${fmt(r.pred_low)} ~ ${cy}${fmt(r.pred_high)}`],
    ['방향 적중률', (r.pred_hit!=null?r.pred_hit:'-')+'%'],
    ['평균오차', (r.pred_mae!=null?r.pred_mae:'-')+'%'],
    ['거래량배수',r.vol_ratio+'x'],['변동성(ATR)',r.atr_pct+'%']];
  document.getElementById('mStats').innerHTML = stats.map(s=>
    `<div><div class="k">${s[0]}</div><div class="v">${s[1]}</div></div>`).join('');
  const obv=[]; let acc=0;
  for(let k=0;k<d.vol.length;k++){ acc += (d.updown[k]>0?1:-1)*d.vol[k]; obv.push(Math.round(acc)); }
  const volColors = d.updown.map(u=> u>0?'rgba(242,54,69,.7)':'rgba(59,130,246,.7)');
  const grid={color:'#21262d'}, tick={color:'#8b949e',maxTicksLimit:8};
  if(priceChart)priceChart.destroy(); if(flowChart)flowChart.destroy();
  priceChart=new Chart(document.getElementById('mPrice'),{type:'line',
    data:{labels:d.dates,datasets:[{label:'종가',data:d.close,borderColor:'#cbd5e1',
      borderWidth:1.8,pointRadius:0,tension:.15}]},
    options:{responsive:true,plugins:{legend:{labels:{color:'#8b949e'}},
      title:{display:true,text:'가격 (최근 60일)',color:'#e6edf3'}},
      scales:{x:{ticks:tick,grid:grid},y:{ticks:tick,grid:grid}}}});
  flowChart=new Chart(document.getElementById('mFlow'),{
    data:{labels:d.dates,datasets:[
      {type:'bar',label:'거래량(매수=빨강/매도=파랑)',data:d.vol,backgroundColor:volColors,yAxisID:'y',order:2},
      {type:'line',label:'누적 매수세',data:obv,borderColor:'#d29922',borderWidth:1.6,
       pointRadius:0,tension:.15,yAxisID:'y1',order:1}]},
    options:{responsive:true,plugins:{legend:{labels:{color:'#8b949e'}},
      title:{display:true,text:'매수세 / 매도세',color:'#e6edf3'}},
      scales:{x:{ticks:tick,grid:grid},y:{position:'left',ticks:tick,grid:grid},
        y1:{position:'right',ticks:{color:'#d29922'},grid:{drawOnChartArea:false}}}}});
  overlay.classList.add('open');
}
function closeModal(){ modalOpen=false; overlay.classList.remove('open'); }
document.getElementById('mClose').onclick=closeModal;
overlay.onclick=e=>{ if(e.target===overlay) closeModal(); };
document.addEventListener('keydown',e=>{ if(e.key==='Escape') closeModal(); });
document.getElementById('panes').addEventListener('click',e=>{
  const tr=e.target.closest('tr[data-idx]'); if(!tr)return;
  openModal(tr.dataset.mode, +tr.dataset.idx);
});
let left = RELOAD;
const cd = document.getElementById('countdown');
cd.textContent = left+'초';
setInterval(()=>{
  if(modalOpen){ cd.textContent='차트 보는 중 (일시정지)'; return; }
  left--; if(left<=0){ location.reload(); return; }
  cd.textContent = left+'초';
}, 1000);
renderMarket();
</script>
</body>
</html>"""
