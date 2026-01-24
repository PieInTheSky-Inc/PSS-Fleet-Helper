import aiohttp as _aiohttp


async def get_data_from_url(url: str) -> str:
    async with _aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.text(encoding="utf-8")
    return data


def get_raw_pastebin(link: str) -> str:
    if "/raw/" in link:
        result = link
    else:
        parts = link.split("/")
        parts.insert(len(parts) - 1, "raw")
        result = "/".join(parts)
    return result
