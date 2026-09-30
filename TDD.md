# TDD — Mensajes demasiado largos

**Funcionalidad:** rechazar y desconectar al emisor de un mensaje mayor a 1024 bytes, tanto si llega completo como fragmentado, sin afectar a otros clientes.

| Fase | Trabajo realizado | Resultado registrado |
| --- | --- | --- |
| Red | Se escribió una prueba que exigía desconectar al recibir 1025 bytes y un salto de línea. El servidor todavía mantenía esa conexión. | [1 failed](evidencia/tdd-red.txt) |
| Green | Se agregó la desconexión y el retorno cuando la línea supera `MAX_MENSAJE`. | [1 passed](evidencia/tdd-green.txt) |
| Refactor | Se extrajo `ERROR_LONGITUD` para compartir el error entre la validación y el límite del buffer. | [45 passed en la suite original](evidencia/tdd-refactor.txt) |

La prueba original se movió de `tests/test_servidor.py` a `tests/test_tdd.py` al simplificar la entrega. Los registros conservan los nombres y resultados históricos; la suite compacta actual tiene **33 pruebas aprobadas**.

Para ejecutar la prueba TDD:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_tdd.py -q
```
