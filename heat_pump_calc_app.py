# -*- coding: utf-8 -*-
"""
老旧住宅空气源热泵协同改造计算工具
UI：浅色科技风｜玻璃拟态｜清爽高亮｜大屏展示
分工对应：
页面1：建筑围护参数（建筑与围护组负责）
页面2：末端+热泵参数（末端与热泵组负责）
页面3：三套方案计算结果+经济性+节能率+辅助电加热+碳排放
页面4：手工校核验算页
开发：软件与经济组，全代码逐行注释，参数标注来源
核心三套方案：
方案1：仅更换空气源热泵，围护不改造（基准方案）
方案2：围护结构保温改造 + 常规空气源热泵
方案3：围护改造 + 低温采暖末端 + 低温型空气源热泵
新增：热泵额定制热负荷比对，判断是否需要辅助电加热；运行阶段碳排放核算GB/T51366‑2019
"""
import streamlit as st
import pandas as pd
import plotly.express as px

# ====================== 全局初始化持久参数 ======================
DEFAULT_BUILD = {
    "area": 120.0, "floor_h": 2.8, "volume": 120*2.8, "wall": 85.0, "win": 22.0,
    "Kw_old": 1.8, "Kw_new": 0.45, "Kwin_old": 2.8, "Kwin_new": 1.8,
    "Tin": 20, "Tout": -7, "dT": 27, "HDD": 2106,
    "n": 0.5, "rho": 1.2, "cp": 1005
}
DEFAULT_EQUIP = {
    "SCOP1":2.6, "SCOP2":2.6, "SCOP3":3.2,
    "elec_price":0.56,
    "cost_pump":12500,
    "cost_wall":14200,
    "cost_lowend":9800,
    "budget":30000,
    "Qhp_rated1":12.0,
    "Qhp_rated2":12.0,
    "Qhp_rated3":10.0,
    "supply_temp1":55.0,
    "supply_temp2":55.0,
    "supply_temp3":40.0,
    "grid_ef":0.5810
}
if "build" not in st.session_state:
    st.session_state["build"] = DEFAULT_BUILD.copy()
if "equip" not in st.session_state:
    st.session_state["equip"] = DEFAULT_EQUIP.copy()

def sync_build(key_widget, key_biz):
    st.session_state["build"][key_biz] = st.session_state[key_widget]

def sync_equip(key_widget, key_biz):
    st.session_state["equip"][key_biz] = st.session_state[key_widget]

# ====================== 全局页面基础配置 + 浅色科技CSS ======================
st.set_page_config(
    page_title="郑州老旧住宅热泵协同改造测算工具",
    layout="wide",
    initial_sidebar_state="expanded"
)

light_tech_style = """
<style>
/* 全局浅色科技背景 */
.stApp {
    background: linear-gradient(135deg, #f8fafc 0%, #eaf4ff 100%);
    color: #1e293b;
}
/* 侧边栏：清爽浅蓝 */
[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #e0e7ff;
}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

.light-tech-title {
    background: linear-gradient(135deg, rgba(255,255,255,0.95), rgba(248,250,255,0.95));
    border: 1px solid rgba(99, 102, 241, 0.35);
    border-radius: 14px;
    padding: 22px 26px;
    margin-bottom: 24px;
    box-shadow: 0 8px 24px rgba(99, 102, 241, 0.14);
}
.light-tech-title h1 {
    font-size: 30px;
    font-weight: 800;
    background: linear-gradient(90deg, #6366f1, #8b5cf6, #ec4899);
    -webkit-background-clip: text;
    color: transparent;
    margin: 0 0 8px 0;
}
.light-tech-title p {
    font-size: 15px;
    color: #64748b;
    margin: 0;
}

[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding:16px !important;
    transition: 0.25s ease;
}
[data-testid="stMetric"]:hover {
    border-color: #6366f1;
    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.08), 0 12px 28px rgba(99, 102, 241, 0.12);
}
[data-testid="stMetricLabel"] {
    color: #475569 !important;
    font-weight: 500;
}
[data-testid="stMetricValue"] {
    color: #6366f1 !important;
    font-weight: 800;
}
div[data-testid="stMetricDelta"] > div {
    color: #10b981 !important;
    font-weight: 600;
}

.st-data-frame {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 12px !important;
}
.st-data-frame th {
    background: linear-gradient(90deg, #6366f1, #8b5cf6) !important;
    color: #ffffff !important;
}

div[data-baseweb="input"] {
    background-color: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 8px !important;
}
label.st-label {
    color: #334155 !important;
    font-weight: 500;
}
.st-info > div {
    background-color: #eff6ff !important;
    border-left-color: #6366f1 !important;
    color: #1e40af !important;
}
.st-warning > div {
    background-color: #fffbeb !important;
    border-left-color: #f59e0b !important;
    color: #92400e !important;
}
.st-success > div {
    background-color: #f0fdf4 !important;
    border-left-color: #10b981 !important;
    color: #166534 !important;
}
hr {
    border-color: rgba(99, 102, 241, 0.22) !important;
}
button[kind="primary"] {
    background: linear-gradient(90deg, #6366f1, #8b5cf6) !important;
    border: none !important;
}
</style>
"""
st.markdown(light_tech_style, unsafe_allow_html=True)

