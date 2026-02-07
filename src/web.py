"""FastAPI app with OAuth install routes and health check."""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from src.services.slack.oauth import (
    build_authorize_url,
    exchange_code_for_token,
    generate_state,
    handle_installation,
    send_welcome_dm,
    validate_state,
)

logger = logging.getLogger(__name__)

web_app = FastAPI(title="Slough.ai", docs_url=None, redoc_url=None)


@web_app.get("/health")
def health():
    return {"status": "ok"}


@web_app.get("/slack/install")
def slack_install():
    """Redirect the browser to Slack's OAuth authorize page."""
    state = generate_state()
    url = build_authorize_url(state)
    return RedirectResponse(url)


@web_app.get("/slack/oauth_redirect")
def slack_oauth_redirect(request: Request, code: str = "", state: str = "", error: str = ""):
    """Handle the OAuth callback from Slack."""
    if error:
        logger.warning("OAuth error from Slack: %s", error)
        return HTMLResponse(
            content="<h1>Installation cancelled</h1><p>You can close this window.</p>",
            status_code=400,
        )

    if not code or not state:
        return HTMLResponse(
            content="<h1>Invalid request</h1><p>Missing code or state parameter.</p>",
            status_code=400,
        )

    if not validate_state(state):
        logger.warning("Invalid or expired OAuth state")
        return HTMLResponse(
            content="<h1>Invalid state</h1><p>The link may have expired. Please try installing again.</p>",
            status_code=400,
        )

    try:
        oauth_response = exchange_code_for_token(code)
    except Exception:
        logger.exception("Failed to exchange OAuth code for token")
        return HTMLResponse(
            content="<h1>Installation failed</h1><p>Could not complete the OAuth flow. Please try again.</p>",
            status_code=500,
        )

    try:
        handle_installation(oauth_response)
    except Exception:
        logger.exception("Failed to save workspace")
        return HTMLResponse(
            content="<h1>Installation failed</h1><p>Could not save workspace data. Please try again.</p>",
            status_code=500,
        )

    # Send welcome DM (best-effort, don't fail the install)
    bot_token = oauth_response["access_token"]
    installer_id = oauth_response["authed_user"]["id"]
    send_welcome_dm(bot_token, installer_id)

    return HTMLResponse(content=(
        "<html><body style='font-family: sans-serif; text-align: center; padding: 60px;'>"
        "<h1>Slough.ai 설치 완료!</h1>"
        "<p>Slack으로 돌아가서 봇과 대화를 시작하세요.</p>"
        "<p style='color: #888;'>이 창을 닫아도 됩니다.</p>"
        "</body></html>"
    ))
