import pytest
from servidor import server

@pytest.fixture
def servidor():
    # Arrange
    s = server("127.0.0.1", 5000)
    yield s
    # Limpieza: se ejecuta siempre, pase o falle el test.
    s.server_socket.close()


def test_servidor_nuevo_no_tiene_clientes(servidor):
    # Act
    cantidad = len(servidor.clientes)
    # Assert
    assert cantidad == 0


class SocketFalso:
    def __init__(self, falla=False):
        self.enviados = []
        self.cerrado = False
        self.falla = falla

    def send(self,datos):
        if self.falla:
            raise OSError("Conexión rota")
        self.enviados.append(datos)

    def close(self):
        self.cerrado = True


def test_broadcast_envia_a_todos_menos_al_emisor(servidor):
    
    #Arrange
    emisor, otro1, otro2 = SocketFalso(), SocketFalso(), SocketFalso()
    servidor.clientes = {emisor:"Steve",otro1:"Peter",otro2:"Tony"}
    
    #Act
    servidor.broadcast("Hola",emisor)

    #Assert
    assert otro1.enviados == [b"Hola"]
    assert otro2.enviados == [b"Hola"]
    assert emisor.enviados == []


def test_broadcast_desconecta_al_cliente_que_falla(servidor, monkeypatch):

    # Arrange
    monkeypatch.setattr(servidor, "guardar_log", lambda mensaje: None)
    emisor, roto, sano = SocketFalso(), SocketFalso(falla=True), SocketFalso()
    servidor.clientes = {emisor: "Diana", roto: "Bruce", sano: "Clark"}
    
    # Act
    servidor.broadcast("hola", emisor)
    
    # Assert
    assert roto not in servidor.clientes
    assert roto.cerrado
    assert b"hola" in sano.enviados


def test_desconectar_cliente(servidor,monkeypatch):

    monkeypatch.setattr(servidor, "guardar_log", lambda mensaje: None)
    cliente1, roto, cliente2 = SocketFalso(), SocketFalso(), SocketFalso()
    servidor.clientes = {cliente1: "Wally", roto: "Hal", cliente2: "John"}

    servidor.desconectar_cliente(roto)

    assert roto not in servidor.clientes


def test_desconectar_cliente_que_ya_no_esta(servidor, monkeypatch):
    
    # Arrange
    monkeypatch.setattr(servidor, "guardar_log", lambda mensaje: None)
    cliente1, cliente2, ausente = SocketFalso(), SocketFalso(), SocketFalso()
    servidor.clientes = {cliente1: "Wally", cliente2: "John"}
    # `ausente` nunca se agregó al diccionario, así que "ya no está"

    # Act
    servidor.desconectar_cliente(ausente)

    # Assert
    assert ausente not in servidor.clientes
    assert len(servidor.clientes) == 2
    assert not ausente.cerrado
    assert cliente1.enviados == []
    assert cliente2.enviados == []