# 侧边栏
with st.sidebar:
    st.markdown("""
<div style="padding:10px 0;border-bottom:1px solid rgba(99,102,241,0.25);margin-bottom:14px;">
<h3 style="color:#6366f1;margin:0;">📌 参数来源台账</h3>
</div>
""", unsafe_allow_html=True)
    st.markdown("""
    1. 建筑传热系数K：《民用建筑热工设计规范》GB 50176、中原地区老旧住宅实测文献
    2. 郑州采暖度日数HDD18：中国建筑节能气象参数数据库
    3. 空气源热泵SCOP、额定制热量：美的低温型空气源热泵官方样本手册
    4. 电价、改造材料费：河南郑州市场家装/旧房改造市场价调研
    5. 热负荷计算公式：《供热工程》教材经典稳态传热负荷公式
    6. 碳排放：GB/T51366‑2019建筑碳排放计算标准，电网排放因子取全国平均因子
    """)
    st.divider()
    page_select = st.radio("功能页面切换", [
        "1.建筑围护参数录入",
        "2.采暖末端&热泵参数录入",
        "3.三套方案计算结果",
        "4.手工校核验算页"
    ])

# ====================== 全局通用计算公式 ======================
def calc_wall_win_load(wall_area, win_area, K_wall, K_win, delta_T):
    wall_load = wall_area * K_wall * delta_T
    win_load = win_area * K_win * delta_T
    total_env_load = wall_load + win_load
    return wall_load, win_load, total_env_load

def calc_infiltration_load(volume, n, rho, cp, delta_T):
    mass_flow = rho * volume * n / 3600
    infiltration_Q = mass_flow * cp * delta_T
    return infiltration_Q

def total_heat_load(env_load, infil_load):
    total_W = env_load + infil_load
    total_kW = total_W / 1000
    return total_kW, total_W

def calc_year_heat(total_W, HDD, indoor_T):
    day_hour = 24
    delta_T_day = indoor_T - 18
    year_heat_kwh = total_W * HDD * day_hour / (delta_T_day * 1000)
    return year_heat_kwh

def elec_consume(year_heat, SCOP):
    elec = year_heat / SCOP
    return elec

def payback_period(add_invest, save_elec, elec_price):
    if save_elec <= 0:
        return None
    year_save = save_elec * elec_price
    pay_year = add_invest / year_save
    return round(pay_year, 2)

def check_aux_electric_heat(q_load_kw, q_hp_rated_kw):
    if q_hp_rated_kw >= q_load_kw:
        return False, 0.0
    else:
        aux_load = q_load_kw - q_hp_rated_kw
        return True, round(aux_load,2)

def calc_carbon(elec_kwh, ef_kg_kwh):
    co2 = elec_kwh * ef_kg_kwh
    return round(co2,2)

