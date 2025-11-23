from __future__ import annotations

from typing import TYPE_CHECKING

from twitchio.ext import commands

if TYPE_CHECKING:
    from ..bot import IreBot, Irene


__all__ = ("IreComponent",)


class IreComponent(commands.Component):
    """Base component to use within IreBot."""

    def __init__(self, bot: IreBot) -> None:
        self.bot: IreBot = bot

    @property
    def irene(self) -> Irene:
        """A shortcut to Irene's object."""
        return self.bot.irene
