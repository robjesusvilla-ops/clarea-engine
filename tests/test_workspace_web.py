import base64
import os
import tempfile
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from typer.testing import CliRunner

from clarea.cli import app as cli_app
from clarea.core.parser import MetricParser
from clarea.workspace import Workspace, slugify

EXAMPLES = Path(__file__).parent.parent / "examples"


class TestWorkspace(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ws = Workspace(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_slugify(self):
        self.assertEqual(slugify("Qhatai Piscinas!"), "qhatai-piscinas")
        self.assertEqual(slugify("Peluquería Ñandú"), "peluqueria-nandu")

    def test_client_and_period_history(self):
        c = self.ws.create_client("Qhatai Piscinas", "piscinas", ["a@b.com"])
        abr = MetricParser.load(EXAMPLES / "plantilla_metricas_abril.csv", "x", "Abril 2026")
        may = MetricParser.load(EXAMPLES / "plantilla_metricas_mayo.csv", "x", "Mayo 2026")
        self.ws.save_period(c.slug, "2026-05", may)
        self.ws.save_period(c.slug, "2026-04", abr)
        self.assertEqual([p.key for p in self.ws.list_periods(c.slug)], ["2026-04", "2026-05"])
        self.assertEqual(self.ws.previous_period(c.slug, "2026-05").period_label, "Abril 2026")
        self.assertIsNone(self.ws.previous_period(c.slug, "2026-04"))
        stored = self.ws.get_period(c.slug, "2026-05")
        self.assertEqual(stored.brand_name, "Qhatai Piscinas")
        self.assertEqual(stored.industry, "piscinas")

    def test_duplicate_and_invalid_names(self):
        self.ws.create_client("Kenji")
        with self.assertRaises(ValueError):
            self.ws.create_client("Kenji")
        with self.assertRaises(ValueError):
            self.ws.get_client("../etc")
        c = self.ws.get_client("kenji")
        with self.assertRaises(ValueError):
            self.ws.save_period(c.slug, "../../x", MetricParser.load(EXAMPLES / "plantilla_metricas_mayo.csv"))


class TestWebApp(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient
        from clarea.web.app import create_app
        self.tmp = tempfile.TemporaryDirectory()
        self.ws = Workspace(Path(self.tmp.name))
        self.client = TestClient(create_app(self.ws))

    def tearDown(self):
        self.tmp.cleanup()
        os.environ.pop("CLAREA_WEB_USER", None)
        os.environ.pop("CLAREA_WEB_PASSWORD", None)

    def upload(self, slug, name, key, label):
        with open(EXAMPLES / name, "rb") as f:
            return self.client.post(f"/clients/{slug}/periods", data={"key": key, "label": label},
                                    files={"file": (name, f, "text/csv")})

    def test_full_flow(self):
        r = self.client.post("/clients", data={"name": "Qhatai Piscinas", "industry": "piscinas", "emails": "a@b.com"})
        self.assertEqual(r.status_code, 200)  # followed redirect to the client page
        self.assertIn("Subir un periodo", r.text)
        self.upload("qhatai-piscinas", "plantilla_metricas_abril.csv", "2026-04", "Abril 2026")
        r = self.upload("qhatai-piscinas", "plantilla_metricas_mayo.csv", "2026-05", "Mayo 2026")
        self.assertIn("Vista Gerente", r.text)
        self.assertIn("Enviar por correo", r.text)
        # Growth computed against April.
        page = self.client.get("/clients/qhatai-piscinas").text
        self.assertIn("Mayo 2026", page)
        self.assertIn("+39.4%", page)
        home = self.client.get("/").text
        self.assertIn("Qhatai Piscinas", home)
        md = self.client.get("/clients/qhatai-piscinas/periods/2026-05/reporte.md")
        self.assertIn("Vista Gerente", md.text)
        self.assertIn("wa.me", self.client.get("/clients/qhatai-piscinas/periods/2026-05").text)
        os.environ.pop("CLAREA_SMTP_HOST", None)
        sent = self.client.post("/clients/qhatai-piscinas/periods/2026-05/send")
        self.assertIn("se guardó para revisarlo", sent.text)
        self.assertEqual(len(list((Path(self.tmp.name) / "outbox").glob("*.eml"))), 1)

    def test_bad_upload_shows_error(self):
        self.client.post("/clients", data={"name": "Kenji"})
        r = self.client.post("/clients/kenji/periods", data={"key": "2026-05"},
                             files={"file": ("x.csv", b"id,likes\n1,2\n", "text/csv")})
        self.assertIn("alcance", r.text)

    def test_unknown_client_is_404(self):
        self.assertEqual(self.client.get("/clients/nadie").status_code, 404)

    def test_basic_auth_when_configured(self):
        os.environ["CLAREA_WEB_USER"], os.environ["CLAREA_WEB_PASSWORD"] = "robert", "secreto"
        self.assertEqual(self.client.get("/").status_code, 401)
        token = base64.b64encode(b"robert:secreto").decode()
        self.assertEqual(self.client.get("/", headers={"Authorization": f"Basic {token}"}).status_code, 200)

    def test_template_download(self):
        r = self.client.get("/plantilla.csv")
        self.assertIn("alcance", r.text)


class TestEnvFile(unittest.TestCase):
    def test_loads_without_overriding(self):
        from clarea.cli import load_env_file
        with tempfile.TemporaryDirectory() as tmp:
            env = Path(tmp) / ".env"
            env.write_text('# comment\nexport CLAREA_T1="uno"\nCLAREA_T2=dos\nCLAREA_T3=\n', encoding="utf-8")
            os.environ["CLAREA_T2"] = "ya-estaba"
            try:
                load_env_file(env)
                self.assertEqual(os.environ["CLAREA_T1"], "uno")
                self.assertEqual(os.environ["CLAREA_T2"], "ya-estaba")
            finally:
                for k in ("CLAREA_T1", "CLAREA_T2", "CLAREA_T3"):
                    os.environ.pop(k, None)


class TestClientCli(unittest.TestCase):
    def test_add_import_report(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            env = {"CLAREA_DATA_DIR": tmp}
            self.assertEqual(runner.invoke(cli_app, ["client", "add", "Qhatai Piscinas", "-i", "piscinas"], env=env).exit_code, 0)
            for key, f in (("2026-04", "plantilla_metricas_abril.csv"), ("2026-05", "plantilla_metricas_mayo.csv")):
                res = runner.invoke(cli_app, ["client", "import", "qhatai-piscinas", str(EXAMPLES / f), "-k", key], env=env)
                self.assertEqual(res.exit_code, 0, res.output)
            out = Path(tmp) / "r.md"
            res = runner.invoke(cli_app, ["client", "report", "qhatai-piscinas", "-o", str(out)], env=env)
            self.assertEqual(res.exit_code, 0, res.output)
            self.assertIn("+39.4%", out.read_text(encoding="utf-8"))
            self.assertIn("qhatai-piscinas", runner.invoke(cli_app, ["client", "list"], env=env).output)


if __name__ == "__main__":
    unittest.main()
