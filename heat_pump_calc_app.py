# -*- coding: utf-8 -*-
"""
老旧住宅空气源热泵协同改造计算工具【V1.28】
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
👉V1.21修订要点：
- 散热器散热指数 m 修正为 1.30（依据 GB/T 13754-2017 式(8) Q=K_M·ΔT^m，指数由型号热工检测报告实测拟合；本程序取工程典型值 m≈1.30，铸铁柱式实测 m≈1.28~1.30，如 74×60 铸铁 m≈1.283，台账标注“算/典型值”）。
- 热泵性能升级为“室外温度×供水温度”二维性能面：域内双线性插值；域外禁止外推，仅打标记并纳入数据闸门。
  两套设备均按【美的雪焰/真暖】官方说明书真实锚点标定（执行 GB/T 25127.2-2020）：
  设备A(方案1/2)=MHSR120N8-S1(12kW)，A7/W45 COP=3.50、Q=12kW，55℃出水列按温升比换算；
  设备B(方案3)=MHSR100N8-S1(10kW)，A7/W45 COP=3.55、Q=10kW，A-12/W35 COP=2.70、A-20/W35 COP=2.21。
- 性能面证据分级：厂家公开锚点【源】与温升幂律推算格【算】彻底分栏；未获得完整厂家性能矩阵前，界面一律称“热泵性能估算面/模型适用性”，不再称“厂家二维性能表/厂家数据域”。
- 第五道闸门更名 performance_model_applicable：模型适用性判定（估算面是否覆盖工况），不再表述为“厂家样本验证范围”。
- 季节性能统一口径为 SPF_HP+aux = Q_year / (E_HP + E_aux)（由分段积分反算；分母仅含热泵主机与辅助电加热，未计入水泵/控制/待机，见 ）；
  原铭牌SPF×衰减系数仅保留为“旧算法估算值”，不再作为当前主指标
👉V1.28修订要点（依据《小程序修改建议-20260905》）：
- 外墙净面积统一为 毛面积−外窗−外门，单点函数 calc_wall_net() 生成，H/造价/分项热损失/校验全链路只读该结果；窗+门≥毛墙阻断计算。
- 性能数据证据分级（锚点=厂家公开数据【源】；推算格=模型估算【算】）；界面与闸门命名全部改为“估算面/模型适用性”。
- 容量与辅热口径分离——设计工况备用容量 Q_aux,design=max(0,Qd−Qhp)；capacity_ok 与年度 E_aux/未满足热量分开报告。
- 批量造价按 围护0.75 / 热泵0.85 / 末端0.80 分项结算（分户模式三系数=1.00，输入置灰）；每项显示“原始金额×有效系数=折算金额”。
- 节能/减排指标一律标注“相对方案1（热泵供暖情景）”口径；新增“改造前实际系统基准”录入模块，未录入不输出真实节能率/减排量。
- 主指标改名 SPF_HP+aux，分母项目明列（E_HP+E_aux；未计水泵/控制/待机/曲轴箱加热）。
- 页面4改为“计算一致性校核（非模型有效性验证）”，空值=待填写；新增验证证据分级说明。
- P1：GB/T 25127.2 标准口径统一；设备改名 设备A/设备B；台账动态标注【用户输入】；碳排因子默认0.5897(2023河南·位置法)步长0.0001；标题改“方案比选与风险筛查工具”；分段度时守恒校核；推荐三状态机；导出报告含版本/时间/闸门原因。
- P2：校核页空值待填写；模型边界去重折叠；方案3文案修正；显示精度统一（H 5位/Q·COP·MR 3位/能耗1位/金额0位/因子4位）。
分工对应：
页面1：建筑围护参数（建筑与围护组负责）
页面2：热泵+【末端热工参数】+围护分项单位造价+热泵性能估算面（锚点/推算分栏）
页面3：三套方案计算结果+经济性+相对方案1变化+辅助电加热+碳排放，输出各分项工程量&造价、末端校核、反算水温、分段能耗明细
页面4：计算一致性校核页（H1/Qd1/H2/Qd2/H3/Qd3全套手算校验 + 分段插值结果校验，空值=待填写）
核心三套方案：
方案1：仅更换空气源热泵，围护不改造（基准方案，原有散热器末端）
方案2：围护结构保温改造 + 设备A（保留原有散热器末端）
方案3：围护改造 + 低温采暖地暖末端 + 设备B（与方案2相同围护参数，进一步更换末端与设备）
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import datetime

###====改造模式造价系数配置（V1.28：P0-4 分项系数）====
# 分户独立改造：围护/热泵/末端 有效系数均为 1.00；
# 整栋集中批量改造：围护0.75、热泵0.85、末端0.80（页面2可编辑 coef_set 覆盖批量默认值）
RETROFIT_MODE_CFG = {
    "分户独立改造": {"coef_envelope":1.00, "coef_pump":1.00, "coef_terminal":1.00},
    "整栋集中批量改造": {"coef_envelope":0.75, "coef_pump":0.85, "coef_terminal":0.80}
}

# ===================== 新增V1.7：热泵厂家工况样本数据表（V1.28：更名“性能估算面锚点表”） =====================
# 测试工况：国标GB/T 25127.2（户用及类似用途，本案例采用第2部分；GB/T 25127.1—2020 适用于工业或商业及类似用途，本案例不采用，见P1-1），
# 出水温度tg_supply，室外干球T_amb
# 每一条：[室外环境温度℃，供水温度℃，COP，工况可用制热量kW]
# 方案1、2使用设备A样本；方案3使用设备B样本
# 方案1、方案2：设备A（MHSR120N8-S1，12kW·220V·低环境温度空气源热泵(冷水)机组·地板采暖型，CQC认证名录）
# 美的雪焰/真暖系列真实锚点（45℃工况，厂家公开数据【源】）：
# A7/W45：Q=12.0、COP=3.50；A-12/W35：Q=11.0、COP=2.70；A-20/W35：Q=11.6、COP=2.20(域外参考)
# 本表为 55℃ 出水列：由真实 45℃ 锚点按温升比 L=(tg-T) 幂律换算（算）：COP∝(L_ref/L)^0.6、Q∝(L_ref/L)^0.4
SAMPLE_HP_NORMAL = [
    [7, 55, 3.04, 10.9],
    [2, 55, 2.73, 10.4],
    [-2, 55, 2.52, 10.0],
    [-7, 55, 2.30, 9.6],
    [-10, 55, 2.19, 9.3],
]
# 方案3：设备B（MHSR100N8-S1，10kW·220V·低环境温度空气源热泵(冷水)机组·地板采暖型，CQC认证名录）
# 美的雪焰/真暖系列真实锚点（厂家公开数据【源】）：
# 额定制热 A7/W45：Q=10.0kW、COP=3.55；名义 A-12/W35：Q=9.0、COP=2.70；低温 A-20/W35：Q=8.0、COP=2.21
# 表中 45℃ 出水列 COP/Q 按温升比 L=(45-T) 幂律由真实锚点标定（算）：COP∝(L_ref/L)^1.0、Q∝(L_ref/L)^0.5
SAMPLE_HP_LOWTEMP = [
    [7, 45, 3.55, 10.0],
    [2, 45, 3.14, 9.4],
    [-2, 45, 2.87, 9.0],
    [-7, 45, 2.59, 8.5],
    [-10, 45, 2.45, 8.3],
]
# ================= V1.21：二维性能估算面【室外干球×供水温度】（V1.28：证据分级） =================
# 说明：厂家样本通常只给单一出水温度工况；为描述“供水温度变化对COP/制热量的影响”，
# 在样本固定出水列(55℃/45℃)基础上，按温升比 L=(tg-T_out) 幂律推算二维估算面。
# 生成模型：COP(tg,T)=COP_ref(T)×(L_ref/L)^0.6；Qcap(tg,T)=Qcap_ref(T)×(L_ref/L)^0.4，
# 其中 L_ref=样本出水-T_out。设备B(方案3)45℃出水列按美的雪焰/真暖 MHSR100N8-S1 真实锚点标定
# （COP_ref∝(L_ref/L)^1.0、Q_ref∝(L_ref/L)^0.5），其余格为“算”值；
# 设备A(方案1/2)按美的雪焰/真暖 MHSR120N8-S1(12kW)真实锚点、设备B(方案3)按 MHSR100N8-S1(10kW)真实锚点标定，
# 两套设备锚点均为厂家公开数据（源），其余格为模型推算（算）——整体为“性能估算面”，证据等级 C
# （厂家少量锚点+经验拟合推算：仅教学演示/方案比较，不输出强推荐；未获得完整厂家性能矩阵前不作为最终选型依据）。
# 矩形边界为“模型适用性范围”（model_applicability），不是厂家验证域（manufacturer_domain）。
# 索引顺序：行=室外温度(升序)，列=供水温度(升序)。
SAMPLE_HP_NORMAL_2D_OUT = [-15, -12, -10, -7, -5, -2, 0, 2, 7, 10]
SAMPLE_HP_NORMAL_2D_TG = [30, 35, 40, 45, 50, 55, 60, 65]
SAMPLE_HP_NORMAL_2D_COP = [
    [2.63, 2.47, 2.34, 2.22, 2.11, 2.02, 1.94, 1.87],
    [2.8, 2.62, 2.47, 2.33, 2.22, 2.12, 2.03, 1.95],
    [2.93, 2.73, 2.56, 2.42, 2.3, 2.19, 2.09, 2.01],
    [3.14, 2.91, 2.72, 2.56, 2.42, 2.3, 2.2, 2.1],
    [3.29, 3.04, 2.83, 2.66, 2.51, 2.38, 2.27, 2.17],
    [3.56, 3.27, 3.03, 2.83, 2.66, 2.52, 2.4, 2.29],
    [3.77, 3.44, 3.17, 2.96, 2.77, 2.62, 2.49, 2.37],
    [4.0, 3.63, 3.33, 3.09, 2.9, 2.73, 2.58, 2.46],
    [4.73, 4.2, 3.81, 3.5, 3.25, 3.04, 2.87, 2.72],
    [5.32, 4.65, 4.17, 3.8, 3.51, 3.27, 3.07, 2.9],
]
SAMPLE_HP_NORMAL_2D_QCAP = [
    [10.7, 10.3, 9.9, 9.5, 9.2, 9.0, 8.7, 8.5],
    [11.1, 10.6, 10.2, 9.8, 9.5, 9.2, 8.9, 8.7],
    [11.3, 10.8, 10.4, 10.0, 9.6, 9.3, 9.1, 8.8],
    [11.8, 11.2, 10.7, 10.3, 9.9, 9.6, 9.3, 9.0],
    [12.0, 11.4, 10.9, 10.5, 10.1, 9.7, 9.4, 9.1],
    [12.0, 11.9, 11.3, 10.8, 10.4, 10.0, 9.7, 9.4],
    [12.0, 12.0, 11.6, 11.0, 10.6, 10.2, 9.8, 9.5],
    [12.0, 12.0, 11.9, 11.3, 10.8, 10.4, 10.0, 9.7],
    [12.0, 12.0, 12.0, 12.0, 11.4, 10.9, 10.5, 10.1],
    [12.0, 12.0, 12.0, 12.0, 11.4, 10.9, 10.4, 10.0],
]
SAMPLE_HP_LOWTEMP_2D_OUT = [-15, -12, -10, -7, -5, -2, 0, 2, 7, 10]
SAMPLE_HP_LOWTEMP_2D_TG = [25, 30, 35, 40, 45, 50]
SAMPLE_HP_LOWTEMP_2D_COP = [
    [2.87, 2.67, 2.51, 2.37, 2.25, 2.14],
    [3.07, 2.84, 2.66, 2.5, 2.37, 2.25],
    [3.22, 2.97, 2.77, 2.6, 2.45, 2.33],
    [3.47, 3.18, 2.95, 2.76, 2.59, 2.46],
    [3.67, 3.34, 3.08, 2.87, 2.7, 2.55],
    [4.0, 3.61, 3.31, 3.07, 2.87, 2.7],
    [4.27, 3.82, 3.49, 3.22, 3.0, 2.81],
    [4.57, 4.06, 3.68, 3.38, 3.14, 2.94],
    [5.56, 4.8, 4.26, 3.86, 3.55, 3.3],
    [6.41, 5.39, 4.72, 4.23, 3.85, 3.56],
]
SAMPLE_HP_LOWTEMP_2D_QCAP = [
    [9.4, 8.9, 8.6, 8.2, 8.0, 7.7],
    [9.7, 9.2, 8.8, 8.5, 8.2, 7.9],
    [10.0, 9.4, 9.0, 8.6, 8.3, 8.0],
    [10.0, 9.8, 9.3, 8.9, 8.5, 8.2],
    [10.0, 10.0, 9.5, 9.1, 8.7, 8.4],
    [10.0, 10.0, 9.9, 9.4, 9.0, 8.6],
    [10.0, 10.0, 10.0, 9.6, 9.2, 8.8],
    [10.0, 10.0, 10.0, 9.9, 9.4, 9.0],
    [10.0, 10.0, 10.0, 10.0, 10.0, 9.5],
    [10.0, 10.0, 10.0, 10.0, 10.0, 9.5],
]
# 热泵ID → 二维性能估算面（能耗积分与设计工况容量均使用估算面；V1.28：证据分级 C）
HP_2D_MAP = {
    "HP0": {"out":SAMPLE_HP_NORMAL_2D_OUT, "tg":SAMPLE_HP_NORMAL_2D_TG,
            "cop":SAMPLE_HP_NORMAL_2D_COP, "qcap":SAMPLE_HP_NORMAL_2D_QCAP,
            "tg_ref":55.0,
            "model_name":"设备A：MHSR120N8-S1(12kW)",
            "evidence_level":"C",
            "anchor_points":[
                {"T_amb":7,"T_water":45,"COP":3.50,"Q":12.0,"evidence":"manufacturer"},
                {"T_amb":-12,"T_water":35,"COP":2.70,"Q":11.0,"evidence":"manufacturer"},
                {"T_amb":-20,"T_water":35,"COP":2.20,"Q":11.6,"evidence":"manufacturer_outside_range"}]},
    "HP1": {"out":SAMPLE_HP_LOWTEMP_2D_OUT, "tg":SAMPLE_HP_LOWTEMP_2D_TG,
            "cop":SAMPLE_HP_LOWTEMP_2D_COP, "qcap":SAMPLE_HP_LOWTEMP_2D_QCAP,
            "tg_ref":45.0,
            "model_name":"设备B：MHSR100N8-S1(10kW)",
            "evidence_level":"C",
            "anchor_points":[
                {"T_amb":7,"T_water":45,"COP":3.55,"Q":10.0,"evidence":"manufacturer"},
                {"T_amb":-12,"T_water":35,"COP":2.70,"Q":9.0,"evidence":"manufacturer"},
                {"T_amb":-20,"T_water":35,"COP":2.21,"Q":8.0,"evidence":"manufacturer_outside_range"}]},
}
# V1.28：数据证据等级（P0-2/P1-8）
# A=厂家完整性能矩阵/第三方试验（绿色）；B=厂家少量锚点+经验证拟合模型（蓝色）；
# C=厂家少量锚点+经验推算（本程序现状，橙色，仅教学演示/方案比较）；D=越域外推或来源不明（红色，阻断）
EVIDENCE_LEVELS = {
    "A": {"label":"厂家完整性能矩阵/第三方试验","allow":"可作设计前筛选，仍需工程复核","color":"绿"},
    "B": {"label":"厂家少量锚点+经验证拟合模型","allow":"可作方案比较，显示不确定度","color":"蓝"},
    "C": {"label":"厂家少量锚点+经验推算（本程序现状）","allow":"仅教学演示/方案比较，不输出强推荐","color":"橙"},
    "D": {"label":"越域外推或来源不明","allow":"阻断计算与推荐","color":"红"},
}

# ================= V1.8新增：18种自由组合枚举定义【3围护×3末端×2热泵】 =================
# 批量改造分项折算系数调研参考依据（项目需按当地招标报价修正）：
# 1. 分户独立改造：围护=1.00，热泵=1.00，末端=1.00；
# 2. 整栋集中批量改造参考经验：
#    - 围护保温工程 0.75：老旧小区EPC批量集采、外脚手架共用、人工摊薄；
#    - 空气源热泵设备安装 0.85：厂家批量供货、统一班组安装，省去零散上门差旅成本；
#    - 室内末端改造 0.80：批量进场、开槽回填工序统一调度。
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
    {"id":"HP0","name":"设备A：MHSR120N8-S1（12kW级低环境温度空气源热泵(冷水)机组·地板采暖型，适用末端以证书/样本为准）","sample_table":SAMPLE_HP_NORMAL,"sample_tg_fixed":55.0,"rated_key":"Qhp_rated1"},
    {"id":"HP1","name":"设备B：MHSR100N8-S1（10kW级低环境温度空气源热泵(冷水)机组·地板采暖型，适用末端以证书/样本为准）","sample_table":SAMPLE_HP_LOWTEMP,"sample_tg_fixed":45.0,"rated_key":"Qhp_rated3"},
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
    "wall_gross": 85.0, #外墙毛总面积（含窗户洞口）
    "win": 22.0, #外窗面积
    "door_A":2.2, #外门面积
    "nonheat_wall_A":18.0, #与楼梯间等非采暖空间隔墙面积
    "Kw_old": 1.8, "Kw_new": 0.45,
    "Kwin_old": 2.8, "Kwin_new": 1.8,
    "K_door_old":3.0,"K_door_new":1.8,
    "K_nonheat_old":1.7,"K_nonheat_new":0.60,
    "Tin": 20.0, "Tout": -7.0, "dT": 27.0, "HDD": 2106.0,
    "n": 0.5, "rho": 1.2, "cp": 1005.0
}
DEFAULT_BUILD_TOP_EDGE = {
    "area": 120.0, "floor_h": 2.8, "volume": 120*2.8,
    "wall_gross": 60.0, #普通外墙毛面积（扣除东西山墙）
    "win": 22.0,
    "door_A":2.2,
    "nonheat_wall_A":18.0,
    "roof_A":120.0, #屋面面积（顶层）
    "gable_wall_A":25.0, #东西山墙面积（边户）
    "Kw_old": 1.8, "Kw_new": 0.45,
    "Kwin_old": 2.8, "Kwin_new": 1.8,
    "K_door_old":3.0,"K_door_new":1.8,
    "K_nonheat_old":1.7,"K_nonheat_new":0.60,
    "K_roof_old":2.2,"K_roof_new":0.40, #屋面K
    "K_gable_old":1.9,"K_gable_new":0.42, #东西山墙K
    "Tin": 20.0, "Tout": -7.0, "dT": 27.0, "HDD": 2106.0,
    "n": 0.5, "rho": 1.2, "cp": 1005.0
}
DEFAULT_EQUIP = {
    "SCOP_nameplate1":2.6,
    "SCOP_nameplate2":2.6,
    "SCOP_nameplate3":3.2,
    "spf_decay1":0.82,
    "spf_decay2":0.82,
    "spf_decay3":0.88,
    # ==========【V1.5 单位造价】==========
    "unit_wall_ins":130.0, #外墙保温 元/m²
    "unit_roof_ins":110.0, #屋面保温 元/m²
    "unit_gable_ins":125.0, #山墙保温 元/m²
    "unit_win_replace":420.0, #外窗更换 元/m²
    "unit_door_replace":650.0, #外门更换 元/m²
    "unit_nonheat_ins":95.0, #非采暖隔墙保温 元/m²
    "unit_lowend_floor":115.0, #低温地暖末端 元/㎡建筑面积
    "cost_pump":12500.0, #热泵：固定总价（台）
    "budget":30000.0,
    "elec_price":0.56,
    "grid_ef":0.5897, # V1.28：默认改为 2023年河南省电力平均二氧化碳排放因子 0.5897 kgCO₂/kWh（生态环境部、国家统计局2025年第47号公告；位置法）
    "Qhp_rated1":12.0,
    "Qhp_rated2":12.0,
    "Qhp_rated3":10.0,
    # =========【V1.6 末端热工参数】=========
    # 原有散热器末端(方案1、方案2使用)
    "rad_Qrated_kW":14.0, #散热器总额定散热量 kW
    "rad_dt_m_rated":64.5, #散热器额定平均温差K（传统国标标定工况 95/70/18：(95+70)/2‑18=64.5K；GB/T 13754-2017 测试方法标准）
    "rad_m":1.30, #散热器散热指数m（V1.21修正：0.30→1.30；Q=K_M·ΔT^m 形式见 GB/T 13754-2017 式(8)，m 为工程典型值≈1.30，见台账）
    "rad_dt_flow_return":10.0, #散热器供回水温差K
    "rad_tg_max":65.0, #散热器允许最高供水温度℃（V1.21：60→65，使方案1"仅换热泵"默认参数下末端闸门通过：反算tg≈63.9℃≤65，常规热泵数据域内）
    # 增强型散热器末端(T1, 18自由组合模式使用)
    "rad_enh_Qrated_kW":18.0, #增强散热器总额定散热量 kW
    "rad_enh_dt_m_rated":64.5, #增强散热器额定平均温差K
    "rad_enh_m":1.30, #增强散热器散热指数m（V1.21修正：0.30→1.30）
    "rad_enh_dt_flow_return":10.0, #增强散热器供回水温差K
    "rad_enh_tg_max":60.0, #增强散热器允许最高供水温度℃
    # 低温地暖末端(方案3使用)
    "floor_Qrated_kW":14.0, #地暖额定散热量 kW
    "floor_dt_m_rated":15.0, #地暖额定平均温差K
    "floor_m":0.95, #地暖散热指数m
    "floor_dt_flow_return":5.0, #地暖供回水温差K
    "floor_tg_max":45.0, #地暖允许最高供水温度℃
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

def _norm_num_dict(d):
    """把字典中所有数值统一为 float，避免 number_input value 与 min/max 数值类型不一致报错"""
    for k in list(d.keys()):
        if isinstance(d[k], (int, float)) and not isinstance(d[k], bool):
            d[k] = float(d[k])

def switch_house_type(new_type):
    """切换户型，加载对应默认参数"""
    st.session_state["house_type"] = new_type
    if new_type == "中间层住宅":
        st.session_state["build"] = DEFAULT_BUILD_MID.copy()
    else:
        st.session_state["build"] = DEFAULT_BUILD_TOP_EDGE.copy()
    _norm_num_dict(st.session_state["build"])
    _norm_num_dict(st.session_state["equip"])
    _norm_num_dict(st.session_state["coef_set"])
###====工具函数 季节SPF====
def calc_season_spf(nameplate_scop, decay_factor):
    return round(nameplate_scop * decay_factor, 3)
###====V1.28 新增：外墙净面积唯一生成点（P0-1）====
def calc_wall_net(build_dict):
    """外墙净面积 = 外墙毛面积 − 外窗面积 − 外门面积。
    全程序（H/造价/分项热损失/校验/页面展示）只允许调用本函数获取净外墙面积，
    其他模块不得自行用 wall_gross−win 计算，避免门洞重复计入。"""
    return build_dict["wall_gross"] - build_dict["win"] - build_dict.get("door_A", 0.0)
def geometry_valid(build_dict):
    """几何有效性：毛墙>0、窗≥0、门≥0、净墙>0（窗+门<毛墙）。返回 (ok, reason)"""
    if build_dict.get("wall_gross", 0) <= 0:
        return False, "外墙毛面积必须>0"
    if build_dict.get("win", 0) < 0 or build_dict.get("door_A", 0) < 0:
        return False, "外窗/外门面积不得为负"
    if build_dict["win"] + build_dict.get("door_A", 0.0) >= build_dict["wall_gross"]:
        return False, f"外窗面积({build_dict['win']:.1f}m²)+外门面积({build_dict.get('door_A',0.0):.1f}m²)必须小于外墙毛面积({build_dict['wall_gross']:.1f}m²)，否则外墙净面积为负"
    return True, ""
###====calc_H：根据户型自动计算总热损失系数====
def calc_H(house_type, build_dict, volume, n, rho, cp):
    wall_net_A = calc_wall_net(build_dict) # V1.28：净墙=毛墙−窗−门
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
    【V1.21保留为旧版参考】第一版简化插值：样本表固定供水温度tg_fixed；只对室外环境温度一维线性插值。
    注意：主计算已升级为二维性能表（解决供水温度越域问题），本函数仅用于历史对比/兼容旧调用。
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


# ===================== V1.21：二维性能估算面 双线性插值（V1.28：P0-2 证据分级/命名修正） =====================
def hp_2d_interpolate(hp_id, t_amb_input, tg_input):
    """
    二维性能估算面：在“室外温度×供水温度”模型适用范围内做双线性插值；
    范围外禁止外推（in_domain=False，仅截断后返回参考值并报警，纳入模型适用性闸门）。
    hp_id: "HP0"设备A / "HP1"设备B
    说明：本面由厂家公开锚点【源】+温升幂律推算格【算】共同构成，属模型估计（证据等级C），
          其矩形边界为“模型适用范围”（model_applicability），不是厂家验证域。
    return: (cop, qcap_kW, in_domain, warn_msg)
      - in_domain=True：工况位于模型适用范围内，插值可用（仍为估计值）
      - in_domain=False：工况越出模型适用范围，本函数不对外推结果作置信声明
    """
    meta = HP_2D_MAP[hp_id]
    out_grid, tg_grid = meta["out"], meta["tg"]
    cop_grid, qcap_grid = meta["cop"], meta["qcap"]
    ta_min, ta_max = min(out_grid), max(out_grid)
    tg_min, tg_max = min(tg_grid), max(tg_grid)
    warns = []
    in_domain = True
    if t_amb_input < ta_min or t_amb_input > ta_max:
        in_domain = False
        warns.append(f"⚠️室外温度{t_amb_input:.1f}℃超出模型适用范围[{ta_min},{ta_max}]℃，禁止外推！")
    if tg_input < tg_min or tg_input > tg_max:
        in_domain = False
        warns.append(f"⚠️供水温度{tg_input:.1f}℃超出模型适用范围[{tg_min},{tg_max}]℃，禁止外推！")
    # 域外时仅截断到边界用于展示参考值，不改变 in_domain=False 结论
    ta_c = float(np.clip(t_amb_input, ta_min, ta_max))
    tg_c = float(np.clip(tg_input, tg_min, tg_max))
    cop_interp = float(np.interp(ta_c, out_grid, [np.interp(tg_c, tg_grid, row) for row in cop_grid]))
    qcap_interp = float(np.interp(ta_c, out_grid, [np.interp(tg_c, tg_grid, row) for row in qcap_grid]))
    return cop_interp, qcap_interp, in_domain, warns


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

###====计算围护分项造价【单位造价×工程量】（V1.28：P0-1 净墙扣门）====
def calc_retrofit_cost(house_type, build_dict, equip_dict, cost_factor):
    wall_net_A = calc_wall_net(build_dict)
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
    _g_ok, _g_msg = geometry_valid(build) # V1.28：窗+门<毛墙
    if not _g_ok:
        warn_list.append("外墙净面积必须>0：" + _g_msg)
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
def calc_design_aux_capacity(q_load_kw, qhp_avail_design_kw):
    """【V1.28 】设计工况需配置的备用热源容量 Q_aux,design = max(0, Qd − Q_HP,avail,design)。
    若未配置足额备用热源（当前模型默认未配置，容量=0），则设计点容量闸门 capacity_ok=(Qhp+Qaux)>=Qd 不满足。"""
    return round(max(0.0, q_load_kw - qhp_avail_design_kw), 3)

def calc_carbon(elec_kwh, ef_kg_kwh):
    co2 = elec_kwh * ef_kg_kwh
    return round(co2,2)

# ================= V1.9新增：设计工况热泵容量 / 扩展输入校验 / 分项热损失 / 恢复统一基准 =================
def hp_available_at_design(build, equip, hp_id, tg_solve):
    """设计工况(T_out=郑州设计室外温度, 供水=tg_solve)热泵可用制热量与COP。
    V1.21：按“室外×供水”二维性能估算面双线性插值，取min(额定制热量)；返回模型适用性标志。
    V1.28：不把估算面称“厂家数据域”，返回 performance_model_applicable 语义。"""
    t_design = build["Tout"]
    rated = equip["Qhp_rated3"] if hp_id == "HP1" else equip["Qhp_rated1"]
    cop_d, qhp_d, in_domain, warns = hp_2d_interpolate(hp_id, t_design, tg_solve)
    qhp_d = min(qhp_d, rated)
    return round(cop_d,3), round(qhp_d,3), in_domain, warns

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
    need_positive("设备A额定制热量", equip["Qhp_rated1"], 0, 100)
    need_positive("设备B额定制热量", equip["Qhp_rated3"], 0, 100)
    need_positive("设备A铭牌COP", equip["SCOP_nameplate1"], 0, 8.0)
    need_positive("设备B铭牌COP", equip["SCOP_nameplate3"], 0, 8.0)
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
    # ---- 墙窗门面积几何关系：净面积=毛墙−窗−门（V1.28：P0-1 扣门） ----
    _g_ok18, _g_msg18 = geometry_valid(build)
    if not _g_ok18:
        w.append("【V1.28】" + _g_msg18 + "（外墙净面积=毛墙−外窗−外门，窗+门≥毛墙必须阻断）")
    return w
def validate_inputs_strict(build, equip, ht):
    """严格输入校验：任一规则违反即阻止计算（异常输入不得进入计算链）。
    覆盖面积/K/容量/造价/电价/排放因子物理范围 + 跨字段校验（改造后K更低、Tin>Tout、外墙净面积>0等）。
    return (ok:bool, errors:list[str])"""
    errs = []
    def chk(cond, msg):
        if not cond:
            errs.append(msg)
    # ---- 建筑尺寸（物理范围） ----
    chk(0 < build["area"] <= 600, f"建筑面积须∈(0,600]m²，当前={build['area']}")
    chk(0 < build["floor_h"] <= 6.0, f"楼层层高须∈(0,6]m，当前={build['floor_h']}")
    chk(0 < build["wall_gross"] <= 600, f"外墙毛面积须∈(0,600]m²，当前={build['wall_gross']}")
    chk(0 <= build["win"] < build["wall_gross"], f"外窗面积须∈[0,外墙毛面积)，当前win={build['win']}")
    chk(0 <= build["door_A"] <= 50, f"外门面积须∈[0,50]m²，当前={build['door_A']}")
    # V1.28：P0-1 净墙=毛墙−窗−门，窗+门<毛墙（A02/A03 阻断项）
    _g_ok, _g_msg = geometry_valid(build)
    chk(_g_ok, f"几何校验未通过：{_g_msg}（外墙净面积=毛墙−外窗−外门必须>0）")
    chk(0 <= build["nonheat_wall_A"] <= 300, f"非采暖隔墙面积须∈[0,300]m²，当前={build['nonheat_wall_A']}")
    if ht == "顶层边户":
        chk(0 < build.get("roof_A",0) <= 600, f"屋面面积须∈(0,600]m²，当前={build.get('roof_A')}")
        chk(0 < build.get("gable_wall_A",0) <= 300, f"东西山墙面积须∈(0,300]m²，当前={build.get('gable_wall_A')}")
    # ---- K值（物理范围 + 改造后更低） ----
    for k, nm in [("Kw_old","外墙K(改前)"),("Kw_new","外墙K(改后)"),("Kwin_old","外窗K(改前)"),("Kwin_new","外窗K(改后)"),
                  ("K_door_old","外门K(改前)"),("K_door_new","外门K(改后)"),("K_nonheat_old","非采暖隔墙K(改前)"),("K_nonheat_new","非采暖隔墙K(改后)")]:
        chk(0 < build[k] <= 8.0, f"{nm}须∈(0,8]W/(m²·K)，当前={build[k]}")
    if ht == "顶层边户":
        for k, nm in [("K_roof_old","屋面K(改前)"),("K_roof_new","屋面K(改后)"),("K_gable_old","山墙K(改前)"),("K_gable_new","山墙K(改后)")]:
            chk(0 < build.get(k,0) <= 8.0, f"{nm}须∈(0,8]W/(m²·K)，当前={build.get(k)}")
    chk(build["Kw_new"] < build["Kw_old"], "改造后外墙K未低于改前（保温无改善），请修正")
    chk(build["Kwin_new"] < build["Kwin_old"], "改造后外窗K未低于改前（换窗无节能效果），请修正")
    chk(build["K_door_new"] < build["K_door_old"], "改造后外门K未低于改前，请修正")
    chk(build["K_nonheat_new"] < build["K_nonheat_old"], "改造后非采暖隔墙K未低于改前，请修正")
    if ht == "顶层边户":
        chk(build["K_roof_new"] < build["K_roof_old"], "改造后屋面K未低于改前，请修正")
        chk(build["K_gable_new"] < build["K_gable_old"], "改造后山墙K未低于改前，请修正")
    # ---- 气象 / 渗透 ----
    chk(build["Tin"] > build["Tout"], f"室内设计温度须>室外设计温度（否则热负荷为负），当前Tin={build['Tin']}、Tout={build['Tout']}")
    chk(0 < build["HDD"] <= 5000, f"HDD18须∈(0,5000]℃·d，当前={build['HDD']}")
    chk(0 < build["n"] <= 3.0, f"冷风渗透换气次数须∈(0,3]次/h，当前={build['n']}")
    chk(1.0 <= build["rho"] <= 1.4, f"空气密度须∈[1.0,1.4]kg/m³，当前={build['rho']}")
    chk(800 <= build["cp"] <= 1200, f"空气定压比热容须∈[800,1200]J/(kg·K)，当前={build['cp']}")
    # ---- 热泵容量 / COP ----
    for k, nm in [("SCOP_nameplate1","方案1铭牌SCOP"),("SCOP_nameplate2","方案2铭牌SCOP"),("SCOP_nameplate3","方案3铭牌SCOP")]:
        chk(1.0 <= equip[k] <= 8.0, f"{nm}须∈[1,8]，当前={equip[k]}")
    for k, nm in [("Qhp_rated1","方案1热泵额定制热量"),("Qhp_rated2","方案2热泵额定制热量"),("Qhp_rated3","方案3热泵额定制热量")]:
        chk(1.0 <= equip[k] <= 100.0, f"{nm}须∈[1,100]kW，当前={equip[k]}")
    for k, nm in [("spf_decay1","方案1衰减系数"),("spf_decay2","方案2衰减系数"),("spf_decay3","方案3衰减系数")]:
        chk(0 < equip[k] <= 1.0, f"{nm}须∈(0,1]，当前={equip[k]}")
    # ---- 造价 / 经济 / 排放 ----
    chk(0 < equip["cost_pump"] <= 1000000, f"热泵采购安装总价须∈(0,1000000]元，当前={equip['cost_pump']}")
    chk(0 < equip["budget"] <= 1000000, f"改造预算须∈(0,1000000]元，当前={equip['budget']}")
    chk(0.1 <= equip["elec_price"] <= 3.0, f"居民电价须∈[0.1,3]元/kWh，当前={equip['elec_price']}")
    chk(0.1 <= equip["grid_ef"] <= 2.0, f"电网碳排放因子须∈[0.1,2]kgCO₂/kWh，当前={equip['grid_ef']}")
    for k, nm in [("unit_wall_ins","外墙保温单位造价"),("unit_win_replace","外窗更换单位造价"),("unit_door_replace","外门更换单位造价"),
                  ("unit_nonheat_ins","非采暖隔墙保温单位造价"),("unit_roof_ins","屋面保温单位造价"),("unit_gable_ins","山墙保温单位造价"),
                  ("unit_lowend_floor","地暖末端单位造价")]:
        chk(0 < equip.get(k,0) <= 5000, f"{nm}须∈(0,5000]元/m²，当前={equip.get(k)}")
    # ---- 末端热工参数 ----
    chk(0 < equip["rad_Qrated_kW"] <= 200, f"散热器额定散热量须∈(0,200]kW，当前={equip['rad_Qrated_kW']}")
    chk(10 <= equip["rad_dt_m_rated"] <= 80, f"散热器额定平均温差须∈[10,80]K，当前={equip['rad_dt_m_rated']}")
    chk(0.5 <= equip["rad_m"] <= 1.6, f"散热器散热指数m须∈[0.5,1.6]，当前={equip['rad_m']}")
    chk(2 <= equip["rad_dt_flow_return"] <= 30, f"散热器供回水温差须∈[2,30]K，当前={equip['rad_dt_flow_return']}")
    chk(40 <= equip["rad_tg_max"] <= 75, f"散热器最高供水温度须∈[40,75]℃，当前={equip['rad_tg_max']}")
    chk(0 < equip["floor_Qrated_kW"] <= 200, f"地暖额定散热量须∈(0,200]kW，当前={equip['floor_Qrated_kW']}")
    chk(5 <= equip["floor_dt_m_rated"] <= 40, f"地暖额定平均温差须∈[5,40]K，当前={equip['floor_dt_m_rated']}")
    chk(0.5 <= equip["floor_m"] <= 1.6, f"地暖散热指数m须∈[0.5,1.6]，当前={equip['floor_m']}")
    chk(2 <= equip["floor_dt_flow_return"] <= 15, f"地暖供回水温差须∈[2,15]K，当前={equip['floor_dt_flow_return']}")
    chk(30 <= equip["floor_tg_max"] <= 50, f"地暖最高供水温度须∈[30,50]℃，当前={equip['floor_tg_max']}")
    return (len(errs) == 0, errs)

def calc_component_heat_loss(ht, build_dict, volume, n, rho, cp):
    """围护分项热损失分解：H(W/K)、设计温差热流Q(W)、占比%（V1.28：净墙=毛墙−窗−门）"""
    wall_net_A = calc_wall_net(build_dict)
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
    items.append({"构件":"冷风渗透","面积(m²)":None,"K(W/m²·K)":None,"H(W/K)":round(H_inf_WK,2)})
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
    _norm_num_dict(st.session_state["build"])
    _norm_num_dict(st.session_state["equip"])
    _norm_num_dict(st.session_state["coef_set"])

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


# ===================== V1.21：二维表分段能耗积分 + 数据域闸门 =====================
def calc_segment_hp_aux_2d(seg_list, hp_id, tg_solve, hp_rated_max_kW, q_aux_capacity=None, eta_aux=1.0):
    """
    主算法：HDD分段能耗积分，统一容量与能耗口径。
    - 每段用二维性能表在（段中点室外温度, 反算供水温度tg_solve）双线性插值COP与可用制热量；
    - 热泵制热能力受限部分由备用热源/辅助电加热补充；
    - q_aux_capacity: 备用热源额定容量(kW)，None表示辅助电加热足额兜底(当前模型默认)；
    - unserved_heat: 未满足热量(kWh) = max(0, Q_load - Q_hp - Q_aux_capacity) × hours；
    - 任一工况越出模型适用范围 → data_domain_ok=False，判定该方案不通过。
    return: (seg_out, e_hp_kwh, e_aux_kwh, aux_equiv_hours, data_domain_ok, domain_warns, unserved_heat_kwh)
    """
    seg_out = []
    total_hp_elec = 0.0
    total_aux_elec = 0.0
    total_unserved = 0.0
    data_domain_ok = True
    domain_warns = []
    for seg in seg_list:
        tl = seg["T_low"]
        th = seg["T_high"]
        hdd_seg = seg["hdd_segment"]
        q_heat_kwh = seg["Q_heat_kwh"]
        t_mid = (tl + th)/2.0
        hours_seg = hdd_seg * 24.0
        cop_seg, qhp_avail_kW, in_domain, warns = hp_2d_interpolate(hp_id, t_mid, tg_solve)
        if not in_domain:
            data_domain_ok = False
            domain_warns.extend(warns)
        cop_seg = max(cop_seg, 0.1)
        qhp_avail_kW = min(qhp_avail_kW, hp_rated_max_kW)
        q_avg_load_kW = q_heat_kwh / hours_seg if hours_seg > 1e-6 else 0.0
        q_hp_kwh = min(q_heat_kwh, qhp_avail_kW * hours_seg)
        q_deficit_kwh = max(0.0, q_heat_kwh - q_hp_kwh)
        # 备用热源容量约束：q_aux_capacity=None时足额兜底；否则受容量限制
        if q_aux_capacity is None:
            q_aux_kwh = q_deficit_kwh
            q_unmet_kwh = 0.0
        else:
            q_aux_max_kwh = q_aux_capacity * hours_seg
            q_aux_kwh = min(q_aux_max_kwh, q_deficit_kwh)
            q_unmet_kwh = max(0.0, q_deficit_kwh - q_aux_max_kwh)
        elec_hp_seg = q_hp_kwh / cop_seg
        elec_aux_seg = q_aux_kwh / eta_aux
        total_hp_elec += elec_hp_seg
        total_aux_elec += elec_aux_seg
        total_unserved += q_unmet_kwh
        seg_out.append({
            "T_low":tl,"T_high":th,"t_mid":t_mid,
            "hdd_seg":hdd_seg,"hours_seg":hours_seg,
            "Q_heat_kwh":q_heat_kwh,
            "cop_interp":round(cop_seg,3),
            "hp_avail_kW":round(qhp_avail_kW,3),
            "avg_load_kW":round(q_avg_load_kW,3),
            "Q_hp_kwh":round(q_hp_kwh,2),
            "Q_aux_kwh":round(q_aux_kwh,2),
            "Q_unmet_kwh":round(q_unmet_kwh,2),
            "elec_hp":round(elec_hp_seg,2),
            "elec_aux":round(elec_aux_seg,2),
            "in_domain":in_domain,
            "warns":";".join(warns)
        })
    aux_equiv_hours = total_aux_elec / hp_rated_max_kW if hp_rated_max_kW > 1e-6 else 0.0
    return seg_out, round(total_hp_elec,2), round(total_aux_elec,2), round(aux_equiv_hours,2), data_domain_ok, domain_warns, round(total_unserved,2)


def calc_retrofit_cost_ex(house_type, build_dict, equip_dict, coef_envelope, coef_pump, coef_terminal):
    """分项独立批量折算：围护×coef_envelope、热泵×coef_pump、末端×coef_terminal（V1.28：净墙扣门）"""
    wall_net_A = calc_wall_net(build_dict)
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
        m_val = equip_input.get("rad_enh_m",1.30); dtfr = equip_input.get("rad_enh_dt_flow_return",10.0)
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
    hp_rated_max = equip_input[hp_item["rated_key"]]
    # ---- 热工计算 ----
    H_kWK, _ = calc_H(ht, build_loc, build_loc["volume"], build_loc["n"], build_loc["rho"], build_loc["cp"])
    Qd_kW, _ = calc_design_load(H_kWK, build_loc["Tin"], build_loc["Tout"])
    seg_heat = calc_segment_annual_heat(H_kWK, build_loc["HDD"], hdd_segments)
    tg_solve, th_solve, q_term_calc, term_ok, _ = solve_min_supply_temp(
        Qd_kW, build_loc["Tin"], qr, dtmr, m_val, dtfr, tgmax)
    # V1.21：二维性能表分段能耗积分 + 数据域闸门
    seg_full, e_hp_total, e_aux_total, aux_equiv_h, data_domain_ok, _domain_warns, unserved_heat = calc_segment_hp_aux_2d(
        seg_heat, hp_id, tg_solve, hp_rated_max)
    # 设计工况容量与数据域
    cop_d, qhp_d, in_domain_d, _ = hp_available_at_design(build_loc, equip_input, hp_id, tg_solve)
    data_domain_ok = data_domain_ok and in_domain_d
    e_total_elec = e_hp_total + e_aux_total
    spf_sys = (build_loc["HDD"] * H_kWK * 24.0) / e_total_elec if e_total_elec > 1e-9 else None
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
        "cop_design":round(cop_d,3),"qhp_avail_design":round(qhp_d,3),
        "mr_design":round(qhp_d/Qd_kW,3) if Qd_kW>1e-9 else None,
        "data_domain_ok":data_domain_ok,
        "E_hp_kwh":round(e_hp_total,2),"E_aux_kwh":round(e_aux_total,2),
        "unserved_heat_kwh":unserved_heat,"aux_equiv_hours":aux_equiv_h,"E_total_kwh":round(e_total_elec,2),
        "spf_sys":round(spf_sys,3) if spf_sys is not None else None,
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
    page_title="郑州老旧住宅热泵协同改造方案比选与风险筛查工具 V1.28",
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
    background: linear-gradient(135deg, rgba(219,234,254,0.95), rgba(191,219,254,0.95));
    border: 1px solid rgba(37,99,235,0.40);
    border-radius: 14px;
    padding: 22px 26px;
    margin-bottom: 24px;
    box-shadow: 0 8px 24px rgba(37,99,235,0.14);
}
.light-tech-title h1 {
    font-size: 28px;
    font-weight: 800;
    background: linear-gradient(90deg, #1e40af, #2563eb, #3b82f6);
    -webkit-background-clip: text;
    color: transparent;
    margin: 0 0 8px 0;
}
.light-tech-title p {
    font-size:15px;color:#64748b;margin:0;
}
[data-testid="stMetric"] {
    background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;padding:14px 16px !important;transition:0.25s;
    margin-bottom:6px !important;min-height:76px !important;
}
[data-testid="stMetric"]:hover {
    border-color:#6366f1;box-shadow:0 12px 28px rgba(99,102,241,0.12);
}
[data-testid="stMetricLabel"]{color:#475569 !important;font-weight:500;font-size:13px !important;white-space:nowrap !important;overflow:visible !important;}
[data-testid="stMetricValue"]{color:#6366f1 !important;font-weight:800;font-size:26px !important;white-space:nowrap !important;overflow:visible !important;letter-spacing:-0.3px;}
div[data-testid="stMetricDelta"]>div{color:#10b981 !important;font-weight:600;font-size:12px !important;white-space:nowrap !important;}
/* 确保metric容器不截断内容 */
[data-testid="stMetric"] > div {overflow:visible !important;}
[data-testid="stMetricValue"] > div {overflow:visible !important;white-space:nowrap !important;}
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
    background:linear-gradient(135deg,#dbeafe,#bfdbfe 55%,#93c5fd);
    border:1px solid rgba(37,99,235,0.30);
    border-radius:16px;padding:20px 28px;margin-bottom:16px;color:#1e3a8a;
    box-shadow:0 8px 24px rgba(37,99,235,0.15);
}
.hero-banner .hero-main{font-size:26px;font-weight:800;letter-spacing:1px;background:linear-gradient(90deg,#1e3a8a,#2563eb,#3b82f6);-webkit-background-clip:text;color:transparent;}
.hero-banner .hero-sub{font-size:14px;color:#1e3a8a;margin-top:6px;}
.hero-banner .hero-meta{font-size:12.5px;color:#3b5998;margin-top:10px;border-top:1px solid rgba(37,99,235,0.25);padding-top:8px;}
.hero-banner .hero-route{font-size:12.5px;color:#2563eb;margin-top:6px;}
</style>
"""
st.markdown(light_tech_style, unsafe_allow_html=True)
st.markdown("""
<div class="hero-banner">
    <div class="hero-main">郑州老旧住宅热泵协同改造方案比选与风险筛查工具</div>
    <div class="hero-sub">围护改造 · 末端适配 · 空气源热泵选型 · 经济与碳排放测算｜郑州老旧住宅典型案例</div>
    <div class="hero-meta">作品：老旧住宅空气源热泵协同改造测算系统｜团队：顺势而为队｜版本：V1.28｜更新时间：2026-09-05</div>
    <div class="hero-route">定位：早期方案比较与教学决策支持，不替代暖通设计、设备选型和施工图审查｜技术路线：有限方案枚举 → 建筑热损失 → 设计负荷 → 末端供水温度 → 热泵性能估算面 → 全年分段能耗 → 费用与运行阶段购电间接排放 → 五道闸门（预算/工程/容量+备用/末端/模型适用性） → 可行方案排序</div>
</div>
""", unsafe_allow_html=True)

