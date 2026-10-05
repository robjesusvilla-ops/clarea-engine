"""Multi-client storage on disk.

clarea_data/                      (or the folder in CLAREA_DATA_DIR)
  clients/<slug>/client.json      name, industry, report recipients
  clients/<slug>/periods/<key>.json   one PeriodSummary per period

Period keys sort chronologically (use AAAA-MM, e.g. 2026-05), so the
previous period is simply the one before in key order.
"""
import json
import os
import re
import unicodedata
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field

from clarea.core.models import PeriodSummary

DATA_DIR_ENV = "CLAREA_DATA_DIR"
KEY_PATTERN = re.compile(r"^[0-9A-Za-z][0-9A-Za-z_-]{0,40}$")


class Client(BaseModel):
    slug: str
    name: str
    industry: Optional[str] = None
    report_emails: List[str] = Field(default_factory=list)
    whatsapp: Optional[str] = None


class PeriodRef(BaseModel):
    key: str
    label: str


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")[:40] or "cliente"


class Workspace:

    def __init__(self, root: Optional[Path] = None):
        self.root = Path(root or os.environ.get(DATA_DIR_ENV, "clarea_data"))
        self.clients_dir = self.root / "clients"
        self.outbox_dir = self.root / "outbox"

    # Clients -----------------------------------------------------------
    def _client_dir(self, slug: str) -> Path:
        if slugify(slug) != slug:
            raise ValueError(f"Identificador de cliente inválido: {slug!r}")
        return self.clients_dir / slug

    def create_client(self, name: str, industry: Optional[str] = None,
                      report_emails: Optional[List[str]] = None, whatsapp: Optional[str] = None) -> Client:
        if not name.strip():
            raise ValueError("El cliente necesita un nombre.")
        slug = slugify(name)
        if (self.clients_dir / slug).exists():
            raise ValueError(f"Ya existe un cliente llamado '{name}'.")
        client = Client(slug=slug, name=name.strip(), industry=industry or None,
                        report_emails=report_emails or [], whatsapp=whatsapp or None)
        self.save_client(client)
        return client

    def save_client(self, client: Client) -> None:
        d = self._client_dir(client.slug)
        (d / "periods").mkdir(parents=True, exist_ok=True)
        (d / "client.json").write_text(client.model_dump_json(indent=2), encoding="utf-8")

    def get_client(self, slug: str) -> Client:
        path = self._client_dir(slug) / "client.json"
        if not path.exists():
            raise KeyError(f"No existe el cliente '{slug}'.")
        return Client.model_validate_json(path.read_text(encoding="utf-8"))

    def list_clients(self) -> List[Client]:
        if not self.clients_dir.exists():
            return []
        return sorted((self.get_client(d.name) for d in self.clients_dir.iterdir() if (d / "client.json").exists()),
                      key=lambda c: c.name.lower())

    # Periods -----------------------------------------------------------
    def _period_path(self, slug: str, key: str) -> Path:
        if not KEY_PATTERN.match(key):
            raise ValueError("La clave del periodo debe ser tipo AAAA-MM (ej. 2026-05).")
        return self._client_dir(slug) / "periods" / f"{key}.json"

    def save_period(self, slug: str, key: str, summary: PeriodSummary) -> None:
        client = self.get_client(slug)
        summary.brand_name = client.name
        if client.industry and not summary.industry:
            summary.industry = client.industry
        self._period_path(slug, key).write_text(summary.model_dump_json(indent=2), encoding="utf-8")

    def get_period(self, slug: str, key: str) -> PeriodSummary:
        path = self._period_path(slug, key)
        if not path.exists():
            raise KeyError(f"No existe el periodo '{key}' para '{slug}'.")
        return PeriodSummary.model_validate_json(path.read_text(encoding="utf-8"))

    def list_periods(self, slug: str) -> List[PeriodRef]:
        d = self._client_dir(slug) / "periods"
        if not d.exists():
            return []
        refs = []
        for f in sorted(d.glob("*.json")):
            data = json.loads(f.read_text(encoding="utf-8"))
            refs.append(PeriodRef(key=f.stem, label=data.get("period_label", f.stem)))
        return refs

    def previous_period(self, slug: str, key: str) -> Optional[PeriodSummary]:
        keys = [p.key for p in self.list_periods(slug)]
        earlier = [k for k in keys if k < key]
        return self.get_period(slug, earlier[-1]) if earlier else None

    def delete_period(self, slug: str, key: str) -> None:
        self._period_path(slug, key).unlink(missing_ok=True)
