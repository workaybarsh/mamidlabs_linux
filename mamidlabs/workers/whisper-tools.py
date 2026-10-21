"""Audio transcription worker: calls the ``transcriber`` package.

Engine: faster-whisper large-v3-tr (Turkish). Sound events (AST) and speaker
diarization (pyannote) are on by default. Output is chronological and has no
timestamps:

    (footsteps)
    Speaker: Did you come?
    (door sound)
    Speaker: Yes, I was a little late.

UI/worker contract: reads JSON from stdin, writes JSON to stdout.
    request: {"action":"transcribe","path":...,"device":"auto|cuda|cpu","need_swap":bool,"profile":"lite|pro","language":"tr", ...}
    request: {"action":"plan","local_model_loaded":bool,"profile":"lite|pro"}   -> {"device":..,"need_swap":..}
    request: {"action":"unload"}   -> releases the loaded models from memory (returns VRAM/RAM)
    response: {"text":..., "model":..., "chars":..., "events":N, "diarized":bool} or {"error":...}

WARM (persistent) worker: with ``--serve`` it runs continuously on 127.0.0.1 instead
of one-shot stdin and keeps the models IN-PROCESS. The fixed cost repeated on every
audio turn (Python startup + torch/transformers/faster-whisper imports; measured
~10 s, ~25 s on the first/cold disk) is therefore paid ONCE per session; when the
language model needs VRAM the caller sends ``{"action":"unload"}`` to release the
audio models (the process keeps running).
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

# The transcriber package is the subfolder next to this file (<root>/agent/transcriber).
AGENT_DIR = pathlib.Path(__file__).resolve().parent
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from transcriber import config, main as transcriber_main  # noqa: E402


def _profile(req: dict):
    """The audio-line tier comes from the SELECTED profile name: 'lite', 'pro'
    ('max'/'flash'), or the legacy names 'pc1'/'pc2'. When the name is absent or
    unknown, the tier is decided by the machine's total VRAM (see
    config.select_profile_for)."""
    language = str(req.get('language') or '').strip()
    overrides = {}
    if language and language != 'auto':
        overrides['language'] = language
    name = req.get('profile')
    if name:
        return config.select_profile_for(name, **overrides)
    return config.select_profile(**overrides) if overrides else config.select_profile()


def transcribe(req: dict) -> dict:
    # 'auto' is passed through; the transcriber package picks the device from the recording length.
    device = str(req.get('device') or 'auto').lower()
    if device == 'gpu':
        device = 'cuda'
    # need_swap: tell the worker that the local 27B provider pays a language-model VRAM
    # swap cost. When the field is absent leave it None (the package applies its safe default).
    need_swap = req.get('need_swap')
    if need_swap is not None:
        need_swap = bool(need_swap)
    profile = _profile(req)
    payload = transcriber_main.run(
        str(req.get('path') or ''),
        profile=profile,
        device=device,
        need_swap=need_swap,
        initial_prompt=req.get('initial_prompt'),
        events=req.get('events'),
        diarize_enabled=req.get('diarize'),
        token=req.get('token'),
        include_timestamps=False,
        out_base=req.get('out_base'),
        keep_wav=False,
    )
    return {
        'text': payload['text'],
        'model': os.path.basename(profile.whisper_model),
        'vad': 'silero',
        'chars': len(payload['text']),
        'language': payload['language'],
        'profile': profile.name,
        'events': len(payload['events']),
        'diarized': payload['diarized'],
    }


def plan(req: dict) -> dict:
    """Return the (device, swap) plan before an audio job starts (see config.choose_plan).

    Priority: (1) if it fits in free VRAM together with the language model, GPU with no
    swap; (2) if not, and the recording is SHORT (the swap cost outweighs the gain) and
    it fits in CPU RAM, CPU with no swap; (3) otherwise (long recording or not enough
    RAM) GPU with a mandatory swap. The duration is estimated from ``path`` without
    decoding it. The worker reports this plan to the UI/worker layer; the language model
    is released ONLY when a swap is required.
    """
    profile = _profile(req)
    local = req.get('local_model_loaded')
    local = True if local is None else bool(local)
    vram = config.free_vram_mib()
    ram = config.available_ram_mib()
    # Recording length (short -> CPU, long -> GPU for efficiency). Estimated without decoding.
    duration = None
    path = str(req.get('path') or '')
    if path:
        try:
            from transcriber import audio
            duration = audio.probe_duration_seconds(path)
        except Exception:
            duration = None
    device, need_swap = config.choose_plan(
        profile, duration_seconds=duration, vram_free_mib=vram, ram_free_mib=ram,
        local_model_loaded=local)
    return {
        'device': device,
        'need_swap': need_swap,
        'profile': profile.name,
        'duration_seconds': duration,
        'free_vram_mib': vram,
        'free_ram_mib': ram,
    }


def unload(_req: dict | None = None) -> dict:
    """Release the loaded ASR/AST/diarization models from memory (return VRAM/RAM).

    The persistent (warm) worker keeps models in-process; this is called so the audio
    models are released BEFORE the language model is loaded back into VRAM (see
    mamidlabs-inference.ps1). The process KEEPS RUNNING (only the models are dropped):
    imports/caches stay warm.
    """
    from transcriber import asr, diarize, events
    for fn in (getattr(asr, 'unload_model', None),
               getattr(events, 'unload_events_model', None),
               getattr(diarize, 'unload_pipeline', None)):
        if callable(fn):
            try:
                fn()
            except Exception:
                pass
    return {'ok': True, 'unloaded': True}


ACTIONS = {'transcribe': transcribe, 'plan': plan, 'unload': unload}


def _dispatch(req: dict) -> dict:
    """Handle one request and return the response dict (shared by one-shot main + serve)."""
    action = req.get('action')
    if action == 'ping':
        return {'ok': True, 'pid': os.getpid()}
    handler = ACTIONS.get(action)
    if not handler:
        return {'error': 'unknown action'}
    try:
        return handler(req)
    except Exception as exc:
        return {'error': '%s: %s' % (type(exc).__name__, exc)}


def _write_state(state_file: str, data: dict) -> None:
    """Write the state file ATOMICALLY (so the client never reads partial/corrupt JSON)."""
    tmp = state_file + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as fh:
        json.dump(data, fh)
    os.replace(tmp, state_file)


def _parent_gone(parent_pid: int) -> bool:
    """Has the parent process (the app) exited? If so the server shuts itself down (no leak)."""
    if not parent_pid:
        return False
    if os.name == 'nt':
        try:
            import ctypes
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            STILL_ACTIVE = 259
            handle = ctypes.windll.kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION, False, int(parent_pid))
            if not handle:
                return True
            try:
                code = ctypes.c_ulong()
                ok = ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
                return bool(ok) and code.value != STILL_ACTIVE
            finally:
                ctypes.windll.kernel32.CloseHandle(handle)
        except Exception:
            return False
    try:
        os.kill(int(parent_pid), 0)
        return False
    except ProcessLookupError:
        return True
    except Exception:
        return False


def _serve_client(conn) -> None:
    """Handle one client connection: one line of JSON request -> one line of JSON response."""
    stream = conn.makefile('rwb')
    try:
        line = stream.readline()
        if not line:
            return
        try:
            req = json.loads(line.decode('utf-8') or '{}')
        except Exception as exc:
            resp = {'error': 'invalid request: %s' % exc}
        else:
            resp = _dispatch(req)
        stream.write((json.dumps(resp, ensure_ascii=False) + '\n').encode('utf-8'))
        stream.flush()
    finally:
        try:
            stream.close()
        except Exception:
            pass


def serve(state_file: str, parent_pid: int = 0, idle_timeout: float = 600.0) -> int:
    """Persistent (warm) worker: keeps models IN-PROCESS, accepts requests over 127.0.0.1.

    Goal: pay the fixed cost repeated on every audio turn (Python startup + torch/
    transformers/faster-whisper imports) ONCE per session. When the language model needs
    VRAM the caller sends ``{"action":"unload"}`` to release the audio models; the
    process keeps running and the next turn only pays the model LOADING cost.

    Safety: the process exits when `parent_pid` (the app) goes away or when no request
    arrives for `idle_timeout` seconds, so there is no orphan process/VRAM/RAM leak.
    """
    import socket
    import time

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('127.0.0.1', 0))
    server.listen(8)
    port = server.getsockname()[1]
    server.settimeout(1.0)
    try:
        _write_state(state_file, {'pid': os.getpid(), 'port': port, 'started': time.time()})
    except Exception:
        pass
    last = time.time()
    try:
        while True:
            try:
                conn, _ = server.accept()
            except socket.timeout:
                if _parent_gone(parent_pid) or (idle_timeout > 0 and time.time() - last > idle_timeout):
                    break
                continue
            except OSError:
                break
            try:
                _serve_client(conn)
            finally:
                try:
                    conn.close()
                except Exception:
                    pass
            last = time.time()
            if _parent_gone(parent_pid):
                break
    finally:
        try:
            server.close()
        except Exception:
            pass
        try:
            if os.path.isfile(state_file):
                os.remove(state_file)
        except Exception:
            pass
    return 0


def main() -> None:
    argv = sys.argv[1:]
    if '--serve' in argv:
        parser = argparse.ArgumentParser(description='Persistent (warm) audio transcription worker')
        parser.add_argument('--serve', action='store_true')
        parser.add_argument('--state-file', required=True)
        parser.add_argument('--parent-pid', type=int, default=0)
        parser.add_argument('--idle-timeout', type=float, default=600.0)
        args = parser.parse_args(argv)
        raise SystemExit(serve(args.state_file, args.parent_pid, args.idle_timeout))
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stdin.reconfigure(encoding='utf-8')
    except Exception:
        pass
    try:
        req = json.loads(sys.stdin.read() or '{}')
    except Exception as exc:
        print(json.dumps({'error': 'invalid request: %s' % exc}, ensure_ascii=False))
        return
    print(json.dumps(_dispatch(req), ensure_ascii=False))


if __name__ == '__main__':
    main()
