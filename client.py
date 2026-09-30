import socket
import threading
import time

HOST = "127.0.0.1"
PORT = 65432
REINTENTO_SEGUNDOS = 2


def conectar_con_reintento():
    while True:
        try:
            sock = socket.create_connection((HOST, PORT))
            print(f"Conectado al servidor: {HOST}:{PORT}. Escribe exit para salir.")
            return sock
        except OSError:
            print(
                f"No se pudo conectar. Reintentando en {REINTENTO_SEGUNDOS} segundos..."
            )
            time.sleep(REINTENTO_SEGUNDOS)


def recibir_mensajes(sock, desconectado):
    try:
        # El lector reconstruye líneas y caracteres UTF-8 divididos por TCP.
        with sock.makefile("r", encoding="utf-8") as entrada:
            for mensaje in entrada:
                print(mensaje.rstrip("\n"))
        print("Servidor desconectado. Presiona Enter para reconectar.")
    except (OSError, UnicodeError):
        print("Conexión perdida. Presiona Enter para reconectar.")
    finally:
        desconectado.set()


def run_cliente():
    try:
        while True:
            sock = conectar_con_reintento()
            desconectado = threading.Event()
            hilo = threading.Thread(
                target=recibir_mensajes, args=(sock, desconectado), daemon=True
            )
            hilo.start()
            try:
                while not desconectado.is_set():
                    mensaje = input()
                    if mensaje.lower() == "exit":
                        return
                    if desconectado.is_set():
                        break
                    # Un salto de línea delimita cada mensaje, incluso si está vacío.
                    sock.sendall((mensaje + "\n").encode("utf-8"))
            except OSError:
                print("No se pudo enviar el mensaje. Intentando reconectar...")
            finally:
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                sock.close()
                hilo.join(timeout=1)
    except (KeyboardInterrupt, EOFError):
        print("\nCerrando cliente...")


if __name__ == "__main__":
    run_cliente()
