const API_URL = 'http://127.0.0.1:5001/api';
let cart = [];
let products = [];

function showToast(message, type='default', timeout=3000){
    const container = document.getElementById('toastContainer');
    if(!container) return;
    const t = document.createElement('div');
    t.className = `toast ${type==='error'?'error': type==='success'?'success':''}`;
    t.textContent = message;
    container.appendChild(t);
    setTimeout(()=> t.remove(), timeout);
}

function fetchProducts(){
    return fetch(`${API_URL}/products`).then(r=>r.json()).then(data=>{ products = data; renderProductPanel(); return data; });
}

function renderProductPanel(){
    const panel = document.getElementById('productPanel');
    if(!panel) return;
    panel.innerHTML = '';
    products.forEach(p => {
        const card = document.createElement('div');
        card.className = 'product-card';
        card.innerHTML = `
            <div class="product-thumb">${p.name.charAt(0).toUpperCase()}</div>
            <div class="product-meta">
                <div>
                    <div class="product-name">${p.name}</div>
                    <div class="muted">$${p.price.toFixed(2)}</div>
                </div>
                <div style="text-align:right">
                    <div class="stock-badge">庫存 ${p.stock}</div>
                    <div style="margin-top:8px"><button class="action-btn" onclick="addToCart(${p.id})">加入</button></div>
                </div>
            </div>
        `;
        panel.appendChild(card);
    });
}

function updateSearchSuggestions(query){
    const box = document.getElementById('searchSuggestions');
    box.innerHTML = '';
    if(!query) return;
    const matches = products.filter(p => p.name.toLowerCase().includes(query.toLowerCase())).slice(0,8);
    matches.forEach(m =>{
        const d = document.createElement('div');
        d.style.padding='8px';d.style.cursor='pointer';d.className='muted';
        d.textContent = `${m.name} — $${m.price}`;
        d.onclick = ()=>{ addToCart(m.id); document.getElementById('productSearch').value=''; box.innerHTML=''; };
        box.appendChild(d);
    });
}

function addToCart(productId, qty=1){
    const p = products.find(x=>x.id===productId);
    if(!p){ showToast('找不到產品','error'); return; }
    if(p.stock <=0){ showToast('庫存不足','error'); return; }
    const existing = cart.find(i=>i.product_id===productId);
    if(existing){ existing.quantity += qty; }
    else{ cart.push({ product_id:p.id, name:p.name, price:p.price, quantity: qty }); }
    renderCart();
    showToast(`${p.name} 已加入購物車`, 'success');
}

function renderCart(){
    const container = document.getElementById('cartItems');
    container.innerHTML = '';
    let total = 0; let count = 0;
    cart.forEach((item, idx)=>{
        const row = document.createElement('div');
        row.style.display='flex';row.style.justifyContent='space-between';row.style.alignItems='center';row.style.padding='8px 0';
        row.innerHTML = `
            <div style="flex:1">
                <div style="font-weight:600">${item.name}</div>
                <div class="muted">$${item.price.toFixed(2)}</div>
            </div>
            <div style="display:flex;gap:6px;align-items:center">
                <button class="btn ghost" onclick="changeQuantity(${idx}, ${Math.max(1,item.quantity-1)})">-</button>
                <input type="number" min="1" value="${item.quantity}" onchange="changeQuantity(${idx}, this.value)" style="width:56px;padding:6px;border-radius:6px;border:1px solid #e6edf7">
                <button class="btn ghost" onclick="changeQuantity(${idx}, ${item.quantity+1})">+</button>
                <div style="width:80px;text-align:right">$${(item.price*item.quantity).toFixed(2)}</div>
                <button class="btn" style="margin-left:8px" onclick="removeFromCart(${idx})">移除</button>
            </div>
        `;
        container.appendChild(row);
        total += item.price*item.quantity; count += item.quantity;
    });
    document.getElementById('totalDisplay').textContent = `總金額：${total.toFixed(2)}`;
    document.getElementById('cartCount').textContent = `${count} 件`;
}

function changeQuantity(idx, value){
    const v = Math.max(1, parseInt(value));
    cart[idx].quantity = v;
    renderCart();
}

function removeFromCart(idx){
    cart.splice(idx,1);
    renderCart();
}

function clearCart(){ cart = []; renderCart(); }

function openCheckout(){
    if(cart.length===0){ showToast('購物車為空','error'); return; }
    const summary = document.getElementById('checkoutSummary');
    let html = '<ul style="padding-left:18px">';
    let total = 0;
    cart.forEach(i=>{ html += `<li>${i.name} x ${i.quantity} — $${(i.quantity*i.price).toFixed(2)}</li>`; total += i.quantity*i.price; });
    html += `</ul><div style="font-weight:700;margin-top:8px">應付：$${total.toFixed(2)}</div>`;
    summary.innerHTML = html;
    document.getElementById('checkoutModal').style.display='flex';
}

function confirmCheckout(){
    const payload = cart.map(i=>({ product_id:i.product_id, quantity:i.quantity }));
    fetch(`${API_URL}/checkout`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) })
    .then(res=>res.json().then(data=>({status:res.status,data})))
    .then(({status,data})=>{
        if(status===201){ showToast('結帳成功','success'); cart=[]; renderCart(); fetchProducts(); }
        else{ showToast(data.error||'結帳失敗','error'); }
        document.getElementById('checkoutModal').style.display='none';
    })
    .catch(err=>{ showToast('伺服器錯誤','error'); document.getElementById('checkoutModal').style.display='none'; });
}

// keyboard shortcuts
document.addEventListener('keydown', (e)=>{
    if(e.key === '/') { e.preventDefault(); document.getElementById('productSearch').focus(); }
    if(e.key === 'Enter' && document.activeElement.id === 'productSearch'){
        const q = document.getElementById('productSearch').value.trim();
        if(!q) return;
        // find best match
        const p = products.find(x=>x.name.toLowerCase()===q.toLowerCase()) || products.find(x=>x.name.toLowerCase().includes(q.toLowerCase()));
        if(p) addToCart(p.id,1);
    }
});

document.addEventListener('DOMContentLoaded', ()=>{
    fetchProducts();
    document.getElementById('productSearch').addEventListener('input', (e)=> updateSearchSuggestions(e.target.value));
    document.getElementById('openAllBtn').addEventListener('click', ()=> renderProductPanel());
    document.getElementById('checkoutBtn').addEventListener('click', openCheckout);
    document.getElementById('clearCartBtn').addEventListener('click', clearCart);
    document.getElementById('closeCheckout').addEventListener('click', ()=> document.getElementById('checkoutModal').style.display='none');
    document.getElementById('cancelCheckout').addEventListener('click', ()=> document.getElementById('checkoutModal').style.display='none');
    document.getElementById('confirmCheckout').addEventListener('click', confirmCheckout);
});
