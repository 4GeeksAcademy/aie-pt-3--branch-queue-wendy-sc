"""
branch_queue.py — Branch Queue: Gestor de Cola por Servicio

Banco Meridional — Sistema de gestión de colas para sucursales bancarias.
Usa únicamente la biblioteca estándar de Python.
"""

from __future__ import annotations

import sys
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Modelo de datos
# ---------------------------------------------------------------------------

VALID_SERVICE_TYPES = frozenset({"deposito", "retiro", "gestion_cuenta"})


@dataclass(order=True)
class Ticket:
    """Representa un ticket emitido a un cliente."""

    number: int
    client_name: str
    service_type: str
    issued_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        ts = self.issued_at.strftime("%H:%M:%S")
        return (
            f"Ticket(#{self.number:03d}, {self.client_name!r}, "
            f"{self.service_type}, {ts})"
        )

    def display(self) -> str:
        """Devuelve una cadena legible para el usuario."""
        ts = self.issued_at.strftime("%H:%M:%S")
        return f"[#{self.number:03d}] {self.client_name} — {self.service_type} ({ts})"


# ---------------------------------------------------------------------------
# Excepciones personalizadas
# ---------------------------------------------------------------------------


class QueueError(Exception):
    """Error relacionado con la cola de servicio."""


# ---------------------------------------------------------------------------
# BranchQueue — Gestor principal de colas por tipo de servicio
# ---------------------------------------------------------------------------


class BranchQueue:
    """Gestiona colas independientes por tipo de servicio y un contador
    global de tickets.

    Cada tipo de servicio tiene su propia cola (``collections.deque``) para
    que ``call_next()`` sea O(1) — no es necesario recorrer toda la sala de
    espera para encontrar al siguiente cliente de un servicio concreto.
    """

    def __init__(self) -> None:
        # Cola separada por tipo de servicio → deque ordenado FIFO
        self._queues: Dict[str, deque] = {
            st: deque() for st in VALID_SERVICE_TYPES
        }
        # Contador global secuencial (compartido por todos los servicios)
        self._counter: int = 0

    # -- Operaciones públicas ------------------------------------------------

    def issue_ticket(self, client_name: str, service_type: str) -> Ticket:
        """Crea un nuevo ticket y lo encola en la cola de servicio adecuada.

        Args:
            client_name: Nombre del cliente.
            service_type: Tipo de servicio ("deposito", "retiro",
                          "gestion_cuenta").

        Returns:
            El ticket emitido.

        Raises:
            QueueError: Si el tipo de servicio no es válido.
        """
        self._validate_service_type(service_type)

        self._counter += 1
        ticket = Ticket(
            number=self._counter,
            client_name=client_name.strip(),
            service_type=service_type,
        )
        self._queues[service_type].append(ticket)
        return ticket

    def call_next(self, service_type: str) -> Ticket:
        """Desencola y devuelve el siguiente cliente para un tipo de servicio.

        Args:
            service_type: Tipo de servicio.

        Returns:
            El ticket del cliente que pasa a ser atendido.

        Raises:
            QueueError: Si el tipo de servicio no es válido.
            QueueError: Si no hay clientes esperando para ese servicio.
        """
        self._validate_service_type(service_type)
        self._ensure_not_empty(service_type)
        return self._queues[service_type].popleft()

    def peek_next(self, service_type: str) -> Optional[Ticket]:
        """Devuelve el siguiente cliente para un tipo de servicio sin
        retirarlo de la cola.

        Args:
            service_type: Tipo de servicio.

        Returns:
            El siguiente ticket, o ``None`` si la cola está vacía.

        Raises:
            QueueError: Si el tipo de servicio no es válido.
        """
        self._validate_service_type(service_type)
        if self._is_empty(service_type):
            return None
        return self._queues[service_type][0]

    def list_waiting(self) -> Dict[str, List[Ticket]]:
        """Devuelve un diccionario con cada tipo de servicio como clave y
        su lista ordenada de tickets en espera como valor.

        Returns:
            Dict[service_type, List[Ticket]] — copia superficial de las
            colas internas convertidas a listas.
        """
        return {st: list(self._queues[st]) for st in VALID_SERVICE_TYPES}

    def stats(self) -> Dict[str, int]:
        """Devuelve estadísticas de la cola.

        Returns:
            Diccionario con el número de clientes por tipo de servicio y
            una clave ``"total"`` con la suma.
        """
        counts: Dict[str, int] = {}
        total = 0
        for st in VALID_SERVICE_TYPES:
            n = len(self._queues[st])
            counts[st] = n
            total += n
        counts["total"] = total
        return counts

    # -- Métodos auxiliares --------------------------------------------------

    @staticmethod
    def _validate_service_type(service_type: str) -> None:
        """Lanza ``QueueError`` si el tipo de servicio no es válido."""
        if service_type not in VALID_SERVICE_TYPES:
            valid = ", ".join(sorted(VALID_SERVICE_TYPES))
            raise QueueError(
                f"Tipo de servicio inválido: {service_type!r}. "
                f"Los válidos son: {valid}."
            )

    def _ensure_not_empty(self, service_type: str) -> None:
        """Lanza ``QueueError`` si la cola del servicio está vacía."""
        if self._is_empty(service_type):
            raise QueueError(
                f"No hay clientes esperando para '{service_type}'."
            )

    def _is_empty(self, service_type: str) -> bool:
        return len(self._queues[service_type]) == 0


