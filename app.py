import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io
from datetime import datetime

st.title("Zaagplan Optimalisatie")

# Projectnaam invoer
project_naam = st.text_input("Projectnaam")

# Initieer sessie state voor stukken
if "stukken" not in st.session_state:
    st.session_state.stukken = []

# Input velden
st.subheader("Voeg stuk toe")
col1, col2, col3 = st.columns([2,1,1])
with col1:
    raamnummer = st.text_input("Raamnummer")
with col2:
    lengte_mm = st.number_input("Lengte (mm)", min_value=1, value=1000)
with col3:
    if st.button("➕ Toevoegen"):
        if not raamnummer:
            st.error("Voer een raamnummer in")
        else:
            st.session_state.stukken.append({"raam": raamnummer, "lengte": lengte_mm})

# Toon ingevoerde stukken en mogelijkheid tot aanpassen/verwijderen
if st.session_state.stukken:
    st.subheader("Ingevoerde stukken (aanpasbaar)")
    for i, stuk in enumerate(st.session_state.stukken):
        col1, col2, col3 = st.columns([2,1,1])
        with col1:
            raam = st.text_input(f"Raamnummer {i+1}", value=stuk["raam"], key=f"raam_{i}")
        with col2:
            lengte = st.number_input(f"Lengte (mm) {i+1}", min_value=1, value=stuk["lengte"], key=f"lengte_{i}")
        with col3:
            if st.button(f"❌ Verwijder {i+1}", key=f"verwijder_{i}"):
                st.session_state.stukken.pop(i)
                st.experimental_rerun()
        st.session_state.stukken[i]["raam"] = raam
        st.session_state.stukken[i]["lengte"] = lengte

# Optimalisatie
if st.button("✅ Bereken Zaagplan"):
    stukken_sorted = sorted(st.session_state.stukken, key=lambda x: x['lengte'], reverse=True)
    profielen = []  # lijst van dicts: {"lengte": mm, "stukken": [stuks]}

    for stuk in stukken_sorted:
        geplaatst = False
        for profiel in profielen:
            if sum(s['lengte'] for s in profiel['stukken']) + stuk['lengte'] <= profiel['lengte']:
                profiel['stukken'].append(stuk)
                geplaatst = True
                break
        if not geplaatst:
            opties = [5000, 7000]
            best_choice = min(opties, key=lambda x: x - stuk['lengte'])
            profielen.append({'lengte': best_choice, 'stukken': [stuk]})

    # Output zaagplan
    st.subheader("Zaagplan")
    totaal_5m = totaal_7m = 0
    totaal_lengte = gebruikt = 0

    for i, profiel in enumerate(profielen, start=1):
        rest = profiel['lengte'] - sum(s['lengte'] for s in profiel['stukken'])
        weergave_stukken = [f"{{{s['raam']},{s['lengte']}}}" for s in profiel['stukken']]
        st.write(f"Profiel {i} ({profiel['lengte']} mm): {weergave_stukken} → Rest: {rest} mm")
        if profiel['lengte'] == 5000:
            totaal_5m += 1
        else:
            totaal_7m += 1
        totaal_lengte += profiel['lengte']
        gebruikt += sum(s['lengte'] for s in profiel['stukken'])

    afval = totaal_lengte - gebruikt
    afval_pct = afval / totaal_lengte * 100 if totaal_lengte > 0 else 0

    st.markdown(f"**Totaal profielen nodig:** 5 m: {totaal_5m}, 7 m: {totaal_7m}")
    st.markdown(f"**Totale afval:** {afval} mm ({afval_pct:.1f}%)")

    # PDF export
    def create_pdf(profielen, totaal_5m, totaal_7m, afval, afval_pct, project_naam):
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        datum = datetime.now().strftime("%d-%m-%Y")
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, height - 50, f"Zaagplan Rapport - {project_naam} ({datum})")
        c.setFont("Helvetica", 10)

        y = height - 100
        for i, profiel in enumerate(profielen, start=1):
            rest = profiel['lengte'] - sum(s['lengte'] for s in profiel['stukken'])
            weergave_stukken = [f"{{{s['raam']},{s['lengte']}}}" for s in profiel['stukken']]
            lijn = f"Profiel {i} ({profiel['lengte']} mm): {weergave_stukken} → Rest: {rest} mm"
            c.drawString(50, y, lijn)
            y -= 20
            if y < 50:
                c.showPage()
                y = height - 50

        c.drawString(50, y-40, f"Totaal profielen: 5 m: {totaal_5m}, 7 m: {totaal_7m}")
        c.drawString(50, y-60, f"Totale afval: {afval} mm ({afval_pct:.1f}%)")

        c.save()
        buffer.seek(0)
        return buffer

    pdf_buffer = create_pdf(profielen, totaal_5m, totaal_7m, afval, afval_pct, project_naam)
    datum_bestand = datetime.now().strftime("%y%m%d")
    bestandsnaam = f"{datum_bestand} - {project_naam} - Optimalisatie.pdf"
    st.download_button(
        label="📄 Download Zaagplan als PDF",
        data=pdf_buffer,
        file_name=bestandsnaam,
        mime="application/pdf"
    )

