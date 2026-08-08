#!/usr/bin/env python3
import json
D = json.load(open('/tmp/report_data.json'))
DATA_JS = json.dumps(D, separators=(',', ':'))

HTML = r'''<title>STR Feasibility — 54 Ashburner St, Higgins</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{
  --plane:#eef1ee; --surface:#fbfcfb; --surface-2:#f4f6f4;
  --ink:#14191b; --secondary:#535d59; --muted:#8a938d;
  --accent:#0f6f5f; --accent-soft:#d7ece7;
  --line:#e0e5e0; --line-strong:#cbd2cc;
  --down:#bf6a1e; --mid:#2a6f8f; --up:#0f7a52; --ltr:#6a5bb0;
  --down-soft:#f4e4d2; --up-soft:#d6ecdf; --mid-soft:#d9e8ef;
  --good:#0ca30c; --warn:#c98a00; --crit:#c6403f;
  --shadow:0 1px 2px rgba(20,25,27,.05),0 8px 28px rgba(20,25,27,.06);
  --maxw:1080px;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --plane:#0e100f; --surface:#191d1b; --surface-2:#20241f;
  --ink:#f3f5f2; --secondary:#b7bfb9; --muted:#8a938d;
  --accent:#4fd1bb; --accent-soft:#123a34;
  --line:#2b302c; --line-strong:#3a413b;
  --down:#d98a3e; --mid:#59a9cc; --up:#37b477; --ltr:#9a8be0;
  --down-soft:#33260f; --up-soft:#122e20; --mid-soft:#122932;
  --good:#3bc44a; --warn:#e0aa2a; --crit:#e2635f;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px rgba(0,0,0,.35);
}}
:root[data-theme="dark"]{
  --plane:#0e100f; --surface:#191d1b; --surface-2:#20241f;
  --ink:#f3f5f2; --secondary:#b7bfb9; --muted:#8a938d;
  --accent:#4fd1bb; --accent-soft:#123a34;
  --line:#2b302c; --line-strong:#3a413b;
  --down:#d98a3e; --mid:#59a9cc; --up:#37b477; --ltr:#9a8be0;
  --down-soft:#33260f; --up-soft:#122e20; --mid-soft:#122932;
  --good:#3bc44a; --warn:#e0aa2a; --crit:#e2635f;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px rgba(0,0,0,.35);
}
*{box-sizing:border-box}
body{margin:0;background:var(--plane);color:var(--ink);
  font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  line-height:1.55;-webkit-font-smoothing:antialiased;}
.wrap{max-width:var(--maxw);margin:0 auto;padding:clamp(20px,4vw,56px) clamp(16px,4vw,40px);}
.num{font-variant-numeric:tabular-nums;}
h1,h2,h3{line-height:1.15;text-wrap:balance;margin:0;}
h1{font-size:clamp(26px,4.6vw,42px);letter-spacing:-.02em;font-weight:680;}
h2{font-size:clamp(19px,2.6vw,24px);letter-spacing:-.01em;font-weight:660;}
h3{font-size:15px;font-weight:640;}
p{margin:0;}
.eyebrow{text-transform:uppercase;letter-spacing:.16em;font-size:11.5px;font-weight:680;color:var(--accent);}
.lead{color:var(--secondary);font-size:clamp(15px,2vw,17.5px);max-width:62ch;}
a{color:var(--accent);}
/* header */
header{border-bottom:1px solid var(--line);padding-bottom:26px;margin-bottom:34px;}
.meta{display:flex;flex-wrap:wrap;gap:8px 10px;margin-top:20px;}
.chip{font-size:12px;color:var(--secondary);background:var(--surface);border:1px solid var(--line);
  border-radius:999px;padding:5px 12px;}
.chip b{color:var(--ink);font-weight:640;}
/* sections */
section{margin:44px 0;}
.sec-head{display:flex;align-items:baseline;gap:12px;margin-bottom:18px;}
.sec-head .n{font-size:12px;font-weight:680;color:var(--muted);font-variant-numeric:tabular-nums;}
.sec-head p{color:var(--secondary);font-size:14px;}
/* verdict */
.verdict{background:var(--surface);border:1px solid var(--line);border-radius:16px;
  padding:clamp(20px,3vw,30px);box-shadow:var(--shadow);position:relative;overflow:hidden;}
.verdict::before{content:"";position:absolute;left:0;top:0;bottom:0;width:4px;background:var(--warn);}
.verdict .tag{display:inline-flex;align-items:center;gap:8px;font-weight:650;font-size:13px;
  color:var(--warn);text-transform:uppercase;letter-spacing:.08em;}
.verdict .dot{width:9px;height:9px;border-radius:50%;background:var(--warn);}
.verdict h2{margin:12px 0 10px;max-width:32ch;}
.verdict p{color:var(--secondary);max-width:64ch;font-size:15.5px;}
/* stat grid */
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1px;
  background:var(--line);border:1px solid var(--line);border-radius:14px;overflow:hidden;margin-top:22px;}
.stat{background:var(--surface);padding:16px 18px;}
.stat .k{font-size:11.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;font-weight:600;}
.stat .v{font-size:clamp(20px,3vw,26px);font-weight:680;margin-top:6px;font-variant-numeric:tabular-nums;letter-spacing:-.01em;}
.stat .s{font-size:12.5px;color:var(--secondary);margin-top:3px;}
.up{color:var(--up)} .down{color:var(--down)} .mid{color:var(--mid)}
/* cards & charts */
.card{background:var(--surface);border:1px solid var(--line);border-radius:16px;
  padding:clamp(16px,2.4vw,24px);box-shadow:var(--shadow);}
.card h3{margin-bottom:4px;} .card .cap{color:var(--secondary);font-size:13px;margin-bottom:14px;max-width:70ch;}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:20px;}
@media(max-width:760px){.grid2{grid-template-columns:1fr;}}
figure{margin:0;}
svg{display:block;width:100%;height:auto;overflow:visible;}
.axis{fill:var(--muted);font-size:11px;font-variant-numeric:tabular-nums;}
.gl{stroke:var(--line);stroke-width:1;}
.baseline{stroke:var(--line-strong);stroke-width:1.4;}
.lbl{fill:var(--ink);font-size:12px;font-weight:640;font-variant-numeric:tabular-nums;}
.lbl-s{fill:var(--secondary);font-size:11px;}
.legend{display:flex;flex-wrap:wrap;gap:14px;margin-top:12px;font-size:12.5px;color:var(--secondary);}
.legend span{display:inline-flex;align-items:center;gap:6px;}
.sw{width:11px;height:11px;border-radius:3px;display:inline-block;}
.dash{width:16px;height:0;border-top:2px dashed var(--ltr);display:inline-block;}
/* table */
.tw{overflow-x:auto;border:1px solid var(--line);border-radius:14px;}
table{border-collapse:collapse;width:100%;font-size:13.5px;min-width:560px;}
th,td{padding:11px 14px;text-align:right;border-bottom:1px solid var(--line);font-variant-numeric:tabular-nums;}
th:first-child,td:first-child{text-align:left;font-variant-numeric:normal;}
thead th{background:var(--surface-2);font-size:11.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--secondary);font-weight:640;}
tbody tr:last-child td{border-bottom:none;}
tr.hi td{background:var(--accent-soft);font-weight:640;}
td .pos{color:var(--up);font-weight:640;} td .neg{color:var(--down);font-weight:640;}
.foot-note{font-size:12.5px;color:var(--muted);margin-top:10px;}
/* risk list */
.risks{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
@media(max-width:760px){.risks{grid-template-columns:1fr;}}
.risk{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:15px 17px;}
.risk .h{display:flex;align-items:center;gap:9px;font-weight:640;font-size:14px;}
.risk .h .i{width:22px;height:22px;border-radius:6px;display:grid;place-items:center;font-size:12px;font-weight:800;color:#fff;}
.risk p{color:var(--secondary);font-size:13px;margin-top:7px;}
.pill{font-size:11px;font-weight:660;padding:2px 8px;border-radius:999px;text-transform:uppercase;letter-spacing:.04em;}
/* tooltip */
#tip{position:fixed;pointer-events:none;opacity:0;transition:opacity .12s;z-index:50;
  background:var(--ink);color:var(--plane);font-size:12px;padding:7px 10px;border-radius:8px;
  box-shadow:var(--shadow);font-variant-numeric:tabular-nums;max-width:230px;line-height:1.4;}
#tip b{color:var(--surface);}
footer{border-top:1px solid var(--line);margin-top:52px;padding-top:22px;color:var(--muted);font-size:12.5px;}
.src{font-size:12.5px;color:var(--secondary);}
.src li{margin:4px 0;}
mark{background:var(--accent-soft);color:var(--ink);padding:0 3px;border-radius:3px;}
@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important;}}
</style>

<div class="wrap">
<header>
  <div class="eyebrow">Short-term rental feasibility · AirROI market analysis</div>
  <h1>54 Ashburner St, Higgins ACT 2615</h1>
  <p class="lead" style="margin-top:14px">Should this four-bedroom house be converted from a long-term rental into a short-term (Airbnb) let? This report models both, using AirROI's own revenue projection and 25 live comparable listings around the property.</p>
  <div class="meta" id="meta"></div>
</header>

<section id="verdict-sec" style="margin-top:8px">
  <div class="verdict">
    <span class="tag"><span class="dot"></span>Verdict — proceed only with top-tier execution</span>
    <h2 id="verdict-head"></h2>
    <p id="verdict-body"></p>
  </div>
  <div class="stats" id="stats"></div>
</section>

<section>
  <div class="sec-head"><span class="n">01</span><h2>Scenario returns vs. long-term rent</h2></div>
  <p class="lead" style="margin-bottom:18px">Net operating income after all running costs and the 5% ACT levy, before furnishing amortisation. The dashed line is what the house earns as a <b>$750/week long-term rental</b> — the bar has to clear it for short-term to be worth the extra work.</p>
  <div class="card"><figure><div id="chart-noi"></div></figure>
    <div class="legend">
      <span><span class="sw" style="background:var(--down)"></span>Conservative (AirROI p25)</span>
      <span><span class="sw" style="background:var(--mid)"></span>Base (median)</span>
      <span><span class="sw" style="background:var(--up)"></span>Aggressive (p75)</span>
      <span><span class="dash"></span>Long-term rent NOI</span>
    </div>
  </div>
  <div class="tw" style="margin-top:20px"><table id="scen-table"></table></div>
  <p class="foot-note" id="scen-note"></p>
</section>

<section>
  <div class="grid2">
    <div class="card">
      <h3>Where the base-case money goes</h3>
      <p class="cap">From AirROI's median gross revenue down to net operating income, per year.</p>
      <figure><div id="chart-waterfall"></div></figure>
    </div>
    <div class="card">
      <h3>Demand is barely seasonal</h3>
      <p class="cap">Share of annual revenue by month — mild summer peaks (Dec–Jan), a shallow autumn trough. Canberra runs on year-round government, business & event demand, not a holiday season.</p>
      <figure><div id="chart-season"></div></figure>
    </div>
  </div>
</section>

<section>
  <div class="sec-head"><span class="n">02</span><h2>The comparables tell the real story: execution &gt; location</h2></div>
  <p class="lead" style="margin-bottom:18px">Each dot is a live listing near the property. The spread is enormous — well-run 4-bed homes clear <b>60–70% occupancy</b> at <b>$340–425</b> a night; poorly-run ones sit under 30%. Your outcome depends far more on how the property is run than on the suburb.</p>
  <div class="card"><figure><div id="chart-scatter"></div></figure>
    <div class="legend">
      <span><span class="sw" style="background:var(--accent);border-radius:50%"></span>Comparable listing (bubble size = annual revenue)</span>
      <span><span class="sw" style="background:var(--ink);border-radius:50%"></span>This property — AirROI projection</span>
    </div>
  </div>
</section>

<section>
  <div class="sec-head"><span class="n">03</span><h2>Sensitivity — what it takes to beat long-term rent</h2></div>
  <p class="lead" style="margin-bottom:18px">Net yield (NOI ÷ $1M value) across occupancy and nightly rate. Cells at or above the long-term-rent net yield of <b id="ltr-yield-inline"></b> are green; below are amber. The <mark>break-even line sits around 51% occupancy</mark> at a $346 ADR.</p>
  <div class="card"><figure><div id="chart-heat"></div></figure></div>
</section>

<section>
  <div class="sec-head"><span class="n">04</span><h2>Management is the swing factor</h2></div>
  <p class="lead" style="margin-bottom:18px">The single biggest lever in the whole model isn't occupancy — it's <b>who runs it</b>. A full-service manager takes ~18% of revenue. Do it yourself and that money is yours, which is what tips the median case decisively past long-term rent.</p>
  <div class="grid2">
    <div class="card"><figure><div id="chart-mgmt"></div></figure>
      <div class="legend">
        <span><span class="sw" style="background:var(--mid)"></span>Professionally managed (−18%)</span>
        <span><span class="sw" style="background:var(--up)"></span>Self-managed</span>
        <span><span class="dash"></span>Long-term rent NOI</span>
      </div>
    </div>
    <div class="card" style="display:flex;flex-direction:column;justify-content:center;gap:14px">
      <div><div class="stat" style="padding:0"><div class="k">Self-managing adds</div><div class="v up" id="mgmt-delta"></div><div class="s">per year vs a manager — for your time on guest comms, cleaning coordination & pricing</div></div></div>
      <p style="font-size:14px;color:var(--secondary);border-top:1px solid var(--line);padding-top:14px">Managed, the base case is line-ball with long-term rent. <b>Self-managed, it clears it comfortably</b> — but you take on the operating work a long-term tenant would never create. That trade — roughly $11k/yr for a part-time job — is the real question behind "should I do this."</p>
    </div>
  </div>
</section>

<section>
  <div class="sec-head"><span class="n">05</span><h2>Financing, tax &amp; total return</h2></div>
  <p class="lead" style="margin-bottom:14px">Layering in a mortgage, your marginal tax rate, and capital growth. One thing to hold onto: <mark>capital growth is identical whether you let short- or long-term</mark> — same house, same market — so it's a wash between the two, and the bulk of your wealth here comes from the asset appreciating, not the letting strategy.</p>
  <div class="card">
    <div class="tw"><table id="lev-table"></table></div>
    <p class="foot-note" id="lev-note"></p>
  </div>
  <div class="grid2" style="margin-top:20px">
    <div class="card"><h3>Total return on equity — STR vs long-term</h3>
      <p class="cap">After-tax cash yield + capital growth, by how much you borrow. Bars converge because growth dominates and is common to both.</p>
      <figure><div id="chart-total"></div></figure>
      <div class="legend"><span><span class="sw" style="background:var(--mid)"></span>Short-term (self-manage upside not shown)</span><span><span class="sw" style="background:var(--ltr)"></span>Long-term rent</span></div>
    </div>
    <div class="card">
      <h3>What the tax layer means</h3>
      <ul class="src" style="padding-left:18px;margin:8px 0 0;font-size:13px" id="tax-notes"></ul>
    </div>
  </div>
</section>

<section>
  <div class="sec-head"><span class="n">06</span><h2>The 10-year picture</h2></div>
  <p class="lead" style="margin-bottom:14px">Projecting a decade out (rent &amp; revenue growing ~3%/yr, costs ~3%, the levy stepping to 7.5% in 2027, all-cash after-tax). The gap between the strategies is the <b>cumulative cash</b> — total wealth is dominated by the ~$411k capital gain that every option shares.</p>
  <div class="stats" id="proj-stats" style="margin-bottom:20px"></div>
  <div class="grid2">
    <div class="card"><h3>Cumulative after-tax cash flow</h3>
      <p class="cap">Where the strategies actually diverge over 10 years. Self-managing compounds the fee saving.</p>
      <figure><div id="chart-cash"></div></figure>
      <div class="legend">
        <span><span class="sw" style="background:var(--up)"></span>STR self-managed</span>
        <span><span class="sw" style="background:var(--mid)"></span>STR managed</span>
        <span><span class="sw" style="background:var(--ltr)"></span>Long-term rent</span>
      </div>
    </div>
    <div class="card"><h3>Total wealth at year 10</h3>
      <p class="cap">Property value + cumulative cash − setup. The capital-gain slab (grey) is identical for all three — the coloured tip is the only real difference.</p>
      <figure><div id="chart-wealth"></div></figure>
    </div>
  </div>
  <p class="foot-note" id="proj-note"></p>
</section>

<section>
  <div class="sec-head"><span class="n">07</span><h2>Market context</h2><p>AirROI trailing-12-month averages (all property sizes)</p></div>
  <div class="tw"><table id="market-table"></table></div>
  <p class="foot-note">Market averages blend all sizes — mostly 1–2 bedroom units — so they read low. A 4-bedroom home like this one sits well above them, which is why the property-specific projection ($383 ADR) is the right anchor, not the ~$230 market ADR.</p>
</section>

<section>
  <div class="sec-head"><span class="n">08</span><h2>Regulatory &amp; risk</h2></div>
  <div class="risks" id="risks"></div>
</section>

<section>
  <div class="sec-head"><span class="n">09</span><h2>Assumptions &amp; sources</h2></div>
  <div class="grid2">
    <div class="card">
      <h3>Key assumptions</h3>
      <ul class="src" id="assump" style="padding-left:18px;margin:10px 0 0"></ul>
    </div>
    <div class="card">
      <h3>Data sources</h3>
      <ul class="src" style="padding-left:18px;margin:10px 0 0">
        <li><b>AirROI Airbnb Data API</b> — property revenue calculator, 25 comparables, and market summaries for Higgins / District of Belconnen / North Canberra / Canberra. Pulled 8 Aug 2026.</li>
        <li><b>ACT Revenue Office</b> — short-term rental accommodation levy: 5% now, legislated to 7.5% from 1 Jul 2027.</li>
        <li><b>User-provided</b> — property value ($1.0M), configuration (4bd/2ba), expected long-term rent ($750/wk), furnishing budget ($30k).</li>
        <li>Cost assumptions (management, utilities, insurance, rates) are labelled estimates — all editable in the accompanying spreadsheet model.</li>
      </ul>
    </div>
  </div>
</section>

<footer>
  <p>Prepared for a short-term-rental conversion decision · Figures in AUD · Not financial advice — a decision aid built on modelled projections. Actual returns vary with management quality, pricing strategy, condition and regulation. Pair with a local leasing appraisal before committing.</p>
</footer>
</div>
<div id="tip"></div>

<script>
const DATA = __DATA__;
const AUD=(n,d=0)=>'$'+Number(n).toLocaleString('en-AU',{maximumFractionDigits:d,minimumFractionDigits:d});
const K=(n)=>'$'+(Math.round(n/1000))+'k';
const PC=(n,d=0)=>(n*100).toFixed(d)+'%';
const SVGNS='http://www.w3.org/2000/svg';
function el(t,a={},kids=[]){const e=document.createElementNS(SVGNS,t);for(const k in a)e.setAttribute(k,a[k]);
  (Array.isArray(kids)?kids:[kids]).forEach(c=>e.appendChild(c instanceof Node?c:document.createTextNode(String(c))));return e;}
const tip=document.getElementById('tip');
function showTip(html,ev){tip.innerHTML=html;tip.style.opacity=1;moveTip(ev);}
function moveTip(ev){const p=12;let x=ev.clientX+p,y=ev.clientY+p;
  if(x+tip.offsetWidth>innerWidth-8)x=ev.clientX-tip.offsetWidth-p;
  if(y+tip.offsetHeight>innerHeight-8)y=ev.clientY-tip.offsetHeight-p;tip.style.left=x+'px';tip.style.top=y+'px';}
function hideTip(){tip.style.opacity=0;}
function hoverable(node,html){node.style.cursor='default';
  node.addEventListener('mousemove',e=>showTip(html,e));node.addEventListener('mouseleave',hideTip);
  node.addEventListener('touchstart',e=>showTip(html,e.touches[0]),{passive:true});}

/* ---- meta chips ---- */
(()=>{const m=document.getElementById('meta');
  const chips=[['Value','$1.0M'],['Config','4 bd · 2 ba · sleeps 8'],['Market','Higgins, District of Belconnen'],
    ['Data','AirROI · Aug 2026'],['Comparables','25 listings']];
  m.innerHTML=chips.map(c=>`<span class="chip">${c[0]} <b>${c[1]}</b></span>`).join('');})();

/* ---- verdict + stats ---- */
(()=>{const s=DATA.scenarios,ltr=DATA.ltr,cmp=DATA.compare,be=DATA.breakeven;
  document.getElementById('verdict-head').textContent=
    `At typical performance, short-term letting is about line-ball with a long-term rental — the upside is real but only with top-quartile execution.`;
  document.getElementById('verdict-body').innerHTML=
    `AirROI's median projection puts short-term NOI at <b>${AUD(s.base.noi)}</b> against <b>${AUD(ltr.noi)}</b> for a $750/week long-term rent — a difference of <b>${AUD(cmp.str_advantage_pre_amort)}</b> before you amortise the ${AUD(30000)} fit-out. The downside case earns <b>${AUD(s.conservative.noi-ltr.noi)}</b> less than long-term; the top-quartile case earns <b>+${AUD(s.aggressive.noi-ltr.noi)}</b> more. It's a higher-variance bet whose expected edge shows up only in the upper quartile.`;
  const stats=[
    ['Base STR revenue',AUD(s.base.gross_revenue),'AirROI median for this home','mid'],
    ['Base STR net income',AUD(s.base.noi),'after costs & 5% levy','mid'],
    ['Long-term rent income',AUD(ltr.noi),'$750/wk, net','ltrc'],
    ['Break-even occupancy',PC(be.occupancy_to_match_ltr_at_base_adr),'to match long-term rent',''],
    ['Upside vs long-term',' +'+AUD(s.aggressive.noi-ltr.noi),'top-quartile (p75) case','up'],
    ['Downside vs long-term',AUD(s.conservative.noi-ltr.noi),'weak case (p25)','down'],
  ];
  document.getElementById('stats').innerHTML=stats.map(x=>
    `<div class="stat"><div class="k">${x[0]}</div><div class="v ${x[3]==='up'?'up':x[3]==='down'?'down':''}">${x[1]}</div><div class="s">${x[2]}</div></div>`).join('');
  document.getElementById('ltr-yield-inline').textContent=PC(ltr.net_yield_pct/100,2);
})();

/* ---- Chart 1: scenario NOI bars vs LTR line ---- */
(()=>{const s=DATA.scenarios,ltr=DATA.ltr.noi;
  const items=[['Conservative',s.conservative,'var(--down)'],['Base',s.base,'var(--mid)'],['Aggressive',s.aggressive,'var(--up)']];
  const W=720,H=340,mL=64,mR=20,mT=16,mB=54;const iw=W-mL-mR,ih=H-mT-mB;
  const max=Math.max(s.aggressive.noi,ltr)*1.15;
  const x=i=>mL+iw*(i+0.5)/items.length;const bw=iw/items.length*0.5;
  const y=v=>mT+ih-ih*(v/max);
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,role:'img'});
  for(let t=0;t<=max;t+=10000){svg.appendChild(el('line',{class:'gl',x1:mL,x2:W-mR,y1:y(t),y2:y(t)}));
    svg.appendChild(el('text',{class:'axis',x:mL-8,y:y(t)+4,'text-anchor':'end'},K(t)));}
  svg.appendChild(el('line',{class:'baseline',x1:mL,x2:W-mR,y1:y(0),y2:y(0)}));
  items.forEach((it,i)=>{const[name,sc,col]=it;const bx=x(i)-bw/2,by=y(sc.noi),bh=y(0)-by;
    const r=el('rect',{x:bx,y:by,width:bw,height:bh,rx:5,fill:col});
    hoverable(r,`<b>${name}</b><br>Occupancy ${PC(sc.occupancy)} · ADR ${AUD(sc.adr)}<br>Gross ${AUD(sc.gross_revenue)}<br>NOI <b>${AUD(sc.noi)}</b><br>Net yield ${sc.net_yield_pct}%`);
    svg.appendChild(r);
    svg.appendChild(el('text',{class:'lbl',x:x(i),y:by-8,'text-anchor':'middle'},AUD(sc.noi)));
    svg.appendChild(el('text',{class:'lbl-s',x:x(i),y:H-32,'text-anchor':'middle'},name));
    svg.appendChild(el('text',{class:'axis',x:x(i),y:H-17,'text-anchor':'middle'},PC(sc.occupancy)+' · '+AUD(sc.adr)));
  });
  // LTR reference line
  svg.appendChild(el('line',{x1:mL,x2:W-mR,y1:y(ltr),y2:y(ltr),stroke:'var(--ltr)','stroke-width':2,'stroke-dasharray':'7 5'}));
  const tagw=156;
  svg.appendChild(el('rect',{x:W-mR-tagw,y:y(ltr)-24,width:tagw,height:19,rx:5,fill:'var(--ltr)'}));
  svg.appendChild(el('text',{x:W-mR-8,y:y(ltr)-10.5,fill:'#fff','font-size':11,'font-weight':650,'text-anchor':'end'},`Long-term rent ${AUD(ltr)}`));
  document.getElementById('chart-noi').appendChild(svg);
})();

/* ---- scenario table ---- */
(()=>{const s=DATA.scenarios,ltr=DATA.ltr;
  const rows=[['Occupancy',x=>PC(x.occupancy)],['ADR (nightly)',x=>AUD(x.adr)],['Nights booked',x=>x.nights_booked],
    ['Gross revenue',x=>AUD(x.gross_revenue)],['ACT levy (5%)',x=>AUD(-x.act_levy)],['Platform fee',x=>AUD(-x.platform_fee)],
    ['Management fee',x=>AUD(-x.management_fee)],['Fixed operating costs',x=>AUD(-x.fixed_opex)],
    ['Net operating income',x=>AUD(x.noi)],['Net yield',x=>x.net_yield_pct+'%'],
    ['vs. long-term rent',x=>{const d=x.noi-ltr.noi;return `<span class="${d>=0?'pos':'neg'}">${d>=0?'+':''}${AUD(d)}</span>`;}]];
  const cols=[['conservative','Conservative'],['base','Base'],['aggressive','Aggressive']];
  let h='<thead><tr><th>Per year (AUD)</th>'+cols.map(c=>`<th>${c[1]}</th>`).join('')+'</tr></thead><tbody>';
  rows.forEach(r=>{const hi=(r[0]==='Net operating income')?' class="hi"':'';
    h+=`<tr${hi}><td>${r[0]}</td>`+cols.map(c=>`<td>${r[1](s[c[0]])}</td>`).join('')+'</tr>';});
  h+='</tbody>';document.getElementById('scen-table').innerHTML=h;
  document.getElementById('scen-note').innerHTML=`Scenarios anchored to AirROI's revenue percentiles for this exact property: Conservative = p25, Base = median (p50), Aggressive = p75. Break-even to match long-term rent ≈ ${AUD(DATA.breakeven.gross_revenue_to_match_ltr)} gross (~${PC(DATA.breakeven.occupancy_to_match_ltr_at_base_adr)} occupancy). All-cash basis; furnishing amortised separately.`;
})();

/* ---- Chart 2: waterfall ---- */
(()=>{const b=DATA.scenarios.base;
  const steps=[['Gross',b.gross_revenue,'total','var(--mid)'],['ACT levy',-b.act_levy,'neg','var(--down)'],
    ['Platform',-b.platform_fee,'neg','var(--down)'],['Mgmt fee',-b.management_fee,'neg','var(--down)'],
    ['Fixed costs',-b.fixed_opex,'neg','var(--down)'],['NOI',b.noi,'total','var(--up)']];
  const W=520,H=320,mL=52,mR=12,mT=14,mB=48;const iw=W-mL-mR,ih=H-mT-mB;
  const max=b.gross_revenue*1.08;const y=v=>mT+ih-ih*(v/max);
  const n=steps.length;const bw=iw/n*0.62;const cx=i=>mL+iw*(i+0.5)/n;
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,role:'img'});
  for(let t=0;t<=max;t+=20000){svg.appendChild(el('line',{class:'gl',x1:mL,x2:W-mR,y1:y(t),y2:y(t)}));
    svg.appendChild(el('text',{class:'axis',x:mL-7,y:y(t)+4,'text-anchor':'end'},K(t)));}
  svg.appendChild(el('line',{class:'baseline',x1:mL,x2:W-mR,y1:y(0),y2:y(0)}));
  let run=0;
  steps.forEach((st,i)=>{const[name,val,kind,col]=st;let top,bot;
    if(kind==='total'){top=y(val);bot=y(0);run=val;}
    else{const start=run;run+=val;top=y(Math.max(start,run));bot=y(Math.min(start,run));}
    const hgt=Math.max(bot-top,1.5);
    const r=el('rect',{x:cx(i)-bw/2,y:top,width:bw,height:hgt,rx:3,fill:col});
    hoverable(r,`<b>${name}</b><br>${val>=0?'+':''}${AUD(val)}${kind!=='total'?'<br>running: '+AUD(run):''}`);
    svg.appendChild(r);
    if(i<n-1&&kind!=='total'){/*connector*/}
    svg.appendChild(el('text',{class:'lbl-s',x:cx(i),y:H-30,'text-anchor':'middle','font-size':10.5},name));
    svg.appendChild(el('text',{class:'axis',x:cx(i),y:H-16,'text-anchor':'middle','font-size':10},(val>=0?'':'−')+K(Math.abs(val)).slice(1)));
  });
  document.getElementById('chart-waterfall').appendChild(svg);
})();

/* ---- Chart: seasonality ---- */
(()=>{const s=DATA.seasonality;const mo=['J','F','M','A','M','J','J','A','S','O','N','D'];
  const full=['January','February','March','April','May','June','July','August','September','October','November','December'];
  const W=520,H=300,mL=40,mR=12,mT=14,mB=40;const iw=W-mL-mR,ih=H-mT-mB;
  const max=Math.max(...s)*1.12;const y=v=>mT+ih-ih*(v/max);
  const bw=iw/12*0.62;const cx=i=>mL+iw*(i+0.5)/12;
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,role:'img'});
  for(let t=0;t<=max;t+=0.03){svg.appendChild(el('line',{class:'gl',x1:mL,x2:W-mR,y1:y(t),y2:y(t)}));
    svg.appendChild(el('text',{class:'axis',x:mL-7,y:y(t)+4,'text-anchor':'end'},(t*100).toFixed(0)+'%'));}
  svg.appendChild(el('line',{class:'baseline',x1:mL,x2:W-mR,y1:y(0),y2:y(0)}));
  const avg=1/12;
  s.forEach((v,i)=>{const col=v>=avg?'var(--up)':'var(--mid)';
    const r=el('rect',{x:cx(i)-bw/2,y:y(v),width:bw,height:y(0)-y(v),rx:3,fill:col,opacity:0.9});
    hoverable(r,`<b>${full[i]}</b><br>${PC(v,1)} of annual revenue`);svg.appendChild(r);
    svg.appendChild(el('text',{class:'axis',x:cx(i),y:H-14,'text-anchor':'middle'},mo[i]));});
  document.getElementById('chart-season').appendChild(svg);
})();

/* ---- Chart 3: comparables scatter (occ x adr, size=rev) ---- */
(()=>{const c=DATA.comps;const calc=DATA.calc;
  const W=720,H=420,mL=54,mR=18,mT=18,mB=52;const iw=W-mL-mR,ih=H-mT-mB;
  const adrMax=620,occMax=0.8;
  const x=o=>mL+iw*(o/occMax);const y=a=>mT+ih-ih*(a/adrMax);
  const rMax=Math.max(...c.map(p=>p.rev),calc.revenue);const rad=v=>6+16*Math.sqrt(v/rMax);
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,role:'img'});
  for(let o=0;o<=occMax+.001;o+=0.2){svg.appendChild(el('line',{class:'gl',x1:x(o),x2:x(o),y1:mT,y2:mT+ih}));
    svg.appendChild(el('text',{class:'axis',x:x(o),y:H-32,'text-anchor':'middle'},PC(o)));}
  for(let a=0;a<=adrMax;a+=100){svg.appendChild(el('line',{class:'gl',x1:mL,x2:W-mR,y1:y(a),y2:y(a)}));
    svg.appendChild(el('text',{class:'axis',x:mL-8,y:y(a)+4,'text-anchor':'end'},'$'+a));}
  svg.appendChild(el('text',{class:'lbl-s',x:mL+iw/2,y:H-12,'text-anchor':'middle'},'Occupancy →'));
  svg.appendChild(el('text',{class:'lbl-s',x:14,y:mT+ih/2,'text-anchor':'middle',transform:`rotate(-90 14 ${mT+ih/2})`},'ADR (nightly) →'));
  c.forEach(p=>{const cc=el('circle',{cx:x(p.occ),cy:y(Math.min(p.adr,adrMax)),r:rad(p.rev),
      fill:'var(--accent)','fill-opacity':0.24,stroke:'var(--accent)','stroke-width':1.3});
    hoverable(cc,`<b>${p.bd}-bed comparable</b><br>Occupancy ${PC(p.occ)}<br>ADR ${AUD(p.adr)}<br>Annual revenue <b>${AUD(p.rev)}</b>`);
    svg.appendChild(cc);});
  // property projection point
  const px=x(calc.occ),py=y(Math.min(calc.adr,adrMax));
  svg.appendChild(el('circle',{cx:px,cy:py,r:rad(calc.revenue),fill:'none',stroke:'var(--ink)','stroke-width':2,'stroke-dasharray':'4 3'}));
  const star=el('circle',{cx:px,cy:py,r:7,fill:'var(--ink)',stroke:'var(--surface)','stroke-width':2});
  hoverable(star,`<b>This property (projection)</b><br>Occupancy ${PC(calc.occ)}<br>ADR ${AUD(calc.adr)}<br>Revenue (avg) <b>${AUD(calc.revenue)}</b><br>Median ${AUD(calc.pct.revenue.p50)}`);
  svg.appendChild(star);
  svg.appendChild(el('text',{class:'lbl',x:px+12,y:py-10},'This property'));
  document.getElementById('chart-scatter').appendChild(svg);
})();

/* ---- Chart 4: sensitivity heatmap ---- */
(()=>{const I=DATA;const OC_var=0.05+0.03+0.18;// levy+platform+mgmt
  const fixed=6000+2400+2400+3500+3800+800;const value=1000000;const ltrYield=DATA.ltr.net_yield_pct/100;
  const occs=[0.30,0.40,0.50,0.60,0.70,0.80];const adrs=[500,450,400,350,300,250];
  const W=720,H=380,mL=64,mT=30,cellG=4;const gw=W-mL-14,gh=H-mT-30;
  const cw=(gw)/occs.length,ch=(gh)/adrs.length;
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,role:'img'});
  svg.appendChild(el('text',{class:'lbl-s',x:mL+gw/2,y:16,'text-anchor':'middle'},'Occupancy →'));
  svg.appendChild(el('text',{class:'lbl-s',x:16,y:mT+gh/2,'text-anchor':'middle',transform:`rotate(-90 16 ${mT+gh/2})`},'ADR →'));
  occs.forEach((o,j)=>svg.appendChild(el('text',{class:'axis',x:mL+cw*(j+0.5),y:mT-8,'text-anchor':'middle'},PC(o))));
  adrs.forEach((a,i)=>svg.appendChild(el('text',{class:'axis',x:mL-8,y:mT+ch*(i+0.5)+4,'text-anchor':'end'},'$'+a)));
  adrs.forEach((a,i)=>occs.forEach((o,j)=>{
    const gross=a*o*365;const noi=gross*(1-OC_var)-fixed;const yld=noi/value;
    const diff=yld-ltrYield;
    // color: amber below LTR, green above; intensity by distance
    const t=Math.max(-1,Math.min(1,diff/0.02));
    const col=t>=0?`color-mix(in srgb, var(--up) ${20+t*70}%, var(--surface))`
                   :`color-mix(in srgb, var(--down) ${20+(-t)*70}%, var(--surface))`;
    const rx=mL+cw*j+cellG/2,ry=mT+ch*i+cellG/2;
    const r=el('rect',{x:rx,y:ry,width:cw-cellG,height:ch-cellG,rx:4,fill:col});
    hoverable(r,`Occ ${PC(o)} · ADR ${AUD(a)}<br>Gross ${AUD(gross)}<br>NOI ${AUD(noi)}<br>Net yield <b>${PC(yld,2)}</b><br>vs LTR ${diff>=0?'+':''}${PC(diff,2)}`);
    svg.appendChild(r);
    svg.appendChild(el('text',{x:rx+(cw-cellG)/2,y:ry+(ch-cellG)/2+4,'text-anchor':'middle',
      'font-size':11,'font-variant-numeric':'tabular-nums',fill:'var(--ink)','font-weight':600},PC(yld,1)));
  }));
  document.getElementById('chart-heat').appendChild(svg);
})();

/* ---- Chart: management self vs managed ---- */
(()=>{const mc=DATA.advanced.management_comparison,ltr=DATA.ltr.noi;
  const items=[['Managed',mc.managed.noi,'var(--mid)'],['Self-managed',mc.self_managed.noi,'var(--up)']];
  const W=520,H=300,mL=58,mR=16,mT=16,mB=44;const iw=W-mL-mR,ih=H-mT-mB;
  const max=Math.max(mc.self_managed.noi,ltr)*1.18;
  const cx=i=>mL+iw*(i+0.5)/items.length;const bw=iw/items.length*0.44;const y=v=>mT+ih-ih*(v/max);
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,role:'img'});
  for(let t=0;t<=max;t+=10000){svg.appendChild(el('line',{class:'gl',x1:mL,x2:W-mR,y1:y(t),y2:y(t)}));
    svg.appendChild(el('text',{class:'axis',x:mL-7,y:y(t)+4,'text-anchor':'end'},K(t)));}
  svg.appendChild(el('line',{class:'baseline',x1:mL,x2:W-mR,y1:y(0),y2:y(0)}));
  items.forEach((it,i)=>{const[nm,v,col]=it;const by=y(v);
    const r=el('rect',{x:cx(i)-bw/2,y:by,width:bw,height:y(0)-by,rx:5,fill:col});
    hoverable(r,`<b>${nm}</b><br>Base-case NOI <b>${AUD(v)}</b>`);svg.appendChild(r);
    svg.appendChild(el('text',{class:'lbl',x:cx(i),y:by-8,'text-anchor':'middle'},AUD(v)));
    svg.appendChild(el('text',{class:'lbl-s',x:cx(i),y:H-16,'text-anchor':'middle'},nm));});
  svg.appendChild(el('line',{x1:mL,x2:W-mR,y1:y(ltr),y2:y(ltr),stroke:'var(--ltr)','stroke-width':2,'stroke-dasharray':'7 5'}));
  svg.appendChild(el('text',{x:W-mR,y:y(ltr)-6,'text-anchor':'end',fill:'var(--ltr)','font-size':11,'font-weight':650},`Long-term rent ${AUD(ltr)}`));
  document.getElementById('chart-mgmt').appendChild(svg);
  document.getElementById('mgmt-delta').textContent='+'+AUD(mc.self_managed.extra_income_vs_managed);
})();

/* ---- leverage & tax table ---- */
(()=>{const lt=DATA.advanced.leverage_and_tax,a=DATA.advanced.assumptions;
  const labels=Object.keys(lt.str_base_managed);
  const rows=[
    ['Loan',x=>AUD(x.loan)],['Your equity',x=>AUD(x.equity_invested)],
    ['Interest cost',x=>AUD(-x.interest)],['Pre-tax cash flow',x=>AUD(x.pre_tax_cash_flow)],
    ['Tax / (refund)',x=>x.tax_or_refund<=0?`<span class="pos">refund ${AUD(-x.tax_or_refund)}</span>`:AUD(-x.tax_or_refund)],
    ['After-tax cash flow',x=>{const v=x.after_tax_cash_flow;return `<span class="${v>=0?'pos':'neg'}">${AUD(v)}</span>`;}],
    ['Cash-on-cash (after tax)',x=>{const v=x.cash_on_cash_aftertax_pct;return `<span class="${v>=0?'pos':'neg'}">${v}%</span>`;}],
    ['Capital gain @'+PC(a.capital_growth_rate,1),x=>AUD(x.capital_gain)],
    ['Total return on equity',x=>`<b>${x.total_return_pct}%</b>`],
  ];
  let h='<thead><tr><th>Base STR (managed) — per year</th>'+labels.map(l=>`<th>${l}</th>`).join('')+'</tr></thead><tbody>';
  rows.forEach(r=>{const hi=r[0]==='Total return on equity'?' class="hi"':'';
    h+=`<tr${hi}><td>${r[0]}</td>`+labels.map(l=>`<td>${r[1](lt.str_base_managed[l])}</td>`).join('')+'</tr>';});
  h+='</tbody>';document.getElementById('lev-table').innerHTML=h;
  document.getElementById('lev-note').innerHTML=`Assumptions: interest ${PC(a.interest_rate,1)}, marginal tax ${PC(a.marginal_rate)}, capital growth ${PC(a.capital_growth_rate,1)} (=${AUD(a.capital_gain_pa)}/yr, identical for long-term rent). Negative cash-on-cash under leverage = negative gearing — the shortfall is funded by you but is tax-deductible and offset against other income. Not tax advice.`;
})();

/* ---- Chart: total return STR vs LTR by leverage ---- */
(()=>{const lt=DATA.advanced.leverage_and_tax;const labels=Object.keys(lt.str_base_managed);
  const W=520,H=300,mL=44,mR=14,mT=16,mB=44;const iw=W-mL-mR,ih=H-mT-mB;
  const vals=labels.flatMap(l=>[lt.str_base_managed[l].total_return_pct,lt.long_term_rental[l].total_return_pct]);
  const max=Math.max(...vals)*1.16;const y=v=>mT+ih-ih*(v/max);
  const gx=i=>mL+iw*(i+0.5)/labels.length;const gw=iw/labels.length;const bw=gw*0.3;
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,role:'img'});
  for(let t=0;t<=max;t+=2){svg.appendChild(el('line',{class:'gl',x1:mL,x2:W-mR,y1:y(t),y2:y(t)}));
    svg.appendChild(el('text',{class:'axis',x:mL-6,y:y(t)+4,'text-anchor':'end'},t+'%'));}
  svg.appendChild(el('line',{class:'baseline',x1:mL,x2:W-mR,y1:y(0),y2:y(0)}));
  labels.forEach((l,i)=>{const s=lt.str_base_managed[l].total_return_pct,ll=lt.long_term_rental[l].total_return_pct;
    const pairs=[[s,'var(--mid)','STR',-1],[ll,'var(--ltr)','LTR',1]];
    pairs.forEach(([v,col,nm,off])=>{const bx=gx(i)+off*bw/2-bw/2+off*1;
      const r=el('rect',{x:bx,y:y(v),width:bw,height:y(0)-y(v),rx:4,fill:col});
      hoverable(r,`<b>${nm} · ${l}</b><br>Total return ${v}%`);svg.appendChild(r);
      svg.appendChild(el('text',{class:'lbl-s',x:bx+bw/2,y:y(v)-5,'text-anchor':'middle','font-size':10},v+'%'));});
    svg.appendChild(el('text',{class:'lbl-s',x:gx(i),y:H-16,'text-anchor':'middle'},l));});
  document.getElementById('chart-total').appendChild(svg);
})();

/* ---- tax notes ---- */
(()=>{const n=[
  'Both STR and long-term rental income are taxed at your <b>marginal rate</b> (~39% assumed). STR earns more gross but also carries more deductible cost and depreciation.',
  'You already own the property, so you are <b>grandfathered for negative gearing</b> — under leverage the rental loss offsets your other income (the refund shown).',
  'Depreciation is largely the <b>new $30k furnishings</b> (claimable because bought new); the ~1970s building likely predates the 1987 capital-works rule, so little building depreciation.',
  'On sale, a <b>50% CGT discount</b> applies if held &gt;12 months. If this was ever your home, income use can affect the main-residence exemption — get advice.',
  'Residential letting (short or long) is <b>input-taxed for GST</b> — no GST on rent, no credits. Watch the ATO holiday-home <b>“main use” test</b> if personal use is high.',
];
  document.getElementById('tax-notes').innerHTML=n.map(x=>`<li style="margin:6px 0">${x}</li>`).join('');
})();

/* ---- 10-year projection ---- */
(()=>{const pj=DATA.projection;const s=pj.series,sum=pj.summary_year10;
  // stat row
  const stats=[
    ['Property value, yr 10','$'+(sum.property_value/1e6).toFixed(2)+'M','+'+AUD(sum.capital_gain_10yr)+' gain (all)',''],
    ['10-yr cash — self-managed',AUD(sum.cumulative_cash.str_self),'cumulative after-tax','up'],
    ['10-yr cash — managed',AUD(sum.cumulative_cash.str_managed),'cumulative after-tax','mid'],
    ['10-yr cash — long-term',AUD(sum.cumulative_cash.ltr),'cumulative after-tax','ltrc'],
    ['Wealth vs LTR — self',(sum.str_self_vs_ltr_wealth>=0?'+':'')+AUD(sum.str_self_vs_ltr_wealth),'10-yr total','up'],
    ['Wealth vs LTR — managed',AUD(sum.str_managed_vs_ltr_wealth),'10-yr total','down'],
  ];
  document.getElementById('proj-stats').innerHTML=stats.map(x=>
    `<div class="stat"><div class="k">${x[0]}</div><div class="v ${x[3]==='up'?'up':x[3]==='down'?'down':''}">${x[1]}</div><div class="s">${x[2]}</div></div>`).join('');
  document.getElementById('proj-note').innerHTML=`Assumptions: income +${PC(pj.assumptions.income_growth,0)}/yr, costs +${PC(pj.assumptions.cost_inflation,0)}/yr, capital growth ${PC(pj.assumptions.capital_growth,1)}/yr, levy 5%→7.5% in 2027, all-cash after-tax. Over 10 years, self-managed STR builds ~${AUD(sum.str_self_vs_ltr_wealth)} more wealth than long-term rent; managed STR builds ~${AUD(-sum.str_managed_vs_ltr_wealth)} less — while the ${AUD(sum.capital_gain_10yr)} capital gain is common to all three.`;

  // Chart A: cumulative after-tax cash lines
  const lines=[['str_self','var(--up)'],['str_managed','var(--mid)'],['ltr','var(--ltr)']];
  const W=520,H=320,mL=52,mR=16,mT=16,mB=40;const iw=W-mL-mR,ih=H-mT-mB;
  const yrs=s.ltr.map(d=>d.year);const n=yrs.length;
  const max=Math.max(...lines.map(([k])=>s[k][n-1].cumulative_cash))*1.08;
  const x=i=>mL+iw*i/(n-1);const y=v=>mT+ih-ih*(v/max);
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,role:'img'});
  for(let t=0;t<=max;t+=50000){svg.appendChild(el('line',{class:'gl',x1:mL,x2:W-mR,y1:y(t),y2:y(t)}));
    svg.appendChild(el('text',{class:'axis',x:mL-7,y:y(t)+4,'text-anchor':'end'},K(t)));}
  svg.appendChild(el('line',{class:'baseline',x1:mL,x2:W-mR,y1:y(0),y2:y(0)}));
  [0,Math.floor((n-1)/2),n-1].forEach(i=>svg.appendChild(el('text',{class:'axis',x:x(i),y:H-14,'text-anchor':'middle'},yrs[i])));
  lines.forEach(([k,col])=>{const pts=s[k].map((d,i)=>`${x(i)},${y(d.cumulative_cash)}`).join(' ');
    svg.appendChild(el('polyline',{points:pts,fill:'none',stroke:col,'stroke-width':2.4,'stroke-linejoin':'round'}));
    s[k].forEach((d,i)=>{const c=el('circle',{cx:x(i),cy:y(d.cumulative_cash),r:8,fill:'transparent'});
      hoverable(c,`<b>${d.year} · ${k==='str_self'?'STR self-managed':k==='str_managed'?'STR managed':'Long-term'}</b><br>Year cash ${AUD(d.after_tax_cash)}<br>Cumulative <b>${AUD(d.cumulative_cash)}</b>`);
      svg.appendChild(c);});
    const last=s[k][n-1];svg.appendChild(el('circle',{cx:x(n-1),cy:y(last.cumulative_cash),r:3.5,fill:col}));});
  document.getElementById('chart-cash').appendChild(svg);

  // Chart B: year-10 total wealth stacked (capital gain common + cumulative cash - capex)
  const value0=1000000;const capGain=sum.capital_gain_10yr;
  const items=[['Self-managed','str_self','var(--up)'],['Managed','str_managed','var(--mid)'],['Long-term','ltr','var(--ltr)']];
  const W2=520,H2=320,mL2=54,mR2=14,mT2=16,mB2=40;const iw2=W2-mL2-mR2,ih2=H2-mT2-mB2;
  const wmax=Math.max(...items.map(([_,k])=>sum.total_wealth[k]))*1.05;
  const cx=i=>mL2+iw2*(i+0.5)/items.length;const bw=iw2/items.length*0.5;const y2=v=>mT2+ih2-ih2*(v/wmax);
  const svg2=el('svg',{viewBox:`0 0 ${W2} ${H2}`,role:'img'});
  for(let t=0;t<=wmax;t+=400000){svg2.appendChild(el('line',{class:'gl',x1:mL2,x2:W2-mR2,y1:y2(t),y2:y2(t)}));
    svg2.appendChild(el('text',{class:'axis',x:mL2-7,y:y2(t)+4,'text-anchor':'end'},'$'+(t/1e6).toFixed(1)+'M'));}
  svg2.appendChild(el('line',{class:'baseline',x1:mL2,x2:W2-mR2,y1:y2(0),y2:y2(0)}));
  const common=value0;  // starting value slab (common)
  items.forEach((it,i)=>{const[nm,k,col]=it;const tot=sum.total_wealth[k];
    // slab 1: starting value (grey, common)
    const s1=el('rect',{x:cx(i)-bw/2,y:y2(common),width:bw,height:y2(0)-y2(common),rx:3,fill:'var(--line-strong)'});
    hoverable(s1,`<b>Starting value</b><br>${AUD(common)} (common to all)`);svg2.appendChild(s1);
    // slab 2: everything above starting value (the differentiator: capital gain + cumulative cash - capex)
    const s2=el('rect',{x:cx(i)-bw/2,y:y2(tot),width:bw,height:y2(common)-y2(tot),rx:3,fill:col});
    hoverable(s2,`<b>${nm}</b><br>Total wealth <b>${AUD(tot)}</b><br>Capital gain ${AUD(capGain)} (common)<br>+ cumulative cash − setup`);
    svg2.appendChild(s2);
    svg2.appendChild(el('text',{class:'lbl',x:cx(i),y:y2(tot)-8,'text-anchor':'middle','font-size':11},AUD(tot)));
    svg2.appendChild(el('text',{class:'lbl-s',x:cx(i),y:H2-14,'text-anchor':'middle'},nm));});
  document.getElementById('chart-wealth').appendChild(svg2);
})();

/* ---- market table ---- */
(()=>{const m=DATA.markets;
  const order=[['higgins','Higgins (suburb)'],['belconnen','District of Belconnen'],['north_canberra','North Canberra'],['canberra','Canberra (city)']];
  let h='<thead><tr><th>Market</th><th>Occupancy</th><th>ADR</th><th>RevPAR</th><th>Avg annual rev</th><th>Listings</th></tr></thead><tbody>';
  order.forEach(o=>{const d=m[o[0]];const hi=o[0]==='belconnen'?' class="hi"':'';
    h+=`<tr${hi}><td>${o[1]}</td><td>${PC(d.occ)}</td><td>${AUD(d.adr)}</td><td>${AUD(d.revpar)}</td><td>${AUD(d.revenue)}</td><td>${d.listings}</td></tr>`;});
  h+='</tbody>';document.getElementById('market-table').innerHTML=h;
})();

/* ---- risks ---- */
(()=>{const risks=[
  ['warn','ACT levy rising','var(--warn)','The short-term rental levy is 5% today but is legislated to jump to <b>7.5% on 1 July 2027</b> — modelled in the spreadsheet. It shaves roughly $1,500/yr off the base case at that point.'],
  ['crit','Huge performance dispersion','var(--crit)','Comparable 4-bed revenue ranges from ~$18k to ~$126k. The median-to-upside gap is almost entirely <b>management & pricing quality</b>. Weak execution lands you well below long-term rent.'],
  ['warn','Low absolute yield','var(--warn)','Even the aggressive case is a <b>4.5% net yield</b> on a $1M asset. Canberra is a capital-growth, low-yield market — short-term rental improves cash yield only modestly and only if run well.'],
  ['good','Regulation is light — for now','var(--good)','The ACT has <b>no mandatory STR registration cap</b> currently, and demand is barely seasonal (steady government/business travel). But the regime is under review — factor in tightening risk.'],
  ['warn','Operating intensity','var(--warn)','Short-term letting means guest turnover, cleaning logistics, reviews, and ~18% management fees (or your time). The base case barely out-earns a hands-off long-term tenant after the $30k fit-out.'],
  ['good','Break-even is achievable','var(--good)','Break-even vs long-term rent is ~<b>51% occupancy</b> at $346/night — below what well-run local 4-beds already achieve (58–71%). The upside is attainable with professional management.'],
];
  document.getElementById('risks').innerHTML=risks.map(r=>
    `<div class="risk"><div class="h"><span class="i" style="background:${r[2]}">${r[0]==='good'?'✓':r[0]==='crit'?'!':'i'}</span>${r[1]}</div><p>${r[3]}</p></div>`).join('');
})();

/* ---- assumptions ---- */
(()=>{const a=[
  'Property value $1,000,000; all-cash basis (no mortgage supplied — cash-on-cash equals net yield).',
  'STR scenarios = AirROI revenue percentiles for this 4bd/2ba property: p25 $38.0k · median $62.0k · p75 $86.9k.',
  'Management 18% of revenue, platform 3%, plus utilities $6.0k, insurance $2.4k, consumables $2.4k, maintenance $3.5k, council rates $3.8k, supplies $0.8k.',
  'Furnishing & setup $30,000, amortised over 5 years (shown separately from NOI).',
  'Long-term rent $750/week, 2 weeks vacancy, 7% management, $1.5k maintenance, rates & insurance as above.',
  'ACT STR levy 5% (current). A separate 7.5% (2027) view is in the spreadsheet model.',
];
  document.getElementById('assump').innerHTML=a.map(x=>`<li>${x}</li>`).join('');
})();
</script>'''

HTML = HTML.replace('__DATA__', DATA_JS)
open('deliverables/report.html','w').write(HTML)
print('report.html bytes:', len(HTML))
