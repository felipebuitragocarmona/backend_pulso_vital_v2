# Medical ECG Architecture

Servidor por capas para gestionar pacientes y PDFs ECG exportados desde Apple Watch.

## Capas

- `presentation/rest`: endpoints FastAPI.
- `presentation/mcp`: tools MCP y carga de archivos.
- `business`: servicios y casos de uso.
- `data`: repositorio genérico, repositorios concretos, factory y persistencia relacional.
- `models/dto`: modelos de entrada/salida.
- `models/entity`: entidades del dominio.
- `infrastructure/extractors`: extracción/procesamiento del PDF ECG.

## Persistencia relacional

La capa `data` usa **Generic Repository + repositorios concretos + Factory Method**. Ya no existe una interfaz médica gigante con todos los métodos de pacientes y ECG.

La idea es similar a Spring Data/JPA:

- `data/base_repository.py`: contiene `GenericRepository`, con CRUD base reutilizable: `save`, `find_all`, `find_by_id`, `update`, `delete_by_id`, `exists_by_id` y `find_by_fields`.
- `data/patient_repository.py`: contiene `PatientRepository`, que hereda del repositorio genérico y puede agregar consultas propias de pacientes.
- `data/ecg_repository.py`: contiene `EcgRepository`, que hereda del repositorio genérico y agrega `find_by_patient_id`.
- `data/database.py`: centraliza engine, sesión SQLAlchemy y creación de tablas.
- `data/sqlalchemy_models.py`: modelos ORM y relación `PatientORM 1:N EcgORM`.
- `data/repository_factory.py`: construye y agrupa los repositorios concretos.

La capa de negocio depende de repositorios concretos pequeños, no de SQLite, PostgreSQL, MySQL ni de una interfaz con todos los métodos del sistema.

Por defecto usa SQLite:

```env
REPO_TYPE=sqlite
SQLITE_PATH=medical_ecg.db
```

También puedes usar `DATABASE_URL`:

```env
DATABASE_URL=sqlite:///medical_ecg.db
```

Para PostgreSQL:

```env
REPO_TYPE=postgresql
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/medical_ecg
```

Para MySQL:

```env
REPO_TYPE=mysql
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/medical_ecg
```

> Nota: para PostgreSQL instala `psycopg`; para MySQL instala `PyMySQL`. SQLite no requiere instalar driver adicional porque viene con Python.

## Relación de tablas

```text
patients
- id PK autoincrement
- fullName
- birthDate
- createdAt
- updatedAt

ecgs
- id PK autoincrement
- patientId FK -> patients.id ON DELETE CASCADE
- registeredAt
- pdfUrl
- originalFilename
- uploadedAt
```

Al eliminar un paciente, la base elimina sus ECG asociados mediante `ON DELETE CASCADE`. Además, el servicio elimina la carpeta física del paciente en `uploads/ecgs/patient_{id}`.

## Selección de extractor ECG (Factory Method)

La extracción de ECG usa inversión de dependencias con `EcgExtractorInterface` + Factory Method por creators concretos:

- `AppleWatchCreator`
- `KardiaCreator`
- `SamsungHealthCreator`

Puedes seleccionar la fuente por variable de entorno:

```env
ECG_EXTRACTOR_SOURCE=apple_watch
```

Valores soportados actualmente:

- `apple_watch`
- `kardia`
- `samsung` (placeholder, aún no implementado en detalle)

Alias aceptados: `apple`, `applewatch`, `alivecor`, `kardia_mobile`, `samsung_health`.

Si envías explícitamente `source` al servicio de extracción, ese valor tiene prioridad sobre el valor de entorno.

## Cómo extender un repositorio concreto

Si necesitas una consulta especial, no agregues métodos a una interfaz global. Agrégala únicamente al repositorio que la necesita.

Ejemplo:

```python
class PatientRepository(GenericRepository[PatientORM, PatientEntity]):
    def __init__(self, session_factory):
        super().__init__(session_factory, PatientORM, PatientEntity)

    def find_by_name_contains(self, text: str):
        with self.session_factory() as session:
            rows = session.scalars(
                select(PatientORM)
                .where(PatientORM.fullName.ilike(f"%{text}%"))
                .order_by(PatientORM.id.asc())
            ).all()
            return [self._to_dict(row) for row in rows]
```

El servicio puede usar los métodos genéricos cuando bastan:

```python
created = self.repo.save(patient_data)
patient = self.repo.find_by_id(patient_id)
patients = self.repo.find_all()
updated = self.repo.update(patient_id, data)
deleted = self.repo.delete_by_id(patient_id)
```

Y puede usar métodos propios cuando el repositorio concreto los tenga:

```python
ecgs = self.ecg_repo.find_by_patient_id(patient_id)
```

## Cambio importante frente a una persistencia JSON

En una base de datos relacional, el servicio **no debe calcular el id** con `max(id)+1`. Esa responsabilidad queda en la base de datos. Por eso:

- `PatientService.create_patient()` crea la entidad sin id.
- `EcgService.upload_ecg_pdf_bytes()` crea el registro ECG sin id.
- `PatientRepository.save()` y `EcgRepository.save()` retornan el registro creado con el id generado por la base de datos.

## Ejecutar API REST

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m uvicorn main_api_rest_server:app --reload --port 5000
```

## Ejecutar servidor MCP

```powershell
python main_mcp_server.py
```

## Endpoints principales

- `POST /patients`
- `GET /patients`
- `GET /patients/{patient_id}`
- `PUT /patients/{patient_id}`
- `DELETE /patients/{patient_id}`
- `POST /patients/{patient_id}/ecgs/upload`
- `GET /patients/{patient_id}/ecgs`
- `GET /ecgs/{ecg_id}`
- `DELETE /ecgs/{ecg_id}`

## Exponer el servidor públicamente con Cloudflare Tunnel

Para usar el servidor MCP desde Claude (u otro cliente externo) sin necesidad de despliegue en la nube, puedes exponerlo temporalmente mediante **Cloudflare Tunnel**. Esto crea una URL pública `https://` que apunta a tu servidor local.

### Requisitos

Instala `cloudflared` desde [https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/) o con:

```powershell
winget install Cloudflare.cloudflared
```

### Pasos

1. Levanta el servidor MCP en el puerto 9000:

```powershell
python -m uvicorn main_api_rest_server:app --reload --port 9000
```

2. En otra terminal, abre el túnel:

```powershell
cloudflared tunnel --url http://localhost:9000
```

3. `cloudflared` imprimirá una URL pública similar a:

```
https://random-name-here.trycloudflare.com
```

4. Copia esa URL y úsala en Claude como base del servidor MCP o REST.

> **Nota:** cada vez que ejecutes el comando se genera una URL distinta. El túnel se cierra al terminar el proceso. Para una URL estable, considera crear un túnel con nombre usando `cloudflared tunnel create <nombre>`.
