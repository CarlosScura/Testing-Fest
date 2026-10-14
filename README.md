# Testing Fest

Suite de pruebas automatizadas para un chat multicliente en terminal escrito con sockets en Python. El objetivo no es solo "tener tests", sino comprobar que el servidor se comporta bien cuando hay varios clientes a la vez y cuando alguno se cae sin avisar, y dejar documentado lo que las pruebas descubren. Challenge de CodePRO (Penguin Academy).

El código del chat (`servidor.py`, `cliente.py` y `conexion.py`) proviene de [conexion-0](https://github.com/CarlosScura/conexion-0) y se copió sin cambios para escribir los tests sobre él.

## Metodología

- **Pruebas unitarias:** las funciones críticas del servidor (`broadcast` y `desconectar_cliente`) se prueban de forma aislada, con sockets falsos, sin red.
- **TDD:** se agregó un módulo nuevo, `validacion.py`, que valida los mensajes del chat (rechaza los vacíos, los de solo espacios y los de más de 300 caracteres). Se desarrolló en cuatro ciclos Red, Green y Refactor, uno por regla.
- **Pruebas de integración:** el servidor real se levanta en un hilo aparte, en un puerto libre, y se conectan clientes reales para comprobar el reparto de mensajes, el envío simultáneo de varios clientes y que el emisor no recibe su propio mensaje.
- **Desconexiones:** se simulan clientes que se van con un cierre normal y clientes que se caen de golpe (un reset de conexión), y se verifica que el servidor sigue funcionando y que los demás clientes no se ven afectados.
- **Los tests también se prueban a ellos mismos:** para varios tests se rompió el código a propósito y se confirmó que el test fallaba por el motivo esperado.
- **Cobertura:** medida con `pytest-cov`, con una meta mínima del 80%.

Todo el registro (pruebas, resultados, experimentos y decisiones) está en `pruebas.md`.

## Estructura del repo

```
Testing-Fest/
├── servidor.py          # Servidor del chat (de conexion-0)
├── cliente.py           # Cliente del chat (de conexion-0)
├── conexion.py          # Host, puerto y constantes compartidas
├── validacion.py        # Validación de mensajes (desarrollada con TDD)
├── tests/
│   ├── test_servidor.py     # Pruebas unitarias del servidor
│   ├── test_validacion.py   # Pruebas unitarias y TDD de la validación
│   └── test_integracion.py  # Servidor real con varios clientes
├── pytest.ini           # Configuración de pytest y cobertura
├── pruebas.md           # Registro de pruebas, resultados y decisiones
└── README.md
```

## Resultados

- **19 tests:** 18 pasan y 1 está marcado como fallo esperado (`xfail`), porque documenta un problema conocido del servidor (ver Hallazgos).
- **Cobertura:** 87% sobre `servidor.py` y `validacion.py`. `cliente.py` no se midió porque no tiene tests propios.

## Hallazgos

Las pruebas encontraron comportamientos del servidor que no se corrigieron. Cada uno está documentado con más detalle en `pruebas.md`.

- **Los mensajes consecutivos del mismo emisor se pegan.** TCP no conserva los límites entre mensajes y el servidor lee con `recv(1024)` sin separarlos: mensajes seguidos pueden llegar fusionados. El test que lo muestra está marcado como `xfail`. Posible arreglo: terminar cada mensaje con `\n` y acumular los bytes en un buffer por cliente.
- **El servidor acepta clientes con nombre vacío.** Posible arreglo: validar el nombre al conectarse.
- **Un cliente que se conecta y no envía su nombre bloquea al servidor.** Se identificó leyendo el código, sin un test que lo reproduzca. Posible arreglo: un `timeout` en esa espera.
- **El `log.txt` se escribe durante los tests de integración.** La causa es probable pero no está comprobada: el servidor se entera de la salida de un cliente un instante después de terminar el test.
- **`cliente.py` no tiene tests.** Depende de `input()`, de dos hilos en bucle y de una espera de 5 segundos al reconectar, por lo que probarlo requiere reemplazar esas partes.

## Tecnologías

Python · pytest · pytest-cov · socket · selectors · threading

## Cómo correrlo

Preparar el entorno (Linux):

```
python3 -m venv .venv
source .venv/bin/activate
pip install pytest pytest-cov
```

Correr todos los tests, con cobertura:

```
pytest
```

La configuración de `pytest.ini` agrega la cobertura sobre `servidor.py` y `validacion.py`, y hace que la ejecución falle si la cobertura total baja del 80%. Tarda unos 16 segundos, porque los tests de integración esperan a que el servidor responda. Al final se ve:

```
18 passed, 1 xfailed
Required test coverage of 80% reached. Total coverage: 87.37%
```

Correr un solo test (hay que desactivar la cobertura; con un test suelto cae por debajo del 80% y la ejecución termina en error aunque el test pase):

```
pytest -k nombre_del_test --no-cov
```

Ver el detalle de cada test y el motivo del fallo esperado:

```
pytest -v -rx
```

## Autor

Fede Alarcón Scura — Estudiante de Penguin Academy
Challenge desarrollado como parte del programa de formación.