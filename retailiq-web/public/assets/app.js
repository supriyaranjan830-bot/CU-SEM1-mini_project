const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const CATEGORY_COLORS = ['#69aaff','#b79aff','#38d6b0','#f3c96a','#ff9d72'];
const CATEGORY_MAP = new Map(['Electronics','Clothing','Food','Home & Garden','Sports'].map((c,i)=>[c,CATEGORY_COLORS[i]]));
const charts = {};
const filters = {
  year: document.getElementById('yearFilter'),
  category: document.getElementById('categoryFilter'),
  region: document.getElementById('regionFilter'),
  store: document.getElementById('storeFilter'),
  start: document.getElementById('startMonth'),
  end: document.getElementById('endMonth')
};
let toastTimer;

function money(value, compact=false) {
  const n = Number(value || 0);
  if (compact) {
    if (Math.abs(n) >= 10000000) return `₹${(n/10000000).toFixed(2)}Cr`;
    if (Math.abs(n) >= 100000) return `₹${(n/100000).toFixed(2)}L`;
    if (Math.abs(n) >= 1000) return `₹${(n/1000).toFixed(1)}K`;
  }
  return new Intl.NumberFormat('en-IN',{style:'currency',currency:'INR',maximumFractionDigits:0}).format(n);
}
function number(value) { return new Intl.NumberFormat('en-IN').format(Number(value || 0)); }
function pct(value) { return `${Number(value || 0).toFixed(1)}%`; }
function monthName(month) { return MONTHS[Number(month)-1] || '—'; }
function showToast(message) {
  const el = document.getElementById('toast');
  el.textContent = message;
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(()=>el.classList.remove('show'),2600);
}
function setStatus(message) { document.getElementById('statusText').textContent = message; }
function currentParams() {
  const p = new URLSearchParams({
    year: filters.year.value,
    category: filters.category.value,
    region: filters.region.value,
    store: filters.store.value,
    start_month: filters.start.value,
    end_month: filters.end.value
  });
  return p;
}
function makeMonthOptions() {
  MONTHS.forEach((name,index)=>{
    const optionStart = new Option(name,index+1);
    const optionEnd = new Option(name,index+1);
    filters.start.add(optionStart);
    filters.end.add(optionEnd);
  });
  filters.start.value = '1';
  filters.end.value = '12';
}
async function initializeFilters() {
  makeMonthOptions();
  try {
    const response = await fetch('/api/filters');
    if (!response.ok) throw new Error('Could not load filter options');
    const data = await response.json();
    data.categories.forEach(x=>filters.category.add(new Option(x,x)));
    data.regions.forEach(x=>filters.region.add(new Option(x,x)));
    data.stores.forEach(x=>filters.store.add(new Option(x,x)));
  } catch (error) {
    console.error(error);
    showToast('Could not load filter options.');
  }
}

