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

## Despliegue en Databricks Apps

Conservar `app.yaml` como configuracion de despliegue y verificar que contiene los valores reales requeridos por el entorno. Revisar los permisos del SQL Warehouse y las tablas antes de publicar.

Comandos habituales:

```bash
databricks bundle validate
databricks apps deploy
```
