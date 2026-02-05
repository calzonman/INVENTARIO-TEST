import { writable, get } from 'svelte/store';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// --- INTERFACES ---
export interface Product {
    id: string;
    name: string;
    sku: string;
    barcode: string;
    currentStock: number;
    minStock: number;
    unitPrice: number;
    category: string;
    location: string;
    tenantId: string;
    description?: string;
    trackBatches: boolean;
}

export interface Movement {
    id: string;
    timestamp: string;
    tenantId?: string;
    productId: string;
    productName: string;
    productSku: string;
    type: 'in' | 'out' | 'adjustment';
    quantity: number;
    previousStock?: number;
    newStock?: number;
    userId: string;
    userName: string;
    location?: string;
    batchNumber?: string;
    expirationDate?: string;
}

export interface User {
    id: string;
    name: string;
    email: string;
    role: 'admin' | 'supervisor' | 'operator';
    tenantId: string;
    createdAt?: string;
    badgeToken?: string; // <--- NUEVO: Token para QR
}

export interface Location {
    id: string;
    code: string;
    name: string;
    description: string;
    tenantId: string;
}

export interface Lot {
    id: string;
    productId: string;
    productSku: string;
    number: string;
    quantity: number;
    expiryDate: string;
    tenantId: string;
    status: string;
}

// --- PERSISTENCIA SEGURA (Helpers) ---
const getStoredItem = (key: string) => {
    if (typeof window !== 'undefined') {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : null;
    }
    return null;
};

const setStoredItem = (key: string, value: any) => {
    if (typeof window !== 'undefined') {
        if (value) localStorage.setItem(key, JSON.stringify(value));
        else localStorage.removeItem(key);
    }
};

// --- STORES ---
export const authToken = writable<string | null>(getStoredItem('authToken'));
export const currentUser = writable<User | null>(getStoredItem('currentUser'));

// NUEVO: Store para manejar vistas públicas (Login vs Kiosco)
export const publicView = writable<'login' | 'kiosk'>('login');

// Suscribirse a cambios para persistir en localStorage
authToken.subscribe(val => setStoredItem('authToken', val));
currentUser.subscribe(val => setStoredItem('currentUser', val));

export const currentTenant = writable({ 
    id: 't1', 
    name: 'TechRetail Ltda', 
    industry: 'Retail Tecnológico', 
    primaryColor: '#030213', 
    createdAt: new Date().toISOString() 
});

export const products = writable<Product[]>([]);
export const movements = writable<Movement[]>([]);
export const users = writable<User[]>([]);
export const locations = writable<Location[]>([]);
export const lots = writable<Lot[]>([]);
export const activeView = writable('dashboard');
export const pendingBarcode = writable<string | null>(null); 

// --- HELPER DE AUTORIZACIÓN ---
const getAuthHeaders = () => {
    const token = get(authToken);
    return {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
    };
};

// --- ADAPTERS (Mapeo Backend -> Frontend) ---
const adaptProduct = (data: any): Product => ({
    id: data._id || data.id,
    name: data.name,
    sku: data.sku,
    barcode: data.barcode,
    currentStock: data.current_stock,
    minStock: data.min_stock,
    unitPrice: data.unit_price,
    category: data.category,
    location: data.location,
    tenantId: data.tenant_id,
    description: data.description,
    trackBatches: data.track_batches || false
});

const adaptMovement = (data: any): Movement => ({
    id: data._id || data.id,
    timestamp: data.timestamp,
    productId: data.product_id,
    productName: data.product_name,
    productSku: data.product_sku || "UNK",
    type: data.type,
    quantity: data.quantity,
    userId: data.user_id,
    userName: data.user_name,
    location: data.location || "-",
    previousStock: 0, 
    newStock: 0,
    tenantId: data.tenant_id,
    batchNumber: data.batch_number,
    expirationDate: data.expiration_date
});

