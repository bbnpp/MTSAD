"""
Mock-up 데이터 생성 스크립트
이상탐지 및 고장진단을 위한 샘플 데이터를 생성합니다.
"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd

# 설정
START_TIME = datetime(2024, 1, 15, 10, 0, 0)  # 시작 시간
TIME_INTERVAL_MINUTES = 2  # 2분 간격
NUM_TIME_POINTS = 30  # 1시간 = 30개 포인트 (2분 * 30 = 60분)

# Product ID 샘플
PRODUCT_IDS = [
    "RAG-00042",
    "RAG-00055",
    "RAG-00038",
    "RAG-00066",
    "RAG-00051",
    "RAG-00073",
]

# 센서 목록
SENSORS = [
    "temperature-sensor",
    "fuse-state",
    "current-position",
    "adb-value",
    "snr-db",
]

# 알림 종류
ALERT_IDENTIFIERS = [
    "사용제한",
    "인덕션 연결 끊김",
    "오버 히팅",
    "내부 과열",
    "스톨",
    "수동 모드",
    "라이트 커튼 인식",
    "온도 센서 연결 끊김",
]

# 조치 내역 관련 설정
PHENOMENA = ["가열불가", "작동 중 전원 꺼짐", "과열", "로봇팔 작동 이상"]

TREATMENTS = ["온도센서교체", "하네스교체", "X축 교체", "RGB버튼 교체"]

# 현상별 원인 템플릿
CAUSE_TEMPLATES = {
    "가열불가": [
        "온도 센서의 노후화로 인한 측정 오류가 발생했습니다.",
        "가열부 하네스의 접촉 불량으로 전류 공급이 원활하지 않았습니다.",
        "온도 제어 보드의 오작동으로 가열 기능이 비정상적으로 동작했습니다.",
    ],
    "작동 중 전원 꺼짐": [
        "전원 공급 하네스의 접촉 불량으로 인해 전원이 불안정했습니다.",
        "전원 보드의 과부하로 인한 보호 회로 작동으로 전원이 차단되었습니다.",
        "하네스 연결부의 산화로 인한 접촉 저항 증가가 원인입니다.",
    ],
    "과열": [
        "냉각 팬의 작동 불량으로 인해 내부 온도가 비정상적으로 상승했습니다.",
        "온도 센서의 측정 오류로 인해 과도한 가열이 발생했습니다.",
        "열 방출 경로의 막힘으로 인해 내부 열이 정상적으로 방출되지 않았습니다.",
    ],
    "로봇팔 작동 이상": [
        "X축 모터의 베어링 마모로 인해 정확한 위치 제어가 불가능했습니다.",
        "로봇팔 제어 보드의 신호 오류로 인해 정상적인 동작이 불가능했습니다.",
        "X축 가이드 레일의 마모와 오염으로 인해 부드러운 이동이 저해되었습니다.",
    ],
}

# 현상별 처방 매핑
PHENOMENON_TO_TREATMENT = {
    "가열불가": ["온도센서교체", "하네스교체"],
    "작동 중 전원 꺼짐": ["하네스교체"],
    "과열": ["온도센서교체"],
    "로봇팔 작동 이상": ["X축 교체"],
}

# 하드웨어 및 펌웨어 버전
HW_VERSIONS = ["1.0", "1.1", "1.2"]
FW_VERSIONS = ["3.4.1", "3.5.2", "3.6.6"]


def generate_normal_sensor_scores():
    """
    정상 상태의 센서 스코어 생성 (대부분 초록색)
    """
    scores = {}
    for sensor in SENSORS:
        # 정상 상태: 0에 가까운 작은 값
        score = np.random.exponential(0.05)
        score = min(score, 0.3)  # 최대 0.3까지
        scores[sensor] = round(score, 2)
    return scores


def generate_spike_anomaly_scores():
    """
    간헐적 불규칙 이상 패턴: 갑자기 높은 스코어 발생
    """
    scores = {}
    # 하나 또는 여러 센서가 높은 값을 가짐
    anomaly_sensors = np.random.choice(
        SENSORS, size=np.random.randint(1, len(SENSORS) + 1), replace=False
    )

    for sensor in SENSORS:
        if sensor in anomaly_sensors:
            # 이상 발생: 높은 스코어
            score = np.random.uniform(2.0, 3.5)
        else:
            # 정상 범위
            score = np.random.exponential(0.05)
            score = min(score, 0.3)
        scores[sensor] = round(score, 2)
    return scores


def generate_gradual_anomaly_scores(base_level):
    """
    점진적 증가 이상 패턴: 시간에 따라 점진적으로 증가
    base_level: 현재 이상 레벨 (0.0 ~ 3.5)
    """
    scores = {}
    # base_level을 중심으로 센서별 변동
    for sensor in SENSORS:
        variation = np.random.normal(0, 0.15)
        score = max(0, base_level + variation)
        # 점진적 증가이므로 최소값 보장
        score = max(score, base_level * 0.8)
        scores[sensor] = round(min(score, 3.5), 2)
    return scores


def generate_data():
    """
    Mock-up 데이터 생성
    - 대부분 정상 상태 (초록색)
    - 간헐적 불규칙 이상 (랜덤 스파이크)
    - 점진적 증가 이상 (특정 product_id에서 시간에 따라 증가)
    """
    records = []

    # 점진적 증가 패턴을 위한 상태 추적
    # {product_id: {'in_gradual_anomaly': bool,
    #               'anomaly_level': float, 'start_time': int}}
    product_states = {
        pid: {
            "in_gradual_anomaly": False,
            "anomaly_level": 0.0,
            "start_time": -1,
        }
        for pid in PRODUCT_IDS
    }

    # 점진적 이상이 발생할 product_id 선택 (1-2개)
    gradual_anomaly_products = np.random.choice(
        PRODUCT_IDS, size=np.random.randint(1, 3), replace=False
    )
    # 점진적 이상 시작 시간 (전반부에 시작)
    gradual_start_times = {
        pid: np.random.randint(5, 15) for pid in gradual_anomaly_products
    }

    for i in range(NUM_TIME_POINTS):
        current_time = START_TIME + timedelta(minutes=i * TIME_INTERVAL_MINUTES)
        time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")

        for product_id in PRODUCT_IDS:
            state = product_states[product_id]
            sensor_scores = None

            # 점진적 이상 패턴 체크
            if product_id in gradual_anomaly_products:
                start_time = gradual_start_times[product_id]
                if i >= start_time:
                    if not state["in_gradual_anomaly"]:
                        state["in_gradual_anomaly"] = True
                        state["anomaly_level"] = 0.5  # 시작 레벨
                        state["start_time"] = i

                    # 점진적으로 증가 (시간에 따라)
                    elapsed = i - state["start_time"]
                    # 최대 3.5까지 점진적 증가
                    state["anomaly_level"] = min(0.5 + (elapsed * 0.15), 3.5)
                    sensor_scores = generate_gradual_anomaly_scores(
                        state["anomaly_level"]
                    )

            # 간헐적 불규칙 이상 패턴 또는 정상 상태
            if sensor_scores is None:
                # 95% 확률로 정상 상태
                if np.random.random() < 0.95:
                    sensor_scores = generate_normal_sensor_scores()
                else:
                    # 5% 확률로 간헐적 이상 발생
                    sensor_scores = generate_spike_anomaly_scores()

            product_score = max(sensor_scores.values())

            record = {
                "time": time_str,
                "product_id": product_id,
                "sensor_anomaly_score": sensor_scores,
                "product_anomaly_score": round(product_score, 2),
            }
            records.append(record)

    return pd.DataFrame(records)


def generate_alert_data():
    """
    알림 시스템 Mock-up 데이터 생성
    - 간헐적으로 알림 발생
    - 알림은 연속적으로 발생할 수 있음
    """
    records = []

    # 알림 발생 상태 추적
    # {product_id: {'has_alert': bool, 'alert_type': str, 'duration': int}}
    alert_states = {
        pid: {"has_alert": False, "alert_type": None, "duration": 0}
        for pid in PRODUCT_IDS
    }

    for i in range(NUM_TIME_POINTS):
        current_time = START_TIME + timedelta(minutes=i * TIME_INTERVAL_MINUTES)
        time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")

        for product_id in PRODUCT_IDS:
            state = alert_states[product_id]

            # 기존 알림이 지속 중인 경우
            if state["has_alert"]:
                state["duration"] += 1
                # 알림 지속 시간 (1-5개 시간 포인트)
                if state["duration"] <= np.random.randint(1, 6):
                    record = {
                        "time": time_str,
                        "product_id": product_id,
                        "identifier": state["alert_type"],
                    }
                    records.append(record)
                else:
                    # 알림 종료
                    state["has_alert"] = False
                    state["alert_type"] = None
                    state["duration"] = 0
            else:
                # 새로운 알림 발생 (약 3-5% 확률)
                if np.random.random() < np.random.uniform(0.03, 0.05):
                    alert_type = np.random.choice(ALERT_IDENTIFIERS)
                    state["has_alert"] = True
                    state["alert_type"] = alert_type
                    state["duration"] = 1

                    record = {
                        "time": time_str,
                        "product_id": product_id,
                        "identifier": alert_type,
                    }
                    records.append(record)

    return pd.DataFrame(records)


def generate_action_history_data(num_records=15, days_back_min=7, days_back_max=90):
    """
    과거 조치 내역 Mock-up 데이터 생성
    며칠~몇개월 전의 조치 내역을 생성합니다.
    """
    records = []
    base_date = datetime.now()

    for _ in range(num_records):
        # 조치 일자: 며칠~몇개월 전 (7일~90일 전)
        days_ago = np.random.randint(days_back_min, days_back_max + 1)
        action_date = (base_date - timedelta(days=days_ago)).date()

        # Product ID 선택
        product_id = np.random.choice(PRODUCT_IDS)

        # 현상 선택
        phenomenon = np.random.choice(PHENOMENA)

        # 원인 선택 (현상에 맞는 원인 템플릿에서 선택)
        causes = CAUSE_TEMPLATES[phenomenon]
        cause = np.random.choice(causes)

        # 처방 선택 (현상에 맞는 처방 중에서 선택)
        possible_treatments = PHENOMENON_TO_TREATMENT[phenomenon]
        treatment = np.random.choice(possible_treatments)

        record = {
            "조치 일자": action_date.strftime("%Y-%m-%d"),
            "product_id": product_id,
            "현상": phenomenon,
            "원인": cause,
            "처방": treatment,
        }
        records.append(record)

    # 날짜 순서대로 정렬 (오래된 것부터)
    df = pd.DataFrame(records)
    df["조치 일자"] = pd.to_datetime(df["조치 일자"])
    df = df.sort_values("조치 일자")
    df["조치 일자"] = df["조치 일자"].dt.strftime("%Y-%m-%d")

    return df


def generate_product_info_data():
    """
    제품 정보 Mock-up 데이터 생성
    product_id별 설치 날짜, 하드웨어 버전, 펌웨어 버전 정보
    """
    records = []
    base_date = datetime.now()

    for product_id in PRODUCT_IDS:
        # 설치 날짜: 6개월~2년 전 사이의 랜덤 날짜
        days_ago = np.random.randint(180, 730)  # 6개월~2년
        installation_date = (base_date - timedelta(days=days_ago)).date()

        # 하드웨어 버전 선택
        hw_version = np.random.choice(HW_VERSIONS)

        # 펌웨어 버전 선택
        fw_version = np.random.choice(FW_VERSIONS)

        record = {
            "product_id": product_id,
            "installation_date": installation_date.strftime("%Y-%m-%d"),
            "hw_version": hw_version,
            "fw_version": fw_version,
        }
        records.append(record)

    df = pd.DataFrame(records)
    # product_id 순서대로 정렬
    df = df.sort_values("product_id")

    return df


def save_to_csv(df, filename="anomaly_data.csv"):
    """데이터프레임을 CSV로 저장"""
    # sensor_anomaly_score 딕셔너리를 문자열로 변환
    df_export = df.copy()
    df_export["sensor_anomaly_score"] = df_export["sensor_anomaly_score"].apply(
        lambda x: str(x) if isinstance(x, dict) else x
    )
    df_export.to_csv(filename, index=False)
    print(f"데이터가 {filename}에 저장되었습니다.")
    print(f"총 {len(df)}개의 레코드가 생성되었습니다.")


if __name__ == "__main__":
    print("Mock-up 데이터 생성 중...")

    # ML 이상탐지 데이터 생성
    print("\n1. ML 이상탐지 데이터 생성 중...")
    df_anomaly = generate_data()
    save_to_csv(df_anomaly, "anomaly_data.csv")
    print("\n생성된 이상탐지 데이터 샘플:")
    print(df_anomaly.head(10))

    # 알림 시스템 데이터 생성
    print("\n2. 알림 시스템 데이터 생성 중...")
    df_alert = generate_alert_data()
    df_alert.to_csv("alert_data.csv", index=False)
    print("알림 데이터가 alert_data.csv에 저장되었습니다.")
    print(f"총 {len(df_alert)}개의 알림 레코드가 생성되었습니다.")
    print("\n생성된 알림 데이터 샘플:")
    print(df_alert.head(10))

    # 조치 내역 데이터 생성
    print("\n3. 조치 내역 데이터 생성 중...")
    df_action = generate_action_history_data()
    df_action.to_csv("action_history.csv", index=False)
    print("조치 내역 데이터가 action_history.csv에 저장되었습니다.")
    print(f"총 {len(df_action)}개의 조치 내역 레코드가 생성되었습니다.")
    print("\n생성된 조치 내역 데이터 샘플:")
    print(df_action.head(10))

    # 제품 정보 데이터 생성
    print("\n4. 제품 정보 데이터 생성 중...")
    df_product_info = generate_product_info_data()
    df_product_info.to_csv("product_info.csv", index=False)
    print("제품 정보 데이터가 product_info.csv에 저장되었습니다.")
    print(f"총 {len(df_product_info)}개의 제품 정보 레코드가 생성되었습니다.")
    print("\n생성된 제품 정보 데이터:")
    print(df_product_info)
