# Branch Queue — Gestor de Cola por Servicio

Sistema de gestión de colas para sucursales bancarias **Banco Meridional**.

Cuando un cliente llega a la sucursal, toma un ticket numerado etiquetado con un
tipo de servicio: **depósito**, **retiro** o **gestión de cuenta**. Cada agente
está asignado a un único tipo de servicio y trabaja de forma independiente:
cuando queda libre, llama al siguiente cliente de *su* cola, sin tener que
recorrer toda la sala de espera.

Este proyecto implementa un gestor de colas en terminal que modela ese sistema
antes de integrarse en los quioscos táctiles de la sucursal.

---

## Características

- **Cola independiente por tipo de servicio** (`collections.deque`): `call_next`
  es O(1), instantáneo sin importar cuántas personas esperen para otros servicios.
- **Tickets globalmente secuenciales**: el número de ticket es único entre todos
  los servicios (contador global desde 1).
- **Orden estricto de llegada (FIFO)** dentro de cada cola de servicio.
- **Cinco operaciones de cola**: emisión, llamada, peek, listado y estadísticas.
- **Casos borde gestionados**: cola vacía y tipo de servicio inválido no rompen
  el programa.
- **CLI interactiva** con menú en bucle en español.
- **Solo biblioteca estándar de Python** — sin dependencias externas.

---

## Requisitos

- Python 3.8+ (fechas con zona horaria UTC, `frozenset`, `dataclasses`).
- No requiere instalar ningún paquete externo.

---

## Cómo ejecutar

### CLI interactiva

Desde la raíz del proyecto:

```bash
python3 branch_queue.py
```

Se abre un menú con las siguientes opciones:

```
========================================================
  BANCO MERIDIONAL — Gestor de Cola por Servicio
========================================================

    1. Emitir un nuevo ticket
    2. Llamar al siguiente cliente
    3. Ver la lista de espera
    4. Ver estadísticas de la cola
    5. Salir

  Seleccione una opción [1-5]:
```

### Uso programático

```python
from branch_queue import BranchQueue, QueueError

bq = BranchQueue()

# Emitir tickets (los números son globalmente secuenciales)
t1 = bq.issue_ticket("Alice", "deposito")       # #1
t2 = bq.issue_ticket("Bob", "retiro")           # #2
t3 = bq.issue_ticket("Carlos", "deposito")      # #3

# Ver quién sigue sin retirarlo
bq.peek_next("deposito")                        # #1 Alice

# Llamar al siguiente cliente de un servicio
siguiente = bq.call_next("deposito")            # #1 Alice

# Listar la espera agrupada por servicio
bq.list_waiting()

# Estadísticas
bq.stats()                                      # {'deposito': 1, 'retiro': 1,
                                                #  'gestion_cuenta': 0, 'total': 2}

# Los errores son descriptivos y no rompen el flujo
try:
    bq.call_next("gestion_cuenta")              # cola vacía
except QueueError as e:
    print(e)                                    # No hay clientes esperando para 'gestion_cuenta'.
```

---

## Referencia de la API

### `Ticket`

Dataclass que representa un ticket emitido.

| Campo | Tipo | Descripción |
|---|---|---|
| `number` | `int` | Número de ticket, global y secuencial. |
| `client_name` | `str` | Nombre del cliente. |
| `service_type` | `str` | `"deposito"`, `"retiro"` o `"gestion_cuenta"`. |
| `issued_at` | `datetime` | Momento de emisión (UTC). |

### `BranchQueue`

| Método | Firma | Descripción |
|---|---|---|
| `issue_ticket` | `(client_name: str, service_type: str) -> Ticket` | Crea, numera y encola un ticket. Lanza `QueueError` si el tipo es inválido. |
| `call_next` | `(service_type: str) -> Ticket` | Desencola y devuelve el siguiente cliente del servicio. **O(1)**. Lanza `QueueError` si el tipo es inválido o la cola está vacía. |
| `peek_next` | `(service_type: str) -> Optional[Ticket]` | Devuelve el siguiente cliente **sin retirarlo**; `None` si la cola está vacía. |
| `list_waiting` | `() -> Dict[str, List[Ticket]]` | Devuelve los tickets en espera agrupados por servicio, en orden FIFO. Devuelve una copia. |
| `stats` | `() -> Dict[str, int]` | Número de clientes en espera por servicio, más la clave `"total"`. |

### `QueueError`

Excepción lanzada ante errores de uso: tipo de servicio inválido o `call_next`
sobre una cola vacía.

---

## Estructura del proyecto

```
.
├── CONTEXT.md        # Contexto de negocio y requisitos (Banco Meridional)
├── DESIGN.md         # Notas de diseño y análisis de complejidad/concurrencia
├── README.md         # Este documento
└── branch_queue.py   # Implementación: modelo de datos, cola y CLI
```

---

## Notas de diseño

El análisis detallado, la justificación de la estructura por servicio y el
escenario de concurrencia de `call_next` se documentan en
[`DESIGN.md`](DESIGN.md). Resumen:

- **¿Por qué una cola por servicio y no una única lista?** Con una sola lista
  compartida, cada agente tendría que recorrerla entera (O(n)) para encontrar a
  su primer cliente. Con un `deque` por servicio, `call_next` es `popleft()`
  sobre la cola del propio agente: **O(1)** e independiente del tamaño total de
  la sucursal.
- **¿Qué pasa si dos agentes llaman a `call_next` a la vez?** La mutación
  crítica es el **desencolado atómico** (`popleft()`). En este CLI secuencial el
  GIL de Python lo garantiza; en un entorno multihilo real se protegería con un
  `threading.Lock`. Las colas separadas, además, eliminan la contención entre
  agentes de distintos servicios.

---

## Verificación

El módulo compila sin warnings:

```bash
python3 -W error -m py_compile branch_queue.py
```

Los casos de uso y casos borde pueden verificarse de forma programática
importando las clases, como se muestra en la sección *Uso programático*.

---

## Licencia

Proyecto educativo de ejemplo. Banco Meridional es un caso ficticio.