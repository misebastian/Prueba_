import streamlit as st
import pandas as pd
import numpy as np
import random
import plotly.express as px

# ---------- Simulación de datos ----------
@st.cache_data
def generar_datos():
    num_empresas = 250
    num_proveedores = 200
    num_materiales = 100
    num_filas = 1000

    empresas = [f"Empresa_{i:03}" for i in range(1, num_empresas + 1)]
    proveedores = [f"Proveedor_{i:03}" for i in range(1, num_proveedores + 1)]
    materiales = [f"Material_{i:03}" for i in range(1, num_materiales + 1)]

    np.random.seed(42)
    random.seed(42)

    datos = {
        "empresa": np.random.choice(empresas, num_filas),
        "proveedor": np.random.choice(proveedores, num_filas),
        "material": np.random.choice(materiales, num_filas),
        "unidades": np.random.randint(1, 1000, size=num_filas),
    }

    precio_base = {
        (prov, mat): round(random.uniform(5, 100), 2)
        for prov in proveedores for mat in materiales
    }

    datos["precio_unitario"] = [
        round(precio_base[(prov, mat)] + random.uniform(-5, 5), 2)
        for prov, mat in zip(datos["proveedor"], datos["material"])
    ]

    df = pd.DataFrame(datos)
    df["gasto_usd"] = (df["unidades"] * df["precio_unitario"]).round(2)

    # Precio mínimo para el proveedor-material
    precio_min = df.groupby(["proveedor", "material"])["precio_unitario"].min().reset_index()
    precio_min = precio_min.rename(columns={"precio_unitario": "precio_unitario_min"})
    df = df.merge(precio_min, on=["proveedor", "material"])
    df["ahorro_potencial"] = ((df["precio_unitario"] - df["precio_unitario_min"]) * df["unidades"]).clip(lower=0).round(2)

    return df

df = generar_datos()

# ---------- KPIs ----------
kpi_prov = df.groupby("proveedor").agg({
    "gasto_usd": "sum",
    "ahorro_potencial": "sum",
    "empresa": pd.Series.nunique,
    "material": pd.Series.nunique
}).reset_index().rename(columns={
    "gasto_usd": "Gasto Total (USD)",
    "ahorro_potencial": "Ahorro Potencial (USD)",
    "empresa": "Empresas Distintas",
    "material": "Materiales Distintos"
}).sort_values("Ahorro Potencial (USD)", ascending=False)

mejoras = df[df["ahorro_potencial"] > 0].sort_values("ahorro_potencial", ascending=False)

# ---------- UI ----------
st.title("📊 Análisis de Proveedores y Ahorro Potencial")
st.markdown("Este dashboard permite identificar oportunidades de ahorro en contratos compartidos por múltiples empresas dentro del portafolio.")

# ---------- Gráfico interactivo ----------
fig = px.bar(
    kpi_prov.head(15),
    x="proveedor",
    y="Ahorro Potencial (USD)",
    hover_data=["Gasto Total (USD)", "Empresas Distintas", "Materiales Distintos"],
    title="Top 15 Proveedores con Mayor Ahorro Potencial",
)
st.plotly_chart(fig)

# ---------- Tabla general ----------
st.subheader("🔎 KPIs por Proveedor")
st.dataframe(kpi_prov, use_container_width=True)

# ---------- Tabla filtrable por proveedor ----------
st.subheader("🏢 Empresas que pueden renegociar contratos")
proveedor_sel = st.selectbox("Selecciona un proveedor", options=mejoras["proveedor"].unique())
detalle = mejoras[mejoras["proveedor"] == proveedor_sel][[
    "empresa", "material", "unidades", "precio_unitario", "precio_unitario_min", "ahorro_potencial"
]].sort_values("ahorro_potencial", ascending=False)

st.dataframe(detalle, use_container_width=True)
