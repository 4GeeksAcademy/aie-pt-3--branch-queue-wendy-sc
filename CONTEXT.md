# CONTEXT --- Branch Queue — Gestor de Cola por Servicio

Banco Meridional ha modernizado sus sucursales — los clientes toman un ticket numerado en la entrada y esperan sentados. Cada ticket está etiquetado con un tipo de servicio: depósitos, retiros o gestión de cuenta. La sucursal cuenta con agentes dedicados a cada tipo de servicio, y trabajan de forma independiente: el agente de depósitos llama a su siguiente cliente sin importar lo que esté haciendo el agente de retiros.

La responsable de operaciones ha detectado un problema con el sistema en papel actual: cuando el agente de depósitos termina con un cliente y las únicas personas esperando son de retiros, el agente de depósitos se queda sin hacer nada aunque pudiera haber un cliente de depósitos que llegó antes pero está enterrado en la lista general. La sucursal necesita un sistema donde cada agente pueda llamar al siguiente cliente al instante, sin tener que recorrer toda la sala de espera.

El equipo de IT ha recibido el encargo de construir un gestor de colas en terminal para modelar este sistema antes de integrarlo en los quioscos táctiles de la sucursal.

## Ticket recibido

El documento de requisitos de la responsable de operaciones dice lo siguiente:

### Emisión de tickets
- Un cliente toma un ticket especificando un **tipo de servicio**: `deposito`, `retiro` o `gestion_cuenta`.
- El ticket debe registrar el nombre del cliente, el tipo de servicio y el momento de llegada.
- Los tickets se numeran de forma secuencial a partir del 1 (contador global, entre todos los servicios).

### Operaciones de los agentes
- Cada agente está asignado a exactamente un tipo de servicio.
- Cuando un agente queda libre, **llama al siguiente cliente de su cola de servicio** — el que lleva más tiempo esperando para ese tipo de servicio.
- Un agente no puede llamar a un cliente de una cola de servicio diferente.

### Operaciones requeridas del sistema
- Emitir ticket: registrar un nuevo cliente en la cola de servicio correspondiente.
- Llamar al siguiente: dado un tipo de servicio, desencolar y devolver el siguiente cliente que espera por él.
- Peek siguiente: mostrar quién es el siguiente para un tipo de servicio sin retirarlo.
- Listar en espera: mostrar todos los clientes en espera, agrupados por tipo de servicio, en el orden en que serán atendidos dentro de cada grupo.
- Stats globales: reportar el número de clientes en espera por tipo de servicio y en total.

## Objetivo

Piensa con cuidado cómo estructurar las colas internamente. Una única lista ordenada de todos los clientes requeriría recorrerla entera cada vez que un agente llama a su siguiente cliente — lo que se vuelve lento a medida que la sucursal se llena. Hay una estructura más simple que hace que la operación `llamar al siguiente` de cada agente sea instantánea, sin importar cuántas personas esperen para otros servicios. ¿Cuál es?