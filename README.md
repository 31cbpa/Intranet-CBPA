# 🔐 Conexión SSH con clave personalizada

Este instructivo te guía paso a paso para:

1. Crear una clave SSH personalizada desde Windows (Git Bash).
2. Agregarla directamente desde la consola del servidor en DigitalOcean.
3. Verificar la conexión usando la nueva clave.

---

## 🖥️ 1. Crear clave SSH desde Windows

| Paso | Comando |
|------|---------|
| Generar clave | `ssh-keygen -t rsa -b 4096 -f ~/.ssh/nombre` |

> 🔸 Puedes dejar el passphrase vacío o ingresar uno por seguridad.  
> 🔸 Se generarán dos archivos:
> - Clave privada: `~/.ssh/nombre`  
> - Clave pública: `~/.ssh/nombre.pub`

---

## 📋 2. Copiar el contenido de la clave pública

| Paso | Comando |
|------|---------|
| Mostrar clave pública | `cat ~/.ssh/nombre.pub` |

> 🔸 Copia TODO el contenido mostrado.

---

## 🛜 3. Acceder a la consola del servidor (DigitalOcean)

1. Entra a tu proyecto en DigitalOcean.
2. Ubica el *Droplet* (ej: `Intranet-CBPA`).
3. Haz clic en los tres puntos `⋮` y selecciona **Access console**.

---

## 🛠️ 4. Agregar la nueva clave pública al servidor

Una vez dentro de la consola del Droplet:

| Paso | Comando |
|------|---------|
| Editar archivo | `nano ~/.ssh/authorized_keys` |
| Pegar clave pública al final del archivo | _(Pega manualmente)_ |
| Guardar y salir | `Ctrl + X`, luego `Y`, luego `Enter` |
| Asegurar permisos | `chmod 700 ~/.ssh` <br> `chmod 600 ~/.ssh/authorized_keys` |

---

## 🔁 5. Verificar la conexión con la nueva clave

Desde Git Bash en tu PC:

| Paso | Comando |
|------|---------|
| Conectarse | `ssh -i ~/.ssh/nombre root@ip` |

> 🔸 Asegúrate de reemplazar `nombre` por el nombre real de tu archivo de clave privada.

---

## 🧠 6. ¿Qué pasa al agregar una clave SSH desde el panel de DigitalOcean?

Agregar una clave en **Settings > Security > SSH Keys** del panel:

- ✅ La guarda en tu cuenta de DigitalOcean.
- ✅ Se agregará automáticamente a nuevos droplets que crees.
- ⚠️ **No se agrega a los droplets ya existentes.**

> Por eso, si agregas una nueva clave desde el panel pero intentas acceder a un droplet ya creado, **no funcionará**.

---

## ✅ ¿Cómo solucionarlo? Agregar clave directamente al droplet

Para que una clave funcione en un droplet ya creado, **debes conectarte por consola** y **agregarla manualmente**.

---

## ✅ ¡Todo listo!

Ahora puedes acceder de forma segura al servidor usando tu nueva clave SSH: `nombre` 🔐.