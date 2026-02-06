from fastapi.testclient import TestClient

from matverse_runtime.loop_controller import loop_controller
from matverse_runtime.main import app


def test_loop_status_and_trigger_flow():
    client = TestClient(app)

    loop_controller.start()
    status = client.get('/loop/status')
    assert status.status_code == 200
    assert status.json()['state'] == 'running'

    trigger = client.post('/loop/trigger', json={'type': 'manual', 'tx_id': 'pbse_x', 'doi': '10.1/x'})
    assert trigger.status_code == 200
    assert trigger.json()['triggered'] is True

    audit = client.get('/loop/audit?limit=1')
    assert audit.status_code == 200
    assert audit.json()[0]['trigger'] in {'manual', 'publish'}


def test_pause_accelerate_destroy():
    client = TestClient(app)

    pause = client.post('/loop/pause')
    assert pause.status_code == 200
    assert pause.json()['status'] == 'paused'

    blocked = client.post('/loop/trigger', json={'type': 'cron', 'tx_id': 'pbse_x'})
    assert blocked.status_code == 200
    assert blocked.json()['triggered'] is False

    start = client.post('/loop/start')
    assert start.status_code == 200

    accel = client.post('/loop/accelerate', json={'factor': 10})
    assert accel.status_code == 200
    assert accel.json()['replay_interval_seconds'] == 2160

    destroy = client.post('/loop/destroy')
    assert destroy.status_code == 200
    assert destroy.json()['status'] == 'destroyed'
