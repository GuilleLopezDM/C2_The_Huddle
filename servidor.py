import select
import socket
import threading

HOST = "127.0.0.1"
PORT = 65432
BUFFER = 4096
MAX_MENSAJE = 1024  # Bytes UTF-8, sin contar el salto de línea final.
ERROR_LONGITUD = f"El mensaje no puede superar {MAX_MENSAJE} bytes."


def validar_mensaje(mensaje):
    """Devuelve el texto original o lanza ValueError si no es válido."""
    if not isinstance(mensaje, str):
        raise ValueError("El mensaje debe ser texto.")
    if not mensaje.strip():
        raise ValueError("El mensaje no puede estar vacío.")
    if "\n" in mensaje or "\r" in mensaje:
        raise ValueError("El mensaje debe ocupar una sola línea.")
    if len(mensaje.encode("utf-8")) > MAX_MENSAJE:
        raise ValueError(ERROR_LONGITUD)
    return mensaje


def desconectar(cliente, clientes):
    """Elimina al cliente y sus datos pendientes; se puede llamar varias veces."""
    clientes.pop(cliente, None)
    try:
        cliente.close()
    except OSError:
        pass


def enviar(cliente, datos, clientes):
    try:
        cliente.sendall(datos)
        return True
    except OSError:
        desconectar(cliente, clientes)
        return False


def broadcast(mensaje, remitente, clientes):
    """Reenvía a todos excepto al remitente; un fallo no afecta a los demás."""
    for cliente in list(clientes):
        if cliente != remitente:
            enviar(cliente, mensaje, clientes)


class ServidorChat:
    """Chat con select, un único bucle y un buffer por cliente."""

    def __init__(self, host=HOST, port=PORT):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((host, port))
            self.socket.listen()
        except OSError:
            self.socket.close()
            raise
        self.direccion = self.socket.getsockname()
        self.clientes = {}  # socket: bytes que aún no terminan en salto de línea.
        self.detener = threading.Event()

    def recibir(self, cliente):
        try:
            datos = cliente.recv(BUFFER)
        except OSError:
            desconectar(cliente, self.clientes)
            return
        if not datos:
            desconectar(cliente, self.clientes)
            return

        pendientes = self.clientes[cliente] + datos
        # TCP puede juntar mensajes o dividir incluso un carácter UTF-8.
        while b"\n" in pendientes:
            linea, pendientes = pendientes.split(b"\n", 1)
            try:
                validar_mensaje(linea.decode("utf-8"))
            except ValueError as error:
                respuesta = f"ERROR: {error}\n".encode("utf-8")
                if not enviar(cliente, respuesta, self.clientes):
                    return
                if len(linea) > MAX_MENSAJE:
                    desconectar(cliente, self.clientes)
                    return
            else:
                broadcast(linea + b"\n", cliente, self.clientes)

        self.clientes[cliente] = pendientes
        if len(pendientes) > MAX_MENSAJE:
            # Limita la memoria si un cliente nunca termina su mensaje.
            enviar(cliente, f"ERROR: {ERROR_LONGITUD}\n".encode("utf-8"), self.clientes)
            desconectar(cliente, self.clientes)

    def ejecutar(self):
        try:
            while not self.detener.is_set():
                lectura, _, _ = select.select(
                    [self.socket, *self.clientes], [], [], 0.05
                )
                for activo in lectura:
                    if activo is self.socket:
                        try:
                            cliente, _ = self.socket.accept()
                        except OSError:
                            continue
                        # Un receptor que no lee no puede bloquear indefinidamente.
                        cliente.settimeout(0.5)
                        self.clientes[cliente] = b""
                    elif activo in self.clientes:
                        # Un broadcast anterior pudo eliminar un socket fallido.
                        self.recibir(activo)
        finally:
            for cliente in list(self.clientes):
                desconectar(cliente, self.clientes)
            self.socket.close()


def run_server():
    servidor = ServidorChat()
    print(f"Servidor escuchando en {servidor.direccion[0]}:{servidor.direccion[1]}")
    try:
        servidor.ejecutar()
    except KeyboardInterrupt:
        print("\nCerrando servidor...")


if __name__ == "__main__":
    run_server()
