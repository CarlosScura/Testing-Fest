# Hallazgos durante los tests:

- El `log.txt` se escribe durante los tests de integración. Causa probable (hipótesis, no comprobada): una carrera entre el hilo del servidor y el final del test. Cuando el cliente cierra su socket, el servidor se entera un instante después, cuando el `monkeypatch` que silencia `guardar_log` ya se deshizo, y escribe la salida con el `guardar_log` real. En el archivo solo aparecieron avisos de salida ("abandonó el chat"), ninguno de entrada ni mensajes, lo que encaja con esa explicación.
- El servidor acepta clientes con nombre vacío. Se detectó al revisar `log.txt`: aparecían líneas ` abandonó el chat.` sin nombre. Probablemente vienen de `test_cliente_recibe_pedido_de_nombre`, que se conecta y se va sin enviar nombre (no se comprobó con otro test). `aceptar_conexion` guarda como nombre lo que devuelva `recv`, aunque sea vacío.
- Problema de `test_varios_mensajes_llegan_en_orden_sin_perderse`:
    1. *Qué se probó:* Dinah envía tres mensajes seguidos y Oliver debería recibirlos separados, una vez cada uno y en orden.
    2. *Resultado esperado y obtenido:* Oliver recibió `[12:22] Dinah: uno[12:22] Dinah: dostres`.
    3. *Corridas:* el test falló en las tres, y los mensajes dos y tres llegaron juntos las tres veces. 
        Esto puede variar dependiendo de la velocidad de la maquina en la que corren los tests.
    4. *Causa:* TCP es un flujo de bytes sin límites entre mensajes, y el servidor lee con `recv(1024)` sin separar.
    5. *Decisión:* el test se marca como `xfail`, y el arreglo (delimitador `\n` y buffer por cliente, en servidor y cliente) queda para los requerimientos opcionales. El test se marcó con `@pytest.mark.xfail` (con `strict=False`, el valor por defecto, para que no rompa la suite si pasa de casualidad según los tiempos de la máquina).
- Un cliente que se conecta y no envía su nombre bloquea al servidor:
    1. *Qué se observó:* en `aceptar_conexion`, el servidor pone el socket del cliente nuevo en modo bloqueante y hace `recv` esperando el nombre, sin pasar por el selector y sin límite de tiempo.
    2. *Consecuencia:* mientras ese cliente no escriba nada ni cierre, el servidor no atiende a nadie más. Con un solo hilo, un bloqueo ahí frena todo.
    3. *Cómo se identificó:* leyendo el código; no hay un test que lo reproduzca.
    4. *Decisión:* queda como mejora posible para los requerimientos opcionales (por ejemplo, un `timeout` en esa espera o registrar al cliente en el selector antes de pedirle el nombre).

# Pruebas unitarias del servidor

Tests: `test_servidor_nuevo_no_tiene_clientes`, `test_broadcast_envia_a_todos_menos_al_emisor`, `test_broadcast_desconecta_al_cliente_que_falla`, `test_desconectar_cliente` y `test_desconectar_cliente_que_ya_no_esta`.

1. *Qué se probó:* las funciones críticas del servidor de forma aislada: `broadcast` (reparte a todos menos al emisor y desconecta a quien falla) y `desconectar_cliente` (saca al cliente del diccionario, cierra su socket, avisa a los demás y no hace nada si el cliente ya no está). Se usa un `SocketFalso` con `send` y `close` (y una opción para que `send` falle), una fixture `servidor` con `yield` que cierra el socket aunque el test falle, y `monkeypatch` para que `guardar_log` no escriba en el archivo.
2. *Resultado:* los cinco tests pasaron con el servidor original.
3. *Comprobación de que los tests pueden fallar:*
    - Comenté `del self.clientes[cliente_socket]` en `desconectar_cliente`. Fallaron `test_desconectar_cliente` (el cliente seguía en el diccionario) y `test_broadcast_desconecta_al_cliente_que_falla` (`RecursionError`).
    - Comenté el `if cliente_socket not in self.clientes: return`. Falló `test_desconectar_cliente_que_ya_no_esta` con `assert not True` sobre `ausente.cerrado`.
