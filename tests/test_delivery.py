import email
import os
import tempfile
import unittest
import sys
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent))

from clarea.core.parser import MetricParser
from clarea.delivery import build_email, send_report, whatsapp_link, whatsapp_message
from clarea.pipeline import analyze

EXAMPLES = Path(__file__).parent.parent / "examples"


def result():
    return analyze(MetricParser.from_json_file(EXAMPLES / "sample_facebook_metrics.json"))


class TestWhatsApp(unittest.TestCase):
    def test_message_is_short_and_complete(self):
        msg = whatsapp_message(result())
        self.assertIn("Qhatai Piscinas", msg)
        self.assertIn("Próxima decisión", msg)
        self.assertLess(len(msg), 1500)

    def test_link_cleans_number_and_encodes_text(self):
        link = whatsapp_link("Hola mundo", "+51 999-888-777")
        self.assertEqual(link, "https://wa.me/51999888777?text=Hola%20mundo")


class TestEmail(unittest.TestCase):
    def test_email_has_summary_and_attachments(self):
        msg = build_email(result(), ["dueno@qhatai.pe"], "clarea@agencia.pe")
        self.assertIn("Qhatai Piscinas", msg["Subject"])
        names = [p.get_filename() for p in msg.iter_attachments()]
        self.assertTrue(any(n.startswith("dashboard-") and n.endswith(".html") for n in names))
        self.assertTrue(any(n.endswith(".md") for n in names))

    def test_rejects_bad_recipients(self):
        with self.assertRaises(ValueError):
            build_email(result(), ["no-es-correo"], "a@b.com")
        with self.assertRaises(ValueError):
            build_email(result(), [], "a@b.com")

    def test_without_smtp_saves_to_outbox(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CLAREA_SMTP_HOST", None)
            out = send_report(result(), ["dueno@qhatai.pe"], Path(tmp))
            self.assertFalse(out.sent)
            parsed = email.message_from_bytes(out.eml_path.read_bytes())
            self.assertEqual(parsed["To"], "dueno@qhatai.pe")

    def test_sends_with_smtp(self):
        env = {"CLAREA_SMTP_HOST": "smtp.example.com", "CLAREA_SMTP_USER": "robert@example.com",
               "CLAREA_SMTP_PASSWORD": "app-pass"}
        with mock.patch.dict(os.environ, env), mock.patch("smtplib.SMTP") as smtp:
            server = smtp.return_value
            server.__enter__.return_value = server
            out = send_report(result(), ["dueno@qhatai.pe"], Path("unused"))
        self.assertTrue(out.sent)
        server.starttls.assert_called_once()
        server.login.assert_called_once_with("robert@example.com", "app-pass")
        self.assertEqual(server.send_message.call_args[0][0]["From"], "robert@example.com")


if __name__ == "__main__":
    unittest.main()
