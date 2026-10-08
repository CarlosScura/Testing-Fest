from servidor import server

def test_servidor_nuevo_no_tiene_clientes():
    # Arrange
    s = server("127.0.0.1", 5000)
    # Act
    cantidad = len(s.clientes)
    # Assert
    assert cantidad == 0
    s.server_socket.close()