# ============================================================================
# CLI — Interfaz de línea de comandos (menú interactivo)
# ============================================================================


def _read_service_type(prompt: str) -> str:
    """Lee un tipo de servicio del usuario, validándolo."""
    while True:
        value = input(prompt).strip().lower()
        if value in VALID_SERVICE_TYPES:
            return value
        valid = ", ".join(sorted(VALID_SERVICE_TYPES))
        print(f"  ⚠  Tipo inválido. Opciones: {valid}")


def _press_to_continue() -> None:
    """Pausa hasta que el usuario presione Enter."""
    input("\n  Presione Enter para continuar...")


def _print_header(title: str) -> None:
    """Imprime un encabezado formateado."""
    sep = "=" * 56
    print(f"\n{sep}")
    print(f"  {title}")
    print(sep)


# ---------------------------------------------------------------------------
# Menú principal
# ---------------------------------------------------------------------------


def run_cli() -> None:
    """Bucle principal del menú CLI."""
    bq = BranchQueue()

    menu_items = [
        ("Emitir un nuevo ticket", "emitir"),
        ("Llamar al siguiente cliente", "llamar"),
        ("Ver la lista de espera", "espera"),
        ("Ver estadísticas de la cola", "stats"),
        ("Salir", "salir"),
    ]

    while True:
        _print_header("BANCO MERIDIONAL — Gestor de Cola por Servicio")
        print()
        for i, (label, _) in enumerate(menu_items, start=1):
            print(f"    {i}. {label}")
        print()

        try:
            choice = input("  Seleccione una opción [1-5]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  Hasta luego.")
            sys.exit(0)

        print()

        if choice == "1":
            _issue_ticket_flow(bq)
        elif choice == "2":
            _call_next_flow(bq)
        elif choice == "3":
            _show_waiting(bq)
        elif choice == "4":
            _show_stats(bq)
        elif choice == "5":
            print("  Hasta luego.\n")
            break
        else:
            print("  Opción no válida. Intente de nuevo.")
            _press_to_continue()


# ---------------------------------------------------------------------------
# Flujos de cada opción del menú
# ---------------------------------------------------------------------------


def _issue_ticket_flow(bq: BranchQueue) -> None:
    """Flujo: emitir un nuevo ticket."""
    _print_header("EMITIR NUEVO TICKET")
    name = input("  Nombre del cliente: ").strip()
    if not name:
        print("  ⚠  El nombre no puede estar vacío.")
        _press_to_continue()
        return

    st = _read_service_type("  Tipo de servicio: ")
    try:
        ticket = bq.issue_ticket(name, st)
        print(f"\n  ✅ Ticket emitido: {ticket.display()}")
    except QueueError as e:
        print(f"  ⚠  {e}")

    _press_to_continue()


def _call_next_flow(bq: BranchQueue) -> None:
    """Flujo: llamar al siguiente cliente de un servicio."""
    _print_header("LLAMAR AL SIGUIENTE CLIENTE")
    st = _read_service_type("  Tipo de servicio: ")
    try:
        ticket = bq.call_next(st)
        print(f"\n  🏁 Cliente llamado: {ticket.display()}")
    except QueueError as e:
        print(f"  ⚠  {e}")

    _press_to_continue()


def _show_waiting(bq: BranchQueue) -> None:
    """Flujo: mostrar todos los clientes en espera."""
    _print_header("CLIENTES EN ESPERA")
    waiting = bq.list_waiting()
    any_waiting = False

    for st in sorted(VALID_SERVICE_TYPES):
        tickets = waiting[st]
        if not tickets:
            continue
        any_waiting = True
        print(f"\n  [{st.upper()}] — {len(tickets)} en espera")
        print(f"  {'─' * 44}")
        for t in tickets:
            print(f"    #{t.number:03d} │ {t.client_name:<20} │ "
                  f"{t.issued_at.strftime('%H:%M:%S')}")

    if not any_waiting:
        print("  No hay clientes en espera.")

    _press_to_continue()


def _show_stats(bq: BranchQueue) -> None:
    """Flujo: mostrar estadísticas de la cola."""
    _print_header("ESTADÍSTICAS DE LA COLA")
    data = bq.stats()

    print()
    for st in sorted(VALID_SERVICE_TYPES):
        bar = "█" * data[st]
        print(f"  {st:<18} : {data[st]:>3}  {bar}")

    print(f"  {'─' * 32}")
    print(f"  {'TOTAL':<18} : {data['total']:>3}")

    _press_to_continue()


# ============================================================================
# Entry point
# ============================================================================


def main() -> None:
    """Punto de entrada principal."""
    try:
        run_cli()
    except (EOFError, KeyboardInterrupt):
        print("\n\n  Hasta luego.")
        sys.exit(0)


if __name__ == "__main__":
    main()