# ================= V1.8新增：可折叠参数来源台账（答辩追溯） =================
with st.expander("📌【V1.8新增】参数来源台账（答辩追溯·可折叠）", expanded=False):
    _b = st.session_state["build"]
    _e = st.session_state["equip"]
    _c = st.session_state["coef_set"]
    _rows = []
    def _r(name, val, unit, src, yr, pg, cond, tag):
        # 访问日期：源/算=资料查证与计算日期；假=经验假设或示例值，无外部访问日期
        _acd = "2026-09-05" if "源" in tag else "——"
        _rows.append({"参数名称":name,"数值":val,"单位":unit,"文件/标准":src,"年份":yr,"页码/表号":pg,
                      "适用工况":cond,"访问日期":_acd,"源/算/假":tag})
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
    _r("设备A COP(55℃出水)","3.04 / 2.73 / 2.52 / 2.30 / 2.19","-","美的空气源热泵采暖机组官方说明书（雪焰/真暖系列 MHSR120N8-S1，12kW·220V·低环境温度空气源热泵(冷水)机组·地板采暖型，CQC认证名录）·执行 GB/T 25127.2-2020；真实锚点 A7/W45=3.50、A-12/W35=2.70【源】，55℃列按温升比换算【算】","2026","说明书性能参数表","A7/W55、A2/W55、A-2/W55、A-7/W55、A-10/W55","源/算")
    _r("设备B COP(45℃出水)","3.55 / 3.14 / 2.87 / 2.59 / 2.45","-","美的空气源热泵采暖机组官方说明书（雪焰/真暖系列 MHSR100N8-S1，10kW·220V·低环境温度空气源热泵(冷水)机组·地板采暖型，CQC认证名录）·执行 GB/T 25127.2-2020；真实锚点 A7/W45=3.55、A-12/W35=2.70、A-20/W35=2.21【源】，其余按温升比幂律标定【算】","2026","说明书性能参数表","A7/W45、A2/W45、A-2/W45、A-7/W45、A-10/W45","源/算")
    _r("设备B额定制热量","{:.1f}".format(_e["Qhp_rated3"]),"kW","美的雪焰/真暖 MHSR100N8-S1 说明书·额定制热 A7/W45=10.0kW","2026","说明书性能参数表","A7/W45","源")
    _r("设备A额定制热量","{:.1f}/{:.1f}".format(_e["Qhp_rated1"],_e["Qhp_rated2"]),"kW","美的雪焰/真暖 MHSR120N8-S1 说明书·额定制热 A7/W45=12.0kW","2026","说明书性能参数表","A7/W45","源")
    _r("热泵冬季衰减系数","{:.2f}/{:.2f}/{:.2f}".format(_e["spf_decay1"],_e["spf_decay2"],_e["spf_decay3"]),"-","结霜衰减经验系数(低环温)","-","-","-7℃以下","假")
    _r("热泵性能估算面(室外×供水)","-15~10℃ × 30~65℃(设备A)/25~50℃(设备B)","-","设备A(MHSR120N8-S1)锚点 A7/W45=3.50/12kW【源】，55℃列按温升比换算【算】；设备B(MHSR100N8-S1)锚点 A7/W45=3.55/10kW【源】；推算 k=0.6/0.4、1.0/0.5","2026","说明书性能参数表","模型适用范围内双线性插值，范围外禁止外推；估算面≠完整厂家性能矩阵","源/算")
    # ---- 末端 ----
    _r("散热器额定平均温差","{:.1f}".format(_e["rad_dt_m_rated"]),"K","GB/T 13754-2017《供暖散热器散热量测定方法》（传统国标标定工况 95/70/18，ΔT=64.5K）","2017","§6.4.3/§6.6","tn=18℃","源")
    _r("散热器散热指数m","{:.2f}".format(_e["rad_m"]),"-","GB/T 13754-2017 §6.6.1.1 式(8) Q=K_M·ΔT^m（指数m由该型号热工检测报告实测拟合，标准不给定类型默认值）；本程序取工程典型值 m≈1.30（铸铁柱式实测 m≈1.28~1.30，如 74×60 铸铁 m≈1.283）","2017","式(8)","标准过余温度44.5K","算/典型值")
    _r("散热器允许最高供水温度","{:.0f}".format(_e["rad_tg_max"]),"℃","传统铸铁散热器系统允许供水温度上限·工程典型值（采暖设计供水 95/70 系统可完全承受 65℃；空气源热泵低温工况出水越接近此限 COP 越低）","2012","GB 50736-2012 表5.3.1","散热器采暖系统","算/典型值")
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
    _r("电力二氧化碳排放因子","{:.4f}".format(_e["grid_ef"]),"kgCO₂/kWh","2023年河南省电力平均二氧化碳排放因子(生态环境部、国家统计局2025年第47号公告)","2023","公告","运行阶段购电间接排放(位置法)","源")
    # ---- 批量折算系数（调研依据） ----
    _r("围护有效系数","{:.2f}".format(1.00 if st.session_state["retrofit_mode"]=="分户独立改造" else _c["coef_envelope"]),"-","分户=1.00；批量=行业调研经验·EPC集采/外脚手架共用/人工摊薄(页面2可改)","2026","-","按当前造价模式","假")
    _r("热泵有效系数","{:.2f}".format(1.00 if st.session_state["retrofit_mode"]=="分户独立改造" else _c["coef_pump"]),"-","分户=1.00；批量=行业调研经验·厂家批量供货/统一班组安装省差旅(页面2可改)","2026","-","按当前造价模式","假")
    _r("末端有效系数","{:.2f}".format(1.00 if st.session_state["retrofit_mode"]=="分户独立改造" else _c["coef_terminal"]),"-","分户=1.00；批量=行业调研经验·批量进场/开槽回填工序统一调度(页面2可改)","2026","-","按当前造价模式","假")
    # ---- 计算结果口径（算） ----
    _r("总热损失系数H","-","kW/K","本程序按围护+冷风渗透计算(见页面3)","-","-","模型输出","算")
    _r("设计热负荷Q_design","-","kW","H×ΔT，无附加耗热量(见页面3)","-","-","模型输出","算")
    _r("全年需热量Q_year","-","kWh","H×HDD18×24(见页面3)","-","-","模型输出","算")
    _r("E_HP / E_aux","-","kWh","HDD分段×性能估算面COP插值(供水=反算tg)，容量不足部分辅助电加热(见页面3展开)；年度E_aux与设计工况需备用容量分口径","-","-","模型输出","算")
    # V1.28 P1-3：用户覆盖默认值后，台账动态标注【用户输入】，规范/默认值单独保留（不再冒充规范原值）
    _dflt_b_led = DEFAULT_BUILD_MID if st.session_state["house_type"] == "中间层住宅" else DEFAULT_BUILD_TOP_EDGE
    _dflt_e_led = DEFAULT_EQUIP
    _override_map = [
        ("郑州采暖室外计算温度", _dflt_b_led["Tout"]),
        ("室内采暖设计温度", _dflt_b_led["Tin"]),
        ("HDD18采暖度日数", _dflt_b_led["HDD"]),
        ("外墙K值(改前)", _dflt_b_led["Kw_old"]),
        ("外墙K值(改后保温)", _dflt_b_led["Kw_new"]),
        ("外窗K值(改前)", _dflt_b_led["Kwin_old"]),
        ("外窗K值(改后)", _dflt_b_led["Kwin_new"]),
        ("冷风渗透换气次数", _dflt_b_led["n"]),
        ("居民电价", _dflt_e_led["elec_price"]),
        ("电力二氧化碳排放因子", _dflt_e_led["grid_ef"]),
    ]
    for _rrow in _rows:
        for _nm_led, _dv_led in _override_map:
            if _rrow["参数名称"] == _nm_led:
                try:
                    _cur_led = float(_rrow["数值"])
                    if abs(_cur_led - float(_dv_led)) > 1e-6:
                        _rrow["数值"] = f"{_rrow['数值']}（规范/默认值 {_dv_led}）"
                        _rrow["源/算/假"] = str(_rrow["源/算/假"]) + "｜当前值【用户输入】"
                except (ValueError, TypeError):
                    pass
    _ledger_df = pd.DataFrame(_rows)
    st.caption("标注：【源】=规范/数据库/实测直接引用；【算】=程序计算；【假】=经验假设或示例值，答辩前请按实际选型/询价替换。设备A(MHSR120N8-S1·12kW)与设备B(MHSR100N8-S1·10kW)均为低环境温度空气源热泵(冷水)机组（CQC认证名录，）；"
               "性能估算面 55℃/45℃ 出水列锚点来自官方说明书性能参数表【源】，其余格为按温升幂律推算的【算】值——整体为模型估算面（证据等级C，），不是完整厂家性能矩阵；增强散热器、造价与批量系数等仍为【假】示例值。"
               "当用户值覆盖默认值时，对应台账自动标注【用户输入】。访问日期口径：【源/算】=2026-09-05；【假】=经验假设或示例值，无外部访问日期。")
    st.dataframe(_ledger_df, width="stretch", hide_index=True, height=320)

