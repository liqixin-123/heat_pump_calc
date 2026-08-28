# -*- coding: utf-8 -*-
"""
老旧住宅空气源热泵协同改造计算工具【V1.7｜新增热泵厂家样本插值+HDD分段能耗】
UI：浅色科技风｜玻璃拟态｜清爽高亮｜大屏展示
⚠️户型切换：
①中间层住宅：上下均为采暖住户；不计屋面、地面楼板；构件：外墙、外窗、外门、非采暖楼梯间隔墙+冷风渗透
②顶层边户：顶层+东西山墙边户；计入屋面、山墙；不计底层地面楼板；构件：外墙、东西山墙、屋面、外窗、外门、非采暖隔墙+冷风渗透
不适用：底层住户；
👉V1.6重大更新：
- 删除人工输入供水温度；使用散热器/地暖末端公式迭代求解【满足热负荷的最低供水温度】
公式 Q_terminal = Q_rated × (ΔT_m / ΔT_m_rated)^m
ΔT_m = (tg+th)/2 - Tin；供回水温差固定：散热器Δtg‑h=10K；地暖Δtg‑h=5K
约束：末端最大可提供散热量 >= 建筑设计热负荷Q_load；超过上限输出改进建议
方案1/2 = 旧散热器末端；方案3 = 低温地暖末端；围护改造后负荷下降自动降低供水温度，体现围护‑末端‑热泵协同
👉V1.7更新：
- 增加热泵厂家样本数据表（室外干球温度‑供水温度‑COP‑可用制热量）
- 一维线性插值，超出样本范围、供水温度偏离样本工况输出报警
- HDD拆分为6个室外温度区间，分段计算全年能耗；保留旧SPF算法作为对比
分工对应：
页面1：建筑围护参数（建筑与围护组负责）
页面2：热泵+【末端热工参数】+围护分项单位造价+热泵厂家样本表
页面3：三套方案计算结果+经济性+节能率+辅助电加热+碳排放，输出各分项工程量&造价、末端校核、反算水温、分段能耗明细
页面4：手工校核验算页（H1/Qd1/H2/Qd2/H3/Qd3全套手算校验 + 分段插值结果校验）
核心三套方案：
方案1：仅更换空气源热泵，围护不改造（基准方案，原有散热器末端）
方案2：围护结构保温改造 + 常规空气源热泵（保留原有散热器末端）
方案3：围护改造 + 低温采暖地暖末端 + 低温型空气源热泵
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import datetime

###====改造模式造价系数配置====
RETROFIT_MODE_CFG = {
    "分户独立改造": {"cost_factor":1.00},
    "整栋集中批量改造": {"cost_factor":0.80}
}

# ===================== 新增V1.7：空气源热泵厂家工况样本数据表 =====================
"""
热泵样本表：
测试工况：国标GB/T 25127.1，出水温度tg_supply，室外干球T_amb
每一条：[室外环境温度℃，供水温度℃，COP，工况可用制热量kW]
方案1、2使用常规热泵样本；方案3使用低温热泵样本
"""
# 方案1、方案2：常规型热泵厂家样本（样本固定出水55℃）
SAMPLE_HP_NORMAL = [
    [7, 55, 3.80, 12.0],
    [2, 55, 3.10, 12.0],
    [-2, 55, 2.70, 10.8],
    [-7, 55, 2.20, 9.6],
    [-10, 55, 1.80, 8.4],
]
# 方案3：低温专用热泵厂家样本（样本固定出水45℃）
SAMPLE_HP_LOWTEMP = [
    [7, 45, 4.20, 10.0],
    [2, 45, 3.60, 10.0],
    [-2, 45, 3.20, 9.2],
    [-7, 45, 2.80, 8.5],
    [-10, 45, 2.40, 7.8],
]

# ================= V1.8新增：18种自由组合枚举定义【3围护×3末端×2热泵】 =================
"""
批量改造分项折算系数调研参考依据（项目需按当地招标报价修正）：
1. 分户独立改造：围护=1.00，热泵=1.00，末端=1.00；
2. 整栋集中批量改造参考经验：
   - 围护保温工程 0.75：老旧小区EPC批量集采、外脚手架共用、人工摊薄；
   - 空气源热泵设备安装 0.85：厂家批量供货、统一班组安装，省去零散上门差旅成本；
   - 室内末端改造 0.80：批量进场、开槽回填工序统一调度。
