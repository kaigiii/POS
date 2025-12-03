const API_URL = (window.__API_URL__ || 'http://127.0.0.1:5001') + '/api';

// state
let txCache = [];
let currentPage = 1;
let perPage = 10;
let lastQuery = '';

function showToast(message, type='default', timeout=3000){
    const container = document.getElementById('toastContainer');
    if(!container) return;
    const t = document.createElement('div');
    t.className = `toast ${type==='error'?'error': type==='success'?'success':''}`;
    t.textContent = message;
    container.appendChild(t);
    setTimeout(()=> t.remove(), timeout);
}

async function fetchTransactions() {
    // fetch all transactions (for simplicity) and cache client-side
    try{
        const res = await fetch(`${API_URL}/transactions`);
        const data = await res.json();
        txCache = data.map(t => ({...t}));
        renderStats();
        renderList();
    }catch(e){
        showToast('無法載入交易資料','error');
    }
}

function applyFilters(){
    currentPage = 1;
    perPage = parseInt(document.getElementById('perPage').value,10)||10;
    lastQuery = document.getElementById('qInput').value.trim();
    renderList();
}

function clearFilters(){
    document.getElementById('qInput').value = '';
    document.getElementById('fromDate').value = '';
    document.getElementById('toDate').value = '';
    document.getElementById('perPage').value = '10';
    applyFilters();
}

function filterTxs(){
    const q = (document.getElementById('qInput').value||'').trim().toLowerCase();
    const from = document.getElementById('fromDate').value;
    const to = document.getElementById('toDate').value;
    let list = txCache.slice();
    if(q){
        list = list.filter(t=> (String(t.id).includes(q) || String(t.timestamp).toLowerCase().includes(q)) );
    }
    if(from){ list = list.filter(t => t.timestamp >= from); }
    if(to){ list = list.filter(t => t.timestamp <= to + ' 23:59:59'); }
    return list;
}

function renderStats(){
    const total = txCache.length;
    const revenue = txCache.reduce((s,t)=> s + (t.total_amount||0),0).toFixed(2);
    const last = txCache[0]? txCache[0].timestamp : '-';
    document.getElementById('statTotalTx').textContent = total;
    document.getElementById('statTotalRevenue').textContent = `$${revenue}`;
    document.getElementById('statLastTx').textContent = last;
}

function renderList(){
    const list = filterTxs();
    const txListEl = document.getElementById('txList');
    txListEl.innerHTML = '';
    const totalPages = Math.max(1, Math.ceil(list.length / perPage));
    currentPage = Math.min(currentPage, totalPages);
    const start = (currentPage-1)*perPage;
    const pageItems = list.slice(start, start+perPage);
    pageItems.forEach(t => {
        const el = document.createElement('div');
        el.className = 'transaction-item';
        const meta = document.createElement('div'); meta.className='meta';
        meta.innerHTML = `<div class="id">#${t.id}</div><div class="muted">${t.timestamp}</div>`;
        const right = document.createElement('div'); right.className='transaction-actions';
        right.innerHTML = `<div class="amount">$${(t.total_amount||0).toFixed(2)}</div><button class="btn" onclick="showTransactionDetail(${t.id})">查看</button>`;
        el.appendChild(meta); el.appendChild(right);
        txListEl.appendChild(el);
    });
    renderPagination(list.length, totalPages);
}

function renderPagination(totalItems, totalPages){
    const p = document.getElementById('pagination');
    p.innerHTML = '';
    const prev = document.createElement('button'); prev.textContent='‹ 上一頁'; prev.disabled = currentPage<=1; prev.onclick = ()=>{ currentPage--; renderList(); };
    const next = document.createElement('button'); next.textContent='下一頁 ›'; next.disabled = currentPage>=totalPages; next.onclick = ()=>{ currentPage++; renderList(); };
    p.appendChild(prev);
    const info = document.createElement('div'); info.textContent = `第 ${currentPage} / ${totalPages} 頁 (${totalItems} 筆)`; p.appendChild(info);
    p.appendChild(next);
}

async function showTransactionDetail(id){
    try{
        const res = await fetch(`${API_URL}/transactions/${id}`);
        const tx = await res.json();
        if(tx.error){ showToast(tx.error,'error'); return; }
        const modal = document.getElementById('txModal');
        const content = document.getElementById('modalContent');
        let html = `<h2>交易 #${tx.id}</h2><p class="muted">時間：${tx.timestamp}</p><p class="muted">總金額：$${(tx.total_amount||0).toFixed(2)}</p>`;
        html += '<table style="width:100%;border-collapse:collapse"><thead><tr><th style="text-align:left;padding:8px">產品ID</th><th style="text-align:left;padding:8px">數量</th><th style="text-align:left;padding:8px">單價</th></tr></thead><tbody>';
        tx.items.forEach(i=>{ html += `<tr><td style="padding:8px">${i.product_id}</td><td style="padding:8px">${i.quantity}</td><td style="padding:8px">${i.price_at_sale}</td></tr>`; });
        html += '</tbody></table>';
        html += `<div style="margin-top:12px;display:flex;gap:8px"><button id="downloadReceipt" class="btn">下載收據 (CSV)</button><button class="btn ghost" onclick="document.getElementById('txModal').style.display='none'">關閉</button></div>`;
        content.innerHTML = html;
        modal.style.display='flex';
        document.getElementById('downloadReceipt').addEventListener('click', ()=> downloadTxCSV(tx));
    }catch(e){ showToast('無法取得交易明細','error'); }
}

function downloadTxCSV(tx){
    let csv = 'product_id,quantity,price_at_sale\n';
    tx.items.forEach(i=> csv += `${i.product_id},${i.quantity},${i.price_at_sale}\n`);
    const blob = new Blob([csv], {type:'text/csv'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = `transaction_${tx.id}.csv`; a.click(); URL.revokeObjectURL(url);
}

function exportFilteredCSV(){
    const list = filterTxs();
    let csv = 'transaction_id,timestamp,total_amount\n';
    list.forEach(t=> csv += `${t.id},"${t.timestamp}",${t.total_amount}\n`);
    const blob = new Blob([csv], {type:'text/csv'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = `transactions_export.csv`; a.click(); URL.revokeObjectURL(url);
}

document.addEventListener('DOMContentLoaded', ()=>{
    fetchTransactions();
    document.getElementById('applyFilters').addEventListener('click', applyFilters);
    document.getElementById('clearFilters').addEventListener('click', clearFilters);
    document.getElementById('exportCsv').addEventListener('click', exportFilteredCSV);
    const close = document.getElementById('closeModal');
    const modal = document.getElementById('txModal');
    if (close) close.addEventListener('click', () => modal.style.display = 'none');
    if (modal) modal.addEventListener('click', (e) => { if (e.target === modal) modal.style.display = 'none'; });
});
