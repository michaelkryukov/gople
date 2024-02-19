import asyncio
import json
import subprocess
from typing import List, Optional

import chevron
from playwright.async_api import Browser, BrowserContext, async_playwright
from playwright.async_api._context_manager import PlaywrightContextManager
from playwright.async_api._generated import Playwright as AsyncPlaywright

PLAYWRIGHT_LOCK = asyncio.Lock()
PLAYWRIGHT_CONTEXT: PlaywrightContextManager
PLAYWRIGHT: AsyncPlaywright
BROWSER: Optional[Browser] = None
BROWSER_CONTEXT: Optional[BrowserContext] = None


async def initiate_playwright():
    global PLAYWRIGHT_CONTEXT, PLAYWRIGHT
    PLAYWRIGHT_CONTEXT = async_playwright()
    PLAYWRIGHT = await PLAYWRIGHT_CONTEXT.__aenter__()


async def shutdown_playwrite():
    if BROWSER:
        await BROWSER.close()
    await PLAYWRIGHT_CONTEXT.__aexit__()


async def _launch_browser():
    global BROWSER
    if not BROWSER:
        BROWSER = await PLAYWRIGHT.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--use-gl=angle",
                "--use-angle=swiftshader",
            ],
        )
    return BROWSER

async def _render(method, url=None, content=None, *args, **kwargs):
    async with PLAYWRIGHT_LOCK:
        browser = await _launch_browser()

    viewport_width = kwargs.get("width") or 1123
    viewport_height = kwargs.get("height") or 794

    if method == 'pdf':
        kwargs['width'] = str(viewport_width)
        kwargs['height'] = str(viewport_height)
    else:
        kwargs.pop('width', None)
        kwargs.pop('height', None)

    context = await browser.new_context(
        viewport={
            "width": viewport_width,
            "height": viewport_height,
        },
        bypass_csp=True,
    )

    page = await context.new_page()

    page.set_default_timeout(60000)
    page.set_default_navigation_timeout(60000)

    try:
        await page.emulate_media(media="screen")
        if url:
            await page.goto(url)
        elif content:
            await page.set_content(content)
        if await page.query_selector('.__will_be_ready'):
            await page.wait_for_selector('.__ready')
        return await getattr(page, method)(
            *args,
            **kwargs,
        )
    finally:
        await page.close()
        await context.close()


async def render_png(**kwargs):
    return await _render(
        "screenshot",
        type="png",
        **kwargs,
    )


async def render_jpeg(**kwargs):
    return await _render(
        "screenshot",
        type="jpeg",
        **kwargs,
    )


async def render_pdf(**kwargs):
    return await _render(
        "pdf",
        print_background=True,
        **kwargs,
    )


class ProviderException(Exception):
    def __init__(self, provider_path: str):
        self.provider_path = provider_path


async def load_content(template_path: str, provider_paths: Optional[List[str]]):
    data = {}

    with open(f"templates/{template_path}", "r") as fh:
        return chevron.render(
            template=fh,
            data=data,
            partials_path=None,
        )
