"""scan_dashboard.py — 스캔 결과를 자동 새로고침 HTML 대시보드로 생성 (v2 친화 디자인)

- 반응형(폰/PC 자동), 라이트/다크 토글
- 시장 토글, 종목 검색(전체), 탭(추천/급등/급락/거래량/변동성/뉴스)
- 종목 클릭 → 가격·매수세/매도세 차트 + (한국)투자자별 표/차트 + 관련 뉴스
- 색: 상승/매수=빨강, 하락/매도=파랑 (한국식)
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
<title>마켓 스캐너</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  :root{--bg:#f5f6f8;--card:#fff;--soft:#f0f2f5;--bd:#e6e9ee;--tx:#1b2330;--mut:#6b7280;
    --hint:#9aa1ac;--up:#e02d3c;--down:#2563eb;--accent:#6d28d9;--info:#eef2ff;--infotx:#4338ca;
    --grid:#eef1f5;--line:#334155;}
  body.night{--bg:#0d1117;--card:#161b22;--soft:#1c2330;--bd:#2a3340;--tx:#e6edf3;--mut:#8b949e;
    --hint:#6b7280;--up:#f23645;--down:#3b82f6;--accent:#7c3aed;--info:#15233b;--infotx:#9db8ff;
    --grid:#21262d;--line:#cbd5e1;}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--tx);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Malgun Gothic",sans-serif;}
  .wrap{max-width:760px;margin:0 auto;padding:18px 16px 70px}
  .top{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px}
  .top h1{font-size:19px;margin:0;font-weight:700}
  .clock{font-size:11.5px;color:var(--hint);text-align:right;line-height:1.5}
  .clock b{color:var(--down)}
  .tbtn{background:var(--soft);color:var(--tx);border:1px solid var(--bd);border-radius:999px;
    padding:7px 13px;font-size:13px;cursor:pointer;font-weight:600}
  .banner{background:var(--info);color:var(--infotx);border-radius:14px;padding:13px 15px;
    font-size:13.5px;line-height:1.55;margin:12px 0 14px}
  .pills{display:flex;gap:8px;margin-bottom:12px}
  .pill{border-radius:999px;padding:9px 20px;font-size:14px;cursor:pointer;background:var(--soft);color:var(--mut)}
  .pill.on{background:var(--accent);color:#fff;font-weight:700}
  .search{display:flex;align-items:center;gap:9px;background:var(--soft);border-radius:14px;
    padding:13px 15px;margin-bottom:16px}
  .search input{border:0;background:transparent;outline:none;color:var(--tx);font-size:15px;width:100%}
  .tabs{display:flex;gap:16px;border-bottom:1px solid var(--bd);margin-bottom:4px;overflow-x:auto}
  .tab{padding:10px 0;font-size:14.5px;color:var(--hint);cursor:pointer;white-space:nowrap;border-bottom:2px solid transparent}
  .tab.on{color:var(--tx);font-weight:700;border-bottom-color:var(--accent)}
  .row{display:flex;align-items:center;gap:12px;padding:15px 6px;border-bottom:1px solid var(--bd);cursor:pointer}
  .row:hover{background:var(--soft)}
  .rk{width:18px;color:var(--hint);font-size:12.5px;text-align:center}
  .sig{font-size:12px;font-weight:700;padding:6px 10px;border-radius:9px;min-width:42px;text-align:center}
  .s-buy{background:rgba(224,45,60,.12);color:var(--up)}
  .s-sell{background:rgba(37,99,235,.12);color:var(--down)}
  .s-hold{background:var(--soft);color:var(--mut)}
  .nm{font-size:15.5px;font-weight:700}
  .nm small{color:var(--hint);font-size:13px;font-weight:400;margin-left:5px}
  .why{font-size:12.5px;color:var(--mut);margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:46vw}
  .px{font-size:15.5px;font-weight:700;text-align:right;white-space:nowrap}
  .chg{font-size:13px;text-align:right;white-space:nowrap}
  .up{color:var(--up)} .down{color:var(--down)}
  .chev{color:var(--hint);font-size:20px}
  .empty{padding:34px;text-align:center;color:var(--hint);font-size:14px}
  .ttl{font-size:14px;font-weight:700;margin:16px 0 8px}
  .nitem{display:block;padding:12px 6px;border-bottom:1px solid var(--bd);text-decoration:none;color:var(--tx)}
  .nitem:hover{background:var(--soft)}
  .nt{font-size:14.5px;font-weight:500;line-height:1.4}
  .nsrc{font-size:11.5px;color:var(--hint);margin-top:3px}
  .ov{position:fixed;inset:0;background:rgba(0,0,0,.5);display:none;align-items:center;justify-content:center;padding:14px;z-index:9}
  .ov.on{display:flex}
  .modal{background:var(--card);border-radius:18px;max-width:580px;width:100%;max-height:92vh;overflow:auto;padding:20px}
  .mh{display:flex;justify-content:space-between;align-items:center}
  .mh h2{margin:0;font-size:19px}
  .x{border:0;background:none;font-size:26px;color:var(--mut);cursor:pointer;line-height:1}
  .msub{font-size:13px;color:var(--mut);margin-top:2px}
  .stat{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:14px 0}
  .stat .b{background:var(--soft);border-radius:11px;padding:11px}
  .stat .k{font-size:11.5px;color:var(--mut)} .stat .v{font-size:15px;font-weight:700;margin-top:3px}
  .box{background:var(--soft);border-radius:12px;padding:12px;margin-top:12px}
  #tfbtns{display:flex;gap:6px;margin:12px 0 0}
  .tf{background:var(--soft);color:var(--mut);border:1px solid var(--bd);border-radius:8px;padding:6px 14px;font-size:13px;cursor:pointer}
  .tf.on{background:var(--accent);color:#fff;border-color:var(--accent);font-weight:700}
  table{width:100%;border-collapse:collapse;font-size:13px}
  .it td,.it th{padding:8px 6px;border-bottom:1px solid var(--bd);text-align:right}
  .it th:first-child,.it td:first-child{text-align:left;color:var(--mut)}
  @media(max-width:600px){
    .top h1{font-size:17px}
    .why{max-width:42vw}
    .nm{font-size:15px}
    .stat{grid-template-columns:1fr 1fr}
  }
</style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <h1>🛰️ 마켓 스캐너</h1>
    <div style="display:flex;align-items:center;gap:10px">
      <button class="tbtn" id="theme">🌙 야간</button>
      <div class="clock">갱신 <b id="updated"></b><br/><span id="countdown"></span></div>
    </div>
  </div>
  <div class="banner" id="banner"></div>
  <div class="pills" id="pills"></div>
  <div class="search"><span style="color:var(--hint)">🔍</span><input id="q" placeholder="어떤 종목을 찾으세요? (예: AAPL, 삼성)"/></div>
  <div class="tabs" id="tabs"></div>
  <div id="list"></div>
</div>

<div class="ov" id="ov">
  <div class="modal">
    <div class="mh"><div><h2 id="mt"></h2><div class="msub" id="ms"></div></div><button class="x" id="mx">×</button></div>
    <div class="stat" id="mstat"></div>
    <div id="tfbtns"></div>
    <div class="box"><canvas id="mc" height="150"></canvas></div>
    <div class="box"><canvas id="mflow" height="150"></canvas></div>
    <div id="mnews"></div>
    <div id="minv"></div>
  </div>
</div>

<script>
const DATA = /*__DATA__*/;
const RELOAD = __RELOAD__;
const M = DATA.meta, MK = DATA.markets;
const MK_LABEL = {US:'🇺🇸 미국', KR:'🇰🇷 한국'};
const CUR = {US:'$', KR:'₩'};
const TAB_KEYS = ['recommend','imminent','gainers','losers','vol_surge','volatile'];
const TABS = [['recommend','⭐ 추천'],['imminent','🚀 급등임박'],['gainers','📈 급등'],['losers','📉 급락'],
              ['vol_surge','🔊 거래량'],['volatile','⚡ 변동성'],['news','📰 뉴스']];
let curMarket = M.market_order[0], curTab = 'recommend', curRows = [];

const fmt = n => (n==null?'-':Number(n).toLocaleString());
const cur = () => CUR[curMarket]||'';
const sigCls = s => s==='BUY'?'s-buy':s==='SELL'?'s-sell':'s-hold';
const sigT = s => s==='BUY'?'매수':s==='SELL'?'매도':'관망';
const RK = () => MK[curMarket].ranked;
const ALL = () => MK[curMarket].all || [];

document.getElementById('updated').textContent = M.generated;

// 테마
const themeBtn=document.getElementById('theme');
function applyTheme(t){ document.body.classList.toggle('night', t==='night');
  themeBtn.textContent = t==='night'?'☀️ 주간':'🌙 야간'; }
applyTheme(localStorage.getItem('theme')||'light');
themeBtn.onclick=()=>{ const t=document.body.classList.contains('night')?'light':'night';
  localStorage.setItem('theme',t); applyTheme(t); };

// 시장 토글 / 탭
document.getElementById('pills').innerHTML = M.market_order.map(mk=>
  `<div class="pill ${mk===curMarket?'on':''}" data-m="${mk}">${MK_LABEL[mk]||mk}</div>`).join('');
document.getElementById('tabs').innerHTML = TABS.map(([k,l])=>
  `<div class="tab ${k===curTab?'on':''}" data-t="${k}">${l}</div>`).join('');
document.getElementById('pills').onclick=e=>{const p=e.target.closest('.pill');if(!p)return;
  curMarket=p.dataset.m; document.querySelectorAll('.pill').forEach(x=>x.classList.toggle('on',x.dataset.m===curMarket));
  document.getElementById('q').value=''; render();};
document.getElementById('tabs').onclick=e=>{const t=e.target.closest('.tab');if(!t)return;
  curTab=t.dataset.t; document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('on',x.dataset.t===curTab));
  document.getElementById('q').value=''; render();};
document.getElementById('q').oninput=render;

function whyText(d){
  if(curTab==='recommend') return (d.headline||(d.reasons||[]).join(' · '))+(d.score100!=null?` · 점수 ${d.score100}`:'');
  if(curTab==='imminent') return `거래량 평소의 ${d.vol_ratio}배 · 가격은 아직 (점수 ${d.score100!=null?d.score100:'-'})`;
  if(curTab==='vol_surge') return `거래량 평소의 ${d.vol_ratio}배`;
  if(curTab==='volatile') return `변동성(ATR) ${d.atr_pct}%`;
  return `예상 ${cur()}${fmt(d.pred_close)} (${d.pred_chg>0?'+':''}${d.pred_chg}%)`;
}
function rowHtml(d,i,rank){
  const up=d.day_change>0,dn=d.day_change<0;
  return `<div class="row" data-i="${i}">
    ${rank?`<span class="rk">${rank}</span>`:''}
    <span class="sig ${sigCls(d.signal)}">${sigT(d.signal)}</span>
    <div style="flex:1;min-width:0">
      <div class="nm">${d.ticker}<small>${d.name||''}</small></div>
      <div class="why">${whyText(d)}</div>
    </div>
    <div>
      <div class="px">${cur()}${fmt(d.close)}</div>
      <div class="chg ${up?'up':dn?'down':''}">${up?'▲':dn?'▼':''}${Math.abs(d.day_change)}%</div>
    </div>
    <span class="chev">›</span>
  </div>`;
}

function render(){
  const info = MK[curMarket], rk = info.ranked;
  const g=rk.gainers[0];
  document.getElementById('banner').innerHTML =
    `💡 오늘 ${curMarket==='US'?'미국':'한국'} 시장 — 추천 매수 <b>${rk.recommend.length}개</b>`
    + (g?`, 급등 1위 <b>${g.ticker} +${g.day_change}%</b>`:'')
    + `. 종목을 누르면 차트·뉴스가 열려요. <span style="color:var(--hint)">(${info.universe_size}종목·${info.data_mode})</span>`;

  const q=(document.getElementById('q').value||'').trim().toLowerCase();
  const L=document.getElementById('list');

  if(q){
    const res=ALL().filter(r=>r.ticker.toLowerCase().includes(q)||(r.name||'').toLowerCase().includes(q)).slice(0,60);
    curRows=res;
    L.innerHTML = res.length? `<div class="ttl">🔍 검색 결과 ${res.length}개</div>`
      + res.map((d,i)=>{const up=d.day_change>0,dn=d.day_change<0;
        return `<div class="row" data-i="${i}"><span class="sig ${sigCls(d.signal)}">${sigT(d.signal)}</span>
          <div style="flex:1;min-width:0"><div class="nm">${d.ticker}<small>${d.name||''}</small></div>
          <div class="why">예상 ${cur()}${fmt(d.pred_close)} (${d.pred_chg>0?'+':''}${d.pred_chg}%)</div></div>
          <div><div class="px">${cur()}${fmt(d.close)}</div>
          <div class="chg ${up?'up':dn?'down':''}">${up?'▲':dn?'▼':''}${Math.abs(d.day_change)}%</div></div>
          <span class="chev">›</span></div>`;}).join('')
      : '<div class="empty">검색 결과가 없어요</div>';
    return;
  }
  if(curTab==='news'){ curRows=[]; L.innerHTML=newsHtml(); return; }

  curRows = rk[curTab] || [];
  L.innerHTML = curRows.length? curRows.map((d,i)=>rowHtml(d,i,i+1)).join('')
    : '<div class="empty">해당 종목이 없어요</div>';
}

function newsHtml(){
  const n=M.news||{kr:[],us:[]};
  const li=(a,en)=>`<a class="nitem" href="${a.link||'#'}" target="_blank" rel="noopener">
    <div class="nt">${a.title||''}</div>
    <div class="nsrc">${a.source||''}${en&&a.title_en?(' · 원문: '+a.title_en):''}${a.date?(' · '+a.date):''}</div></a>`;
  const kr=(n.kr||[]).map(a=>li(a,false)).join('')||'<div class="empty">한국 뉴스 없음</div>';
  const us=(n.us||[]).map(a=>li(a,true)).join('')||'<div class="empty">미국 뉴스 없음</div>';
  return `<div class="ttl">🇰🇷 한국 증시 뉴스</div>${kr}<div class="ttl">🇺🇸 미국 증시 뉴스 <span style="font-weight:400;color:var(--hint)">(자동 한글 번역)</span></div>${us}`;
}

// 모달
let chart, flowChart, invChart, modalOpen=false;
const ov=document.getElementById('ov');
function openModalRow(r){
  if(!r) return;
  let full=r;
  if(!r.detail){ for(const k of TAB_KEYS){ const x=(RK()[k]||[]).find(z=>z.ticker===r.ticker&&z.detail); if(x){full=x;break;} } }
  const cy=cur(); modalOpen=true;
  document.getElementById('mt').textContent=`${r.ticker} ${r.name||''}`;
  document.getElementById('ms').textContent=`현재가 ${cy}${fmt(r.close)} · 등락 ${r.day_change>0?'+':''}${r.day_change}% · RSI ${r.rsi!=null?r.rsi:'-'} · 신호 ${sigT(r.signal)}`;
  const st=[['종합 매수점수', (full.score100!=null?full.score100:'-')+' / 100 ('+(full.grade||'-')+')'],
    ['자금흐름 MFI', full.mfi!=null?full.mfi:'-'],
    ['내일 예측 마감',`${cy}${fmt(r.pred_close)} (${r.pred_chg>0?'+':''}${r.pred_chg}%)`],
    ['예측 적중률',(r.pred_hit!=null?r.pred_hit:(full.pred_hit!=null?full.pred_hit:'-'))+'%'],
    ['예측 범위', full.pred_low!=null?`${cy}${fmt(full.pred_low)}~${fmt(full.pred_high)}`:'-'],
    ['거래량배수', full.vol_ratio!=null?full.vol_ratio+'x':'-']];
  document.getElementById('mstat').innerHTML=st.map(s=>`<div class="b"><div class="k">${s[0]}</div><div class="v">${s[1]}</div></div>`).join('');

  const cs=getComputedStyle(document.body);
  const gcol=cs.getPropertyValue('--grid').trim(), tcol=cs.getPropertyValue('--mut').trim();
  const lcol=cs.getPropertyValue('--line').trim(), txt=cs.getPropertyValue('--tx').trim();
  const grid={color:gcol}, tick={color:tcol,maxTicksLimit:8};
  const d=full.detail;
  if(chart)chart.destroy(); if(flowChart)flowChart.destroy(); if(invChart)invChart.destroy();
  const tfWrap=document.getElementById('tfbtns');
  function drawPrice(s,label){ if(chart)chart.destroy();
    chart=new Chart(document.getElementById('mc'),{type:'line',data:{labels:s.dates,
      datasets:[{label:'가격 ('+label+')',data:s.close,borderColor:lcol,borderWidth:1.8,pointRadius:0,tension:.15}]},
      options:{plugins:{legend:{labels:{color:tcol}}},scales:{x:{ticks:tick,grid:grid},y:{ticks:tick,grid:grid}}}}); }
  if(full.chart){
    const lab={"일":"일봉","주":"주봉","월":"월봉","년":"연봉"};
    const tfs=['일','주','월','년'].filter(k=>full.chart[k]&&full.chart[k].dates.length);
    tfWrap.innerHTML=tfs.map((k,i)=>`<button class="tf${i===0?' on':''}" data-k="${k}">${k}</button>`).join('');
    document.getElementById('mc').style.display='';
    drawPrice(full.chart[tfs[0]],lab[tfs[0]]);
    tfWrap.querySelectorAll('.tf').forEach(b=>b.onclick=()=>{
      tfWrap.querySelectorAll('.tf').forEach(x=>x.classList.toggle('on',x===b));
      drawPrice(full.chart[b.dataset.k],lab[b.dataset.k]);});
  } else if(d){ tfWrap.innerHTML=''; document.getElementById('mc').style.display='';
    drawPrice({dates:d.dates,close:d.close},'최근 60일');
  } else { tfWrap.innerHTML=''; document.getElementById('mc').style.display='none'; }
  document.getElementById('mflow').style.display = d?'':'none';
  if(d){
    const obv=[];let acc=0;for(let k=0;k<d.vol.length;k++){acc+=(d.updown[k]>0?1:-1)*d.vol[k];obv.push(Math.round(acc));}
    const vc=d.updown.map(u=>u>0?'rgba(224,45,60,.7)':'rgba(37,99,235,.7)');
    flowChart=new Chart(document.getElementById('mflow'),{data:{labels:d.dates,datasets:[
      {type:'bar',label:'거래량(매수=빨강/매도=파랑)',data:d.vol,backgroundColor:vc,yAxisID:'y',order:2},
      {type:'line',label:'누적 매수세',data:obv,borderColor:'#d29922',borderWidth:1.6,pointRadius:0,tension:.15,yAxisID:'y1',order:1}]},
      options:{plugins:{legend:{labels:{color:tcol}}},scales:{x:{ticks:tick,grid:grid},
        y:{position:'left',ticks:tick,grid:grid},y1:{position:'right',ticks:{color:'#d29922'},grid:{drawOnChartArea:false}}}}});
  }
  // 관련 뉴스
  const cn=full.news||[];
  document.getElementById('mnews').innerHTML = cn.length
    ? `<div class="ttl">📰 관련 뉴스</div>`+cn.map(a=>`<a class="nitem" href="${a.link||'#'}" target="_blank" rel="noopener"><div class="nt">${a.title||''}</div>${a.title_en?('<div class="nsrc">원문: '+a.title_en+'</div>'):''}</a>`).join('')
    : '';
  // 투자자별(한국)
  const inv=full.investors;
  const mi=document.getElementById('minv');
  if(inv&&inv.dates&&inv.dates.length){
    const n=inv.dates.length,stt=Math.max(0,n-8);
    const cellv=v=>`<td class="${v>0?'up':v<0?'down':''}">${v>0?'+':''}${v}</td>`;
    let rows='';for(let k=n-1;k>=stt;k--){rows+=`<tr><td>${inv.dates[k]}</td>${cellv(inv.indiv[k])}${cellv(inv.foreign[k])}${cellv(inv.inst[k])}</tr>`;}
    mi.innerHTML=`<div class="ttl">📊 투자자별 순매수 <span style="font-weight:400;color:var(--mut)">(억원·+매수/−매도)</span></div>
      <table class="it"><thead><tr><th>날짜</th><th>개인</th><th>외국인</th><th>기관</th></tr></thead><tbody>${rows}</tbody></table>
      <div class="box"><canvas id="minvc" height="150"></canvas></div>`;
    invChart=new Chart(document.getElementById('minvc'),{type:'bar',data:{labels:inv.dates,datasets:[
      {label:'개인',data:inv.indiv,backgroundColor:'#9ca3af'},
      {label:'외국인',data:inv.foreign,backgroundColor:'#10b981'},
      {label:'기관',data:inv.inst,backgroundColor:'#3b82f6'}]},
      options:{plugins:{legend:{labels:{color:tcol}}},scales:{x:{ticks:tick,grid:grid},y:{ticks:tick,grid:grid}}}});
  } else mi.innerHTML='';
  ov.classList.add('on');
}
document.getElementById('list').onclick=e=>{const r=e.target.closest('.row[data-i]');if(!r)return;
  const d=curRows[+r.dataset.i]; if(d) openModalRow(d);};
document.getElementById('mx').onclick=()=>{modalOpen=false;ov.classList.remove('on');};
ov.onclick=e=>{if(e.target===ov){modalOpen=false;ov.classList.remove('on');}};
document.addEventListener('keydown',e=>{if(e.key==='Escape'){modalOpen=false;ov.classList.remove('on');}});

// 자동 새로고침
let left=RELOAD; const cd=document.getElementById('countdown');
cd.textContent='다음 새로고침 '+left+'초';
setInterval(()=>{ if(modalOpen){cd.textContent='보는 중 (일시정지)';return;}
  left--; if(left<=0){location.reload();return;} cd.textContent='다음 새로고침 '+left+'초'; },1000);

render();
</script>
</body>
</html>"""
