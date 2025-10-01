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
        # update de waarden
        st.session_state.stukken[i]["raam"] = raam
        st.session_state.stukken[i]["lengte"] = lengte

# Profielkeuze (standaard beide)
profiel_opties = ["5 m", "7 m", "Beide"]
keuze = st.radio("Kies welke profielen te gebruiken", profiel_opties, index=2)

# Optimalisatie functie
def optimaliseer(stukken, profielen):
    stukken_sorted = sorted(stukken, key=lambda x: x['lengte'], reverse=True)
    resultaat = []

    for stuk in stukken_sorted:
        geplaatst = False
        for profiel in resultaat:
            if sum(s['lengte'] for s in profiel['stukken']) + stuk['lengte'] <= profiel['lengte']:
                profiel['stukken'].append(stuk)
                geplaatst = True
                break
        if not geplaatst:
            mogelijke = [p for p in profielen if p*1000 >= stuk['lengte']]
            if not mogelijke:
                continue
            lengte_profiel = min(mogelijke)*1000  # in mm
            resultaat.append({"lengte": lengte_profiel, "stukken": [stuk]})
    return resultaat

# Uitvoering
if st.session_state.stukken:
    if keuze == "5 m":
        profielen = [5,]
    elif keuze == "7 m":
        profielen = [7,]
    else:
        profielen = [5,7]

    plan = optimaliseer(st.session_state.stukken, profielen)

    st.subheader("Zaagplan")
    totaal_profielen = len(plan)
    totaal_lengte = sum(p['lengte'] for p in plan)
    gebruikt = sum(sum(s['lengte'] for s in p['stukken']) for p in plan)
    afval = totaal_lengte - gebruikt
    afval_pct = afval / totaal_lengte * 100 if totaal_lengte > 0 else 0

    for i, profiel in enumerate(plan, start=1):
        rest = profiel['lengte'] - sum(s['lengte'] for s in profiel['stukken'])
        st.write(f"Profiel {i} ({profiel['lengte']} mm): {[{'Raam': s['raam'], 'Lengte': s['lengte']} for s in profiel['stukken']]} → Rest: {rest} mm")

    st.markdown(f"**Totaal profielen nodig:** {totaal_profielen}")
    st.markdown(f"**Totale afval:** {afval} mm ({afval_pct:.1f}%)")

    # PDF export
    def create_pdf(plan, afval, afval_pct, project_naam):
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        datum = datetime.now().strftime("%d-%m-%Y")
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, height - 50, f"Zaagplan Rapport - {project_naam} ({datum})")
        c.setFont("Helvetica", 10)

        y = height - 100
        for i, profiel in enumerate(plan, start=1):
            rest = profiel['lengte'] - sum(s['lengte'] for s in profiel['stukken'])
            lijn = f"Profiel {i} ({profiel['lengte']} mm): {[{'Raam': s['raam'], 'Lengte': s['lengte']} for s in profiel['stukken']]} → Rest: {rest} mm"
            c.drawString(50, y, lijn)
            y -= 20
            if y < 50:
                c.showPage()
                y = height - 50

        c.drawString(50, y-40, f"Totale afval: {afval} mm ({afval_pct:.1f}%)")

        c.save()
        buffer.seek(0)
        return buffer

    pdf_buffer = create_pdf(plan, afval, afval_pct, project_naam)
    datum_bestand = datetime.now().strftime("%y%m%d")
    bestandsnaam = f"{datum_bestand} - {project_naam} - Optimalisatie.pdf"
    st.download_button(
        label="📄 Download Zaagplan als PDF",
        data=pdf_buffer,
        file_name=bestandsnaam,
        mime="application/pdf"
    )
