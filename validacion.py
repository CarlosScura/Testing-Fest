class MensajeInvalido(Exception):
    pass

def validar_mensaje(texto):
    if texto.strip() == "":
        raise MensajeInvalido("Mensaje vacío")
    return texto
