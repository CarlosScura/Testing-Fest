# Hallazgos durante los tests:

- El `log.txt` se escribe durante los tests de integración, por una carrera entre el hilo del servidor y el final del test.
- El servidor acepta clientes con nombre vacío.
- Problema de `test_varios_mensajes_llegan_en_orden_sin_perderse`:
    1. *Qué se probó:* Dinah envía tres mensajes seguidos y Oliver debería recibirlos separados, una vez cada uno y en orden.
    2. *Resultado esperado y obtenido:* Oliver recibió `[12:22] Dinah: uno[12:22] Dinah: dostres`.
    3. *Corridas:* el test falló en las tres, y los mensajes dos y tres llegaron juntos las tres veces. 
        Esto puede variar dependiendo de la velocidad de la maquina en la que corren los tests.
    4. *Causa:* TCP es un flujo de bytes sin límites entre mensajes, y el servidor lee con `recv(1024)` sin separar.
    5. *Decisión:* el test se marca como `xfail`, y el arreglo (delimitador `\n` y buffer por cliente, en servidor y cliente) queda para los requerimientos opcionales.  
- Un cliente que se conecta y no envía su nombre bloquea al servidor:
    1. *Qué se observó:* en `aceptar_conexion`, el servidor pone el socket del cliente nuevo en modo bloqueante y hace `recv` esperando el nombre, sin pasar por el selector y sin límite de tiempo.
    2. *Consecuencia:* mientras ese cliente no escriba nada ni cierre, el servidor no atiende a nadie más. Con un solo hilo, un bloqueo ahí frena todo.
    3. *Cómo se identificó:* leyendo el código; no hay un test que lo reproduzca.
    4. *Decisión:* queda como mejora posible para los requerimientos opcionales (por ejemplo, un `timeout` en esa espera o registrar al cliente en el selector antes de pedirle el nombre).

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