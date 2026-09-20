"""Define preço e descrição de cada peça a partir da lista da usuária."""
import json
from pathlib import Path

DATA = Path(__file__).parent / "pecas.json"

# chave = pasta (caminho relativo em Fotos.site), (preco, descricao)
PREÇOS = {
    "centro de mesa costela adão grande": (890, ""),
    "centro de mesa marrom-verde-azul mescla": (790, ""),
    "conjunto centro de mesa folha azul": (1490, "Kit com 2 peças"),
    "conjunto peça bege com flor centro de mesa": (1490, "Kit com 2 peças"),
    "fruteira-centro de mesa verde": (630, ""),
    "mesa posta concha/concha azul": (590, "Mesa posta para 13 lugares"),
    "mesa posta folha": (390, "Mesa posta para 6 lugares"),
    "mesa posta verde-marrom": (630, "Mesa posta para 13 lugares"),
    "peça azul conha centro de mesa": (590, "Bandeija R$ 590 cada · menor R$ 550"),
    "petisqueira bege": (630, ""),
    "vaso verde-marrom": (750, ""),
    # concha verde: usuário não informou — deixa sob consulta
    "mesa posta concha/concha verde": (0, ""),
}

def main():
    pecas = json.loads(DATA.read_text(encoding="utf-8"))
    n = 0
    for p in pecas:
        pasta = p.get("pasta", "")
        if pasta in PREÇOS:
            preco, desc = PREÇOS[pasta]
            p["preco"] = float(preco)
            if desc:
                p["descricao"] = desc
            n += 1
            print(f"  R$ {preco:>6.0f}  {p['nome']}" + (f"  ({desc})" if desc else ""))
        else:
            print(f"  [sem preço]  {p['nome']}  (pasta: {pasta})")
    DATA.write_text(json.dumps(pecas, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{n} peças com preço definido.")

if __name__ == "__main__":
    main()
