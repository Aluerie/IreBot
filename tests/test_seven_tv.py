import pytest
from aiohttp import ClientSession

from utils import const, seven_tv

pytest_plugins = ("pytest_asyncio",)


@pytest.fixture
async def stv() -> seven_tv.SevenTVClient:
    async with ClientSession() as session:
        return seven_tv.SevenTVClient(session)


@pytest.mark.asyncio
async def test_active_emote_set_by_broadcaster(stv: seven_tv.SevenTVClient) -> None:
    irene_stv_id: str = await stv.active_emote_set_by_broadcaster(broadcaster_id=const.UserID.Irene)
    assert irene_stv_id == "01FAQVCS500002EV4FV330P46A"
