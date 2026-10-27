"""Etiqueta de plantilla para cargar los assets de Vite.

En desarrollo apunta al servidor de Vite (``bun run dev``). En producción lee
``static/build/manifest.json`` generado por ``bun run build``.
"""

from __future__ import annotations

import json
from pathlib import Path

from django import template
from django.conf import settings
from django.templatetags.static import static
from django.utils.safestring import mark_safe

register = template.Library()


def _manifest() -> dict:
    candidatos = [
        Path(settings.BASE_DIR) / "static" / "build" / "manifest.json",
    ]
    static_root = getattr(settings, "STATIC_ROOT", None)
    if static_root:
        candidatos.append(Path(static_root) / "build" / "manifest.json")
    for ruta in candidatos:
        if ruta.exists():
            return json.loads(ruta.read_text(encoding="utf-8"))
    return {}


@register.simple_tag
def vite_assets() -> str:
    """Devuelve las etiquetas ``<script>`` y ``<link>`` del entrypoint."""
    entrada = getattr(settings, "VITE_ENTRY", "frontend/main.ts")

    if settings.DEBUG:
        base = getattr(settings, "VITE_DEV_SERVER", "http://127.0.0.1:5173").rstrip("/")
        return mark_safe(f'<script type="module" src="{base}/{entrada}"></script>')

    manifest = _manifest()
    asset = manifest.get(entrada)
    if not asset:
        return mark_safe(
            "<!-- Falta static/build/manifest.json: ejecute 'bun run build'. -->"
        )

    etiquetas = [
        f'<link rel="stylesheet" href="{static("build/" + css)}">'
        for css in asset.get("css", [])
    ]
    etiquetas.append(
        f'<script type="module" src="{static("build/" + asset["file"])}"></script>'
    )
    return mark_safe("\n    ".join(etiquetas))

