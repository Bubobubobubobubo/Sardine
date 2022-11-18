import inspect

from rich import print

from ..base import BaseHandler
from .async_runner import AsyncRunner
from .constants import MaybeCoroFunc

__all__ = ("Scheduler",)


class Scheduler(BaseHandler):
    def __init__(
        self,
        deferred_scheduling: bool = True,
    ):
        super().__init__()
        self.runners: dict[str, AsyncRunner] = {}
        self.deferred = deferred_scheduling
        self._events = {}

    # TODO: Scheduler.__repr__

    # ---------------------------------------------------------------------- #
    # Clock properties

    # @property
    # def nudge(self) -> int:
    #     return self._nudge

    # @nudge.setter
    # def nudge(self, value: int):
    #     """
    #     Nudge the clock to align on another peer. Very similar to accel
    #     but temporary. Nudge will reset every time the clock loops around.

    #     Args:
    #         value (int): nudge factor
    #     """
    #     self._nudge = value
    #     self._reload_runners()

    # NOTE: on any change to the beat interval (accel, nudge, etc.), reload runners

    # Internal methods

    def _reload_runners(self):
        for runner in self.runners.values():
            runner.reload()

    # Scheduling methods

    def schedule_func(self, func: MaybeCoroFunc, /, *args, **kwargs):
        """Schedules the given function to be executed."""
        if not (inspect.isfunction(func) or inspect.ismethod(func)):
            raise TypeError(f"func must be a function, not {type(func).__name__}")

        name = func.__name__
        runner = self.runners.get(name)
        if runner is None:
            runner = self.runners[name] = AsyncRunner(scheduler=self)

        runner.push(func, *args, **kwargs)
        if runner.started():
            runner.reload()
            runner.swim()
        else:
            runner.start()

    def remove(self, func: MaybeCoroFunc, /):
        """Schedules the given function to stop execution."""
        runner = self.runners.get(func.__name__)
        if runner is not None:
            runner.stop()

    # Public methods

    def print_children(self):
        """Print all children on clock"""
        [print(child) for child in self.runners]

    def reset(self):
        for runner in self.runners.values():
            runner.stop()
        self.runners.clear()

    def setup(self):
        for event in self._events:
            self.register(event)

    def hook(self, event: str, *args):
        func = self._events[event]
        func(*args)