# ====================== 页面1：建筑围护参数录入 ======================
if page_select == "1.建筑围护参数录入":
    st.markdown("""
<div class="light-tech-title">
    <h1>🏠 建筑围护结构参数录入页面</h1>
    <p>录入郑州老旧住宅建筑尺寸、传热系数、气象参数｜建筑围护组模块</p>
</div>
""", unsafe_allow_html=True)

    st.info("每一项输入框后的问号可查看物理意义、单位，由建筑围护组确定参数")
    build = st.session_state["build"]
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("建筑基础尺寸")
        st.number_input("建筑面积 m²",
                        value=build["area"],
                        key="_area",
                        on_change=sync_build, args=("_area", "area"),
                        help="住宅套内+公摊建筑面积，本次案例固定120㎡")
        st.number_input("楼层层高 m",
                        value=build["floor_h"],
                        key="_floor_h",
                        on_change=sync_build, args=("_floor_h", "floor_h"),
                        help="室内层高，用来计算房间体积")
        room_volume = build["area"] * build["floor_h"]
        st.metric("室内总体积 m³", value=round(room_volume, 2))
        st.number_input("外墙总面积 m²",
                        value=build["wall"],
                        key="_wall",
                        on_change=sync_build, args=("_wall", "wall"),
                        help="建筑外围护外墙面积，不含内墙")
        st.number_input("外窗总面积 m²",
                        value=build["win"],
                        key="_win",
                        on_change=sync_build, args=("_win", "win"),
                        help="所有外窗面积之和")
    with col2:
        st.subheader("传热系数K值")
        st.number_input("改造前外墙K W/(m²·K)",
                        value=build["Kw_old"],
                        key="_Kw_old",
                        on_change=sync_build, args=("_Kw_old", "Kw_old"),
                        help="旧房红砖外墙无保温传热系数，来源热工实测文献")
        st.number_input("改造后外墙保温K W/(m²·K)",
                        value=build["Kw_new"],
                        key="_Kw_new",
                        on_change=sync_build, args=("_Kw_new", "Kw_new"),
                        help="外墙外保温改造后传热系数，GB50176节能限值")
        st.number_input("改造前普通窗户K W/(m²·K)",
                        value=build["Kwin_old"],
                        key="_Kwin_old",
                        on_change=sync_build, args=("_Kwin_old", "Kwin_old"),
                        help="原有单层塑钢窗传热系数")
        st.number_input("改造后断桥铝窗K W/(m²·K)",
                        value=build["Kwin_new"],
                        key="_Kwin_new",
                        on_change=sync_build, args=("_Kwin_new", "Kwin_new"),
                        help="节能断桥铝中空玻璃窗户K值")
    st.divider()
    st.subheader("气象与室内设计参数（郑州地区固定值）")
    col3, col4 = st.columns(2)
    with col3:
        st.number_input("室内采暖设计温度 ℃",
                        value=build["Tin"],
                        key="_Tin",
                        on_change=sync_build, args=("_Tin", "Tin"),
                        help="采暖规范室内设计温度")
        st.number_input("郑州冬季采暖室外设计温度 ℃",
                        value=build["Tout"],
                        key="_Tout",
                        on_change=sync_build, args=("_Tout", "Tout"),
                        help="郑州暖通设计室外低温，供热手册取值")
        delta_T = build["Tin"] - build["Tout"]
        st.metric("室内外设计温差 ΔT(K)", value=delta_T)
        st.number_input("郑州HDD18采暖度日数 ℃·d",
                        value=build["HDD"],
                        key="_HDD",
                        on_change=sync_build, args=("_HDD", "HDD"),
                        help="基准18℃采暖度日数，官方气象数据库")
    with col4:
        st.number_input("冷风渗透换气次数 次/h",
                        value=build["n"],
                        key="_n",
                        on_change=sync_build, args=("_n", "n"),
                        help="老旧住宅门窗缝隙冷风渗透换气次数")
        st.number_input("空气密度 kg/m³",
                        value=build["rho"],
                        key="_rho",
                        on_change=sync_build, args=("_rho", "rho"),
                        help="常温常压干空气密度，传热学常用取值")
        st.number_input("空气定压比热容 J/(kg·K)",
                        value=build["cp"],
                        key="_cp",
                        on_change=sync_build, args=("_cp", "cp"),
                        help="干空气定压比热容")

    st.session_state["build"]["volume"] = st.session_state["build"]["area"] * st.session_state["build"]["floor_h"]
    st.session_state["build"]["dT"] = st.session_state["build"]["Tin"] - st.session_state["build"]["Tout"]
    st.success("✅ 建筑围护参数已保存，前往第二页录入热泵末端参数")

