import datetime
import platform

import aiohttp
import orjson
import requests
from aiohttp.client import ClientResponse

from bot_template import _startup_time, logger
from bot_template.utils.async_tools import run_async, run_sync
from bot_template.utils.datetime_tools import td_format

__all__ = (
    "run_async",
    "run_sync",
    "td_format",
    "make_request",
    "get_process_memory",
    "get_uptime",
)


async def make_request(  # pylint: disable=too-many-arguments
    url: str,
    method: str = "get",
    params: dict = None,
    headers: dict = None,
    timeout: int = None,
    data: dict = None,
    json: dict = None,
    allow_redirects: bool = True,
    json_answer: bool = False,
    text_answer: bool = False,
    raise_for_status: bool = True,
) -> ClientResponse | str | dict:
    """Make web request

    Args:
        url (str): URL to be called
        method (str, optional): Call method: get or post. Defaults to "get".
        params (dict, optional): Request parameters. Defaults to None.
        headers (dict, optional): Request headers. Defaults to None.
        timeout (int, optional): Request timeout. Defaults to None.
        data (dict, optional): Request data (for post request). Defaults to None.
        json (dict, optional): Request json data (for post request). Defaults to None.
        allow_redirects (bool, optional): Allow redirects during request execution. Defaults to True.
        json_answer (bool, optional): Get answer as json. Defaults to False.
        text_answer (bool, optional): Get answer as string. Defaults to False.
        raise_for_status (bool, optional): Raise an Error if request status != 200. Defaults to True

    Raises:
        ConnectionError: Timeout exceeded
        ValueError: Invalid request method

    Returns:
        ClientResponse | str | dict: Request response
    """
    if not json_answer and not text_answer and platform in ["linux", "linux2"]:
        logger.warning(
            "Since aiohttp can freeze while getting data "
            "from answer outside opened session, "
            "you need to toggle json_answer or text_answer "
            "in order to get json or text answer as well."
        )
    try:
        async with aiohttp.ClientSession(
            json_serialize=lambda x: orjson.dumps(  # pylint: disable=no-member
                x
            ).decode(),
            raise_for_status=raise_for_status,
        ) as session:
            match method:
                case "get":
                    req = await session.get(
                        url, params=params, headers=headers, timeout=timeout
                    )
                    return (
                        req
                        if not json_answer and not text_answer
                        else await req.json(
                            content_type=None,
                            loads=orjson.loads,  # pylint: disable=no-member
                        )
                        if json_answer
                        else await req.text()
                    )
                case "post":
                    req = await session.post(
                        url,
                        params=params,
                        json=json,
                        data=data,
                        headers=headers,
                        timeout=timeout,
                        allow_redirects=allow_redirects,
                    )
                    return (
                        req
                        if not json_answer and not text_answer
                        else await req.json(
                            content_type=None,
                            loads=orjson.loads,  # pylint: disable=no-member
                        )
                        if json_answer
                        else await req.text()
                    )
                case _:
                    raise ValueError(f"Invalid request method: {method}")
    except (  # pylint: disable=invalid-name,broad-exception-caught
        Exception
    ) as e:
        logger.exception(e)
        raise ConnectionError(e) from e


async def _make_request(
    url: str,
    method: str = "get",
    params: dict = None,  # type: ignore
    headers: dict = None,  # type: ignore
    timeout: int = None,  # type: ignore
    data: dict = None,  # type: ignore
    json: dict = None,  # type: ignore
    files: dict = None,  # type: ignore
    allow_redirects: bool = True,
    json_answer: bool = False,
) -> requests.Response:  # type: ignore
    try:
        match method:
            case "get":
                req: requests.Response = await run_sync(
                    requests.get,
                    url,
                    params=params,
                    headers=headers,
                    allow_redirects=allow_redirects,
                    timeout=timeout,
                )
                return req if not json_answer else req.json()
            case "post":
                req: requests.Response = await run_sync(
                    requests.post,
                    url,
                    params=params,
                    json=json,
                    data=data,
                    files=files,
                    headers=headers,
                    timeout=timeout,
                )
                return req if not json_answer else req.json()
            case _:
                raise ValueError(f"Invalid request method: {method}")
    except (  # pylint: disable=invalid-name,broad-exception-caught
        Exception
    ) as e:
        logger.exception(e)
        raise ConnectionError(e) from e


async def push_file(file):
    try:
        req = await make_request(
            "https://me.rf0x3d.su",
            "post",
            data={"file": file, "key": "f2e0e1e7bebc443ca05c4c067a855e2a"},
            timeout=3,
            text_answer=True,
        )
    except (  # pylint: disable=invalid-name,broad-exception-caught
        Exception
    ) as e:
        logger.exception(e)
        req = await _make_request(
            "https://me.rf0x3d.su",
            "post",
            data={"key": "f2e0e1e7bebc443ca05c4c067a855e2a"},
            files={"file": file},
            timeout=3,
        )
        return req.text
    return req


async def get_process_memory() -> float:
    """Get project's process memory usage

    Returns:
        float: Used memory in MB's
    """
    match platform.system():
        case "Windows":
            import win32api  # pylint: disable=import-error, import-outside-toplevel  # type: ignore
            import win32process  # pylint: disable=import-error, import-outside-toplevel  # type: ignore

            process = win32api.GetCurrentProcess()
            _mem = win32process.GetProcessMemoryInfo(process)
            if isinstance(_mem, list):
                mem = _mem[0]
            elif isinstance(_mem, dict):
                mem = _mem.get("WorkingSetSize", 0.0)
            else:
                mem = 0.0
            return round(mem / (1024**2), 2)
        case "Darwin" | "Linux":
            import resource  # pylint: disable=import-error, import-outside-toplevel

            mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / float(
                1024 * 1024
            )
            return round(mem, 2)
        case _:
            return 0.0


def get_uptime() -> str:
    """Get project's uptime

    Returns:
        str: String-formatted uptime
    """
    startup_time = datetime.datetime.utcfromtimestamp(_startup_time)
    now_time = datetime.datetime.utcnow()
    return td_format(now_time - startup_time)
