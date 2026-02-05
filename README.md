# 📦 Sistema SaaS de Inventario (MVP)

Sistema de gestión de inventario moderno enfocado en trazabilidad, control de lotes y escaneo rápido mediante dispositivos HID. Diseñado para laboratorios y sector alimentario.

## 🚀 Características Principales

* **Escáner HID Global:** Integración con lectores de código de barras físicos. Detecta entradas de teclado automáticamente sin necesidad de "foco" en inputs.
* **Gestión de Lotes y Vencimientos:** Control FEFO (First Expired, First Out) con trazabilidad completa de lotes por producto.
* **Movimientos en Tiempo Real:** Registro de Entradas/Salidas con actualización instantánea de stock.
* **Gestión de Productos:** CRUD completo con categorización y alertas de stock mínimo.
* **Arquitectura Multi-Tenant:** Preparado para gestionar múltiples organizaciones (Tenant ID).
* **Reportes:** Exportación de inventario y movimientos a CSV.

## 🛠️ Stack Tecnológico

**Frontend:**
* ![Svelte](https://img.shields.io/badge/Svelte-4A4A55?style=for-the-badge&logo=svelte&logoColor=FF3E00) **Svelte + Vite**
* ![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white) **Tailwind CSS v3**
* **Lucide Svelte** (Iconografía)

**Backend:**
* ![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi) **FastAPI (Python)**
* ![MongoDB](https://img.shields.io/badge/MongoDB-4EA94B?style=for-the-badge&logo=mongodb&logoColor=white) **MongoDB Atlas + Motor (Async)**
* **Pydantic v2** (Validación de datos)

## 📋 Requisitos Previos

* Node.js (v18 o superior)
* Python (v3.9 o superior)
* Cuenta en MongoDB Atlas (o instancia local)

## ⚙️ Instalación y Configuración

### 1. Clonar el repositorio

`git clone [https://github.com/tu-usuario/nombre-repo.git](https://github.com/tu-usuario/nombre-repo.git)`

`cd nombre-repo`

### 2. Configurar Backend (API)

`cd app`
#### Crear entorno virtual
`python -m venv venv`
#### Activar entorno (Windows)
`venv\Scripts\activate`
#### Activar entorno (Mac/Linux)
`source venv/bin/activate`
#### Instalar dependencias
`pip install -r requirements.txt`

**Variables de Entorno Backend**: Crea un archivo .env en la raíz o carpeta app con:

MONGO_URI=tu_string_de_conexion_mongo
DB_NAME=inventory_db

### 3. Configurar Frontend (UI)
En una nueva terminal:

`cd src`

 O volver a la raíz si el package.json está ahí
 
`npm install`
####▶️ Ejecución
Backend:

**Desde la raíz del proyecto**
`uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

Frontend:
`npm run dev`
La aplicación estará disponible en http://localhost:5173.

### 📂 Estructura del Proyecto

![Estructura de carpetas](https://github.com/Cheuque-C/inventarioDLT/blob/develop/imagenes/Estructura-de-carpetas.png "Estructura de carpetas")

### 🛡️ Estado del Proyecto
Actualmente en fase MVP.

[x] CRUD Productos

[x] Lógica de Escáner HID

[x] Gestión de Lotes (Entrada/Salida)

[x] Historial de Movimientos

[ ] Autenticación JWT Real (Actualmente simulada)

[ ] Roles y Permisos avanzados