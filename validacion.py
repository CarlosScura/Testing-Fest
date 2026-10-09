MAX_LARGO = 300

class MensajeInvalido(Exception):
    pass

def validar_mensaje(texto):
    if texto.strip() == "":
        raise MensajeInvalido("Mensaje vacío")
    if len(texto) > MAX_LARGO:
        raise MensajeInvalido("Mensaje demasiado largo")
    return texto