# Vallaskóli Skjár v1.10

Útgáfa með skjáfit / F11 sýningarham.

Nýtt:
- Compact TV layout sem passar betur í 16:9 skjái.
- Minni haus, betra bil og stýrt hámark á kubbum.
- Minni hliðarkubbar í autoplay svo allt sjáist.
- Mýkri og léttari skjáhreyfingar áfram virkar.
- Betri myndahæð í sýningarham svo myndir fari ekki niður fyrir skjá.

Keyrsla:
```bash
pip install -r requirements.txt
streamlit run app.py
```

Render start command:
```bash
streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
```
