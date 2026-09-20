"""Claustudio — catálogo de peças de cerâmica + checkout Mercado Pago.
Servidor Flask mínimo. As fotos ficam em FOTOS_DIR e são servidas direto.

Rotas:
  GET  /                  vitrine (index.html)
  GET  /api/pecas         lista do catálogo (só visíveis se ?admin=0)
  POST /api/pecas/<id>    atualiza metadata da peça (admin)
  GET  /foto/<id>         imagem da peça
  POST /api/checkout      cria preferência de pagamento no Mercado Pago
"""
import os
import json
import uuid
from pathlib import Path

import requests
from flask import Flask, request, jsonify, send_file, abort
from dotenv import load_dotenv

load_dotenv()

BASE = Path(__file__).parent
DATA_FILE = BASE / "pecas.json"
_fotos_env = os.getenv("FOTOS_DIR", "Fotos.site")
FOTOS_DIR = Path(_fotos_env)
if not FOTOS_DIR.is_absolute():
    FOTOS_DIR = BASE / FOTOS_DIR
if not FOTOS_DIR.exists():
    FOTOS_DIR = BASE / "Fotos.site"
MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN", "")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "claustudio2026")
SITE_URL = os.getenv("SITE_URL", "").rstrip("/")  # ex.: https://claustudio.com.br

def _num(envvar, default=0.0):
    """Lê um número do env de forma robusta (aceita vírgula ou ponto, nunca quebra)."""
    v = os.getenv(envvar, "").strip().replace(",", ".")
    if not v:
        return default
    try:
        return float(v)
    except ValueError:
        return default

FRETE_FIXO = _num("FRETE_FIXO", 0.0)          # ex.: 35.00
FRETE_GRATIS_ACIMA = _num("FRETE_GRATIS_ACIMA", 0.0)  # ex.: 500.00

app = Flask(__name__)


def load_pecas():
    if not DATA_FILE.exists():
        DATA_FILE.write_text("[]", encoding="utf-8")
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def save_pecas(pecas):
    DATA_FILE.write_text(
        json.dumps(pecas, ensure_ascii=False, indent=2), encoding="utf-8"
    )


EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def _limpar_nome(pasta):
    """Converte nome de pasta em nome legível de produto."""
    return pasta.strip()


def scan_fotos():
    """Cada pasta (em qualquer nível) que contenha fotos diretamente é um produto.
    Pastas aninhadas viram produtos com nome composto ("pai — filho")."""
    pecas = load_pecas()
    por_pasta = {p.get("pasta", ""): p for p in pecas if p.get("pasta")}

    # descobre todas as pastas-produto (que têm fotos diretamente dentro)
    produtos_no_disco = []
    for dirpath, dirnames, filenames in os.walk(FOTOS_DIR):
        dirnames.sort()  # ordem determinística
        fotos = sorted(n for n in filenames if Path(n).suffix.lower() in EXTS)
        if fotos:
            rel = os.path.relpath(dirpath, FOTOS_DIR).replace("\\", "/")
            produtos_no_disco.append((rel, fotos))
    produtos_no_disco.sort(key=lambda x: x[0])

    alterado = False
    for rel, fotos in produtos_no_disco:
        if rel not in por_pasta:
            nome = rel.replace("/", " — ")
            por_pasta[rel] = {
                "id": uuid.uuid4().hex[:8],
                "pasta": rel,
                "nome": _limpar_nome(nome),
                "categoria": "",
                "material": "",
                "descricao": "",
                "preco": 0.0,
                "estoque": 1,
                "visivel": True,
                "vendido": False,
                "fotos": fotos,
            }
            alterado = True
        else:
            p = por_pasta[rel]
            if p.get("fotos") != fotos:
                p["fotos"] = fotos
                alterado = True
            # backfill de campos novos em entradas antigas
            for k, default in (("material", ""), ("vendido", False), ("estoque", 1)):
                if k not in p:
                    p[k] = default
                    alterado = True
    validas = {rel for rel, _ in produtos_no_disco}
    final = [por_pasta[r] for r in validas if r in por_pasta]
    if alterado or len(final) != len(pecas):
        save_pecas(final)
    return final


def is_admin():
    return request.headers.get("X-Admin-Password") == ADMIN_PASSWORD


@app.route("/")
def index():
    return (BASE / "index.html").read_text(encoding="utf-8")