const adaptUser = (data: any): User => ({
    id: data._id || data.id,
    name: data.name,
    email: data.email,
    role: data.role,
    tenantId: data.tenant_id,
    createdAt: new Date().toISOString(),
    badgeToken: data.badge_token // <--- NUEVO
});

const adaptLocation = (data: any): Location => ({
    id: data._id || data.id,
    code: data.code,
    name: data.name,
    description: data.description,
    tenantId: data.tenant_id
});

const adaptLot = (data: any): Lot => ({
    id: data._id || data.id,
    productId: data.product_id,
    productSku: data.product_sku,
    number: data.number,
    quantity: data.quantity,
    expiryDate: data.expiry_date,
    tenantId: data.tenant_id,
    status: data.status
});

// --- ACCIONES DE AUTENTICACIÓN ---

export const loginUser = async (email: string, password: string) => {
    try {
        const res = await fetch(`${API_URL}/users/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        if (!res.ok) {
            const errorData = await res.json();
            throw new Error(errorData.detail || 'Error en inicio de sesión');
        }

        const data = await res.json();
        
        authToken.set(data.access_token);
        
        // Obtenemos el perfil completo para tener el badgeToken
        const meRes = await fetch(`${API_URL}/users/me`, {
            headers: { 'Authorization': `Bearer ${data.access_token}` }
        });
        const meData = await meRes.json();

        currentUser.set(adaptUser(meData));
        return true;
    } catch (e) {
        throw e;
    }
};

export const logoutUser = () => {
    authToken.set(null);
    currentUser.set(null);
    activeView.set('dashboard');
    publicView.set('login'); // Volver a login al salir
};

// --- NUEVA ACCIÓN: KIOSK CHECKOUT ---
export const kioskCheckout = async (badgeToken: string, productCode: string) => {
    const res = await fetch(`${API_URL}/movements/kiosk-checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            badge_token: badgeToken, 
            product_code: productCode 
        })
    });
    
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Error en Kiosco');
    }
    
    return await res.json(); // Retorna { message, product_name, remaining_stock, lot_used }
};

// --- API ACTIONS (CRUD) ---

// 1. PRODUCTOS
export const loadProducts = async () => {
    try {
        const tenantId = get(currentTenant).id;
        const res = await fetch(`${API_URL}/products/?tenant_id=${tenantId}`, {
            headers: getAuthHeaders()
        });
        if (res.status === 401) logoutUser(); 
        const data = await res.json();
        products.set(data.map(adaptProduct));
    } catch (e) { console.error(e); }
};

export const addProduct = async (product: Omit<Product, 'id'>) => {
    const apiBody = {
        sku: product.sku,
        barcode: product.barcode,
        name: product.name,
        description: product.description,
        category: product.category,
        current_stock: product.currentStock,
        min_stock: product.minStock,
        unit_price: product.unitPrice,
        location: product.location,
        tenant_id: product.tenantId,
        track_batches: product.trackBatches
    };
    const res = await fetch(`${API_URL}/products/`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(apiBody)
    });
    if (!res.ok) throw new Error('Error al crear producto');
    
    const createdData = await res.json();
    await loadProducts();
    return adaptProduct(createdData); 
};

export const deleteProduct = async (id: string) => {
    if (!confirm('¿Eliminar producto?')) return;
    await fetch(`${API_URL}/products/${id}`, { 
        method: 'DELETE',
        headers: getAuthHeaders()
    });
    await loadProducts();
};

export const getProductByBarcode = async (code: string): Promise<Product | null> => {
    try {
        const tenantId = get(currentTenant).id;
        const res = await fetch(`${API_URL}/products/scan/${code}?tenant_id=${tenantId}`, {
            headers: getAuthHeaders()
        });
        if (res.status === 404) return null;
        const data = await res.json();
        return adaptProduct(data);
    } catch (e) { return null; }
};

