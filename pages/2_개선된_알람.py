"""
개선된 알람 페이지
product_anomaly_score가 alpha를 넘은 기간이 beta분 이상인 경우를 감지합니다.
"""

import ast

import pandas as pd
import streamlit as st

# 페이지 설정
st.set_page_config(page_title="개선된 알람", page_icon="🚨", layout="wide")

st.title("🚨 개선된 알람")
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


# 데이터 로드
anomaly_df = load_anomaly_data()
alert_df = load_alert_data()

if anomaly_df is None:
    st.stop()

# 파라미터 설정
st.sidebar.header("알람 설정")

alpha = st.sidebar.slider(
    "Alpha (Anomaly Score 임계값)",
    min_value=0.0,
    max_value=3.5,
    value=1.0,
    step=0.1,
    help="이 값을 넘는 경우 이상으로 간주합니다.",
)

beta = st.sidebar.slider(
    "Beta (최소 지속 시간, 분)",
    min_value=2,
    max_value=30,
    value=4,
    step=2,
    help="이 시간 이상 지속되어야 알람이 발생합니다.",
)

# 알람 감지 로직
st.subheader("Incident History")

# 각 product_id별로 처리
product_ids = sorted(anomaly_df["product_id"].unique())
alarms = []

for product_id in product_ids:
    # 해당 product_id의 데이터만 필터링 및 시간 순 정렬
    product_data = anomaly_df[anomaly_df["product_id"] == product_id].sort_values(
        "time"
    )

    if len(product_data) == 0:
        continue

    # 연속된 기간 찾기
    i = 0
    while i < len(product_data):
        if product_data.iloc[i]["product_anomaly_score"] > alpha:
            # 연속된 기간의 시작
            start_idx = i
            end_idx = i

            # 연속된 기간 찾기
            while (
                end_idx + 1 < len(product_data)
                and product_data.iloc[end_idx + 1]["product_anomaly_score"] > alpha
            ):
                end_idx += 1

            # 기간 계산
            start_time = product_data.iloc[start_idx]["time"]
            end_time = product_data.iloc[end_idx]["time"]
            duration_minutes = (end_time - start_time).total_seconds() / 60 + 2
            # 마지막 포인트까지 포함하므로 +2분 (2분 간격)

            # beta 분 이상인지 확인
            if duration_minutes >= beta:
                # 해당 기간의 데이터 수집
                period_data = product_data.iloc[start_idx : end_idx + 1]

                # AI 센서 이상 탐지 수집
                sensor_anomalies = []
                for _, row in period_data.iterrows():
                    try:
                        sensor_dict = ast.literal_eval(row["sensor_anomaly_score"])
                        for sensor, score in sensor_dict.items():
                            if score >= 1.0:
                                sensor_anomalies.append(
                                    {
                                        "time": row["time"],
                                        "sensor": sensor,
                                        "score": score,
                                    }
                                )
                    except (ValueError, SyntaxError):
                        continue

                # 제품 이벤트 이상 감지 수집
                period_alerts = alert_df[
                    (alert_df["product_id"] == product_id)
                    & (alert_df["time"] >= start_time)
                    & (alert_df["time"] <= end_time)
                ].copy()

                alarms.append(
                    {
                        "product_id": product_id,
                        "start_time": start_time,
                        "end_time": end_time,
                        "duration_minutes": duration_minutes,
                        "max_score": period_data["product_anomaly_score"].max(),
                        "sensor_anomalies": sensor_anomalies,
                        "alerts": period_alerts,
                    }
                )

            i = end_idx + 1
        else:
            i += 1

# 결과 표시
if len(alarms) == 0:
    st.info(f"조건에 맞는 알람이 없습니다. (Alpha: {alpha}, Beta: {beta}분 이상)")
else:
    st.success(f"총 {len(alarms)}개의 알람이 감지되었습니다.")

    for idx, alarm in enumerate(alarms, 1):
        with st.expander(
            f"알람 #{idx}: {alarm['product_id']} "
            f"({alarm['start_time'].strftime('%Y-%m-%d %H:%M')} ~ "
            f"{alarm['end_time'].strftime('%Y-%m-%d %H:%M')}, "
            f"{alarm['duration_minutes']:.1f}분)",
            expanded=False,
        ):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Product ID", alarm["product_id"])
            with col2:
                st.metric("지속 시간", f"{alarm['duration_minutes']:.1f}분")
            with col3:
                st.metric("최대 Score", f"{alarm['max_score']:.2f}")

            # 기간
            st.markdown("**기간:**")
            st.write(
                f"{alarm['start_time'].strftime('%Y-%m-%d %H:%M:%S')} ~ "
                f"{alarm['end_time'].strftime('%Y-%m-%d %H:%M:%S')}"
            )

            # 제품 이벤트 이상 감지
            st.markdown("**제품 이벤트 이상 감지:**")
            if len(alarm["alerts"]) > 0:
                alert_display = alarm["alerts"][["time", "identifier"]].copy()
                alert_display["time"] = alert_display["time"].dt.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                alert_display.columns = ["시간", "이벤트"]
                st.dataframe(alert_display, width="stretch", hide_index=True)
            else:
                st.info("해당 기간에 이벤트 이상 감지가 없습니다.")

            # AI 센서 이상 탐지
            st.markdown("**AI 센서 이상 탐지:**")
            if alarm["sensor_anomalies"]:
                sensor_df = pd.DataFrame(alarm["sensor_anomalies"])
                sensor_df["time"] = sensor_df["time"].dt.strftime("%Y-%m-%d %H:%M:%S")
                sensor_display = sensor_df[["time", "sensor", "score"]].copy()
                sensor_display.columns = ["시간", "센서", "스코어"]
                st.dataframe(sensor_display, width="stretch", hide_index=True)
            else:
                st.info("해당 기간에 Score ≥ 1.0인 센서가 없습니다.")