4. *Observación:* el `RecursionError` confirma la decisión técnica del README: borrar al cliente del diccionario antes de notificar evita el bucle entre `broadcast` y `desconectar_cliente`. En el test de `broadcast`, el cliente sano recibe el mensaje y también el aviso de salida del que falló, por eso el assert usa `in` y no `==`.
5. *Decisión:* los tests quedan como están. Para probar sin red se usan sockets falsos, y la cobertura de lo que depende de sockets reales queda a cargo de las pruebas de integración.

# Pruebas de integración: conexión y mensajes

Tests: `test_cliente_recibe_pedido_de_nombre`, `test_cliente_recibe_aviso_de_que_se_unio`, `test_mensaje_de_un_cliente_llega_al_otro` y `test_emisor_no_recibe_su_propio_mensaje`.

1. *Qué se probó:* el servidor real, levantado en un hilo aparte con puerto `0` (el sistema asigna uno libre) mediante la fixture `servidor_real`, con clientes que son sockets reales. Se comprueba que el servidor pide el nombre, que avisa cuando alguien se une, que el mensaje de un cliente llega a otro y que el emisor no recibe su propio mensaje. Los `recv` sin asignar a una variable sirven para vaciar los avisos que no interesan en cada test.
2. *Resultado:* los cuatro tests pasaron con el servidor original.
3. *Comprobación de que los tests pueden fallar:*
    - Cambié el texto "Ingresa tu nombre: " del servidor: falló `test_cliente_recibe_pedido_de_nombre`.
    - En `recibir_mensaje` cambié el emisor del `broadcast` a `None`: `test_mensaje_de_un_cliente_llega_al_otro` siguió pasando y `test_emisor_no_recibe_su_propio_mensaje` falló, porque el emisor recibió su propio mensaje.
4. *Observación:* el experimento con `None` mostró un hueco: comprobar que el receptor recibe no alcanza para probar que el emisor no recibe. Por eso se agregó el test del emisor, que espera con un timeout corto y pasa si `recv` se rinde sin recibir nada. Antes de revisar la bandeja del emisor, el test espera a que el otro cliente reciba el mensaje, para no mirar demasiado temprano y pasar por la razón equivocada.
5. *Decisión:* los tests quedan como están.

# Pruebas de integración: desconexiones

Tests: `test_cliente_que_se_va_no_afecta_a_los_demas`, `test_al_irse_un_cliente_los_demas_reciben_aviso_y_sale_de_la_lista` y `test_caida_abrupta_no_afecta_a_los_demas`.

1. *Qué se probó:* un cliente se va con un cierre normal (`close()`) y otro con una caída abrupta (un reset de conexión, con `SO_LINGER` configurado con `struct.pack("ii", 1, 0)`). En ambos casos los demás clientes reciben el aviso de salida, el cliente desaparece de `servidor.clientes` (con una espera hasta que se cumpla, porque el servidor se entera en su propio hilo) y el servidor sigue repartiendo mensajes.
2. *Resultado:* los tres tests pasaron con el servidor original.
3. *Comprobación de que los tests pueden fallar:*
    - Comenté en `desconectar_cliente` la línea del aviso de salida: falló el assert del aviso, y no el de la lista.
    - Agregué temporalmente un `print` en el `except` de `recibir_mensaje` y corrí el test de la caída abrupta: el texto apareció, así que la caída abrupta entra por el `except` (excepción por el reset) y el cierre normal por el `else` (bytes vacíos). Después saqué el `print`.
4. *Observación:* los dos caminos de `recibir_mensaje` terminan en `desconectar_cliente` y dejan el mismo resultado visible para los demás clientes, por lo que el test por sí solo no distingue por cuál entró. Esa información la dio el `print`.
5. *Decisión:* los tests quedan como están.

# Prueba de integración: varios clientes envían a la vez

Test: `test_varios_clientes_envian_a_la_vez`