// 2. MOVIMIENTOS
export const loadMovements = async () => {
    try {
        const tenantId = get(currentTenant).id;
        const res = await fetch(`${API_URL}/movements/?tenant_id=${tenantId}`, {
            headers: getAuthHeaders()
        });
        const data = await res.json();
        movements.set(data.map(adaptMovement));
    } catch (e) { console.error(e); }
};

export const addMovement = async (mov: any, lotId?: string) => {
    const apiBody = {
        product_id: mov.productId,
        product_name: mov.productName,
        product_sku: mov.productSku,
        type: mov.type,
        quantity: mov.quantity,
        user_id: mov.userId,
        user_name: mov.userName,
        tenant_id: mov.tenantId,
        location: mov.location,
        lot_id: lotId || null
    };

    const res = await fetch(`${API_URL}/movements/`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(apiBody)
    });
    if (!res.ok) throw new Error('Error registrando movimiento');
    await loadProducts(); 
    await loadMovements();
    await loadAllLots(); 
};

// 3. LOTES
export const loadAllLots = async () => {
    try {
        const tenantId = get(currentTenant).id;
        const res = await fetch(`${API_URL}/lots/?tenant_id=${tenantId}`, {
            headers: getAuthHeaders()
        });
        const data = await res.json();
        lots.set(data.map(adaptLot));
    } catch (e) { console.error(e); }
};

export const loadLotsByProduct = async (productId: string) => {
    try {
        const tenantId = get(currentTenant).id;
        const res = await fetch(`${API_URL}/lots/?tenant_id=${tenantId}&product_id=${productId}`, {
            headers: getAuthHeaders()
        });
        const data = await res.json();
        return data.map(adaptLot);
    } catch (e) { console.error(e); return []; }
};

export const createLot = async (lotData: any) => {
    const apiBody = {
        product_id: lotData.productId,
        product_sku: lotData.productSku,
        number: lotData.number,
        quantity: lotData.quantity,
        expiry_date: lotData.expiryDate,
        tenant_id: lotData.tenantId,
        status: 'active'
    };
    const res = await fetch(`${API_URL}/lots/`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(apiBody)
    });
    if (!res.ok) throw new Error('Error creando lote');
    await loadAllLots(); 
    return await res.json();
};

// 4. USUARIOS
export const loadUsers = async () => {
    try {
        const tenantId = get(currentTenant).id;
        const res = await fetch(`${API_URL}/users/?tenant_id=${tenantId}`, {
            headers: getAuthHeaders()
        });
        if (!res.ok) return; 
        const data = await res.json();
        users.set(data.map(adaptUser));
    } catch (e) { console.error(e); }
};

export const addUser = async (u: any) => {
    const apiBody = { ...u, tenant_id: u.tenantId };
    const res = await fetch(`${API_URL}/users/register`, { 
        method: 'POST', 
        headers: getAuthHeaders(),
        body: JSON.stringify(apiBody)
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Error creando usuario');
    }
    await loadUsers();
};

export const deleteUser = async (id: string) => {
    await fetch(`${API_URL}/users/${id}`, { 
        method: 'DELETE',
        headers: getAuthHeaders()
    });
    await loadUsers();
};

// 5. UBICACIONES
export const loadLocations = async () => {
    try {
        const tenantId = get(currentTenant).id;
        const res = await fetch(`${API_URL}/locations/?tenant_id=${tenantId}`, {
            headers: getAuthHeaders()
        });
        const data = await res.json();
        locations.set(data.map(adaptLocation));
    } catch (e) { console.error(e); }
};

export const addLocation = async (l: any) => {
    const apiBody = { ...l, tenant_id: l.tenantId };
    const res = await fetch(`${API_URL}/locations/`, {
        method: 'POST', 
        headers: getAuthHeaders(),
        body: JSON.stringify(apiBody)
    });
    if (!res.ok) throw new Error('Error creando ubicación');
    await loadLocations();
};

export const deleteLocation = async (id: string) => {
    await fetch(`${API_URL}/locations/${id}`, { 
        method: 'DELETE',
        headers: getAuthHeaders()
    });
    await loadLocations();
};