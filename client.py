import socket
import threading
import time

HOST = "127.0.0.1"
PORT = 65432
BUFFER = 1024
REINTENTO_SEGUNDOS = 2


def conectar_con_reintento():
    """
    Intenta conectarse al servidor en bucle hasta lograrlo.
    Evita que el cliente crashee si el servidor no está disponible.
    """
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, PORT))
            print(f"Conectado al servidor: {HOST}:{PORT}")
            return s
        except ConnectionRefusedError:
            print(f"No se pudo conectar. Reintentando en {REINTENTO_SEGUNDOS} segundos...")
            time.sleep(REINTENTO_SEGUNDOS)
        except OSError:
            print(f"Error de red. Reintentando en {REINTENTO_SEGUNDOS} segundos...")
            time.sleep(REINTENTO_SEGUNDOS)


def recibir_mensajes(sock):
    """
    Hilo dedicado a escuchar mensajes del servidor.
    Permite recibir mientras el usuario escribe.
    """
    while True:
        try:
            datos = sock.recv(BUFFER)

            # Si recv devuelve vacío, el servidor se cayó o cerró conexión
            if not datos:
                print("Servidor desconectado")
                break

            print(datos.decode("utf-8"))

        except OSError:
            print("Conexion perdida con el servidor")
            break


def run_cliente():
    while True:
        sock = conectar_con_reintento()

        # Thread para recepción simultánea (evita bloquear input)
        hilo_receptor = threading.Thread(
            target=recibir_mensajes,
            args=(sock,),
            daemon=True
        )
        hilo_receptor.start()

        try:
            while True:
                mensaje = input()

                # Comando local de salida
                if mensaje.lower() == "exit":
                    try:
                            sock.shutdown(socket.SHUT_RDWR) #Tarea para la casa  SHUT_RDWR
                    except OSError:
                        pass
                    sock.close()
                    return

                try:
                    sock.send(mensaje.encode("utf-8"))
                except OSError:
                    # Si falla el envío, probablemente se cayó la conexión
                    print("No se pudo enviar el mensaje. Intentando reconectar...")

                    try:
                        sock.close()
                    except OSError:
                        pass

                    break  # salir para reconectar

        except KeyboardInterrupt:
            # Manejo limpio de Ctrl+C
            print("\nCerrando cliente...")
            try:
                sock.close()
            except OSError:
                pass
            return


run_cliente()