import io
import threading
from unittest.mock import Mock

import pytest

import client
from servidor import broadcast, desconectar, validar_mensaje


@pytest.mark.parametrize("mensaje", ["Hola", "¡Hola, 🐧!", "a" * 1024, "á" * 512])
def test_mensaje_valido(mensaje):
    assert validar_mensaje(mensaje) == mensaje


@pytest.mark.parametrize(
    "mensaje",
    ["", "   ", "\t", None, 123, b"hola", "a" * 1025, "á" * 513, "a\nb", "a\rb"],
)
def test_mensaje_invalido(mensaje):
    with pytest.raises(ValueError):
        validar_mensaje(mensaje)


def test_broadcast_envia_a_todos_menos_al_remitente():
    emisor, uno, dos = Mock(), Mock(), Mock()
    broadcast(b"hola\n", emisor, {emisor: b"", uno: b"", dos: b""})
    emisor.sendall.assert_not_called()
    for receptor in (uno, dos):
        receptor.sendall.assert_called_once_with(b"hola\n")


@pytest.mark.parametrize(
    "error", [BrokenPipeError(), ConnectionResetError(), TimeoutError()]
)
def test_broadcast_elimina_al_fallido_y_sigue(error):
    emisor, muerto, sano = Mock(), Mock(), Mock()
    muerto.sendall.side_effect = error
    clientes = {emisor: b"", muerto: b"pendiente", sano: b""}
    broadcast(b"hola\n", emisor, clientes)
    assert muerto not in clientes
    muerto.close.assert_called_once()
    sano.sendall.assert_called_once_with(b"hola\n")


def test_desconectar_repetidamente_no_falla():
    cliente = Mock()
    cliente.close.side_effect = OSError()
    clientes = {cliente: b"incompleto"}
    desconectar(cliente, clientes)
    desconectar(cliente, clientes)
    assert not clientes


def test_cliente_reintenta_tras_error_de_conexion(monkeypatch):
    sock = Mock()
    conectar = Mock(side_effect=[ConnectionRefusedError(), sock])
    monkeypatch.setattr(client.socket, "create_connection", conectar)
    pausa = Mock()
    monkeypatch.setattr(client.time, "sleep", pausa)
    assert client.conectar_con_reintento() is sock
    assert conectar.call_count == 2
    pausa.assert_called_once()


def test_cliente_recibe_y_detecta_desconexion(capsys):
    sock = Mock()
    sock.makefile.return_value = io.StringIO("hola\nchau\n")
    desconectado = threading.Event()
    client.recibir_mensajes(sock, desconectado)
    assert "hola\nchau\n" in capsys.readouterr().out
    assert desconectado.is_set()
