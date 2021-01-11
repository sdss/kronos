# encoding: utf-8
#
# main.py

from pytest import mark

from kronos.apoSite import APOSite
from kronos.app import app


class TestSite(object):
    """Tests for the ``math`` function in main.py."""

    @mark.parametrize(('dec', 'zenithAngle', 'result'),
                      [(5, 5, 0), (5, 3, 0)])
    def test_zenithWarn(self, dec, zenithAngle, result):
        assert APOSite.zenithWarnHA(dec, zenithAngle) == result


@mark.asyncio
async def test_index():
    client = app.test_client()
    response = await client.get('/')
    assert response.status_code == 200


@mark.asyncio
async def test_planObs():
    client = app.test_client()
    response = await client.get('/planObserving.html')
    assert response.status_code == 200
