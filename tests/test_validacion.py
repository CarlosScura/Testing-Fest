import pytest
from validacion import validar_mensaje, MensajeInvalido

def test_mensaje_valido_se_acepta():
    assert validar_mensaje("hola") == "hola"

def test_mensaje_vacio_se_rechaza():
    with pytest.raises(MensajeInvalido):
        validar_mensaje("")