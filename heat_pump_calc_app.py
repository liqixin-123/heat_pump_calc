# -*- coding: utf-8 -*-
"""
老旧住宅空气源热泵协同改造计算工具——竞赛专用软件
分工对应：
页面1：建筑围护参数（建筑与围护组负责）
页面2：末端+热泵参数（末端与热泵组负责）
页面3：三套方案计算结果+经济性+节能率
页面4：强制手算校核页（满足竞赛手算校验要求）
开发：软件与经济组，全代码逐行注释，参数标注来源
核心三套方案：
方案1：仅更换空气源热泵，围护不改造（基准方案）
方案2：围护结构保温改造 + 常规空气源热泵
方案3：围护改造 + 低温采暖末端 + 低温型空气源热泵
"""
import streamlit as st
import pandas as pd
import plotly.express as px

# ====================== 全局页面基础配置 ======================
st.set_page_config(
    page_title="郑州老旧住宅热泵协同改造测算工具",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 隐藏默认菜单与页脚，竞赛演示界面美化
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# 侧边栏：统一记录所有参数来源，满足竞赛参数溯源要求
with st.sidebar:
    st.title("📌 参数来源台账（必查）")
    st.markdown("""
    1. 建筑传热系数K：《民用建筑热工设计规范》GB 50176、中原地区老旧住宅实测文献
    2. 郑州采暖度日数HDD18：中国建筑节能气象参数数据库
    3. 空气源热泵SCOP：美的低温型空气源热泵官方样本手册
    4. 电价、改造材料费：河南郑州市场家装/旧房改造市场价调研
    5. 热负荷计算公式：《供热工程》教材经典稳态传热负荷公式
    """)
    st.divider()
    page_select = st.radio("功能页面切换", [
        "1.建筑围护参数录入",
        "2.采暖末端&热泵参数录入",
        "3.三套方案计算结果",
        "4.手工校核验算页（竞赛强制）"
    ])

# ====================== 全局通用计算公式（核心热工公式） ======================
# 1.围护结构基本传热负荷 W
def calc_wall_win_load(wall_area, win_area, K_wall, K_win, delta_T):
    wall_load = wall_area * K_wall * delta_T
    win_load = win_area * K_win * delta_T
    total_env_load = wall_load + win_load
    return wall_load, win_load, total_env_load

# 2.冷风渗透热负荷 W
def calc_infiltration_load(volume, n, rho, cp, delta_T):
    mass_flow = rho * volume * n / 3600
    infiltration_Q = mass_flow * cp * delta_T
    return infiltration_Q

# 3.总设计热负荷 kW
def total_heat_load(env_load, infil_load):
    total_W = env_load + infil_load
    total_kW = total_W / 1000
    return total_kW, total_W

# 4.全年采暖总需热量 单位：kWh
def calc_year_heat(total_W, HDD, indoor_T):
    day_hour = 24
    delta_T_day = indoor_T - 18  # HDD18基准温度18℃
    year_heat_kwh = total_W * HDD * day_hour / (delta_T_day * 1000)
    return year_heat_kwh

# 5.热泵年耗电量计算
def elec_consume(year_heat, SCOP):
    elec = year_heat / SCOP
    return elec

# 6.简单静态投资回收期（年） 初投资差额 ÷ 每年节约电费
def payback_period(add_invest, save_elec, elec_price):
    if save_elec <= 0:
        return None
    year_save = save_elec * elec_price
    pay_year = add_invest / year_save
    return round(pay_year, 2)

# ====================== 页面1：建筑围护参数录入 ======================
if page_select == "1.建筑围护参数录入":
    st.header("🏠 郑州老旧住宅基础与围护结构参数录入")
    st.info("每一项输入框后的问号可查看物理意义、单位，由建筑围护组确定参数")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("建筑基础尺寸")
        build_area = st.number_input("建筑面积 m²", value=120.0, help="住宅套内+公摊建筑面积，本次案例固定120㎡")
        floor_h = st.number_input("楼层层高 m", value=2.8, help="室内层高，用来计算房间体积")
        room_volume = build_area * floor_h
        st.metric("室内总体积 m³", value=round(room_volume, 2))
        wall_area = st.number_input("外墙总面积 m²", value=85.0, help="建筑外围护外墙面积，不含内墙")
        win_area = st.number_input("外窗总面积 m²", value=22.0, help="所有外窗面积之和")
    with col2:
        st.subheader("传热系数K值")
        K_wall_old = st.number_input("改造前外墙K W/(m²·K)", value=1.8, help="旧房红砖外墙无保温传热系数，来源热工实测文献")
        K_wall_new = st.number_input("改造后外墙保温K W/(m²·K)", value=0.45, help="外墙外保温改造后传热系数，GB50176节能限值")
        K_win_old = st.number_input("改造前普通窗户K W/(m²·K)", value=2.8, help="原有单层塑钢窗传热系数")
        K_win_new = st.number_input("改造后断桥铝窗K W/(m²·K)", value=1.8, help="节能断桥铝中空玻璃窗户K值")

    st.divider()
    st.subheader("气象与室内设计参数（郑州地区固定值）")
    col3, col4 = st.columns(2)
    with col3:
        Tin = st.number_input("室内采暖设计温度 ℃", value=20, help="采暖规范室内设计温度")
        Tout = st.number_input("郑州冬季采暖室外设计温度 ℃", value=-7, help="郑州暖通设计室外低温，供热手册取值")
        delta_T = Tin - Tout
        st.metric("室内外设计温差 ΔT(K)", value=delta_T)
        HDD = st.number_input("郑州HDD18采暖度日数 ℃·d", value=2106, help="基准18℃采暖度日数，官方气象数据库")
    with col4:
        n_air = st.number_input("冷风渗透换气次数 次/h", value=0.5, help="老旧住宅门窗缝隙冷风渗透换气次数")
        rho_air = st.number_input("空气密度 kg/m³", value=1.2, help="常温常压干空气密度，传热学常用取值")
        cp_air = st.number_input("空气定压比热容 J/(kg·K)", value=1005, help="干空气定压比热容")

    st.session_state["build"] = {
        "area": build_area, "volume": room_volume, "wall": wall_area, "win": win_area,
        "Kw_old": K_wall_old, "Kw_new": K_wall_new, "Kwin_old": K_win_old, "Kwin_new": K_win_new,
        "Tin": Tin, "Tout": Tout, "dT": delta_T, "HDD": HDD,
        "n": n_air, "rho": rho_air, "cp": cp_air
    }
    st.success("✅ 建筑围护参数已保存，前往第二页录入热泵末端参数")

# ====================== 页面2：末端&热泵参数录入 ======================
elif page_select == "2.采暖末端&热泵参数录入":
    st.header("🔥 采暖末端形式 + 空气源热泵机组参数录入")
    st.info("由末端与热泵组填写，SCOP取自厂家样本，造价取自市场调研")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("空气源热泵SCOP（制热性能系数）")
        SCOP1 = st.number_input("方案1常规热泵SCOP", value=2.6, help="常温空气源热泵冬季平均制热系数")
        SCOP2 = st.number_input("方案2常规热泵SCOP", value=2.6, help="围护改造只降负荷，热泵机型不变，SCOP不变")
        SCOP3 = st.number_input("方案3低温专用热泵SCOP", value=3.2, help="低温机型+低温地暖末端，供水温度低，机组效率更高")
    with col2:
        st.subheader("初投资造价（单价取自郑州市场调研）")
        elec_price = st.number_input("居民电价 元/kWh", value=0.56, help="河南居民阶梯电价均价")
        pump_only_cost = st.number_input("单台空气源热泵采购安装费 元", value=12500, help="常规冷暖热泵整套造价")
        wall_reform_cost = st.number_input("外墙保温改造总造价 元", value=14200, help="全屋外墙保温施工材料费+人工费")
        low_temp_end_cost = st.number_input("低温地暖末端改造费用 元", value=9800, help="全屋地暖铺设施工费用")

    st.session_state["equip"] = {
        "SCOP1": SCOP1, "SCOP2": SCOP2, "SCOP3": SCOP3,
        "elec_price": elec_price,
        "cost_pump": pump_only_cost,
        "cost_wall": wall_reform_cost,
        "cost_lowend": low_temp_end_cost
    }
    st.success("✅ 末端热泵参数保存完毕，进入第三页一键计算三套方案")

# ====================== 页面3：三套方案整体计算 + 图表对比 ======================
elif page_select == "3.三套方案计算结果":
    build = st.session_state["build"]
    equip = st.session_state["equip"]
    st.header("📊 三套改造方案热负荷、能耗、经济性全自动计算")
    st.divider()

    # ========== 方案1（基准） ==========
    wall_load_1, win_load_1, env_total_1 = calc_wall_win_load(
        build["wall"], build["win"], build["Kw_old"], build["Kwin_old"], build["dT"]
    )
    infil_load = calc_infiltration_load(
        build["volume"], build["n"], build["rho"], build["cp"], build["dT"]
    )
    total_kW_1, total_W_1 = total_heat_load(env_total_1, infil_load)
    year_heat_1 = calc_year_heat(total_W_1, build["HDD"], build["Tin"])
    elec_1 = elec_consume(year_heat_1, equip["SCOP1"])
    invest_1 = equip["cost_pump"]
    year_cost_1 = elec_1 * equip["elec_price"]

    # ========== 方案2 ==========
    wall_load_2, win_load_2, env_total_2 = calc_wall_win_load(
        build["wall"], build["win"], build["Kw_new"], build["Kwin_new"], build["dT"]
    )
    total_kW_2, total_W_2 = total_heat_load(env_total_2, infil_load)
    year_heat_2 = calc_year_heat(total_W_2, build["HDD"], build["Tin"])
    elec_2 = elec_consume(year_heat_2, equip["SCOP2"])
    invest_2 = equip["cost_pump"] + equip["cost_wall"]
    year_cost_2 = elec_2 * equip["elec_price"]
    save_elec_2 = elec_1 - elec_2
    payback_2 = payback_period(equip["cost_wall"], save_elec_2, equip["elec_price"])
    # 节能率（相对方案1基准）
    load_save_rate_2 = round((total_kW_1 - total_kW_2)/total_kW_1*100,2)
    elec_save_rate_2 = round((elec_1 - elec_2)/elec_1*100,2)

    # ========== 方案3 ==========
    wall_load_3, win_load_3, env_total_3 = calc_wall_win_load(
        build["wall"], build["win"], build["Kw_new"], build["Kwin_new"], build["dT"]
    )
    total_kW_3, total_W_3 = total_heat_load(env_total_3, infil_load)
    year_heat_3 = calc_year_heat(total_W_3, build["HDD"], build["Tin"])
    elec_3 = elec_consume(year_heat_3, equip["SCOP3"])
    invest_3 = equip["cost_pump"] + equip["cost_wall"] + equip["cost_lowend"]
    year_cost_3 = elec_3 * equip["elec_price"]
    save_elec_3 = elec_1 - elec_3
    payback_3 = payback_period((equip["cost_wall"] + equip["cost_lowend"]), save_elec_3, equip["elec_price"])
    load_save_rate_3 = round((total_kW_1 - total_kW_3)/total_kW_1*100,2)
    elec_save_rate_3 = round((elec_1 - elec_3)/elec_1*100,2)

    # ========== 指标卡片（新增节能率展示） ==========
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("方案1｜热负荷(kW)", round(total_kW_1,2))
        st.metric("方案1｜年耗电(kWh)", round(elec_1,1))
    with col_b:
        st.metric("方案2｜热负荷(kW)", round(total_kW_2,2), delta=f"-{load_save_rate_2}%")
        st.metric("方案2｜年耗电(kWh)", round(elec_2,1), delta=f"-{elec_save_rate_2}%")
    with col_c:
        st.metric("方案3｜热负荷(kW)", round(total_kW_3,2), delta=f"-{load_save_rate_3}%")
        st.metric("方案3｜年耗电(kWh)", round(elec_3,1), delta=f"-{elec_save_rate_3}%")
    st.divider()

    # ========== 完整数据表，增加节能率列 ==========
    result_df = pd.DataFrame({
        "改造方案": ["方案1：仅更换热泵", "方案2：围护改造+常规热泵", "方案3：围护+低温末端+低温热泵"],
        "设计热负荷(kW)": [round(total_kW_1, 2), round(total_kW_2, 2), round(total_kW_3, 2)],
        "热负荷削减率(%)":["基准", load_save_rate_2, load_save_rate_3],
        "全年采暖需热量(kWh)": [round(year_heat_1, 1), round(year_heat_2, 1), round(year_heat_3, 1)],
        "热泵年耗电量(kWh)": [round(elec_1, 1), round(elec_2, 1), round(elec_3, 1)],
        "耗电量节能率(%)":["基准", elec_save_rate_2, elec_save_rate_3],
        "项目总初投资(元)": [invest_1, invest_2, invest_3],
        "年采暖电费(元)": [round(year_cost_1, 2), round(year_cost_2, 2), round(year_cost_3, 2)],
        "静态投资回收期(年)": ["基准", payback_2, payback_3]
    })
    st.dataframe(result_df, use_container_width=True)

    # 导出CSV，中文不乱码
    csv_bytes = result_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(label="📥 下载计算结果CSV", data=csv_bytes,
                       file_name="热泵改造方案结果_含节能率.csv", mime="text/csv")
    st.divider()

    # ========== 选项卡图表，统一学术白底，放大字体 ==========
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊热负荷对比","🔥年需热量对比","⚡年耗电量对比","💡耗电量节能率对比","💰静态回收期对比"
    ])
    color_list = ["#1f77b4","#ff7f0e","#2ca02c"]
    layout_common = dict(
        template="plotly_white",
        hovermode="x unified",
        height=440,
        font=dict(size=13)
    )

    with tab1:
        fig1 = px.bar(result_df, x="改造方案", y="设计热负荷(kW)", title="三套方案采暖设计热负荷对比",
                      color="改造方案", color_discrete_sequence=color_list)
        fig1.update_layout(**layout_common)
        st.plotly_chart(fig1, use_container_width=True)

    with tab2:
        fig2 = px.bar(result_df, x="改造方案", y="全年采暖需热量(kWh)", title="建筑全年采暖需热量对比",
                      color="改造方案", color_discrete_sequence=color_list)
        fig2.update_layout(**layout_common)
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        fig3 = px.bar(result_df, x="改造方案", y="热泵年耗电量(kWh)", title="热泵系统年耗电量对比",
                      color="改造方案", color_discrete_sequence=color_list)
        fig3.update_layout(**layout_common)
        st.plotly_chart(fig3, use_container_width=True)

    with tab5:
        df_pay = result_df.copy()
        df_pay = df_pay[df_pay["静态投资回收期(年)"]!="基准"]
        fig4 = px.bar(df_pay, x="改造方案", y="静态投资回收期(年)", title="方案静态投资回收期对比",
                      template="plotly_white", color="改造方案", color_discrete_sequence=color_list[1:])
        fig4.update_layout(**layout_common)
        st.plotly_chart(fig4, use_container_width=True)

    with tab4:
        df_save = result_df.copy()
        df_save = df_save[df_save["耗电量节能率(%)"]!="基准"]
        fig5 = px.bar(df_save, x="改造方案", y="耗电量节能率(%)", title="相对基准方案耗电量节能率对比",
                      template="plotly_white", color="改造方案", color_discrete_sequence=color_list[1:])
        fig5.update_layout(**layout_common)
        st.plotly_chart(fig5, use_container_width=True)

    st.divider()
    # ========== 方案推荐（写入节能率） ==========
    text_p2 = payback_2 if payback_2 is not None else "——"
    text_p3 = payback_3 if payback_3 is not None else "——"
    st.subheader("✅ 最终方案推荐与理由")
    st.markdown(f"""
    1. **方案1：仅更换热泵**，围护结构不改造，作为基准对照；热负荷{round(total_kW_1,2)}kW，无节能改造，不推荐实施。
    2. **方案2：围护保温改造+常规空气源热泵**：
        - 热负荷削减 {load_save_rate_2}%，耗电量节能 {elec_save_rate_2}%；
        - 静态投资回收期 {text_p2} 年；外墙保温施工成熟，改造风险低，适合预算有限老旧住宅。
    3. **方案3：围护改造+低温采暖末端+低温热泵**：
        - 热负荷削减 {load_save_rate_3}%，耗电量节能 {elec_save_rate_3}%；
        - 系统效率最高、年度电费最低，但初投资更高，静态投资回收期 {text_p3} 年；适合预算充足、允许室内改造的住宅。

    >综合老旧小区现场施工条件、业主经济承受能力，**优先推荐方案2**；预算充足条件下可选用方案3。
    """)

