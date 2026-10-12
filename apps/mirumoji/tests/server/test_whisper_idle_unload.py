"""
Idle unload of the local Whisper model (`MIRUMOJI_WHISPER_IDLE_UNLOAD`)

The model load and the transcription are replaced with fakes, so these run
without a GPU or `faster-whisper`
"""

import asyncio
import dataclasses
import threading
import time
from collections.abc import Callable

import pytest

from mirumoji.server.config import get_settings
from mirumoji.server.processing import processor as processor_module
from mirumoji.server.processing import whisper
from mirumoji.server.processing.processor import Processor

IDLE = 0.05
"""Idle window used by the tests, in seconds"""


class FakeCT2Model:
    unload_seconds = 0.0
    """How long `unload_model` blocks, standing in for freeing the weights"""

    def __init__(self) -> None:
        self.unloaded = False

    def unload_model(self) -> None:
        time.sleep(self.unload_seconds)
        self.unloaded = True


class FakeWhisperModel:
    def __init__(self) -> None:
        self.model = FakeCT2Model()


@pytest.fixture
def loads(monkeypatch):
    """Replaces the model load, recording every model it builds"""
    built: list[FakeWhisperModel] = []

    def fake_load_model() -> FakeWhisperModel:
        assert all(m.model.unloaded for m in built), (
            "loading a second copy next to a loaded one"
        )
        model = FakeWhisperModel()
        built.append(model)
        return model

    monkeypatch.setattr(whisper, "load_model", fake_load_model)
    return built


@pytest.fixture
def release(monkeypatch):
    """
    Replaces the transcription with one that blocks until the returned event
    is set, so a test can hold a job open
    """
    gate = threading.Event()
    gate.set()

    def fake_transcribe(model, audio_path, *, w_transcribe_args=None):
        assert not model.model.unloaded, "transcribing on an unloaded model"
        gate.wait(5)
        return [], None

    monkeypatch.setattr(whisper, "transcribe", fake_transcribe)
    monkeypatch.setattr(whisper, "to_srt", lambda segments: "")
    return gate


@pytest.fixture
def make_processor(monkeypatch) -> Callable[[float], Processor]:
    """
    Builds a `local` backend `Processor` whose settings carry the given idle
    window (fractions of a second, so the tests stay fast)
    """

    def make(idle: float) -> Processor:
        settings = dataclasses.replace(
            get_settings(),
            whisper_idle_unload=idle,
        )
        monkeypatch.setattr(processor_module, "get_settings", lambda: settings)
        p = Processor()
        p.backend = "local"
        return p

    return make


async def longest_stall(awaitable) -> float:
    """
    Awaits `awaitable` while a ticker runs, returning the longest gap between
    two ticks, i.e. the longest time the event loop was blocked
    """
    gaps: list[float] = []

    async def ticker() -> None:
        last = time.perf_counter()
        while True:
            await asyncio.sleep(IDLE / 5)
            now = time.perf_counter()
            gaps.append(now - last)
            last = now

    t = asyncio.create_task(ticker())
    try:
        await awaitable
    finally:
        t.cancel()
    return max(gaps)


async def test_never_unloads_by_default(make_processor, loads, release):
    p = make_processor(0)
    await p.transcribe("a.wav")
    await asyncio.sleep(IDLE * 3)
    assert p._model is loads[0]
    assert not loads[0].model.unloaded
    assert p._unload_handle is None


async def test_unloads_after_idle_and_reloads(make_processor, loads, release):
    p = make_processor(IDLE)
    await p.transcribe("a.wav")
    assert p._model is loads[0]

    await asyncio.sleep(IDLE * 3)
    assert p._model is None
    assert loads[0].model.unloaded

    await p.transcribe("b.wav")
    assert len(loads) == 2
    assert p._model is loads[1]
    await p.close()


async def test_never_unloads_under_a_running_job(
    make_processor, loads, release
):
    p = make_processor(IDLE)
    release.clear()
    job = asyncio.create_task(p.transcribe("long.wav"))

    # The job outlives the idle window several times over
    await asyncio.sleep(IDLE * 4)
    assert p._model is loads[0]
    assert not loads[0].model.unloaded

    release.set()
    await job
    await asyncio.sleep(IDLE * 3)
    assert p._model is None
    assert loads[0].model.unloaded


