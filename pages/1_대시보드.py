"""
Streamlit 이상탐지 및 고장진단 데모 앱
Grafana state timeline과 유사한 시각화를 제공합니다.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="이상탐지 및 고장진단 대시보드", page_icon="🔍", layout="wide"
)

st.title("🔍 제품 모니터링")
st.markdown("---")


# CSV 데이터 로드
@st.cache_data
def load_data():
    """CSV 데이터 로드"""
    try:
        df = pd.read_csv("anomaly_data.csv")
        # time 컬럼을 datetime으로 변환
        df["time"] = pd.to_datetime(df["time"])
        return df
    except FileNotFoundError:
        error_msg = (
            "anomaly_data.csv 파일을 찾을 수 없습니다. "
            "먼저 generate_mock_data.py를 실행하여 데이터를 생성해주세요."
        )
        st.error(error_msg)
        st.stop()


# 데이터 로드
df = load_data()

# 사이드바 정보
st.sidebar.header("데이터 정보")
st.sidebar.write(f"**총 레코드 수:** {len(df)}")
st.sidebar.write(f"**Product ID 수:** {df['product_id'].nunique()}")
time_range = (
    f"{df['time'].min().strftime('%Y-%m-%d %H:%M')} ~ "
    f"{df['time'].max().strftime('%Y-%m-%d %H:%M')}"
)
st.sidebar.write(f"**시간 범위:** {time_range}")

# Product ID 필터
product_ids = sorted(df["product_id"].unique())
selected_products = st.sidebar.multiselect(
    "Product ID 선택", product_ids, default=product_ids
)

# 필터링된 데이터
filtered_df = df[df["product_id"].isin(selected_products)].copy()

if len(filtered_df) == 0:
    st.warning("선택된 Product ID에 대한 데이터가 없습니다.")
    st.stop()


# 데이터 준비: pivot table 생성
pivot_df = filtered_df.pivot_table(
    index="product_id", columns="time", values="product_anomaly_score", aggfunc="first"
)

# 시간 순서대로 정렬
pivot_df = pivot_df.sort_index(axis=1)

# Plotly Heatmap 생성
fig = go.Figure(
    data=go.Heatmap(
        z=pivot_df.values,
        x=[t.strftime("%H:%M") for t in pivot_df.columns],
        y=pivot_df.index.tolist(),
        colorscale=[
            [0, "green"],  # 0 = 초록색
            [0.5, "yellow"],  # 중간 = 노란색
            [1, "red"],  # 높은 값 = 빨간색
        ],
        colorbar={"title": "Anomaly Score"},
        hovertemplate="<b>%{y}</b><br>"
        + "Time: %{x}<br>"
        + "Anomaly Score: %{z:.2f}<extra></extra>",
        zmin=0,
        zmax=3.5,
    )
)

fig.update_layout(
    title="Product Anomaly Score Timeline",
    xaxis_title="시간",
    yaxis_title="Product ID",
    height=400 + len(pivot_df) * 50,  # Product ID 수에 따라 높이 조정
    xaxis={"tickangle": -45, "tickmode": "linear", "tick0": 0, "dtick": 1},
    yaxis={
        "autorange": "reversed"  # 위에서 아래로 정렬
    },
)

st.plotly_chart(fig, use_container_width=True)

# 통계 정보
st.subheader("통계 정보")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "중위 Anomaly Score", f"{filtered_df['product_anomaly_score'].median():.2f}"
    )
with col2:
    st.metric("최대 Anomaly Score", f"{filtered_df['product_anomaly_score'].max():.2f}")
with col3:
    st.metric("최소 Anomaly Score", f"{filtered_df['product_anomaly_score'].min():.2f}")
with col4:
    high_anomaly_count = len(filtered_df[filtered_df["product_anomaly_score"] > 2.0])
    st.metric("높은 이상 감지 수 (Score > 2.0)", high_anomaly_count)

# 상세 데이터 테이블 (선택사항)
with st.expander("상세 데이터 보기"):
    st.dataframe(
        filtered_df.sort_values(["time", "product_id"]), use_container_width=True
    )
