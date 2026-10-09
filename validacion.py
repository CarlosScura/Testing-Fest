class MensajeInvalido(Exception):
    pass

def validar_mensaje(texto):
    if texto.strip() == "":
        raise MensajeInvalido("Mensaje vacío")
    if len(texto) > 300:
        raise MensajeInvalido("Mensaje demasiado largo")
    return texto