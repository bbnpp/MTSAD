"""
Streamlit 이상탐지 및 고장진단 데모 앱
메인 홈페이지
"""

import streamlit as st

# 페이지 설정
st.set_page_config(page_title="이상탐지 및 고장진단", page_icon="🔍", layout="wide")

st.title("이상탐지 및 진단 데모")
st.markdown("---")

# 가상 데이터 사용 강조
warning_msg = (
    "⚠️ **주의**: 이 애플리케이션은 데모용으로 "
    "**가상 데이터(Mock-up Data)**를 사용합니다."
)
st.warning(warning_msg)

st.markdown("---")

# Flow 그래프 (Graphviz 사용)
st.markdown("### 워크플로우")

# Graphviz DOT 언어로 그래프 정의
graph = """
digraph {
    rankdir=TB;
    node [shape=box, style=rounded, fontsize=14];

    "대시보드" [label="📊 대시보드"];
    "개선된알람" [label="🚨 개선된 알람"];
    "상세정보" [label="📋 상세 정보"];
    "AI진단" [label="🤖 AI 진단"];

    "대시보드" -> "상세정보";
    "개선된알람" -> "상세정보";
    "상세정보" -> "AI진단";
}
"""

st.graphviz_chart(graph)

st.markdown("---")

# Flow 설명
st.markdown("""
**워크플로우 설명:**

1. **대시보드** 또는 **개선된 알람**에서 이상을 발견
2. **상세 정보** 페이지에서 해당 Product ID의 상세 데이터 확인
3. **AI 진단** 기능으로 권장 조치 확인
""")
