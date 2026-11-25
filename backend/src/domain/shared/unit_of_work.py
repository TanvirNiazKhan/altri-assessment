"""Unit of work interface (port). Write use cases end with `await uow.commit()`.

Implemented in src.infra.database.unit_of_work; constraint violations raised at commit
arrive as domain errors.
"""

from abc import ABC, abstractmethod


class UnitOfWork(ABC):
    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...
