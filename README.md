# Claustudio · catálogo de cerâmicas

Site do ateliê Claustudio (claustudio.com.br): vitrine de peças de cerâmica com carrinho e checkout no Mercado Pago, e um painel admin para editar nome/preço/categoria de cada foto.

## Arquivos
- `app.py` — servidor Flask (vitrine + API + Mercado Pago)
- `index.html` — a vitrine inteira (catálogo, carrinho, checkout, painel admin)
- `pecas.json` — catálogo (gerado automaticamente a partir das fotos)
- `Fotos.site/` — pasta com as 38 fotos das peças
- `.env` — suas chaves (copie de `.env.example`)

## Rodar pela primeira vez

```bash
cd C:\CLAUSTUDIO
pip install -r requirements.txt
copy .env.example .env
python app.py
```

Abra http://localhost:5000 no navegador.

## Publicar as peças

1. Clique no ícone ⚙ no canto superior direito.
2. Digite a senha (padrão: `claustudio2026` — troque no `.env`).
3. Você verá a lista das 38 fotos. Para cada uma:
   - **Nome**: dê um nome (ex.: "Vaso tulipa alto")
   - **Categoria**: ex.: "Vasos", "Pratos", "Tigelas", "Morringas"
   - **Preço**: valor em reais
   - **Descrição**: texto curto sobre a peça
   - **Visível**: marque para ela aparecer na vitrine
4. Clique **Salvar**. A peça aparece imediatamente no site.

## Configurar o pagamento (Mercado Pago)

1. Crie a conta em https://www.mercadopago.com.br (é grátis).
2. Acesse **Suas integrações → Credenciais** e copie o **Access Token**.
3. Edite o `.env` e cole o token em `MP_ACCESS_TOKEN`.
   - Token de teste começa com `TEST-` → permite pagar com cartão de teste.
   - Token de produção começa com `APP_USR-` ou similar → cobra de verdade.
4. Reinicie o `python app.py`.

Para testar em sandbox use o cartão de teste do Mercado Pago:
- Número: `5031 7557 3453 0604`
- Validade: qualquer data futura · CVV: `123`

## Colocar no ar (claustudio.com.br)

O domínio foi comprado no Registro.br. Para o site ficar acessível em claustudio.com.br você precisa de uma **hospedagem** que rode Python (Flask). Opções:

- **Render.com / Railway.app** (recomendado, grátis no início): conecta o Git, roda `python app.py` e dá um endereço. Aponte o domínio no Registro.br (DNS) para o endereço fornecido.
- **VPS (Hostinger, Contabo)**: você instala Python e roda o Flask com `gunicorn`. Mais controle, mais trabalho.

Depois de escolher a hospedagem, no painel do Registro.br vá em **DNS → editar zonas** e crie um registro **A** ou **CNAME** apontando para o endereço que a hospedagem fornecer.

## Trocar a senha admin
Edite `ADMIN_PASSWORD` no `.env` e reinicie o servidor.
