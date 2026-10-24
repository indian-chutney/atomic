from atomic_app.session import TimerSession


def test_paused_time_is_not_counted() -> None:
    session = TimerSession(total_minutes=2)
    session.start(now=0.0)
    session.tick(now=30.0)
    session.pause(now=30.0)
    session.tick(now=90.0)
    assert int(session.elapsed_seconds) == 30

    session.resume(now=90.0)
    session.tick(now=120.0)
    assert int(session.elapsed_seconds) == 60
    assert session.productive_minutes == 1
