import os
import select
import socket
import struct
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from servidor import ServidorChat


def esperar(condicion):
    limite = time.monotonic() + 3
    while not condicion():
        assert time.monotonic() < limite, "El servidor no respondió en 3 segundos"
        time.sleep(0.01)


class ClientePrueba:
    def __init__(self, direccion):
        self.socket = socket.create_connection(direccion, timeout=3)
        self.pendientes = b""

    def enviar(self, mensaje):
        self.socket.sendall((mensaje + "\n").encode("utf-8"))

    def recibir(self, cantidad=1):
        mensajes = []
        for _ in range(cantidad):
            while b"\n" not in self.pendientes:
                datos = self.socket.recv(4096)
                assert datos, "Conexión cerrada antes de recibir el mensaje"
                self.pendientes += datos
            linea, self.pendientes = self.pendientes.split(b"\n", 1)
            mensajes.append(linea.decode("utf-8"))
        return mensajes

    def sin_mensajes(self):
        assert not self.pendientes
        assert not select.select([self.socket], [], [], 0.1)[0]

    def cerrar(self, abrupto=False):
        if abrupto:
            # SO_LINGER=0 aborta la conexión con un reset TCP.
            formato = "HH" if os.name == "nt" else "ii"
            self.socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_LINGER, struct.pack(formato, 1, 0)
            )
        self.socket.close()


@pytest.fixture
def chat():
    servidor = ServidorChat(port=0)  # Puerto libre y servidor nuevo por prueba.
    clientes = []
    hilo = threading.Thread(target=servidor.ejecutar, daemon=True)
    hilo.start()

    def conectar():
        cantidad = len(servidor.clientes)
        cliente = ClientePrueba(servidor.direccion)
        clientes.append(cliente)
        esperar(lambda: len(servidor.clientes) == cantidad + 1)
        return cliente

    yield servidor, conectar
    for cliente in clientes:
        cliente.cerrar()
    servidor.detener.set()
    hilo.join(timeout=3)
    assert not hilo.is_alive(), "El servidor quedó bloqueado"
    assert not servidor.clientes


def test_varios_clientes_orden_unicode_y_sin_eco(chat):
    _, conectar = chat
    emisor, uno, dos = conectar(), conectar(), conectar()
    mensajes = ["primero", "¡Hola, 🐧!", "á" * 512]
    for mensaje in mensajes:
        emisor.enviar(mensaje)
    assert uno.recibir(3) == dos.recibir(3) == mensajes
    for cliente in (emisor, uno, dos):
        cliente.sin_mensajes()


def test_tcp_separa_mensajes_y_reconstruye_unicode_fragmentado(chat):
    servidor, conectar = chat
    emisor, receptor = conectar(), conectar()
    datos = "🐧\nuno\ndos\n".encode("utf-8")
    emisor.socket.sendall(datos[:2])
    esperar(lambda: datos[:2] in servidor.clientes.values())
    receptor.sin_mensajes()
    emisor.socket.sendall(datos[2:])
    assert receptor.recibir(3) == ["🐧", "uno", "dos"]


def test_envio_y_recepcion_simultaneos_sin_perdidas_ni_duplicados(chat):
    _, conectar = chat
    emisores = [conectar(), conectar()]
    observadores = [conectar(), conectar()]
    lotes = [[f"{i}:{n}" for n in range(10)] for i in range(2)]
    barrera = threading.Barrier(2)

    def conversar(cliente, lote):
        barrera.wait(timeout=3)
        for mensaje in lote:
            cliente.enviar(mensaje)
        return cliente.recibir(10)

    with ThreadPoolExecutor(max_workers=4) as executor:
        envios = [
            executor.submit(conversar, c, lote) for c, lote in zip(emisores, lotes)
        ]
        vistas = [executor.submit(c.recibir, 20) for c in observadores]
        for i, envio in enumerate(envios):
            assert envio.result(timeout=5) == lotes[1 - i]
        uno, dos = [vista.result(timeout=5) for vista in vistas]
    assert uno == dos
    assert sorted(uno) == sorted(lotes[0] + lotes[1])
    for lote in lotes:
        assert [mensaje for mensaje in uno if mensaje in lote] == lote
    for cliente in emisores + observadores:
        cliente.sin_mensajes()


@pytest.mark.parametrize("datos", [b"\n", b"   \n", b"\xff\n", b"a\rb\n"])
def test_entrada_invalida_no_se_reenvia_y_permite_continuar(chat, datos):
    _, conectar = chat
    emisor, receptor = conectar(), conectar()
    emisor.socket.sendall(datos)
    assert emisor.recibir()[0].startswith("ERROR:")
    receptor.sin_mensajes()
    emisor.enviar("sigo conectado")
    assert receptor.recibir() == ["sigo conectado"]


@pytest.mark.parametrize("final", [b"", b"\n"])
def test_mensaje_largo_se_rechaza_y_desconecta(chat, final):
    servidor, conectar = chat
    emisor, receptor = conectar(), conectar()
    emisor.socket.sendall(b"x" * 1025 + final)
    assert emisor.recibir() == ["ERROR: El mensaje no puede superar 1024 bytes."]
    esperar(lambda: len(servidor.clientes) == 1)
    receptor.sin_mensajes()
    nuevo = conectar()
    nuevo.enviar("el servidor sigue activo")
    assert receptor.recibir() == ["el servidor sigue activo"]


@pytest.mark.parametrize("cantidad", [1, 3])
def test_desconexiones_abruptas_durante_la_transmision(chat, cantidad):
    servidor, conectar = chat
    emisor, receptor = conectar(), conectar()
    caidos = [conectar() for _ in range(cantidad)]
    barrera = threading.Barrier(2)

    def enviar():
        barrera.wait(timeout=3)
        for i in range(30):
            emisor.enviar(f"mensaje-{i}")

    with ThreadPoolExecutor(max_workers=1) as executor:
        envio = executor.submit(enviar)
        barrera.wait(timeout=3)
        for cliente in caidos:
            cliente.socket.sendall(b"mensaje incompleto")
            cliente.cerrar(abrupto=True)
        assert receptor.recibir(30) == [f"mensaje-{i}" for i in range(30)]
        envio.result(timeout=5)
    esperar(lambda: len(servidor.clientes) == 2)
    receptor.sin_mensajes()
    receptor.enviar("todavía funciona")
    assert emisor.recibir() == ["todavía funciona"]
    nuevo = conectar()
    nuevo.enviar("nuevo cliente")
    assert emisor.recibir() == receptor.recibir() == ["nuevo cliente"]
