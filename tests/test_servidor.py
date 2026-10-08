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
    