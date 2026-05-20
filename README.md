# Vallaskóli Skjár v1.8

Upplýsingaskjár fyrir Vallaskóla með stjórnborði, matseðli, veðri, viðburðum, myndasýningu, skjápar/QR, spilunarlistum, fancy UI og málshætti/orðtaki dagsins.

## Nýtt í v1.8

- Stærra Vallaskóla-logo og betra bil í haus.
- Mjúkar hreyfingar, shimmer í haus, fade/slide animation á kortum.
- Málsháttur / orðtak dagsins birtist sjálfkrafa á skjám.
- Rennilína/ticker neðst með stuttum skilaboðum.
- Fleiri þemu: Norðurljós, Hlýr skóladagur, Bleikur föstudagur.
- Skjáritstjóri með fleiri valmöguleikum.
- Preview mode í stjórnborði.
- Apply to all screens.
- Apply only to Matsalur.
- Sérslóðir fyrir skjái eru áfram með `?view=skjar&device=...`.

## Keyrsla staðbundið

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Render start command

```bash
streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
```

## Slóðir

Stjórnborð:

```text
https://vallaskoli-skjar.onrender.com/?view=admin
```

Skjáir:

```text
https://vallaskoli-skjar.onrender.com/?view=skjar&device=ANDDYRI-01
https://vallaskoli-skjar.onrender.com/?view=skjar&device=MATSALUR-01
https://vallaskoli-skjar.onrender.com/?view=skjar&device=KENNARASTOFA-01
https://vallaskoli-skjar.onrender.com/?view=skjar&device=GANGUR-YNGRA-01
https://vallaskoli-skjar.onrender.com/?view=skjar&device=GANGUR-ELDRA-01
https://vallaskoli-skjar.onrender.com/?view=skjar&device=SKRIFSTOFA-01
```

## Uppfærsla

Afritaðu skrárnar yfir eldri möppu, en varðveittu:

```text
data/
uploads/
```

Svo:

```bash
git add .
git commit -m "Vallaskoli Skjar v1.8 fancy UI og malshettir"
git push origin main
```

Render ætti þá að deploy-a sjálfkrafa.
