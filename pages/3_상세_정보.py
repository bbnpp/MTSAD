"""
상세 정보 페이지
Product ID와 시간대를 입력받아 상세 정보를 표시합니다.
"""

import ast
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# 페이지 설정
st.set_page_config(page_title="상세 정보", page_icon="📊", layout="wide")

st.title("📊 상세 정보 조회")
st.markdown("---")


# CSV 데이터 로드
@st.cache_data
def load_anomaly_data():
    """이상탐지 데이터 로드"""
    try:
        df = pd.read_csv("anomaly_data.csv")
        df["time"] = pd.to_datetime(df["time"])
        return df
    except FileNotFoundError:
        st.error("anomaly_data.csv 파일을 찾을 수 없습니다.")
        return None


@st.cache_data
def load_alert_data():
    """알림 데이터 로드"""
    try:
        df = pd.read_csv("alert_data.csv")
        df["time"] = pd.to_datetime(df["time"])
        return df
    except FileNotFoundError:
        st.warning("alert_data.csv 파일을 찾을 수 없습니다.")
        return pd.DataFrame(columns=["time", "product_id", "identifier"])


@st.cache_data
def load_action_history_data():
    """조치 내역 데이터 로드"""
    try:
        df = pd.read_csv("action_history.csv")
        df["조치 일자"] = pd.to_datetime(df["조치 일자"])
        return df
    except FileNotFoundError:
        st.warning("action_history.csv 파일을 찾을 수 없습니다.")
        return pd.DataFrame(columns=["조치 일자", "product_id", "현상", "원인", "처방"])


@st.cache_data
def load_product_info_data():
    """제품 정보 데이터 로드"""
    try:
        df = pd.read_csv("product_info.csv")
        return df
    except FileNotFoundError:
        st.warning("product_info.csv 파일을 찾을 수 없습니다.")
        return pd.DataFrame(
            columns=["product_id", "installation_date", "hw_version", "fw_version"]
        )


# 데이터 로드
anomaly_df = load_anomaly_data()
alert_df = load_alert_data()
action_history_df = load_action_history_data()
product_info_df = load_product_info_data()

if anomaly_df is None:
    st.stop()

# 입력 폼
st.sidebar.header("조회 조건")

# Product ID 선택
product_ids = sorted(anomaly_df["product_id"].unique())
selected_product = st.sidebar.selectbox("Product ID 선택", product_ids)

# 시간 범위 선택
time_min = anomaly_df["time"].min()
time_max = anomaly_df["time"].max()

col1, col2 = st.sidebar.columns(2)
with col1:
    start_time = st.date_input(
        "시작 날짜",
        value=time_min.date(),
        min_value=time_min.date(),
        max_value=time_max.date(),
    )
with col2:
    start_hour = st.time_input("시작 시각", value=time_min.time())

col3, col4 = st.sidebar.columns(2)
with col3:
    end_time = st.date_input(
        "종료 날짜",
        value=time_max.date(),
        min_value=time_min.date(),
        max_value=time_max.date(),
    )
with col4:
    end_hour = st.time_input("종료 시각", value=time_max.time())

# datetime으로 변환
start_datetime = datetime.combine(start_time, start_hour)
end_datetime = datetime.combine(end_time, end_hour)

# 데이터 필터링
filtered_anomaly = anomaly_df[
    (anomaly_df["product_id"] == selected_product)
    & (anomaly_df["time"] >= start_datetime)
    & (anomaly_df["time"] <= end_datetime)
].copy()

filtered_alert = alert_df[
    (alert_df["product_id"] == selected_product)
    & (alert_df["time"] >= start_datetime)
    & (alert_df["time"] <= end_datetime)
].copy()

# 조치 내역 필터링 (해당 Product ID에 한하여, 시간 범위 제한 없음)
filtered_action_history = action_history_df[
    action_history_df["product_id"] == selected_product
].copy()
# 최근 발생일자 순으로 정렬 (내림차순)
if len(filtered_action_history) > 0:
    filtered_action_history = filtered_action_history.sort_values(
        "조치 일자", ascending=False
    )

# 결과 표시
if len(filtered_anomaly) == 0:
    st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
    st.stop()

st.subheader(f"Product ID: {selected_product}")
time_range_str = (
    f"{start_datetime.strftime('%Y-%m-%d %H:%M')} ~ "
    f"{end_datetime.strftime('%Y-%m-%d %H:%M')}"
)
st.markdown("### 제품 정보")
# product_info_df에서 해당 Product ID의 정보만 추출
selected_product_info = product_info_df[
    product_info_df["product_id"] == selected_product
]