# ====================== 页面4：强制手工校核验算页面 ======================
elif page_select == "4.手工校核验算页（竞赛强制）":
    st.header("✍️ 热负荷 & 耗电量手工校核页面")
    st.warning("必须完成1次手算，和程序计算结果做对照，满足竞赛校核规则")
    build = st.session_state["build"]
    equip = st.session_state["equip"]
    st.subheader("1. 热负荷手算步骤演示（以方案1为例）")
    st.markdown(f"""
    **已知输入参数：**
    外墙面积 = {build["wall"]} m²，改造前外墙K = {build["Kw_old"]} W/(m²·K)
    外窗面积 = {build["win"]} m²，原窗K = {build["Kwin_old"]} W/(m²·K)
    室内外计算温差 ΔT = {build["dT"]} K

    1）围护结构传热负荷
    $Q_{{wall}} = A_{{wall}} \\cdot K_{{wall}} \\cdot \\Delta T = {build["wall"]} \\times {build["Kw_old"]} \\times {build["dT"]}$
    $Q_{{win}} = A_{{win}} \\cdot K_{{win}} \\cdot \\Delta T = {build["win"]} \\times {build["Kwin_old"]} \\times {build["dT"]}$

    2）冷风渗透热负荷（换气次数法）
    $Q_{{inf}} = c_p \\cdot \\rho \\cdot V \\cdot n / 3600 \\cdot \\Delta T$
    $V = {round(build["volume"],2)}\ m^3,\ n={build["n"]}\ 次/h$

    3）总热负荷 = 围护负荷 + 冷风渗透负荷，转换为kW，与软件输出对比校验。
    """)
    st.divider()
    st.subheader("2. 耗电量 & 节能率手算校核")
    st.markdown(r"""
    $$E_{year}=\frac{Q_{year}}{SCOP}$$
    $$节能率=\frac{E_{基准}-E_{改造}}{E_{基准}} \times 100\%$$
    """)
    st.info("手算草稿完成后填入参数，和软件结果比对，竞赛存档校核。")
    hand_calc_heat = st.number_input("手算全年采暖需热量 kWh", value=0.0)
    hand_SCOP = st.number_input("校核SCOP取值", value=2.6)
    if st.button("执行校核计算"):
        hand_elec = hand_calc_heat / hand_SCOP if hand_SCOP>0 else 0
        st.metric("🔍手算得到年耗电量(kWh)", round(hand_elec,2))