1. *Qué se probó:* tres clientes (Clark, Bruce y Diana) envían un mensaje cada uno al mismo tiempo, usando un hilo por cliente y una `threading.Barrier` para que salgan juntos. Cada cliente debe recibir el mensaje de los otros dos exactamente una vez, y nunca el propio.
2. *Resultado:* el test pasó con el servidor original.
3. *Comprobación de que el test puede fallar:* en `recibir_mensaje` cambié el emisor del `broadcast` a `None`, para que el servidor le mande el mensaje a todos, incluido el emisor. El test falló en `assert 'Diana: mensaje de Diana' not in ...`, porque Diana recibió su propio mensaje. Después deshice el cambio y volvió a pasar.
4. *Observación:* la salida del fallo mostró los tres mensajes pegados en una sola cadena: `[18:04] Clark: mensaje de Clark[18:04] Bruce: mensaje de Bruce[18:04] Diana: mensaje de Diana`. Es la misma causa del hallazgo de `test_varios_mensajes_llegan_en_orden_sin_perderse`: TCP no conserva los límites entre mensajes y el `recv(1024)` los lee juntos. El test no depende de eso porque cuenta cuántas veces aparece cada mensaje (`count`) en lo recibido y no compara contra mensajes separados.
5. *Decisión:* el test queda como está. El arreglo del protocolo (delimitador `\n` y buffer por cliente) sigue pendiente para los requerimientos opcionales.

# Prueba de integración: varias caídas abruptas seguidas

Test: `test_varias_caidas_abruptas_seguidas`

1. *Qué se probó:* tres clientes (Diana, Bruce y Clark) se conectan, y Bruce y Clark se caen de golpe, uno justo después del otro, con un reset de conexión (`SO_LINGER` con tiempo 0). Diana tiene que recibir un aviso de cada uno, exactamente una vez, y el servidor tiene que seguir funcionando: un cliente nuevo (Jonn) se conecta y recibe un mensaje de Diana.
2. *Resultado:* el test pasó con el servidor original.
3. *Comprobación de que el test puede fallar:* en `desconectar_cliente` comenté el `if cliente_socket not in self.clientes: return`. Falló `test_desconectar_cliente_que_ya_no_esta` (el test unitario), con `assert not True` en `ausente.cerrado`. El test de integración siguió pasando.
4. *Observación:* sin esa protección, la segunda llamada para un cliente ya borrado no avisa ni borra nada de nuevo, porque el resto de la función está dentro de otro `if`. Lo único que hace de más es llamar otra vez a `close()`, y cerrar dos veces un socket real no da error. Por eso solo el test unitario, que usa un socket falso con un atributo `cerrado`, lo detecta. Cada tipo de test protege algo distinto: el unitario ve efectos internos y el de integración ve lo que vería un cliente real.
5. *Decisión:* el test queda como está. La protección se mantiene en el código y está sostenida por el test unitario.

# Ciclo 1: mensaje válido se acepta

## RED

Test agregado: `test_mensaje_valido_se_acepta`. Falla porque el módulo `validacion` no existe.

```
================================================================= test session starts ==================================================================
platform linux -- Python 3.13.15, pytest-9.1.1, pluggy-1.6.0
rootdir: /home/fedev/Documentos/Proyectos/CodePro/Testing-Fest
configfile: pytest.ini
testpaths: tests
collected 5 items / 1 error                                                                                                                            

======================================================================== ERRORS ========================================================================
______________________________________________________ ERROR collecting tests/test_validacion.py _______________________________________________________
ImportError while importing test module '/home/fedev/Documentos/Proyectos/CodePro/Testing-Fest/tests/test_validacion.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.13/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/test_validacion.py:2: in <module>
    from validacion import validar_mensaje, MensajeInvalido
E   ModuleNotFoundError: No module named 'validacion'
=============================================================== short test summary info ================================================================
ERROR tests/test_validacion.py
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
=================================================================== 1 error in 0.16s ===================================================================
```


## GREEN

Código agregado: `validacion.py` con la clase `MensajeInvalido` y `validar_mensaje` que devuelve el texto sin validar nada.

```
======================================================= test session starts =======================================================
platform linux -- Python 3.13.15, pytest-9.1.1, pluggy-1.6.0 -- /home/fedev/Documentos/Proyectos/CodePro/Testing-Fest/.venv/bin/python3
cachedir: .pytest_cache
rootdir: /home/fedev/Documentos/Proyectos/CodePro/Testing-Fest
configfile: pytest.ini
testpaths: tests
collected 6 items                                                                                                                 

tests/test_servidor.py::test_servidor_nuevo_no_tiene_clientes PASSED                                                        [ 16%]
tests/test_servidor.py::test_broadcast_envia_a_todos_menos_al_emisor PASSED                                                 [ 33%]
tests/test_servidor.py::test_broadcast_desconecta_al_cliente_que_falla PASSED                                               [ 50%]
tests/test_servidor.py::test_desconectar_cliente PASSED                                                                     [ 66%]
tests/test_servidor.py::test_desconectar_cliente_que_ya_no_esta PASSED                                                      [ 83%]
tests/test_validacion.py::test_mensaje_valido_se_acepta PASSED                                                              [100%]

======================================================== 6 passed in 0.02s ========================================================
```


