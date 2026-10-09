# Ciclo 1: : mensaje válido se acepta

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


# Ciclo 5: 

## RED

```

```

## GREEN

```

```

## REFACTOR

```

```
