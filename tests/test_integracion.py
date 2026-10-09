import socket
import threading
import pytest
from servidor import server

@pytest.fixture
def servidor_real():
    s = server("127.0.0.1", 0)
    s.establecer_conexion()
    hilo = threading.Thread(target=s.revisar_selectores, daemon=True)
    hilo.start()
    yield s
    s.server_socket.close()


def test_cliente_recibe_pedido_de_nombre(servidor_real):
    puerto = servidor_real.server_socket.getsockname()[1]
    with socket.create_connection(("127.0.0.1", puerto), timeout=2) as cliente:
        assert cliente.recv(1024).decode() == "Ingresa tu nombre: "


def test_cliente_recibe_aviso_de_que_se_unio(servidor_real,monkeypatch):
    
    monkeypatch.setattr(servidor_real, "guardar_log", lambda mensaje: None)
    puerto = servidor_real.server_socket.getsockname()[1]
    
    with socket.create_connection(("127.0.0.1", puerto), timeout=2) as barbara:
        barbara.recv(1024)
        barbara.send(b"Barbara")
        assert barbara.recv(1024).decode() == "Barbara se unió al chat!"


def test_mensaje_de_un_cliente_llega_al_otro(servidor_real,monkeypatch):
    
    monkeypatch.setattr(servidor_real, "guardar_log", lambda mensaje: None)
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