# Ciclo 2: mensaje vacío se rechaza

## RED

Test agregado: `test_mensaje_vacio_se_rechaza`.

```
===================================================================== test session starts =====================================================================
platform linux -- Python 3.13.15, pytest-9.1.1, pluggy-1.6.0 -- /home/fedev/Documentos/Proyectos/CodePro/Testing-Fest/.venv/bin/python3
cachedir: .pytest_cache
rootdir: /home/fedev/Documentos/Proyectos/CodePro/Testing-Fest
configfile: pytest.ini
testpaths: tests
collected 7 items                                                                                                                                             

tests/test_servidor.py::test_servidor_nuevo_no_tiene_clientes PASSED                                                                                    [ 14%]
tests/test_servidor.py::test_broadcast_envia_a_todos_menos_al_emisor PASSED                                                                             [ 28%]
tests/test_servidor.py::test_broadcast_desconecta_al_cliente_que_falla PASSED                                                                           [ 42%]
tests/test_servidor.py::test_desconectar_cliente PASSED                                                                                                 [ 57%]
tests/test_servidor.py::test_desconectar_cliente_que_ya_no_esta PASSED                                                                                  [ 71%]
tests/test_validacion.py::test_mensaje_valido_se_acepta PASSED                                                                                          [ 85%]
tests/test_validacion.py::test_mensaje_vacio_se_rechaza FAILED                                                                                          [100%]

========================================================================== FAILURES ===========================================================================
________________________________________________________________ test_mensaje_vacio_se_rechaza ________________________________________________________________

    def test_mensaje_vacio_se_rechaza():
>       with pytest.raises(MensajeInvalido):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE MensajeInvalido

tests/test_validacion.py:8: Failed
=================================================================== short test summary info ===================================================================
FAILED tests/test_validacion.py::test_mensaje_vacio_se_rechaza - Failed: DID NOT RAISE MensajeInvalido
================================================================= 1 failed, 6 passed in 0.05s =================================================================
```

## GREEN

Código agregado: `if texto == "": raise MensajeInvalido("Mensaje vacío")`.

```
======================================================= test session starts =======================================================
platform linux -- Python 3.13.15, pytest-9.1.1, pluggy-1.6.0 -- /home/fedev/Documentos/Proyectos/CodePro/Testing-Fest/.venv/bin/python3
cachedir: .pytest_cache
rootdir: /home/fedev/Documentos/Proyectos/CodePro/Testing-Fest
configfile: pytest.ini
testpaths: tests
collected 7 items                                                                                                                 

tests/test_servidor.py::test_servidor_nuevo_no_tiene_clientes PASSED                                                        [ 14%]
tests/test_servidor.py::test_broadcast_envia_a_todos_menos_al_emisor PASSED                                                 [ 28%]
tests/test_servidor.py::test_broadcast_desconecta_al_cliente_que_falla PASSED                                               [ 42%]
tests/test_servidor.py::test_desconectar_cliente PASSED                                                                     [ 57%]
tests/test_servidor.py::test_desconectar_cliente_que_ya_no_esta PASSED                                                      [ 71%]
tests/test_validacion.py::test_mensaje_valido_se_acepta PASSED                                                              [ 85%]
tests/test_validacion.py::test_mensaje_vacio_se_rechaza PASSED                                                              [100%]

======================================================== 7 passed in 0.01s ========================================================
```


# Ciclo 3: mensaje de solo espacios se rechaza

## RED

Test agregado: `test_mensaje_solo_espacios_se_rechaza`.