@app.route("/api/pecas")
def api_pecas():
    pecas = scan_fotos()
    admin = request.args.get("admin") == "1"
    if not admin:
        pecas = [p for p in pecas if p.get("visivel")]
    return jsonify(pecas)


@app.route("/api/pecas/<pid>", methods=["POST"])
def update_peca(pid):
    if not is_admin():
        return jsonify({"error": "não autorizado"}), 401
    data = request.get_json(force=True)
    pecas = load_pecas()
    for p in pecas:
        if p["id"] == pid:
            for k in ("nome", "categoria", "material", "descricao"):
                if k in data:
                    p[k] = (data[k] or "").strip()
            if "preco" in data:
                try:
                    p["preco"] = round(float(data["preco"]), 2)
                except (ValueError, TypeError):
                    pass
            if "estoque" in data:
                try:
                    p["estoque"] = int(data["estoque"])
                except (ValueError, TypeError):
                    pass
            if "visivel" in data:
                p["visivel"] = bool(data["visivel"])
            if "vendido" in data:
                p["vendido"] = bool(data["vendido"])
            save_pecas(pecas)
            return jsonify(p)
    return jsonify({"error": "peça não encontrada"}), 404


@app.route("/foto/<pid>")
@app.route("/foto/<pid>/<int:idx>")
def foto(pid, idx=0):
    for p in load_pecas():
        if p["id"] == pid:
            fotos = p.get("fotos") or []
            if not fotos:
                break
            i = min(max(idx, 0), len(fotos) - 1)
            caminho = FOTOS_DIR / p["pasta"] / fotos[i]
            if caminho.exists():
                return send_file(caminho, mimetype="image/jpeg")
            break
    abort(404)


@app.route("/api/checkout", methods=["POST"])
def checkout():
    try:
        if not MP_ACCESS_TOKEN or MP_ACCESS_TOKEN.startswith("TEST-0000"):
            return jsonify(
                {"error": "Mercado Pago ainda não configurado. Edite o .env com seu Access Token."}
            ), 500
        items = (request.get_json(force=True) or {}).get("items", [])
        if not items:
            return jsonify({"error": "carrinho vazio"}), 400

        mp_items = [
            {
                "title": str(it.get("nome", ""))[:255],
                "quantity": int(it["qtd"]),
                "unit_price": float(it["preco"]),
                "currency_id": "BRL",
            }
            for it in items
        ]
        # frete fixo como item no checkout (modo custom — não precisa de Mercado Envios/me2)
        subtotal = sum(float(it["preco"]) * int(it["qtd"]) for it in items)
        frete = 0.0
        if FRETE_FIXO > 0:
            if FRETE_GRATIS_ACIMA > 0 and subtotal >= FRETE_GRATIS_ACIMA:
                frete = 0.0  # frete grátis acima do threshold
            else:
                frete = FRETE_FIXO
        if frete > 0:
            mp_items.append({
                "title": "Frete (envio PAC/SEDEX)",
                "quantity": 1,
                "unit_price": round(frete, 2),
                "currency_id": "BRL",
            })

        base = SITE_URL or request.host_url.rstrip("/")
        payload = {
            "items": mp_items,
            "back_urls": {
                "success": base + "/?status=success",
                "failure": base + "/?status=failure",
                "pending": base + "/?status=pending",
            },
            "auto_return": "approved",
        }
        headers = {
            "Authorization": f"Bearer {MP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }
        r = requests.post(
            "https://api.mercadopago.com/checkout/preferences",
            headers=headers, json=payload, timeout=20,
        )
        if r.status_code >= 400:
            return jsonify({"error": "Mercado Pago: " + r.text}), 502
        data = r.json()
        return jsonify(
            {
                "init_point": data.get("init_point"),
                "sandbox_init_point": data.get("sandbox_init_point"),
            }
        )
    except Exception as e:
        import traceback
        return jsonify({"error": f"erro interno: {e}", "trace": traceback.format_exc()[-500:]}), 200


if __name__ == "__main__":
    n = len(scan_fotos())
    port = int(os.getenv("PORT", "5000"))
    print(f"\n  CLAUSTUDIO — {n} peças catalogadas em {FOTOS_DIR}")
    print(f"  Site:   http://localhost:{port}")
    print("  Admin:  botão Admin no canto superior direito\n")
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG", "0") == "1")