# ====================== 页面2：末端&热泵参数录入【造价全部移到右侧】 ======================
elif page_select == "2.采暖末端&热泵参数录入":
    st.markdown("""
<div class="light-tech-title">
    <h1>🔥 采暖末端与空气源热泵机组参数录入</h1>
    <p>SCOP｜额定制热量｜供水温度｜造价｜电价｜碳排放因子｜末端与热泵组模块</p>
</div>
""", unsafe_allow_html=True)

    st.info("由末端与热泵组填写，SCOP、额定制热量取自厂家样本，造价取自市场调研；碳排放因子参考GB/T51366‑2019")
    equip = st.session_state["equip"]
    col_left, col_right = st.columns([1,1])
    with col_left:
        st.subheader("空气源热泵SCOP（制热性能系数）")
        st.number_input("方案1常规热泵SCOP",
                        value=equip["SCOP1"],
                        key="_SCOP1",
                        on_change=sync_equip, args=("_SCOP1", "SCOP1"),
                        help="常温空气源热泵冬季平均制热系数")
        st.number_input("方案2常规热泵SCOP",
                        value=equip["SCOP2"],
                        key="_SCOP2",
                        on_change=sync_equip, args=("_SCOP2", "SCOP2"),
                        help="围护改造只降负荷，热泵机型不变，SCOP不变")
        st.number_input("方案3低温专用热泵SCOP",
                        value=equip["SCOP3"],
                        key="_SCOP3",
                        on_change=sync_equip, args=("_SCOP3", "SCOP3"),
                        help="低温机型+低温地暖末端，供水温度低，机组效率更高")

        st.divider()
        st.subheader("🧪 热泵额定制热量(kW)")
        st.number_input("方案1热泵额定制热量 kW",
                        value=equip["Qhp_rated1"],
                        key="_Qhp_rated1",
                        on_change=sync_equip, args=("_Qhp_rated1", "Qhp_rated1"),
                        help="郑州室外设计温度(-7℃)工况下机组额定制热量，厂家样本")
        st.number_input("方案2热泵额定制热量 kW",
                        value=equip["Qhp_rated2"],
                        key="_Qhp_rated2",
                        on_change=sync_equip, args=("_Qhp_rated2", "Qhp_rated2"),
                        help="郑州室外设计温度(-7℃)工况下机组额定制热量，厂家样本")
        st.number_input("方案3低温热泵额定制热量 kW",
                        value=equip["Qhp_rated3"],
                        key="_Qhp_rated3",
                        on_change=sync_equip, args=("_Qhp_rated3", "Qhp_rated3"),
                        help="低温机型在室外-7℃额定制热量，厂家样本")

    with col_right:
        st.subheader("🌡️ 系统设计供水温度 ℃")
        st.number_input("方案1供水温度 ℃(原有散热器)",
                        value=equip["supply_temp1"],
                        key="_supply_temp1",
                        on_change=sync_equip, args=("_supply_temp1", "supply_temp1"),
                        help="散热器末端典型供水50‑55℃")
        st.number_input("方案2供水温度 ℃(原有散热器)",
                        value=equip["supply_temp2"],
                        key="_supply_temp2",
                        on_change=sync_equip, args=("_supply_temp2", "supply_temp2"),
                        help="围护改造不换末端，维持散热器供水温度")
        st.number_input("方案3供水温度 ℃(低温地暖)",
                        value=equip["supply_temp3"],
                        key="_supply_temp3",
                        on_change=sync_equip, args=("_supply_temp3", "supply_temp3"),
                        help="低温地暖末端典型供水35‑42℃")

        st.divider()
        st.subheader("♻️ 碳排放与造价参数")
        st.number_input("电网碳排放因子 kgCO₂/kWh",
                        value=equip["grid_ef"],
                        key="_grid_ef",
                        on_change=sync_equip, args=("_grid_ef", "grid_ef"),
                        help="GB/T51366‑2019全国电网缺省0.5810 kgCO₂/kWh")
        st.number_input("居民电价 元/kWh",
                        value=equip["elec_price"],
                        key="_elec_price",
                        on_change=sync_equip, args=("_elec_price", "elec_price"),
                        help="河南居民阶梯电价均价")
        st.number_input("空气源热泵采购安装费 元",
                        value=equip["cost_pump"],
                        key="_cost_pump",
                        on_change=sync_equip, args=("_cost_pump", "cost_pump"),
                        help="常规冷暖热泵整套造价")
        st.number_input("外墙保温改造总造价 元",
                        value=equip["cost_wall"],
                        key="_cost_wall",
                        on_change=sync_equip, args=("_cost_wall", "cost_wall"),
                        help="全屋外墙保温施工材料费+人工费")
        st.number_input("低温地暖末端改造费用 元",
                        value=equip["cost_lowend"],
                        key="_cost_lowend",
                        on_change=sync_equip, args=("_cost_lowend", "cost_lowend"),
                        help="全屋地暖铺设施工费用")
        st.number_input("业主改造费用预算 元",
                        value=equip["budget"],
                        key="_budget",
                        on_change=sync_equip, args=("_budget", "budget"),
                        help="业主可承受的改造总投资上限，用于与各方案初投资比对并筛选合适方案")

    st.success("✅ 末端热泵参数保存完毕，进入第三页一键计算三套方案")

