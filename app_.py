import streamlit as st
import pandas as pd
import numpy as np
import random
import plotly.express as px

# --------- Simulación de datos optimizada y cacheada ---------
@st.cache_data(show_spinner="Cargando datos...")
def generar_datos(num_filas=1000):
    num_empresas = 250
    num_proveedores = 200
    num_materiales = 100

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

    precio_min = df.groupby(["proveedor", "material"])["precio_unitario"].min().reset_index()
    precio_min = precio_min.rename(columns={"precio_unitario": "precio_unitario_min"})
    df = df.merge(precio_min, on=["proveedor", "material"])
    df["ahorro_potencial"] = ((df["precio_unitario"] - df["precio_unitario_min"]) * df["unidades"]).clip(lower=0).round(2)

    return df

# --------- UI principal ---------
st.set_page_config("Análisis de Proveedores", layout="wide")
st.title("📊 Análisis de Ahorro Potencial por Proveedor")
st.markdown("Este dashboard identifica oportunidades para renegociar contratos con proveedores compartidos entre empresas del portafolio.")

# --------- Sidebar control ---------
with st.sidebar:
    st.header("⚙️ Parámetros")
    filas = st.slider("Cantidad de registros simulados", 500, 10000, 1000, step=500)
    df = generar_datos(num_filas=filas)

# --------- KPIs generales ---------
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

# --------- Visualización ---------
col1, col2 = st.columns([3, 2])

with col1:
    top_kpi = kpi_prov.head(15)
    fig = px.bar(
        top_kpi,
        x="proveedor",
        y="Ahorro Potencial (USD)",
        hover_data=["Gasto Total (USD)", "Empresas Distintas"],
        title="Top 15 Proveedores con Mayor Ahorro Potencial",
        color="Ahorro Potencial (USD)",
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.metric("💸 Gasto Total", f"${df['gasto_usd'].sum():,.0f}")
    st.metric("💰 Ahorro Potencial Total", f"${df['ahorro_potencial'].sum():,.0f}")
    st.metric("🏢 Empresas en el portafolio", df["empresa"].nunique())
    st.metric("📦 Proveedores únicos", df["proveedor"].nunique())

# --------- Tabla principal de KPIs ---------
st.subheader("📋 KPIs por Proveedor")
st.dataframe(kpi_prov.head(50), use_container_width=True)

# --------- Filtro interactivo ---------
st.subheader("🏢 Empresas que pueden renegociar precios")

proveedor_sel = st.selectbox(
    "Selecciona un proveedor para ver empresas relacionadas",
    options=mejoras["proveedor"].unique()
)

detalle = mejoras[mejoras["proveedor"] == proveedor_sel][[
    "empresa", "material", "unidades",
    "precio_unitario", "precio_unitario_min", "ahorro_potencial"
]].sort_values("ahorro_potencial", ascending=False)

st.dataframe(detalle, use_container_width=True)

