# Vallaskóli Skjár v1.7 — Skjápar og QR-tenging

Python/Streamlit upplýsingaskjár fyrir Vallaskóla.

## Nýtt í v1.7

- Skjápar: hver skjár fær eigið auðkenni, t.d. `ANDDYRI-01` eða `MATSALUR-01`.
- QR-kóði fyrir hvern skjá í stjórnborði.
- Hver skjár getur haft sinn skjáham og spilunarlista.
- Stjórnborð sýnir síðast hvenær skjárinn var opnaður.
- Opinber grunnslóð er stillanleg fyrir Render eða localhost.

## Keyrsla

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Slóðir

Stjórnborð:

```text
http://localhost:8501/?view=admin
```

Venjulegur skjár:

```text
http://localhost:8501/?view=skjar
```

Skjár með auðkenni:

```text
http://localhost:8501/?view=skjar&device=ANDDYRI-01
```

## Sjálfgefið lykilorð

```text
vallaskoli123
```

Breyttu því í stjórnborði undir **Stillingar**.

## Uppfærsla frá eldri útgáfu

Unzip-aðu yfir eldri möppu, en haltu eftir þessum möppum ef þú ert með gögn:

```text
data/
uploads/
```

## Skjáuppsetning

1. Opnaðu stjórnborð.
2. Farðu í **Skjápar & QR**.
3. Stilltu opinbera grunnslóð, t.d. `http://localhost:8501` eða Render-slóðina.
4. Búðu til eða veldu skjá.
5. Skannaðu QR-kóðann á skjátölvunni eða afritaðu slóðina.
6. Ýttu á F11 fyrir fullscreen.

