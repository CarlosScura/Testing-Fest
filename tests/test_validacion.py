import pytest
from validacion import validar_mensaje, MensajeInvalido, MAX_LARGO

def test_mensaje_valido_se_acepta():
    assert validar_mensaje("hola") == "hola"

def test_mensaje_vacio_se_rechaza():
    with pytest.raises(MensajeInvalido):
        validar_mensaje("")

def test_mensaje_solo_espacios_se_rechaza():
    with pytest.raises(MensajeInvalido):
        validar_mensaje("   ")

def test_mensaje_demasiado_largo_se_rechaza():
    with pytest.raises(MensajeInvalido):
        validar_mensaje("a" * (MAX_LARGO+1) )