if len(selected_product_info) == 0:
    st.info("해당 Product ID에 대한 제품 정보가 없습니다.")
else:
    # 행과 열을 transpose
    display_info = selected_product_info.rename(
        columns={
            "product_id": "Product ID",
            "installation_date": "설치일자",
            "hw_version": "HW 버전",
            "fw_version": "FW 버전",
        }
    )
    # Transpose: 행과 열을 바꿈
    transposed = display_info.set_index("Product ID").T
    st.dataframe(transposed, width="stretch", hide_index=False)


# 1. Product Anomaly Score Line Plot
st.markdown("### 1. Product Anomaly Score")

# 데이터 준비: 시간 순서대로 정렬
filtered_anomaly_sorted = filtered_anomaly.sort_values("time").copy()

# 시간과 스코어 추출
times = filtered_anomaly_sorted["time"]
scores = filtered_anomaly_sorted["product_anomaly_score"].values

# Line plot 생성 (색상으로 값 표현)
fig = go.Figure()

# Line plot 추가
fig.add_trace(
    go.Scatter(
        x=times,
        y=scores,
        mode="lines+markers",
        name="Anomaly Score",
        line={"color": "gray", "width": 2},
        marker={
            "size": 8,
            "color": scores,
            "colorscale": [[0, "green"], [0.5, "yellow"], [1, "red"]],
            "cmin": 0,
            "cmax": 3.5,
            "colorbar": {"title": "Anomaly Score"},
            "showscale": True,
        },
        hovertemplate="<b>%{x|%H:%M}</b><br>"
        + "Anomaly Score: %{y:.2f}<extra></extra>",
    )
)

fig.update_layout(
    title=f"Product Anomaly Score Timeline - {selected_product}",
    xaxis_title="시간",
    yaxis_title="Anomaly Score",
    height=400,
    xaxis={"tickangle": -45},
    yaxis={"range": [0, max(3.5, scores.max() * 1.1)]},
    hovermode="x unified",
)

st.plotly_chart(fig, width="stretch")

# 2. Sensor Anomaly Score (1.0 이상인 센서만)
st.markdown("### 2. AI에 의한 센서 이상 탐지 (Score ≥ 1.0)")

sensor_data_list = []
for _, row in filtered_anomaly.iterrows():
    time_str = row["time"].strftime("%Y-%m-%d %H:%M:%S")
    try:
        # sensor_anomaly_score를 딕셔너리로 파싱
        sensor_dict = ast.literal_eval(row["sensor_anomaly_score"])
        # 1.0 이상인 센서만 필터링
        high_sensors = {
            sensor: score for sensor, score in sensor_dict.items() if score >= 1.0
        }
        if high_sensors:
            # 센서명: 스코어 형식으로 변환
            sensor_str = ", ".join([f"{k}: {v:.2f}" for k, v in high_sensors.items()])
            sensor_data_list.append({"time": time_str, "sensors": sensor_str})
    except (ValueError, SyntaxError):
        # 문자열 파싱 실패 시 스킵
        continue

if sensor_data_list:
    sensor_df = pd.DataFrame(sensor_data_list)
    st.dataframe(sensor_df, width="stretch", hide_index=True)
else:
    st.info("해당 시간대에 Score ≥ 1.0인 센서가 없습니다.")

# 3. Alert Data
st.markdown("### 3. 제품 이벤트 이상 감지")
if len(filtered_alert) > 0:
    alert_display = filtered_alert[["time", "identifier"]].copy()
    alert_display["time"] = alert_display["time"].dt.strftime("%Y-%m-%d %H:%M:%S")
    st.dataframe(alert_display, width="stretch", hide_index=True)
else:
    st.info("해당 시간대에 알림이 없습니다.")

# 4. 조치 내역
st.markdown("### 4. 과거 조치 내역")
if len(filtered_action_history) > 0:
    action_display = filtered_action_history[
        ["조치 일자", "현상", "원인", "처방"]
    ].copy()
    action_display["조치 일자"] = action_display["조치 일자"].dt.strftime("%Y-%m-%d")
    st.dataframe(action_display, width="stretch", hide_index=True)
else:
    st.info("해당 Product ID에 대한 조치 내역이 없습니다.")

# AI 진단 버튼 및 결과 (하단)
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    ai_diagnosis_clicked = st.button(
        "🤖 AI 진단", type="primary", use_container_width=True
    )

