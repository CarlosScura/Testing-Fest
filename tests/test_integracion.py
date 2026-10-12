import socket
import threading
import pytest
import time
import struct
from servidor import server


@pytest.fixture
def servidor_real(monkeypatch):
    s = server("127.0.0.1", 0)
    monkeypatch.setattr(s, "guardar_log", lambda mensaje: None)
    s.establecer_conexion()
    hilo = threading.Thread(target=s.revisar_selectores, daemon=True)
    hilo.start()
    yield s
    s.server_socket.close()


def test_cliente_recibe_pedido_de_nombre(servidor_real):
    puerto = servidor_real.server_socket.getsockname()[1]
    with socket.create_connection(("127.0.0.1", puerto), timeout=2) as cliente:
        assert cliente.recv(1024).decode() == "Ingresa tu nombre: "


def test_cliente_recibe_aviso_de_que_se_unio(servidor_real):
    
    puerto = servidor_real.server_socket.getsockname()[1]
    
    with socket.create_connection(("127.0.0.1", puerto), timeout=2) as barbara:
        barbara.recv(1024)
        barbara.send(b"Barbara")
        assert barbara.recv(1024).decode() == "Barbara se unió al chat!"


def test_mensaje_de_un_cliente_llega_al_otro(servidor_real):
    
    puerto = servidor_real.server_socket.getsockname()[1]
    
    with socket.create_connection(("127.0.0.1", puerto), timeout=2) as barbara:
        barbara.recv(1024)
        barbara.send(b"Barbara")
        barbara.recv(1024)
        
        with socket.create_connection(("127.0.0.1", puerto), timeout=2) as dick:
            dick.recv(1024)
            dick.send(b"Dick")
            barbara.recv(1024)
            dick.recv(1024)

            barbara.send(b"hola")

            assert "Barbara: hola" in dick.recv(1024).decode()


def test_emisor_no_recibe_su_propio_mensaje(servidor_real):

    puerto = servidor_real.server_socket.getsockname()[1]

    with socket.create_connection(("127.0.0.1", puerto), timeout=2) as jason:
        jason.recv(1024)
        jason.send(b"Jason")
        jason.recv(1024)

        with socket.create_connection(("127.0.0.1", puerto), timeout=2) as tim:
            tim.recv(1024)
            tim.send(b"Tim")
            jason.recv(1024)
            tim.recv(1024)

            jason.send(b"hola")
            tim.recv(1024)

            jason.settimeout(0.5)
            with pytest.raises(TimeoutError):
                jason.recv(1024)


def leer_todo(cliente, espera=0.5):
    cliente.settimeout(espera)
    datos = b""
    try:
        while True:
            parte = cliente.recv(1024)
            if not parte:
                break
            datos += parte
    except TimeoutError:
        pass
    return datos.decode()

@pytest.mark.xfail(reason="El servidor fusiona mensjaes consecutivos: recv(1024) no separa mensajes (ver pruebas.md)", strict=False)
def test_varios_mensajes_llegan_en_orden_sin_perderse(servidor_real):
    puerto = servidor_real.server_socket.getsockname()[1]
    with socket.create_connection(("127.0.0.1", puerto), timeout=2) as dinah:
        dinah.recv(1024)
        dinah.send(b"Dinah")
        dinah.recv(1024)
        with socket.create_connection(("127.0.0.1", puerto), timeout=2) as oliver:
            oliver.recv(1024)
            oliver.send(b"Oliver")
            dinah.recv(1024)
            oliver.recv(1024)

            dinah.send(b"uno")
            dinah.send(b"dos")
            dinah.send(b"tres")

            recibido = leer_todo(oliver)

            assert recibido.count("Dinah: uno") == 1
            assert recibido.count("Dinah: dos") == 1
            assert recibido.count("Dinah: tres") == 1
            assert recibido.index("Dinah: uno") < recibido.index("Dinah: dos") < recibido.index("Dinah: tres")


