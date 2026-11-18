# Chapada Advanced Analytics

Aplicacion web desarrollada con Streamlit para explorar datos operativos de Chapada y consultar informacion mediante Databricks AI/BI Genie.

## Funcionalidades

- **Coordenadas paralelas:** visualizacion interactiva de variables de molienda y flotacion, con filtros por fechas, limites de control y puntajes z.
- **Chat con Genie:** consultas en lenguaje natural a un Databricks Genie Space y ejecucion de las consultas generadas sobre un SQL Warehouse.
- **Navegacion central:** acceso directo a la pagina principal y a las herramientas desde la barra lateral.

## Arquitectura

- `app.py`: pagina principal y navegacion.
- `pages/parallel.py`: visualizacion paralela y lectura de tablas desde Databricks SQL.
- `pages/chatbot.py`: interfaz conversacional y conexion con Databricks Genie.
- `app.yaml`: configuracion real utilizada por Databricks Apps.
- `app.example.yaml`: plantilla sin valores reales para compartir o documentar la configuracion.
- `.env.example`: plantilla de variables para ejecucion local.

## Requisitos

- Python 3.10 o superior.
- Acceso a un workspace de Databricks.
- Un SQL Warehouse.
- Un Genie Space habilitado.
- Permisos sobre las tablas utilizadas por la visualizacion.

## Variables de entorno

| Variable | Uso |
|---|---|
| `DATABRICKS_HOST` | URL del workspace de Databricks |
| `DATABRICKS_WAREHOUSE_ID` | ID del SQL Warehouse usado por Genie |
| `GENIE_SPACE_ID` | ID del Genie Space |
| `HTTP_PATH_METRIC` | HTTP path del SQL Warehouse para los datos de metricas |
| `TABLE_METRIC_NAME` | Tabla de metricas historicas |
| `HTTP_PATH_KPI_DICT` | HTTP path del SQL Warehouse para el diccionario de KPI |
| `TABLE_KPI_NAME` | Tabla con nombres y limites de KPI |

El proyecto usa la autenticacion de Databricks del SDK. No es necesario almacenar usuario, contraseña, token o secreto personal en el repositorio. En Databricks Apps, la plataforma administra la identidad y el acceso segun la configuracion del recurso.

## Ejecucion local

1. Crear y activar un entorno virtual:

   ```bash
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

2. Instalar dependencias:

   ```bash
   python -m pip install -r requirements.txt
   ```

3. Configurar el entorno local:

   ```bash
   Copy-Item .env.example .env
   ```

   Completar `.env` con los valores del workspace. Para autenticar con Databricks, tambien se puede configurar `DATABRICKS_CONFIG_PROFILE` o los metodos de autenticacion admitidos por el SDK.

4. Ejecutar la aplicacion:

   ```bash
   streamlit run app.py
   ```

## Despliegue en Databricks Apps

Conservar `app.yaml` como configuracion de despliegue y verificar que contiene los valores reales requeridos por el entorno. Revisar los permisos del SQL Warehouse y las tablas antes de publicar.

Comandos habituales:

```bash
databricks bundle validate
databricks apps deploy
```

Los comandos exactos pueden variar segun la configuracion de Databricks CLI y el despliegue configurado.

## Seguridad antes de subir a GitHub

- No subir `.env`, archivos de credenciales, `secrets.toml` ni la carpeta `.databricks`.
- Revisar el historial y los archivos preparados con `git status` antes del primer commit.
- Mantener credenciales reales fuera del codigo y de `app.example.yaml`.
- Rotar cualquier secreto que haya sido compartido o subido accidentalmente.
