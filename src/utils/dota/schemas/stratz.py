"""Schemas representing data structure for my GraphQL calls with StratzClient."""

from __future__ import annotations

from typing import TypedDict

__all__ = ("Items",)


# STRATZ: GET ITEMS


class Items(TypedDict):
    """Schema for `get_items` response."""

    data: ItemData


class ItemData(TypedDict):
    constants: ItemConstants


class ItemConstants(TypedDict):
    items: list[Item]


class Item(TypedDict):
    id: int
    displayName: str