# AI 진단 결과 표시
if ai_diagnosis_clicked:
    st.markdown("### 🤖 AI 진단 결과")

    # 진단 로직: 데이터 분석
    max_score = filtered_anomaly["product_anomaly_score"].max()
    avg_score = filtered_anomaly["product_anomaly_score"].mean()

    # 높은 스코어 센서 수집
    high_sensor_list = []
    for _, row in filtered_anomaly.iterrows():
        try:
            sensor_dict = ast.literal_eval(row["sensor_anomaly_score"])
            for sensor, score in sensor_dict.items():
                if score >= 1.0:
                    high_sensor_list.append((sensor, score))
        except (ValueError, SyntaxError):
            continue

    # Alert 종류 수집
    alert_types = (
        filtered_alert["identifier"].unique().tolist()
        if len(filtered_alert) > 0
        else []
    )

    # 과거 조치 내역에서 유사한 문제 확인
    similar_actions = []
    if len(filtered_action_history) > 0:
        recent_actions = filtered_action_history.head(3)
        similar_actions = recent_actions[["조치 일자", "현상", "처방"]].to_dict(
            "records"
        )

    # 진단 결과 생성
    diagnosis_parts = []

    # 1. 전체 상태 평가
    if max_score >= 2.5:
        severity = "높음"
        diagnosis_parts.append("⚠️ **심각도: 높음** - 즉시 조치가 필요합니다.")
    elif max_score >= 1.5:
        severity = "중간"
        diagnosis_parts.append("⚡ **심각도: 중간** - 주의 깊은 모니터링이 필요합니다.")
    else:
        severity = "낮음"
        diagnosis_parts.append("✅ **심각도: 낮음** - 현재 상태는 양호합니다.")

    # 2. 권장 조치 (심각도 다음에 표시)
    diagnosis_parts.append("\n**권장 조치:**")

    if max_score >= 2.5:
        if "temperature-sensor" in str(high_sensor_list):
            diagnosis_parts.append("1. 온도 센서 점검 및 교체 검토")
        if "과열" in alert_types or "오버 히팅" in alert_types:
            diagnosis_parts.append("2. 냉각 시스템 점검 및 정비")
        if similar_actions and any(
            "온도센서교체" in a["처방"] for a in similar_actions
        ):
            msg = "3. 과거 조치 이력상 온도 센서 교체가 효과적이었습니다."
            diagnosis_parts.append(msg)
        diagnosis_parts.append("4. 현장 점검을 통한 물리적 상태 확인 권장")
    elif max_score >= 1.5:
        diagnosis_parts.append("1. 지속적인 모니터링 및 데이터 수집")
        if high_sensor_list:
            diagnosis_parts.append("2. 이상 감지된 센서의 상세 점검")
        diagnosis_parts.append("3. 예방적 정비 일정 수립 검토")
    else:
        diagnosis_parts.append("1. 정기 점검 일정 유지")
        diagnosis_parts.append("2. 현재 상태 모니터링 지속")

    # 3. 분석 요약
    diagnosis_parts.append("\n**분석 요약:**")
    diagnosis_parts.append(f"- 최대 Anomaly Score: {max_score:.2f}")
    diagnosis_parts.append(f"- 평균 Anomaly Score: {avg_score:.2f}")

    # 4. 이상 센서 분석
    if high_sensor_list:
        diagnosis_parts.append("\n**이상 감지된 센서:**")
        unique_sensors = {}
        for sensor, score in high_sensor_list:
            if sensor not in unique_sensors or unique_sensors[sensor] < score:
                unique_sensors[sensor] = score

        for sensor, score in sorted(
            unique_sensors.items(), key=lambda x: x[1], reverse=True
        ):
            diagnosis_parts.append(f"- {sensor}: {score:.2f}")

    # 5. Alert 분석
    if alert_types:
        diagnosis_parts.append("\n**이벤트 이상 감지:**")
        for alert_type in alert_types:
            count = len(filtered_alert[filtered_alert["identifier"] == alert_type])
            diagnosis_parts.append(f"- {alert_type}: {count}회 발생")

    # 6. 과거 조치 내역 참고
    if similar_actions:
        diagnosis_parts.append("\n**과거 유사 사례:**")
        for action in similar_actions:
            action_str = f"- {action['조치 일자']}: {action['현상']} → {action['처방']}"
            diagnosis_parts.append(action_str)

    # 진단 결과 표시
    diagnosis_text = "\n".join(diagnosis_parts)

    # 심각도에 따라 다른 스타일 적용
    if severity == "높음":
        st.error(diagnosis_text)
    elif severity == "중간":
        st.warning(diagnosis_text)
    else:
        st.info(diagnosis_text)
