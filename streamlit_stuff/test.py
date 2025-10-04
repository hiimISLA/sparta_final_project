import streamlit as st
import pandas as pd
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import altair as alt
from streamlit_autorefresh import st_autorefresh
from streamlit_option_menu import option_menu
import numpy as np
import streamlit as st
import plotly.express as px

import streamlit as st

# source venv/bin/activate    

# # 페이지 폭/사이드바 먼저 세팅 (가급적 맨 위)
# st.set_page_config(layout="wide", initial_sidebar_state="collapsed")

st.markdown(
    """
    <style>
        /* 전체 페이지 상단 여백 제거 */
        .block-container {
            padding-top: 3rem;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------------------
# 세션 상태 초기화 fsdjlfjslj
# -------------------------------
if "results_df" not in st.session_state:
    st.session_state["results_df"] = None
if "user_inputs" not in st.session_state:
    st.session_state["user_inputs"] = None
if "active_tab" not in st.session_state:
    st.session_state['active_tab'] = 0

# -------------------------------
# 탭 메뉴
# -------------------------------
menu_options = ["광고 소진 확인", "소진 대응 확인", "수요 예측 확인"]
menu_icons = ["graph-up", "shield-check", "stars"]

selected = option_menu(
    None,
    menu_options,
    icons=menu_icons,
    orientation="horizontal",
    default_index=st.session_state["active_tab"],
    styles={
        "container": {"padding": "0!important", "background-color": "black"},
        "icon": {"font-size": "18px"},
        "nav-link": {
            "font-size": "16px",
            "text-align": "center",
            "margin": "0px",
            "--hover-color": "#eee",
        },
        "nav-link-selected": {"background-color": "#EA2F3E", "color": "white"},
    },
)
# -------------------------------
# 탭1: "광고 소진 확인
# -------------------------------
if selected == "광고 소진 확인":
    @st.cache_data
    def df1_1():
        return pd.read_csv("df1_1.csv")
    df1_1 = df1_1()

    # 위/아래 영역 나누기
    top, bottom = st.container(), st.container()
    with top:
        
        # 광고 / 매체 선택 필터를 가로로 배치
        col1, col2 = st.columns(2)
        with col1:
            ads_filter = st.multiselect("광고 선택", df1_1["광고ID"].unique())
        with col2:
            media_filter = st.multiselect("매체 선택", df1_1["매체ID"].unique())
        
        df_filtered = df1_1.copy()
        if ads_filter:
            df_filtered = df_filtered[df_filtered["광고ID"].isin(ads_filter)]
        if media_filter:
            df_filtered = df_filtered[df_filtered["매체ID"].isin(media_filter)]
        
        # 스크롤 가능한 데이터프레임
        st.dataframe(df_filtered, height=300)  # height=300 → 스크롤 가능
    
    with bottom:
        @st.cache_data
        def df1_2():
            df = pd.read_parquet("df1_2.parquet")
            df = df.rename(columns={"광고ID": "ads_idx", "매체ID": "mda_idx"})
            return df

        df1_2 = df1_2()
        df1_2["rpt_time_date"] = pd.to_datetime(df1_2["rpt_time_date"], errors="coerce")

        # ---------------- 아래쪽 ----------------
        # st.markdown("### 📈 일별 추이 그래프")

        # 기간 선택 (라디오 버튼 or 탭)
        period = st.radio(" ", ["이전 12개월", "이전 6개월", "이전 3개월"], horizontal=True)

        # 필터 적용
        df_filtered = df1_2.copy()
        if ads_filter:
            df_filtered = df_filtered[df_filtered["ads_idx"].isin(ads_filter)]
        if media_filter:
            df_filtered = df_filtered[df_filtered["mda_idx"].isin(media_filter)]

        if not df_filtered.empty:
            # 일별 합계
            df_daily_sum = df_filtered.groupby("rpt_time_date", as_index=False)["turn_sum"].sum()

            # 오늘 날짜 기준으로 기간 필터
            max_date = df_daily_sum["rpt_time_date"].max()
            if period == "이전 6개월":
                start_date = max_date - pd.DateOffset(months=6)
            elif period == "이전 3개월":
                start_date = max_date - pd.DateOffset(months=3)
            else:  # 최근 12개월
                start_date = max_date - pd.DateOffset(months=12)

            df_daily_sum = df_daily_sum[df_daily_sum["rpt_time_date"] >= start_date]

            # 그래프 출력
            st.line_chart(
                df_daily_sum.set_index("rpt_time_date"),
                color="#EA2F3E")   # 원하는 색상 (빨간색)            )
   
        else:
            st.info("⚠️ 선택한 광고/매체에 해당하는 데이터가 없습니다.")


#_----------------------------------------------------------------------------
# -------------------------------
# 탭2: 소진 대응 확인
# -------------------------------
elif selected == "소진 대응 확인":
    @st.cache_data
    def load_df():
        df = pd.read_csv("df2_1.csv")
        df["rpt_time_date"] = pd.to_datetime(df["rpt_time_date"], errors="coerce")
        df["ads_edate"] = pd.to_datetime(df["ads_edate"], errors="coerce")
        df["goal_final_num"] = pd.to_numeric(df["goal_final"], errors="coerce")
        return df

    df2 = load_df()

    import datetime
    last_update = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.caption(f"⏱️ 새로고침 기준: 2025-08-29 12:00:00")
    

    # -------------------------------
    # 상단 KPI 요약
    # -------------------------------
    df2["remain"] = df2["goal_final_num"] - df2["turn_sum"]
    df2["achieve_rate"] = np.where(df2["goal_final_num"] > 0,
                                   (df2["turn_sum"] / df2["goal_final_num"]) * 100, 0)
    df2["days_left"] = (df2["ads_edate"] - df2["rpt_time_date"]).dt.days

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("전체 광고", 24955)
    col2.metric("위험 광고", (df2["achieve_rate"] > 120).sum())
    col3.metric("주의 광고", ((df2["achieve_rate"] < 80) & (df2["days_left"] < 3)).sum())
    col4.metric("평균 달성률", f"{df2['achieve_rate'].mean():.1f}%")

    # -------------------------------
    # 정렬 기준 선택
    # -------------------------------
    sort_option = st.selectbox("정렬 기준", ["우선순위", "남은 일수 오름차순", "달성률 낮은 순"])

    # 상태 분류
    alert_cards = []
    for _, row in df2.iterrows():
        goal = int(row["goal_final_num"]) if pd.notna(row["goal_final_num"]) else 0
        turn_sum = int(row["turn_sum"]) if pd.notna(row["turn_sum"]) else 0
        days_left = int(row["days_left"]) if pd.notna(row["days_left"]) else None
        remain = int(row["remain"]) if pd.notna(row["remain"]) else None
        achieve_rate = row["achieve_rate"]

        if achieve_rate > 120:
            status, color, priority = "소진과다⚠️", "#FF4B4B", 1
        elif achieve_rate < 80 and days_left is not None and days_left < 3:
            status, color, priority = "소진부족❗", "#FFA500", 2
        else:
            status, color, priority = "정상✅", "#4CAF50", 3

        card_html = f"""
        <div style="display:flex; flex-direction:column; border-left:6px solid {color};
                    padding:8px 12px; margin-bottom:6px; background-color:#1e1e1e; border-radius:6px;">
          <div style="font-size:14px; color:white; margin-bottom:4px;">
            <b style="color:{color};">{status}</b> | 광고 <b>{row['ads_idx']}</b> / 매체 <b>{row['mda_idx']}</b>
          </div>
          <div style="font-size:13px; color:#ccc;">
            남은 일수: <b>{days_left if days_left is not None else 'N/A'}일</b> |
            남은 재고: <b>{remain if remain is not None else 'N/A'}</b> |
            달성률: <b>{achieve_rate:.1f}%</b>
          </div>
        </div>
        """

        if priority < 3:  # 정상은 제외
            alert_cards.append((priority, days_left, achieve_rate, card_html))

    # -------------------------------
    # 정렬 적용
    # -------------------------------
    if sort_option == "우선순위":
        alert_cards = sorted(alert_cards, key=lambda x: x[0])  # priority
    elif sort_option == "남은 일수 오름차순":
        alert_cards = sorted(alert_cards, key=lambda x: (x[1] if x[1] is not None else 9999))
    elif sort_option == "달성률 낮은 순":
        alert_cards = sorted(alert_cards, key=lambda x: x[2])

    # -------------------------------
    # 카드 출력
    # -------------------------------
    for _, _, _, card in alert_cards:
        st.markdown(card, unsafe_allow_html=True)






# -------------------------------
# 탭3: 수요 예측 확인 
# -------------------------------
elif selected == "수요 예측 확인":
    @st.cache_data
    def df3_1():
        return pd.read_csv("df3_1_2.csv")   # parquet → csv 로 변경

    df_merged = df3_1()

    # 광고는 1개만 선택
    ad_name = st.selectbox("광고 선택", df_merged['ads_idx'].unique())

    # 선택된 광고에 속한 매체들만 표시 (여러 개 허용)
    available_mdas = df_merged.loc[df_merged['ads_idx']==ad_name, 'mda_idx'].unique()
    mda_names = st.multiselect("매체 선택", available_mdas, default=available_mdas)

    # 조건 필터링
    cond_df = df_merged[
        (df_merged['ads_idx']==ad_name) &
        (df_merged['mda_idx'].isin(mda_names))
    ].sort_values('rpt_time_date')

    # ---------------- 그래프 ----------------
    if not cond_df.empty:
        # 숫자 변환 (NaN → 0)
        cond_df["turn_sum"] = pd.to_numeric(cond_df["turn_sum"], errors="coerce").fillna(0)

        # pivot_table 집계
        pivot_df = cond_df.pivot_table(
            index="rpt_time_date",
            columns="mda_idx",
            values="turn_sum",
            aggfunc="sum"
        )

        # Streamlit 라인차트 (매체별 색상 자동 구분)
        st.line_chart(pivot_df)
    else:
        st.info("선택한 조건에 해당하는 데이터가 없습니다.")
