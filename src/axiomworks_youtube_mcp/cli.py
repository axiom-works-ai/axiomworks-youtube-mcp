"""CLI entry point for the YouTube MCP server.

Provides setup, status, and run commands.
"""

from __future__ import annotations

import click
import sys


@click.group()
def main():
    """Axiom Works YouTube + YouTube Music MCP Server."""
    pass


@main.command()
def run():
    """Start the MCP server (stdio transport)."""
    from .server import mcp

    mcp.run(transport="stdio")


@main.command()
def setup():
    """Interactive setup — configure API key and OAuth credentials."""
    from .config import ensure_config_dir, save_api_key, load_config, API_KEY_PATH

    ensure_config_dir()
    click.echo("=== Axiom Works YouTube MCP Setup ===\n")

    # Step 1: API key
    click.echo("Step 1: YouTube Data API Key")
    click.echo("  Get one at: https://console.cloud.google.com/apis/credentials")
    click.echo("  Enable: YouTube Data API v3, YouTube Analytics API")
    api_key = click.prompt(
        "  Enter your API key (or press Enter to skip)", default="", show_default=False
    )
    if api_key.strip():
        save_api_key(api_key.strip())
        click.echo("  API key saved.\n")
    else:
        click.echo("  Skipped. Tier 0 features available (transcripts, YT Music browsing).\n")

    # Step 2: Google OAuth
    click.echo("Step 2: Google OAuth (for likes, comments, playlists, uploads, analytics)")
    if click.confirm("  Authenticate with Google?", default=False):
        click.echo("  Opening browser for OAuth consent...")
        _setup_google_oauth()
        click.echo("  Google OAuth configured.\n")
    else:
        click.echo("  Skipped.\n")

    # Step 3: YouTube Music OAuth
    click.echo("Step 3: YouTube Music (for library, history, playlist management)")
    if click.confirm("  Authenticate with YouTube Music?", default=False):
        from .clients.ytmusic import setup_ytmusic_oauth

        success = setup_ytmusic_oauth()
        if success:
            click.echo("  YouTube Music authenticated.\n")
        else:
            click.echo("  YouTube Music setup failed. You can retry later.\n")
    else:
        click.echo("  Skipped.\n")

    # Summary
    config = load_config()
    click.echo("=== Setup Complete ===")
    click.echo(f"  Auth tier: {config.auth_tier.name}")
    click.echo(f"  Available tools: {config.available_tool_count}/68")
    click.echo(f"\nAdd to Claude Code .mcp.json:")
    click.echo('  {')
    click.echo('    "mcpServers": {')
    click.echo('      "youtube": {')
    click.echo('        "command": "uvx",')
    click.echo('        "args": ["axiomworks-youtube-mcp", "run"]')
    click.echo('      }')
    click.echo('    }')
    click.echo('  }')


@main.command()
def status():
    """Show current configuration and auth status."""
    from .config import load_config

    config = load_config()

    click.echo("=== Axiom Works YouTube MCP Status ===")
    click.echo(f"  API Key:        {'configured' if config.api_key else 'not set'}")
    click.echo(
        f"  Google OAuth:   {'authenticated' if config.google_oauth_credentials else 'not set'}"
    )
    click.echo(
        f"  YouTube Music:  {'authenticated' if config.ytmusic_auth_path else 'not set'}"
    )
    click.echo(f"  Auth Tier:      {config.auth_tier.name} ({config.auth_tier.value})")
    click.echo(f"  Available Tools: {config.available_tool_count}/68")
    click.echo(f"  Quota Used:     {config.quota_used_today}/{config.quota_daily_limit}")


def _setup_google_oauth():
    """Run Google OAuth setup flow."""
    from google_auth_oauthlib.flow import InstalledAppFlow
    from .config import save_google_oauth, CONFIG_DIR

    # Check for client secrets file
    client_secrets = CONFIG_DIR / "client_secrets.json"
    if not client_secrets.exists():
        click.echo(
            "\n  You need a client_secrets.json file from Google Cloud Console."
            f"\n  Download it and place it at: {client_secrets}"
            "\n  Then run setup again."
        )
        return

    scopes = [
        "https://www.googleapis.com/auth/youtube",
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/yt-analytics.readonly",
    ]

    flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets), scopes)
    credentials = flow.run_local_server(port=0)
    save_google_oauth(
        {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": list(credentials.scopes),
        }
    )


@main.command()
def version():
    """Show version."""
    from . import __version__

    click.echo(f"axiomworks-youtube-mcp {__version__}")


if __name__ == "__main__":
    main()
