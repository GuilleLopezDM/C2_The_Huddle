from unittest.mock import Mock

from servidor import ServidorChat


def test_mensaje_largo_completo_desconecta_igual_que_uno_fragmentado():
    servidor = ServidorChat.__new__(ServidorChat)
    cliente, sano = Mock(), Mock()
    cliente.recv.return_value = b"x" * 1025 + b"\n"
    servidor.clientes = {cliente: b"", sano: b""}
    servidor.recibir(cliente)
    assert cliente not in servidor.clientes
    cliente.close.assert_called_once()
    assert cliente.sendall.call_args.args[0].startswith(b"ERROR:")
    sano.sendall.assert_not_called()
