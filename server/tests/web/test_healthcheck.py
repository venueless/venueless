import pytest


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_healthcheck_valid(async_client, world):
    r = await async_client.get("/healthcheck/", HTTP_HOST="foobar.com")
    assert r.status_code == 200