"""
ENVELOPE_OPTIONS = [
    {"id":"E0","name":"E0-不做围护改造","is_retrofit":False},
    {"id":"E1","name":"E1-部分围护改造","is_retrofit":True},
    {"id":"E2","name":"E2-全套围护改造","is_retrofit":True},
]
TERMINAL_OPTIONS = [
    {"id":"T0","name":"T0-原有旧散热器"},
    {"id":"T1","name":"T1-增强型散热器"},
    {"id":"T2","name":"T2-低温水地暖"},
]
HEATPUMP_OPTIONS = [
    {"id":"HP0","name":"HP0-常规型空气源热泵","sample_table":SAMPLE_HP_NORMAL,"sample_tg_fixed":55.0,"rated_key":"Qhp_rated1"},
    {"id":"HP1","name":"HP1-低温专用空气源热泵","sample_table":SAMPLE_HP_LOWTEMP,"sample_tg_fixed":45.0,"rated_key":"Qhp_rated3"},
]

# V1.7 采暖度日数分段配置（6段室外温度区间）
# (T_low, T_high, HDD_fraction) HDD_fraction：该温度区间占总HDD的比例，总和=1.0
HDD_SEGMENTS = [
    (10, 5, 0.20),
    (5, 0, 0.30),
    (0, -5, 0.25),
    (-5, -10, 0.20),
    (-10, -15, 0.05),
]

# ======================全局初始化 ======================
DEFAULT_BUILD_MID = {
    "area": 120.0, "floor_h": 2.8, "volume": 120*2.8,
    "wall_gross": 85.0,       #外墙毛总面积（含窗户洞口）
    "win": 22.0,              #外窗面积
    "door_A":2.2,             #外门面积
    "nonheat_wall_A":18.0,    #与楼梯间等非采暖空间隔墙面积
    "Kw_old": 1.8, "Kw_new": 0.45,
    "Kwin_old": 2.8, "Kwin_new": 1.8,
    "K_door_old":3.0,"K_door_new":1.8,
    "K_nonheat_old":1.7,"K_nonheat_new":0.60,
    "Tin": 20, "Tout": -7, "dT": 27, "HDD": 2106,
    "n": 0.5, "rho": 1.2, "cp": 1005
}
DEFAULT_BUILD_TOP_EDGE = {
    "area": 120.0, "floor_h": 2.8, "volume": 120*2.8,
    "wall_gross": 60.0,       #普通外墙毛面积（扣除东西山墙）
    "win": 22.0,
    "door_A":2.2,
    "nonheat_wall_A":18.0,
    "roof_A":120.0,          #屋面面积（顶层）
    "gable_wall_A":25.0,    #东西山墙面积（边户）
    "Kw_old": 1.8, "Kw_new": 0.45,
    "Kwin_old": 2.8, "Kwin_new": 1.8,
    "K_door_old":3.0,"K_door_new":1.8,
    "K_nonheat_old":1.7,"K_nonheat_new":0.60,
    "K_roof_old":2.2,"K_roof_new":0.40,     #屋面K
    "K_gable_old":1.9,"K_gable_new":0.42,   #东西山墙K
    "Tin": 20, "Tout": -7, "dT": 27, "HDD": 2106,
    "n": 0.5, "rho": 1.2, "cp": 1005
}
DEFAULT_EQUIP = {
    "SCOP_nameplate1":2.6,
    "SCOP_nameplate2":2.6,
    "SCOP_nameplate3":3.2,
    "spf_decay1":0.82,
    "spf_decay2":0.82,
    "spf_decay3":0.88,
    # ==========【V1.5 单位造价】==========
    "unit_wall_ins":130.0,      #外墙保温 元/m²
    "unit_roof_ins":110.0,     #屋面保温 元/m²
    "unit_gable_ins":125.0,    #山墙保温 元/m²
    "unit_win_replace":420.0,  #外窗更换 元/m²
    "unit_door_replace":650.0, #外门更换 元/m²
    "unit_nonheat_ins":95.0,   #非采暖隔墙保温 元/m²
    "unit_lowend_floor":115.0, #低温地暖末端 元/㎡建筑面积
    "cost_pump":12500,         #热泵：固定总价（台）
    "budget":30000,
    "elec_price":0.56,
    "grid_ef":0.5810,
    "Qhp_rated1":12.0,
    "Qhp_rated2":12.0,
    "Qhp_rated3":10.0,
    # =========【V1.6 末端热工参数】=========
    # 原有散热器末端(方案1、方案2使用)
    "rad_Qrated_kW":14.0,          #散热器总额定散热量 kW
    "rad_dt_m_rated":64.5,         #散热器额定平均温差K（国标75/55，tn20：(75+55)/2‑20=64.5）
    "rad_m":0.30,                  #散热器散热指数m
    "rad_dt_flow_return":10.0,     #散热器供回水温差K
    "rad_tg_max":60.0,             #散热器允许最高供水温度℃
    # 增强型散热器末端(T1, 18自由组合模式使用)
    "rad_enh_Qrated_kW":18.0,      #增强散热器总额定散热量 kW
    "rad_enh_dt_m_rated":64.5,     #增强散热器额定平均温差K
    "rad_enh_m":0.30,              #增强散热器散热指数m
    "rad_enh_dt_flow_return":10.0, #增强散热器供回水温差K
    "rad_enh_tg_max":60.0,         #增强散热器允许最高供水温度℃
    # 低温地暖末端(方案3使用)
    "floor_Qrated_kW":14.0,        #地暖额定散热量 kW
    "floor_dt_m_rated":15.0,       #地暖额定平均温差K
    "floor_m":0.95,                #地暖散热指数m
    "floor_dt_flow_return":5.0,    #地暖供回水温差K
    "floor_tg_max":45.0,           #地暖允许最高供水温度℃
}
if "house_type" not in st.session_state:
    st.session_state["house_type"] = "中间层住宅"
if "build" not in st.session_state:
    st.session_state["build"] = DEFAULT_BUILD_MID.copy()
if "equip" not in st.session_state:
    st.session_state["equip"] = DEFAULT_EQUIP.copy()
if "retrofit_mode" not in st.session_state:
    st.session_state["retrofit_mode"] = "分户独立改造"
if "coef_set" not in st.session_state:
    st.session_state["coef_set"] = {"coef_envelope":0.75,"coef_pump":0.85,"coef_terminal":0.80}
if "calc_mode" not in st.session_state:
    st.session_state["calc_mode"] = "typical"

def switch_house_type(new_type):
    """切换户型，加载对应默认参数"""
    st.session_state["house_type"] = new_type
    if new_type == "中间层住宅":
        st.session_state["build"] = DEFAULT_BUILD_MID.copy()
    else:
        st.session_state["build"] = DEFAULT_BUILD_TOP_EDGE.copy()
###====工具函数 季节SPF====
def calc_season_spf(nameplate_scop, decay_factor):
    return round(nameplate_scop * decay_factor, 3)
###====calc_H：根据户型自动计算总热损失系数====
def calc_H(house_type, build_dict, volume, n, rho, cp):
    wall_net_A = build_dict["wall_gross"] - build_dict["win"]
    H_wall_WK = wall_net_A * build_dict["Kw"]
    H_win_WK = build_dict["win"] * build_dict["Kwin"]
    H_door_WK = build_dict["door_A"] * build_dict["K_door"]
    H_nonheat_WK = build_dict["nonheat_wall_A"] * build_dict["K_nonheat"]
    H_env_sum_WK = H_wall_WK + H_win_WK + H_door_WK + H_nonheat_WK
    #顶层边户额外增加屋面、东西山墙热损失
    if house_type == "顶层边户":
        H_roof_WK = build_dict["roof_A"] * build_dict["K_roof"]
        H_gable_WK = build_dict["gable_wall_A"] * build_dict["K_gable"]
        H_env_sum_WK = H_env_sum_WK + H_roof_WK + H_gable_WK
    #冷风渗透
    H_inf_WK = rho * cp * volume * n / 3600
    H_total_WK = H_env_sum_WK + H_inf_WK
    H_kWK = H_total_WK / 1000.0
    return H_kWK, wall_net_A

def calc_design_load(H_kWK, Tin, Tout_design):
    delta_T = Tin - Tout_design
    Qd_kW = H_kWK * delta_T
    return Qd_kW, delta_T

def calc_annual_heat(H_kWK, HDD18):
    Q_year_kwh = H_kWK * HDD18 * 24.0
    return Q_year_kwh

###====【V1.6 末端迭代求解最低供水温度】====
def solve_min_supply_temp(Q_load_kW, t_n, Q_rated_kW, dt_m_rated, m, dt_flow_return, tg_max, step=0.1):
    """
    Q_load_kW: 建筑设计热负荷 kW
    t_n:室内温度℃
    Q_rated_kW:末端额定总散热量 kW
    dt_m_rated:额定平均温差 K
    m:散热指数
    dt_flow_return:供‑回水温差 K
    tg_max:末端允许最大供水温度℃
    step:迭代步长
    返回：(tg_solve, th_solve, Q_terminal_calc, is_ok, advice_list)
    """
    advice_list = []
    tg = 20.0
    found = False
    Q_terminal_calc = 0.0
    while tg <= tg_max + 1e-6:
        th = tg - dt_flow_return
        dt_m = ((tg + th)/2.0) - t_n
        if dt_m <= 0:
            tg += step
            continue
        Q_terminal_calc = Q_rated_kW * pow(dt_m / dt_m_rated, m)
        if Q_terminal_calc >= Q_load_kW - 1e-4:
            found = True
            break
        tg += step
    th_solve = tg - dt_flow_return
    if found:
        return (round(tg,2), round(th_solve,2), round(Q_terminal_calc,3), True, [])
    else:
        advice_list.append("①可提高供水温度上限；")
        advice_list.append("②增大末端额定散热量（增加散热器片数 / 加密地暖管间距）；")
        advice_list.append("③更换低温辐射采暖末端。")
        return (round(tg_max,2), round(tg_max-dt_flow_return,2), round(Q_terminal_calc,3), False, advice_list)

# ===================== V1.7新增工具函数 =====================
def hp_sample_interpolate(sample_table, t_amb_input, tg_input, tg_fixed):
    """
    第一版简化插值：样本表固定供水温度tg_fixed；只对室外环境温度一维线性插值
    sample_table: [[T_amb, tg, cop, Qhp],...]
    t_amb_input: 当前室外温度 ℃
    tg_input: 当前系统供水温度（来自末端迭代tg）
    tg_fixed: 该样本对应的固定供水温度（厂家样本出水点）
    return: (cop_interp, qhp_interp, is_out_range, warn_msg)
    """
    warn_msg = []
    is_out_range = False
    # 校验供水温度和样本工况是否匹配
    if abs(tg_input - tg_fixed) > 2.0:
        warn_msg.append(f"⚠️供水温度{tg_input:.1f}℃偏离样本测试出水{tg_fixed}℃超过2K，插值可信度下降！")
    # 提取样本环境温度、cop、制热量
    t_amb_list = [row[0] for row in sample_table]
    cop_list = [row[2] for row in sample_table]
    qhp_list = [row[3] for row in sample_table]

    t_min = min(t_amb_list)
    t_max = max(t_amb_list)
    if t_amb_input < t_min or t_amb_input > t_max:
        is_out_range = True
        warn_msg.append(f"⚠️室外温度{t_amb_input:.1f}℃超出样本工况范围[{t_min}, {t_max}]℃，外推结果不可靠！")

    cop_interp = float(np.interp(t_amb_input, t_amb_list, cop_list))
    qhp_interp = float(np.interp(t_amb_input, t_amb_list, qhp_list))
    return cop_interp, qhp_interp, is_out_range, warn_msg


def calc_segment_annual_heat(H_kWK, total_HDD, seg_list):
    """
    分段计算每个温度区间的需热量
    seg_list: [(T_low,T_high,fraction),...] fraction区间占总HDD比例
    return list {"T_low":,"T_high":,"hdd_segment":,"Q_heat_kwh":}
    """
    seg_res = []
    for tl, th, frac in seg_list:
        hdd_seg = total_HDD * frac
        q_heat_kwh = H_kWK * hdd_seg * 24.0
        seg_res.append({
            "T_low": tl,
            "T_high": th,
            "hdd_segment": round(hdd_seg,2),
            "Q_heat_kwh": round(q_heat_kwh,2)
        })
    return seg_res

###====计算围护分项造价【单位造价×工程量】====
def calc_retrofit_cost(house_type, build_dict, equip_dict, cost_factor):
    wall_net_A = build_dict["wall_gross"] - build_dict["win"]
    cost_wall_ins = wall_net_A * equip_dict["unit_wall_ins"]
    cost_win = build_dict["win"] * equip_dict["unit_win_replace"]
    cost_door = build_dict["door_A"] * equip_dict["unit_door_replace"]
    cost_nonheat = build_dict["nonheat_wall_A"] * equip_dict["unit_nonheat_ins"]
    cost_roof_ins = 0.0
    cost_gable_ins = 0.0
    if house_type == "顶层边户":
        cost_roof_ins = build_dict["roof_A"] * equip_dict["unit_roof_ins"]
        cost_gable_ins = build_dict["gable_wall_A"] * equip_dict["unit_gable_ins"]
    cost_lowend_raw = build_dict["area"] * equip_dict["unit_lowend_floor"]
    sum_envelope_raw = cost_wall_ins + cost_win + cost_door + cost_nonheat + cost_roof_ins + cost_gable_ins
    sum_envelope_final = sum_envelope_raw * cost_factor
    cost_lowend_final = cost_lowend_raw * cost_factor
    res = {
        "wall_net_A":wall_net_A,
        "cost_wall_ins_raw":cost_wall_ins,
        "cost_win_raw":cost_win,
        "cost_door_raw":cost_door,
        "cost_nonheat_raw":cost_nonheat,
        "roof_A":build_dict.get("roof_A",0.0),
        "gable_wall_A":build_dict.get("gable_wall_A",0.0),
        "cost_roof_ins_raw":cost_roof_ins,
        "cost_gable_ins_raw":cost_gable_ins,
        "sum_envelope_raw":sum_envelope_raw,
        "sum_envelope_final":sum_envelope_final,
        "cost_lowend_raw":cost_lowend_raw,
        "cost_lowend_final":cost_lowend_final
    }
    return res
###====创新点工具函数====
def calc_sensitivity(base_envelope_cost, base_lowend_cost, base_elec_price, save_elec_2, save_elec_3):
    scenes = []
    env_cost_list = [round(base_envelope_cost*0.8,0), base_envelope_cost, round(base_envelope_cost*1.2,0)]
    elec_price_list = [round(base_elec_price-0.1,2), base_elec_price, round(base_elec_price+0.1,2)]
    for ec in env_cost_list:
        py2 = round(ec/(save_elec_2*base_elec_price),2) if save_elec_2>0 else None
        py3 = round((ec+base_lowend_cost)/(save_elec_3*base_elec_price),2) if save_elec_3>0 else None
        scenes.append({"场景":"围护造价:"+str(int(ec))+"元","电价":base_elec_price,"方案2回收期":py2,"方案3回收期":py3})
    for ep in elec_price_list:
        py2 = round(base_envelope_cost/(save_elec_2*ep),2) if save_elec_2>0 else None
        py3 = round((base_envelope_cost+base_lowend_cost)/(save_elec_3*ep),2) if save_elec_3>0 else None
        scenes.append({"场景":"电价:"+str(ep)+"元/kWh","电价":ep,"方案2回收期":py2,"方案3回收期":py3})
    return pd.DataFrame(scenes)

def get_radar_score(pay2,pay3,save_rate2,save_rate3,carbon_rate2,carbon_rate3,invest2,invest3):
    s1 = {"初投资":10,"回收期":10,"节能率":0,"减碳":0,"施工难度":10}
    score_pay2 = max(0, 10 - (pay2/15)*10) if pay2 is not None else 0
    score_save2 = save_rate2/100*10
    score_carbon2 = carbon_rate2/100*10
    score_inv2 = max(0,10-(invest2/80000)*10)
    score_con2 = 4
    s2={"初投资":score_inv2,"回收期":score_pay2,"节能率":score_save2,"减碳":score_carbon2,"施工难度":score_con2}
    score_pay3 = max(0,10-(pay3/15)*10) if pay3 is not None else 0
    score_save3 = save_rate3/100*10
    score_carbon3 = carbon_rate3/100*10
    score_inv3 = max(0,10-(invest3/80000)*10)
    score_con3 = 2
    s3={"初投资":score_inv3,"回收期":score_pay3,"节能率":score_save3,"减碳":score_carbon3,"施工难度":score_con3}
    return s1,s2,s3

###====输入校验工具====
def input_warning_check(build, equip):
    warn_list = []
    if build["area"] <= 0:
        warn_list.append("建筑面积必须大于0")
    if build["win"] <= 0:
        warn_list.append("外窗面积必须大于0")
    if (build["wall_gross"] - build["win"]) <= 0:
        warn_list.append("外墙毛面积必须大于窗户面积，否则外墙净面积为负！")
    if build["Kw_new"] >= build["Kw_old"]:
        warn_list.append("警告：改造后外墙K值不低于改造前，保温没有改善！")
    if build["Kwin_new"] >= build["Kwin_old"]:
        warn_list.append("警告：改造后窗户K值不低于改造前，窗户节能没有改善！")
    if build["Tin"] <= build["Tout"]:
        warn_list.append("室内温度必须大于室外设计温度，否则热负荷为负！")
    if not (0 < equip["spf_decay1"] <=1 and 0<equip["spf_decay2"]<=1 and 0<equip["spf_decay3"]<=1):
        warn_list.append("低温衰减系数必须在(0,1]之间")
    if equip["elec_price"] <=0:
        warn_list.append("电价必须大于0")
    return warn_list

def sync_build(key_widget, key_biz):
    st.session_state["build"][key_biz] = st.session_state[key_widget]

def sync_equip(key_widget, key_biz):
    st.session_state["equip"][key_biz] = st.session_state[key_widget]

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

# ================= V1.9新增：设计工况热泵容量 / 扩展输入校验 / 分项热损失 / 恢复统一基准 =================
def hp_available_at_design(build, equip, hp_id, tg_solve):
    """设计工况(T_out=郑州设计室外温度, 供水=tg_solve)热泵可用制热量与COP。
    不能把厂家样本额定制热量直接当郑州-7℃可用制热量：按室外温度一维插值后取min(额定制热量)。"""
    sample = SAMPLE_HP_LOWTEMP if hp_id == "HP1" else SAMPLE_HP_NORMAL
    tg_fixed = 45.0 if hp_id == "HP1" else 55.0
    t_design = build["Tout"]
    rated = equip["Qhp_rated3"] if hp_id == "HP1" else equip["Qhp_rated1"]
    cop_d, qhp_d, _outr, warns = hp_sample_interpolate(sample, t_design, tg_solve, tg_fixed)
    qhp_d = min(qhp_d, rated)
    return round(cop_d,3), round(qhp_d,3), warns

def input_warning_check_v18(build, equip, ht):
    """扩展输入边界与交叉校验（V1.10加强版，覆盖《小程序修改建议》4.1校验表全部规则；不改原input_warning_check）"""
    w = []
    def need_positive(name, v, lo, hi=None):
        if not (v > 0):
            w.append(f"【V1.10】{name}必须>0，当前={v}")
        elif hi is not None and v > hi:
            w.append(f"【V1.10】{name}超出合理上限{hi}，当前={v}")
    # ---- 面积/体积/K值/COP/容量/费用 必须>0 并设合理上下限 ----
    need_positive("建筑面积", build["area"], 0, 600)
    need_positive("楼层层高", build["floor_h"], 0, 6.0)
    need_positive("室内体积(面积×层高)", build["area"]*build["floor_h"], 0, 5000)
    need_positive("外墙毛面积", build["wall_gross"], 0, 600)
    need_positive("外窗面积", build["win"], 0, build.get("wall_gross", 999))
    need_positive("外门面积", build["door_A"], 0, 50)
    need_positive("非采暖隔墙面积", build["nonheat_wall_A"], 0, 300)
    for _kn, _n in [("Kw_old","外墙K值(改前)"),("Kw_new","外墙K值(改后)"),
                    ("Kwin_old","外窗K值(改前)"),("Kwin_new","外窗K值(改后)"),
                    ("K_door_old","外门K值(改前)"),("K_door_new","外门K值(改后)"),
                    ("K_nonheat_old","非采暖隔墙K值(改前)"),("K_nonheat_new","非采暖隔墙K值(改后)")]:
        if _kn in build:
            need_positive(_n, build[_kn], 0, 8.0)
    if ht == "顶层边户":
        for _kn, _n in [("K_roof_old","屋面K值(改前)"),("K_roof_new","屋面K值(改后)"),
                        ("K_gable_old","山墙K值(改前)"),("K_gable_new","山墙K值(改后)")]:
            if _kn in build:
                need_positive(_n, build[_kn], 0, 8.0)
    need_positive("常规热泵额定制热量", equip["Qhp_rated1"], 0, 100)
    need_positive("低温热泵额定制热量", equip["Qhp_rated3"], 0, 100)
    need_positive("常规热泵铭牌COP", equip["SCOP_nameplate1"], 0, 8.0)
    need_positive("低温热泵铭牌COP", equip["SCOP_nameplate3"], 0, 8.0)
    need_positive("热泵造价", equip["cost_pump"], 0)
    need_positive("预算", equip["budget"], 0)
    need_positive("电价", equip["elec_price"], 0, 3.0)
    need_positive("电网碳排放因子", equip["grid_ef"], 0, 2.0)
    for _uk in ["unit_wall_ins","unit_win_replace","unit_door_replace","unit_nonheat_ins",
                "unit_roof_ins","unit_gable_ins","unit_lowend_floor"]:
        need_positive("单位造价("+_uk+")", equip.get(_uk, 0.0), 0)
    # ---- 改造前后K值：K_after<K_before ----
    if build["Kw_new"] >= build["Kw_old"]:
        w.append("【V1.10】改造后外墙K值未低于改前，保温无改善，请核对")
    if build["Kwin_new"] >= build["Kwin_old"]:
        w.append("【V1.10】改造后外窗K值未低于改前，换窗无节能效果，请核对")
    # ---- 设计温度：T_in>T_out，否则禁止负热负荷 ----
    if build["Tin"] <= build["Tout"]:
        w.append("【V1.10】室内温度必须大于室外设计温度，否则热负荷为负，禁止计算")
    # ---- 低温衰减系数 0<f≤1 ----
    if not (0 < equip["spf_decay1"] <= 1 and 0 < equip["spf_decay2"] <= 1 and 0 < equip["spf_decay3"] <= 1):
        w.append("【V1.10】低温衰减系数必须∈(0,1]，避免效率被无依据放大")
    # ---- 供水温度位于机组和末端允许范围 ----
    if equip.get("floor_tg_max", 45.0) > 45:
        w.append("【V1.10】地暖供水温度上限超45℃，超常规低温辐射允许范围")
    if equip.get("rad_tg_max", 60.0) > 75:
        w.append("【V1.10】散热器供水温度上限超75℃，超出常规机组/末端允许范围")
    # ---- 墙窗面积几何关系：净/毛面积 ----
    if build.get("wall_gross", 0) <= build.get("win", 0):
        w.append("【V1.10】外墙毛面积须大于窗面积，否则外墙净面积为负（窗面积重复计入外墙）")
    return w

def calc_component_heat_loss(ht, build_dict, volume, n, rho, cp):
    """围护分项热损失分解：H(W/K)、设计温差热流Q(W)、占比%"""
    wall_net_A = build_dict["wall_gross"] - build_dict["win"]
    items = []
    def add(name, A, K):
        items.append({"构件":name,"面积(m²)":round(A,2),"K(W/m²·K)":round(K,3),"H(W/K)":round(A*K,2)})
    add("外墙(净面积)", wall_net_A, build_dict["Kw"])
    add("外窗", build_dict["win"], build_dict["Kwin"])
    add("外门", build_dict["door_A"], build_dict["K_door"])
    add("非采暖隔墙", build_dict["nonheat_wall_A"], build_dict["K_nonheat"])
    if ht == "顶层边户":
        add("屋面", build_dict.get("roof_A",0.0), build_dict.get("K_roof",0.0))
        add("东西山墙", build_dict.get("gable_wall_A",0.0), build_dict.get("K_gable",0.0))
    H_inf_WK = rho * cp * volume * n / 3600.0
    items.append({"构件":"冷风渗透","面积(m²)":"—","K(W/m²·K)":"—","H(W/K)":round(H_inf_WK,2)})
    total = sum(it["H(W/K)"] for it in items)
    dT = build_dict["Tin"] - build_dict["Tout"]
    for it in items:
        it["设计热流Q(W)"] = round(it["H(W/K)"]*dT,1)
        it["占比%"] = round(it["H(W/K)"]/total*100,1) if total>0 else 0
    return items

def reset_to_defaults():
    """恢复统一基准：重置建筑/设备/批量系数为默认值（答辩演示用）"""
    st.session_state["build"] = (DEFAULT_BUILD_MID if st.session_state["house_type"]=="中间层住宅" else DEFAULT_BUILD_TOP_EDGE).copy()
    st.session_state["equip"] = DEFAULT_EQUIP.copy()
    st.session_state["coef_set"] = {"coef_envelope":0.75,"coef_pump":0.85,"coef_terminal":0.80}

# ================= V1.8新增：18自由组合核心工具函数（原有函数全部保留） =================
def calc_segment_hp_aux(seg_list, hp_sample_table, hp_sample_tg_fixed, tg_solve, hp_rated_max_kW):
    """HDD分段：热泵可用制热能力受限部分用辅助电加热补充，输出E_aux与等效小时"""
    seg_out = []
    total_hp_elec = 0.0
    total_aux_elec = 0.0
    total_hours = 0.0
    for seg in seg_list:
        tl = seg["T_low"]
        th = seg["T_high"]
        hdd_seg = seg["hdd_segment"]
        q_heat_kwh = seg["Q_heat_kwh"]
        t_mid = (tl + th)/2.0
        hours_seg = hdd_seg * 24.0
        cop_seg, qhp_avail_kW, _, warns = hp_sample_interpolate(hp_sample_table, t_mid, tg_solve, hp_sample_tg_fixed)
        cop_seg = max(cop_seg, 0.1)
        qhp_avail_kW = min(qhp_avail_kW, hp_rated_max_kW)
        q_avg_load_kW = q_heat_kwh / hours_seg if hours_seg > 1e-6 else 0.0
        q_hp_kwh = min(q_heat_kwh, qhp_avail_kW * hours_seg)
        q_aux_kwh = max(0.0, q_heat_kwh - q_hp_kwh)
        elec_hp_seg = q_hp_kwh / cop_seg
        elec_aux_seg = q_aux_kwh
        total_hp_elec += elec_hp_seg
        total_aux_elec += elec_aux_seg
        total_hours += hours_seg
        seg_out.append({
            "T_low":tl,"T_high":th,"t_mid":t_mid,
            "hdd_seg":hdd_seg,"hours_seg":hours_seg,
            "Q_heat_kwh":q_heat_kwh,
            "cop_interp":round(cop_seg,3),
            "hp_avail_kW":round(qhp_avail_kW,3),
            "avg_load_kW":round(q_avg_load_kW,3),
            "Q_hp_kwh":round(q_hp_kwh,2),
            "Q_aux_kwh":round(q_aux_kwh,2),
            "elec_hp":round(elec_hp_seg,2),
            "elec_aux":round(elec_aux_seg,2),
            "warns":";".join(warns)
        })
    aux_equiv_hours = total_aux_elec / hp_rated_max_kW if hp_rated_max_kW > 1e-6 else 0.0
    return seg_out, total_hp_elec, total_aux_elec, round(aux_equiv_hours,2)


def calc_retrofit_cost_ex(house_type, build_dict, equip_dict, coef_envelope, coef_pump, coef_terminal):
    """分项独立批量折算：围护×coef_envelope、热泵×coef_pump、末端×coef_terminal"""
    wall_net_A = build_dict["wall_gross"] - build_dict["win"]
    cost_wall_ins = wall_net_A * equip_dict["unit_wall_ins"]
    cost_win = build_dict["win"] * equip_dict["unit_win_replace"]
    cost_door = build_dict["door_A"] * equip_dict["unit_door_replace"]
    cost_nonheat = build_dict["nonheat_wall_A"] * equip_dict["unit_nonheat_ins"]
    cost_roof_ins = 0.0
    cost_gable_ins = 0.0
    if house_type == "顶层边户":
        cost_roof_ins = build_dict["roof_A"] * equip_dict["unit_roof_ins"]
        cost_gable_ins = build_dict["gable_wall_A"] * equip_dict["unit_gable_ins"]
    cost_lowend_raw = build_dict["area"] * equip_dict["unit_lowend_floor"]
    sum_envelope_raw = cost_wall_ins + cost_win + cost_door + cost_nonheat + cost_roof_ins + cost_gable_ins
    sum_envelope_final = sum_envelope_raw * coef_envelope
    cost_lowend_final = cost_lowend_raw * coef_terminal
    cost_pump_final = equip_dict["cost_pump"] * coef_pump
    return {
        "wall_net_A":wall_net_A,
        "sum_envelope_raw":sum_envelope_raw,
        "sum_envelope_final":sum_envelope_final,
        "cost_lowend_raw":cost_lowend_raw,
        "cost_lowend_final":cost_lowend_final,
        "cost_pump_raw":equip_dict["cost_pump"],
        "cost_pump_final":cost_pump_final
    }


def calc_one_combination(ht, build_input, equip_input, coef_envelope, coef_pump, coef_terminal,
                         env_id, term_id, hp_id, hdd_segments):
    """计算一个自由组合方案，返回完整结果字典"""
    build_loc = build_input.copy()
    # ---- 围护K值选择 ----
    if env_id == "E0":
        build_loc["Kw"] = build_loc["Kw_old"]
        build_loc["Kwin"] = build_loc["Kwin_old"]
        build_loc["K_door"] = build_loc["K_door_old"]
        build_loc["K_nonheat"] = build_loc["K_nonheat_old"]
        if ht == "顶层边户":
            build_loc["K_roof"] = build_loc["K_roof_old"]
            build_loc["K_gable"] = build_loc["K_gable_old"]
        env_do_retrofit = False
    elif env_id in ("E1","E2"):
        build_loc["Kw"] = build_loc["Kw_new"]
        build_loc["Kwin"] = build_loc["Kwin_new"]
        build_loc["K_door"] = build_loc["K_door_new"]
        build_loc["K_nonheat"] = build_loc["K_nonheat_new"]
        if ht == "顶层边户":
            build_loc["K_roof"] = build_loc["K_roof_new"]
            build_loc["K_gable"] = build_loc["K_gable_new"]
        env_do_retrofit = True
    else:
        raise ValueError("非法env_id: "+str(env_id))
    # ---- 末端参数选择 ----
    if term_id == "T0":
        qr = equip_input["rad_Qrated_kW"]; dtmr = equip_input["rad_dt_m_rated"]; m_val = equip_input["rad_m"]
        dtfr = equip_input["rad_dt_flow_return"]; tgmax = equip_input["rad_tg_max"]
        term_is_lowend = False
    elif term_id == "T1":
        qr = equip_input.get("rad_enh_Qrated_kW",18.0); dtmr = equip_input.get("rad_enh_dt_m_rated",64.5)
        m_val = equip_input.get("rad_enh_m",0.30); dtfr = equip_input.get("rad_enh_dt_flow_return",10.0)
        tgmax = equip_input.get("rad_enh_tg_max",60.0)
        term_is_lowend = False
    elif term_id == "T2":
        qr = equip_input["floor_Qrated_kW"]; dtmr = equip_input["floor_dt_m_rated"]; m_val = equip_input["floor_m"]
        dtfr = equip_input["floor_dt_flow_return"]; tgmax = equip_input["floor_tg_max"]
        term_is_lowend = True
    else:
        raise ValueError("非法term_id: "+str(term_id))
    # ---- 热泵样本与额定制热量 ----
    hp_item = next(x for x in HEATPUMP_OPTIONS if x["id"] == hp_id)
    hp_sample = hp_item["sample_table"]
    hp_tg_fixed = hp_item["sample_tg_fixed"]
    hp_rated_max = equip_input[hp_item["rated_key"]]
    # ---- 热工计算 ----
    H_kWK, _ = calc_H(ht, build_loc, build_loc["volume"], build_loc["n"], build_loc["rho"], build_loc["cp"])
    Qd_kW, _ = calc_design_load(H_kWK, build_loc["Tin"], build_loc["Tout"])
    seg_heat = calc_segment_annual_heat(H_kWK, build_loc["HDD"], hdd_segments)
    tg_solve, th_solve, q_term_calc, term_ok, _ = solve_min_supply_temp(
        Qd_kW, build_loc["Tin"], qr, dtmr, m_val, dtfr, tgmax)
    seg_full, e_hp_total, e_aux_total, aux_equiv_h = calc_segment_hp_aux(
        seg_heat, hp_sample, hp_tg_fixed, tg_solve, hp_rated_max)
    e_total_elec = e_hp_total + e_aux_total
    # ---- 分项独立造价 ----
    cost_ex = calc_retrofit_cost_ex(ht, build_loc, equip_input, coef_envelope, coef_pump, coef_terminal)
    invest_pump = cost_ex["cost_pump_final"]
    invest_env = cost_ex["sum_envelope_final"] if env_do_retrofit else 0.0
    invest_terminal = cost_ex["cost_lowend_final"] if term_is_lowend else 0.0
    total_invest = invest_pump + invest_env + invest_terminal
    year_cost = e_total_elec * equip_input["elec_price"]
    co2_run_kg = round(e_total_elec * equip_input["grid_ef"], 2)
    return {
        "env_id":env_id,"term_id":term_id,"hp_id":hp_id,
        "H_kWK":round(H_kWK,4),"Qd_kW":round(Qd_kW,2),
        "q_load_per_area_Wm2":round(Qd_kW/build_loc["area"]*1000,2),
        "tg_solve":tg_solve,"th_solve":th_solve,
        "q_term_calc":q_term_calc,"term_ok":term_ok,
        "E_hp_kwh":round(e_hp_total,2),"E_aux_kwh":round(e_aux_total,2),
        "aux_equiv_hours":aux_equiv_h,"E_total_kwh":round(e_total_elec,2),
        "invest_pump":round(invest_pump,2),"invest_env":round(invest_env,2),
        "invest_terminal":round(invest_terminal,2),"total_invest":round(total_invest,2),
        "year_cost":round(year_cost,2),"co2_run_kg":co2_run_kg,
        "seg_detail":seg_full
    }


def payback_period_incremental(base_invest, add_invest, base_year_elec, new_year_elec, elec_price):
    """相对基准方案的增量静态回收期（仅方案间对比，非工程真实回收期）"""
    save_kwh = base_year_elec - new_year_elec
    if save_kwh <= 1e-3:
        return None
    annual_save_money = save_kwh * elec_price
    return round(add_invest / annual_save_money, 2)

# ======================全局页面基础配置 + 浅色科技CSS ======================
st.set_page_config(
    page_title="郑州老旧住宅热泵改造协同优化平台 V1.10",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)
light_tech_style = """
<style>
.stApp {
    background: linear-gradient(135deg, #f8fafc 0%, #eaf4ff 100%);
    color: #1e293b;
}
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
    font-size: 28px;
    font-weight: 800;
    background: linear-gradient(90deg, #6366f1, #8b5cf6, #ec4899);
    -webkit-background-clip: text;
    color: transparent;
    margin: 0 0 8px 0;
}
.light-tech-title p {
    font-size:15px;color:#64748b;margin:0;
}
[data-testid="stMetric"] {
    background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;padding:16px !important;transition:0.25s;
}
[data-testid="stMetric"]:hover {
    border-color:#6366f1;box-shadow:0 12px 28px rgba(99,102,241,0.12);
}
[data-testid="stMetricLabel"]{color:#475569 !important;font-weight:500;}
[data-testid="stMetricValue"]{color:#6366f1 !important;font-weight:800;}
div[data-testid="stMetricDelta"]>div{color:#10b981 !important;font-weight:600;}
.st-data-frame{background:#ffffff !important;border:1px solid #e2e8f0 !important;border-radius:12px !important;}
.st-data-frame th{background:linear-gradient(90deg,#6366f1,#8b5cf6) !important;color:#ffffff !important;}
div[data-baseweb="input"]{background:#ffffff !important;border:1px solid #cbd5e1 !important;border-radius:8px !important;}
label.st-label{color:#334155 !important;font-weight:500;}
.st-info>div{background:#eff6ff !important;border-left-color:#6366f1 !important;color:#1e40af !important;}
.st-warning>div{background:#fffbeb !important;border-left-color:#f59e0b !important;color:#92400e !important;}
.st-success>div{background:#f0fdf4 !important;border-left-color:#10b981 !important;color:#166534 !important;}
hr{border-color:rgba(99,102,241,0.22) !important;}
button[kind="primary"]{background:linear-gradient(90deg,#6366f1,#8b5cf6) !important;border:none !important;}
header[data-testid="stHeader"]{visibility:hidden;height:0;}
.block-container{padding-top:1.2rem;}
.hero-banner{
    background:linear-gradient(135deg,#312e81,#6d28d9 55%,#be185d);
    border-radius:16px;padding:20px 28px;margin-bottom:16px;color:#ffffff;
    box-shadow:0 12px 32px rgba(99,102,241,0.30);
}
.hero-banner .hero-main{font-size:26px;font-weight:800;letter-spacing:1px;}
.hero-banner .hero-sub{font-size:14px;color:#e0e7ff;margin-top:6px;}
.hero-banner .hero-meta{font-size:12.5px;color:#c7d2fe;margin-top:10px;border-top:1px solid rgba(255,255,255,0.25);padding-top:8px;}
.hero-banner .hero-route{font-size:12.5px;color:#fbcfe8;margin-top:6px;}
</style>
"""
st.markdown(light_tech_style, unsafe_allow_html=True)
st.markdown("""
<div class="hero-banner">
    <div class="hero-main">郑州老旧住宅热泵改造协同优化平台</div>
    <div class="hero-sub">围护改造 · 末端适配 · 空气源热泵选型 · 经济与碳排放测算｜郑州老旧住宅典型案例</div>
    <div class="hero-meta">作品：老旧住宅空气源热泵协同改造测算系统｜团队：**【团队名称】**｜版本：V1.10｜更新时间：2026-08-28</div>
    <div class="hero-route">技术路线：建筑围护 H → 设计负荷 → 末端反算供水温度 → 热泵设计工况容量/COP → HDD 分段能耗 → 经济/碳排 → 四道闸门 → 方案推荐</div>
</div>
""", unsafe_allow_html=True)

# ================= V1.8新增：可折叠参数来源台账（答辩追溯） =================
with st.expander("📌【V1.8新增】参数来源台账（答辩追溯·可折叠）", expanded=False):
    _b = st.session_state["build"]
    _e = st.session_state["equip"]
    _c = st.session_state["coef_set"]
    _rows = []
    def _r(name, val, unit, src, yr, pg, cond, tag):
        _rows.append({"参数名称":name,"数值":val,"单位":unit,"文件/标准":src,"年份":yr,"页码/表号":pg,"适用工况":cond,"源/算/假":tag})
    # ---- 建筑 & 围护 ----
    _r("建筑面积","{:.0f}".format(_b["area"]),"m²","《住宅设计规范》GB 50096-2011 / 实测","2011","表5.3","郑州老旧住宅","源")
    _r("层高","{:.2f}".format(_b["floor_h"]),"m","实测","-","-","郑州老旧住宅","源")
    _r("外墙K值(改前)","{:.2f}".format(_b["Kw_old"]),"W/(m²·K)","《民用建筑热工设计规范》GB 50176-2016","2016","附录B表B.0.1","郑州(夏热冬冷北缘)","源")
    _r("外墙K值(改后保温)","{:.2f}".format(_b["Kw_new"]),"W/(m²·K)","《严寒和寒冷地区居住建筑节能设计标准》JGJ 26-2018","2018","表4.2.2-3","郑州(围护限值)","源")
    _r("外窗K值(改前)","{:.2f}".format(_b["Kwin_old"]),"W/(m²·K)","JGJ 26-2018 / 实测","2018","表4.2.2-4","郑州","源")
    _r("外窗K值(改后)","{:.2f}".format(_b["Kwin_new"]),"W/(m²·K)","JGJ 26-2018(断桥铝中空)","2018","表4.2.2-4","郑州","源")
    _r("外门K值(改后)","{:.2f}".format(_b["K_door_new"]),"W/(m²·K)","JGJ 26-2018(节能门)","2018","表4.2.2-5","郑州","源")
    _r("非采暖隔墙K值(改后)","{:.2f}".format(_b["K_nonheat_new"]),"W/(m²·K)","JGJ 26-2018","2018","表4.2.2-6","楼梯间侧","源")
    _r("屋面K值(改后)","{:.2f}".format(_b.get("K_roof_new",0.0)),"W/(m²·K)","JGJ 26-2018","2018","表4.2.2-2","顶层边户","源")
    _r("东西山墙K值(改后)","{:.2f}".format(_b.get("K_gable_new",0.0)),"W/(m²·K)","JGJ 26-2018","2018","表4.2.2-3","顶层边户","源")
    # ---- 气象 ----
    _r("郑州采暖室外计算温度","{:.1f}".format(_b["Tout"]),"℃","《民用建筑热工设计规范》GB 50176-2016 附录A","2016","附录A表A.0.1","郑州站(57083)采暖设计","源")
    _r("室内采暖设计温度","{:.0f}".format(_b["Tin"]),"℃","《民用建筑供暖通风与空气调节设计规范》GB 50736-2012","2012","表3.0.1-1","住宅采暖房间","源")
    _r("HDD18采暖度日数","{:.0f}".format(_b["HDD"]),"℃·d","《中国建筑热环境分析专用气象数据集》(典型气象年)·郑州站57083","1984-2003","郑州站数据集表","基准温度18℃，统计周期典型气象年","源")
    _r("冷风渗透换气次数","{:.1f}".format(_b["n"]),"次/h","住宅通风经验值(客厅/卧室)","-","-","郑州住宅","假")
    _r("空气密度","{:.1f}".format(_b["rho"]),"kg/m³","工程热力学手册","-","-","标准大气","源")
    _r("空气定压比热","{:.0f}".format(_b["cp"]),"J/(kg·K)","工程热力学手册","-","-","标准大气","源")
    # ---- 热泵（含具体型号与工况） ----
    _r("常规热泵 COP","3.80 / 3.10 / 2.70 / 2.20 / 1.80","-","厂家选型手册·常规型空气源热泵【示例型号：Midea KFR-14SW/A(或按实际选型替换)】","2026","表2-3","A7/W55、A2/W55、A-2/W55、A-7/W55、A-10/W55","源/假")
    _r("低温热泵 COP","4.20 / 3.60 / 3.20 / 2.80 / 2.40","-","厂家选型手册·低温喷焓型空气源热泵【示例型号：Midea KFR-10NW/A(或按实际选型替换)】","2026","表2-3","A7/W45、A2/W45、A-2/W45、A-7/W45、A-10/W45","源/假")
    _r("常规热泵额定制热量","{:.1f}".format(_e["Qhp_rated1"]),"kW","厂家选型手册(样本)","2026","表2-3","A-7/W55","源/假")
    _r("低温热泵额定制热量","{:.1f}".format(_e["Qhp_rated3"]),"kW","厂家选型手册(样本)","2026","表2-3","A-7/W45","源/假")
    _r("热泵冬季衰减系数","{:.2f}/{:.2f}/{:.2f}".format(_e["spf_decay1"],_e["spf_decay2"],_e["spf_decay3"]),"-","结霜衰减经验系数(低环温)","-","-","-7℃以下","假")
    # ---- 末端 ----
    _r("散热器额定平均温差","{:.1f}".format(_e["rad_dt_m_rated"]),"K","GB/T 13754-2017(散热器国标75/55)","2017","表1","tn=20℃","源")
    _r("散热器散热指数m","{:.2f}".format(_e["rad_m"]),"-","GB/T 13754-2017(铸铁/钢制)","2017","表1","标准工况","源")
    _r("地暖额定平均温差","{:.1f}".format(_e["floor_dt_m_rated"]),"K","JGJ 142-2012《辐射供暖供冷技术规程》","2012","表5.4.1","低温热水地面辐射","源")
    _r("地暖散热指数m","{:.2f}".format(_e["floor_m"]),"-","JGJ 142-2012","2012","表5.4.1","标准工况","源")
    _r("增强散热器额定散热量","{:.1f}".format(_e.get("rad_enh_Qrated_kW",18.0)),"kW","厂家样本(增强型钢制散热器)【示例】","2026","-","A-7/W55","源/假")
    # ---- 造价（含调查时间/地区/报价对象/含税与恢复说明） ----
    _r("外墙保温单位造价","{:.0f}".format(_e["unit_wall_ins"]),"元/m²","郑州2026-08市场询价·老旧小区改造分包报价·含税含运输含施工含外墙面恢复","2026","-","郑州地区","假")
    _r("外窗更换单位造价","{:.0f}".format(_e["unit_win_replace"]),"元/m²","郑州2026-08询价(断桥铝中空)含税含安装含拆除","2026","-","郑州地区","假")
    _r("外门更换单位造价","{:.0f}".format(_e["unit_door_replace"]),"元/m²","郑州2026-08询价(节能门)含税含安装","2026","-","郑州地区","假")
    _r("非采暖隔墙保温单位造价","{:.0f}".format(_e["unit_nonheat_ins"]),"元/m²","郑州2026-08询价含税含施工","2026","-","郑州地区","假")
    _r("屋面保温单位造价","{:.0f}".format(_e["unit_roof_ins"]),"元/m²","郑州2026-08询价含税含防水保护层恢复","2026","-","顶层边户","假")
    _r("东西山墙保温单位造价","{:.0f}".format(_e["unit_gable_ins"]),"元/m²","郑州2026-08询价含税含施工(吊篮/脚手架)","2026","-","顶层边户","假")
    _r("地暖末端单位造价","{:.0f}".format(_e["unit_lowend_floor"]),"元/m²","郑州2026-08询价含税含回填含找平","2026","-","郑州地区","假")
    _r("热泵采购安装总价","{:.0f}".format(_e["cost_pump"]),"元/台","郑州2026-08经销商报价·含税含运输含安装含基础","2026","-","郑州地区","假")
    _r("居民电价","{:.2f}".format(_e["elec_price"]),"元/kWh","河南省居民阶梯电价(现行)","2023","豫发改价管〔2023〕号","居民采暖","源")
    _r("电网碳排放因子","{:.4f}".format(_e["grid_ef"]),"kgCO₂/kWh","全国电网平均排放因子(生态环境部公告)","2022","-","运行阶段","源")
    # ---- 批量折算系数（调研依据） ----
    _r("围护批量折算系数","{:.2f}".format(_c["coef_envelope"]),"-","行业调研经验·老旧小区EPC集采/外脚手架共用/人工摊薄(页面2可改)","2026","-","整栋集中批量","假")
    _r("热泵批量折算系数","{:.2f}".format(_c["coef_pump"]),"-","行业调研经验·厂家批量供货/统一班组安装省差旅(页面2可改)","2026","-","整栋集中批量","假")
    _r("末端批量折算系数","{:.2f}".format(_c["coef_terminal"]),"-","行业调研经验·批量进场/开槽回填工序统一调度(页面2可改)","2026","-","整栋集中批量","假")
    # ---- 计算结果口径（算） ----
    _r("总热损失系数H","-","kW/K","本程序按围护+冷风渗透计算(见页面3)","-","-","模型输出","算")
    _r("设计热负荷Q_design","-","kW","H×ΔT，无附加耗热量(见页面3)","-","-","模型输出","算")
    _r("全年需热量Q_year","-","kWh","H×HDD18×24(见页面3)","-","-","模型输出","算")
    _r("E_HP / E_aux","-","kWh","HDD分段×样本COP插值，容量不足部分辅助电加热(见页面3展开)","-","-","模型输出","算")
    _ledger_df = pd.DataFrame(_rows)
    st.caption("标注：【源】=规范/数据库/实测直接引用；【算】=程序计算；【假】=经验假设或示例值，答辩前请按实际选型/询价替换。热泵【示例型号】需替换为真实选型。")
    st.dataframe(_ledger_df, use_container_width=True, hide_index=True, height=320)

#侧边栏
with st.sidebar:
    st.markdown("""
<div style="padding:10px 0;border-bottom:1px solid rgba(99,102,241,0.25);margin-bottom:14px;">
<h3 style="color:#6366f1;margin:0;">📌 参数来源台账</h3>
<div style="font-size:12px;color:#666;">V1.7｜热泵样本插值+HDD分段能耗｜末端热工迭代求供水温度｜围护：单位造价×工程量</div>
</div>
""", unsafe_allow_html=True)
    sel_house = st.selectbox("🏠选择户型",["中间层住宅","顶层边户"])
    if sel_house != st.session_state["house_type"]:
        switch_house_type(sel_house)
    ht = st.session_state["house_type"]
    if ht == "中间层住宅":
        st.info("【中间层住宅】上下均采暖住户；不计屋面、地面楼板；构件：外墙、外窗、外门、非采暖隔墙")
    else:
        st.info("【顶层边户】顶层+东西山墙边户；计入屋面、东西山墙；不计底层地面楼板")
    st.session_state["retrofit_mode"] = st.selectbox("🔧改造造价模式", list(RETROFIT_MODE_CFG.keys()))
    cost_factor = RETROFIT_MODE_CFG[st.session_state["retrofit_mode"]]["cost_factor"]
    st.info(f"批量造价折算系数：{cost_factor}")
    # ===== V1.8新增：计算模式切换 =====
    st.session_state["calc_mode"] = st.radio("🧮计算模式",["三套典型方案","18种自由组合批量计算"])
    if st.session_state["calc_mode"] == "18种自由组合批量计算":
        st.session_state["calc_mode"] = "batch_18"
    else:
        st.session_state["calc_mode"] = "typical"

    # ===== V1.9新增：模型版本号 + 恢复统一基准 =====
    st.markdown("**🛠 模型版本号：V1.10**（按《小程序修改建议》修订）")
    st.caption("更新时间：2026-08-28\n计算链：H → Q_design → Q_year → SPF/COP → E_HP → E_aux → 费用 → 碳排放")
    if st.button("♻️恢复统一基准（重置全部默认参数）", use_container_width=True):
        reset_to_defaults()
        st.success("已恢复统一基准：建筑/设备/批量系数回到默认值")
    # ===== V1.10新增：保存方案快照（可载入） =====
    if st.button("💾保存当前方案", use_container_width=True):
        _snap = {
            "时间": datetime.datetime.now().strftime("%m-%d %H:%M"),
            "户型": st.session_state["house_type"],
            "建筑": dict(st.session_state["build"]),
            "设备": dict(st.session_state["equip"]),
            "系数": dict(st.session_state["coef_set"]),
        }
        if "saved_schemes" not in st.session_state:
            st.session_state["saved_schemes"] = []
        st.session_state["saved_schemes"].append(_snap)
        st.success(f"已保存方案{len(st.session_state['saved_schemes'])}（{_snap['时间']}，{_snap['户型']}）")
    if st.session_state.get("saved_schemes"):
        with st.expander(f"📚已保存方案（{len(st.session_state['saved_schemes'])}个，点击载入）"):
            for _si, _s in enumerate(st.session_state["saved_schemes"]):
                if st.button(f"载入方案{_si+1}｜{_s['时间']}｜{_s['户型']}", key=f"load_scheme_{_si}", use_container_width=True):
                    st.session_state["build"] = _s["建筑"]
                    st.session_state["equip"] = _s["设备"]
                    st.session_state["coef_set"] = _s["系数"]
                    st.rerun()
    st.divider()
    st.markdown("""
    1. 建筑传热系数K：《民用建筑热工设计规范》GB 50176
    2. 热负荷：本模型不计算朝向、风力、高度附加耗热量
    3. 郑州采暖度日数HDD18：中国建筑节能气象参数数据库
    4. 空气源热泵样本参考GB/T 25127.1
    5. ⚠️本程序**不适用底层住户**
    6. V1.7：厂家样本一维插值；HDD多温度分段计算全年能耗；保留旧SPF算法对比
    """)
    st.divider()
    page_select = st.radio("功能页面切换", [
        "1.建筑围护参数录入",
        "2.热泵&末端热工&单位造价录入",
        "3.三套方案计算结果",
        "4.手工校核验算页"
    ])

# ======================页面1：建筑围护参数录入 ======================
if page_select == "1.建筑围护参数录入":
    ht = st.session_state["house_type"]
    st.markdown(f"""
<div class="light-tech-title">
    <h1>🏠建筑围护结构参数｜对象：{ht}</h1>
</div>
""", unsafe_allow_html=True)
    if ht == "中间层住宅":
        st.warning("⚠️边界条件：上下楼层均为采暖住户；不计屋面、地面楼板热损失；构件：外墙、外窗、外门、非采暖楼梯间隔墙；无附加耗热量。本模型不适用顶层、底层、边户。")
    else:
        st.warning("⚠️边界条件：顶层东西山墙边户；计入屋面、东西山墙热损失；不计底层地面楼板；构件：普通外墙、东西山墙、屋面、外窗、外门、非采暖楼梯间隔墙；无附加耗热量。本模型不适用底层住户。")
    build = st.session_state["build"]
    warn_messages = input_warning_check(build, st.session_state["equip"])
    for w in warn_messages:
        st.warning(w)

    # ===== V1.9新增：扩展输入边界与交叉校验 =====
    for wv in input_warning_check_v18(build, st.session_state["equip"], ht):
        st.warning(wv)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📐建筑基础尺寸")
        st.number_input("建筑面积 m²",value=build["area"],key="_area",on_change=sync_build,args=("_area", "area"))
        st.number_input("楼层层高 m",value=build["floor_h"],key="_floor_h",on_change=sync_build,args=("_floor_h", "floor_h"))
        room_volume = build["area"] * build["floor_h"]
        st.metric("室内总体积 m³", value=round(room_volume,2))
        st.number_input("外墙毛总面积 m²（含窗洞口）",value=build["wall_gross"],key="_wall_gross",on_change=sync_build,args=("_wall_gross","wall_gross"))
        st.number_input("外窗总面积 m²",value=build["win"],key="_win",on_change=sync_build,args=("_win","win"))
        st.number_input("外门面积 m²",value=build["door_A"],key="_door_A",on_change=sync_build,args=("_door_A","door_A"))
        st.number_input("非采暖隔墙面积 m²(楼梯间等)",value=build["nonheat_wall_A"],key="_nonheat_wall_A",on_change=sync_build,args=("_nonheat_wall_A","nonheat_wall_A"))
        if ht == "顶层边户":
            st.divider()
            st.subheader("顶层边户专属构件")
            st.number_input("屋面面积 m²",value=build["roof_A"],key="_roof_A",on_change=sync_build,args=("_roof_A","roof_A"))
            st.number_input("东西山墙面积 m²",value=build["gable_wall_A"],key="_gable_wall_A",on_change=sync_build,args=("_gable_wall_A","gable_wall_A"))
    with col2:
        st.subheader("🔥围护传热系数 K W/(m²·K)")
        st.markdown("**外墙 & 外窗 & 外门 & 非采暖隔墙**")
        st.number_input("改造前外墙K",value=build["Kw_old"],key="_Kw_old",on_change=sync_build,args=("_Kw_old","Kw_old"))
        st.number_input("改造后外墙保温K",value=build["Kw_new"],key="_Kw_new",on_change=sync_build,args=("_Kw_new","Kw_new"))
        st.number_input("改造前外窗K",value=build["Kwin_old"],key="_Kwin_old",on_change=sync_build,args=("_Kwin_old","Kwin_old"))
        st.number_input("改造后外窗K",value=build["Kwin_new"],key="_Kwin_new",on_change=sync_build,args=("_Kwin_new","Kwin_new"))
        st.number_input("改造前外门K",value=build["K_door_old"],key="_K_door_old",on_change=sync_build,args=("_K_door_old","K_door_old"))
        st.number_input("改造后外门K",value=build["K_door_new"],key="_K_door_new",on_change=sync_build,args=("_K_door_new","K_door_new"))
        st.number_input("改造前非采暖隔墙K",value=build["K_nonheat_old"],key="_K_nonheat_old",on_change=sync_build,args=("_K_nonheat_old","K_nonheat_old"))
        st.number_input("改造后非采暖隔墙K",value=build["K_nonheat_new"],key="_K_nonheat_new",on_change=sync_build,args=("_K_nonheat_new","K_nonheat_new"))
        if ht == "顶层边户":
            st.divider()
            st.markdown("**顶层边户专属K值（屋面、东西山墙）**")
            st.number_input("改造前屋面K",value=build["K_roof_old"],key="_K_roof_old",on_change=sync_build,args=("_K_roof_old","K_roof_old"))
            st.number_input("改造后屋面保温K",value=build["K_roof_new"],key="_K_roof_new",on_change=sync_build,args=("_K_roof_new","K_roof_new"))
            st.number_input("改造前东西山墙K",value=build["K_gable_old"],key="_K_gable_old",on_change=sync_build,args=("_K_gable_old","K_gable_old"))
            st.number_input("改造后东西山墙保温K",value=build["K_gable_new"],key="_K_gable_new",on_change=sync_build,args=("_K_gable_new","K_gable_new"))
    st.divider()
    col3,col4 = st.columns(2)
    with col3:
        st.subheader("🌡️气象室内设计参数")
        st.number_input("室内采暖设计温度 ℃",value=build["Tin"],key="_Tin",on_change=sync_build,args=("_Tin","Tin"))
        st.number_input("郑州室外设计温度 ℃",value=build["Tout"],key="_Tout",on_change=sync_build,args=("_Tout","Tout"))
        delta_T = build["Tin"] - build["Tout"]
        st.metric("室内外温差ΔT(K)", delta_T)
        st.number_input("HDD18采暖度日数 ℃·d",value=build["HDD"],key="_HDD",on_change=sync_build,args=("_HDD","HDD"))
    with col4:
        st.subheader("💨冷风渗透参数")
        st.number_input("冷风渗透换气次数 次/h",value=build["n"],key="_n",on_change=sync_build,args=("_n","n"))
        st.number_input("空气密度 kg/m³",value=build["rho"],key="_rho",on_change=sync_build,args=("_rho","rho"))
        st.number_input("空气定压比热容 J/(kg·K)",value=build["cp"],key="_cp",on_change=sync_build,args=("_cp","cp"))
        st.info("本模型**不设置朝向、风力、高度附加耗热量**")
    st.session_state["build"]["volume"] = build["area"] * build["floor_h"]
    st.session_state["build"]["dT"] = build["Tin"] - build["Tout"]
    st.success(f"✅{ht}围护参数保存完毕，前往页面2录入热泵、末端热工与单位造价参数")
# ======================页面2：热泵&末端热工&单位造价录入【V1.7增加厂家样本表】 ======================
elif page_select == "2.热泵&末端热工&单位造价录入":
    st.markdown("""
<div class="light-tech-title">
    <h1>🔥 空气源热泵、末端热工模型、围护分项单位造价录入</h1>
    <p>👉V1.6更新：不再手动输入供水温度；输入末端额定参数，程序迭代反算满足热负荷的最低供水温度；围护=单位造价×工程量</p>
    <p>👉V1.7新增：热泵厂家样本数据表；一维插值；HDD分段全年能耗计算</p>
    <p>末端公式：$Q_{terminal}=Q_{rated} \\times (\\Delta T_m / \\Delta T_{m,rated})^m$</p>
</div>
""", unsafe_allow_html=True)
    equip = st.session_state["equip"]
    build = st.session_state["build"]
    warn_messages = input_warning_check(build, equip)
    for w in warn_messages:
        st.warning(w)
    col_left, col_mid, col_right = st.columns([1,1,1])
    # ===== V1.8新增：分项独立批量折算系数（可编辑，含调研依据） =====
    st.subheader("🔧批量改造分项折算系数（可编辑）")
    st.info("""
**调研参考依据（行业经验值，项目需结合当地招标报价修正）：**
1. 分户独立改造：围护=1.00，热泵=1.00，末端=1.00；
2. 整栋集中批量改造参考：
   - 围护保温工程 **0.75**：老旧小区EPC批量集采、外脚手架共用、人工摊薄；
   - 空气源热泵设备安装 **0.85**：厂家批量供货、统一班组安装，省去零散上门差旅成本；
   - 室内末端改造 **0.80**：批量进场、开槽回填工序统一调度。
""")
    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        st.number_input("围护工程折算系数", min_value=0.4, max_value=1.0, step=0.01,
                        value=st.session_state["coef_set"]["coef_envelope"], key="_coef_env",
                        on_change=lambda: st.session_state["coef_set"].update({"coef_envelope": st.session_state["_coef_env"]}))
    with cc2:
        st.number_input("热泵设备安装折算系数", min_value=0.4, max_value=1.0, step=0.01,
                        value=st.session_state["coef_set"]["coef_pump"], key="_coef_pump",
                        on_change=lambda: st.session_state["coef_set"].update({"coef_pump": st.session_state["_coef_pump"]}))
    with cc3:
        st.number_input("室内末端改造折算系数", min_value=0.4, max_value=1.0, step=0.01,
                        value=st.session_state["coef_set"]["coef_terminal"], key="_coef_term",
                        on_change=lambda: st.session_state["coef_set"].update({"coef_terminal": st.session_state["_coef_term"]}))
    st.divider()
    col_left, col_mid, col_right = st.columns([1,1,1])
    with col_left:
        st.subheader("空气源热泵参数（固定总价）")
        st.number_input("方案1常规热泵铭牌SCOP",value=equip["SCOP_nameplate1"],key="_SCOPnp1",on_change=sync_equip,args=("_SCOPnp1", "SCOP_nameplate1"))
        st.number_input("方案2常规热泵铭牌SCOP",value=equip["SCOP_nameplate2"],key="_SCOPnp2",on_change=sync_equip,args=("_SCOPnp2", "SCOP_nameplate2"))
        st.number_input("方案3低温专用热泵铭牌SCOP",value=equip["SCOP_nameplate3"],key="_SCOPnp3",on_change=sync_equip,args=("_SCOPnp3", "SCOP_nameplate3"))
        st.divider()
        st.subheader("❄️冬季低温衰减系数(0<f≤1)")
        st.number_input("方案1 衰减系数",value=equip["spf_decay1"],key="_decay1",on_change=sync_equip,args=("_decay1", "spf_decay1"))
        st.number_input("方案2 衰减系数",value=equip["spf_decay2"],key="_decay2",on_change=sync_equip,args=("_decay2", "spf_decay2"))
        st.number_input("方案3 衰减系数",value=equip["spf_decay3"],key="_decay3",on_change=sync_equip,args=("_decay3", "spf_decay3"))
        st.divider()
        st.subheader("🧪 热泵‑7℃工况额定制热量(kW)")
        st.number_input("方案1热泵额定制热量 kW",value=equip["Qhp_rated1"],key="_Qhp_rated1",on_change=sync_equip,args=("_Qhp_rated1", "Qhp_rated1"))
        st.number_input("方案2热泵额定制热量 kW",value=equip["Qhp_rated2"],key="_Qhp_rated2",on_change=sync_equip,args=("_Qhp_rated2", "Qhp_rated2"))
        st.number_input("方案3低温热泵额定制热量 kW",value=equip["Qhp_rated3"],key="_Qhp_rated3",on_change=sync_equip,args=("_Qhp_rated3", "Qhp_rated3"))
    with col_mid:
        st.subheader("🧱围护分项单位造价【元/m²】")
        st.number_input("外墙保温单位造价 元/m²",value=equip["unit_wall_ins"],key="_unit_wall_ins",on_change=sync_equip,args=("_unit_wall_ins","unit_wall_ins"))
        st.number_input("外窗更换单位造价 元/m²",value=equip["unit_win_replace"],key="_unit_win_replace",on_change=sync_equip,args=("_unit_win_replace","unit_win_replace"))
        st.number_input("外门更换单位造价 元/m²",value=equip["unit_door_replace"],key="_unit_door_replace",on_change=sync_equip,args=("_unit_door_replace","unit_door_replace"))
        st.number_input("非采暖隔墙保温单位造价 元/m²",value=equip["unit_nonheat_ins"],key="_unit_nonheat_ins",on_change=sync_equip,args=("_unit_nonheat_ins","unit_nonheat_ins"))
        st.divider()
        st.info("顶层边户才生效，中间层不计入")
        st.number_input("屋面保温单位造价 元/m²",value=equip["unit_roof_ins"],key="_unit_roof_ins",on_change=sync_equip,args=("_unit_roof_ins","unit_roof_ins"))
        st.number_input("东西山墙保温单位造价 元/m²",value=equip["unit_gable_ins"],key="_unit_gable_ins",on_change=sync_equip,args=("_unit_gable_ins","unit_gable_ins"))
        st.divider()
        st.subheader("低温地暖末端造价")
        st.number_input("地暖末端单位造价 元/㎡建筑面积",value=equip["unit_lowend_floor"],key="_unit_lowend_floor",on_change=sync_equip,args=("_unit_lowend_floor","unit_lowend_floor"))
    with col_right:
        st.subheader("💰设备总价与经济参数")
        st.number_input("空气源热泵采购安装总价 元【固定，与面积无关】",value=equip["cost_pump"],key="_cost_pump",on_change=sync_equip,args=("_cost_pump", "cost_pump"))
        st.number_input("业主改造费用预算 元",value=equip["budget"],key="_budget",on_change=sync_equip,args=("_budget", "budget"))
        st.number_input("居民电价 元/kWh",value=equip["elec_price"],key="_elec_price",on_change=sync_equip,args=("_elec_price", "elec_price"))
        st.number_input("电网碳排放因子 kgCO₂/kWh",value=equip["grid_ef"],key="_grid_ef",on_change=sync_equip,args=("_grid_ef", "grid_ef"))
    st.divider()
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.subheader("🔥原有散热器末端（方案1、方案2使用）")
        st.number_input("散热器总额定散热量 kW",value=equip["rad_Qrated_kW"],key="_rad_Qrated_kW",on_change=sync_equip,args=("_rad_Qrated_kW","rad_Qrated_kW"))
        st.number_input("散热器额定平均温差 K",value=equip["rad_dt_m_rated"],key="_rad_dt_m_rated",on_change=sync_equip,args=("_rad_dt_m_rated","rad_dt_m_rated"))
        st.number_input("散热器散热指数 m",value=equip["rad_m"],key="_rad_m",on_change=sync_equip,args=("_rad_m","rad_m"))
        st.number_input("散热器供‑回水温差 K",value=equip["rad_dt_flow_return"],key="_rad_dt_flow_return",on_change=sync_equip,args=("_rad_dt_flow_return","rad_dt_flow_return"))
        st.number_input("散热器允许最高供水温度 ℃",value=equip["rad_tg_max"],key="_rad_tg_max",on_change=sync_equip,args=("_rad_tg_max","rad_tg_max"))
    with col_t2:
        st.subheader("❄️低温地暖末端（仅方案3使用）")
        st.number_input("地暖总额定散热量 kW",value=equip["floor_Qrated_kW"],key="_floor_Qrated_kW",on_change=sync_equip,args=("_floor_Qrated_kW","floor_Qrated_kW"))
        st.number_input("地暖额定平均温差 K",value=equip["floor_dt_m_rated"],key="_floor_dt_m_rated",on_change=sync_equip,args=("_floor_dt_m_rated","floor_dt_m_rated"))
        st.number_input("地暖散热指数 m",value=equip["floor_m"],key="_floor_m",on_change=sync_equip,args=("_floor_m","floor_m"))
        st.number_input("地暖供‑回水温差 K",value=equip["floor_dt_flow_return"],key="_floor_dt_flow_return",on_change=sync_equip,args=("_floor_dt_flow_return","floor_dt_flow_return"))
        st.number_input("地暖允许最高供水温度 ℃",value=equip["floor_tg_max"],key="_floor_tg_max",on_change=sync_equip,args=("_floor_tg_max","floor_tg_max"))

    # ========= V1.7新增：热泵厂家样本表展示 =========
    st.divider()
    st.subheader("📋热泵厂家样本数据表（用于插值计算COP、可用制热量）")
    st.info("第一版：样本固定出水温度；根据室外温度线性插值；超出样本范围输出报警")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.markdown("**方案1/2 常规热泵样本｜样本出水：55℃**")
        df_sample_norm = pd.DataFrame(SAMPLE_HP_NORMAL,columns=["室外温度℃","样本供水温度℃","COP","可用制热量kW"])
        st.dataframe(df_sample_norm)
    with col_s2:
        st.markdown("**方案3 低温热泵样本｜样本出水：45℃**")
        df_sample_low = pd.DataFrame(SAMPLE_HP_LOWTEMP,columns=["室外温度℃","样本供水温度℃","COP","可用制热量kW"])
        st.dataframe(df_sample_low)

    st.success("✅热泵、末端热工、单位造价参数保存完毕，进入第三页；程序自动迭代求解最低供水温度！")
# ======================页面3：三套方案计算结果 ======================
elif page_select == "3.三套方案计算结果":
    ht = st.session_state["house_type"]
    build = st.session_state["build"]
    equip = st.session_state["equip"]
    cost_factor = RETROFIT_MODE_CFG[st.session_state["retrofit_mode"]]["cost_factor"]
    st.markdown(f"""
<div class="light-tech-title">
    <h1>📊三套改造方案｜户型：{ht}｜V1.7【热泵样本插值+HDD分段能耗】</h1>
</div>
""", unsafe_allow_html=True)
    if ht == "中间层住宅":
        st.warning("⚠️边界：中间层，上下均采暖住户；不计屋面、地面楼板；构件：外墙、外窗、外门、非采暖隔墙；无附加耗热量；本结果不能用于顶层、底层、边户！")
    else:
        st.warning("⚠️边界：顶层东西山墙边户；计入屋面、东西山墙；不计底层地面楼板；无附加耗热量；本结果不能用于中间层、底层住户！")
    if "build" not in st.session_state or "equip" not in st.session_state:
        st.warning("⚠️请先录入页面1、页面2参数")
        st.stop()
    warn_messages = input_warning_check(build, equip)
    for w in warn_messages:
        st.warning(w)
    allow_wall_retrofit = st.checkbox("✅允许外墙围护改造（若小区外立面限制可取消勾选）",value=True)
    spf1 = calc_season_spf(equip["SCOP_nameplate1"], equip["spf_decay1"])
    spf2 = calc_season_spf(equip["SCOP_nameplate2"], equip["spf_decay2"])
    spf3 = calc_season_spf(equip["SCOP_nameplate3"], equip["spf_decay3"])
    st.info(f"📌季节综合SPF（旧算法使用）：方案1={spf1}｜方案2={spf2}｜方案3={spf3}")
    cost_dict = calc_retrofit_cost(ht, build, equip, cost_factor)
    real_cost_pump = equip["cost_pump"]
    real_envelope = cost_dict["sum_envelope_final"]
    real_lowend = cost_dict["cost_lowend_final"]
    with st.expander("🔍展开查看围护工程量 & 分项造价明细（原始未批量）"):
        df_cost_detail = pd.DataFrame([
            {"分项":"外墙保温","工程量m²":cost_dict["wall_net_A"],"单位造价元/m²":equip["unit_wall_ins"],"原始造价元":round(cost_dict["cost_wall_ins_raw"],2)},
            {"分项":"外窗更换","工程量m²":build["win"],"单位造价元/m²":equip["unit_win_replace"],"原始造价元":round(cost_dict["cost_win_raw"],2)},
            {"分项":"外门更换","工程量m²":build["door_A"],"单位造价元/m²":equip["unit_door_replace"],"原始造价元":round(cost_dict["cost_door_raw"],2)},
            {"分项":"非采暖隔墙保温","工程量m²":build["nonheat_wall_A"],"单位造价元/m²":equip["unit_nonheat_ins"],"原始造价元":round(cost_dict["cost_nonheat_raw"],2)},
            {"分项":"屋面保温【顶层边户】","工程量m²":cost_dict["roof_A"],"单位造价元/m²":equip["unit_roof_ins"],"原始造价元":round(cost_dict["cost_roof_ins_raw"],2)},
            {"分项":"东西山墙保温【顶层边户】","工程量m²":cost_dict["gable_wall_A"],"单位造价元/m²":equip["unit_gable_ins"],"原始造价元":round(cost_dict["cost_gable_ins_raw"],2)},
            {"分项":"低温地暖末端","工程量m²建筑面积":build["area"],"单位造价元/m²建筑面积":equip["unit_lowend_floor"],"原始造价元":round(cost_dict["cost_lowend_raw"],2)},
            {"分项":"围护改造合计(原始)","工程量m²":"-","单位造价元/m²":"-","原始造价元":round(cost_dict["sum_envelope_raw"],2)},
        ])
        st.dataframe(df_cost_detail, use_container_width=True)
        st.info(f"批量折算系数{cost_factor}；折算后围护合计：{round(real_envelope,2)}元；折算后地暖：{round(real_lowend,2)}元；热泵固定总价：{real_cost_pump}元")

    # --------方案1：围护不改造，散热器末端 --------
    build_old = build.copy()
    build_old["Kw"] = build_old["Kw_old"]
    build_old["Kwin"] = build_old["Kwin_old"]
    build_old["K_door"] = build_old["K_door_old"]
    build_old["K_nonheat"] = build_old["K_nonheat_old"]
    if ht == "顶层边户":
        build_old["K_roof"] = build_old["K_roof_old"]
        build_old["K_gable"] = build_old["K_gable_old"]
    H1_kWK, wallnet1 = calc_H(ht, build_old, build["volume"], build["n"], build["rho"], build["cp"])
    Qd1_kW, dT_design = calc_design_load(H1_kWK, build["Tin"], build["Tout"])
    q_year1_kwh = calc_annual_heat(H1_kWK, build["HDD"])
    seg1 = calc_segment_annual_heat(H1_kWK, build["HDD"], HDD_SEGMENTS)
    tg1, th1, qterm1, end_ok1, advice1 = solve_min_supply_temp(
        Qd1_kW, build["Tin"],
        equip["rad_Qrated_kW"], equip["rad_dt_m_rated"], equip["rad_m"],
        equip["rad_dt_flow_return"], equip["rad_tg_max"]
    )
    hp_warns_1 = []
    elec_seg_sum_1 = 0.0
    for seg in seg1:
        t_seg_mid = (seg["T_low"] + seg["T_high"]) / 2.0
        cop_seg, qhp_seg, out_range, warns = hp_sample_interpolate(SAMPLE_HP_NORMAL, t_seg_mid, tg1, tg_fixed=55.0)
        hp_warns_1.extend(warns)
        if cop_seg <= 0.1:
            cop_seg = 0.1
        elec_seg = seg["Q_heat_kwh"] / cop_seg
        elec_seg_sum_1 += elec_seg
        seg.update({"t_mid":t_seg_mid,"cop_interp":cop_seg,"qhp_avail":qhp_seg,"elec_kwh":elec_seg})

    elec_1_old = elec_consume(q_year1_kwh, spf1)
    elec_1 = elec_seg_sum_1
    invest_1 = real_cost_pump
    year_cost_1 = elec_1 * equip["elec_price"]
    need_aux1, aux_load1 = check_aux_electric_heat(Qd1_kW, equip["Qhp_rated1"])
    co2_1 = calc_carbon(elec_1, equip["grid_ef"])
    q_load_per_area1 = round(Qd1_kW / build["area"] *1000, 2)

    # --------方案2：围护改造，仍然散热器末端 --------
    build_new = build.copy()
    build_new["Kw"] = build_new["Kw_new"]
    build_new["Kwin"] = build_new["Kwin_new"]
    build_new["K_door"] = build_new["K_door_new"]
    build_new["K_nonheat"] = build_new["K_nonheat_new"]
    if ht == "顶层边户":
        build_new["K_roof"] = build_new["K_roof_new"]
        build_new["K_gable"] = build_new["K_gable_new"]
    H2_kWK, wallnet2 = calc_H(ht, build_new, build["volume"], build["n"], build["rho"], build["cp"])
    Qd2_kW, _ = calc_design_load(H2_kWK, build["Tin"], build["Tout"])
    q_year2_kwh = calc_annual_heat(H2_kWK, build["HDD"])
    seg2 = calc_segment_annual_heat(H2_kWK, build["HDD"], HDD_SEGMENTS)
    tg2, th2, qterm2, end_ok2, advice2 = solve_min_supply_temp(
        Qd2_kW, build["Tin"],
        equip["rad_Qrated_kW"], equip["rad_dt_m_rated"], equip["rad_m"],
        equip["rad_dt_flow_return"], equip["rad_tg_max"]
    )
    hp_warns_2 = []
    elec_seg_sum_2 = 0.0
    for seg in seg2:
        t_seg_mid = (seg["T_low"] + seg["T_high"]) / 2.0
        cop_seg, qhp_seg, out_range, warns = hp_sample_interpolate(SAMPLE_HP_NORMAL, t_seg_mid, tg2, tg_fixed=55.0)
        hp_warns_2.extend(warns)
        if cop_seg <=0.1:
            cop_seg=0.1
        elec_seg = seg["Q_heat_kwh"] / cop_seg
        elec_seg_sum_2 += elec_seg
        seg.update({"t_mid":t_seg_mid,"cop_interp":cop_seg,"qhp_avail":qhp_seg,"elec_kwh":elec_seg})
    elec_2_old = elec_consume(q_year2_kwh, spf2)
    elec_2 = elec_seg_sum_2
    invest_2 = real_cost_pump + real_envelope
    year_cost_2 = elec_2 * equip["elec_price"]
    save_elec_2 = elec_1 - elec_2
    payback_2 = payback_period(real_envelope, save_elec_2, equip["elec_price"])
    load_save_rate_2 = round((Qd1_kW - Qd2_kW)/Qd1_kW*100,2)
    elec_save_rate_2 = round((elec_1 - elec_2)/elec_1*100,2)
    need_aux2, aux_load2 = check_aux_electric_heat(Qd2_kW, equip["Qhp_rated2"])
    co2_2 = calc_carbon(elec_2, equip["grid_ef"])
    co2_reduce_2 = round(co2_1 - co2_2,2)
    co2_reduce_rate_2 = round((co2_1 - co2_2)/co2_1*100,2) if co2_1>0 else 0
    q_load_per_area2 = round(Qd2_kW / build["area"] *1000,2)

    # --------方案3：围护改造+更换地暖末端 --------
    H3_kWK = H2_kWK
    Qd3_kW = Qd2_kW
    q_year3_kwh = q_year2_kwh
    seg3 = calc_segment_annual_heat(H3_kWK, build["HDD"], HDD_SEGMENTS)
    tg3, th3, qterm3, end_ok3, advice3 = solve_min_supply_temp(
        Qd3_kW, build["Tin"],
        equip["floor_Qrated_kW"], equip["floor_dt_m_rated"], equip["floor_m"],
        equip["floor_dt_flow_return"], equip["floor_tg_max"]
    )
    hp_warns_3 = []
    elec_seg_sum_3 = 0.0
    for seg in seg3:
        t_seg_mid = (seg["T_low"] + seg["T_high"]) / 2.0
        cop_seg, qhp_seg, out_range, warns = hp_sample_interpolate(SAMPLE_HP_LOWTEMP, t_seg_mid, tg3, tg_fixed=45.0)
        hp_warns_3.extend(warns)
        if cop_seg <=0.1:
            cop_seg=0.1
        elec_seg = seg["Q_heat_kwh"] / cop_seg
        elec_seg_sum_3 += elec_seg
        seg.update({"t_mid":t_seg_mid,"cop_interp":cop_seg,"qhp_avail":qhp_seg,"elec_kwh":elec_seg})
    elec_3_old = elec_consume(q_year3_kwh, spf3)
    elec_3 = elec_seg_sum_3
    invest_3 = real_cost_pump + real_envelope + real_lowend
    year_cost_3 = elec_3 * equip["elec_price"]
    save_elec_3 = elec_1 - elec_3
    payback_3 = payback_period((real_envelope + real_lowend), save_elec_3, equip["elec_price"])
    load_save_rate_3 = round((Qd1_kW - Qd3_kW)/Qd1_kW*100,2)
    elec_save_rate_3 = round((elec_1 - elec_3)/elec_1*100,2)
    need_aux3, aux_load3 = check_aux_electric_heat(Qd3_kW, equip["Qhp_rated3"])
    co2_3 = calc_carbon(elec_3, equip["grid_ef"])
    co2_reduce_3 = round(co2_1 - co2_3,2)
    co2_reduce_rate_3 = round((co2_1 - co2_3)/co2_1*100,2) if co2_1>0 else 0
    q_load_per_area3 = round(Qd3_kW / build["area"] *1000,2)

    budget = equip["budget"]
    def get_scheme_status(invest, allow_wall, q_load, qhp_rated, end_ok):
        budget_ok = invest <= budget
        engineering_ok = allow_wall
        hp_cap_ok = qhp_rated >= q_load
        terminal_ok = end_ok
        eligible = budget_ok and engineering_ok and hp_cap_ok and terminal_ok
        return {"budget_ok":budget_ok,"engineering_ok":engineering_ok,"hp_cap_ok":hp_cap_ok,"terminal_ok":terminal_ok,"eligible":eligible}
    stat1 = get_scheme_status(invest_1, True, Qd1_kW, equip["Qhp_rated1"], end_ok1)
    stat2 = get_scheme_status(invest_2, allow_wall_retrofit, Qd2_kW, equip["Qhp_rated2"], end_ok2)
    stat3 = get_scheme_status(invest_3, allow_wall_retrofit, Qd3_kW, equip["Qhp_rated3"], end_ok3)
    status_df = pd.DataFrame([
        {"方案":"方案1仅换热泵","预算满足":stat1["budget_ok"],"工程允许外墙":stat1["engineering_ok"],"热泵容量足够":stat1["hp_cap_ok"],"末端能力满足":stat1["terminal_ok"],"整体可行":stat1["eligible"]},
        {"方案":"方案2围护+热泵","预算满足":stat2["budget_ok"],"工程允许外墙":stat2["engineering_ok"],"热泵容量足够":stat2["hp_cap_ok"],"末端能力满足":stat2["terminal_ok"],"整体可行":stat2["eligible"]},
        {"方案":"方案3围护+末端+热泵","预算满足":stat3["budget_ok"],"工程允许外墙":stat3["engineering_ok"],"热泵容量足够":stat3["hp_cap_ok"],"末端能力满足":stat3["terminal_ok"],"整体可行":stat3["eligible"]},
    ])
    st.subheader("🔍四道可行性闸门状态表（新增：末端能力满足校验）")
    st.dataframe(status_df, use_container_width=True)

    # ===== V1.9新增：四道独立可行性闸门（热泵按设计工况可用制热量校核，P0错误2修正） =====
    with st.expander("🚦【V1.9新增】四道独立可行性闸门（热泵用设计工况可用制热量）"):
        st.info("热泵容量不能直接用样本额定制热量：须用设计工况(室外=郑州设计温度，供水=末端反算tg)插值后的可用制热量Q_HP,avail校核。")
        _tg_list = [tg1, tg2, tg3]
        _hp_ids = ["HP0", "HP0", "HP1"]
        _rows_gate = []
        _gate_reasons = []
        for _i, (nm, inv, allowwall, Qd, tgv, hpid, endok) in enumerate([
            ("方案1仅换热泵", invest_1, True, Qd1_kW, tg1, "HP0", end_ok1),
            ("方案2围护+热泵", invest_2, allow_wall_retrofit, Qd2_kW, tg2, "HP0", end_ok2),
            ("方案3围护+末端+低温热泵", invest_3, allow_wall_retrofit, Qd3_kW, tg3, "HP1", end_ok3),
        ]):
            cop_d, qhp_d, _warn_d = hp_available_at_design(build, equip, hpid, tgv)
            b_ok = inv <= budget
            e_ok = allowwall
            h_ok = qhp_d >= Qd
            t_ok = endok
            _rows_gate.append({"方案":nm, "初投资(元)":round(inv,0), "预算满足":b_ok, "工程允许外墙":e_ok,
                               "设计工况Q_HP可用(kW)":qhp_d, "设计负荷(kW)":round(Qd,2), "热泵容量满足":h_ok,
                               "末端满足":t_ok, "整体可行":b_ok and e_ok and h_ok and t_ok})
            _rs = []
            if not b_ok: _rs.append("❌超出预算")
            if not e_ok: _rs.append("❌工程禁止外墙改造")
            if not h_ok: _rs.append("❌热泵容量不足(设计工况)")
            if not t_ok: _rs.append("❌末端能力不足")
            _gate_reasons.append("；".join(_rs) if _rs else "✅全部条件通过")
        st.dataframe(pd.DataFrame(_rows_gate), use_container_width=True, hide_index=True)
        for _nm, _rsn in zip(["方案1", "方案2", "方案3"], _gate_reasons):
            st.markdown(f"**{_nm}**：{_rsn}")
        st.caption("四个独立判断逐条输出，不再合并为『超预算/工程禁止』标签；工程禁止时不会误报为预算不足。")
    def gen_status_text(st):
        msg_list=[]
        if not st["budget_ok"]: msg_list.append("❌超出预算")
        if not st["engineering_ok"]: msg_list.append("❌工程禁止外墙改造")
        if not st["hp_cap_ok"]: msg_list.append("❌热泵容量不足，需辅助电加热")
        if not st["terminal_ok"]: msg_list.append("❌末端能力不足，无法覆盖热负荷")
        return "；".join(msg_list) if len(msg_list)>0 else "✅全部条件通过，方案可行"
    tag_1 = gen_status_text(stat1)
    tag_2 = gen_status_text(stat2)
    tag_3 = gen_status_text(stat3)
    candidates=[]
    if stat2["eligible"] and payback_2 is not None:
        candidates.append(("方案2",payback_2,elec_save_rate_2))
    if stat3["eligible"] and payback_3 is not None:
        candidates.append(("方案3",payback_3,elec_save_rate_3))
    best_scheme = min(candidates,key=lambda x:x[1])[0] if candidates else None
    budget_sufficient = budget >= invest_3*1.2
    eco_scheme = None
    if stat2["eligible"] and stat3["eligible"]:
        eco_scheme = "方案3" if elec_save_rate_3>=elec_save_rate_2 else "方案2"
    elif stat2["eligible"]: eco_scheme="方案2"
    elif stat3["eligible"]: eco_scheme="方案3"
    st.session_state["calc_mid"] = {
        "H1_kWK":H1_kWK,"Qd1_kW":Qd1_kW,"q_year1_kwh":q_year1_kwh,"spf1":spf1,"elec1":elec_1,
        "seg1":seg1,
        "H2_kWK":H2_kWK,"Qd2_kW":Qd2_kW,"q_year2_kwh":q_year2_kwh,"spf2":spf2,"elec2":elec_2,
        "seg2":seg2,
        "H3_kWK":H3_kWK,"Qd3_kW":Qd3_kW,"q_year3_kwh":q_year3_kwh,"spf3":spf3,"elec3":elec_3,
        "seg3":seg3,
        "q_load_per_area1":q_load_per_area1,"q_load_per_area2":q_load_per_area2,"q_load_per_area3":q_load_per_area3,
        "aux_load1":aux_load1,"aux_load2":aux_load2,"aux_load3":aux_load3,
        "co2_1":co2_1,"co2_2":co2_2,"co2_3":co2_3,
        "tg1":tg1,"tg2":tg2,"tg3":tg3
    }
    st.info(f"🔍中间输出｜方案1总热损失H1={round(H1_kWK,4)} kW/K；单位面积热负荷 {q_load_per_area1} W/m²")
    #输出热泵样本插值报警
    for w in hp_warns_1:
        st.warning("[方案1] "+w)
    for w in hp_warns_2:
        st.warning("[方案2] "+w)
    for w in hp_warns_3:
        st.warning("[方案3] "+w)

    # 末端改进建议
    if not end_ok1:
        st.warning("⚠️【方案1末端能力不足改进建议】"+" ".join(advice1))
    if not end_ok2:
        st.warning("⚠️【方案2末端能力不足改进建议】"+" ".join(advice2))
    if not end_ok3:
        st.warning("⚠️【方案3末端能力不足改进建议】"+" ".join(advice3))

    with st.expander("🔍查看：室外温度分段插值能耗明细"):
        st.markdown("**方案1分段明细**")
        st.dataframe(pd.DataFrame(seg1))
        st.markdown("**方案2分段明细**")
        st.dataframe(pd.DataFrame(seg2))
        st.markdown("**方案3分段明细**")
        st.dataframe(pd.DataFrame(seg3))

    # ===== V1.8新增：辅助电加热 E_aux + 运行小时（三套方案，追加不改原逻辑） =====
    with st.expander("🔋【V1.8新增】辅助电加热：运行小时 & 年耗电量 E_aux"):
        st.info("按HDD各温度分段计算：热泵可用制热能力不足的部分由辅助电加热承担；等效运行小时 = E_aux / 热泵额定制热量。")
        aux_items = [
            (seg1, tg1, SAMPLE_HP_NORMAL, 55.0, equip["Qhp_rated1"], "方案1：仅热泵(E0-T0-HP0)"),
            (seg2, tg2, SAMPLE_HP_NORMAL, 55.0, equip["Qhp_rated2"], "方案2：围护+热泵(E2-T0-HP0)"),
            (seg3, tg3, SAMPLE_HP_LOWTEMP, 45.0, equip["Qhp_rated3"], "方案3：围护+地暖+低温热泵(E2-T2-HP1)"),
        ]
        aux_cols = st.columns(3)
        for idx, (seg_x, tg_x, sample_x, tg_fix_x, rated_x, label_x) in enumerate(aux_items):
            seg_full_x, e_hp_x, e_aux_x, aux_h_x = calc_segment_hp_aux(seg_x, sample_x, tg_fix_x, tg_x, rated_x)
            with aux_cols[idx]:
                st.markdown(f"**{label_x}**")
                st.metric("热泵年耗电 E_HP (kWh)", round(e_hp_x, 2))
                st.metric("辅助电加热 E_aux (kWh)", round(e_aux_x, 2))
                st.metric("辅助电等效运行小时 (h)", aux_h_x)
                df_aux_seg = pd.DataFrame(seg_full_x)[["T_low","T_high","Q_heat_kwh","Q_hp_kwh","Q_aux_kwh","elec_hp","elec_aux"]]
                st.dataframe(df_aux_seg, use_container_width=True)

    # ===== V1.9新增：围护分项热损失分解 & 能耗强度 & HDD回归校核对照 =====
    with st.expander("🔍【V1.9新增】围护分项热损失分解 & 能耗强度 kWh/(m²·a) & 回归校核"):
        _vol_room = build["area"] * build["floor_h"]
        comp_old = calc_component_heat_loss(ht, build_old, _vol_room, build["n"], build["rho"], build["cp"])
        comp_new = calc_component_heat_loss(ht, build_new, _vol_room, build["n"], build["rho"], build["cp"])
        c1o, c2o = st.columns(2)
        with c1o:
            st.markdown("**改造前围护分项热损失（方案1基准）**")
            st.dataframe(pd.DataFrame(comp_old), use_container_width=True, hide_index=True)
        with c2o:
            st.markdown("**改造后围护分项热损失（方案2/3）**")
            st.dataframe(pd.DataFrame(comp_new), use_container_width=True, hide_index=True)
        st.caption("外墙面积按净面积（毛面积−窗洞口）计，避免窗面积重复计热损失；顶层边户另计屋面、东西山墙。")
        ei1 = elec_1 / build["area"]; ei2 = elec_2 / build["area"]; ei3 = elec_3 / build["area"]
        eic = st.columns(3)
        for _j, (_nm, _ei) in enumerate([("方案1", ei1), ("方案2", ei2), ("方案3", ei3)]):
            with eic[_j]:
                st.metric(f"{_nm} 采暖能耗强度", f"{_ei:.1f} kWh/(m²·a)")
                if _ei > 150:
                    st.warning("能耗强度异常偏高(>150 kWh/(m²·a))，请核对参数数量级")
        _aux_all = []
        for _segx, _sx, _tfx, _rtx in [(seg1, SAMPLE_HP_NORMAL, 55.0, equip["Qhp_rated1"]),
                                       (seg2, SAMPLE_HP_NORMAL, 55.0, equip["Qhp_rated2"]),
                                       (seg3, SAMPLE_HP_LOWTEMP, 45.0, equip["Qhp_rated3"])]:
            _sg, _eh, _ea, _ah = calc_segment_hp_aux(_segx, _sx, _tfx, _tfx, _rtx)
            _aux_all.append((_eh, _ea))
        st.markdown("**🧮 HDD回归校核对照：SPF法(Q_year/SPF) vs 分段插值法（量纲均已按 H×HDD×24 修正）**")
        reg_df = pd.DataFrame({
            "方案":["方案1","方案2","方案3"],
            "H(kW/K)":[round(H1_kWK,4),round(H2_kWK,4),round(H3_kWK,4)],
            "Q_year(kWh)":[round(q_year1_kwh,1),round(q_year2_kwh,1),round(q_year3_kwh,1)],
            "季节SPF":[spf1,spf2,spf3],
            "SPF法E(kWh)":[round(elec_1_old,1),round(elec_2_old,1),round(elec_3_old,1)],
            "分段插值E_HP(kWh)":[round(_aux_all[0][0],1),round(_aux_all[1][0],1),round(_aux_all[2][0],1)],
            "E_aux(kWh)":[round(_aux_all[0][1],1),round(_aux_all[1][1],1),round(_aux_all[2][1],1)],
        })
        st.dataframe(reg_df, use_container_width=True, hide_index=True)
        st.caption("SPF法为简化链 E=Q_year/SPF；分段插值法为主算法（HDD分段×样本COP，含容量约束）。两者差异源于温度分布与部分负荷，属正常。")

    st.divider()
    col_a,col_b,col_c = st.columns(3)
    CARD_FIX_HEIGHT=740
    with col_a:
        with st.container(height=CARD_FIX_HEIGHT):
            st.markdown("### 🟦方案1｜仅更换热泵（基准，原有散热器）")
            st.metric("总热损失系数H(kW/K)",round(H1_kWK,4))
            st.metric("设计热负荷(kW)",round(Qd1_kW,2))
            st.metric("单位面积热负荷(W/m²)",q_load_per_area1)
            st.metric("铭牌SCOP",equip["SCOP_nameplate1"])
            st.metric("季节SPF",spf1)
            st.metric("迭代最低供水温度℃",tg1)
            st.metric("回水温度℃",th1)
            st.metric("末端计算散热量(kW)",qterm1)
            st.metric("末端能力是否满足","✅满足" if end_ok1 else "❌不满足")
            st.metric("年采暖需热量(kWh)",round(q_year1_kwh,1))
            st.metric("年耗电(kWh)",round(elec_1,1))
            st.metric("旧SPF算法年耗电(kWh)",round(elec_1_old,1))
            st.metric("年CO₂排放(kg)",co2_1)
            st.metric("是否需辅助电加热","✅需要" if need_aux1 else "❌不需要")
            st.divider()
            st.metric("总初投资(元)",round(invest_1,0))
            st.markdown(f"**可行性校验：**{tag_1}")
    with col_b:
        with st.container(height=CARD_FIX_HEIGHT):
            st.markdown("### 🟩方案2｜围护保温改造+常规热泵（保留原有散热器）")
            if not allow_wall_retrofit: st.info("🚫工程约束，禁止围护改造")
            st.metric("总热损失系数H(kW/K)",round(H2_kWK,4))
            st.metric("设计热负荷(kW)",round(Qd2_kW,2),delta=f"-{load_save_rate_2}%")
            st.metric("单位面积热负荷(W/m²)",q_load_per_area2)
            st.metric("铭牌SCOP",equip["SCOP_nameplate2"])
            st.metric("季节SPF",spf2)
            st.metric("迭代最低供水温度℃",tg2)
            st.metric("回水温度℃",th2)
            st.metric("末端计算散热量(kW)",qterm2)
            st.metric("末端能力是否满足","✅满足" if end_ok2 else "❌不满足")
            st.metric("年采暖需热量(kWh)",round(q_year2_kwh,1))
            st.metric("年耗电(kWh)",round(elec_2,1),delta=f"-{elec_save_rate_2}%")
            st.metric("旧SPF算法年耗电(kWh)",round(elec_2_old,1))
            st.metric("年CO₂排放(kg)",co2_2,delta=f"-{co2_reduce_rate_2}%")
            st.metric("是否需辅助电加热","✅需要" if need_aux2 else "❌不需要")
            st.divider()
            st.metric("围护改造造价(批量后)",round(real_envelope,0))
            st.metric("总初投资(元)",round(invest_2,0))
            st.markdown(f"**可行性校验：**{tag_2}")
    with col_c:
        with st.container(height=CARD_FIX_HEIGHT):
            st.markdown("### 🟨方案3｜围护改造+低温地暖+低温热泵")
            if not allow_wall_retrofit: st.info("🚫工程约束，禁止围护改造")
            st.metric("总热损失系数H(kW/K)",round(H3_kWK,4))
            st.metric("设计热负荷(kW)",round(Qd3_kW,2),delta=f"-{load_save_rate_3}%")
            st.metric("单位面积热负荷(W/m²)",q_load_per_area3)
            st.metric("铭牌SCOP",equip["SCOP_nameplate3"])
            st.metric("季节SPF",spf3)
            st.metric("迭代最低供水温度℃",tg3)
            st.metric("回水温度℃",th3)
            st.metric("末端计算散热量(kW)",qterm3)
            st.metric("末端能力是否满足","✅满足" if end_ok3 else "❌不满足")
            st.metric("年采暖需热量(kWh)",round(q_year3_kwh,1))
            st.metric("年耗电(kWh)",round(elec_3,1),delta=f"-{elec_save_rate_3}%")
            st.metric("旧SPF算法年耗电(kWh)",round(elec_3_old,1))
            st.metric("年CO₂排放(kg)",co2_3,delta=f"-{co2_reduce_rate_3}%")
            st.metric("是否需辅助电加热","✅需要" if need_aux3 else "❌不需要")
            st.divider()
            st.metric("围护+地暖造价(批量后)",round(real_envelope+real_lowend,0))
            st.metric("总初投资(元)",round(invest_3,0))
            st.markdown(f"**可行性校验：**{tag_3}")
    st.divider()
    result_df = pd.DataFrame({
        "户型":[ht,ht,ht],
        "改造方案":["方案1：仅更换热泵","方案2：围护改造+常规热泵","方案3：围护+低温末端+低温热泵"],
        "总热损失系数H(kW/K)":[round(H1_kWK,4),round(H2_kWK,4),round(H3_kWK,4)],
        "设计热负荷(kW)":[round(Qd1_kW,2),round(Qd2_kW,2),round(Qd3_kW,2)],
        "单位面积热负荷(W/m²)":[q_load_per_area1,q_load_per_area2,q_load_per_area3],
        "铭牌SCOP":[equip["SCOP_nameplate1"],equip["SCOP_nameplate2"],equip["SCOP_nameplate3"]],
        "季节综合SPF":[spf1,spf2,spf3],
        "迭代最低供水温度(℃)":[tg1,tg2,tg3],
        "回水温度(℃)":[th1,th2,th3],
        "末端计算散热量(kW)":[qterm1,qterm2,qterm3],
        "末端能力是否满足":["是" if end_ok1 else "否","是" if end_ok2 else "否","是" if end_ok3 else "否"],
        "热泵额定制热量(kW)":[equip["Qhp_rated1"],equip["Qhp_rated2"],equip["Qhp_rated3"]],
        "热泵设备总价(元)":[real_cost_pump,real_cost_pump,real_cost_pump],
        "围护改造造价(批量后元)":[0,round(real_envelope,0),round(real_envelope,0)],
        "低温地暖末端造价(批量后元)":[0,0,round(real_lowend,0)],
        "是否需要辅助电加热":["是" if need_aux1 else "否","是" if need_aux2 else "否","是" if need_aux3 else "否"],
        "辅助电加热承担负荷(kW)":[aux_load1,aux_load2,aux_load3],
        "热负荷削减率(%)":["基准",load_save_rate_2,load_save_rate_3],
        "全年采暖需热量(kWh)":[round(q_year1_kwh,1),round(q_year2_kwh,1),round(q_year3_kwh,1)],
        "分段插值算法年耗电量(kWh)":[round(elec_1,1),round(elec_2,1),round(elec_3,1)],
        "旧SPF算法年耗电量(kWh)":[round(elec_1_old,1),round(elec_2_old,1),round(elec_3_old,1)],
        "耗电量节能率(%)":["基准",elec_save_rate_2,elec_save_rate_3],
        "年运行CO₂排放(kgCO₂)":[co2_1,co2_2,co2_3],
        "年减碳量(kgCO₂)":["基准",co2_reduce_2,co2_reduce_3],
        "碳排放削减率(%)":["基准",co2_reduce_rate_2,co2_reduce_rate_3],
        "项目总初投资(元)":[round(invest_1,0),round(invest_2,0),round(invest_3,0)],
        "可行性校验":[tag_1,tag_2,tag_3],
        "年采暖电费(元)":[round(year_cost_1,2),round(year_cost_2,2),round(year_cost_3,2)],
        "静态增量投资回收期(年)":["基准",payback_2,payback_3]
    })
    st.dataframe(result_df, use_container_width=True)
    csv_bytes = result_df.to_csv(index=False,encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button("📥下载CSV结果",csv_bytes,file_name=f"{ht}_热泵改造V1.7_样本插值分段能耗.csv",mime="text/csv")

    # ===== V1.9新增：导出完整计算报告（输入+来源+中间变量+可行性+推荐） =====
    with st.expander("📤【V1.9新增】导出完整计算报告（含全部输入/来源/中间变量/可行性/推荐）"):
        _coef_s = st.session_state["coef_set"]
        _rep_rows = []
        _rep_rows.append({"类别":"批量系数","参数":"coef_envelope","数值":_coef_s["coef_envelope"],"来源":"行业调研经验(台账·页面2可改)","备注":""})
        _rep_rows.append({"类别":"批量系数","参数":"coef_pump","数值":_coef_s["coef_pump"],"来源":"行业调研经验(台账·页面2可改)","备注":""})
        _rep_rows.append({"类别":"批量系数","参数":"coef_terminal","数值":_coef_s["coef_terminal"],"来源":"行业调研经验(台账·页面2可改)","备注":""})
        for _k, _v in build.items():
            _rep_rows.append({"类别":"输入-建筑","参数":_k,"数值":_v,"来源":"见参数来源台账","备注":""})
        for _k, _v in equip.items():
            _rep_rows.append({"类别":"输入-设备/造价","参数":_k,"数值":_v,"来源":"见参数来源台账","备注":""})
        for _nm, _v1, _v2, _v3 in [
            ("H(kW/K)", H1_kWK, H2_kWK, H3_kWK),
            ("Q_design(kW)", Qd1_kW, Qd2_kW, Qd3_kW),
            ("Q_year(kWh)", q_year1_kwh, q_year2_kwh, q_year3_kwh),
            ("SPF", spf1, spf2, spf3),
            ("供水温度tg(℃)", tg1, tg2, tg3),
            ("E_HP(kWh)", _aux_all[0][0], _aux_all[1][0], _aux_all[2][0]),
            ("E_aux(kWh)", _aux_all[0][1], _aux_all[1][1], _aux_all[2][1]),
            ("年电费(元)", year_cost_1, year_cost_2, year_cost_3),
            ("碳排放(kgCO₂)", co2_1, co2_2, co2_3),
        ]:
            _rep_rows.append({"类别":"中间变量","参数":_nm,
                              "数值":f"方案1:{round(_v1,2)} | 方案2:{round(_v2,2)} | 方案3:{round(_v3,2)}",
                              "来源":"程序计算","备注":"H→Qd→Q_year→SPF→E→费用→碳排"})
        _rep_rows.append({"类别":"可行性","参数":"四道闸门理由","数值":f"方案1:{tag_1}；方案2:{tag_2}；方案3:{tag_3}","来源":"独立判断","备注":"预算/工程/末端/热泵"})
        _rep_rows.append({"类别":"推荐","参数":"推荐方案","数值":str(best_scheme) if best_scheme else "无可行方案(建议提高预算/允许外墙改造)","来源":"程序推荐","备注":""})
        _rep_df = pd.DataFrame(_rep_rows)
        st.dataframe(_rep_df, use_container_width=True, hide_index=True)
        _rep_bytes = _rep_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button("📥导出完整计算报告CSV", _rep_bytes, file_name=f"{ht}_完整计算报告_V1.9.csv", mime="text/csv")
    tabE, tabC, tabN, tabS = st.tabs(["⚡能耗","💰经济","🌿环境","📈敏感性"])
    color_list = ["#6366f1","#f59e0b","#10b981"]
    layout_common = dict(template="plotly_white",hovermode="x unified",height=440,font=dict(size=13),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(99,102,241,0.04)")
    with tabE:
        st.markdown("**能耗维度：热负荷 → 年需热量 → 年耗电量 → 节能率**")
        fig1 = px.bar(result_df,x="改造方案",y="设计热负荷(kW)",color="改造方案",color_discrete_sequence=color_list,title=f"{ht}｜三套方案设计热负荷对比")
        fig1.update_layout(**layout_common)
        st.plotly_chart(fig1,use_container_width=True)
        fig2 = px.bar(result_df,x="改造方案",y="全年采暖需热量(kWh)",color="改造方案",color_discrete_sequence=color_list,title="全年采暖需热量(HDD法)")
        fig2.update_layout(**layout_common)
        st.plotly_chart(fig2,use_container_width=True)
        fig3 = px.bar(result_df,x="改造方案",y="分段插值算法年耗电量(kWh)",color="改造方案",color_discrete_sequence=color_list,title="【V1.7分段插值】热泵系统年耗电量对比")
        fig3.update_layout(**layout_common)
        st.plotly_chart(fig3,use_container_width=True)
        df_save = result_df[result_df["耗电量节能率(%)"]!="基准"].copy()
        fig5 = px.bar(df_save,x="改造方案",y="耗电量节能率(%)",color="改造方案",color_discrete_sequence=color_list[1:],title="耗电量节能率对比")
        fig5.update_layout(**layout_common)
        st.plotly_chart(fig5,use_container_width=True)
    with tabC:
        st.markdown("**经济维度：静态增量回收期（相对方案1基准）**")
        df_pay = result_df[result_df["静态增量投资回收期(年)"]!="基准"].copy()
        fig4 = px.bar(df_pay,x="改造方案",y="静态增量投资回收期(年)",color="改造方案",color_discrete_sequence=color_list[1:],title="静态增量投资回收期对比（相对方案1基准）")
        fig4.update_layout(**layout_common)
        st.plotly_chart(fig4,use_container_width=True)
        st.caption("回收期为『相对方案1的静态增量投资回收期』，非项目真实全生命周期回收期；未计除霜、循环水泵、部分负荷与辅助热源。")
    with tabN:
        st.markdown("**环境维度：年运行碳排放（运行阶段）**")
        fig6 = px.bar(result_df,x="改造方案",y="年运行CO₂排放(kgCO₂)",color="改造方案",color_discrete_sequence=color_list,title="年运行CO₂排放对比")
        fig6.update_layout(**layout_common)
        st.plotly_chart(fig6,use_container_width=True)
        st.caption("碳排放为运行阶段（电耗×电网排放因子），不包含生产与施工阶段隐含碳。")
    with tabS:
        st.markdown("**敏感性分析：围护造价与电价波动对回收期影响**")
        sen_df = calc_sensitivity(real_envelope, real_lowend, equip["elec_price"], save_elec_2,save_elec_3)
        st.dataframe(sen_df,use_container_width=True)
        fig_sen = px.bar(sen_df,x="场景",y=["方案2回收期","方案3回收期"],barmode="group",title="造价电价波动‑回收期敏感性（围护造价随工程量联动）")
        fig_sen.update_layout(**layout_common)
        st.plotly_chart(fig_sen,use_container_width=True)
        st.markdown("**多维度雷达综合评分**")
        s1,s2,s3 = get_radar_score(payback_2,payback_3,elec_save_rate_2,elec_save_rate_3,co2_reduce_rate_2,co2_reduce_rate_3,invest_2,invest_3)
        categories = ["初投资","回收期","节能率","减碳","施工难度"]
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(r=list(s1.values()),theta=categories,name="方案1仅换热泵",fill="toself"))
        fig_radar.add_trace(go.Scatterpolar(r=list(s2.values()),theta=categories,name="方案2围护+热泵",fill="toself"))
        fig_radar.add_trace(go.Scatterpolar(r=list(s3.values()),theta=categories,name="方案3围护+末端+低温热泵",fill="toself"))
        fig_radar.update_layout(polar=dict(radialaxis=dict(range=[0,10])),title="多维度雷达综合评分",**layout_common)
        st.plotly_chart(fig_radar,use_container_width=True)
    st.divider()
    text_p2 = payback_2 if payback_2 is not None else "——"
    text_p3 = payback_3 if payback_3 is not None else "——"
    st.subheader(f"✅{ht}｜最终方案推荐")
    if ht == "中间层住宅":
        boundary_text = """
> 【模型边界重要声明】本计算对象：**老旧住宅中间层；上下楼层均为采暖住户**
> 热工构件：外墙、外窗、外门、楼梯间非采暖隔墙、冷风渗透；**不计屋面、地面楼板热损失；不计算朝向、风力、高度附加耗热量。**
> 👉V1.7逻辑：热泵厂家样本一维插值+HDD多温度分段算全年能耗；末端公式迭代求解最低供水温度；围护造价=单位造价×实际工程量；热泵设备为固定总价。
> ⚠️**本模型不可直接用于顶层、底层、东西山墙边角户型。**
"""
    else:
        boundary_text = """
> 【模型边界重要声明】本计算对象：**老旧住宅顶层东西山墙边户**
> 热工构件：普通外墙、东西山墙、屋面、外窗、外门、楼梯间非采暖隔墙、冷风渗透；**不计底层地面楼板热损失；不计算朝向、风力、高度附加耗热量。**
> 👉V1.7逻辑：热泵厂家样本一维插值+HDD多温度分段算全年能耗；末端公式迭代求解最低供水温度；围护造价=单位造价×实际工程量；热泵设备为固定总价。
> ⚠️**本模型不可直接用于中间层、底层住户。**
"""
    st.info(f"💰预算 {budget:,}元｜{boundary_text}")
    budget_note_1 = f"初投资 {round(invest_1):,}元，{tag_1}"
    budget_note_2 = f"初投资 {round(invest_2):,}元，{tag_2}"
    budget_note_3 = f"初投资 {round(invest_3):,}元，{tag_3}"
    rec1_label = "⚠️唯一可行" if (not stat2["eligible"] and not stat3["eligible"]) else "❌不推荐"
    rec1_reason = "仅更换热泵，围护不保温；仅作为基准对照。"
    if stat2["eligible"]:
        rec2_label = "✅优先推荐" if best_scheme=="方案2" else "✅可推荐"
        rec2_reason = f"全部条件通过；增量回收期{text_p2}年；耗电节能{elec_save_rate_2}%；碳排放削减{co2_reduce_rate_2}%；围护构件同步保温改造。"
    else:
        rec2_label = "❌不推荐"
        rec2_reason = tag_2
    if stat3["eligible"]:
        rec3_label = "✅优先推荐" if best_scheme=="方案3" else "✅可推荐"
        rec3_reason = f"全部条件通过；增量回收期{text_p3}年；耗电节能{elec_save_rate_3}%；碳排放削减{co2_reduce_rate_3}%；围护+低温地暖+低温热泵，系统效率更高。"
    else:
        rec3_label = "❌不推荐"
        rec3_reason = tag_3
    if best_scheme:
        if budget_sufficient and stat2["eligible"] and stat3["eligible"]:
            overall = f">预算充足，方案2、3均可实施，可权衡经济导向/节能减碳导向。"
        else:
            overall = f">综上预算约束下，最优方案：**{best_scheme}**"
    else:
        overall = f">方案2、3校验不通过；建议提高预算，或仅实施方案1。"
    dual_rec=""
    if budget_sufficient and stat2["eligible"] and stat3["eligible"]:
        eco_pay = text_p2 if eco_scheme=="方案2" else text_p3
        eco_save = elec_save_rate_2 if eco_scheme=="方案2" else elec_save_rate_3
        eco_carbon = co2_reduce_rate_2 if eco_scheme=="方案2" else co2_reduce_rate_3
        eco_cost = round(year_cost_2,2) if eco_scheme=="方案2" else round(year_cost_3,2)
        dual_rec = f"""
**💡双维度权衡（预算充足）**
- 💰经济导向推荐：{best_scheme}（回收期最短）
- 🌿节能减碳导向推荐：{eco_scheme}，节能{eco_save}%，减碳{eco_carbon}%，年采暖电费{eco_cost}元，回收期{eco_pay}年
"""
    st.markdown(f"""{boundary_text}
1. **方案1｜仅更换热泵** —— {budget_note_1}
    - 分析：H={round(H1_kWK,4)}kW/K；设计热负荷{round(Qd1_kW,2)}kW；单位面积热负荷{q_load_per_area1} W/m²。
    - 结论：**{rec1_label}** —— {rec1_reason}
2. **方案2｜全套围护保温改造+常规热泵** —— {budget_note_2}
    - 分析：围护构件同步保温；热负荷削减{load_save_rate_2}%；耗电节能{elec_save_rate_2}%；年减碳 {co2_reduce_2}kgCO₂；回收期 {text_p2} 年。
    - 结论：**{rec2_label}** —— {rec2_reason}
3. **方案3｜全套围护保温+低温地暖末端+低温热泵** —— {budget_note_3}
    - 分析：全套围护保温+低温末端；热负荷削减{load_save_rate_3}%；耗电节能{elec_save_rate_3}%；年减碳 {co2_reduce_3}kgCO₂；回收期 {text_p3} 年。
    - 结论：**{rec3_label}** —— {rec3_reason}
{overall}
{dual_rec}
""")
# ======================页面4：手工校核验算页 ======================
    # ================= V1.8新增：18种自由组合批量计算模块（追加，不动原有代码） =================
    if st.session_state.get("calc_mode","typical") == "batch_18":
        st.divider()
        st.markdown("# 🧪【V1.8新增】18种自由组合批量计算｜3围护 ×3末端 ×2热泵")
        st.info("E0=不改造围护；E1/E2=围护改造；T0旧散热器；T1增强散热器；T2低温地暖；HP0常规热泵；HP1低温热泵。基准=E0-T0-HP0；增量回收期仅方案间对比，非工程真实回收期。")
        coef_envelope = st.session_state["coef_set"]["coef_envelope"]
        coef_pump = st.session_state["coef_set"]["coef_pump"]
        coef_terminal = st.session_state["coef_set"]["coef_terminal"]
        all_result_list = []
        for e_item in ENVELOPE_OPTIONS:
            for t_item in TERMINAL_OPTIONS:
                for hp_item in HEATPUMP_OPTIONS:
                    all_result_list.append(calc_one_combination(
                        ht, build, equip, coef_envelope, coef_pump, coef_terminal,
                        e_item["id"], t_item["id"], hp_item["id"], HDD_SEGMENTS))
        base = next(x for x in all_result_list if x["env_id"]=="E0" and x["term_id"]=="T0" and x["hp_id"]=="HP0")
        out_rows = []
        for item in all_result_list:
            delta_inv = item["total_invest"] - base["total_invest"]
            pb = payback_period_incremental(base["total_invest"], delta_inv,
                                            base["E_total_kwh"], item["E_total_kwh"], equip["elec_price"])
            elec_save_rate = round((base["E_total_kwh"]-item["E_total_kwh"])/base["E_total_kwh"]*100,2) if base["E_total_kwh"]>1e-3 else None
            out_rows.append({
                "围护":item["env_id"],"末端":item["term_id"],"热泵":item["hp_id"],
                "H(kW/K)":item["H_kWK"],"Qd(kW)":item["Qd_kW"],"q(W/m²)":item["q_load_per_area_Wm2"],
                "供水℃":item["tg_solve"],"末端校验":"OK" if item["term_ok"] else "NG",
                "E_hp(kWh)":item["E_hp_kwh"],"E_aux(kWh)":item["E_aux_kwh"],"aux_eq(h)":item["aux_equiv_hours"],
                "E_total(kWh)":item["E_total_kwh"],"节电率%":elec_save_rate,
                "CO₂(kg)":item["co2_run_kg"],
                "投资热泵":item["invest_pump"],"投资围护":item["invest_env"],"投资末端":item["invest_terminal"],
                "总投资(元)":item["total_invest"],"年电费(元)":item["year_cost"],"增量回收期(年)":pb
            })
        df_18 = pd.DataFrame(out_rows)
        st.dataframe(df_18, use_container_width=True, height=260)
        csv_18 = df_18.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button("📥下载18种自由组合结果CSV", csv_18,
                           file_name=f"{ht}_18种自由组合_V18.csv", mime="text/csv")
        st.info("💡注：18组合中，末端校验NG表示该末端在最高供水温度下无法覆盖热负荷；围护E0/E1/E2区分是否做保温改造。")

# ======================页面4：手工校核验算页 ======================
elif page_select == "4.手工校核验算页":
    ht = st.session_state["house_type"]
    st.markdown(f"""
<div class="light-tech-title">
    <h1>✍️手工校核验算页面｜户型：{ht}</h1>
</div>
""", unsafe_allow_html=True)
    if ht == "中间层住宅":
        st.info("边界：中间层，不计屋面、地面楼板；构件：外墙、外窗、外门、非采暖隔墙+冷风渗透；无附加耗热量")
    else:
        st.info("边界：顶层边户；计入屋面、东西山墙；不计底层地面楼板；构件：外墙、东西山墙、屋面、外窗、外门、非采暖隔墙+冷风渗透；无附加耗热量")
    st.info("软件自动带出计算结果，输入手算值对比误差。误差阈值：≤1%判定校验通过。")
    if "calc_mid" not in st.session_state:
        st.warning("⚠️请先访问页面3完成计算生成中间变量")
        st.stop()
    mid = st.session_state["calc_mid"]
    st.subheader("核心公式")
    st.markdown(r"""
$H_{total}=\sum H_{envelope} + H_{inf}\quad [kW/K]$
设计热负荷：$Q_{design}=H_{total}\cdot \Delta T$（无附加耗热量）
年采暖需热量：$Q_{year}=H_{total}\cdot HDD18 \cdot 24$
""")
    st.divider()
    col_h1, col_h2 = st.columns(2)
    with col_h1:
        st.number_input("软件 H1(kW/K)", value=mid["H1_kWK"], disabled=True)
        hand_H1 = st.number_input("✍️手算 H1(kW/K)", value=0.0)
        err_H1 = abs(mid["H1_kWK"] - hand_H1)
        if mid["H1_kWK"] != 0:
            rel_H1 = err_H1 / mid["H1_kWK"] * 100
        else:
            rel_H1 = 0.0
        st.metric("H1绝对误差", round(err_H1, 6))
        st.metric("H1相对误差%", round(rel_H1, 3))
        if rel_H1 <= 1.0:
            st.success("✅H1校验通过")
        else:
            st.error("❌H1误差>1%，核对构件热损失公式")
    with col_h2:
        st.number_input("软件 Qd1(kW)", value=mid["Qd1_kW"], disabled=True)
        hand_Qd1 = st.number_input("✍️手算 Qd1(kW)", value=0.0)
        err_Qd1 = abs(mid["Qd1_kW"] - hand_Qd1)
        if mid["Qd1_kW"] != 0:
            rel_Qd1 = err_Qd1 / mid["Qd1_kW"] * 100
        else:
            rel_Qd1 = 0.0
        st.metric("Qd1绝对误差", round(err_Qd1, 4))
        st.metric("Qd1相对误差%", round(rel_Qd1, 3))
        if rel_Qd1 <= 1.0:
            st.success("✅Qd1校验通过")
        else:
            st.error("❌Qd1误差>1%")
    st.divider()
    st.subheader("方案2 H2 / Qd2 手算校核")
    col_h3, col_h4 = st.columns(2)
    with col_h3:
        st.number_input("软件 H2(kW/K)", value=mid["H2_kWK"], disabled=True)
        hand_H2 = st.number_input("✍️手算 H2(kW/K)", value=0.0)
        err_H2 = abs(mid["H2_kWK"] - hand_H2)
        if mid["H2_kWK"] != 0:
            rel_H2 = err_H2 / mid["H2_kWK"] * 100
        else:
            rel_H2 = 0.0
        st.metric("H2绝对误差", round(err_H2,6))
        st.metric("H2相对误差%", round(rel_H2,3))
        if rel_H2 <= 1.0:
            st.success("✅H2校验通过")
        else:
            st.error("❌H2误差>1%，核对改造后K值输入")
    with col_h4:
        st.number_input("软件 Qd2(kW)", value=mid["Qd2_kW"], disabled=True)
        hand_Qd2 = st.number_input("✍️手算 Qd2(kW)", value=0.0)
        err_Qd2 = abs(mid["Qd2_kW"] - hand_Qd2)
        if mid["Qd2_kW"] !=0:
            rel_Qd2 = err_Qd2 / mid["Qd2_kW"] *100
        else:
            rel_Qd2 =0.0
        st.metric("Qd2绝对误差", round(err_Qd2,4))
        st.metric("Qd2相对误差%", round(rel_Qd2,3))
        if rel_Qd2 <=1.0:
            st.success("✅Qd2校验通过")
        else:
            st.error("❌Qd2误差>1%")
    st.divider()
    st.subheader("方案3 H3 / Qd3 手算校核（方案3围护与方案2相同，H3=H2）")
    col_h5, col_h6 = st.columns(2)
    with col_h5:
        st.number_input("软件 H3(kW/K)", value=mid["H3_kWK"], disabled=True)
        hand_H3 = st.number_input("✍️手算 H3(kW/K)", value=0.0)
        err_H3 = abs(mid["H3_kWK"] - hand_H3)
        if mid["H3_kWK"] != 0:
            rel_H3 = err_H3 / mid["H3_kWK"] *100
        else:
            rel_H3 =0.0
        st.metric("H3绝对误差", round(err_H3,6))
        st.metric("H3相对误差%", round(rel_H3,3))
        if rel_H3 <= 1.0:
            st.success("✅H3校验通过")
        else:
            st.error("❌H3误差>1%")
    with col_h6:
        st.number_input("软件 Qd3(kW)", value=mid["Qd3_kW"], disabled=True)
        hand_Qd3 = st.number_input("✍️手算 Qd3(kW)", value=0.0)
        err_Qd3 = abs(mid["Qd3_kW"] - hand_Qd3)
        if mid["Qd3_kW"] != 0:
            rel_Qd3 = err_Qd3 / mid["Qd3_kW"] *100
        else:
            rel_Qd3 = 0.0
        st.metric("Qd3绝对误差", round(err_Qd3,4))
        st.metric("Qd3相对误差%", round(rel_Qd3,3))
        if rel_Qd3 <= 1.0:
            st.success("✅Qd3校验通过")
        else:
            st.error("❌Qd3误差>1%")
    st.divider()
    st.subheader("🔬V1.7新增：HDD分段插值结果查看")
    st.info("💡提示：方案3只更换末端，围护结构不变，热损失系数H、设计热负荷Qd和方案2完全相等；只有SPF、耗电量、运行电费发生变化。")
    if "seg1" in mid:
        st.markdown("**方案1分段插值明细**")
        st.dataframe(pd.DataFrame(mid["seg1"]), use_container_width=True)
    if "seg2" in mid:
        st.markdown("**方案2分段插值明细**")
        st.dataframe(pd.DataFrame(mid["seg2"]), use_container_width=True)
    if "seg3" in mid:
        st.markdown("**方案3分段插值明细**")
        st.dataframe(pd.DataFrame(mid["seg3"]), use_container_width=True)

    # ================= V1.8新增：逐级误差校核（软件值自动带入，仅填手算值） =================
    st.divider()
    st.subheader("🧪【V1.8新增】逐级误差校核（软件值自动带入，只填手算值）")
    st.info("校核链：H → Q_design → Q_year → SPF/COP → E_HP → E_aux → 费用 → 碳排放。误差≤1%判『通过』，>1%判『未通过』。E_HP/E_aux/费用/碳排按V1.8含热泵容量约束的分段口径计算。")
    equip_chk = st.session_state["equip"]
    _spf_list = [mid["spf1"], mid["spf2"], mid["spf3"]]
    # 计算每方案 E_HP / E_aux（含容量约束）
    _aux_results = []
    for _seg, _sample, _tgfix, _rated in [
        (mid["seg1"], SAMPLE_HP_NORMAL, 55.0, equip_chk["Qhp_rated1"]),
        (mid["seg2"], SAMPLE_HP_NORMAL, 55.0, equip_chk["Qhp_rated2"]),
        (mid["seg3"], SAMPLE_HP_LOWTEMP, 45.0, equip_chk["Qhp_rated3"]),
    ]:
        _, _ehp, _eaux, _ah = calc_segment_hp_aux(_seg, _sample, _tgfix, _tgfix, _rated)
        _aux_results.append((round(_ehp,2), round(_eaux,2), _ah))

    _scheme_meta = [
        ("方案1：仅热泵(E0-T0-HP0)",
         {"H (kW/K)":round(mid["H1_kWK"],5),"Q_design (kW)":round(mid["Qd1_kW"],3),
          "Q_year (kWh)":round(mid["q_year1_kwh"],1),"SPF/COP":_spf_list[0],
          "E_HP (kWh)":_aux_results[0][0],"E_aux (kWh)":_aux_results[0][1],
          "费用(年电费,元)":round((_aux_results[0][0]+_aux_results[0][1])*equip_chk["elec_price"],2),
          "碳排放(kgCO₂)":round((_aux_results[0][0]+_aux_results[0][1])*equip_chk["grid_ef"],2)}),
        ("方案2：围护+热泵(E2-T0-HP0)",
         {"H (kW/K)":round(mid["H2_kWK"],5),"Q_design (kW)":round(mid["Qd2_kW"],3),
          "Q_year (kWh)":round(mid["q_year2_kwh"],1),"SPF/COP":_spf_list[1],
          "E_HP (kWh)":_aux_results[1][0],"E_aux (kWh)":_aux_results[1][1],
          "费用(年电费,元)":round((_aux_results[1][0]+_aux_results[1][1])*equip_chk["elec_price"],2),
          "碳排放(kgCO₂)":round((_aux_results[1][0]+_aux_results[1][1])*equip_chk["grid_ef"],2)}),
        ("方案3：围护+地暖+低温热泵(E2-T2-HP1)",
         {"H (kW/K)":round(mid["H3_kWK"],5),"Q_design (kW)":round(mid["Qd3_kW"],3),
          "Q_year (kWh)":round(mid["q_year3_kwh"],1),"SPF/COP":_spf_list[2],
          "E_HP (kWh)":_aux_results[2][0],"E_aux (kWh)":_aux_results[2][1],
          "费用(年电费,元)":round((_aux_results[2][0]+_aux_results[2][1])*equip_chk["elec_price"],2),
          "碳排放(kgCO₂)":round((_aux_results[2][0]+_aux_results[2][1])*equip_chk["grid_ef"],2)}),
    ]
    _unit_map = {"H (kW/K)":"kW/K","Q_design (kW)":"kW","Q_year (kWh)":"kWh","SPF/COP":"-",
                 "E_HP (kWh)":"kWh","E_aux (kWh)":"kWh","费用(年电费,元)":"元","碳排放(kgCO₂)":"kgCO₂"}
    # ---- 软件值逐级中间值总览 ----
    st.markdown("**① 软件值逐级中间值总览（自动带入，仅供对照手算）**")
    _overview_rows = []
    for _name, _soft in _scheme_meta:
        for _k, _v in _soft.items():
            _overview_rows.append({"方案":_name.split("：")[0],"参数":_k,"软件值":_v,"单位":_unit_map[_k]})
    st.dataframe(pd.DataFrame(_overview_rows), use_container_width=True, hide_index=True)
    # ---- 每方案逐项误差校核 ----
    st.markdown("**② 逐项误差校核（软件值已锁定，请在『手算值』栏填写手算结果）**")
    for _sidx, (_name, _soft) in enumerate(_scheme_meta):
        with st.expander(f"🔬 {_name} 逐级校核", expanded=(_sidx==0)):
            _hand_vals = {}
            for _k, _v in _soft.items():
                _hand_vals[_k] = st.number_input(
                    f"手算 {_k} ｜软件值 = {_v} {_unit_map[_k]}", value=0.0,
                    format="%.4f", key=f"chk_{_sidx}_{_k}")
            _res_rows = []
            _all_pass = True
            for _k, _v in _soft.items():
                _hv = _hand_vals[_k]
                _ae = abs(_v - _hv)
                _re = (_ae / abs(_v) * 100.0) if abs(_v) > 1e-9 else 0.0
                _ok = _re <= 1.0
                _all_pass = _all_pass and _ok
                _res_rows.append({"参数":_k,"软件值":_v,"手算值":_hv,
                                  "绝对误差":round(_ae,4),"相对误差%":round(_re,3),
                                  "结论":"✅通过" if _ok else "❌未通过"})
            st.dataframe(pd.DataFrame(_res_rows), use_container_width=True, hide_index=True)
            if _all_pass:
                st.success(f"✅ {_name}：全部 8 项误差 ≤1%，手算校核通过")
            else:
                st.error(f"❌ {_name}：存在误差 >1% 的项，请核对手算过程（逐级中间值见上方总览）")

    # ===== V1.9新增：供水温度(末端反算) 与 热泵设计工况可用制热量 校核 =====
    st.divider()
    st.markdown("**🔎【V1.9新增】供水温度(末端反算) 与 热泵设计工况可用制热量 校核**")
    st.info("供水温度由负荷与末端能力反算：Q_terminal=Q_rated×(ΔT_m/ΔT_m,rated)^m；热泵容量按设计工况(室外=郑州设计温度)插值，不直接用样本额定值。")
    _bd4 = st.session_state["build"]
    _eq4 = st.session_state["equip"]
    _rows4 = []
    for _i, (nm, _tgk, _hpid, _qdk) in enumerate([
        ("方案1", "tg1", "HP0", "Qd1_kW"),
        ("方案2", "tg2", "HP0", "Qd2_kW"),
        ("方案3", "tg3", "HP1", "Qd3_kW"),
    ]):
        _tgv = mid.get(_tgk, None)
        if _tgv is None:
            continue
        _copd, _qav, _warns4 = hp_available_at_design(_bd4, _eq4, _hpid, _tgv)
        _qd = mid[_qdk]
        _ok = _qav >= _qd
        _rows4.append({"方案":nm, "反算供水温度tg(℃)":_tgv, "设计工况COP":_copd,
                       "设计工况Q_HP可用(kW)":_qav, "设计负荷(kW)":round(_qd,2),
                       "容量满足":"✅" if _ok else "❌",
                       "说明":"热泵可用制热量≥设计负荷，可行" if _ok else "需增容或配置辅助电加热"})
    st.dataframe(pd.DataFrame(_rows4), use_container_width=True, hide_index=True)
    st.caption("当末端/热泵能力不满足时，应给出『提高水温/增加散热器面积/更换末端』及『增容或辅助热源』建议，避免直接把额定值当可用值。")
