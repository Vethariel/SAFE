# 🛡️ SAFE: Sistema Académico de Formación Empresarial

## 📖 Descripción  
SAFE es una plataforma integral de aprendizaje y gestión del talento que busca optimizar la forma en que las organizaciones capacitan y acompañan a sus colaboradores. Permite a cada empleado acceder a cursos y rutas de formación personalizadas, avanzar a su propio ritmo y recibir notificaciones oportunas sobre sus logros y pendientes. Al mismo tiempo, brinda a talento humano las herramientas para administrar usuarios, roles, contenidos y evaluaciones, mientras que supervisores y directivos cuentan con tableros e indicadores claros para dar seguimiento al progreso de sus equipos. De esta manera, SAFE no solo centraliza la formación, sino que convierte el aprendizaje en un proceso continuo, medible y alineado con los objetivos estratégicos de la empresa.

---

## 👥 Integrantes  
- Tomás Alejandro Bermúdez Guaqueta  : tbermudezg@unal.edu.co
- Daniel Alfonso Cely Infante  : dcelyi@unal.edu.co
- David Alejandro Herrera Novoa  : daherreran@unal.edu.co
- Daniel Alonso Gracia Pinto  : dagraciap@unal.edu.co

---

## 📂 Estructura del repositorio  

📁 **Vista resumida**  

- `/Asignaciones` → Entregas individuales y grupales  
- `/Documentación` → Casos de uso, diagramas, scripts y materiales de apoyo  
- `/Proyecto` → Código, diagramas y material visual del desarrollo  

---

📁 **Vista tipo árbol**  


```plaintext
.
├── .gitignore
├── README.md
├── Asignaciones
│   ├── Tarea_01.pdf
│   ├── Tarea_02.pdf
│   ├── Taller_<name>.pdf
│   └── ... (más archivos según se asignen)
├── Documentación
│   ├── Casos de uso
│   │   ├── CU_<nickname>_01.pdf
│   │   ├── CU_<nickname>_02.pdf
│   │   └── ... (más casos de uso)
│   ├── Proyecto
│   │   ├── diagramas.md
│   │   ├── script_implementacion.sql
│   │   └── ... (documentos relacionados al proyecto)
│   ├── Diagramas
│   │   ├── bd.md
│   │   └── ... (documentos relacionados a diagramas)
│   └── ... (otros documentos si es necesario)
└── Proyecto
    └── ... (estructura libre según la tecnología utilizada)
```

# Instalación y uso

## Requisitos

Este proyecto utiliza Docker para facilitar la instalación y despliegue del software.

- [Docker](https://www.docker.com/get-started) instalado en tu sistema.

## Instalación

1. **Clona el repositorio:**
    ```bash
    git clone https://github.com/TommyBermu/error404.git
    cd error404/Proyecto
    ```

2. **Configura las variables de entorno (si es necesario):**
    - Revisa si existe un archivo `.env.example` y renómbralo a `.env`.
    - Modifica los valores según tu entorno.

3. **Ejecuta el fichero setup.bat:**
    - Usando Windows:
      ```bash
      ./setup.bat
      ```
     - Usando MAC/Linux:
        ```bash
        chmod +x setup.sh
        ./setup.sh
        ```

4. **Accede a la aplicación:**
    - Abre tu navegador y visita `http://localhost:8000` o el puerto configurado.

## Notas

- Asegúrate de que los puertos necesarios estén libres.
- Consulta los archivos Docker (`Dockerfile`, `docker-compose.yml`) para más detalles de configuración.

## Usuario administrador de prueba

Tras las migraciones, puedes crear o actualizar un superusuario de demo para validar permisos de administración:

```bash
docker compose exec -T web python manage.py ensure_default_admin
# Credenciales por defecto: usuario "admin" / contraseña "Admin123!"
```

Personaliza los valores con banderas (`--username`, `--email`, `--password`, `--role`, `--reset-password`) o variables de entorno (`DEFAULT_ADMIN_USERNAME`, `DEFAULT_ADMIN_EMAIL`, `DEFAULT_ADMIN_PASSWORD`, `DEFAULT_ADMIN_ROLE`).