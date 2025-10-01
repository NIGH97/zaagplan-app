import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io

st.title("Zaagplan Optimalisatie")

# Initieer sessie state voor stukken
if "stukken" not in st.session_state:
    st.session_state.stukken = []

# Input velden
st.subheader("Voeg stuk toe")
col1, col2, col3 = st.columns([2,1,1])
with col1:
    lengte_mm = st.number_input("Lengte (mm)", min_value=1, value=1000)
with col2:
    aantal = st.number_input("Aantal", min_value=1, value=1)
with col3:
    if st.button("➕ Toevoegen"):
        for _ in range(aantal):
            st.session_state.stukken.append(lengte_mm / 1000.0)  # opslaan in meter

# Toon ingevoerde stukken
if st.session_state.stukken:
    st.subheader("Ingevoerde stukken")
    df = pd.DataFrame(st.session_state.stukken, columns=["Lengte (m)"])
    st.dataframe(df)

# Profielkeuze
profiel_opties = ["5 m", "7 m", "Beide"]
keuze = st.radio("Kies welke profielen te gebruiken", profiel_opties)

# Optimalisatie functie
def optimaliseer(stukken, profielen):
    stukken_sorted = sorted(stukken, reverse=True)
    resultaat = []

    for stuk in stukken_sorted:
        geplaatst = False
        for profiel in resultaat:
            if sum(profiel["stukken"]) + stuk <= profiel["lengte"]:
                profiel["stukken"].append(stuk)
                geplaatst = True
                break
        if not geplaatst:
            # Kies het kleinste profiel waar stuk in past
            mogelijke = [p for p in profielen if p >= stuk]
            if not mogelijke:
                continue
            lengte_profiel = min(mogelijke)
            resultaat.append({"lengte": lengte_profiel, "stukken": [stuk]})
    return resultaat

# Uitvoering
if st.session_state.stukken:
    if keuze == "5 m":
        profielen = [5.0]
    elif keuze == "7 m":
        profielen = [7.0]
    else:
        profielen = [5.0, 7.0]

    plan = optimaliseer(st.session_state.stukken, profielen)

    st.subheader("Zaagplan")
    totaal_profielen = len(plan)
    totaal_lengte = sum(p["lengte"] for p in plan)
    gebruikt = sum(sum(p["stukken"]) for p in plan)
    afval = totaal_lengte - gebruikt
    afval_pct = afval / totaal_lengte * 100 if totaal_lengte > 0 else 0

    for i, profiel in enumerate(plan, start=1):
        rest = profiel["lengte"] - sum(profiel["stukken"])
        st.write(f"Profiel {i} ({profiel['lengte']} m): {profiel['stukken']} → Rest: {rest:.2f} m")

    st.markdown(f"**Totaal profielen nodig:** {totaal_profielen}")
    st.markdown(f"**Totale afval:** {afval:.2f} m ({afval_pct:.1f}%)")

    # PDF export
    def create_pdf(plan, afval, afval_pct):
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, height - 50, "Zaagplan Rapport")
        c.setFont("Helvetica", 10)

        y = height - 100
        for i, profiel in enumerate(plan, start=1):
            rest = profiel["lengte"] - sum(profiel["stukken"])
            line = f"Profiel {i} ({profiel['lengte']} m): {profiel['stukken']} → Rest: {rest:.2f} m"
            c.drawString(50, y, line)
            y -= 20
            if y < 50:
                c.showPage()
                y = height - 50

        c.drawString(50, y-40, f"Totale afval: {afval:.2f} m ({afval_pct:.1f}%)")

        c.save()
        buffer.seek(0)
        return buffer

    pdf_buffer = create_pdf(plan, afval, afval_pct)
    st.download_button(
        label="📄 Download Zaagplan als PDF",
        data=pdf_buffer,
        file_name="zaagplan.pdf",
        mime="application/pdf"
    )