# ====================== 页面3：三套方案计算结果【卡片固定高度，大小完全相等对齐】 ======================
elif page_select == "3.三套方案计算结果":
    st.markdown("""
<div class="light-tech-title">
    <h1>📊 三套改造方案全自动计算结果页面</h1>
    <p>热负荷｜能耗｜供水温度｜辅助电加热｜碳排放｜图表｜方案推荐｜CSV结果导出</p>
</div>
""", unsafe_allow_html=True)

    if "build" not in st.session_state or "equip" not in st.session_state:
        st.warning("⚠️ 请先在页面1录入建筑围护参数、页面2录入热泵末端参数后，再查看计算结果。")
        st.stop()
    build = st.session_state["build"]
    equip = st.session_state["equip"]
    st.divider()

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
    need_aux1, aux_load1 = check_aux_electric_heat(total_kW_1, equip["Qhp_rated1"])
    co2_1 = calc_carbon(elec_1, equip["grid_ef"])

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
    load_save_rate_2 = round((total_kW_1 - total_kW_2)/total_kW_1*100,2)
    elec_save_rate_2 = round((elec_1 - elec_2)/elec_1*100,2)
    need_aux2, aux_load2 = check_aux_electric_heat(total_kW_2, equip["Qhp_rated2"])
    co2_2 = calc_carbon(elec_2, equip["grid_ef"])
    co2_reduce_2 = round(co2_1 - co2_2,2)
    co2_reduce_rate_2 = round((co2_1 - co2_2)/co2_1*100,2) if co2_1>0 else 0

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
    need_aux3, aux_load3 = check_aux_electric_heat(total_kW_3, equip["Qhp_rated3"])
    co2_3 = calc_carbon(elec_3, equip["grid_ef"])
    co2_reduce_3 = round(co2_1 - co2_3,2)
    co2_reduce_rate_3 = round((co2_1 - co2_3)/co2_1*100,2) if co2_1>0 else 0

    budget = equip["budget"]
    within_1 = invest_1 <= budget
    within_2 = invest_2 <= budget
    within_3 = invest_3 <= budget
    tag_1 = "✅ 预算内" if within_1 else "❌ 超预算"
    tag_2 = "✅ 预算内" if within_2 else "❌ 超预算"
    tag_3 = "✅ 预算内" if within_3 else "❌ 超预算"

    candidates = []
    if within_2 and payback_2 is not None:
        candidates.append(("方案2", payback_2, elec_save_rate_2))
    if within_3 and payback_3 is not None:
        candidates.append(("方案3", payback_3, elec_save_rate_3))
    best_scheme = min(candidates, key=lambda x: x[1])[0] if candidates else None

    budget_sufficient = budget >= invest_3 * 1.2
    if within_2 and within_3:
        eco_scheme = "方案3" if elec_save_rate_3 >= elec_save_rate_2 else "方案2"
    elif within_2:
        eco_scheme = "方案2"
    elif within_3:
        eco_scheme = "方案3"
    else:
        eco_scheme = None

    col_a, col_b, col_c = st.columns([1,1,1])
    CARD_FIX_HEIGHT = 660

    with col_a:
        with st.container(height=CARD_FIX_HEIGHT):
            st.markdown("### 🟦 方案1｜仅更换热泵")
            st.metric("热负荷(kW)", round(total_kW_1,2))
            st.metric("供水温度℃", equip["supply_temp1"])
            st.metric("年耗电(kWh)", round(elec_1,1))
            st.metric("年CO₂排放(kg)", co2_1)
            st.metric("是否需辅助电加热","✅需要" if need_aux1 else "❌不需要")
            st.divider()
            st.metric("总初投资(元)", invest_1)
            st.metric("年采暖电费(元)", round(year_cost_1,2))

    with col_b:
        with st.container(height=CARD_FIX_HEIGHT):
            st.markdown("### 🟩 方案2｜围护改造+常规热泵")
            st.metric("热负荷(kW)", round(total_kW_2,2), delta=f"-{load_save_rate_2}%")
            st.metric("供水温度℃", equip["supply_temp2"])
            st.metric("年耗电(kWh)", round(elec_2,1), delta=f"-{elec_save_rate_2}%")
            st.metric("年CO₂排放(kg)", co2_2, delta=f"-{co2_reduce_rate_2}%")
            st.metric("是否需辅助电加热","✅需要" if need_aux2 else "❌不需要")
            st.divider()
            st.metric("总初投资(元)", invest_2)
            st.metric("年采暖电费(元)", round(year_cost_2,2))

    with col_c:
        with st.container(height=CARD_FIX_HEIGHT):
            st.markdown("### 🟨 方案3｜围护+低温末端+低温热泵")
            st.metric("热负荷(kW)", round(total_kW_3,2), delta=f"-{load_save_rate_3}%")
            st.metric("供水温度℃", equip["supply_temp3"])
            st.metric("年耗电(kWh)", round(elec_3,1), delta=f"-{elec_save_rate_3}%")
            st.metric("年CO₂排放(kg)", co2_3, delta=f"-{co2_reduce_rate_3}%")
            st.metric("是否需辅助电加热","✅需要" if need_aux3 else "❌不需要")
            st.divider()
            st.metric("总初投资(元)", invest_3)
            st.metric("年采暖电费(元)", round(year_cost_3,2))

    st.divider()

    result_df = pd.DataFrame({
        "改造方案": ["方案1：仅更换热泵", "方案2：围护改造+常规热泵", "方案3：围护+低温末端+低温热泵"],
        "设计热负荷(kW)": [round(total_kW_1, 2), round(total_kW_2, 2), round(total_kW_3, 2)],
        "设计供水温度(℃)":[equip["supply_temp1"],equip["supply_temp2"],equip["supply_temp3"]],
        "热泵额定制热量(kW)":[equip["Qhp_rated1"],equip["Qhp_rated2"],equip["Qhp_rated3"]],
        "是否需要辅助电加热":["是" if need_aux1 else "否","是" if need_aux2 else "否","是" if need_aux3 else "否"],
        "辅助电加热承担负荷(kW)":[aux_load1,aux_load2,aux_load3],
        "热负荷削减率(%)":["基准", load_save_rate_2, load_save_rate_3],
        "全年采暖需热量(kWh)": [round(year_heat_1, 1), round(year_heat_2, 1), round(year_heat_3, 1)],
        "热泵年耗电量(kWh)": [round(elec_1, 1), round(elec_2, 1), round(elec_3, 1)],
        "耗电量节能率(%)":["基准", elec_save_rate_2, elec_save_rate_3],
        "年运行CO₂排放(kgCO₂)":[co2_1,co2_2,co2_3],
        "年减碳量(kgCO₂)":["基准",co2_reduce_2,co2_reduce_3],
        "碳排放削减率(%)":["基准",co2_reduce_rate_2,co2_reduce_rate_3],
        "项目总初投资(元)": [invest_1, invest_2, invest_3],
        "预算比对": [tag_1, tag_2, tag_3],
        "年采暖电费(元)": [round(year_cost_1, 2), round(year_cost_2, 2), round(year_cost_3, 2)],
        "静态投资回收期(年)": ["基准", payback_2, payback_3]
    })

    st.dataframe(result_df, use_container_width=True)
    csv_bytes = result_df.to_csv(index=False, encoding="utf‑8‑sig").encode("utf‑8‑sig")
    st.download_button(label="📥 下载计算结果CSV", data=csv_bytes,
                       file_name="热泵改造结果_供水温度_辅助电加热_碳排放.csv", mime="text/csv")

    st.divider()

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊热负荷对比","🔥年需热量对比","⚡年耗电量对比","💡耗电量节能率对比","💰静态回收期对比","🌿年碳排放对比"
    ])

    color_list = ["#6366f1","#f59e0b","#10b981"]
    layout_common = dict(
        template="plotly_white",
        hovermode="x unified",
        height=440,
        font=dict(size=13),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(99,102,241,0.04)"
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
                      color="改造方案", color_discrete_sequence=color_list[1:])
        fig4.update_layout(**layout_common)
        st.plotly_chart(fig4, use_container_width=True)
    with tab4:
        df_save = result_df.copy()
        df_save = df_save[df_save["耗电量节能率(%)"]!="基准"]
        fig5 = px.bar(df_save, x="改造方案", y="耗电量节能率(%)", title="相对基准方案耗电量节能率对比",
                      color="改造方案", color_discrete_sequence=color_list[1:])
        fig5.update_layout(**layout_common)
        st.plotly_chart(fig5, use_container_width=True)
    with tab6:
        fig6 = px.bar(result_df, x="改造方案", y="年运行CO₂排放(kgCO₂)", title="三套方案年运行阶段CO₂排放对比",
                      color="改造方案", color_discrete_sequence=color_list)
        fig6.update_layout(**layout_common)
        st.plotly_chart(fig6, use_container_width=True)

    st.divider()

    text_p2 = payback_2 if payback_2 is not None else "——"
    text_p3 = payback_3 if payback_3 is not None else "——"

    st.subheader("✅ 最终方案推荐与理由（预算+辅助电加热+供水温度+碳排放多维度）")
    st.info(f"💰 业主改造费用预算：**{budget:,} 元**")

    budget_note_1 = f"初投资 {invest_1:,} 元，{tag_1}"
    budget_note_2 = f"初投资 {invest_2:,} 元，{tag_2}"
    budget_note_3 = f"初投资 {invest_3:,} 元，{tag_3}"

    if not within_2 and not within_3:
        rec1_label = "⚠️ 预算内唯一可行"
        rec1_reason = "方案2、3初投资均超出预算，方案1为预算内唯一可实施方案；但仅更换热泵不改造围护，无节能减碳效益。"
    else:
        rec1_label = "❌ 不推荐"
        rec1_reason = "仅更换热泵而不改造围护结构，热负荷无削减、无节能减碳效益，仅作为基准对照。"

    if within_2:
        rec2_label = "✅ 优先推荐" if best_scheme == "方案2" else "✅ 可推荐"
        rec2_reason = (f"预算内可行，静态投资回收期{text_p2}年，耗电量节能{elec_save_rate_2}%，碳排放削减{co2_reduce_rate_2}%；"
                       f"供水温度{equip['supply_temp2']}℃，改造难度低，综合性价比优。")
    else:
        rec2_label = "❌ 不推荐"
        rec2_reason = f"初投资{invest_2:,}元超出业主预算{budget:,}元，不具备实施条件。"

    if within_3:
        rec3_label = "✅ 优先推荐" if best_scheme == "方案3" else "✅ 可推荐"
        rec3_reason = (f"预算内可行，静态投资回收期{text_p3}年，耗电量节能{elec_save_rate_3}%，碳排放削减{co2_reduce_rate_3}%；"
                       f"低温地暖供水温度{equip['supply_temp3']}℃，系统效率更高，长期运行更低碳。")
    else:
        rec3_label = "❌ 不推荐"
        rec3_reason = f"初投资{invest_3:,}元超出业主预算{budget:,}元，不具备实施条件。"

    if best_scheme:
        if budget_sufficient and within_2 and within_3:
            overall = f">预算 {budget:,} 元充足（≥方案3费用1.2倍），方案2、3均可行，以下提供**经济导向**与**节能减碳导向**两种推荐思路供权衡。"
        else:
            overall = f">综上，在预算 {budget:,} 元约束下，**{best_scheme}** 为最优方案。"
    else:
        overall = f">综上，预算 {budget:,} 元下方案2、3均不可行，建议提高预算或仅实施方案1。"

    dual_rec = ""
    if budget_sufficient and within_2 and within_3:
        eco_pay = text_p2 if eco_scheme == "方案2" else text_p3
        eco_save = elec_save_rate_2 if eco_scheme == "方案2" else elec_save_rate_3
        eco_carbon = co2_reduce_rate_2 if eco_scheme == "方案2" else co2_reduce_rate_3
        eco_cost = round(year_cost_2,2) if eco_scheme=="方案2" else round(year_cost_3,2)
        eco_invest = invest_2 if eco_scheme=="方案2" else invest_3
        econ_pay = text_p2 if best_scheme == "方案2" else text_p3
        dual_rec = f"""
**💡 预算充足·双维度推荐思路：**
- 💰 **经济导向推荐：{best_scheme}** ——静态投资回收期最短（{econ_pay}年），初投资更低、施工风险更小。
- 🌿 **节能减碳导向推荐：{eco_scheme}** ——耗电量节能率最高（{eco_save}%），碳排放削减{eco_carbon}%，年采暖电费最低（{eco_cost}元）；初投资{eco_invest:,}元、回收期{eco_pay}年。
"""

    def _gen_sequence(scheme):
        if scheme == "方案3":
            return """
**🔧 改造顺序（方案3）：**
1. **围护结构保温改造**：外墙保温 + 更换断桥铝窗，先降低建筑热负荷。
2. **低温采暖末端铺设**：地暖施工，完成后进行水压试验和回填养护。
3. **低温型空气源热泵安装与联调**：与地暖末端联动调试供水温度、流量分配及除霜逻辑。
"""
        elif scheme == "方案2":
            return """
**🔧 改造顺序（方案2）：**
1. **围护结构保温改造**：外墙保温 + 更换断桥铝窗，降低建筑热负荷。
2. **常规空气源热泵安装与联调**：与原有散热器末端联动调试供水温度及运行参数。
"""
        elif scheme == "方案1":
            return """
**🔧 改造顺序（方案1）：**
- 仅涉及空气源热泵更换，拆除旧机组、安装新热泵并调试即可。
- 建议同步检查原有末端及管路密封性。
"""
        return ""

    if budget_sufficient and eco_scheme and best_scheme and eco_scheme != best_scheme:
        sequence_text = _gen_sequence(best_scheme)+_gen_sequence(eco_scheme)
    elif best_scheme:
        sequence_text = _gen_sequence(best_scheme)
    else:
        sequence_text = ""

    st.markdown(f"""
1. **方案1：仅更换热泵** —— {budget_note_1}
    - 分析：围护不改造，设计热负荷{round(total_kW_1,2)}kW；供水温度{equip['supply_temp1']}℃；热泵额定制热量{equip['Qhp_rated1']}kW；{"需要辅助电加热，辅助负荷"+str(aux_load1)+"kW" if need_aux1 else "机组能力满足，不需要辅助电加热"}；年运行CO₂排放 {co2_1} kgCO₂。
    - 结论：**{rec1_label}** —— {rec1_reason}
2. **方案2：围护保温改造+常规空气源热泵** —— {budget_note_2}
    - 分析：热负荷削减{load_save_rate_2}%，耗电量节能{elec_save_rate_2}%；供水温度{equip['supply_temp2']}℃；设计热负荷{round(total_kW_2,2)}kW，热泵额定制热量{equip['Qhp_rated2']}kW；{"需要辅助电加热，辅助负荷"+str(aux_load2)+"kW" if need_aux2 else "机组能力满足，不需要辅助电加热"}；年减碳 {co2_reduce_2} kgCO₂，碳排放削减 {co2_reduce_rate_2}%；静态投资回收期{text_p2}年。
    - 结论：**{rec2_label}** —— {rec2_reason}
3. **方案3：围护改造+低温采暖末端+低温热泵** —— {budget_note_3}
    - 分析：热负荷削减{load_save_rate_3}%，耗电量节能{elec_save_rate_3}%；低温地暖供水温度{equip['supply_temp3']}℃；设计热负荷{round(total_kW_3,2)}kW，热泵额定制热量{equip['Qhp_rated3']}kW；{"需要辅助电加热，辅助负荷"+str(aux_load3)+"kW" if need_aux3 else "机组能力满足，不需要辅助电加热"}；年减碳 {co2_reduce_3} kgCO₂，碳排放削减 {co2_reduce_rate_3}%；静态投资回收期{text_p3}年。
    - 结论：**{rec3_label}** —— {rec3_reason}
{overall}
{dual_rec}
{sequence_text}
""")

