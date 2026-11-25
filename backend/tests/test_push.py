"""Notifiche push: chiavi VAPID, configurazione, iscrizioni e invio delle variazioni nuove."""
import pytest
from py_vapid import Vapid
from pydantic import ValidationError

from app.config import Settings
from scripts.generate_vapid import generate


# ---------- chiavi e configurazione ----------
def test_generated_keys_are_usable_by_pywebpush():
  public, private = generate()
  assert len(public) == 87 and len(private) == 43  # 65 e 32 byte in base64url senza "="
  vapid = Vapid.from_string(private_key=private)  # lo stesso caricamento che fa pywebpush.webpush
  assert vapid.public_key is not None


def test_push_needs_both_keys_and_database():
  public, private = generate()
  base = {"vapid_public_key": public, "vapid_private_key": private, "vapid_subject": "mailto:admin@example.com"}
  assert Settings(_env_file=None, **base, database_url="sqlite://").push_enabled
  assert not Settings(_env_file=None, **base).push_enabled  # senza database le iscrizioni non si salvano
  assert not Settings(_env_file=None).push_enabled


@pytest.mark.parametrize("values", [
  {"vapid_public_key": "x"},  # manca la privata
  {"vapid_public_key": "x", "vapid_private_key": "y"},  # manca il contatto
  {"vapid_public_key": "x", "vapid_private_key": "y", "vapid_subject": "admin@example.com"},  # senza mailto:
])
def test_invalid_push_configuration_is_rejected(values):
  with pytest.raises(ValidationError):
    Settings(_env_file=None, **values)
