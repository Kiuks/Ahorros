"""Convierte el Excel de tricount-extractor en tricount.json cifrado para la app "Mis ahorros".

Uso: python tricount_a_json.py <carpeta_con_xlsx> <salida.json>
Necesita la variable de entorno CLAVE (la contraseña que Inés pondrá en la app).
"""
import base64
import datetime
import glob
import json
import os
import sys

from openpyxl import load_workbook
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ITER = 200_000


def b64(b):
    return base64.b64encode(b).decode()


def leer(carpeta):
    filas = []
    ficheros = sorted(glob.glob(os.path.join(carpeta, "**", "*.xlsx"), recursive=True))
    if not ficheros:
        sys.exit("No se ha encontrado ningún .xlsx en " + carpeta)
    for f in ficheros:
        wb = load_workbook(f, read_only=True, data_only=True)
        if "allocations" not in wb.sheetnames:
            sys.exit(f"{f} no tiene la hoja 'allocations' (hojas: {wb.sheetnames})")
        it = wb["allocations"].iter_rows(values_only=True)
        cab = [str(h).strip() if h is not None else "" for h in next(it)]
        for r in it:
            d = dict(zip(cab, r))
            if d.get("entry_id") is None:
                continue
            for k, v in d.items():
                if isinstance(v, (datetime.date, datetime.datetime)):
                    d[k] = v.isoformat()
            d["registry"] = os.path.splitext(os.path.basename(f))[0]
            filas.append(d)
    return filas


def main():
    carpeta, salida = sys.argv[1], sys.argv[2]
    filas = leer(carpeta)
    datos = {
        "generado": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "filas": filas,
    }
    texto = json.dumps(datos, ensure_ascii=False, default=str).encode()
    salt, iv = os.urandom(16), os.urandom(12)
    clave = PBKDF2HMAC(hashes.SHA256(), 32, salt, ITER).derive(os.environ["CLAVE"].encode())
    cifrado = AESGCM(clave).encrypt(iv, texto, None)
    with open(salida, "w") as fh:
        json.dump({"v": 1, "iter": ITER, "salt": b64(salt), "iv": b64(iv), "data": b64(cifrado)}, fh)
    print(f"{len(filas)} filas escritas en {salida}")


if __name__ == "__main__":
    main()
