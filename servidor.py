import socket
import select

HOST = "127.0.0.1"
PORT = 65432
BUFFER = 1024


def broadcast(mensaje, remitente, clientes, servidor):
    """
    Envía un mensaje a todos los clientes conectados,
    excepto al remitente y al socket del servidor.
    """
    clientes_muertos = []
# Como se que no se murio un cliente
    for cliente in clientes:
        # nunca intentar enviar al servidor ni al remitente
        if cliente == remitente or cliente == servidor:
            continue
        try:
            cliente.send(mensaje)
        except OSError:
            # Si falla el envío, marcamos el cliente "Muerto"
            clientes_muertos.append(cliente)

    # Limpieza de sockets muertos fuera del loop principal
    for muerto in clientes_muertos:
        if muerto in clientes:
            clientes.remove(muerto)
        try:
            muerto.close()
        except OSError:
            pass


def run_server():
    # Uso de context manager para asegurar cierre del socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        # Permite reutilizar el puerto sin esperar TIME_WAIT
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)# tarea para la casa SOL_SOCKET SETSOCKOPT SO_REUSEADDR

        servidor.bind((HOST, PORT))
        servidor.listen()

        print(f"Servidor escuchando en {HOST}:{PORT}")

        # Lista que contiene tanto el servidor como los clientes
        lista_sockets = [servidor]

        try:
            while True:
                # select evita usar threads para manejar múltiples clientes
                lectura_sockets, _, _ = select.select(lista_sockets, [], [])

                for socket_activo in lectura_sockets:
                    if socket_activo == servidor:
                        # Nueva conexión entrante
                        conn, addr = servidor.accept()
                        print(f"Conexion establecida con {addr}")
                        lista_sockets.append(conn)

                        mensaje = f"Nuevo cliente conectado: {addr}".encode("utf-8")
                        broadcast(mensaje, conn, lista_sockets, servidor)

                    else:
                        try:
                            datos = socket_activo.recv(BUFFER)

                            # recv vacío => cliente desconectado correctamente
                            if not datos: 
                                print("Cliente desconectado")
 
                                mensaje = "Un usuario se fue".encode("utf-8")
                                broadcast(mensaje, socket_activo, lista_sockets, servidor)

                                if socket_activo in lista_sockets:
                                    lista_sockets.remove(socket_activo)

                                socket_activo.close()
                            else:
                                # Reenvío directo (no decodificar/recodificar innecesariamente)
                                broadcast(datos, socket_activo, lista_sockets, servidor)

                        except (ConnectionResetError, OSError): #Que errores maneja el OSError
                            # Desconexión abrupta (cable, crash, etc.)
                            print("El cliente se desconecto de forma abrupta")

                            if socket_activo in lista_sockets:
                                lista_sockets.remove(socket_activo)

                            try:
                                socket_activo.close()
                            except OSError:
                                pass

        except KeyboardInterrupt:
            # Manejo limpio de Ctrl+C
            print("\nCerrando servidor...")

        finally:
            # Cerrar todos los sockets abiertos
            for sock in lista_sockets:
                try:
                    sock.close()
                except OSError:
                    pass


run_server()