def test_varios_clientes_envian_a_la_vez(servidor_real):
    puerto = servidor_real.server_socket.getsockname()[1]
    nombres = ["Diana", "Bruce", "Clark"]
    clientes = {}
    try:
        for nombre in nombres:
            cliente = socket.create_connection(("127.0.0.1", puerto), timeout=2)
            cliente.recv(1024)
            cliente.send(nombre.encode())
            clientes[nombre] = cliente

        for cliente in clientes.values():
            leer_todo(cliente)

        largada = threading.Barrier(len(nombres))

        def enviar(nombre):
            largada.wait()
            clientes[nombre].send(f"mensaje de {nombre}".encode())

        hilos = [threading.Thread(target=enviar, args=(n,)) for n in nombres]
        for hilo in hilos:
            hilo.start()
        for hilo in hilos:
            hilo.join()

        for nombre, cliente in clientes.items():
            recibido = leer_todo(cliente)
            for otro in nombres:
                if otro == nombre:
                    assert f"{otro}: mensaje de {otro}" not in recibido
                else:
                    assert recibido.count(f"{otro}: mensaje de {otro}") == 1
    finally:
        for cliente in clientes.values():
            cliente.close()


def test_cliente_que_se_va_no_afecta_a_los_demas(servidor_real):
    puerto = servidor_real.server_socket.getsockname()[1]
    clientes = {}
    try:
        for nombre in ["Barry", "Wally", "Jay"]:
            cliente = socket.create_connection(("127.0.0.1", puerto), timeout=2)
            cliente.recv(1024)
            cliente.send(nombre.encode())
            clientes[nombre] = cliente

        for cliente in clientes.values():
            leer_todo(cliente)

        clientes["Jay"].close()  # Jay se va
        leer_todo(clientes["Barry"])   # vacía el aviso de salida
        leer_todo(clientes["Wally"])

        clientes["Barry"].send(b"hola")

        assert "Barry: hola" in leer_todo(clientes["Wally"])
    finally:
        for cliente in clientes.values():
            cliente.close()


def esperar_hasta(condicion, tiempo=2):
    limite = time.time() + tiempo
    while time.time() < limite:
        if condicion():
            return True
        time.sleep(0.01)
    return False

def test_al_irse_un_cliente_los_demas_reciben_aviso_y_sale_de_la_lista(servidor_real):
    puerto = servidor_real.server_socket.getsockname()[1]
    clientes = {}
    try:
        for nombre in ["Barry", "Wally", "Jay"]:
            cliente = socket.create_connection(("127.0.0.1", puerto), timeout=2)
            cliente.recv(1024)
            cliente.send(nombre.encode())
            clientes[nombre] = cliente

        for cliente in clientes.values():
            leer_todo(cliente)

        clientes["Jay"].close()

        # esperamos a que el servidor se entere de la salida
        assert esperar_hasta(lambda: "Jay" not in list(servidor_real.clientes.values()))

        assert "Jay abandonó el chat." in leer_todo(clientes["Barry"])
        assert "Jay abandonó el chat." in leer_todo(clientes["Wally"])
    finally:
        for cliente in clientes.values():
            cliente.close()


def test_caida_abrupta_no_afecta_a_los_demas(servidor_real):
    puerto = servidor_real.server_socket.getsockname()[1]
    clientes = {}
    try:
        for nombre in ["Barry", "Wally", "Jay"]:
            cliente = socket.create_connection(("127.0.0.1", puerto), timeout=2)
            cliente.recv(1024)
            cliente.send(nombre.encode())
            clientes[nombre] = cliente

        for cliente in clientes.values():
            leer_todo(cliente)

        # Barry se cae de golpe: SO_LINGER con tiempo 0 hace que close() envíe un reset
        clientes["Barry"].setsockopt(
            socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0)
        )
        clientes["Barry"].close()

        assert esperar_hasta(lambda: "Barry" not in list(servidor_real.clientes.values()))
        assert "Barry abandonó el chat." in leer_todo(clientes["Wally"])
        assert "Barry abandonó el chat." in leer_todo(clientes["Jay"])

        # el servidor sigue funcionando
        clientes["Wally"].send(b"sigo aca")
        assert "Wally: sigo aca" in leer_todo(clientes["Jay"])
    finally:
        for cliente in clientes.values():
            cliente.close()