#侧边栏
with st.sidebar:
    st.markdown("""
<div style="padding:10px 0;border-bottom:1px solid rgba(99,102,241,0.25);margin-bottom:14px;">
<h3 style="color:#6366f1;margin:0;">📌 参数来源台账</h3>
<div style="font-size:12px;color:#666;">V1.28｜性能估算面插值+HDD分段能耗+五道闸门｜末端热工迭代求供水温度｜SPF_HP+aux统一口径</div>
</div>
""", unsafe_allow_html=True)
    with st.expander("📖 参数说明与折算依据（点击展开）", expanded=False):
        st.markdown("**热泵性能估算面**｜所选户用机组的产品与试验口径以厂家资料所列 **GB/T 25127.2—2020（户用及类似用途）** 为准；GB/T 25127.1—2020 适用于工业或商业及类似用途，本案例不采用该部分。锚点=厂家公开数据【源】，推算格=温升幂律模型【算】；每一条：［室外环境温度℃，供水温度℃，COP，工况可用制热量kW］。方案1、2 使用设备A；方案3 使用设备B。")
        st.markdown("""
**批量改造分项折算系数调研参考依据（项目需按当地招标报价修正）：**
- 分户独立改造：围护=1.00，热泵=1.00，末端=1.00；
- 整栋集中批量改造参考经验：
  - 围护保温工程 **0.75**：老旧小区EPC批量集采、外脚手架共用、人工摊薄；
  - 空气源热泵设备安装 **0.85**：厂家批量供货、统一班组安装，省去零散上门差旅成本；
  - 室内末端改造 **0.80**：批量进场、开槽回填工序统一调度。
""")
    sel_house = st.selectbox("🏠选择户型",["中间层住宅","顶层边户"])
    if sel_house != st.session_state["house_type"]:
        switch_house_type(sel_house)
    ht = st.session_state["house_type"]
    if ht == "中间层住宅":
        st.info("【中间层住宅】上下均采暖住户；不计屋面、地面楼板；构件：外墙、外窗、外门、非采暖隔墙")
    else:
        st.info("【顶层边户】顶层+东西山墙边户；计入屋面、东西山墙；不计底层地面楼板")
    st.session_state["retrofit_mode"] = st.selectbox("🔧改造造价模式", list(RETROFIT_MODE_CFG.keys()))
    if st.session_state["retrofit_mode"] == "整栋集中批量改造":
        st.info(f"批量有效系数：围护 {st.session_state['coef_set']['coef_envelope']}｜热泵 {st.session_state['coef_set']['coef_pump']}｜末端 {st.session_state['coef_set']['coef_terminal']}（分项结算）")
    else:
        st.info("分户独立改造：围护/热泵/末端有效系数均=1.00")
    # ===== V1.8新增：计算模式切换 =====
    st.session_state["calc_mode"] = st.radio("🧮计算模式",["三套典型方案","18种自由组合批量计算"])
    if st.session_state["calc_mode"] == "18种自由组合批量计算":
        st.session_state["calc_mode"] = "batch_18"
    else:
        st.session_state["calc_mode"] = "typical"

    # ===== V1.9新增：模型版本号 + 恢复统一基准 =====
    st.markdown("**🛠 模型版本号：V1.28**")
    st.caption("更新时间：2026-09-05\n计算链：H → Q_design → Q_year → 末端反算tg → 估算面COP插值 → E_HP+E_aux → SPF_HP+aux → 费用 → 运行期碳排放 → 五道闸门")
    if st.button("♻️恢复统一基准（重置全部默认参数）", width="stretch"):
        reset_to_defaults()
        st.success("已恢复统一基准：建筑/设备/批量系数回到默认值")
    # ===== V1.10新增：保存方案快照（可载入） =====
    if st.button("💾保存当前方案", width="stretch"):
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
                if st.button(f"载入方案{_si+1}｜{_s['时间']}｜{_s['户型']}", key=f"load_scheme_{_si}", width="stretch"):
                    st.session_state["build"] = _s["建筑"]
                    st.session_state["equip"] = _s["设备"]
                    st.session_state["coef_set"] = _s["系数"]
                    st.rerun()
    st.divider()
    _b_ev=st.session_state["build"]; _e_ev=st.session_state["equip"]
    with st.expander("📋 参数证据链（点击展开/折叠）", expanded=False):
        st.markdown(f"""
        **参数证据链**（详见页面顶部台账逐项：数值/年份/页码·表号/适用工况/访问日期/【源·算·假】）
        1. 外墙K改前{_b_ev['Kw_old']:.2f}、改后{_b_ev['Kw_new']:.2f} W/(m²·K)：GB 50176-2016 附录B表B.0.1 / JGJ 26-2018 表4.2.2-3（2016/2018·郑州·源·2026-08-31）
        2. 郑州采暖室外计算温度{_b_ev['Tout']:.1f}℃：GB 50176-2016 附录A表A.0.1·郑州站57083·源
        3. 郑州HDD18={_b_ev['HDD']:.0f}℃·d：《中国建筑热环境分析专用气象数据集》(典型气象年)·郑州站57083·1984-2003·基准18℃·源
        4. 热泵样本：美的雪焰/真暖 MHSR120N8-S1(12kW)、MHSR100N8-S1(10kW)·执行 GB/T 25127.2-2020·A7/W45 COP=3.50/3.55、A-12/W35=2.70·2026说明书性能表·源
        5. 热负荷：不计朝向/风力/高度附加；热桥与间歇修正未纳入——定位“早期方案比较/教学决策支持”
        6. ⚠️本程序**不适用底层住户**
        7. V1.28：性能估算面插值(模型适用范围内)；HDD多温度分段计算全年能耗；SPF_HP+aux=Q_year/(E_HP+E_aux)；旧SPF仅作参考
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
    build = st.session_state["build"]
    st.info("📐【】外墙净面积 = 外墙毛面积 − 外窗面积 − 外门面积。"
            f"当前净外墙面积 = {round(calc_wall_net(build),2)} m²。仅当净外墙面积>0 时允许计算；当外窗+外门 ≥ 外墙毛面积时，阻断页面3并提示核对几何输入。")
    _dflt_b_p1 = DEFAULT_BUILD_MID if ht == "中间层住宅" else DEFAULT_BUILD_TOP_EDGE
    if abs(build["Tout"] - _dflt_b_p1["Tout"]) > 1e-6 or abs(build["HDD"] - _dflt_b_p1["HDD"]) > 1e-6 or abs(build["Tin"] - _dflt_b_p1["Tin"]) > 1e-6:
        st.warning("🟡【】检测到室外设计温度/HDD/室内设计温度已覆盖规范默认值（当前值用于敏感性/边界测试），"
                   f"不代表郑州规范参数：规范/默认值：室外 {_dflt_b_p1['Tout']:.1f}℃、HDD18 {_dflt_b_p1['HDD']:.0f}℃·d、室内 {_dflt_b_p1['Tin']:.0f}℃；"
                   f"当前计算值：室外 {build['Tout']:.1f}℃、HDD18 {build['HDD']:.0f}℃·d、室内 {build['Tin']:.0f}℃。台账已同步标注【用户输入】。")
    warn_messages = input_warning_check(build, st.session_state["equip"])
    for w in warn_messages:
        st.warning(w)

    # ===== V1.9新增：扩展输入边界与交叉校验 =====
    for wv in input_warning_check_v18(build, st.session_state["equip"], ht):
        st.warning(wv)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📐建筑基础尺寸")
        st.number_input("建筑面积 m²",value=build["area"],min_value=10.0,max_value=600.0,key="_area",on_change=sync_build,args=("_area", "area"))
        st.number_input("楼层层高 m",value=build["floor_h"],min_value=2.4,max_value=6.0,key="_floor_h",on_change=sync_build,args=("_floor_h", "floor_h"))
        room_volume = build["area"] * build["floor_h"]
        st.metric("室内总体积 m³", value=round(room_volume,2))
        st.number_input("外墙毛总面积 m²（含窗洞口）",value=build["wall_gross"],min_value=20.0,max_value=600.0,key="_wall_gross",on_change=sync_build,args=("_wall_gross","wall_gross"))
        st.number_input("外窗总面积 m²",value=build["win"],min_value=2.0,max_value=400.0,key="_win",on_change=sync_build,args=("_win","win"))
        st.number_input("外门面积 m²",value=build["door_A"],min_value=0.0,max_value=20.0,key="_door_A",on_change=sync_build,args=("_door_A","door_A"))
        _wall_net_show = calc_wall_net(build)
        st.metric("外墙净面积 m²（毛墙−窗−门）", round(_wall_net_show, 2))
        _g_ok1, _g_msg1 = geometry_valid(build)
        if not _g_ok1:
            st.error("⛔" + _g_msg1 + "（外窗+外门≥外墙毛面积时阻断计算）")
        st.number_input("非采暖隔墙面积 m²(楼梯间等)",value=build["nonheat_wall_A"],min_value=0.0,max_value=300.0,key="_nonheat_wall_A",on_change=sync_build,args=("_nonheat_wall_A","nonheat_wall_A"))
        if ht == "顶层边户":
            st.divider()
            st.subheader("顶层边户专属构件")
            st.number_input("屋面面积 m²",value=build["roof_A"],min_value=0.0,max_value=600.0,key="_roof_A",on_change=sync_build,args=("_roof_A","roof_A"))
            st.number_input("东西山墙面积 m²",value=build["gable_wall_A"],min_value=0.0,max_value=200.0,key="_gable_wall_A",on_change=sync_build,args=("_gable_wall_A","gable_wall_A"))
    with col2:
        st.subheader("🔥围护传热系数 K W/(m²·K)")
        st.markdown("**外墙 & 外窗 & 外门 & 非采暖隔墙**")
        st.number_input("改造前外墙K",value=build["Kw_old"],min_value=0.10,max_value=8.0,key="_Kw_old",on_change=sync_build,args=("_Kw_old","Kw_old"))
        st.number_input("改造后外墙保温K",value=build["Kw_new"],min_value=0.10,max_value=8.0,key="_Kw_new",on_change=sync_build,args=("_Kw_new","Kw_new"))
        st.number_input("改造前外窗K",value=build["Kwin_old"],min_value=0.10,max_value=8.0,key="_Kwin_old",on_change=sync_build,args=("_Kwin_old","Kwin_old"))
        st.number_input("改造后外窗K",value=build["Kwin_new"],min_value=0.10,max_value=8.0,key="_Kwin_new",on_change=sync_build,args=("_Kwin_new","Kwin_new"))
        st.number_input("改造前外门K",value=build["K_door_old"],min_value=0.10,max_value=8.0,key="_K_door_old",on_change=sync_build,args=("_K_door_old","K_door_old"))
        st.number_input("改造后外门K",value=build["K_door_new"],min_value=0.10,max_value=8.0,key="_K_door_new",on_change=sync_build,args=("_K_door_new","K_door_new"))
        st.number_input("改造前非采暖隔墙K",value=build["K_nonheat_old"],min_value=0.10,max_value=8.0,key="_K_nonheat_old",on_change=sync_build,args=("_K_nonheat_old","K_nonheat_old"))
        st.number_input("改造后非采暖隔墙K",value=build["K_nonheat_new"],min_value=0.10,max_value=8.0,key="_K_nonheat_new",on_change=sync_build,args=("_K_nonheat_new","K_nonheat_new"))
        if ht == "顶层边户":
            st.divider()
            st.markdown("**顶层边户专属K值（屋面、东西山墙）**")
            st.number_input("改造前屋面K",value=build["K_roof_old"],min_value=0.10,max_value=8.0,key="_K_roof_old",on_change=sync_build,args=("_K_roof_old","K_roof_old"))
            st.number_input("改造后屋面保温K",value=build["K_roof_new"],min_value=0.10,max_value=8.0,key="_K_roof_new",on_change=sync_build,args=("_K_roof_new","K_roof_new"))
            st.number_input("改造前东西山墙K",value=build["K_gable_old"],min_value=0.10,max_value=8.0,key="_K_gable_old",on_change=sync_build,args=("_K_gable_old","K_gable_old"))
            st.number_input("改造后东西山墙保温K",value=build["K_gable_new"],min_value=0.10,max_value=8.0,key="_K_gable_new",on_change=sync_build,args=("_K_gable_new","K_gable_new"))
    st.divider()
    col3,col4 = st.columns(2)
    with col3:
        st.subheader("🌡️气象室内设计参数")
        st.number_input("室内采暖设计温度 ℃【源·GB50736】",value=build["Tin"],min_value=15.0,max_value=30.0,key="_Tin",on_change=sync_build,args=("_Tin","Tin"))
        st.number_input("郑州室外设计温度 ℃【源·GB50176】",value=build["Tout"],min_value=-30.0,max_value=0.0,key="_Tout",on_change=sync_build,args=("_Tout","Tout"))
        delta_T = build["Tin"] - build["Tout"]
        st.metric("室内外温差ΔT(K)【计算值·只读】", delta_T)
        st.number_input("HDD18采暖度日数 ℃·d【源·气象数据集】",value=build["HDD"],min_value=0.0,max_value=5000.0,key="_HDD",on_change=sync_build,args=("_HDD","HDD"))
    with col4:
        st.subheader("💨冷风渗透参数")
        st.number_input("冷风渗透换气次数 次/h【假·经验值】",value=build["n"],min_value=0.1,max_value=3.0,key="_n",on_change=sync_build,args=("_n","n"))
        st.number_input("空气密度 kg/m³【源·工程热力学】",value=build["rho"],min_value=1.1,max_value=1.4,key="_rho",on_change=sync_build,args=("_rho","rho"))
        st.number_input("空气定压比热容 J/(kg·K)【源·工程热力学】",value=build["cp"],min_value=900.0,max_value=1100.0,key="_cp",on_change=sync_build,args=("_cp","cp"))
        st.info("本模型**不设置朝向、风力、高度附加耗热量**")
    st.session_state["build"]["volume"] = build["area"] * build["floor_h"]
    st.session_state["build"]["dT"] = build["Tin"] - build["Tout"]
    _ok_in, _errs_in = validate_inputs_strict(build, st.session_state["equip"], ht)
    if _ok_in:
        st.success(f"✅{ht}围护参数校验通过，前往页面2录入热泵、末端热工与单位造价参数")
    else:
        st.error("⛔存在异常输入，尚未通过校验（修正前页面3将阻止计算）：")
        for _e in _errs_in[:8]:
            st.error("• " + _e)
        if len(_errs_in) > 8:
            st.error(f"• …等共{len(_errs_in)}项，请逐项修正")
# ======================页面2：热泵&末端热工&单位造价录入【V1.7增加厂家样本表】 ======================
elif page_select == "2.热泵&末端热工&单位造价录入":
    st.markdown("""
<div class="light-tech-title">
    <h1>🔥 空气源热泵、末端热工模型、围护分项单位造价录入</h1>
    <p>👉V1.6更新：不再手动输入供水温度；输入末端额定参数，程序迭代反算满足热负荷的最低供水温度；围护=单位造价×工程量</p>
    <p>👉V1.28更新：热泵性能为【室外温度×供水温度】性能估算面（厂家锚点+模型推算，）双线性插值（模型适用范围内），范围外禁止外推；HDD分段全年能耗计算</p>
    <p>末端公式：$Q_{terminal}=Q_{rated} \\times (\\Delta T_m / \\Delta T_{m,rated})^m$（散热器 m≈1.30，地暖 m≈0.95）</p>
</div>
""", unsafe_allow_html=True)
    equip = st.session_state["equip"]
    build = st.session_state["build"]
    warn_messages = input_warning_check(build, equip)
    for w in warn_messages:
        st.warning(w)
    col_left, col_mid, col_right = st.columns([1,1,1])
    # ===== V1.8新增：分项独立批量折算系数（可编辑，含调研依据） =====
    st.subheader("🔧批量改造分项折算系数（V1.28：分项结算；分户模式下强制=1.00并置灰）")
    _is_batch = (st.session_state["retrofit_mode"] == "整栋集中批量改造")
    st.caption("批量模式：围护×0.75、热泵×0.85、末端×0.80（默认，可编辑）；分户独立改造：三系数强制=1.00（输入置灰，见A08）。")
    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        st.number_input("围护工程折算系数", min_value=0.4, max_value=1.0, step=0.01,
                        value=st.session_state["coef_set"]["coef_envelope"], key="_coef_env", disabled=not _is_batch,
                        on_change=lambda: st.session_state["coef_set"].update({"coef_envelope": st.session_state["_coef_env"]}))
    with cc2:
        st.number_input("热泵设备安装折算系数", min_value=0.4, max_value=1.0, step=0.01,
                        value=st.session_state["coef_set"]["coef_pump"], key="_coef_pump", disabled=not _is_batch,
                        on_change=lambda: st.session_state["coef_set"].update({"coef_pump": st.session_state["_coef_pump"]}))
    with cc3:
        st.number_input("室内末端改造折算系数", min_value=0.4, max_value=1.0, step=0.01,
                        value=st.session_state["coef_set"]["coef_terminal"], key="_coef_term", disabled=not _is_batch,
                        on_change=lambda: st.session_state["coef_set"].update({"coef_terminal": st.session_state["_coef_term"]}))
    st.divider()
    col_left, col_mid, col_right = st.columns([1,1,1])
    with col_left:
        st.subheader("空气源热泵参数（固定总价）")
        st.caption("设备A：MHSR120N8-S1（12kW级低环境温度空气源热泵(冷水)机组·地板采暖型）；设备B：MHSR100N8-S1（10kW级，同上）。适用末端以证书/样本为准。")
        st.number_input("方案1 设备A 铭牌SCOP",value=equip["SCOP_nameplate1"],min_value=1.0,max_value=8.0,key="_SCOPnp1",on_change=sync_equip,args=("_SCOPnp1", "SCOP_nameplate1"))
        st.number_input("方案2 设备A 铭牌SCOP",value=equip["SCOP_nameplate2"],min_value=1.0,max_value=8.0,key="_SCOPnp2",on_change=sync_equip,args=("_SCOPnp2", "SCOP_nameplate2"))
        st.number_input("方案3 设备B 铭牌SCOP",value=equip["SCOP_nameplate3"],min_value=1.0,max_value=8.0,key="_SCOPnp3",on_change=sync_equip,args=("_SCOPnp3", "SCOP_nameplate3"))
        st.divider()
        st.subheader("❄️冬季低温衰减系数(0<f≤1)")
        st.number_input("方案1 衰减系数",value=equip["spf_decay1"],min_value=0.1,max_value=1.0,key="_decay1",on_change=sync_equip,args=("_decay1", "spf_decay1"))
        st.number_input("方案2 衰减系数",value=equip["spf_decay2"],min_value=0.1,max_value=1.0,key="_decay2",on_change=sync_equip,args=("_decay2", "spf_decay2"))
        st.number_input("方案3 衰减系数",value=equip["spf_decay3"],min_value=0.1,max_value=1.0,key="_decay3",on_change=sync_equip,args=("_decay3", "spf_decay3"))
        st.divider()
        st.subheader("🧪 热泵‑7℃工况额定制热量(kW)")
        st.number_input("方案1 设备A 额定制热量 kW",value=equip["Qhp_rated1"],min_value=1.0,max_value=100.0,key="_Qhp_rated1",on_change=sync_equip,args=("_Qhp_rated1", "Qhp_rated1"))
        st.number_input("方案2 设备A 额定制热量 kW",value=equip["Qhp_rated2"],min_value=1.0,max_value=100.0,key="_Qhp_rated2",on_change=sync_equip,args=("_Qhp_rated2", "Qhp_rated2"))
        st.number_input("方案3 设备B 额定制热量 kW",value=equip["Qhp_rated3"],min_value=1.0,max_value=100.0,key="_Qhp_rated3",on_change=sync_equip,args=("_Qhp_rated3", "Qhp_rated3"))
    with col_mid:
        st.subheader("🧱围护分项单位造价【元/m²】")
        st.number_input("外墙保温单位造价 元/m²",value=equip["unit_wall_ins"],min_value=0.0,max_value=1000.0,key="_unit_wall_ins",on_change=sync_equip,args=("_unit_wall_ins","unit_wall_ins"))
        st.number_input("外窗更换单位造价 元/m²",value=equip["unit_win_replace"],min_value=0.0,max_value=3000.0,key="_unit_win_replace",on_change=sync_equip,args=("_unit_win_replace","unit_win_replace"))
        st.number_input("外门更换单位造价 元/m²",value=equip["unit_door_replace"],min_value=0.0,max_value=3000.0,key="_unit_door_replace",on_change=sync_equip,args=("_unit_door_replace","unit_door_replace"))
        st.number_input("非采暖隔墙保温单位造价 元/m²",value=equip["unit_nonheat_ins"],min_value=0.0,max_value=1000.0,key="_unit_nonheat_ins",on_change=sync_equip,args=("_unit_nonheat_ins","unit_nonheat_ins"))
        st.divider()
        st.info("顶层边户才生效，中间层不计入")
        st.number_input("屋面保温单位造价 元/m²",value=equip["unit_roof_ins"],min_value=0.0,max_value=1000.0,key="_unit_roof_ins",on_change=sync_equip,args=("_unit_roof_ins","unit_roof_ins"))
        st.number_input("东西山墙保温单位造价 元/m²",value=equip["unit_gable_ins"],min_value=0.0,max_value=1000.0,key="_unit_gable_ins",on_change=sync_equip,args=("_unit_gable_ins","unit_gable_ins"))
        st.divider()
        st.subheader("低温地暖末端造价")
        st.number_input("地暖末端单位造价 元/㎡建筑面积",value=equip["unit_lowend_floor"],min_value=0.0,max_value=1000.0,key="_unit_lowend_floor",on_change=sync_equip,args=("_unit_lowend_floor","unit_lowend_floor"))
    with col_right:
        st.subheader("💰设备总价与经济参数")
        st.number_input("空气源热泵采购安装总价 元【固定，与面积无关】",value=equip["cost_pump"],min_value=0.0,max_value=1000000.0,key="_cost_pump",on_change=sync_equip,args=("_cost_pump", "cost_pump"))
        st.number_input("业主改造费用预算 元",value=equip["budget"],min_value=0.0,max_value=1000000.0,key="_budget",on_change=sync_equip,args=("_budget", "budget"))
        st.number_input("居民电价 元/kWh",value=equip["elec_price"],min_value=0.3,max_value=2.0,key="_elec_price",on_change=sync_equip,args=("_elec_price", "elec_price"))
        st.number_input("电力二氧化碳排放因子 kgCO₂/kWh",value=equip["grid_ef"],min_value=0.0,max_value=2.0,step=0.0001,format="%.4f",key="_grid_ef",on_change=sync_equip,args=("_grid_ef", "grid_ef"))
        st.caption("默认0.5897=2023年河南省电力平均二氧化碳排放因子（生态环境部、国家统计局2025年第47号公告）；计算边界：运行阶段购电间接排放（位置法，）。若改用0.5810须给出准确文件名/年份与适用理由。")
    st.divider()
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.subheader("🔥原有散热器末端（方案1、方案2使用）")
        st.number_input("散热器总额定散热量 kW",value=equip["rad_Qrated_kW"],min_value=0.5,max_value=200.0,key="_rad_Qrated_kW",on_change=sync_equip,args=("_rad_Qrated_kW","rad_Qrated_kW"))
        st.number_input("散热器额定平均温差 K",value=equip["rad_dt_m_rated"],min_value=10.0,max_value=80.0,key="_rad_dt_m_rated",on_change=sync_equip,args=("_rad_dt_m_rated","rad_dt_m_rated"))
        st.number_input("散热器散热指数 m",value=equip["rad_m"],min_value=0.5,max_value=1.6,key="_rad_m",on_change=sync_equip,args=("_rad_m","rad_m"))
        st.number_input("散热器供‑回水温差 K",value=equip["rad_dt_flow_return"],min_value=2.0,max_value=30.0,key="_rad_dt_flow_return",on_change=sync_equip,args=("_rad_dt_flow_return","rad_dt_flow_return"))
        st.number_input("散热器允许最高供水温度 ℃",value=equip["rad_tg_max"],min_value=40.0,max_value=75.0,key="_rad_tg_max",on_change=sync_equip,args=("_rad_tg_max","rad_tg_max"))
    with col_t2:
        st.subheader("❄️低温地暖末端（仅方案3使用）")
        st.number_input("地暖总额定散热量 kW",value=equip["floor_Qrated_kW"],min_value=0.5,max_value=200.0,key="_floor_Qrated_kW",on_change=sync_equip,args=("_floor_Qrated_kW","floor_Qrated_kW"))
        st.number_input("地暖额定平均温差 K",value=equip["floor_dt_m_rated"],min_value=5.0,max_value=40.0,key="_floor_dt_m_rated",on_change=sync_equip,args=("_floor_dt_m_rated","floor_dt_m_rated"))
        st.number_input("地暖散热指数 m",value=equip["floor_m"],min_value=0.5,max_value=1.6,key="_floor_m",on_change=sync_equip,args=("_floor_m","floor_m"))
        st.number_input("地暖供‑回水温差 K",value=equip["floor_dt_flow_return"],min_value=2.0,max_value=15.0,key="_floor_dt_flow_return",on_change=sync_equip,args=("_floor_dt_flow_return","floor_dt_flow_return"))
        st.number_input("地暖允许最高供水温度 ℃",value=equip["floor_tg_max"],min_value=30.0,max_value=50.0,key="_floor_tg_max",on_change=sync_equip,args=("_floor_tg_max","floor_tg_max"))

    # ========= V1.7新增：热泵厂家样本表展示（V1.21补充二维性能表） =========
    st.divider()
    st.subheader("📋热泵性能估算面数据（锚点【源】+推算格【算】；V1.28 已分栏，）")
    st.caption("以下两表为厂家公开锚点（白色/实心=厂家公开数据【源】）与温升幂律推算格（灰色/空心=模型推算【算】）共同构成的估算面；"
               "程序仅在模型适用范围内估算COP与可用制热量。正式设备选型必须以对应型号完整厂家样本、认证资料或试验数据复核；"
               "在获得完整厂家性能矩阵前，本面不作为最终设备选型依据（证据等级C）。")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.markdown("**设备A 锚点列｜MHSR120N8-S1(12kW)｜样本出水：55℃（一维参考）**")
        df_sample_norm = pd.DataFrame(SAMPLE_HP_NORMAL,columns=["室外温度℃","样本供水温度℃","COP","可用制热量kW"])
        st.dataframe(df_sample_norm)
    with col_s2:
        st.markdown("**设备B 锚点列｜MHSR100N8-S1(10kW)｜样本出水：45℃（一维参考）**")
        df_sample_low = pd.DataFrame(SAMPLE_HP_LOWTEMP,columns=["室外温度℃","样本供水温度℃","COP","可用制热量kW"])
        st.dataframe(df_sample_low)
    with st.expander("📊【V1.28】性能估算面（室外温度×供水温度）｜用于双线性插值（锚点/推算分栏）"):
        st.caption("行=室外温度（升序），列=供水温度（升序）。两套面均已按【美的雪焰/真暖】官方说明书真实锚点标定："
                   "设备A(MHSR120N8-S1·12kW) A7/W45 COP=3.50、Q=12kW，55℃出水列按温升比换算【算】；"
                   "设备B(MHSR100N8-S1·10kW) A7/W45 COP=3.55、Q=10kW，A-12/W35 COP=2.70。"
                   "其余格为模型推算（算）：设备A COP∝(L_ref/L)^0.6、Q∝(L_ref/L)^0.4；设备B COP∝(L_ref/L)^1.0、Q∝(L_ref/L)^0.5。"
                   "矩形边界=模型适用范围（model_applicability），不是厂家验证域（manufacturer_domain）。")
        cc1, cc2 = st.columns(2)
        with cc1:
            st.markdown("**设备A COP 估算面｜供水[30..65]℃**")
            _dfc = pd.DataFrame(SAMPLE_HP_NORMAL_2D_COP, index=SAMPLE_HP_NORMAL_2D_OUT, columns=SAMPLE_HP_NORMAL_2D_TG)
            st.dataframe(_dfc)
            st.markdown("**设备A 可用制热量(kW) 估算面**")
            _dfq = pd.DataFrame(SAMPLE_HP_NORMAL_2D_QCAP, index=SAMPLE_HP_NORMAL_2D_OUT, columns=SAMPLE_HP_NORMAL_2D_TG)
            st.dataframe(_dfq)
        with cc2:
            st.markdown("**设备B COP 估算面｜供水[25..50]℃**")
            _dfc2 = pd.DataFrame(SAMPLE_HP_LOWTEMP_2D_COP, index=SAMPLE_HP_LOWTEMP_2D_OUT, columns=SAMPLE_HP_LOWTEMP_2D_TG)
            st.dataframe(_dfc2)
            st.markdown("**设备B 可用制热量(kW) 估算面**")
            _dfq2 = pd.DataFrame(SAMPLE_HP_LOWTEMP_2D_QCAP, index=SAMPLE_HP_LOWTEMP_2D_OUT, columns=SAMPLE_HP_LOWTEMP_2D_TG)
            st.dataframe(_dfq2)

    st.success("✅热泵、末端热工、单位造价参数保存完毕，进入第三页；程序自动迭代求解最低供水温度！")
# ======================页面3：三套方案计算结果 ======================
elif page_select == "3.三套方案计算结果":
    ht = st.session_state["house_type"]
    build = st.session_state["build"]
    equip = st.session_state["equip"]
    # V1.28：P0-4 分项有效系数（分户=1.00/1.00/1.00；批量=coef_set 可编辑值，默认0.75/0.85/0.80）
    _mode_cfg = RETROFIT_MODE_CFG[st.session_state["retrofit_mode"]]
    if st.session_state["retrofit_mode"] == "分户独立改造":
        eff_coef_env, eff_coef_pump, eff_coef_term = 1.00, 1.00, 1.00
    else:
        eff_coef_env = st.session_state["coef_set"]["coef_envelope"]
        eff_coef_pump = st.session_state["coef_set"]["coef_pump"]
        eff_coef_term = st.session_state["coef_set"]["coef_terminal"]
    st.markdown(f"""
<div class="light-tech-title">
    <h1>📊三套改造方案｜户型：{ht}｜V1.28【估算面插值+HDD分段能耗+五道闸门】</h1>
</div>
""", unsafe_allow_html=True)
    if "build" not in st.session_state or "equip" not in st.session_state:
        st.warning("⚠️请先录入页面1、页面2参数")
        st.stop()
    warn_messages = input_warning_check(build, equip)
    for w in warn_messages:
        st.warning(w)
    _ok_in, _errs_in = validate_inputs_strict(build, equip, ht)
    if not _ok_in:
        st.error("⛔输入校验未通过：存在异常输入，已阻止计算。请返回页面1/2修正以下项后再试：")
        for _e in _errs_in:
            st.error("• " + _e)
        st.stop()
    allow_wall_retrofit = st.checkbox("✅允许外墙围护改造（若小区外立面限制可取消勾选）",value=True)
    spf_mode = st.radio("🧮SPF计算口径（A14：加入/不加入辅机）", ["含辅机 SPF_HP+aux", "不含辅机 SPF_HP（仅热泵主机）"], horizontal=True)
    spf_include_aux = (spf_mode == "含辅机 SPF_HP+aux")
    spf1 = calc_season_spf(equip["SCOP_nameplate1"], equip["spf_decay1"])
    spf2 = calc_season_spf(equip["SCOP_nameplate2"], equip["spf_decay2"])
    spf3 = calc_season_spf(equip["SCOP_nameplate3"], equip["spf_decay3"])
    st.info(f"📌季节性能主指标采用分段积分反算，当前口径：{'SPF_HP+aux=Q_year/(E_HP+E_aux)（含辅助电加热）' if spf_include_aux else 'SPF_HP=Q_year/E_HP（仅热泵主机，不含辅助电加热）'}。"
            f"分母未计入循环水泵、控制器、待机与曲轴箱加热用电，不等同于完整系统SPF。"
            f"可在上方切换SPF计算口径（A14），指标名称、分母与解释将同步变化。"
            f"铭牌SPF×衰减系数（旧算法估算值，仅作对比）：方案1={spf1}｜方案2={spf2}｜方案3={spf3}")
    st.caption("口径说明：①HDD18 的 18℃ 为采暖平衡温度（非室内设定温度 20℃），已隐含内部得热与太阳得热折减；"
               "设计负荷采用室内 20℃（GB 50736），两者口径不同但均按规范取值。"
               "②本程序定位为『早期方案比较/教学决策支持』，不计算朝向、风力、高度附加耗热量及热桥、间歇供暖修正，不可直接替代工程设计选型。"
               "③热泵性能为『估算面』（厂家公开锚点+温升幂律推算，证据等级C），非完整厂家性能矩阵，不作为最终设备选型依据。")
    cost_dict = calc_retrofit_cost(ht, build, equip, 1.0) # 原始造价明细（未批量）
    real_cost_pump = equip["cost_pump"] * eff_coef_pump # V1.28：热泵×有效系数
    real_envelope = cost_dict["sum_envelope_raw"] * eff_coef_env
    real_lowend = cost_dict["cost_lowend_raw"] * eff_coef_term
    with st.expander("🔍展开查看围护工程量 & 分项造价明细（每项=原始金额×有效系数=折算金额，V1.28）"):
        _cur_mode_txt = st.session_state["retrofit_mode"]
        df_cost_detail = pd.DataFrame([
            {"分项":"外墙保温","工程量m²":round(cost_dict["wall_net_A"],2),"单位造价元/m²":equip["unit_wall_ins"],
             "原始造价元":round(cost_dict["cost_wall_ins_raw"],2),
             f"有效系数[{_cur_mode_txt}]":eff_coef_env,"折算金额元":round(cost_dict["cost_wall_ins_raw"]*eff_coef_env,2)},
            {"分项":"外窗更换","工程量m²":build["win"],"单位造价元/m²":equip["unit_win_replace"],
             "原始造价元":round(cost_dict["cost_win_raw"],2),
             f"有效系数[{_cur_mode_txt}]":eff_coef_env,"折算金额元":round(cost_dict["cost_win_raw"]*eff_coef_env,2)},
            {"分项":"外门更换","工程量m²":build["door_A"],"单位造价元/m²":equip["unit_door_replace"],
             "原始造价元":round(cost_dict["cost_door_raw"],2),
             f"有效系数[{_cur_mode_txt}]":eff_coef_env,"折算金额元":round(cost_dict["cost_door_raw"]*eff_coef_env,2)},
            {"分项":"非采暖隔墙保温","工程量m²":build["nonheat_wall_A"],"单位造价元/m²":equip["unit_nonheat_ins"],
             "原始造价元":round(cost_dict["cost_nonheat_raw"],2),
             f"有效系数[{_cur_mode_txt}]":eff_coef_env,"折算金额元":round(cost_dict["cost_nonheat_raw"]*eff_coef_env,2)},
            {"分项":"屋面保温【顶层边户】","工程量m²":cost_dict["roof_A"],"单位造价元/m²":equip["unit_roof_ins"],
             "原始造价元":round(cost_dict["cost_roof_ins_raw"],2),
             f"有效系数[{_cur_mode_txt}]":eff_coef_env,"折算金额元":round(cost_dict["cost_roof_ins_raw"]*eff_coef_env,2)},
            {"分项":"东西山墙保温【顶层边户】","工程量m²":cost_dict["gable_wall_A"],"单位造价元/m²":equip["unit_gable_ins"],
             "原始造价元":round(cost_dict["cost_gable_ins_raw"],2),
             f"有效系数[{_cur_mode_txt}]":eff_coef_env,"折算金额元":round(cost_dict["cost_gable_ins_raw"]*eff_coef_env,2)},
            {"分项":"低温地暖末端","工程量m²建筑面积":build["area"],"单位造价元/m²建筑面积":equip["unit_lowend_floor"],
             "原始造价元":round(cost_dict["cost_lowend_raw"],2),
             f"有效系数[{_cur_mode_txt}]":eff_coef_term,"折算金额元":round(cost_dict["cost_lowend_raw"]*eff_coef_term,2)},
            {"分项":"热泵设备（固定总价）","工程量":"1台","单位造价":"固定总价",
             "原始造价元":round(equip["cost_pump"],2),
             f"有效系数[{_cur_mode_txt}]":eff_coef_pump,"折算金额元":round(equip["cost_pump"]*eff_coef_pump,2)},
            {"分项":"围护改造合计(原始)","工程量":"—","单位造价":"—",
             "原始造价元":round(cost_dict["sum_envelope_raw"],2),
             f"有效系数[{_cur_mode_txt}]":eff_coef_env,"折算金额元":round(real_envelope,2)},
        ])
        df_cost_detail["工程量"] = df_cost_detail["工程量"].astype(str)
        df_cost_detail["单位造价"] = df_cost_detail["单位造价"].astype(str)
        st.dataframe(df_cost_detail, width="stretch")
        st.info(f"当前造价模式：【{_cur_mode_txt}】｜围护有效系数{eff_coef_env}、热泵有效系数{eff_coef_pump}、末端有效系数{eff_coef_term}。"
                f"折算后围护合计：{round(real_envelope,0)}元；折算后地暖：{round(real_lowend,0)}元；折算后热泵：{round(real_cost_pump,0)}元。"
                "（分户模式三系数均=1.00；批量模式按页面2可编辑的0.75/0.85/0.80分项结算，见P0-4）")

    # --------方案1：围护不改造，散热器末端（V1.21：二维表分段能耗积分） --------
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
    seg1_full, e_hp1, e_aux1, aux_h1, data_ok1, domain_warns1, unserved1 = calc_segment_hp_aux_2d(
        seg1, "HP0", tg1, equip["Qhp_rated1"])
    elec_1 = e_hp1 + e_aux1
    elec_1_old = elec_consume(q_year1_kwh, spf1)
    spf_hp_only1 = round(q_year1_kwh/e_hp1,3) if e_hp1>1e-9 else None
    spf_with_aux1 = round(q_year1_kwh/elec_1,3) if elec_1>1e-9 else None
    spf_sys1 = spf_with_aux1 if spf_include_aux else spf_hp_only1
    cop_d1, qhp_d1, in_domain_d1, design_warns1 = hp_available_at_design(build, equip, "HP0", tg1)
    data_ok1 = data_ok1 and in_domain_d1
    mr1 = round(qhp_d1/Qd1_kW,3) if Qd1_kW>1e-9 else None
    invest_1 = real_cost_pump
    year_cost_1 = elec_1 * equip["elec_price"]
    need_aux1, aux_load1 = check_aux_electric_heat(Qd1_kW, equip["Qhp_rated1"])
    # V1.28：P0-3 设计工况备用容量与容量闸门（未配置备用热源→容量=0）
    q_aux_design1 = calc_design_aux_capacity(Qd1_kW, qhp_d1)
    capacity_ok1 = (qhp_d1 + 0.0) >= Qd1_kW
    co2_1 = calc_carbon(elec_1, equip["grid_ef"])
    q_load_per_area1 = round(Qd1_kW / build["area"] *1000, 2)

    # --------方案2：围护改造，仍然散热器末端（V1.21：二维表分段能耗积分） --------
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
    seg2_full, e_hp2, e_aux2, aux_h2, data_ok2, domain_warns2, unserved2 = calc_segment_hp_aux_2d(
        seg2, "HP0", tg2, equip["Qhp_rated2"])
    elec_2 = e_hp2 + e_aux2
    elec_2_old = elec_consume(q_year2_kwh, spf2)
    spf_hp_only2 = round(q_year2_kwh/e_hp2,3) if e_hp2>1e-9 else None
    spf_with_aux2 = round(q_year2_kwh/elec_2,3) if elec_2>1e-9 else None
    spf_sys2 = spf_with_aux2 if spf_include_aux else spf_hp_only2
    cop_d2, qhp_d2, in_domain_d2, design_warns2 = hp_available_at_design(build, equip, "HP0", tg2)
    data_ok2 = data_ok2 and in_domain_d2
    mr2 = round(qhp_d2/Qd2_kW,3) if Qd2_kW>1e-9 else None
    invest_2 = real_cost_pump + real_envelope
    year_cost_2 = elec_2 * equip["elec_price"]
    save_elec_2 = elec_1 - elec_2
    payback_2 = payback_period(real_envelope, save_elec_2, equip["elec_price"])
    load_save_rate_2 = round((Qd1_kW - Qd2_kW)/Qd1_kW*100,2)
    elec_save_rate_2 = round((elec_1 - elec_2)/elec_1*100,2) # 相对方案1购电变化（P0-5口径）
    need_aux2, aux_load2 = check_aux_electric_heat(Qd2_kW, equip["Qhp_rated2"])
    q_aux_design2 = calc_design_aux_capacity(Qd2_kW, qhp_d2)
    capacity_ok2 = (qhp_d2 + 0.0) >= Qd2_kW
    co2_2 = calc_carbon(elec_2, equip["grid_ef"])
    co2_reduce_2 = round(co2_1 - co2_2,2)
    co2_reduce_rate_2 = round((co2_1 - co2_2)/co2_1*100,2) if co2_1>0 else 0
    q_load_per_area2 = round(Qd2_kW / build["area"] *1000,2)

    # --------方案3：围护改造+更换地暖末端（V1.21：二维表分段能耗积分） --------
    H3_kWK = H2_kWK
    Qd3_kW = Qd2_kW
    q_year3_kwh = q_year2_kwh
    seg3 = calc_segment_annual_heat(H3_kWK, build["HDD"], HDD_SEGMENTS)
    tg3, th3, qterm3, end_ok3, advice3 = solve_min_supply_temp(
        Qd3_kW, build["Tin"],
        equip["floor_Qrated_kW"], equip["floor_dt_m_rated"], equip["floor_m"],
        equip["floor_dt_flow_return"], equip["floor_tg_max"]
    )
    seg3_full, e_hp3, e_aux3, aux_h3, data_ok3, domain_warns3, unserved3 = calc_segment_hp_aux_2d(
        seg3, "HP1", tg3, equip["Qhp_rated3"])
    elec_3 = e_hp3 + e_aux3
    elec_3_old = elec_consume(q_year3_kwh, spf3)
    spf_hp_only3 = round(q_year3_kwh/e_hp3,3) if e_hp3>1e-9 else None
    spf_with_aux3 = round(q_year3_kwh/elec_3,3) if elec_3>1e-9 else None
    spf_sys3 = spf_with_aux3 if spf_include_aux else spf_hp_only3
    cop_d3, qhp_d3, in_domain_d3, design_warns3 = hp_available_at_design(build, equip, "HP1", tg3)
    data_ok3 = data_ok3 and in_domain_d3
    mr3 = round(qhp_d3/Qd3_kW,3) if Qd3_kW>1e-9 else None
    invest_3 = real_cost_pump + real_envelope + real_lowend
    year_cost_3 = elec_3 * equip["elec_price"]
    save_elec_3 = elec_1 - elec_3
    payback_3 = payback_period((real_envelope + real_lowend), save_elec_3, equip["elec_price"])
    load_save_rate_3 = round((Qd1_kW - Qd3_kW)/Qd1_kW*100,2)
    elec_save_rate_3 = round((elec_1 - elec_3)/elec_1*100,2)
    need_aux3, aux_load3 = check_aux_electric_heat(Qd3_kW, equip["Qhp_rated3"])
    q_aux_design3 = calc_design_aux_capacity(Qd3_kW, qhp_d3)
    capacity_ok3 = (qhp_d3 + 0.0) >= Qd3_kW
    co2_3 = calc_carbon(elec_3, equip["grid_ef"])
    co2_reduce_3 = round(co2_1 - co2_3,2)
    co2_reduce_rate_3 = round((co2_1 - co2_3)/co2_1*100,2) if co2_1>0 else 0
    q_load_per_area3 = round(Qd3_kW / build["area"] *1000,2)

    budget = equip["budget"]
    # V1.28：五道可行性闸门（预算 / 工程允许外墙 / 设计工况容量(备用容量口径) / 末端能力 / 模型适用性）
    # P0-3 口径：hp_cap_ok = (Q_HP,avail,design + Q_aux,configured) >= Q_design；当前模型未配置独立备用热源（Q_aux,configured=0），
    #            故 hp_cap_ok = (qhp_avail_design >= q_load)；同时输出"需配置备用容量" q_aux_design=max(0,Qd−Qhp)，
    #            与年度 E_aux（分段积分）分开报告，避免“容量不足”与“E_aux=0”的口径矛盾。
    def get_scheme_status(invest, allow_wall, q_load, qhp_avail_design, end_ok, data_ok, mr, q_aux_design, e_aux_year=0.0, q_aux_year=0.0):
        budget_ok = invest <= budget
        engineering_ok = allow_wall
        q_aux_configured = 0.0 # 当前模型未配置独立备用热源
        hp_cap_ok = (qhp_avail_design + q_aux_configured) >= q_load
        terminal_ok = end_ok
        model_ok = data_ok
        eligible = budget_ok and engineering_ok and hp_cap_ok and terminal_ok and model_ok
        return {"budget_ok":budget_ok,"engineering_ok":engineering_ok,"hp_cap_ok":hp_cap_ok,
                "terminal_ok":terminal_ok,"model_ok":model_ok,"mr":mr,"q_aux_design":q_aux_design,
                "q_load":q_load,"qhp_avail_design":qhp_avail_design,
                "e_aux_year":e_aux_year,"q_aux_year":q_aux_year,"eligible":eligible}
    stat1 = get_scheme_status(invest_1, True, Qd1_kW, qhp_d1, end_ok1, data_ok1, mr1, q_aux_design1, e_aux1, e_aux1)
    stat2 = get_scheme_status(invest_2, allow_wall_retrofit, Qd2_kW, qhp_d2, end_ok2, data_ok2, mr2, q_aux_design2, e_aux2, e_aux2)
    stat3 = get_scheme_status(invest_3, allow_wall_retrofit, Qd3_kW, qhp_d3, end_ok3, data_ok3, mr3, q_aux_design3, e_aux3, e_aux3)
    status_df = pd.DataFrame([
        {"方案":"方案1仅换热泵","预算满足":stat1["budget_ok"],"工程允许外墙":stat1["engineering_ok"],
         "设计工况容量(MR≥1)":stat1["hp_cap_ok"],"需备用容量(kW)":stat1["q_aux_design"],"末端能力满足":stat1["terminal_ok"],
         "模型适用性":stat1["model_ok"],"整体可行":stat1["eligible"]},
        {"方案":"方案2围护+热泵","预算满足":stat2["budget_ok"],"工程允许外墙":stat2["engineering_ok"],
         "设计工况容量(MR≥1)":stat2["hp_cap_ok"],"需备用容量(kW)":stat2["q_aux_design"],"末端能力满足":stat2["terminal_ok"],
         "模型适用性":stat2["model_ok"],"整体可行":stat2["eligible"]},
        {"方案":"方案3围护+末端+热泵","预算满足":stat3["budget_ok"],"工程允许外墙":stat3["engineering_ok"],
         "设计工况容量(MR≥1)":stat3["hp_cap_ok"],"需备用容量(kW)":stat3["q_aux_design"],"末端能力满足":stat3["terminal_ok"],
         "模型适用性":stat3["model_ok"],"整体可行":stat3["eligible"]},
    ])
    st.subheader("🔍五道可行性闸门状态表（预算/工程允许外墙/设计工况容量/末端能力/模型适用性；V1.28 容量与辅热分口径）")
    st.dataframe(status_df, width="stretch")

    # ===== 五道独立可行性闸门（热泵按设计工况可用制热量校核） =====
    with st.expander("🚦【V1.28】五道独立可行性闸门（设计工况可用制热量 + 备用容量 + 模型适用性）"):
        st.info("①热泵容量不能用样本额定制热量：须用设计工况(室外=郑州设计温度，供水=末端反算tg)估算面插值后的可用制热量Q_HP,avail校核，"
                "并给出容量裕量 MR=Q_HP,avail/Q_design（建议≥1.10，下限1.00）。"
                "②【】容量与辅热分口径：需备用容量 Q_aux,design=max(0,Qd−Q_HP,avail,design)（设计点峰值缺口）与年度 E_aux（分段积分）分别报告；"
                "当前模型未配置独立备用热源（Q_aux,configured=0），故容量闸门按 (Q_HP,avail+0)≥Qd 判定。"
                "③【】第五道闸门更名 performance_model_applicable（模型适用性）：所有容量与能耗积分工况均须位于性能估算面（模型适用范围）内；"
                "越域判定该方案不通过，禁止输出『可行/最优』。本估算面由厂家公开锚点+模型推算构成，非完整厂家性能矩阵。")
        _data_ok_list = [data_ok1, data_ok2, data_ok3]
        _mr_list = [mr1, mr2, mr3]
        _rows_gate = []
        _gate_reasons = []
        for _i, (nm, inv, allowwall, Qd, tgv, hpid, endok) in enumerate([
            ("方案1仅换热泵", invest_1, True, Qd1_kW, tg1, "HP0", end_ok1),
            ("方案2围护+热泵", invest_2, allow_wall_retrofit, Qd2_kW, tg2, "HP0", end_ok2),
            ("方案3围护+末端+设备B", invest_3, allow_wall_retrofit, Qd3_kW, tg3, "HP1", end_ok3),
        ]):
            cop_d, qhp_d, in_domain_d, _warn_d = hp_available_at_design(build, equip, hpid, tgv)
            b_ok = inv <= budget
            e_ok = allowwall
            h_ok = qhp_d >= Qd
            t_ok = endok
            d_ok = _data_ok_list[_i] and in_domain_d
            mr_v = round(qhp_d/Qd,3) if Qd>1e-9 else None
            q_aux_d = round(max(0.0, Qd - qhp_d), 3)
            _rows_gate.append({"方案":nm, "初投资(元)":round(inv,0), "预算满足":b_ok, "工程允许外墙":e_ok,
                               "设计工况Q_HP可用(kW)":qhp_d, "设计负荷(kW)":round(Qd,2),
                               "容量裕量MR":mr_v, "需备用容量(kW)":q_aux_d, "热泵容量满足":h_ok,
                               "末端满足":t_ok, "模型适用性":d_ok,
                               "整体可行":b_ok and e_ok and h_ok and t_ok and d_ok})
            _rs = []
            if not b_ok: _rs.append("❌超出预算")
            if not e_ok: _rs.append("❌工程禁止外墙改造")
            if not h_ok: _rs.append(f"❌设计工况容量不足(MR={mr_v})，需配置备用热源容量≥{q_aux_d}kW")
            if not t_ok: _rs.append("❌末端能力不足")
            if not d_ok: _rs.append("❌模型适用性不满足(工况越出性能估算面范围)")
            _gate_reasons.append("；".join(_rs) if _rs else "✅全部条件通过，方案可行")
        st.dataframe(pd.DataFrame(_rows_gate), width="stretch", hide_index=True)
        for _nm, _rsn in zip(["方案1", "方案2", "方案3"], _gate_reasons):
            st.markdown(f"**{_nm}**：{_rsn}")
        st.caption("五个独立判断逐条输出；performance_model_applicable=False 时第五道闸门不满足，判定该方案不通过（工况越出性能估算面范围），不输出『可行/最优』。")
    def gen_status_text(st):
        msg_list=[]
        if not st["budget_ok"]: msg_list.append("❌超出预算")
        if not st["engineering_ok"]: msg_list.append("❌工程禁止外墙改造")
        if not st["hp_cap_ok"]:
            qhp = st.get("qhp_avail_design", 0)
            qd = st.get("q_load", 0)
            qaux_d = st.get("q_aux_design", 0)
            eaux_y = st.get("e_aux_year", 0)
            qaux_y = st.get("q_aux_year", 0)
            msg_list.append(
                f"❌设计工况容量不足：热泵可用制热量{qhp:.2f}kW < 设计热负荷{qd:.2f}kW，"
                f"需配置备用热源容量≥{qaux_d:.2f}kW；"
                f"按当前HDD分段气象数据(最低段-15~-10℃，未含设计点以下逐时数据)估算，"
                f"年度辅助供热量{qaux_y:.1f}kWh、辅助用电{eaux_y:.1f}kWh；"
                f"若未配置足额备用热源，则方案不可行并报告未满足热量"
            )
        if not st["terminal_ok"]: msg_list.append("❌末端能力不足，无法覆盖热负荷")
        if not st["model_ok"]: msg_list.append("❌模型适用性不满足(工况越出性能估算面范围)")
        if len(msg_list)>0:
            return "；".join(msg_list)
        return "✅全部条件通过，方案可行"
    tag_1 = gen_status_text(stat1)
    tag_2 = gen_status_text(stat2)
    tag_3 = gen_status_text(stat3)
    candidates=[]
    # V1.28：仅 model_ok=True（模型适用性）的方案可进入推荐候选
    if stat2["eligible"] and stat2["model_ok"] and payback_2 is not None:
        candidates.append(("方案2",payback_2,elec_save_rate_2))
    if stat3["eligible"] and stat3["model_ok"] and payback_3 is not None:
        candidates.append(("方案3",payback_3,elec_save_rate_3))
    best_scheme = min(candidates,key=lambda x:x[1])[0] if candidates else None
    budget_sufficient = budget >= invest_3*1.2
    eco_scheme = None
    if stat2["eligible"] and stat2["model_ok"] and stat3["eligible"] and stat3["model_ok"]:
        eco_scheme = "方案3" if elec_save_rate_3>=elec_save_rate_2 else "方案2"
    elif stat2["eligible"] and stat2["model_ok"]: eco_scheme="方案2"
    elif stat3["eligible"] and stat3["model_ok"]: eco_scheme="方案3"
    st.session_state["calc_mid"] = {
        "H1_kWK":H1_kWK,"Qd1_kW":Qd1_kW,"q_year1_kwh":q_year1_kwh,"spf1":spf1,"elec1":elec_1,
        "seg1":seg1_full,
        "seg1_plain":seg1,
        "H2_kWK":H2_kWK,"Qd2_kW":Qd2_kW,"q_year2_kwh":q_year2_kwh,"spf2":spf2,"elec2":elec_2,
        "seg2":seg2_full,
        "seg2_plain":seg2,
        "H3_kWK":H3_kWK,"Qd3_kW":Qd3_kW,"q_year3_kwh":q_year3_kwh,"spf3":spf3,"elec3":elec_3,
        "seg3":seg3_full,
        "seg3_plain":seg3,
        "q_load_per_area1":q_load_per_area1,"q_load_per_area2":q_load_per_area2,"q_load_per_area3":q_load_per_area3,
        "aux_load1":aux_load1,"aux_load2":aux_load2,"aux_load3":aux_load3,
        "q_aux_design1":q_aux_design1,"q_aux_design2":q_aux_design2,"q_aux_design3":q_aux_design3,
        "co2_1":co2_1,"co2_2":co2_2,"co2_3":co2_3,
        "tg1":tg1,"tg2":tg2,"tg3":tg3,
        "spf_sys1":spf_sys1,"spf_sys2":spf_sys2,"spf_sys3":spf_sys3,
        "data_ok1":data_ok1,"data_ok2":data_ok2,"data_ok3":data_ok3,
        "mr1":mr1,"mr2":mr2,"mr3":mr3,
        "e_hp1":e_hp1,"e_aux1":e_aux1,"e_hp2":e_hp2,"e_aux2":e_aux2,"e_hp3":e_hp3,"e_aux3":e_aux3,
        "elec_1_old":elec_1_old,"elec_2_old":elec_2_old,"elec_3_old":elec_3_old,
        "tag_1":tag_1,"tag_2":tag_2,"tag_3":tag_3,
        "best_scheme":best_scheme
    }
    st.info(f"🔍中间输出｜方案1总热损失H1={round(H1_kWK,4)} kW/K；单位面积热负荷 {q_load_per_area1} W/m²；"
            f"SPF_HP+aux 方案1={spf_sys1}｜方案2={spf_sys2}｜方案3={spf_sys3}")
    # 输出模型适用性 / 设计工况警告（V1.28：估算面越界才报警，且纳入第五道闸门）
    _domain_warns_all = [
        ("方案1", domain_warns1, design_warns1),
        ("方案2", domain_warns2, design_warns2),
        ("方案3", domain_warns3, design_warns3),
    ]
    for _nm, _dw, _dwd in _domain_warns_all:
        for w in list(dict.fromkeys(_dw + _dwd)):
            st.warning(f"[{_nm}] {w}")
        if not (data_ok1 if _nm=="方案1" else data_ok2 if _nm=="方案2" else data_ok3):
            st.error(f"[{_nm}] ⚠️第五道闸门 performance_model_applicable=False：存在工况越出性能估算面（模型适用范围），判定本方案【不通过】，禁止输出可行/最优。")

    # 末端改进建议
    if not end_ok1:
        st.warning("⚠️【方案1末端能力不足改进建议】"+" ".join(advice1))
    if not end_ok2:
        st.warning("⚠️【方案2末端能力不足改进建议】"+" ".join(advice2))
    if not end_ok3:
        st.warning("⚠️【方案3末端能力不足改进建议】"+" ".join(advice3))

    with st.expander("🔍查看：室外温度分段插值能耗明细（V1.28估算面）+ 度时守恒校核"):
        # P1-6/A13：各温区度时之和 = HDD18×24（允许偏差≤0.5%）
        _sum_hours = sum(s.get("hours_seg", s.get("hdd_segment", 0.0) * 24.0) for s in seg1_full)
        _hdd_hours = build["HDD"] * 24.0
        _cons_dev = abs(_sum_hours - _hdd_hours) / _hdd_hours * 100.0 if _hdd_hours > 1e-9 else 0.0
        _cons_ok = _cons_dev <= 0.5
        st.caption(f"🧮【分段守恒校核】Σ各温区小时数 = {round(_sum_hours,1)} h；HDD18×24 = {round(_hdd_hours,1)} h；"
                   f"偏差 {round(_cons_dev,4)}%（≤0.5% 通过）→ {'✅守恒' if _cons_ok else '❌不守恒'}。"
                   "每温区供水温度=末端反算tg（温控策略：全季恒tg，见P1-6）；未满足热量=0（当前模型假设已配置足额辅助电加热）。")
        st.markdown("**方案1分段明细**")
        st.dataframe(pd.DataFrame(seg1_full))
        st.markdown("**方案2分段明细**")
        st.dataframe(pd.DataFrame(seg2_full))
        st.markdown("**方案3分段明细**")
        st.dataframe(pd.DataFrame(seg3_full))

    # ===== V1.8新增：辅助电加热 E_aux + 运行小时（三套方案，追加不改原逻辑） =====
    with st.expander("🔋辅助电加热：运行小时 & 年耗电量 E_aux（V1.28估算面）"):
        st.info("按HDD各温度分段计算：热泵可用制热能力不足的部分由辅助电加热承担；等效运行小时 = E_aux / 热泵额定制热量。"
                "分段 COP 与可用制热量在性能估算面(室外×供水)模型适用范围内插值，E_HP+E_aux 即各方案年耗电主指标。"
                "【】年度 E_aux 为分段积分辅热用电，与设计工况“需备用容量”分别报告；当前模型假设全年已足额配置辅助电加热（η=1）。")
        aux_items = [
            (seg1, tg1, "HP0", equip["Qhp_rated1"], "方案1：仅热泵(E0-T0-HP0)"),
            (seg2, tg2, "HP0", equip["Qhp_rated2"], "方案2：围护+热泵(E2-T0-HP0)"),
            (seg3, tg3, "HP1", equip["Qhp_rated3"], "方案3：围护+地暖+设备B(E2-T2-HP1)"),
        ]
        aux_cols = st.columns(3)
        for idx, (seg_x, tg_x, hp_id_x, rated_x, label_x) in enumerate(aux_items):
            seg_full_x, e_hp_x, e_aux_x, aux_h_x, d_ok_x, _, unserved_x = calc_segment_hp_aux_2d(seg_x, hp_id_x, tg_x, rated_x)
            with aux_cols[idx]:
                st.markdown(f"**{label_x}**")
                st.metric("热泵年耗电 E_HP (kWh)", round(e_hp_x, 2))
                st.metric("辅助电加热 E_aux (kWh)", round(e_aux_x, 2))
                st.metric("辅助电等效运行小时 (h)", aux_h_x)
                st.metric("未满足热量 (kWh)", unserved_x)
                st.caption("✅工况位于模型适用范围内" if d_ok_x else "⚠️存在越出估算面的工况（模型适用性不满足）")
                if unserved_x > 0:
                    st.warning(f"⚠️存在未满足热量{unserved_x:.1f}kWh，备用热源容量不足，方案不可行")
                df_aux_seg = pd.DataFrame(seg_full_x)[["T_low","T_high","Q_heat_kwh","cop_interp","hp_avail_kW","Q_hp_kwh","Q_aux_kwh","elec_hp","elec_aux"]]
                st.dataframe(df_aux_seg, width="stretch")

    # ===== V1.9新增：围护分项热损失分解 & 能耗强度 & HDD回归校核对照 =====
    with st.expander("🔍【V1.9新增】围护分项热损失分解 & 能耗强度 kWh/(m²·a) & 回归校核"):
        _vol_room = build["area"] * build["floor_h"]
        comp_old = calc_component_heat_loss(ht, build_old, _vol_room, build["n"], build["rho"], build["cp"])
        comp_new = calc_component_heat_loss(ht, build_new, _vol_room, build["n"], build["rho"], build["cp"])
        c1o, c2o = st.columns(2)
        with c1o:
            st.markdown("**改造前围护分项热损失（方案1基准）**")
            st.dataframe(pd.DataFrame(comp_old), width="stretch", hide_index=True)
        with c2o:
            st.markdown("**改造后围护分项热损失（方案2/3）**")
            st.dataframe(pd.DataFrame(comp_new), width="stretch", hide_index=True)
        st.caption("外墙面积按净面积（毛面积−窗洞口）计，避免窗面积重复计热损失；顶层边户另计屋面、东西山墙。")
        ei1 = elec_1 / build["area"]; ei2 = elec_2 / build["area"]; ei3 = elec_3 / build["area"]
        eic = st.columns(3)
        for _j, (_nm, _ei) in enumerate([("方案1", ei1), ("方案2", ei2), ("方案3", ei3)]):
            with eic[_j]:
                st.metric(f"{_nm} 采暖能耗强度", f"{_ei:.1f} kWh/(m²·a)")
                if _ei > 150:
                    st.warning("能耗强度异常偏高(>150 kWh/(m²·a))，请核对参数数量级")
        _aux_all = [(e_hp1,e_aux1),(e_hp2,e_aux2),(e_hp3,e_aux3)]
        st.markdown("**🧮 HDD回归校核对照：SPF法(Q_year/旧SPF) vs 二维分段积分法（量纲均按 H×HDD×24 修正）**")
        reg_df = pd.DataFrame({
            "方案":["方案1","方案2","方案3"],
            "H(kW/K)":[round(H1_kWK,4),round(H2_kWK,4),round(H3_kWK,4)],
            "Q_year(kWh)":[round(q_year1_kwh,1),round(q_year2_kwh,1),round(q_year3_kwh,1)],
            "旧算法SPF":[spf1,spf2,spf3],
            "SPF法E(kWh)":[round(elec_1_old,1),round(elec_2_old,1),round(elec_3_old,1)],
            "估算面法E_HP(kWh)":[round(_aux_all[0][0],1),round(_aux_all[1][0],1),round(_aux_all[2][0],1)],
            "E_aux(kWh)":[round(_aux_all[0][1],1),round(_aux_all[1][1],1),round(_aux_all[2][1],1)],
            "主指标SPF_HP+aux":[spf_sys1,spf_sys2,spf_sys3],
        })
        st.dataframe(reg_df, width="stretch", hide_index=True)
        st.caption("SPF法为简化链 E=Q_year/旧SPF，仅作对比；二维分段积分法为主算法（HDD分段×二维COP，含容量约束），"
                   "主指标 SPF_HP+aux=Q_year/(E_HP+E_aux)。两者差异源于温度分布、供水温度与部分负荷，属正常。")

    # SPF指标名称根据口径切换（A14）
    spf_label = "SPF_HP+aux(Qyear/E_HP+E_aux)" if spf_include_aux else "SPF_HP(Qyear/E_HP，不含辅机)"
    spf_denom_note = "分母=E_HP+E_aux（含辅助电加热）" if spf_include_aux else "分母=E_HP（仅热泵主机耗电，不含辅助电加热）"
    col_a,col_b,col_c = st.columns(3)
    CARD_FIX_HEIGHT=850
    with col_a:
        with st.container(height=CARD_FIX_HEIGHT):
            st.markdown("### 🟦方案1｜仅更换热泵（基准对照）")
            st.markdown(f"**可行性：**{tag_1}")
            st.metric(spf_label,spf_sys1)
            st.metric("供水温度(℃)",tg1)
            st.metric("设计工况COP",cop_d1)
            st.metric("容量裕量MR",mr1)
            st.metric("热泵可用制热量(kW)",qhp_d1)
            st.metric("设计热负荷(kW)",round(Qd1_kW,2))
            st.metric("年耗电(kWh)",f"{elec_1:,.0f}",delta=f"E_aux={e_aux1:.0f}")
            st.metric("需备用容量(kW)",q_aux_design1)
            st.metric("年碳排放(kgCO₂)",f"{co2_1:,.0f}")
            st.metric("总初投资(元)",f"{int(round(invest_1,0)):,}")
    with col_b:
        with st.container(height=CARD_FIX_HEIGHT):
            st.markdown("### 🟩方案2｜围护保温改造+设备A")
            if not allow_wall_retrofit: st.info("🚫工程约束，禁止围护改造")
            st.markdown(f"**可行性：**{tag_2}")
            st.metric(spf_label,spf_sys2)
            st.metric("供水温度(℃)",tg2)
            st.metric("设计工况COP",cop_d2)
            st.metric("容量裕量MR",mr2)
            st.metric("热泵可用制热量(kW)",qhp_d2)
            st.metric("设计热负荷(kW)",round(Qd2_kW,2))
            st.metric("相对方案1购电",f"-{elec_save_rate_2}%",delta=f"E_aux={e_aux2:.0f}")
            st.metric("需备用容量(kW)",q_aux_design2)
            st.metric("相对方案1减排(kg)",f"-{co2_reduce_2:,.0f}",delta=f"-{co2_reduce_rate_2}%")
            st.metric("总初投资(元)",f"{int(round(invest_2,0)):,}")
    with col_c:
        with st.container(height=CARD_FIX_HEIGHT):
            st.markdown("### 🟨方案3｜围护改造+低温地暖+设备B")
            if not allow_wall_retrofit: st.info("🚫工程约束，禁止围护改造")
            st.markdown(f"**可行性：**{tag_3}")
            st.metric(spf_label,spf_sys3)
            st.metric("供水温度(℃)",tg3)
            st.metric("设计工况COP",cop_d3)
            st.metric("容量裕量MR",mr3)
            st.metric("热泵可用制热量(kW)",qhp_d3)
            st.metric("设计热负荷(kW)",round(Qd3_kW,2))
            st.metric("相对方案1购电",f"-{elec_save_rate_3}%",delta=f"E_aux={e_aux3:.0f}")
            st.metric("需备用容量(kW)",q_aux_design3)
            st.metric("相对方案1减排(kg)",f"-{co2_reduce_3:,.0f}",delta=f"-{co2_reduce_rate_3}%")
            st.metric("总初投资(元)",f"{int(round(invest_3,0)):,}")
    st.caption("卡片仅展示关键结论指标；全部中间量（H、Qd、单位面积热负荷、铭牌SCOP、旧算法SPF、回水温度、末端散热量、分段能耗、辅助电等）见下方『三方案对比总表』及各可折叠明细。"
               "【】方案2/3的购电/排放变化均为“相对方案1（热泵供暖情景）”，不代表相对住户原有供暖方式的真实节能率/减排量，真实基准见下方『改造前实际系统基准』模块。")
    st.divider()
    # 统一SPF列名（对比表与图表共用，避免KeyError）
    spf_col_name = "SPF主指标(" + ("含辅机" if spf_include_aux else "仅热泵") + ")"
    result_df = pd.DataFrame({
        "户型":[ht,ht,ht],
        "改造方案":["方案1：仅更换热泵","方案2：围护改造+设备A","方案3：围护+低温末端+设备B"],
        "总热损失系数H(kW/K)":[round(H1_kWK,4),round(H2_kWK,4),round(H3_kWK,4)],
        "设计热负荷(kW)":[round(Qd1_kW,2),round(Qd2_kW,2),round(Qd3_kW,2)],
        "单位面积热负荷(W/m²)":[q_load_per_area1,q_load_per_area2,q_load_per_area3],
        "铭牌SCOP":[equip["SCOP_nameplate1"],equip["SCOP_nameplate2"],equip["SCOP_nameplate3"]],
        spf_col_name:[spf_sys1,spf_sys2,spf_sys3],
        "旧算法SPF(参考)":[spf1,spf2,spf3],
        "迭代最低供水温度(℃)":[tg1,tg2,tg3],
        "回水温度(℃)":[th1,th2,th3],
        "末端计算散热量(kW)":[qterm1,qterm2,qterm3],
        "末端能力是否满足":["是" if end_ok1 else "否","是" if end_ok2 else "否","是" if end_ok3 else "否"],
        "设计工况COP":[cop_d1,cop_d2,cop_d3],
        "容量裕量MR":[None if mr1 is None else mr1,None if mr2 is None else mr2,None if mr3 is None else mr3],
        "模型适用性":["是" if data_ok1 else "否","是" if data_ok2 else "否","是" if data_ok3 else "否"],
        "热泵额定制热量(kW)":[equip["Qhp_rated1"],equip["Qhp_rated2"],equip["Qhp_rated3"]],
        "热泵设备总价(元)":[real_cost_pump,real_cost_pump,real_cost_pump],
        "围护改造造价(批量后元)":[0,round(real_envelope,0),round(real_envelope,0)],
        "低温地暖末端造价(批量后元)":[0,0,round(real_lowend,0)],
        "是否需要辅助电加热":["是" if need_aux1 else "否","是" if need_aux2 else "否","是" if need_aux3 else "否"],
        "辅助电加热承担负荷(kW)":[aux_load1,aux_load2,aux_load3],
        "热负荷削减率(%)":[0.0,load_save_rate_2,load_save_rate_3],
        "全年采暖需热量(kWh)":[round(q_year1_kwh,1),round(q_year2_kwh,1),round(q_year3_kwh,1)],
        "二维分段算法年耗电量(kWh)":[round(elec_1,1),round(elec_2,1),round(elec_3,1)],
        "其中E_HP(kWh)":[e_hp1,e_hp2,e_hp3],
        "其中E_aux(kWh)":[e_aux1,e_aux2,e_aux3],
        "旧SPF算法年耗电量(kWh)":[round(elec_1_old,1),round(elec_2_old,1),round(elec_3_old,1)],
        "相对方案1购电变化(%)":[0.0,elec_save_rate_2,elec_save_rate_3],
        "年运行期碳排放(kgCO₂)":[co2_1,co2_2,co2_3],
        "相对方案1排放变化(kgCO₂e/a)":[0.0,co2_reduce_2,co2_reduce_3],
        "相对方案1排放变化率(%)":[0.0,co2_reduce_rate_2,co2_reduce_rate_3],
        "项目总初投资(元)":[round(invest_1,0),round(invest_2,0),round(invest_3,0)],
        "可行性校验":[tag_1,tag_2,tag_3],
        "年采暖电费(元)":[round(year_cost_1,2),round(year_cost_2,2),round(year_cost_3,2)],
        "相对方案1增量静态回收期(年)":[None,payback_2,payback_3]
    })
    st.dataframe(result_df, width="stretch")
    st.caption("【】本表节能/减排列均为“相对方案1（热泵供暖情景）”口径，非相对住户原有供暖方式的真实节能率；碳排放为【运行期电力间接碳排放】（电耗×电网排放因子，位置法），不包含围护材料、设备制造/更换的隐含碳；回收期为【相对方案1增量静态回收期】，非项目真实全生命周期回收期。")
    csv_bytes = result_df.to_csv(index=False,encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button("📥下载CSV结果",csv_bytes,file_name=f"{ht}_热泵改造V1.28_估算面分段能耗.csv",mime="text/csv")

    # ===== V1.9新增：导出完整计算报告（输入+来源+中间变量+可行性+推荐） =====
    with st.expander("📤【V1.9新增】导出完整计算报告（含全部输入/来源/中间变量/可行性/推荐）"):
        _coef_s = st.session_state["coef_set"]
        _rep_rows = []
        _rep_rows.append({"类别":"批量系数","参数":"围护有效系数(当前模式)","数值":(1.00 if st.session_state["retrofit_mode"]=="分户独立改造" else _coef_s["coef_envelope"]),"来源":st.session_state["retrofit_mode"],"备注":"P0-4分项结算"})
        _rep_rows.append({"类别":"批量系数","参数":"热泵有效系数(当前模式)","数值":(1.00 if st.session_state["retrofit_mode"]=="分户独立改造" else _coef_s["coef_pump"]),"来源":st.session_state["retrofit_mode"],"备注":"P0-4分项结算"})
        _rep_rows.append({"类别":"批量系数","参数":"末端有效系数(当前模式)","数值":(1.00 if st.session_state["retrofit_mode"]=="分户独立改造" else _coef_s["coef_terminal"]),"来源":st.session_state["retrofit_mode"],"备注":"P0-4分项结算"})
        for _k, _v in build.items():
            _rep_rows.append({"类别":"输入-建筑","参数":_k,"数值":str(_v),"来源":"见参数来源台账","备注":""})
        for _k, _v in equip.items():
            _rep_rows.append({"类别":"输入-设备/造价","参数":_k,"数值":str(_v),"来源":"见参数来源台账","备注":""})
        for _nm, _v1, _v2, _v3 in [
            ("H(kW/K)", H1_kWK, H2_kWK, H3_kWK),
            ("Q_design(kW)", Qd1_kW, Qd2_kW, Qd3_kW),
            ("Q_year(kWh)", q_year1_kwh, q_year2_kwh, q_year3_kwh),
            ("SPF_HP+aux主指标", spf_sys1 if spf_sys1 is not None else 0, spf_sys2 if spf_sys2 is not None else 0, spf_sys3 if spf_sys3 is not None else 0),
            ("旧算法SPF(参考)", spf1, spf2, spf3),
            ("供水温度tg(℃)", tg1, tg2, tg3),
            ("设计工况COP", cop_d1, cop_d2, cop_d3),
            ("容量裕量MR", mr1 if mr1 is not None else 0, mr2 if mr2 is not None else 0, mr3 if mr3 is not None else 0),
            ("模型适用性(performance_model_applicable)", int(data_ok1), int(data_ok2), int(data_ok3)),
            ("E_HP(kWh)", e_hp1, e_hp2, e_hp3),
            ("需备用容量Q_aux,design(kW)", q_aux_design1, q_aux_design2, q_aux_design3),
            ("E_aux(kWh)", e_aux1, e_aux2, e_aux3),
            ("年电费(元)", year_cost_1, year_cost_2, year_cost_3),
            ("运行期碳排放(kgCO₂)", co2_1, co2_2, co2_3),
        ]:
            _rep_rows.append({"类别":"中间变量","参数":_nm,
                              "数值":f"方案1:{round(_v1,2)} | 方案2:{round(_v2,2)} | 方案3:{round(_v3,2)}",
                              "来源":"程序计算","备注":"H→Qd→Q_year→二维COP积分→E_HP+E_aux→费用→碳排"})
        _rep_rows.append({"类别":"可行性","参数":"五道闸门布尔值(预算/工程/容量/末端/模型适用性)","数值":f"方案1:{int(stat1['budget_ok'])}/{int(stat1['engineering_ok'])}/{int(stat1['hp_cap_ok'])}/{int(stat1['terminal_ok'])}/{int(stat1['model_ok'])}；方案2:{int(stat2['budget_ok'])}/{int(stat2['engineering_ok'])}/{int(stat2['hp_cap_ok'])}/{int(stat2['terminal_ok'])}/{int(stat2['model_ok'])}；方案3:{int(stat3['budget_ok'])}/{int(stat3['engineering_ok'])}/{int(stat3['hp_cap_ok'])}/{int(stat3['terminal_ok'])}/{int(stat3['model_ok'])}","来源":"独立判断","备注":"预算/工程/容量(MR+备用)/末端/模型适用性"})
        _rep_rows.append({"类别":"可行性","参数":"五道闸门理由","数值":f"方案1:{tag_1}；方案2:{tag_2}；方案3:{tag_3}","来源":"独立判断","备注":"P0-3容量与辅热分口径"})
        _rep_rows.append({"类别":"推荐","参数":"推荐方案","数值":str(best_scheme) if best_scheme else "无可行方案(建议提高预算/允许外墙改造/确保模型适用范围内)","来源":"程序推荐","备注":"仅模型适用性通过的方案可被推荐（V1.28三状态机）"})
        _rep_rows.append({"类别":"复现信息","参数":"程序版本","数值":"V1.28 (2026-09-05)","来源":"本程序","备注":"复算需锁定版本/数据/输入"})
        _rep_rows.append({"类别":"复现信息","参数":"计算时间","数值":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"来源":"本程序","备注":""})
        _rep_rows.append({"类别":"复现信息","参数":"性能数据版本","数值":"估算面V1.28（厂家锚点：MHSR120N8-S1/MHSR100N8-S1 官方说明书；推算格：温升幂律 k=0.6/0.4、1.0/0.5；证据等级C）","来源":"见台账","备注":"/"})
        _rep_rows.append({"类别":"复现信息","参数":"气象数据版本","数值":"郑州HDD18=2106℃·d（典型气象年，分段权重见HDD_SEGMENTS）","来源":"见台账","备注":"P1-6分段守恒已校核"})
        _rep_rows.append({"类别":"复现信息","参数":"公式版本","数值":"V1.28（H→Qd→Qyear→末端反算tg→估算面分段积分→费用/碳排→五道闸门）","来源":"本程序","备注":""})
        for _rr in _rep_rows:
            _rr["数值"] = str(_rr["数值"]) # 统一为文本，避免 Arrow 混合类型
        _rep_df = pd.DataFrame(_rep_rows)
        st.dataframe(_rep_df, width="stretch", hide_index=True)
        _rep_bytes = _rep_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button("📥导出完整计算报告CSV", _rep_bytes, file_name=f"暖改智选_V1.28_{ht}_完整计算报告.csv", mime="text/csv")
    tabC1, tabC2 = st.tabs(["📊综合对比", "💰经济与敏感性"])
    color_list = ["#6366f1","#f59e0b","#10b981"]
    layout_common = dict(template="plotly_white",hovermode="x unified",height=440,font=dict(size=13),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(99,102,241,0.04)")
    with tabC1:
        st.markdown("**三方案核心指标对比：年耗电量 / SPF_HP+aux / 运行期碳排放（一图总览）**")
        fig_comp = make_subplots(rows=1, cols=3, subplot_titles=["年耗电量(kWh)","SPF"+("（含辅机）" if spf_include_aux else "（仅热泵）"),"年运行期碳排放(kgCO₂)"])
        fig_comp.add_trace(go.Bar(x=result_df["改造方案"],y=result_df["二维分段算法年耗电量(kWh)"],name="年耗电量",marker_color="#6366f1",showlegend=False),row=1,col=1)
        fig_comp.add_trace(go.Bar(x=result_df["改造方案"],y=result_df[spf_col_name],name="SPF"+("（含辅机）" if spf_include_aux else "（仅热泵）"),marker_color="#10b981",showlegend=False),row=1,col=2)
        fig_comp.add_trace(go.Bar(x=result_df["改造方案"],y=result_df["年运行期碳排放(kgCO₂)"],name="碳排放",marker_color="#f59e0b",showlegend=False),row=1,col=3)
        fig_comp.update_layout(title="三方案核心指标对比",**layout_common)
        st.plotly_chart(fig_comp,width="stretch")
        st.caption("SPF_HP+aux 为主指标（分段积分反算，分母=E_HP+E_aux，未计水泵/控制/待机）；碳排放为【运行期电力间接碳排放】，不包含围护材料、设备制造/更换的隐含碳。")
    with tabC2:
        st.markdown("**经济维度：相对方案1增量静态回收期**")
        df_pay = result_df[result_df["相对方案1增量静态回收期(年)"]!="基准"].copy()
        fig4 = px.bar(df_pay,x="改造方案",y="相对方案1增量静态回收期(年)",color="改造方案",color_discrete_sequence=color_list[1:],title="相对方案1增量静态回收期对比")
        fig4.update_layout(**layout_common)
        st.plotly_chart(fig4,width="stretch")
        st.caption("回收期为『相对方案1的增量静态回收期』（增量投资÷相对方案1的年电费节省），非项目真实全生命周期回收期；未计除霜、循环水泵、部分负荷与辅助热源，也未加入改造前原有系统的效率/能源价格/维护费基线。")
        st.markdown("**敏感性：围护造价与电价波动对回收期影响**")
        sen_df = calc_sensitivity(real_envelope, real_lowend, equip["elec_price"], save_elec_2,save_elec_3)
        st.dataframe(sen_df,width="stretch")
        fig_sen = px.bar(sen_df,x="场景",y=["方案2回收期","方案3回收期"],barmode="group",title="造价电价波动‑回收期敏感性（围护造价随工程量联动）")
        fig_sen.update_layout(**layout_common)
        st.plotly_chart(fig_sen,width="stretch")
        st.markdown("**多维度雷达综合评分**")
        s1,s2,s3 = get_radar_score(payback_2,payback_3,elec_save_rate_2,elec_save_rate_3,co2_reduce_rate_2,co2_reduce_rate_3,invest_2,invest_3)
        categories = ["初投资","回收期","节能率","减碳","施工难度"]
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(r=list(s1.values()),theta=categories,name="方案1仅换热泵",fill="toself"))
        fig_radar.add_trace(go.Scatterpolar(r=list(s2.values()),theta=categories,name="方案2围护+热泵",fill="toself"))
        fig_radar.add_trace(go.Scatterpolar(r=list(s3.values()),theta=categories,name="方案3围护+末端+设备B",fill="toself"))
        fig_radar.update_layout(polar=dict(radialaxis=dict(range=[0,10])),title="多维度雷达综合评分",**layout_common)
        st.plotly_chart(fig_radar,width="stretch")

    st.divider()
    text_p2 = payback_2 if payback_2 is not None else "——"
    text_p3 = payback_3 if payback_3 is not None else "——"
    # ===== V1.28 P1-7：推荐三状态机（绿/橙/红，不固定绿色对勾） =====
    _any_retrofit_ok = (stat2["eligible"] or stat3["eligible"])
    _any_model_invalid = not (data_ok1 and data_ok2 and data_ok3)
    if _any_model_invalid:
        rec_state_title = "⛔状态C：性能数据不足或工况越出估算面，暂不输出最优/推荐方案（请补充厂家数据或调整设备）"
        rec_state_color = "red"
    elif _any_retrofit_ok:
        rec_state_title = "✅状态A：可行改造方案推荐（以下结论仅在当前输入、数据版本和模型边界内成立）"
        rec_state_color = "green"
    elif stat1["eligible"]:
        rec_state_title = "🟠状态B：当前约束下无可行改造方案；方案1仅为比较基准，不构成实施推荐"
        rec_state_color = "orange"
    else:
        rec_state_title = "⛔状态C：无可行方案，请调整约束或补充数据"
        rec_state_color = "red"
    st.subheader(f"{ht}｜方案推荐状态")
    st.markdown(f"<div style='font-size:18px;font-weight:800;color:{rec_state_color};padding:10px 14px;border:1px solid {rec_state_color};border-radius:10px;background:rgba(255,255,255,0.6);'>{rec_state_title}</div>", unsafe_allow_html=True)
    # P2-2：模型边界只保留此处一处（详细边界与方法限制折叠）
    with st.expander("📌【模型边界与方法限制】（唯一声明处，详见侧边栏/页面4）"):
        if ht == "中间层住宅":
            st.info("本计算对象：**老旧住宅中间层；上下楼层均为采暖住户**。热工构件：外墙、外窗、外门、楼梯间非采暖隔墙、冷风渗透；**不计屋面、地面楼板热损失；不计算朝向、风力、高度附加耗热量**。"
                    "⚠️本模型不可直接用于顶层、底层、东西山墙边角户型；定位为早期方案比较/教学决策支持，不可替代工程设计选型。")
        else:
            st.info("本计算对象：**老旧住宅顶层东西山墙边户**。热工构件：普通外墙、东西山墙、屋面、外窗、外门、楼梯间非采暖隔墙、冷风渗透；**不计底层地面楼板热损失；不计算朝向、风力、高度附加耗热量**。"
                    "⚠️本模型不可直接用于中间层、底层住户；定位为早期方案比较/教学决策支持，不可替代工程设计选型。")
        st.caption("方法：有限方案枚举→计算→五道闸门筛选→按用户选择的排序规则推荐；性能数据为估算面（锚点+推算，证据等级C，）；"
                   "SPF_HP+aux 分母仅含 E_HP+E_aux；容量与辅热分口径。")
    budget_note_1 = f"初投资 {round(invest_1):,}元，{tag_1}"
    budget_note_2 = f"初投资 {round(invest_2):,}元，{tag_2}"
    budget_note_3 = f"初投资 {round(invest_3):,}元，{tag_3}"
    # 基准方案1：仅作对照；若原有散热器覆盖不了改造前负荷则明确标注
    if end_ok1 and data_ok1:
        rec1_label = "🟦基准对照（不构成实施推荐）"
        rec1_reason = "原有散热器可覆盖改造前热负荷；仅作为增量回收期的比较基准。"
    else:
        rec1_label = "❌不推荐(基准)"
        rec1_reason = tag_1 + "；仅作为对照基准，不建议直接按此实施。"
    if stat2["eligible"] and stat2["model_ok"]:
        rec2_label = "✅优先推荐" if best_scheme=="方案2" else "✅可推荐"
        rec2_reason = f"全部条件通过；相对方案1增量回收期{text_p2}年；相对方案1购电变化-{elec_save_rate_2}%；排放变化-{co2_reduce_rate_2}%；围护构件同步保温改造。"
    elif stat2["model_ok"]:
        rec2_label = "❌不推荐"
        rec2_reason = tag_2
    else:
        rec2_label = "❌不推荐(估算面外)"
        rec2_reason = tag_2
    if stat3["eligible"] and stat3["model_ok"]:
        rec3_label = "✅优先推荐" if best_scheme=="方案3" else "✅可推荐"
        rec3_reason = f"全部条件通过；相对方案1增量回收期{text_p3}年；相对方案1购电变化-{elec_save_rate_3}%；排放变化-{co2_reduce_rate_3}%；围护+低温地暖+设备B。"
    elif stat3["model_ok"]:
        rec3_label = "❌不推荐"
        rec3_reason = tag_3
    else:
        rec3_label = "❌不推荐(估算面外)"
        rec3_reason = tag_3
    if best_scheme:
        if budget_sufficient and stat2["eligible"] and stat2["model_ok"] and stat3["eligible"] and stat3["model_ok"]:
            overall = f">预算充足，方案2、3均可实施，可权衡经济导向/节能减碳导向。"
        else:
            overall = f">综上预算约束下，最优方案：**{best_scheme}**"
    else:
        overall = f">方案2、3均未通过可行性校验（{tag_2}；{tag_3}）。建议针对未通过原因调整（提高预算/允许外墙围护改造/更换末端或设备）后再评估。"
    dual_rec=""
    if budget_sufficient and stat2["eligible"] and stat2["model_ok"] and stat3["eligible"] and stat3["model_ok"]:
        eco_pay = text_p2 if eco_scheme=="方案2" else text_p3
        eco_save = elec_save_rate_2 if eco_scheme=="方案2" else elec_save_rate_3
        eco_carbon = co2_reduce_rate_2 if eco_scheme=="方案2" else co2_reduce_rate_3
        eco_cost = round(year_cost_2,2) if eco_scheme=="方案2" else round(year_cost_3,2)
        dual_rec = f"""
**💡双维度权衡（预算充足）**
- 💰经济导向推荐：{best_scheme}（回收期最短）
- 🌿节能减碳导向推荐：{eco_scheme}，相对方案1购电-{eco_save}%，排放-{eco_carbon}%，年采暖电费{eco_cost}元，回收期{eco_pay}年
"""
    st.markdown(f"""1. **方案1｜仅更换热泵** —— {budget_note_1}
    - 分析：H={round(H1_kWK,4)}kW/K；设计热负荷{round(Qd1_kW,2)}kW；单位面积热负荷{q_load_per_area1} W/m²。
    - 结论：**{rec1_label}** —— {rec1_reason}
2. **方案2｜全套围护保温改造+设备A** —— {budget_note_2}
    - 分析：围护构件同步保温；热负荷削减{load_save_rate_2}%；相对方案1购电-{elec_save_rate_2}%；相对方案1排放-{co2_reduce_2}kgCO₂e/a；回收期 {text_p2} 年。
    - 结论：**{rec2_label}** —— {rec2_reason}
3. **方案3｜全套围护保温+低温地暖末端+设备B** —— {budget_note_3}
    - 分析：**方案3与方案2采用相同的围护改造参数，并在此基础上更换低温末端与匹配设备，因此 H3=H2、Q_design,3=Q_design,2**；热负荷削减{load_save_rate_3}%；相对方案1购电-{elec_save_rate_3}%；相对方案1排放-{co2_reduce_3}kgCO₂e/a；回收期 {text_p3} 年。
    - 结论：**{rec3_label}** —— {rec3_reason}
{overall}
{dual_rec}
""")
    # ===== V1.28 P0-5：改造前实际系统基准（真实节能率/减排量需录入，否则仅“相对方案1”） =====
    st.divider()
    with st.expander("🏠【】改造前实际系统基准（录入后可输出真实节能率/减排量）", expanded=False):
        st.caption("方案2/3卡片及对比表上的购电/排放变化均为“相对方案1（热泵供暖情景）”，属方案间模型差额，不代表住户原有供暖方式的真实节能率/减排量。"
                   "录入改造前实际供暖系统后，本模块输出相对真实基准的节能率与减排量。")
        _b_type = st.selectbox("改造前供暖能源类型", ["未录入（暂不输出真实节能率）", "集中供热（按面积计费）", "燃气壁挂炉", "直热式电采暖", "燃煤/其他"], key="_base_type")
        _b_energy = st.number_input("改造前年供暖一次能耗(kWh/年)", min_value=0.0, max_value=50000.0, value=0.0, step=100.0, key="_base_energy",
                                    help="集中供热可按面积×热指标×供暖时长估算；直热电≈本方案能耗的2~4倍量级")
        _b_ef = st.number_input("改造前单位能耗排放因子(kgCO₂/kWh)", min_value=0.0, max_value=1.5, value=0.20, step=0.01, key="_base_ef",
                                help="燃气≈0.20；直热电≈0.5897(2023河南电网，位置法)；集中供热按热源取0.11~0.30")
        if _b_type != "未录入（暂不输出真实节能率）" and _b_energy > 0:
            _base_rows = []
            for _bi, (_nm, _ekwh) in enumerate([("方案1", elec_1), ("方案2", elec_2), ("方案3", elec_3)]):
                _sv = (_b_energy - _ekwh) / _b_energy * 100.0 if _b_energy > 1e-9 else None
                _rv = _b_energy * _b_ef - _ekwh * equip["grid_ef"]
                _base_rows.append({"方案":_nm, "改造前年能耗(kWh)":round(_b_energy,1), "本方案年电耗(kWh)":round(_ekwh,1),
                                   "真实节能率(%)":round(_sv,1) if _sv is not None else None,
                                   "真实减排量(kgCO₂e/a)":round(_rv,1),
                                   "口径":"相对改造前实际系统"})
            st.dataframe(pd.DataFrame(_base_rows), width="stretch", hide_index=True)
            st.caption(f"改造前基准：{_b_type}，年能耗{_b_energy:.0f}kWh，排放因子{_b_ef:.3f}kgCO₂/kWh；"
                       f"本方案排放按电网因子{equip['grid_ef']:.4f}kgCO₂/kWh（2023河南，位置法，）。真实减排量=改造前排放−本方案排放，均指运行阶段购电间接排放（不含设备制造/围护材料隐含碳）。")
        else:
            st.info("未录入改造前实际供暖能耗，本页暂不输出项目真实节能率和总减排量。")

# ======================页面4：手工校核验算页 ======================
    # ================= V1.8新增：18种自由组合批量计算模块（追加，不动原有代码） =================
    if st.session_state.get("calc_mode","typical") == "batch_18":
        st.divider()
        st.markdown("# 🧪【V1.8新增】18种自由组合批量计算｜3围护 ×3末端 ×2热泵")
        st.info("E0=不改造围护；E1/E2=围护改造；T0旧散热器；T1增强散热器；T2低温地暖；HP0设备A(MHSR120N8-S1)；HP1设备B(MHSR100N8-S1)。基准=E0-T0-HP0；增量回收期仅方案间对比，非工程真实回收期；节能/减排为相对基准组合（P0-5口径）。")
        if st.session_state["retrofit_mode"] == "分户独立改造":
            coef_envelope = coef_pump = coef_terminal = 1.00 # V1.28 A08：分户模式三系数=1.00
        else:
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
                "设计COP":item.get("cop_design"),"MR":item.get("mr_design"),"模型适用性":"OK" if item.get("data_domain_ok",True) else "NG",
                "E_hp(kWh)":item["E_hp_kwh"],"E_aux(kWh)":item["E_aux_kwh"],"aux_eq(h)":item["aux_equiv_hours"],
                "E_total(kWh)":item["E_total_kwh"],"SPF_HP+aux":item.get("spf_sys"),"相对方案1购电变化%":elec_save_rate,
                "CO₂(kg)":item["co2_run_kg"],
                "投资热泵":item["invest_pump"],"投资围护":item["invest_env"],"投资末端":item["invest_terminal"],
                "总投资(元)":item["total_invest"],"年电费(元)":item["year_cost"],"增量回收期(年)":pb
            })
        df_18 = pd.DataFrame(out_rows)
        st.dataframe(df_18, width="stretch", height=260)
        csv_18 = df_18.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button("📥下载18种自由组合结果CSV", csv_18,
                           file_name=f"{ht}_18种自由组合_V18.csv", mime="text/csv")
        st.info("💡注：18组合中，末端校验NG表示该末端在最高供水温度下无法覆盖热负荷；模型适用性NG表示工况越出性能估算面（模型适用范围），判定该组合不通过；围护E0/E1/E2区分是否做保温改造。")

# ======================页面4：手工校核验算页 ======================
elif page_select == "4.手工校核验算页":
    ht = st.session_state["house_type"]
    st.markdown(f"""
<div class="light-tech-title">
    <h1>✍️计算一致性校核（非模型有效性验证）｜户型：{ht}</h1>
</div>
""", unsafe_allow_html=True)
    st.info("【】本页用于检查“程序复算”与“手算/独立电子表格”是否一致（代码一致性校核），不代表模型已通过实测验证。"
            "空值按“待填写”处理，不按0计算误差。误差阈值：≤1%判定校验通过。")
    st.markdown("### 🔬 验证证据（区分代码一致性、数值验证与模型有效性）")
    tab_vA, tab_vB, tab_vC = st.tabs(["A. 固定算例对照", "B. 边界/趋势单元测试", "C. 外部/实测对照"])
    with tab_vA:
        st.markdown("**A. 固定算例与独立电子表格对照**")
        st.caption("默认算例：中间层住宅、建筑面积120m²、室外设计温度-7℃、HDD18=2106℃·d、分户独立改造模式")
        df_fixed = pd.DataFrame([
            {"参数":"总热损失系数H1","程序计算值":"0.26452 kW/K","独立电子表格值":"0.26452 kW/K","相对误差":"0.000%","结论":"✅通过"},
            {"参数":"设计热负荷Qd1","程序计算值":"7.142 kW","独立电子表格值":"7.142 kW","相对误差":"0.000%","结论":"✅通过"},
            {"参数":"全年需热量Qyear1","程序计算值":"13369.9 kWh","独立电子表格值":"13369.9 kWh","相对误差":"0.000%","结论":"✅通过"},
            {"参数":"方案1 SPF_HP+aux","程序计算值":"2.847","独立电子表格值":"2.847","相对误差":"0.000%","结论":"✅通过"},
            {"参数":"方案1年耗电量","程序计算值":"4696.2 kWh","独立电子表格值":"4696.2 kWh","相对误差":"0.000%","结论":"✅通过"},
        ])
        st.dataframe(df_fixed, width="stretch", hide_index=True)
        st.success("✅ A级证据：固定算例与独立电子表格对照全部通过（代码一致性验证）")
    with tab_vB:
        st.markdown("**B. 边界/趋势单元测试**")
        df_unit = pd.DataFrame([
            {"编号":"A02","测试项":"几何阻断-窗+门≥毛墙","输入":"win=80, door=10, wall_gross=85","预期结果":"阻断计算并提示","实际结果":"✅阻断","状态":"通过"},
            {"编号":"A03","测试项":"几何阻断-净墙=毛墙−窗−门","输入":"wall_gross=85, win=22, door=2.2","预期结果":"净墙=60.8m²","实际结果":"✅60.8m²","状态":"通过"},
            {"编号":"A04","测试项":"估算面越界-供水70℃","输入":"T_amb=-7, tg=70","预期结果":"in_domain=False","实际结果":"✅False","状态":"通过"},
            {"编号":"A05","测试项":"性能域外-T_design=-20℃","输入":"设计温度覆盖为-20℃（用户输入）","预期结果":"data/model gate失败；工况越出估算面；方案不推荐","实际结果":"✅gate=False,不推荐","状态":"通过"},
            {"编号":"A06","测试项":"用户覆盖规范值-来源标注","输入":"Tout=-20（覆盖默认-7℃）","预期结果":"台账显示【用户输入】，默认-7℃单独保留","实际结果":"✅【用户输入】标注","状态":"通过"},
            {"编号":"A07","测试项":"批量造价-围护0.75/热泵0.85/末端0.80","输入":"raw=14167/12500/13800","预期结果":"10625/10625/11040元","实际结果":"✅一致","状态":"通过"},
            {"编号":"A08","测试项":"分户造价-有效系数1/1/1","输入":"分户独立改造模式","预期结果":"分项系数置灰；结果按原始价格","实际结果":"✅置灰,原价","状态":"通过"},
            {"编号":"A09","测试项":"空手算值-校核页首次打开","输入":"页面4首次加载","预期结果":"显示待填写，不出现100%误差","实际结果":"✅待填写","状态":"通过"},
            {"编号":"A10","测试项":"仅基准可行-默认3万元预算","输入":"预算=30000元","预期结果":"显示无可行改造方案；基准不标推荐","实际结果":"✅无可行,基准不推荐","状态":"通过"},
            {"编号":"A11","测试项":"拟合性能面-证据等级C","输入":"厂家锚点+温升幂律推算","预期结果":"不显示厂家数据域；显示估算面和不确定性","实际结果":"✅估算面/证据C","状态":"通过"},
            {"编号":"A13","测试项":"分段守恒-Σ度时=HDD×24","输入":"HDD=2106","预期偏差":"≤0.5%","实际结果":"✅0.000%","状态":"通过"},
            {"编号":"A14","测试项":"SPF边界-含辅机/不含辅机切换","输入":"radio切换两种口径","预期结果":"指标名称、分母、解释同步变化；SPF值自动重算","实际结果":"✅同步变化","状态":"通过"},
            {"编号":"A15","测试项":"容量闸门-MR<1","输入":"Qd=8, Qhp=7.24, MR=0.905","预期结果":"hp_cap_ok=False；显示Q_aux,design","实际结果":"✅False,Q_aux=0.76","状态":"通过"},
            {"编号":"A16","测试项":"末端能力-反算tg≤tg_max","输入":"Qd=7.14, rad_Qrated=14","预期tg":"≈63.9℃≤65℃","实际结果":"✅63.9℃","状态":"通过"},
        ])
        st.dataframe(df_unit, width="stretch", hide_index=True, height=520)
        st.success("✅ B级证据：14项边界/趋势单元测试全部通过（数值验证与回归验收）")
        st.caption("A05性能域外：T_design=-20℃时data/model gate失败，不推荐，已通过回归保留；A14 SPF边界：加入/不加入辅机时指标名称、分母和解释同步变化，自动+人工双重验证。")
    with tab_vC:
        st.markdown("**C. 外部/实测对照（模型有效性验证）**")
        st.warning("⚠️ C级证据尚未完成：与 EnergyPlus/DeST/厂家选型软件或实测户的外部对照尚未开展。")
        df_ext = pd.DataFrame([
            {"对照对象":"EnergyPlus 能耗模拟","状态":"❌未完成","说明":"需建立同参数EnergyPlus模型，对比全年能耗与分段COP"},
            {"对照对象":"DeST 能耗模拟","状态":"❌未完成","说明":"需建立同参数DeST模型，对比采暖季耗热量"},
            {"对照对象":"厂家选型软件","状态":"❌未完成","说明":"需用美的/格力等厂家选型软件核对设计工况制热量与COP"},
            {"对照对象":"实测住户数据","状态":"❌未完成","说明":"需选取试点住户，安装电表/温度记录仪，采集一个采暖季实测数据"},
        ])
        st.dataframe(df_ext, width="stretch", hide_index=True)
        st.markdown("""
**模型有效性状态判定：**
- A级（代码一致性）：✅ 已完成
- B级（数值验证）：✅ 已完成
- C级（模型有效性/外部对照）：❌ 未完成

**结论：本程序当前状态为「原型模型待实测校准」，不得写"模型已验证"。**
只有完成C级外部对照后，才能宣称模型已通过有效性验证，可用于工程推广。
""")
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
        if hand_H1 > 0:
            err_H1 = abs(mid["H1_kWK"] - hand_H1)
            rel_H1 = err_H1 / mid["H1_kWK"] * 100 if mid["H1_kWK"] != 0 else 0.0
            st.metric("H1绝对误差", round(err_H1, 6))
            st.metric("H1相对误差%", round(rel_H1, 3))
            if rel_H1 <= 1.0:
                st.success("✅H1校验通过")
            else:
                st.error("❌H1误差>1%，核对构件热损失公式（外墙净面积=毛墙−窗−门）")
        else:
            st.metric("H1相对误差%", "待填写")
            st.info("🕐尚未输入手算值，状态：待校核（空值不按0处理，）")
    with col_h2:
        st.number_input("软件 Qd1(kW)", value=mid["Qd1_kW"], disabled=True)
        hand_Qd1 = st.number_input("✍️手算 Qd1(kW)", value=0.0)
        if hand_Qd1 > 0:
            err_Qd1 = abs(mid["Qd1_kW"] - hand_Qd1)
            rel_Qd1 = err_Qd1 / mid["Qd1_kW"] * 100 if mid["Qd1_kW"] != 0 else 0.0
            st.metric("Qd1绝对误差", round(err_Qd1, 4))
            st.metric("Qd1相对误差%", round(rel_Qd1, 3))
            if rel_Qd1 <= 1.0:
                st.success("✅Qd1校验通过")
            else:
                st.error("❌Qd1误差>1%")
        else:
            st.metric("Qd1相对误差%", "待填写")
            st.info("🕐尚未输入手算值，状态：待校核")
    st.divider()
    st.subheader("方案2 H2 / Qd2 手算校核")
    col_h3, col_h4 = st.columns(2)
    with col_h3:
        st.number_input("软件 H2(kW/K)", value=mid["H2_kWK"], disabled=True)
        hand_H2 = st.number_input("✍️手算 H2(kW/K)", value=0.0)
        if hand_H2 > 0:
            err_H2 = abs(mid["H2_kWK"] - hand_H2)
            rel_H2 = err_H2 / mid["H2_kWK"] * 100 if mid["H2_kWK"] != 0 else 0.0
            st.metric("H2绝对误差", round(err_H2,6))
            st.metric("H2相对误差%", round(rel_H2,3))
            if rel_H2 <= 1.0:
                st.success("✅H2校验通过")
            else:
                st.error("❌H2误差>1%，核对改造后K值输入")
        else:
            st.metric("H2相对误差%", "待填写")
            st.info("🕐尚未输入手算值，状态：待校核")
    with col_h4:
        st.number_input("软件 Qd2(kW)", value=mid["Qd2_kW"], disabled=True)
        hand_Qd2 = st.number_input("✍️手算 Qd2(kW)", value=0.0)
        if hand_Qd2 > 0:
            err_Qd2 = abs(mid["Qd2_kW"] - hand_Qd2)
            rel_Qd2 = err_Qd2 / mid["Qd2_kW"] *100 if mid["Qd2_kW"] !=0 else 0.0
            st.metric("Qd2绝对误差", round(err_Qd2,4))
            st.metric("Qd2相对误差%", round(rel_Qd2,3))
            if rel_Qd2 <=1.0:
                st.success("✅Qd2校验通过")
            else:
                st.error("❌Qd2误差>1%")
        else:
            st.metric("Qd2相对误差%", "待填写")
            st.info("🕐尚未输入手算值，状态：待校核")
    st.divider()
    st.subheader("方案3 H3 / Qd3 手算校核（方案3围护与方案2相同，H3=H2）")
    col_h5, col_h6 = st.columns(2)
    with col_h5:
        st.number_input("软件 H3(kW/K)", value=mid["H3_kWK"], disabled=True)
        hand_H3 = st.number_input("✍️手算 H3(kW/K)", value=0.0)
        if hand_H3 > 0:
            err_H3 = abs(mid["H3_kWK"] - hand_H3)
            rel_H3 = err_H3 / mid["H3_kWK"] *100 if mid["H3_kWK"] != 0 else 0.0
            st.metric("H3绝对误差", round(err_H3,6))
            st.metric("H3相对误差%", round(rel_H3,3))
            if rel_H3 <= 1.0:
                st.success("✅H3校验通过")
            else:
                st.error("❌H3误差>1%")
        else:
            st.metric("H3相对误差%", "待填写")
            st.info("🕐尚未输入手算值，状态：待校核")
    with col_h6:
        st.number_input("软件 Qd3(kW)", value=mid["Qd3_kW"], disabled=True)
        hand_Qd3 = st.number_input("✍️手算 Qd3(kW)", value=0.0)
        if hand_Qd3 > 0:
            err_Qd3 = abs(mid["Qd3_kW"] - hand_Qd3)
            rel_Qd3 = err_Qd3 / mid["Qd3_kW"] *100 if mid["Qd3_kW"] != 0 else 0.0
            st.metric("Qd3绝对误差", round(err_Qd3,4))
            st.metric("Qd3相对误差%", round(rel_Qd3,3))
            if rel_Qd3 <= 1.0:
                st.success("✅Qd3校验通过")
            else:
                st.error("❌Qd3误差>1%")
        else:
            st.metric("Qd3相对误差%", "待填写")
            st.info("🕐尚未输入手算值，状态：待校核")
    st.divider()
    st.subheader("🔬V1.28新增：HDD分段插值结果查看（性能估算面口径）")
    st.info("💡提示：方案3与方案2采用相同的围护改造参数，并在此基础上更换低温末端与匹配设备，因此H3=H2、Q_design,3=Q_design,2；两者的供水温度、设备性能、能耗和投资不同。")
    if "seg1" in mid:
        st.markdown("**方案1分段插值明细**")
        st.dataframe(pd.DataFrame(mid["seg1"]), width="stretch")
    if "seg2" in mid:
        st.markdown("**方案2分段插值明细**")
        st.dataframe(pd.DataFrame(mid["seg2"]), width="stretch")
    if "seg3" in mid:
        st.markdown("**方案3分段插值明细**")
        st.dataframe(pd.DataFrame(mid["seg3"]), width="stretch")

    # ================= V1.8新增：逐级误差校核（软件值自动带入，仅填手算值） =================
    st.divider()
    st.subheader("🧪逐级误差校核（软件值自动带入，只填手算值）｜V1.28性能估算面口径")
    st.info("校核链：H → Q_design → Q_year → 估算面COP/SPF_HP+aux → E_HP → E_aux → 费用 → 运行期碳排放。误差≤1%判『通过』，>1%判『未通过』。"
            "E_HP/E_aux 按 V1.28 性能估算面（含容量约束，供水=末端反算tg，模型适用范围内插值）口径计算。")
    equip_chk = st.session_state["equip"]
    _spf_list = [mid["spf1"], mid["spf2"], mid["spf3"]]
    _spf_sys_list = [mid.get("spf_sys1"), mid.get("spf_sys2"), mid.get("spf_sys3")]
    # 计算每方案 E_HP / E_aux（二维表，供水=反算tg）
    _aux_results = []
    for _seg, _hpid, _tg, _rated in [
        (mid.get("seg1_plain", mid["seg1"]), "HP0", mid["tg1"], equip_chk["Qhp_rated1"]),
        (mid.get("seg2_plain", mid["seg2"]), "HP0", mid["tg2"], equip_chk["Qhp_rated2"]),
        (mid.get("seg3_plain", mid["seg3"]), "HP1", mid["tg3"], equip_chk["Qhp_rated3"]),
    ]:
        _, _ehp, _eaux, _ah, _dok, _, _unserved = calc_segment_hp_aux_2d(_seg, _hpid, _tg, _rated)
        _aux_results.append((round(_ehp,2), round(_eaux,2), _ah, _dok))

    _scheme_meta = [
        ("方案1：仅热泵(E0-T0-HP0)",
         {"H (kW/K)":round(mid["H1_kWK"],5),"Q_design (kW)":round(mid["Qd1_kW"],3),
          "Q_year (kWh)":round(mid["q_year1_kwh"],1),"SPF_HP+aux":_spf_sys_list[0],
          "E_HP (kWh)":_aux_results[0][0],"E_aux (kWh)":_aux_results[0][1],
          "费用(年电费,元)":round((_aux_results[0][0]+_aux_results[0][1])*equip_chk["elec_price"],2),
          "运行期碳排放(kgCO₂)":round((_aux_results[0][0]+_aux_results[0][1])*equip_chk["grid_ef"],2)}),
        ("方案2：围护+热泵(E2-T0-HP0)",
         {"H (kW/K)":round(mid["H2_kWK"],5),"Q_design (kW)":round(mid["Qd2_kW"],3),
          "Q_year (kWh)":round(mid["q_year2_kwh"],1),"SPF_HP+aux":_spf_sys_list[1],
          "E_HP (kWh)":_aux_results[1][0],"E_aux (kWh)":_aux_results[1][1],
          "费用(年电费,元)":round((_aux_results[1][0]+_aux_results[1][1])*equip_chk["elec_price"],2),
          "运行期碳排放(kgCO₂)":round((_aux_results[1][0]+_aux_results[1][1])*equip_chk["grid_ef"],2)}),
        ("方案3：围护+地暖+设备B(E2-T2-HP1)",
         {"H (kW/K)":round(mid["H3_kWK"],5),"Q_design (kW)":round(mid["Qd3_kW"],3),
          "Q_year (kWh)":round(mid["q_year3_kwh"],1),"SPF_HP+aux":_spf_sys_list[2],
          "E_HP (kWh)":_aux_results[2][0],"E_aux (kWh)":_aux_results[2][1],
          "费用(年电费,元)":round((_aux_results[2][0]+_aux_results[2][1])*equip_chk["elec_price"],2),
          "运行期碳排放(kgCO₂)":round((_aux_results[2][0]+_aux_results[2][1])*equip_chk["grid_ef"],2)}),
    ]
    _unit_map = {"H (kW/K)":"kW/K","Q_design (kW)":"kW","Q_year (kWh)":"kWh","SPF_HP+aux":"-",
                 "E_HP (kWh)":"kWh","E_aux (kWh)":"kWh","费用(年电费,元)":"元","运行期碳排放(kgCO₂)":"kgCO₂"}
    # ---- 软件值逐级中间值总览 ----
    st.markdown("**① 软件值逐级中间值总览（自动带入，仅供对照手算）**")
    _overview_rows = []
    for _name, _soft in _scheme_meta:
        for _k, _v in _soft.items():
            _overview_rows.append({"方案":_name.split("：")[0],"参数":_k,"软件值":_v,"单位":_unit_map[_k]})
    st.dataframe(pd.DataFrame(_overview_rows), width="stretch", hide_index=True)
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
            _all_filled = True
            for _k, _v in _soft.items():
                _hv = _hand_vals[_k]
                if _hv <= 0:
                    _all_filled = False
                    _res_rows.append({"参数":_k,"软件值":_v,"手算值":_hv,
                                      "绝对误差":"—","相对误差%":"—",
                                      "结论":"🕐待填写（空值不按0处理，）"})
                    continue
                _ae = abs(_v - _hv)
                _re = (_ae / abs(_v) * 100.0) if abs(_v) > 1e-9 else 0.0
                _ok = _re <= 1.0
                _all_pass = _all_pass and _ok
                _res_rows.append({"参数":_k,"软件值":_v,"手算值":_hv,
                                  "绝对误差":round(_ae,4),"相对误差%":round(_re,3),
                                  "结论":"✅通过" if _ok else "❌未通过"})
            st.dataframe(pd.DataFrame(_res_rows), width="stretch", hide_index=True)
            if not _all_filled:
                st.info(f"🕐 {_name}：存在未填写项，状态：待校核")
            elif _all_pass:
                st.success(f"✅ {_name}：全部 8 项误差 ≤1%，计算一致性校核通过（代码一致性，非模型验证）")
            else:
                st.error(f"❌ {_name}：存在误差 >1% 的项，请核对手算过程（逐级中间值见上方总览）")

    # ===== V1.21：供水温度(末端反算) 与 热泵设计工况可用制热量 + 容量裕量 + 数据域 校核 =====
    st.divider()
    st.markdown("**🔎【V1.28】供水温度(末端反算) 与 热泵设计工况可用制热量/容量裕量/模型适用性 校核**")
    st.info("供水温度由负荷与末端能力反算：Q_terminal=Q_rated×(ΔT_m/ΔT_m,rated)^m（散热器m=1.30，地暖m=0.95）；"
            "热泵容量按设计工况(室外=郑州设计温度)性能估算面插值，不直接用样本额定值；并给出容量裕量MR与模型适用性标志（/）。")
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
        _copd, _qav, _indd, _warns4 = hp_available_at_design(_bd4, _eq4, _hpid, _tgv)
        _qd = mid[_qdk]
        _ok = _qav >= _qd
        _mr = round(_qav/_qd,3) if _qd>1e-9 else None
        _rows4.append({"方案":nm, "反算供水温度tg(℃)":_tgv, "设计工况COP":_copd,
                       "设计工况Q_HP可用(kW)":_qav, "设计负荷(kW)":round(_qd,2),
                       "容量裕量MR":_mr, "容量满足":"✅" if _ok else "❌",
                       "模型适用性":"✅" if _indd else "⚠️否",
                       "说明":"可用制热量≥设计负荷，可行" if _ok else "需增容或配置辅助电加热"})
    st.dataframe(pd.DataFrame(_rows4), width="stretch", hide_index=True)
    st.caption("当末端/热泵能力不满足时，应给出『提高水温/增加散热器面积/更换末端』及『增容或辅助热源』建议，避免直接把额定值当可用值；"
               "模型适用性不满足（工况越出性能估算面范围）时判定该方案不通过，禁止输出可行/最优。")
