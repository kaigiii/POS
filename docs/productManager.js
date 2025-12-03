const API_URL = (window.__API_URL__ || 'http://127.0.0.1:5001') + '/api';

function showToast(message, type = 'default', timeout = 3500) {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const t = document.createElement('div');
    t.className = `toast ${type}`;
    t.textContent = message;
    container.appendChild(t);
    setTimeout(() => t.remove(), timeout);
}

function renderStats(products) {
    const total = products.length;
    const stock = products.reduce((s, p) => s + (p.stock || 0), 0);
    const elTotal = document.getElementById('statTotalProducts');
    const elStock = document.getElementById('statTotalStock');
    if (elTotal) elTotal.textContent = total;
    if (elStock) elStock.textContent = stock;
}

function renderProductGrid(products) {
    const grid = document.getElementById('productGrid');
    if (!grid) return;
    grid.innerHTML = '';
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
                    <div style="margin-top:8px;display:flex;gap:8px;justify-content:flex-end">
                        <button class="action-btn" onclick="openEditModal(${p.id})">編輯</button>
                        <button class="action-btn" onclick="deleteProduct(${p.id})">刪除</button>
                    </div>
                </div>
            </div>
        `;
        grid.appendChild(card);
    });
}

function fetchProducts() {
    fetch(`${API_URL}/products`)
        .then(res => res.json())
        .then(products => {
            renderStats(products);
            renderProductGrid(products);
            // keep table for compatibility (hidden by default)
            const tbody = document.getElementById('productTableBody');
            if (tbody) {
                tbody.innerHTML = '';
                products.forEach(product => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${product.id}</td>
                        <td>${product.name}</td>
                        <td>${product.price}</td>
                        <td>${product.cost}</td>
                        <td>${product.stock}</td>
                        <td>
                            <button class="action-btn" onclick="openEditModal(${product.id})">編輯</button>
                            <button class="action-btn" onclick="deleteProduct(${product.id})">刪除</button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
            }
        })
        .catch(err => showToast('載入產品失敗', 'error'));
}

function addProduct(e) {
    e.preventDefault();
    const form = e.target;
    const data = {
        name: form.name.value,
        price: parseFloat(form.price.value),
        cost: parseFloat(form.cost.value),
        stock: parseInt(form.stock.value)
    };
    fetch(`${API_URL}/products`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(res => {
        if (!res.ok) throw new Error('新增失敗');
        return res.json();
    })
    .then(() => {
        fetchProducts();
        form.reset();
        showToast('新增產品成功', 'success');
    })
    .catch(() => showToast('新增產品失敗', 'error'));
}

function deleteProduct(id) {
    fetch(`${API_URL}/products/${id}`, {
        method: 'DELETE'
    })
    .then(res => {
        if (!res.ok) throw new Error('刪除失敗');
        fetchProducts();
        showToast('已刪除產品', 'success');
    })
    .catch(() => showToast('刪除產品失敗', 'error'));
}

// --- Edit product modal logic ---
function openEditModal(id){
    // fetch product detail
    fetch(`${API_URL}/products/${id}`)
        .then(r=>{
            if(!r.ok) throw new Error('fetch failed');
            return r.json();
        })
        .then(p=>{
            const modal = document.getElementById('editModal');
            document.getElementById('edit_id').value = p.id;
            document.getElementById('edit_name').value = p.name;
            document.getElementById('edit_price').value = p.price;
            document.getElementById('edit_cost').value = p.cost;
            document.getElementById('edit_stock').value = p.stock;
            modal.style.display = 'flex';
        })
        .catch(()=> showToast('無法載入產品資料','error'));
}

function closeEditModal(){
    const modal = document.getElementById('editModal');
    if(modal) modal.style.display='none';
}

function submitEditForm(e){
    e.preventDefault();
    const id = document.getElementById('edit_id').value;
    const data = {
        name: document.getElementById('edit_name').value,
        price: parseFloat(document.getElementById('edit_price').value),
        cost: parseFloat(document.getElementById('edit_cost').value),
        stock: parseInt(document.getElementById('edit_stock').value)
    };
    fetch(`${API_URL}/products/${id}`, {
        method: 'PUT',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify(data)
    }).then(r=>{
        if(!r.ok) throw new Error('update failed');
        return r.json();
    }).then(()=>{
        showToast('更新成功','success');
        closeEditModal();
        fetchProducts();
    }).catch(()=> showToast('更新失敗','error'));
}

// Attach edit modal handlers when DOM ready
document.addEventListener('DOMContentLoaded', ()=>{
    const editForm = document.getElementById('editProductForm');
    if(editForm) editForm.addEventListener('submit', submitEditForm);
    const editClose = document.getElementById('editClose');
    if(editClose) editClose.addEventListener('click', closeEditModal);
});

document.getElementById('addProductForm').addEventListener('submit', addProduct);

document.addEventListener('DOMContentLoaded', fetchProducts);
