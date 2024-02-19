import time
from typing import List, Literal, Optional

from fastapi import FastAPI, Response, Query
from fastapi.responses import JSONResponse

from .renders import (
    initiate_playwright,
    load_content,
    render_jpeg,
    render_pdf,
    render_png,
    shutdown_playwrite,
    ProviderException,
)

app = FastAPI()


@app.on_event("startup")
async def startup():
    await initiate_playwright()


@app.on_event("shutdown")
async def shutdown():
    await shutdown_playwrite()


@app.get("/ping")
def handle_ping():
    return {"pong": time.time()}


def get_renderer(kind):
    if kind == "pdf":
        return render_pdf
    elif kind == "png":
        return render_png
    elif kind == "jpeg":
        return render_jpeg

    raise ValueError(f'Unexpected renderer kind: "{kind}"')


def get_content_type(kind):
    if kind == "pdf":
        return "application/pdf"
    elif kind == "png":
        return "image/png"
    elif kind == "jpeg":
        return "image/jpeg"

    raise ValueError(f'Unexpected renderer kind: "{kind}"')


@app.get("/{kind}/by-url")
async def handle_url(
    kind: Literal["pdf", "png", "jpeg"],
    url: str,
    width: Optional[str] = None,
    height: Optional[str] = None,
):
    return Response(
        content=await get_renderer(kind)(
            url=url,
            width=width,
            height=height,
        ),
        headers={"Content-Type": "application/pdf"},
    )


@app.get("/{kind}/by-template")
async def handle_template(
    kind: Literal["pdf", "png", "jpeg"],
    template_path: str,
    provider_paths: Optional[List[str]] = Query(None, alias='provider_paths[]'),
    width: Optional[str] = None,
    height: Optional[str] = None,
):
    try:
        content = await load_content(
            template_path,
            provider_paths,
        )
    except ProviderException as exc:
        return JSONResponse(
            {'details': f"Provider '{exc.provider_path}' failed to return data."},
            status_code=500,
        )

    return Response(
        content=await get_renderer(kind)(
            content=content,
            width=width,
            height=height,
        ),
        headers={"Content-Type": get_content_type(kind)},
    )
