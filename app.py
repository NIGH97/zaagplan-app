import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io
from datetime import datetime

st.title("Zaagplan Optimalisatie")

# Sidebar: parameters
st.sidebar.subheader("Zaagparameters")
klemafstand = st.sidebar.number_input("Klemafstand (mm)", min_value=0, value=50)
zaagverlies = st.sidebar.number_input("Zaagbladdikte verlies (mm)", min_value=0, value=3)
st.sidebar.markdown("**Beschikbare profielen (mm)**")
profielen_input = st.sidebar.text_input("Voer profielen gescheiden door komma in", "5000,7000")
beschikbare_profielen = [int(p.strip()) for p in profielen_input.split(",") if p.strip().isdigit()]
min_rest = st.sidebar.number_input("Minimale restlengte (mm)", min_value=0, value=0)

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
            totaal_in_profiel = sum(s['lengte'] + klemafstand + zaagverlies for s in profiel['stukken'])
            if totaal_in_profiel + stuk['lengte'] <= profiel['lengte']:
                profiel['stukken'].append(stuk)
                geplaatst = True
                break
        if not geplaatst:
            # kies profiel dat minst restafval oplevert
            mogelijke = [p for p in beschikbare_profielen if p >= stuk['lengte']]
            if not mogelijke:
                continue
            best_choice = min(mogelijke, key=lambda x: x - stuk['lengte'])
            profielen.append({'lengte': best_choice, 'stukken': [stuk]})

    # Output zaagplan
    st.subheader("Zaagplan")
    totaal_profielen_count = {p:0 for p in beschikbare_profielen}
    totaal_lengte = gebruikt = 0

    for i, profiel in enumerate(profielen, start=1):
        rest = profiel['lengte'] - sum(s['lengte'] for s in profiel['stukken'])
        weergave_stukken = [f"{{{s['raam']},{s['lengte']}}}" for s in profiel['stukken']]
        st.write(f"Profiel {i} ({profiel['lengte']} mm): {weergave_stukken} → Rest: {rest} mm")
        totaal_profielen_count[profiel['lengte']] += 1
        totaal_lengte += profiel['lengte']
        gebruikt += sum(s['lengte'] for s in profiel['stukken'])

    afval = totaal_lengte - gebruikt
    afval_pct = afval / totaal_lengte * 100 if totaal_lengte > 0 else 0

    st.markdown("**Totaal profielen nodig:**")
    for p_len, aantal in totaal_profielen_count.items():
        st.markdown(f"{p_len} mm: {aantal}")
    st.markdown(f"**Totale afval:** {afval} mm ({afval_pct:.1f}%)")

    # PDF export
    def create_pdf(profielen, totaal_profielen_count, afval, afval_pct, klemafstand, zaagverlies, project_naam):
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        datum = datetime.now().strftime("%d-%m-%Y")
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, height - 50, f"Zaagplan Rapport - {project_naam} ({datum})")
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 70, f"Klemafstand: {klemafstand} mm | Zaagbladdikte verlies: {zaagverlies} mm")

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

        c.drawString(50, y-40, f"Totaal profielen:")
        for p_len, aantal in totaal_profielen_count.items():
            c.drawString(50, y-60, f"{p_len} mm: {aantal}")
            y -= 20
        c.drawString(50, y-80, f"Totale afval: {afval} mm ({afval_pct:.1f}%)")

        c.save()
        buffer.seek(0)
        return buffer

    pdf_buffer = create_pdf(profielen, totaal_profielen_count, afval, afval_pct, klemafstand, zaagverlies, project_naam)
    datum_bestand = datetime.now().strftime("%y%m%d")
    bestandsnaam = f"{datum_bestand} - {project_naam} - Optimalisatie.pdf"
    st.download_button(
        label="📄 Download Zaagplan als PDF",
        data=pdf_buffer,
        file_name=bestandsnaam,
        mime="application/pdf"
    )


