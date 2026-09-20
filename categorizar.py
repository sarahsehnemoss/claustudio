"""Atribui categoria automaticamente a cada peça pelo nome da pasta, e corrige typos no nome."""
import json, re
from pathlib import Path

DATA = Path(__file__).parent / "pecas.json"

# ordem importa: checa palavras-chave mais específicas primeiro
REGRAS = [
    ("centro de mesa", "Centro de Mesa"),
    ("mesa posta",     "Mesa Posta"),
    ("fruteira",       "Fruteira"),
    ("petisqueira",    "Petisqueira"),
    ("vaso",           "Vaso"),
    ("vazo",           "Vaso"),
    ("conjunto",       "Conjunto"),
]

def categorizar(pasta):
    s = pasta.lower()
    for kw, cat in REGRAS:
        if kw in s:
            return cat
    return ""

def main():
    pecas = json.loads(DATA.read_text(encoding="utf-8"))
    for p in pecas:
        p["categoria"] = categorizar(p.get("pasta", ""))
        # corrige typo vazo -> vaso no nome
        if "vazo" in p["nome"].lower():
            p["nome"] = re.sub(r"(?i)vazo", "Vaso", p["nome"])
    DATA.write_text(json.dumps(pecas, ensure_ascii=False, indent=2), encoding="utf-8")
    # relatório
    from collections import Counter
    c = Counter(p["categoria"] or "(sem categoria)" for p in pecas)
    print("Categorias atribuídas:")
    for cat, n in c.most_common():
        print(f"  {cat}: {n}")
    print("\nPeças:")
    for p in pecas:
        print(f"  [{p['categoria'] or '-'}] {p['nome']}  ({len(p.get('fotos',[]))} fotos)")

if __name__ == "__main__":
    main()
