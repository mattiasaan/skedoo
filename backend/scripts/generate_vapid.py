"""Genera una coppia di chiavi VAPID per le notifiche push (curva P-256, formato base64url).

Dalla directory ``backend``:

    python -m scripts.generate_vapid

Stampa le due righe da copiare in ``.env`` (o in ``deploy/.env``). La chiave privata resta solo sul server;
quella pubblica il frontend la legge da GET /push/public-key. Se si cambiano le chiavi, le iscrizioni
esistenti smettono di funzionare: ogni dispositivo si reiscrive da solo alla prossima apertura dell'app.
"""
import base64

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat


def b64url(data: bytes) -> str:
  return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def generate() -> tuple[str, str]:
  """(pubblica, privata): la pubblica è il punto non compresso (65 byte), la privata il numero segreto (32 byte)."""
  key = ec.generate_private_key(ec.SECP256R1())
  private = key.private_numbers().private_value.to_bytes(32, "big")
  public = key.public_key().public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
  return b64url(public), b64url(private)


def main() -> None:
  public, private = generate()
  print(f"VAPID_PUBLIC_KEY={public}")
  print(f"VAPID_PRIVATE_KEY={private}")


if __name__ == "__main__":
  main()
