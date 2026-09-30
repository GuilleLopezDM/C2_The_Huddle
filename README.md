# C11 — Pruebas de Sock-it-to-me Chat

Chat TCP con Python, sockets y `select`. Las pruebas usan **pytest**.

## Ejecutar

Desde la carpeta del proyecto, con Python 3.10 o superior:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Para usar el chat, ejecuta `python servidor.py` en una terminal y `python client.py` en otras dos. Escribe mensajes y presiona Enter; los reciben los demás clientes. Usa `exit` para salir.

La dirección es `127.0.0.1:65432`. El cliente reintenta si no puede conectar. Si el servidor cae mientras esperas en `input()`, presiona Enter para reconectar.

## Obligatorios

| Requisito | Dónde se cumple |
| --- | --- |
| Unitarias de funciones críticas | `tests/test_unitarios.py`: validación, broadcast, desconexión y cliente. |
| TDD: Red–Green–Refactor | `tests/test_tdd.py` y [TDD.md](TDD.md), con registros reales en `evidencia/`. |
| Integración y clientes simultáneos | `tests/test_integracion.py`: sockets reales, orden, mensajes completos y ausencia de pérdidas o duplicados. |
| Desconexiones repentinas | Uno y tres clientes abortan su conexión mientras otro envía mensajes. Los restantes siguen funcionando y se aceptan clientes nuevos. |
| Casos positivos y negativos | Texto válido, Unicode, vacíos, tipos incorrectos, límites de longitud, UTF-8 inválido y errores de red. |

Cada integración usa un servidor nuevo en un puerto libre y cierra sus conexiones al terminar. No necesita un servidor iniciado manualmente.

## Decisiones

- Los mensajes terminan en `\n`, para separar los que TCP agrupa y reconstruir los que divide.
- `sendall()` envía todos los bytes. El servidor tiene un timeout de envío para evitar bloqueos indefinidos.
- Se aceptan hasta 1024 bytes UTF-8 por mensaje, sin contar el salto de línea. Las entradas inválidas reciben `ERROR: ...` y no se retransmiten; exceder el límite cierra la conexión del emisor.
- El servidor usa un único bucle, por lo que los clientes reciben los mensajes en el mismo orden de procesamiento. No se guardan mensajes para reconexiones.

## Resultado

**33 pruebas aprobadas**, Ruff y compilación Python correctos, en Windows con Python 3.11.9 y pytest 9.1.1. Registro actual: [evidencia/pruebas-finales.txt](evidencia/pruebas-finales.txt).
