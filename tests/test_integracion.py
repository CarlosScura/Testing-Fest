import socket
import threading
import pytest
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