```
======================================================= test session starts =======================================================
platform linux -- Python 3.13.15, pytest-9.1.1, pluggy-1.6.0 -- /home/fedev/Documentos/Proyectos/CodePro/Testing-Fest/.venv/bin/python3
cachedir: .pytest_cache
rootdir: /home/fedev/Documentos/Proyectos/CodePro/Testing-Fest
configfile: pytest.ini
testpaths: tests
collected 8 items                                                                                                                 

tests/test_servidor.py::test_servidor_nuevo_no_tiene_clientes PASSED                                                        [ 12%]
tests/test_servidor.py::test_broadcast_envia_a_todos_menos_al_emisor PASSED                                                 [ 25%]
tests/test_servidor.py::test_broadcast_desconecta_al_cliente_que_falla PASSED                                               [ 37%]
tests/test_servidor.py::test_desconectar_cliente PASSED                                                                     [ 50%]
tests/test_servidor.py::test_desconectar_cliente_que_ya_no_esta PASSED                                                      [ 62%]
tests/test_validacion.py::test_mensaje_valido_se_acepta PASSED                                                              [ 75%]
tests/test_validacion.py::test_mensaje_vacio_se_rechaza PASSED                                                              [ 87%]
tests/test_validacion.py::test_mensaje_solo_espacios_se_rechaza FAILED                                                      [100%]

============================================================ FAILURES =============================================================
______________________________________________ test_mensaje_solo_espacios_se_rechaza ______________________________________________

    def test_mensaje_solo_espacios_se_rechaza():
>       with pytest.raises(MensajeInvalido):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE MensajeInvalido

tests/test_validacion.py:12: Failed
===================================================== short test summary info =====================================================
FAILED tests/test_validacion.py::test_mensaje_solo_espacios_se_rechaza - Failed: DID NOT RAISE MensajeInvalido
=================================================== 1 failed, 7 passed in 0.05s ===================================================
```

## GREEN

Código modificado: la condición pasó a `texto.strip() == ""`. El mensaje se compara sin espacios, pero se devuelve tal cual lo escribió el usuario.

```
======================================================= test session starts =======================================================
platform linux -- Python 3.13.15, pytest-9.1.1, pluggy-1.6.0 -- /home/fedev/Documentos/Proyectos/CodePro/Testing-Fest/.venv/bin/python3
cachedir: .pytest_cache
rootdir: /home/fedev/Documentos/Proyectos/CodePro/Testing-Fest
configfile: pytest.ini
testpaths: tests
collected 8 items                                                                                                                 

tests/test_servidor.py::test_servidor_nuevo_no_tiene_clientes PASSED                                                        [ 12%]
tests/test_servidor.py::test_broadcast_envia_a_todos_menos_al_emisor PASSED                                                 [ 25%]
tests/test_servidor.py::test_broadcast_desconecta_al_cliente_que_falla PASSED                                               [ 37%]
tests/test_servidor.py::test_desconectar_cliente PASSED                                                                     [ 50%]
tests/test_servidor.py::test_desconectar_cliente_que_ya_no_esta PASSED                                                      [ 62%]
tests/test_validacion.py::test_mensaje_valido_se_acepta PASSED                                                              [ 75%]
tests/test_validacion.py::test_mensaje_vacio_se_rechaza PASSED                                                              [ 87%]
tests/test_validacion.py::test_mensaje_solo_espacios_se_rechaza PASSED                                                      [100%]

======================================================== 8 passed in 0.02s ========================================================
```

# Ciclo 4: mensaje demasiado largo se rechaza

## RED

Test agregado: `test_mensaje_demasiado_largo_se_rechaza`, con un mensaje de un caracter más que el límite de 300.

