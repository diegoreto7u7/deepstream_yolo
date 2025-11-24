# Volúmenes Persistentes en DeepStream Docker

Esta guía explica cómo funcionan los volúmenes persistentes y las diferentes opciones disponibles.

## 📖 ¿Qué son Volúmenes Persistentes?

Los **volúmenes persistentes** son almacenamiento que **NO se pierde** cuando borras o recreas el container Docker.

### ¿Por qué son importantes?

En DeepStream, tienes datos que tardan mucho en generar y NO quieres perder:

| Datos | Tamaño | Tiempo de Generación | ¿Persistente? |
|-------|--------|---------------------|---------------|
| **TensorRT Engine** | ~400MB | 10-20 minutos | ✅ CRÍTICO |
| **Configuraciones** | <1MB | Manual | ✅ CRÍTICO |
| **Logs** | Variable | Continuo | ⚠️ Útil |
| **Recordings** | Varios GB | Continuo | ⚠️ Según necesidad |

## 🔍 Situación Actual: Bind Mounts

**Actualmente usas bind mounts, que YA SON PERSISTENTES:**

```yaml
volumes:
  - ./engines:/app/engines        # ✅ PERSISTENTE en ./engines
  - ./configs:/app/configs        # ✅ PERSISTENTE en ./configs
  - ./logs:/app/logs              # ✅ PERSISTENTE en ./logs
```

### Prueba de Persistencia

```bash
# 1. Ver datos actuales
ls -lh ./engines

# 2. Borrar container
docker rm -f deepstream-yolo11-app

# 3. Verificar datos aún existen
ls -lh ./engines
# ✅ Los archivos siguen ahí!

# 4. Recrear container
./scripts/docker-run.sh

# 5. Dentro del container, los datos están
docker exec deepstream-yolo11-app ls /app/engines
# ✅ El engine sigue disponible!
```

**Conclusión**: Tus datos **YA SON PERSISTENTES** con la configuración actual.

---

## 🎯 Tipos de Volúmenes

Docker tiene 3 tipos de almacenamiento:

### 1. Bind Mounts (Actual - YA es persistente)

```yaml
volumes:
  - ./engines:/app/engines  # Directorio del host → container
```

**Características**:
- ✅ Los datos están en `./engines` (visible en el host)
- ✅ Fácil acceso desde el host: `ls ./engines`
- ✅ Fácil backup: `cp -r ./engines /backup/`
- ✅ Persistente al borrar container
- ❌ Path específico del host (`/home/user/project/engines`)

**Cuándo usar**: Development, cuando necesitas acceder fácilmente a los archivos

### 2. Named Volumes (Alternativa)

```yaml
volumes:
  - deepstream-engines:/app/engines  # Volumen gestionado por Docker

volumes:
  deepstream-engines:
    driver: local
```

**Características**:
- ✅ Docker gestiona el almacenamiento
- ✅ Portable entre diferentes hosts
- ✅ Mejor rendimiento en algunos casos
- ✅ Persistente al borrar container
- ❌ Datos ocultos en `/var/lib/docker/volumes/`
- ❌ Acceso desde host requiere comandos Docker

**Cuándo usar**: Production, clusters, cuando no necesitas acceso directo

### 3. Anonymous Volumes (NO USAR)

```yaml
volumes:
  - /app/engines  # Sin nombre ni bind mount
```

**Características**:
- ❌ **NO persistente** - se pierde al borrar container
- ❌ Difícil de gestionar
- ❌ No recomendado

---

## 🤔 ¿Qué Puede Querer Decir tu Encargado?

### Opción 1: Confirmar que es Persistente ✅

**Pregunta**: "¿Los TensorRT engines se pierden si reinicio el container?"

**Respuesta**: **NO**, ya usas bind mounts que son persistentes.

```bash
# Los datos están en:
ls ./engines/tensorrt/yolo11x_b1.engine  # ✅ Aquí persiste

# Incluso si borras el container:
docker rm -f deepstream-yolo11-app
ls ./engines/tensorrt/yolo11x_b1.engine  # ✅ Sigue ahí
```

