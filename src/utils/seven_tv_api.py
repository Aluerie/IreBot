"""
Seven TV Client.

License
-------
* This Source Code Form is subject to the terms of the [Mozilla Public License v2.0](<http://mozilla.org/MPL/2.0/>).
* Copyright (C) 2020-present [Aluerie](<https://github.com/Aluerie>).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, NotRequired, TypedDict

import orjson
from aiohttp import ClientSession

from config import env
from utils import const, errors

if TYPE_CHECKING:
    from collections.abc import Mapping

    class EmoteIdWithAlias(TypedDict):
        emoteId: str
        alias: NotRequired[str]

    class AddEmoteVariables(TypedDict):
        emoteSetId: str
        emoteIdWithAlias: EmoteIdWithAlias


__all__ = (
    "ConflictingEmoteNameError",
    "EmoteNotFoundInSetError",
    "SevenTVClient",
)

BAD_REQUEST_CONFLICTING_NAME_MESSAGE = "BAD_REQUEST this emote has a conflicting name"
BAD_REQUEST_EMOTE_NOT_FOUND_MESSAGE = "BAD_REQUEST emote not found in set"


class EmoteNotFoundInSetError(errors.IreBotError):
    """Emote Not Found In Set Error."""


class ConflictingEmoteNameError(errors.IreBotError):
    """Conflicting Emote Name Error."""


class SevenTVClient:
    """Seven TV GraphQL API Wrapper.

    This class offers a few methods to perform some common operations with 7TV.
    Such as add, remove, find emote and many more.
    This class uses V4 GQL Endpoint: https://api.7tv.app/v4/gql

    Most of operations here rely on @IrenesBot's 7TV account as they are performed with its Bearer Token.

    Links
    -----
    * https://7tv.app/api/docs
        7TV API Docs
    * https://7tv.io/v4/gql/playground
        7TV GraphQL playground.
    * https://github.com/SevenTV/SevenTV/issues/216
        Remember to search in their issues for some examples of GraphQL requests/responses.
    """

    def __init__(self, session: ClientSession | None = None) -> None:
        self.session: ClientSession | None = session

    async def invoke(self, query: str, *, variables: Mapping[str, Any]) -> dict[str, Any]:
        """Invoke a request to 7TV GraphQL API.

        Parameters
        ----------
        query: str
            GraphQL query.
        variables: Mapping[str, Any]
            (Mapping[str, Any] is type-hinting crunch to be compatible with TypedDict, this is supposed to be dict[str, Any])
            Dictionary of variables to be provided with query into `json` kwarg of GraphQL request.

        Returns
        -------
        dict[str, Any]
            GraphQL json dictionary from the response. Usually heavily nested.

        Raises
        ------
        GraphQLResponseError
            If API json response contains `errors` field then `GraphQLResponseError` is raised with its content.
        """
        async with (self.session or ClientSession()).post(
            url="https://api.7tv.app/v4/gql",
            json={
                "query": query,
                "variables": variables,
            },
            headers={
                "Authorization": env.SEVEN_TV_BEARER,
            },
        ) as response:
            graph_ql_json = await response.json(loads=orjson.loads)

        # ERRORS
        if "errors" in graph_ql_json:
            graph_ql_errors: list[dict[str, Any]] = graph_ql_json["errors"]
            for gql_error in graph_ql_errors:
                message = gql_error.get("message", "")
                status = gql_error.get("extensions", {}).get("status", "")
                error_msg = f"{status} {message}"

                if message == BAD_REQUEST_CONFLICTING_NAME_MESSAGE:
                    raise ConflictingEmoteNameError(error_msg)
                if message == BAD_REQUEST_EMOTE_NOT_FOUND_MESSAGE:
                    raise EmoteNotFoundInSetError(error_msg)

            raise errors.APIDataError(str(graph_ql_json["errors"]), graph_ql_json["errors"])

        # NO ERRORS
        return graph_ql_json

    async def emote_get_name(self, emote_id: str) -> str:
        """
        Get defaultName for an emote.

        Parameters
        ----------
        emote_id: str
            7TV emote id.

        Returns
        -------
        str
            emote's `defaultName`.
        """
        res = await self.invoke(
            query="""
            query EmoteFindName($emoteId: Id!) {
                emotes {
                    emote(id: $emoteId) {
                        defaultName
                    }
                }
            }
            """,
            variables={
                "emoteId": emote_id,
            },
        )
        return res["data"]["emotes"]["emote"]["defaultName"]

    async def emote_set_add_emote(self, *, emote_set_id: str, emote_id: str, emote_alias: str | None = None) -> str:
        """
        Add an emote to a 7TV emote set.

        Parameters
        ----------
        emote_set_id: str
            7TV emote set where we will add the provided emote.
        emote_id: str
            7TV emote id.
        emote_alias: str | None = None
            If provided then the emote will be added with an alias.

        Returns
        -------
        str
            `emote_set_id`, which is pretty illogical and not useful.
        """
        query: str = """
        mutation EmoteSetAddEmote($emoteSetId: Id!, $emoteIdWithAlias: EmoteSetEmoteId!) {
            emoteSets {
                emoteSet(id: $emoteSetId) {
                    addEmote(id: $emoteIdWithAlias) {
                        id
                    }
                }
            }
        }
        """
        variables: AddEmoteVariables = {
            "emoteSetId": emote_set_id,
            "emoteIdWithAlias": {"emoteId": emote_id},
        }
        if emote_alias:
            variables["emoteIdWithAlias"]["alias"] = emote_alias

        res = await self.invoke(
            query,
            variables=variables,
        )
        return res["data"]["emoteSets"]["emoteSet"]["addEmote"]["id"]

    async def emote_set_remove_emote(self, *, emote_set_id: str, emote_id: str) -> str:
        """
        Remove an emote from the emote set.

        Parameters
        ----------
        broadcaster_id: str
            Twitch ID for the broadcaster.
        emote_name: str
            Emote name to query against.

        Returns
        -------
        str
            `emote_set_id`, which is pretty illogical and not useful.
        """
        query: str = """
        mutation EmoteSetRemoveEmote($emoteSetId: Id!, $emoteIdWithAlias: EmoteSetEmoteId!) {
            emoteSets {
                emoteSet(id: $emoteSetId) {
                    removeEmote(id: $emoteIdWithAlias) {
                        id
                    }
                }
            }
        }
        """
        res = await self.invoke(
            query,
            variables={
                "emoteSetId": emote_set_id,
                "emoteIdWithAlias": {
                    "emoteId": emote_id,
                },
            },
        )
        return res["data"]["emoteSets"]["emoteSet"]["removeEmote"]["id"]

    async def emote_emote_set_alias(self, *, emote_set_id: str, emote_id: str) -> str:
        """
        Get emote's alias in the emote alias.

        Parameters
        ----------
        emote_set_id: str
            7TV emote set where we will search for the emote.
        emote_id: str
            7TV emote id.

        Returns
        -------
        str
            Emote's `alias` in the mentioned emote set. If alias wasn't set, it still returns `defaultName` for the emote.
        """
        res = await self.invoke(
            query="""
                query EmoteSetSearchEmoteAlias($emoteSetId: Id!, $emoteId: Id!) {
                    emotes {
                        emote(id: $emoteId) {
                            inEmoteSets (emoteSetIds: [$emoteSetId]) {
                                emote {
                                    alias
                                }
                            }
                        }
                    }
                }
                """,
            variables={"emoteSetId": emote_set_id, "emoteId": emote_id},
        )
        emote = res["data"]["emotes"]["emote"]["inEmoteSets"][0]["emote"]
        if emote is None:
            msg = f"Could not find {emote_id} in emote set {emote_set_id}"
            raise EmoteNotFoundInSetError(msg)
        return emote["alias"]

    async def user_get_active_emote(self, *, broadcaster_id: str) -> str:
        """Get currently active 7TV emote set for a broadcaster.

        Parameters
        ----------
        broadcaster_id: str
            Twitch ID for the broadcaster.
        """
        query = """
        query findActiveEmoteSetByPlatformId ($platformId: String!) {
            users {
                userByConnection(platform: TWITCH, platformId: $platformId ) {
                    style {
                        activeEmoteSetId
                    }
                }
            }
        }
        """
        res = await self.invoke(query, variables={"platformId": broadcaster_id})
        return res["data"]["users"]["userByConnection"]["style"]["activeEmoteSetId"]

    async def user_search_emote(self, *, broadcaster_id: str, emote_name: str) -> str:
        """Search a 7TV emote in a broadcaster's active emote set by emote_name.

        Parameters
        ----------
        broadcaster_id: str
            Twitch ID for the broadcaster.
        emote_name: str
            Emote name to query against.

        Returns
        -------
        str
            Emote ID that matches provided `emote_name` in the active emote set for the broadcaster.
        """
        query: str = """
        query UserSearchEmote($platformId: String!, $emoteName: String) {
            users {
                userByConnection(platform: TWITCH, platformId: $platformId) {
                    style {
                        activeEmoteSet {
                            emotes(query: $emoteName, page: 1, perPage: 20) {
                                items {
                                    id
                                    alias
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        res = await self.invoke(
            query,
            variables={
                "emoteName": emote_name,
                "platformId": broadcaster_id,
            },
        )
        candidates = res["data"]["users"]["userByConnection"]["style"]["activeEmoteSet"]["emotes"]["items"]
        candidate = next(c for c in candidates if c["alias"] == emote_name)
        if candidate is None:
            msg = f"It seems there is no emote named like that {const.FFZ.peepoPolice}"
            raise errors.BadUserInputError(msg)
        return candidate["id"]
