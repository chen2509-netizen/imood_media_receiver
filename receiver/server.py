"""imood_rtp receiver (B): POST /offer for the imood_ai.html frontend.

Approach 1 (negotiation passthrough): the browser's offer is forwarded to LiveTalking's /offer and the
answer comes back unchanged, so WebRTC media flows browser <-> LiveTalking directly and the sessionid is
LiveTalking's own. LiveTalking removes the session itself when that peer connection closes or fails.

To relay media through this process later (approach 2), replace negotiate_with_livetalking() only;
the /offer contract below stays the same. Contract: cyber_gf/docs/frontend_v2_interface.md
(local copy: docs/local_records/frontend_v2_interface_1003.md).

Env: RECEIVER_HOST (0.0.0.0), RECEIVER_PORT (8030), LT_URL (http://127.0.0.1:8010), LT_TIMEOUT_S (30).
"""
import asyncio
import logging
import os
import time

import aiohttp
from aiohttp import web

HOST = os.environ.get("RECEIVER_HOST", "0.0.0.0")
PORT = int(os.environ.get("RECEIVER_PORT", "8030"))
LT_URL = os.environ.get("LT_URL", "http://127.0.0.1:8010").rstrip("/")
LT_TIMEOUT_S = float(os.environ.get("LT_TIMEOUT_S", "30"))

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}

log = logging.getLogger("receiver")


class UpstreamError(Exception):
    """LiveTalking could not be reached or answered with something unusable; str() is shown in the frontend."""


async def negotiate_with_livetalking(http: aiohttp.ClientSession, offer: dict) -> dict:
    """Send the browser's offer (sdp, type, avatar, ...) to LiveTalking; return its JSON reply.

    The reply is {sdp, type, sessionid} on success or {code, msg} when LiveTalking refuses
    (e.g. max sessions reached). The body is forwarded as-is so extra fields reach create_session(params).
    """
    try:
        async with http.post(f"{LT_URL}/offer", json=offer,
                             timeout=aiohttp.ClientTimeout(total=LT_TIMEOUT_S)) as resp:
            if resp.status != 200:
                raise UpstreamError(f"LiveTalking /offer HTTP {resp.status}")
            return await resp.json(content_type=None)
    except aiohttp.ClientConnectionError as e:
        raise UpstreamError(f"LiveTalking unreachable ({LT_URL})") from e
    except asyncio.TimeoutError as e:   # not an alias of TimeoutError on Python 3.10
        raise UpstreamError(f"LiveTalking timed out after {LT_TIMEOUT_S:.0f} s") from e
    except ValueError as e:   # body is not JSON
        raise UpstreamError("LiveTalking returned invalid JSON") from e


def fail(msg: str) -> web.Response:
    return web.json_response({"code": -1, "msg": msg}, headers=CORS)


async def offer(request: web.Request) -> web.Response:
    try:
        params = await request.json()
    except ValueError:
        return fail("request body is not JSON")
    if not isinstance(params, dict) or not params.get("sdp") or params.get("type") != "offer":
        return fail("expected {sdp, type: 'offer', avatar?}")

    t0 = time.monotonic()
    avatar = params.get("avatar") or "(server default)"
    try:
        ans = await negotiate_with_livetalking(request.app["http"], params)
    except UpstreamError as e:
        log.warning("offer avatar=%s failed: %s", avatar, e)
        return fail(str(e))
    if not ans.get("sdp") or not ans.get("sessionid"):
        msg = ans.get("msg") or "LiveTalking answer has no sdp/sessionid"
        log.warning("offer avatar=%s refused by LiveTalking: %s", avatar, msg)
        return fail(msg)

    log.info("offer avatar=%s -> sessionid=%s (%.2f s)", avatar, ans["sessionid"], time.monotonic() - t0)
    return web.json_response({"sdp": ans["sdp"], "type": ans.get("type", "answer"),
                              "sessionid": ans["sessionid"]}, headers=CORS)


async def preflight(request: web.Request) -> web.Response:
    return web.Response(status=204, headers=CORS)


async def health(request: web.Request) -> web.Response:
    return web.json_response({"ok": True, "lt_url": LT_URL, "mode": "passthrough"}, headers=CORS)


async def on_startup(app: web.Application) -> None:
    app["http"] = aiohttp.ClientSession()


async def on_cleanup(app: web.Application) -> None:
    await app["http"].close()


def make_app() -> web.Application:
    app = web.Application()
    app.router.add_post("/offer", offer)
    app.router.add_route("OPTIONS", "/offer", preflight)
    app.router.add_get("/health", health)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    log.info("receiver on %s:%d -> LiveTalking %s", HOST, PORT, LT_URL)
    web.run_app(make_app(), host=HOST, port=PORT, access_log=None)