### Opción 2: Usar Named Volumes (Producción)

**Pregunta**: "¿Deberíamos usar named volumes en lugar de bind mounts para producción?"

**Cuándo SÍ usar named volumes**:
- Deploys en múltiples servidores
- No necesitas acceder a archivos desde el host
- Quieres que Docker gestione el almacenamiento
- Mejor rendimiento I/O en algunos casos

**Cuándo NO (mantener bind mounts)**:
- Development local
- Necesitas editar configs manualmente
- Quieres ver/copiar logs fácilmente
- Necesitas backup manual simple

### Opción 3: Política de Backup

**Pregunta**: "¿Tenemos backup de los datos persistentes?"

**Solución**: Crear script de backup para bind mounts.

---

## 🔧 Implementación: Named Volumes

Si tu encargado quiere **named volumes**, aquí está cómo:

### Opción A: Named Volumes Puros (Docker gestiona)

```yaml
services:
  deepstream-app:
    volumes:
      - deepstream-engines:/app/engines
      - deepstream-logs:/app/logs
      - ./configs:/app/configs  # Config sigue siendo bind mount

volumes:
  deepstream-engines:  # Docker crea en /var/lib/docker/volumes/
  deepstream-logs:
```

**Ubicación real**: `/var/lib/docker/volumes/deepstream_deepstream-engines/_data/`

### Opción B: Named Volumes con Path Específico (Híbrido)

He creado `docker-compose.persistent.yml` que usa esta opción:

```yaml
volumes:
  deepstream-engines:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${PWD}/volumes/engines  # Usa ./volumes/engines pero como named volume
```

**Ventajas**:
- Named volume (mejor gestión Docker)
- Pero datos siguen en path conocido (`./volumes/engines`)
- Lo mejor de ambos mundos

---

## 🚀 Cómo Migrar a Named Volumes

### Paso 1: Crear docker-compose.persistent.yml

Ya lo he creado en: `docker-compose.persistent.yml`

### Paso 2: Crear directorios para volúmenes

```bash
mkdir -p volumes/engines
mkdir -p volumes/logs
mkdir -p volumes/recordings
mkdir -p volumes/output
```

### Paso 3: Copiar datos existentes (si los tienes)

```bash
# Copiar engines existentes
cp -r engines/* volumes/engines/

# Copiar logs
cp -r logs/* volumes/logs/
```

### Paso 4: Usar el nuevo docker-compose

```bash
# Parar container actual
docker-compose down

# Usar nuevo archivo
docker-compose -f docker-compose.persistent.yml up -d

# O renombrar
mv docker-compose.yml docker-compose.bindmounts.yml
mv docker-compose.persistent.yml docker-compose.yml
docker-compose up -d
```

### Paso 5: Verificar datos persisten

```bash
# Dentro del container
docker exec -it deepstream-yolo11-app ls -lh /app/engines/tensorrt/

# Borrar y recrear
docker-compose down
docker-compose up -d

# Verificar datos siguen ahí
docker exec -it deepstream-yolo11-app ls -lh /app/engines/tensorrt/
```

---

## 📦 Gestión de Named Volumes

### Listar volúmenes

```bash
docker volume ls

# Salida:
# DRIVER    VOLUME NAME
# local     deepstream_deepstream-engines
# local     deepstream_deepstream-logs
```

### Inspeccionar volumen

```bash
docker volume inspect deepstream_deepstream-engines

# Muestra:
# {
#   "Mountpoint": "/var/lib/docker/volumes/deepstream_deepstream-engines/_data",
#   "Driver": "local",
#   ...
# }
```

### Backup de named volume

```bash
# Backup
docker run --rm \
  -v deepstream_deepstream-engines:/data \
  -v $(pwd):/backup \
  ubuntu \
  tar czf /backup/engines-backup.tar.gz -C /data .

# Restore
docker run --rm \
  -v deepstream_deepstream-engines:/data \
  -v $(pwd):/backup \
  ubuntu \
  tar xzf /backup/engines-backup.tar.gz -C /data
```

### Limpiar volúmenes no usados

