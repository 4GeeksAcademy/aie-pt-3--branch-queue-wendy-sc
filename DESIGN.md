# Design Notes — Branch Queue

## 1. Cola separada por tipo de servicio

### Problema de una cola única compartida

Si todos los clientes compartieran una única cola ordenada por orden de llegada,
cuando el agente de *depósitos* quiere llamar a su siguiente cliente tendría que
recorrer la cola desde el principio hasta encontrar el primer cliente con
`service_type == "deposito"`. En el peor caso — muchos clientes de retiros y
gestión de cuenta delante — el agente recorrería cientos de tickets antes de
encontrar al suyo, haciendo que la operación sea **O(n)** respecto del total
de clientes en la sucursal.

### Solución: una cola (`deque`) por tipo de servicio

```
cola_depositos:       [Alice, Charlie, ...]
cola_retiros:         [Bob, Eve, ...]
cola_gestion_cuenta:  [Diana, ...]
```

Cada agente opera **exclusivamente sobre su propia cola**. Cuando el agente de
depósitos queda libre, hace `call_next("deposito")`, que es simplemente un
`popleft()` sobre un `collections.deque` — una operación **O(1)**, sin importar
cuántos clientes estén esperando para otros servicios. La estructura es, por
tanto, **escalable**: el coste de llamar al siguiente cliente es constante e
independiente del tamaño total de la sucursal.

Además, el diseño con colas separadas:
- **Respeta el orden de llegada** dentro de cada servicio (FIFO por `deque`).
- **Aísla el trabajo** de cada agente: un agente de depósitos no puede
  accidentalmente llamar a un cliente de retiros.
- **Es sencillo de implementar** sin dependencias externas.

---

## 2. Concurrencia: dos agentes del mismo servicio llaman a `call_next` simultáneamente

### El escenario

Supongamos dos agentes de *depósitos* (A1 y A2) que terminan su atención al
mismo tiempo y ambos ejecutan `call_next("deposito")` de forma concurrente.

### Qué mutación debe ocurrir primero

Para garantizar que **el mismo cliente no sea llamado dos veces**, la operación
crítica es el **desencolado** (la mutación de la cola). Dado que
`BranchQueue.call_next()` ejecuta internamente:

```python
return self._queues[service_type].popleft()
```

la operación `popleft()` debe ocurrir **de forma atómica**: el deque debe
eliminar y devolver el primer elemento antes de que el segundo agente pueda
siquiera leer el estado de la cola.

En un entorno **monohilo** (como este CLI), los dos agentes no pueden ejecutar
`call_next` al mismo tiempo real; el GIL de Python serializa los accesos. El
segundo agente simplemente encontrará la cola vacía (o con el siguiente cliente,
si aún quedan).

En un entorno **multihilo** o **multiproceso real** (por ejemplo, si la
sucursal integrara el sistema en quioscos táctiles con agentes ejecutándose en
hilos separados), sería necesario proteger la operación `popleft()` con un
mecanismo de exclusión mutua (como `threading.Lock`). El diseño actual no
incluye locks porque no son necesarios en un programa secuencial, pero la
arquitectura de colas separadas por servicio **reduce drásticamente la
contención**: dos agentes de distinto servicio nunca compiten por la misma cola,
por lo que podrían operar en paralelo sin bloquearse mutuamente.

### Resumen

| Condición | Consecuencia |
|-----------|-------------|
| `popleft()` ejecutado atómicamente | Cada cliente se desencola exactamente una vez |
| Colas separadas por servicio | Agentes de distintos servicios nunca compiten por la misma cola |
| Sin locks en modo secuencial | El GIL y el bucle single-threaded garantizan la atomicidad |