async function loadDashboard() {
  const main = document.querySelector('.main-content');
  main.classList.add('loading');
  setStatus('Running Python analytics…');
  try {
    const response = await fetch(`/api/dashboard?${currentParams().toString()}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'The dashboard request failed.');
    if (data.empty) {
      renderEmptyState(data.message);
      return;
    }
    renderDashboard(data);
    const start = monthName(filters.start.value);
    const end = monthName(filters.end.value);
    setStatus(`${number(data.record_count)} transactions analyzed · ${start}–${end} ${data.year}`);
  } catch (error) {
    console.error(error);
    setStatus('Unable to load analytics');
    showToast(error.message || 'Something went wrong.');
  } finally {
    main.classList.remove('loading');
  }
}
function renderEmptyState(message) {
  document.getElementById('statusText').textContent = message;
  document.getElementById('productsTable').innerHTML = `<tr><td colspan="8" class="table-empty">${escapeHtml(message)}</td></tr>`;
  document.getElementById('heatmap').innerHTML = '';
  document.getElementById('categoryLegend').innerHTML = '';
  document.getElementById('marginRanking').innerHTML = '';
  document.getElementById('alertsList').innerHTML = `<div class="empty-alert">${escapeHtml(message)}</div>`;
  Object.values(charts).forEach(chart=>chart.destroy());
  Object.keys(charts).forEach(k=>delete charts[k]);
}
function renderDashboard(data) {
  renderKpis(data.kpis);
  renderTrend(data.monthly);
  renderCategories(data.categories);
  renderStores(data.stores);
  renderScatter(data.scatter);
  renderHeatmap(data.heatmap);
  renderInsights(data.insights);
  renderProducts(data.products);
}
function renderKpis(k) {
  const values = [
    [money(k.revenue,true),'Across selected transactions'],
    [number(k.orders),'Transaction count'],
    [money(k.aov,true),'Revenue divided by orders'],
    [money(k.profit,true),'Revenue less estimated cost'],
    [pct(k.margin),'Profit as a share of revenue']
  ];
  document.querySelectorAll('.kpi-card').forEach((card,i)=>{
    card.querySelector('.kpi-value').textContent = values[i][0];
    card.querySelector('.kpi-value').classList.remove('skeleton');
    card.querySelector('.kpi-foot').textContent = values[i][1];
  });
}
function chartBaseOptions() {
  return {
    responsive:true, maintainAspectRatio:false,
    interaction:{mode:'index',intersect:false},
    plugins:{legend:{display:false},tooltip:{backgroundColor:'#0d151e',borderColor:'#344653',borderWidth:1,titleColor:'#e9f0f4',bodyColor:'#afbdc7',padding:10,displayColors:true}},
    scales:{
      x:{grid:{display:false},ticks:{color:'#788b99',font:{family:'DM Sans',size:9}},border:{display:false}},
      y:{grid:{color:'#24313d'},ticks:{color:'#788b99',font:{family:'DM Sans',size:9},callback:v=>money(v,true)},border:{display:false}}
    }
  };
}
function replaceChart(key, canvasId, config) {
  if (charts[key]) charts[key].destroy();
  const canvas = document.getElementById(canvasId);
  charts[key] = new Chart(canvas,config);
}
function renderTrend(rows) {
  const opts = chartBaseOptions();
  opts.plugins.tooltip.callbacks = {label:ctx=>`${ctx.dataset.label}: ${money(ctx.parsed.y)}`};
  replaceChart('trend','trendChart',{
    type:'line',data:{labels:rows.map(x=>x.label),datasets:[
      {label:'Revenue',data:rows.map(x=>x.revenue),borderColor:'#38d6b0',backgroundColor:'rgba(56,214,176,.10)',fill:true,tension:.35,borderWidth:2.4,pointRadius:3,pointHoverRadius:5,pointBackgroundColor:'#38d6b0'},
      {label:'Profit',data:rows.map(x=>x.profit),borderColor:'#69aaff',backgroundColor:'transparent',tension:.35,borderWidth:1.8,borderDash:[5,4],pointRadius:2,pointHoverRadius:4,pointBackgroundColor:'#69aaff'}
    ]},options:opts
  });
}
function renderCategories(rows) {
  const sorted = [...rows].sort((a,b)=>b.revenue-a.revenue);
  replaceChart('category','categoryChart',{
    type:'doughnut',data:{labels:sorted.map(x=>x.category),datasets:[{data:sorted.map(x=>x.revenue),backgroundColor:sorted.map(x=>CATEGORY_MAP.get(x.category)||'#8394a2'),borderColor:'#151e29',borderWidth:4,hoverOffset:5}]},
    options:{responsive:true,maintainAspectRatio:false,cutout:'70%',plugins:{legend:{display:false},tooltip:{backgroundColor:'#0d151e',borderColor:'#344653',borderWidth:1,titleColor:'#e9f0f4',bodyColor:'#afbdc7',padding:10,callbacks:{label:ctx=>`${ctx.label}: ${money(ctx.raw)} (${pct(ctx.raw/Math.max(1,rows.reduce((s,x)=>s+x.revenue,0))*100)})`}}}}
  });
  document.getElementById('categoryLegend').innerHTML = sorted.map(x=>`<div class="cat-legend-row"><i style="background:${CATEGORY_MAP.get(x.category)}"></i><span>${escapeHtml(x.category)}</span><b>${pct(x.share)}</b></div>`).join('');
}
function renderStores(rows) {
  const sorted = [...rows].sort((a,b)=>a.revenue-b.revenue);
  const opts = chartBaseOptions();
  opts.indexAxis = 'y';
  opts.interaction = {mode:'nearest',intersect:true};
  opts.scales.x.ticks.callback = v=>money(v,true);
  opts.scales.y.ticks.font = {family:'DM Sans',size:8};
  opts.plugins.tooltip.callbacks = {label:ctx=>`Revenue: ${money(ctx.parsed.x)}`};
  replaceChart('stores','storeChart',{
    type:'bar',data:{labels:sorted.map(x=>x.store),datasets:[{label:'Revenue',data:sorted.map(x=>x.revenue),backgroundColor:sorted.map((x,i)=>i===sorted.length-1?'#38d6b0':'#367f78'),borderRadius:4,barThickness:12}]},options:opts
  });
}
function renderScatter(rows) {
  const groups = ['Electronics','Clothing','Food','Home & Garden','Sports'];
  const datasets = groups.map(cat=>{
    const points = rows.filter(x=>x.category===cat);
    const maxRev = Math.max(1,...points.map(x=>x.revenue));
    return {label:cat,data:points.map(x=>({x:x.avg_price,y:x.units,r:5+Math.sqrt(x.revenue/maxRev)*8,product:x.product,revenue:x.revenue})),backgroundColor:(CATEGORY_MAP.get(cat)||'#fff')+'bb',borderColor:CATEGORY_MAP.get(cat),borderWidth:1};
  });
  const opts = chartBaseOptions();
  opts.plugins.legend={display:true,position:'bottom',labels:{color:'#91a1ad',boxWidth:7,boxHeight:7,usePointStyle:true,pointStyle:'circle',padding:12,font:{family:'DM Sans',size:8}}};
  opts.plugins.tooltip.callbacks={label:ctx=>`${ctx.raw.product}: ${money(ctx.raw.x)} avg price · ${number(ctx.raw.y)} units`};
  opts.scales.x.title={display:true,text:'Average unit price (₹)',color:'#82939f',font:{size:8}};
  opts.scales.y.title={display:true,text:'Units sold',color:'#82939f',font:{size:8}};
  opts.scales.x.ticks.callback=v=>money(v,true);
  opts.scales.y.ticks.callback=v=>number(v);
  replaceChart('scatter','scatterChart',{type:'bubble',data:{datasets},options:opts});
}
function renderHeatmap(data) {
  const flat = data.values.flat();
  const max = Math.max(1,...flat);
  let html = '<div class="heat-cell hour-label"></div>';
  html += data.hours.map(h=>`<div class="heat-cell hour-label">${h%3===0?String(h).padStart(2,'0'):''}</div>`).join('');
  data.days.forEach((day,di)=>{
    html += `<div class="heat-cell day-label">${day.slice(0,3)}</div>`;
    data.hours.forEach((hour,hi)=>{
      const value = data.values[di][hi];
      const intensity = value===0?0.03:0.12+0.82*Math.sqrt(value/max);
      const title = `${day}, ${String(hour).padStart(2,'0')}:00 · ${money(value)}`;
      html += `<div class="heat-cell" title="${escapeHtml(title)}" style="background:rgba(56,214,176,${intensity.toFixed(3)})"></div>`;
    });
  });
  document.getElementById('heatmap').innerHTML = html;
}
function renderInsights(i) {
  const cards = [
    {label:'BEST PERFORMING MONTH',value:i.best_month.label,detail:`${money(i.best_month.revenue,true)} in revenue`,icon:'↗'},
    {label:'Q4 VS Q1 REVENUE',value:`${i.q4_growth>=0?'+':''}${pct(i.q4_growth)}`,detail:'October–December vs January–March',icon:'◌'},
    {label:'ANNUAL PROJECTION',value:money(i.projected_annual_revenue,true),detail:'Scenario using a fixed 12% uplift',icon:'◎'},
    {label:'WEEKEND REVENUE SHARE',value:pct(i.weekend_revenue_share),detail:'Saturday and Sunday combined',icon:'⌁'}
  ];
  document.getElementById('insightGrid').innerHTML=cards.map((x,index)=>`<article class="insight-card ${index===0?'insight-accent':''}"><span class="insight-icon">${x.icon}</span><div class="insight-label">${x.label}</div><strong>${x.value}</strong><p>${x.detail}</p></article>`).join('');
  const maxMargin=Math.max(1,...i.category_margins.map(x=>x.margin));
  document.getElementById('marginRanking').innerHTML=i.category_margins.map((x,index)=>`<div class="ranking-row"><span class="ranking-name">${escapeHtml(x.category)}</span><div class="rank-track"><div class="rank-fill" style="width:${Math.max(2,x.margin/maxMargin*100)}%;opacity:${1-index*.08}"></div></div><span class="ranking-value">${pct(x.margin)}</span></div>`).join('');
  const alerts=[];
  i.store_anomalies.forEach(x=>alerts.push({danger:true,title:`${x.store} below store average`,detail:`${money(x.revenue,true)} revenue · z-score ${x.z_score}`}));
  i.daily_anomalies.forEach(x=>alerts.push({danger:false,title:`${x.direction} on ${x.date}`,detail:`Daily revenue: ${money(x.revenue,true)}`}));
  document.getElementById('alertCount').textContent=alerts.length;
  document.getElementById('alertsList').innerHTML=alerts.length?alerts.slice(0,6).map(x=>`<div class="alert-row"><i class="alert-dot ${x.danger?'danger':''}"></i><div class="alert-copy"><strong>${escapeHtml(x.title)}</strong><small>${escapeHtml(x.detail)}</small></div></div>`).join(''):'<div class="empty-alert">No significant store or daily anomalies detected in this filtered view.</div>';
  const recommendations=[
    `<b>01</b> Increase inventory attention for ${escapeHtml(i.highest_margin_category)}, which has the highest contribution margin.`,
    `<b>02</b> Review pricing and cost structure in ${escapeHtml(i.lowest_margin_category)}, the lowest-margin category.`,
    `<b>03</b> Test ${escapeHtml(i.promotion_day)} promotions; weekends account for ${pct(i.weekend_revenue_share)} of selected revenue.`,
    `<b>04</b> Use the hourly heatmap to schedule staffing and campaigns around observed peak hours.`
  ];
  document.getElementById('recommendations').innerHTML=recommendations.map(x=>`<div class="recommend-item">${x}</div>`).join('');
}
function renderProducts(rows) {
  const tbody=document.getElementById('productsTable');
  tbody.innerHTML=rows.map((x,index)=>{
    const statusClass=x.status==='Hot'?'status-hot':(x.status==='Growing'?'status-growing':'status-stable');
    return `<tr><td class="rank-number">${String(index+1).padStart(2,'0')}</td><td class="product-name">${escapeHtml(x.product)}</td><td><span class="category-pill">${escapeHtml(x.category)}</span></td><td class="numeric">${number(x.units)}</td><td class="numeric">${money(x.revenue)}</td><td class="numeric">${money(x.profit)}</td><td class="numeric margin-cell">${pct(x.margin)}</td><td><span class="status-pill ${statusClass}">${x.status}</span></td></tr>`;
  }).join('');
}
function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
}
function exportReport(kind) {
  const url=`/api/export/${encodeURIComponent(kind)}?${currentParams().toString()}`;
  const a=document.createElement('a');a.href=url;a.download=`retailiq_${kind}.csv`;document.body.appendChild(a);a.click();a.remove();
  showToast(`${kind.charAt(0).toUpperCase()+kind.slice(1)} CSV requested.`);
}

let filterTimer;
function scheduleRefresh(){
  if(Number(filters.start.value)>Number(filters.end.value)){
    filters.end.value=filters.start.value;
  }
  clearTimeout(filterTimer);
  filterTimer=setTimeout(loadDashboard,180);
}
Object.values(filters).forEach(el=>el.addEventListener('change',scheduleRefresh));
document.getElementById('refreshBtn').addEventListener('click',()=>{loadDashboard();showToast('Dashboard refreshed.');});
document.getElementById('resetBtn').addEventListener('click',()=>{
  filters.year.value='2024';filters.category.value='All categories';filters.region.value='All regions';filters.store.value='All stores';filters.start.value='1';filters.end.value='12';loadDashboard();showToast('Filters reset.');
});
document.querySelectorAll('[data-export]').forEach(btn=>btn.addEventListener('click',()=>exportReport(btn.dataset.export)));
document.getElementById('exportAllBtn').addEventListener('click',()=>{
  ['products','monthly','stores'].forEach((kind,index)=>setTimeout(()=>exportReport(kind),index*500));
  showToast('Preparing all three CSV reports.');
});
document.querySelectorAll('.nav-item').forEach(link=>link.addEventListener('click',()=>{
  document.querySelectorAll('.nav-item').forEach(x=>x.classList.remove('active'));
  link.classList.add('active');
}));

(async()=>{await initializeFilters();await loadDashboard();})();