```bash
# Ver volúmenes huérfanos
docker volume ls -f dangling=true

# Limpiar
docker volume prune

# ⚠️ CUIDADO: Borra volúmenes no usados por ningún container
```

### Borrar volumen específico

```bash
# ⚠️ PELIGRO: Esto BORRA los datos permanentemente
docker volume rm deepstream_deepstream-engines
```

---

## 🎯 Recomendación Final

### Para Development (Actual - YA funciona bien)

```yaml
# Usar bind mounts (configuración actual)
volumes:
  - ./engines:/app/engines      # ✅ Fácil acceso
  - ./configs:/app/configs      # ✅ Fácil edición
  - ./logs:/app/logs            # ✅ Fácil lectura
```

**Por qué**: Acceso directo a archivos, fácil debug, fácil backup.

### Para Production en un Solo Servidor

```yaml
# Seguir con bind mounts PERO con paths absolutos
volumes:
  - /opt/deepstream/engines:/app/engines
  - /opt/deepstream/logs:/app/logs
  - /opt/deepstream/configs:/app/configs
```

**Por qué**: Persistente, fácil backup con rsync/cp, paths conocidos.

### Para Production en Cluster/Kubernetes

```yaml
# Usar named volumes con driver específico (NFS, Ceph, etc)
volumes:
  deepstream-engines:
    driver: nfs
    driver_opts:
      share: nfs-server:/exports/engines
```

**Por qué**: Compartido entre nodos, gestionado por orquestador.

---

## ✅ Checklist de Persistencia

Verifica que estos datos NO se pierden al recrear container:

```bash
# 1. TensorRT Engine (CRÍTICO)
ls -lh ./engines/tensorrt/*.engine
# ✅ Debe existir y ser ~400MB

# 2. Configuraciones (CRÍTICO)
ls -lh ./configs/deepstream/*.txt
# ✅ Debe existir

# 3. Logs (opcional pero útil)
ls -lh ./logs/
# ✅ Puede estar vacío

# 4. Borrar container
docker rm -f deepstream-yolo11-app

# 5. Verificar archivos SIGUEN existiendo
ls -lh ./engines/tensorrt/*.engine
ls -lh ./configs/deepstream/*.txt
# ✅ Deben seguir ahí

# 6. Recrear container
./scripts/docker-run.sh

# 7. Verificar dentro del container
docker exec deepstream-yolo11-app ls /app/engines/tensorrt/
# ✅ Engine disponible sin rebuild
```

Si todos los pasos ✅ pasan, **tus datos SON PERSISTENTES**.

---

## 📋 Pregunta a tu Encargado

Para aclarar qué necesita exactamente, pregúntale:

### Opción 1: Confirmar Persistencia
> "Los TensorRT engines ya persisten en `./engines` usando bind mounts. Si borro el container, los datos NO se pierden. ¿Es esto lo que necesitas confirmar?"

### Opción 2: Named Volumes
> "¿Quieres que cambiemos a named volumes de Docker en lugar de bind mounts? ¿Por alguna razón específica (cluster, portabilidad, etc.)?"

### Opción 3: Política de Backup
> "¿Te refieres a implementar backups automáticos de los datos persistentes?"

### Opción 4: Paths de Producción
> "¿Quieres que usemos paths absolutos para producción como `/opt/deepstream/engines` en lugar de paths relativos `./engines`?"

---

## 📚 Resumen

| Configuración | Persistente | Fácil Acceso | Portable | Recomendado Para |
|---------------|-------------|--------------|----------|------------------|
| **Bind Mounts (actual)** | ✅ Sí | ✅ Muy fácil | ❌ No | Development |
| **Named Volumes (Docker)** | ✅ Sí | ❌ Complicado | ✅ Sí | Production simple |
| **Named + Path (híbrido)** | ✅ Sí | ✅ Fácil | ⚠️ Parcial | Production + acceso |
| **Anonymous Volumes** | ❌ NO | ❌ No | ❌ No | ❌ Nunca |

**Tu configuración actual (bind mounts) YA ES PERSISTENTE y es la adecuada para development.**

Si necesitas cambiar a named volumes, usa `docker-compose.persistent.yml` que he creado.