async def test_late_unload_spares_a_running_job(
    make_processor, loads, release
):
    # The unload callback itself re-checks for users, in case it ever fires
    # while a job holds the model
    p = make_processor(IDLE)
    release.clear()
    job = asyncio.create_task(p.transcribe("long.wav"))
    await asyncio.sleep(IDLE)
    await p._unload_if_idle()
    assert p._model is loads[0]
    assert not loads[0].model.unloaded
    release.set()
    await job
    await p.close()


async def test_new_job_cancels_pending_unload(make_processor, loads, release):
    p = make_processor(IDLE * 6)
    await p.transcribe("a.wav")
    await asyncio.sleep(IDLE * 4)
    # Second job lands inside the window, restarting it
    await p.transcribe("b.wav")
    await asyncio.sleep(IDLE * 4)
    assert p._model is loads[0]
    assert len(loads) == 1
    await p.close()


async def test_concurrent_first_jobs_load_once(make_processor, loads, release):
    p = make_processor(0)
    await asyncio.gather(*(p.transcribe(f"{i}.wav") for i in range(3)))
    assert len(loads) == 1


async def test_failed_load_releases_the_model(
    make_processor, monkeypatch, loads, release
):
    p = make_processor(IDLE)
    load_ok = whisper.load_model

    def failing_load_model() -> FakeWhisperModel:
        raise RuntimeError("no GPU")

    monkeypatch.setattr(whisper, "load_model", failing_load_model)
    with pytest.raises(RuntimeError):
        await p.transcribe("a.wav")
    assert p._model is None
    assert p._model_users == 0
    assert p._unload_handle is None

    # The next job loads the model as usual
    monkeypatch.setattr(whisper, "load_model", load_ok)
    await p.transcribe("b.wav")
    assert p._model is loads[0]
    await p.close()


async def test_close_cancels_pending_unload(make_processor, loads, release):
    p = make_processor(IDLE)
    await p.transcribe("a.wav")
    await p.close()
    await asyncio.sleep(IDLE * 3)
    assert p._model is loads[0]
    assert not loads[0].model.unloaded


async def test_job_during_unload_waits_for_it(
    make_processor, monkeypatch, loads, release
):
    monkeypatch.setattr(FakeCT2Model, "unload_seconds", IDLE * 4)
    p = make_processor(IDLE)
    await p.transcribe("a.wav")
    # The unload starts after IDLE and runs until about IDLE * 5
    await asyncio.sleep(IDLE * 2)
    assert p._model is None
    # The fake load fails if the old copy is still loaded
    await p.transcribe("b.wav")
    assert loads[0].model.unloaded
    assert p._model is loads[1]
    await p.close()


async def test_close_waits_for_a_running_unload(
    make_processor, monkeypatch, loads, release
):
    monkeypatch.setattr(FakeCT2Model, "unload_seconds", IDLE * 4)
    p = make_processor(IDLE)
    await p.transcribe("a.wav")
    await asyncio.sleep(IDLE * 2)
    assert not loads[0].model.unloaded
    await p.close()
    assert loads[0].model.unloaded


async def test_load_does_not_block_the_event_loop(
    monkeypatch, make_processor, release
):
    def slow_load_model() -> FakeWhisperModel:
        time.sleep(IDLE * 8)
        return FakeWhisperModel()

    monkeypatch.setattr(whisper, "load_model", slow_load_model)
    p = make_processor(0)
    assert await longest_stall(p.transcribe("a.wav")) < IDLE * 4


async def test_unload_does_not_block_the_event_loop(
    make_processor, monkeypatch, loads, release
):
    monkeypatch.setattr(FakeCT2Model, "unload_seconds", IDLE * 8)
    p = make_processor(IDLE)
    await p.transcribe("a.wav")
    # Covers the idle window and the whole unload
    assert await longest_stall(asyncio.sleep(IDLE * 12)) < IDLE * 4
    assert loads[0].model.unloaded
