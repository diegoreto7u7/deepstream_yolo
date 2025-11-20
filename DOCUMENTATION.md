# 📚 Documentación - DeepStream YOLO11x Auto-Build

Toda la documentación está organizada por categorías. Elige la que necesites:

---

## 🚀 Comenzar (5 minutos)

**Para empezar rápidamente:**

1. **[START_HERE.md](docs/getting-started/START_HERE.md)** ← **COMIENZA AQUÍ**
   - Qué es este proyecto
   - Cómo instalarlo en 30 segundos
   - Caminos rápidos según tu tiempo

2. **[README.md](docs/getting-started/README.md)**
   - Descripción general
   - Características principales
   - Quick start command

3. **[QUICKSTART.md](docs/getting-started/QUICKSTART.md)**
   - Setup paso a paso
   - Opciones Docker y local
   - Verificación del sistema

---

## 📖 Guías (Específicas)

**Según tu situación:**

1. **[INSTALL.md](docs/guides/INSTALL.md)**
   - Instalación detallada en Linux
   - Drivers NVIDIA, CUDA, Docker
   - Troubleshooting

2. **[RHEL_COMPATIBILITY.md](docs/guides/RHEL_COMPATIBILITY.md)**
   - Si usas RedHat/CentOS/Rocky
   - Diferencias con Debian
   - Solución de problemas específicos

---

## 🔧 Técnico (Profundo)

**Para entender cómo funciona:**

1. **[ARCHITECTURE.md](docs/technical/ARCHITECTURE.md)**
   - Cómo funciona el auto-build
   - Detección de hardware
   - Construcción del engine TensorRT
   - Performance benchmarks

2. **[PROJECT_STRUCTURE.md](docs/technical/PROJECT_STRUCTURE.md)**
   - Estructura de carpetas
   - Ubicación de archivos
   - Descripción de cada componente

3. **[PROJECT_COMPLETION_SUMMARY.md](docs/technical/PROJECT_COMPLETION_SUMMARY.md)**
   - Resumen de todo lo implementado
   - Especificaciones técnicas
   - Checklist de verificación

---

## 🆘 Solución de Problemas

**Si algo no funciona:**

1. **[IMPLEMENTATION_CHECKLIST.md](docs/troubleshooting/IMPLEMENTATION_CHECKLIST.md)**
   - Verificar qué está instalado
   - Validar sintaxis
   - Checklist de despliegue

---

## 📊 Mapa Rápido

```
¿Cuánto tiempo tengo?
├─ 30 segundos  → START_HERE.md (rápido start)
├─ 5 minutos    → README.md + comandos
├─ 15 minutos   → QUICKSTART.md
├─ 1 hora       → README + ARCHITECTURE + INSTALL
└─ Todo         → Lee todo en orden

¿Qué necesito?
├─ Empezar      → docs/getting-started/
├─ Instalar     → docs/guides/
├─ Entender     → docs/technical/
└─ Solucionar   → docs/troubleshooting/

¿Qué sistema tengo?
├─ Ubuntu/Debian → Todos los docs funcionan
├─ RedHat/CentOS → RHEL_COMPATIBILITY.md
└─ Otro Linux    → START_HERE.md recomendado
```

---

## 🎯 Quick Links

| Necesito | Archivo |
|----------|---------|
| Empezar ahora | [START_HERE.md](docs/getting-started/START_HERE.md) |
| Descripción general | [README.md](docs/getting-started/README.md) |
| Setup rápido | [QUICKSTART.md](docs/getting-started/QUICKSTART.md) |
| Instalación detallada | [INSTALL.md](docs/guides/INSTALL.md) |
| Usar en RedHat | [RHEL_COMPATIBILITY.md](docs/guides/RHEL_COMPATIBILITY.md) |
| Entender la arquitectura | [ARCHITECTURE.md](docs/technical/ARCHITECTURE.md) |
| Ver la estructura | [PROJECT_STRUCTURE.md](docs/technical/PROJECT_STRUCTURE.md) |
| Verificar todo | [IMPLEMENTATION_CHECKLIST.md](docs/troubleshooting/IMPLEMENTATION_CHECKLIST.md) |

---

## ✨ Resumen Ejecutivo

```
Este proyecto proporciona:
✅ Auto-build TensorRT engine para cualquier GPU NVIDIA
✅ Docker universal (funciona en Ubuntu, Debian, RedHat, CentOS, Rocky)
✅ Cero configuración manual
✅ Detección automática de hardware
✅ Documentación completa para cada caso

Paso 1: ./build.sh
Paso 2: docker run -it --gpus all deepstream-yolo11x:latest
Paso 3: Done! Engine se auto-genera (primera vez: 5-10 min)
```

---

## 📁 Estructura de Carpetas

```
docs/
├── getting-started/          ← Comienza aquí
│   ├── START_HERE.md         (5 min - punto de entrada)
│   ├── README.md             (2 min - descripción general)
│   └── QUICKSTART.md         (5 min - setup rápido)
│
├── guides/                   ← Guías específicas
│   ├── INSTALL.md            (instalación detallada)
│   └── RHEL_COMPATIBILITY.md (para RedHat/CentOS)
│
├── technical/                ← Detalles técnicos
│   ├── ARCHITECTURE.md       (cómo funciona)
│   ├── PROJECT_STRUCTURE.md  (estructura de archivos)
│   └── PROJECT_COMPLETION_SUMMARY.md (resumen técnico)
│
└── troubleshooting/          ← Solución de problemas
    └── IMPLEMENTATION_CHECKLIST.md (verificar instalación)
```

---

## 🚀 Próximos Pasos

1. **Novato:** Lee [START_HERE.md](docs/getting-started/START_HERE.md)
2. **Quiero empezar:** Lee [QUICKSTART.md](docs/getting-started/QUICKSTART.md)
3. **Necesito instalar:** Lee [INSTALL.md](docs/guides/INSTALL.md)
4. **Entiendo el sistema:** Lee [ARCHITECTURE.md](docs/technical/ARCHITECTURE.md)

---

**Status:** ✅ Documentación completa y organizada
**Última actualización:** Noviembre 2025
