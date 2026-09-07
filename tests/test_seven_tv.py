import pytest

from utils import const, seven_tv_api

pytest_plugins = ("pytest_asyncio",)


@pytest.fixture
async def stv() -> seven_tv_api.SevenTVClient:
    return seven_tv_api.SevenTVClient()


@pytest.mark.asyncio
async def test_active_emote_set_by_broadcaster(stv: seven_tv_api.SevenTVClient) -> None:
    irene_stv_id: str = await stv.user_get_active_emote(broadcaster_id=const.UserID.Irene)
    assert irene_stv_id == const.STV_IRENE_DEFAULT_EMOTE_SET_ID
