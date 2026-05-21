# Vallaskóli Skjár v1.9

Upplýsingaskjár fyrir Vallaskóla með stjórnborði, skjáauðkennum, sjálfvirkum sérslóðum, matseðli, veðri, viðburðum, myndasýningu og skjáritstjóra.

## Nýtt í v1.9

- Sérslóðir fyrir alla staðlaða skjái vistast sjálfkrafa í gagnagrunni.
- Opinber grunnslóð er sjálfgefið `https://vallaskoli-skjar.onrender.com`.
- Skjáir sem stofnast sjálfkrafa:
  - ANDDYRI-01
  - MATSALUR-01
  - KENNARASTOFA-01
  - GANGUR-YNGRA-01
  - GANGUR-ELDRA-01
  - SKRIFSTOFA-01
- Betri myndastýring:
  - velja hvaða skjáhamir eiga að sýna mynd
  - velja staðsetningu myndar: aðalmyndasýning, hægri hlið, bakgrunnur/hero eða alls staðar
  - forgangur mynda
  - fleiri myndaútlit í skjáritstjóra
- Skjáritstjóri með Apply to all screens, Apply only to Matsalur og Apply only to Kennarastofa.

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

## Mikilvægt við uppfærslu

Haldið í þessar möppur ef gögn eru komin inn:

```text
data/
uploads/
```

Render sér um að deploy-a sjálfkrafa þegar breytingum er ýtt á GitHub.
