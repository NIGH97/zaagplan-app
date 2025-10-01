import streamlit as st
import pandas as pd

st.title("Zaagplan Optimalisatie")

st.markdown("Voer hieronder de gewenste lengtes en aantallen in.")

# Basisprofielen (standaard 5m en 7m)
basis_profielen = [5.0, 7.0]

# Invoer tabel
st.subheader("Benodigde stukken")
data = st.text_area("Geef de lengtes en aantallen in (formaat: lengte, aantal per regel)",
"""2.3, 4
1.2, 3""")

stukken = []
if data:
    try:
        for line in data.strip().split("\n"):
            lengte, aantal = line.split(",")
            stukken.extend([float(lengte.strip())] * int(aantal.strip()))
    except:
        st.error("Ongeldige invoer. Gebruik het formaat: lengte, aantal")

# Greedy algoritme (First Fit Decreasing)
def optimaliseer(stukken, profiel_lengte):
    stukken_sorted = sorted(stukken, reverse=True)
    profielen = []
    for stuk in stukken_sorted:
        geplaatst = False
        for profiel in profielen:
            if sum(profiel) + stuk <= profiel_lengte:
                profiel.append(stuk)
                geplaatst = True
                break
        if not geplaatst:
            profielen.append([stuk])
    return profielen

if stukken:
    keuze = st.radio("Kies profiel lengte", basis_profielen)
    resultaat = optimaliseer(stukken, keuze)

    st.subheader("Zaagplan")
    totaal_profielen = len(resultaat)
    totaal_lengte = totaal_profielen * keuze
    gebruikt = sum(sum(profiel) for profiel in resultaat)
    afval = totaal_lengte - gebruikt
    afval_pct = afval / totaal_lengte * 100

    for i, profiel in enumerate(resultaat, start=1):
        rest = keuze - sum(profiel)
        st.write(f"Profiel {i}: {profiel} → Rest: {rest:.2f} m")

    st.markdown(f"**Totaal profielen nodig:** {totaal_profielen}")
    st.markdown(f"**Totale afval:** {afval:.2f} m ({afval_pct:.1f}%)")