```
======================================================= test session starts =======================================================
platform linux -- Python 3.13.15, pytest-9.1.1, pluggy-1.6.0 -- /home/fedev/Documentos/Proyectos/CodePro/Testing-Fest/.venv/bin/python3
cachedir: .pytest_cache
rootdir: /home/fedev/Documentos/Proyectos/CodePro/Testing-Fest
configfile: pytest.ini
testpaths: tests
collected 9 items                                                                                                                 

tests/test_servidor.py::test_servidor_nuevo_no_tiene_clientes PASSED                                                        [ 11%]
tests/test_servidor.py::test_broadcast_envia_a_todos_menos_al_emisor PASSED                                                 [ 22%]
tests/test_servidor.py::test_broadcast_desconecta_al_cliente_que_falla PASSED                                               [ 33%]
tests/test_servidor.py::test_desconectar_cliente PASSED                                                                     [ 44%]
tests/test_servidor.py::test_desconectar_cliente_que_ya_no_esta PASSED                                                      [ 55%]
tests/test_validacion.py::test_mensaje_valido_se_acepta PASSED                                                              [ 66%]
tests/test_validacion.py::test_mensaje_vacio_se_rechaza PASSED                                                              [ 77%]
tests/test_validacion.py::test_mensaje_solo_espacios_se_rechaza PASSED                                                      [ 88%]
tests/test_validacion.py::test_mensaje_demasiado_largo_se_rechaza FAILED                                                    [100%]

============================================================ FAILURES =============================================================
_____________________________________________ test_mensaje_demasiado_largo_se_rechaza _____________________________________________

    def test_mensaje_demasiado_largo_se_rechaza():
>       with pytest.raises(MensajeInvalido):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE MensajeInvalido

tests/test_validacion.py:16: Failed
===================================================== short test summary info =====================================================
FAILED tests/test_validacion.py::test_mensaje_demasiado_largo_se_rechaza - Failed: DID NOT RAISE MensajeInvalido
=================================================== 1 failed, 8 passed in 0.05s ===================================================
```

## GREEN

Código agregado: `if len(texto) > 300: raise MensajeInvalido("Mensaje demasiado largo")`.

```
======================================================= test session starts =======================================================
platform linux -- Python 3.13.15, pytest-9.1.1, pluggy-1.6.0 -- /home/fedev/Documentos/Proyectos/CodePro/Testing-Fest/.venv/bin/python3
cachedir: .pytest_cache
rootdir: /home/fedev/Documentos/Proyectos/CodePro/Testing-Fest
configfile: pytest.ini
testpaths: tests
collected 9 items                                                                                                                 

tests/test_servidor.py::test_servidor_nuevo_no_tiene_clientes PASSED                                                        [ 11%]
tests/test_servidor.py::test_broadcast_envia_a_todos_menos_al_emisor PASSED                                                 [ 22%]
tests/test_servidor.py::test_broadcast_desconecta_al_cliente_que_falla PASSED                                               [ 33%]
tests/test_servidor.py::test_desconectar_cliente PASSED                                                                     [ 44%]
tests/test_servidor.py::test_desconectar_cliente_que_ya_no_esta PASSED                                                      [ 55%]
tests/test_validacion.py::test_mensaje_valido_se_acepta PASSED                                                              [ 66%]
tests/test_validacion.py::test_mensaje_vacio_se_rechaza PASSED                                                              [ 77%]
tests/test_validacion.py::test_mensaje_solo_espacios_se_rechaza PASSED                                                      [ 88%]
tests/test_validacion.py::test_mensaje_demasiado_largo_se_rechaza PASSED                                                    [100%]

======================================================== 9 passed in 0.01s ========================================================
```

## REFACTOR

Cambio: el 300 se extrajo a la constante `MAX_LARGO` en `validacion.py`. El test importa `MAX_LARGO` y usa `MAX_LARGO + 1`, así que siempre prueba justo por encima del límite aunque el valor cambie.

```
======================================================= test session starts =======================================================
platform linux -- Python 3.13.15, pytest-9.1.1, pluggy-1.6.0 -- /home/fedev/Documentos/Proyectos/CodePro/Testing-Fest/.venv/bin/python3
cachedir: .pytest_cache
rootdir: /home/fedev/Documentos/Proyectos/CodePro/Testing-Fest
configfile: pytest.ini
testpaths: tests
collected 9 items                                                                                                                 

tests/test_servidor.py::test_servidor_nuevo_no_tiene_clientes PASSED                                                        [ 11%]
tests/test_servidor.py::test_broadcast_envia_a_todos_menos_al_emisor PASSED                                                 [ 22%]
tests/test_servidor.py::test_broadcast_desconecta_al_cliente_que_falla PASSED                                               [ 33%]
tests/test_servidor.py::test_desconectar_cliente PASSED                                                                     [ 44%]
tests/test_servidor.py::test_desconectar_cliente_que_ya_no_esta PASSED                                                      [ 55%]
tests/test_validacion.py::test_mensaje_valido_se_acepta PASSED                                                              [ 66%]
tests/test_validacion.py::test_mensaje_vacio_se_rechaza PASSED                                                              [ 77%]
tests/test_validacion.py::test_mensaje_solo_espacios_se_rechaza PASSED                                                      [ 88%]
tests/test_validacion.py::test_mensaje_demasiado_largo_se_rechaza PASSED                                                    [100%]

======================================================== 9 passed in 0.01s ========================================================
```

