import pytest

from config import env
from shared import seven_tv
from utils import const

pytest_plugins = ("pytest_asyncio",)


@pytest.fixture
async def stv() -> seven_tv.SevenTVClient:
    return seven_tv.SevenTVClient(env.SEVEN_TV_BEARER)


@pytest.mark.asyncio
async def test_active_emote_set_by_broadcaster(stv: seven_tv.SevenTVClient) -> None:
    irene_stv_id: str = await stv.user_get_active_emote(broadcaster_id=const.UserID.Irene)
    assert irene_stv_id == const.STV_IRENE_DEFAULT_EMOTE_SET_ID