# ====================== 页面4：手工校核验算页【公式分开，不再堆在一起】 ======================
elif page_select == "4.手工校核验算页":
    st.markdown("""
<div class="light-tech-title">
    <h1>✍️ 手工校核验算页面</h1>
    <p>热负荷｜耗电量｜辅助电加热｜供水温度｜碳排放｜手算校验存档</p>
</div>
""", unsafe_allow_html=True)

    st.info("可手动代入参数手算，与程序计算结果进行对照校验，便于报告编写存档。")
    if "build" not in st.session_state or "equip" not in st.session_state:
        st.warning("⚠️ 请先在页面1录入建筑围护参数、页面2录入热泵末端参数后，再进行手算校核。")
        st.stop()
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

    st.subheader("2. 辅助电加热校核公式")
    st.markdown(r"""
$Q_{load}$：建筑设计热负荷(kW)
$Q_{hp,rated}$：热泵室外设计温度额定制热量(kW)

$$
\begin{cases}
Q_{hp,rated} \ge Q_{load}: \quad \text{不需要辅助电加热} \\
Q_{hp,rated} < Q_{load}: \quad \text{需要辅助电加热},\ Q_{aux}=Q_{load}-Q_{hp,rated}
\end{cases}
$$
""")

    st.divider()

    st.subheader("3. 供水温度说明")
    st.markdown("""
- 方案1、方案2：原有散热器末端，供水温度一般50‑55℃；
- 方案3：低温地暖末端，供水温度一般35‑42℃。
> 供水温度越低，空气源热泵机组实际运行COP越高，耗电越少，碳排放越低。
""")

    st.divider()

    st.subheader("4. 热泵年耗电量计算公式")
    st.markdown(r"""
$Q_{year}$：建筑全年采暖需热量(kWh)
$SCOP$：热泵制热性能系数

$$E_{year}=\frac{Q_{year}}{SCOP}$$
""")

    st.divider()

    st.subheader("5. 改造耗电量节能率计算公式")
    st.markdown(r"""
$E_{基准}$：基准方案年耗电量(kWh)
$E_{改造}$：改造后方案年耗电量(kWh)

$$节能率=\frac{E_{基准}-E_{改造}}{E_{基准}} \times 100\%$$
""")

    st.divider()

    st.subheader("6. 运行阶段碳排放计算公式")
    st.markdown(r"""
$EF_{grid}$：电网碳排放因子，单位 kgCO₂/kWh

$$CO_{2}=E_{year} \times EF_{grid}$$
""")

    st.info("将手算草稿结果填入下方参数，和软件结果比对，用于报告存档。")

    hand_calc_heat = st.number_input("手算全年采暖需热量 kWh", value=0.0)
    hand_SCOP = st.number_input("校核SCOP取值", value=2.6)
    hand_qload = st.number_input("手算建筑总热负荷 kW", value=0.0)
    hand_qhp = st.number_input("校核热泵额定制热量 kW", value=12.0)
    hand_supply_temp = st.number_input("手算设计供水温度 ℃", value=55.0)
    hand_ef = st.number_input("校核电网排放因子 kgCO₂/kWh", value=0.5810)

    if st.button("执行校核计算"):
        hand_elec = hand_calc_heat / hand_SCOP if hand_SCOP>0 else 0
        hand_need_aux, hand_aux_load = check_aux_electric_heat(hand_qload, hand_qhp)
        hand_co2 = calc_carbon(hand_elec, hand_ef)
        st.metric("🔍手算得到年耗电量(kWh)", round(hand_elec,2))
        st.metric("🔍手算判断是否需要辅助电加热", "✅需要" if hand_need_aux else "❌不需要")
        st.metric("🔍手算辅助电加热负荷(kW)", hand_aux_load)
        st.metric("🔍手算设计供水温度(℃)", hand_supply_temp)
        st.metric("🔍手算年运行CO₂排放(kgCO₂)", hand_co2)
