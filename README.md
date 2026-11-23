# 💬 Chat TCP cliente-servidor

> Challenge 2 · The Huddle · Python · Sockets

Chat de consola donde varios clientes se conectan a un servidor central y cada mensaje se reenvía (*broadcast*) al resto de los participantes.

## ✨ Características

- **Servidor sin hilos:** usa `select()` para atender a muchos clientes a la vez desde un único proceso.
- **Broadcast:** cada mensaje se reenvía a todos los clientes menos al que lo envió.
- **Limpieza de conexiones:** detecta desconexiones normales y abruptas y libera los sockets muertos.
- **Cliente con reintento:** si el servidor no está disponible, el cliente reintenta cada 2 segundos en lugar de fallar.
- **Cliente concurrente:** un hilo recibe mensajes mientras el principal lee lo que escribís.
- `SO_REUSEADDR` para reiniciar el servidor sin esperar el `TIME_WAIT`.

## 🚀 Ejecutar

Sin dependencias externas (solo la biblioteca estándar).

```bash
# Terminal 1
python servidor.py

# Terminal 2, 3, ... (uno por participante)
python client.py
```

Por defecto escucha en `127.0.0.1:65432` (configurable en las constantes `HOST` y `PORT`).

## 📁 Archivos

| Archivo | Rol |
|---|---|
| `servidor.py` | Acepta conexiones, multiplexa con `select()` y hace broadcast |
| `client.py` | Se conecta con reintento, envía y recibe mensajes en paralelo |