## Decisión sobre el límite exacto

No se agregó un test que compruebe que un mensaje de exactamente 300 caracteres se acepta. El test del Ciclo 4 solo prueba que 301 se rechaza, y esa afirmación es cierta tanto con `> MAX_LARGO` como con `>= MAX_LARGO`. Se decidió no agregarlo porque el código ya deja el límite claro, y el enunciado pide casos positivos y negativos, que ya están cubiertos. Queda como mejora posible: un test de protección contra cambios futuros.

# COBERTURA

## cliente.py quedó fuera de la cobertura.

```
======================================================================== test session starts =========================================================================
platform linux -- Python 3.13.15, pytest-9.1.1, pluggy-1.6.0
rootdir: /home/carlos/Documentos/Penguin/CodePRO/Testing Fest/Testing-Fest
configfile: pytest.ini
testpaths: tests
plugins: cov-7.1.0
collected 19 items                                                                                                                                                   

tests/test_integracion.py ....x.....                                                                                                                           [ 52%]
tests/test_servidor.py .....                                                                                                                                   [ 78%]
tests/test_validacion.py ....                                                                                                                                  [100%]

=========================================================================== tests coverage ===========================================================================
__________________________________________________________ coverage: platform linux, python 3.13.15-final-0 __________________________________________________________

Name            Stmts   Miss  Cover   Missing
---------------------------------------------
servidor.py        86     12    86%   23-24, 127-137, 140-141
validacion.py       9      0   100%
---------------------------------------------
TOTAL              95     12    87%
=================================================================== 18 passed, 1 xfailed in 16.64s ===================================================================


```

# Cobertura de código

Comando: `pytest`

La configuración está en `pytest.ini` (`addopts = --cov=servidor --cov=validacion --cov-report=term-missing --cov-fail-under=80`), de modo que alcanza con un solo comando para correr todos los tests y la cobertura (requerimiento opcional 2). Para correr un solo test hay que agregar `--no-cov`; sin esa opción la ejecución falla porque la cobertura baja del 80%.

1. *Qué se midió:* qué porcentaje de las líneas de `servidor.py` y `validacion.py` ejecutan los tests. `cliente.py` (71 líneas ejecutables) y `conexion.py` quedaron fuera de la medición: `cliente.py` no tiene tests propios y `conexion.py` solo define constantes. Por eso el 87% corresponde únicamente a `servidor.py` y `validacion.py`.
2. *Resultado:* 87% en total, por encima de la meta del 80%.

    | Archivo | Líneas | Sin cubrir | Cobertura | Líneas sin cubrir |
    |---|---|---|---|---|
    | `servidor.py` | 86 | 12 | 86% | 23-24, 127-137, 140-141 |
    | `validacion.py` | 9 | 0 | 100% | — |
    | **Total** | 95 | 12 | 87% | |

3. *Qué quedó sin cubrir y por qué:*
    - Líneas 23-24: el caso de puerto ocupado en `establecer_conexion` (termina con `SystemExit`). Los tests usan el puerto `0`, que el sistema asigna libre, así que ese camino nunca se activa.
    - Líneas 127-141: el método `iniciar` y el bloque `if __name__ == "__main__"`. Los tests importan el archivo y llaman a `establecer_conexion` y `revisar_selectores` por separado, así que el arranque del programa no se ejecuta. Probarlo exigiría lanzar el servidor como proceso aparte, y el esfuerzo no compensa.
4. *Observación:* la cobertura mide qué líneas se ejecutaron, no si el resultado se verificó. Un ejemplo de este proyecto: con un solo test del borde del límite, la línea `len(texto) > MAX_LARGO` figuraría cubierta aunque estuviera escrita `>=` y rechazara mensajes de exactamente 300 caracteres. Por eso el número no reemplaza la revisión de los asserts.
5. *Decisión:* se mantiene el 87% sin sumar tests solo para subir el número. El caso del puerto ocupado queda como posible test adicional.
