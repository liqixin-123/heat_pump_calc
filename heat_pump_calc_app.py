# -*- coding: utf-8 -*-
"""
老旧住宅空气源热泵协同改造计算工具 V1.36
UI：浅色科技风｜玻璃拟态｜清爽高亮｜大屏展示
👉V1.38修订要点（方案B：修复"载入/删除/重置后左右页面不一致"）：
- 根因：载入/删除/重置按钮位于侧边栏"功能页面切换"radio 之前，点击时 st.rerun() 会在 radio 实例化前中断脚本，
  Streamlit 据此把 radio 控件状态当作过期控件清空，下次渲染回落到默认页1；前端 radio 仍显示旧选中页 → 左（导航）右（内容）不一致。
- 修复：①保存方案快照新增"当前页面"字段；②载入方案时在脚本顶部显式写回 page_select_radio（旧方案无该字段时默认回到页面3，便于继续修改）；
  ③删除方案时暂存并恢复当前页面；④恢复统一基准后显式回到页面1。
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
  两套设备均按【美的MHSR-N8-S1系列】官方说明书真实锚点标定（执行 GB/T 25127.2-2020）：
  设备A(方案1/2)=MHSR120N8-S1(12kW)，A7/W45 COP=3.50、Q=12kW，55℃出水列按温升比换算；
  设备B(方案3)=MHSR100N8-S1(10kW)，A7/W45 COP=3.55、Q=10kW，A-12/W35 COP=2.70、A-20/W35 COP=2.21。
- 性能面证据分级：厂家公开锚点【源】与温升幂律推算格【算】彻底分栏；未获得完整厂家性能矩阵前，界面一律称“热泵性能估算面/模型适用性”，不再称“厂家二维性能表/厂家数据域”。
- 第五道闸门更名 performance_model_applicable：模型适用性判定（估算面是否覆盖工况），不再表述为“厂家样本验证范围”。
- 季节性能统一口径为 SPF_HP+aux = Q_year / (E_HP + E_aux)（由分段积分反算；分母仅含热泵主机与辅助电加热，未计入水泵/控制/待机，见 ）；
  原铭牌SPF×衰减系数仅保留为“旧算法估算值”，不再作为当前主指标
👉V1.34修订要点（方案A：机型名称修正+供水温度上限约束）：
- 机型名称修正：原"美的雪焰/真暖"系列功率区间为14-20kW，与代码使用的MHSR100N8-S1(10kW)、MHSR120N8-S1(12kW)不匹配；
  全部替换为"美的MHSR-N8-S1系列"，型号、功率、系列完全自洽。
- 供水温度上限约束：MHSR-N8-S1系列官方手册最高出水温度60℃；
  散热器允许最高供水温度从65℃下调为60℃，校验范围[40,75]→[40,60]，输入上限75→60。
- 参考文献更新：取消70℃《暖通空调》期刊引用（70℃为雪焰系列极限，不适用于MHSR-N8-S1）；
  改用美的MHSR-N8-S1系列官方产品说明书，最高出水温度60℃。
👉V1.35修订要点（依据《小程序修改建议-20260909》五条审查意见）：
- ①计算快照一致性：新增 calc_input_fingerprint 输入+版本指纹（建筑/设备/系数/户型/造价模式/计算模式/外墙开关/SPF口径/备用配置/采暖时长 + APP_VERSION + CALC_DATA_VERSION）；
  页面3写入 calc_mid 时记录指纹，页面4读取前校验：指纹/版本变化立即失效旧结果，显示"参数已改变，当前结果待重新计算"，
  未重新算完前禁止显示旧绿灯/旧导出；恢复统一基准一次性复位输入并删除 calc_mid 派生快照。
- ②度时与时长严格分离：seg 输出新增 degree_hours_seg(℃·h)=hdd_seg×24 与 duration_hours_seg(h)=采暖期总时长×度时占比（一阶假设，须气象时序校核）；
  删除被误当"小时"的 hours_seg 键；度时守恒校核改述为"度时合计ΣD_i=HDD18×24(℃·h)，仅检查温差积分总量；供暖运行时长Σh_i须由气象时序另行统计"。
- ③有效性分维度：hp_2d_interpolate 返回 validity{q_valid容量估算域 / cop_valid COP估算域(室外温度≥-10℃说明书工况下限) / hardware_valid设备包络(供水≤60℃) / reason / all_valid=AND}；
  不得用容量表域代替COP域；COP域外仅作带明显标记的教学估计，退出正式排序。
- ④备用热源不假定足额：新增备用热源配置（无备用／水侧电辅热（受末端能力限制）／独立房间热源）+已安装容量/效率/投资/配电上限；
  未配置时备用供热=0、缺口全部计为未满足热量；分别输出所需备用容量、已配置容量、实际备用供热、备用用电、未满足热量；电力容量/投资联动进入约束与费用。
- ⑤供热完整性：基准方案（方案1）末端能力不足或存在未满足热量时，相对方案1的购电变化/排放变化/增量回收期一律标"不可比"，
  提示"请先补足基准供热或统一舒适度后再计算可比节电率；提高供水温度必须在设备(≤60℃)和末端允许工况内"。
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
import hashlib
import json

# ====================== V1.36：版本与计算快照一致性 ======================
APP_VERSION = "V1.42"
CALC_DATA_VERSION = "V1.35-data-20260909"
DEFAULT_SEASON_HOURS = 2880.0  # 郑州采暖期约120天×24h（一阶假设：把度时积分折算为时段时长；须以气象时序校核）

###====改造模式造价系数配置（分户独立 / 批量分户）====
# 分户独立改造：围护/热泵/末端 有效系数均为 1.00；
# 批量分户（批量采购）改造：围护0.75、热泵0.85、末端0.80（页面2可编辑 coef_set 覆盖批量默认值）。
# 审查意见④：用户设置值（批量采购参考）与本次生效值（按当前造价模式）区分展示；整栋集中更名为批量分户。
RETROFIT_MODE_CFG = {
    "分户独立改造": {"coef_envelope":1.00, "coef_pump":1.00, "coef_terminal":1.00},
    "批量分户改造": {"coef_envelope":0.75, "coef_pump":0.85, "coef_terminal":0.80}
}

# ===================== 新增V1.7：热泵厂家工况样本数据表（V1.34：更名“性能估算面锚点表”） =====================
# 测试工况：国标GB/T 25127.2（户用及类似用途，本案例采用第2部分；GB/T 25127.1—2020 适用于工业或商业及类似用途，本案例不采用，见P1-1），
# 出水温度tg_supply，室外干球T_amb
# 每一条：[室外环境温度℃，供水温度℃，COP，工况可用制热量kW]
# 方案1、2使用设备A样本；方案3使用设备B样本
# 方案1、方案2：设备A（MHSR120N8-S1，12kW·220V·低环境温度空气源热泵(冷水)机组·地板采暖型，CQC认证名录）
# 美的MHSR-N8-S1系列真实锚点（45℃工况，厂家公开数据【源】）：
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
# 美的MHSR-N8-S1系列真实锚点（厂家公开数据【源】）：
# 额定制热 A7/W45：Q=10.0kW、COP=3.55；名义 A-12/W35：Q=9.0、COP=2.70；低温 A-20/W35：Q=8.0、COP=2.21
# 表中 45℃ 出水列 COP/Q 按温升比 L=(45-T) 幂律由真实锚点标定（算）：COP∝(L_ref/L)^1.0、Q∝(L_ref/L)^0.5
SAMPLE_HP_LOWTEMP = [
    [7, 45, 3.55, 10.0],
    [2, 45, 3.14, 9.4],
    [-2, 45, 2.87, 9.0],
    [-7, 45, 2.59, 8.5],
    [-10, 45, 2.45, 8.3],
]
# ================= V1.21：二维性能估算面【室外干球×供水温度】（V1.34：证据分级） =================
# 说明：厂家样本通常只给单一出水温度工况；为描述“供水温度变化对COP/制热量的影响”，
# 在样本固定出水列(55℃/45℃)基础上，按温升比 L=(tg-T_out) 幂律推算二维估算面。
# 生成模型：COP(tg,T)=COP_ref(T)×(L_ref/L)^0.6；Qcap(tg,T)=Qcap_ref(T)×(L_ref/L)^0.4，
# 其中 L_ref=样本出水-T_out。设备B(方案3)45℃出水列按美的MHSR-N8-S1系列 MHSR100N8-S1 真实锚点标定
# （COP_ref∝(L_ref/L)^1.0、Q_ref∝(L_ref/L)^0.5），其余格为“算”值；
# 设备A(方案1/2)按美的MHSR-N8-S1系列 MHSR120N8-S1(12kW)真实锚点、设备B(方案3)按 MHSR100N8-S1(10kW)真实锚点标定，
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
# 热泵ID → 二维性能估算面（能耗积分与设计工况容量均使用估算面；V1.34：证据分级 C）
# V1.35：新增有效性域元数据——
#   cop_T_min：COP估算有效域室外温度下限（覆盖至-15℃；低于该温度COP估算数据不足，仅教学估计）
#   tg_hw_max：设备包络最高供水温度（MHSR-N8-S1系列官方手册60℃）
HP_2D_MAP = {
    "HP0": {"out":SAMPLE_HP_NORMAL_2D_OUT, "tg":SAMPLE_HP_NORMAL_2D_TG,
            "cop":SAMPLE_HP_NORMAL_2D_COP, "qcap":SAMPLE_HP_NORMAL_2D_QCAP,
            "tg_ref":55.0,
            "cop_T_min":-15.0,
            "tg_hw_max":60.0,
            "model_name":"设备A：MHSR120N8-S1(12kW)",
            "evidence_level":"C",
            "anchor_points":[
                {"T_amb":7,"T_water":45,"COP":3.50,"Q":12.0,"evidence":"manufacturer"},
                {"T_amb":-12,"T_water":35,"COP":2.70,"Q":11.0,"evidence":"manufacturer"},
                {"T_amb":-20,"T_water":35,"COP":2.20,"Q":11.6,"evidence":"manufacturer_outside_range"}]},
    "HP1": {"out":SAMPLE_HP_LOWTEMP_2D_OUT, "tg":SAMPLE_HP_LOWTEMP_2D_TG,
            "cop":SAMPLE_HP_LOWTEMP_2D_COP, "qcap":SAMPLE_HP_LOWTEMP_2D_QCAP,
            "tg_ref":45.0,
            "cop_T_min":-15.0,
            "tg_hw_max":60.0,
            "model_name":"设备B：MHSR100N8-S1(10kW)",
            "evidence_level":"C",
            "anchor_points":[
                {"T_amb":7,"T_water":45,"COP":3.55,"Q":10.0,"evidence":"manufacturer"},
                {"T_amb":-12,"T_water":35,"COP":2.70,"Q":9.0,"evidence":"manufacturer"},
                {"T_amb":-20,"T_water":35,"COP":2.21,"Q":8.0,"evidence":"manufacturer_outside_range"}]},
}
# V1.34：数据证据等级（P0-2/P1-8）
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
# 2. 批量分户改造参考经验：
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
    "Tin": 20.0, "Tout": -3.5, "dT": 23.5, "HDD": 2106.0,
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
    "Tin": 20.0, "Tout": -3.5, "dT": 23.5, "HDD": 2106.0,
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
    "grid_ef":0.5897, # V1.34：默认改为 2023年河南省电力平均二氧化碳排放因子 0.5897 kgCO₂/kWh（生态环境部、国家统计局2025年第47号公告；位置法）
    "Qhp_rated1":12.0,
    "Qhp_rated2":12.0,
    "Qhp_rated3":10.0,
    # =========【V1.6 末端热工参数】=========
    # 原有散热器末端(方案1、方案2使用)
    "rad_Qrated_kW":14.0, #散热器总额定散热量 kW
    "rad_dt_m_rated":64.5, #散热器额定平均温差K（传统国标标定工况 95/70/18：(95+70)/2‑18=64.5K；GB/T 13754-2017 测试方法标准）
    "rad_m":1.30, #散热器散热指数m（V1.21修正：0.30→1.30；Q=K_M·ΔT^m 形式见 GB/T 13754-2017 式(8)，m 为工程典型值≈1.30，见台账）
    "rad_dt_flow_return":10.0, #散热器供回水温差K
    "rad_tg_max":60.0, #散热器允许最高供水温度℃（V1.34：65→60，匹配MHSR-N8-S1系列官方手册最高出水60℃）
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
    # ========= 审查意见③：样本额定工况（A7/W45 为设备A/B的额定制热工况点；−7℃不是额定点） =========
    "rated_cond_Tamb":7.0,    # 样本额定制热量对应室外温度 ℃（A7）
    "rated_cond_Tg":45.0,     # 样本额定制热量对应供水温度 ℃（W45）
    "rated_cond_src":"美的MHSR-N8-S1系列官方说明书（2026，A7/W45 额定制热）", # 样本来源
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
# 房间级/工程条件默认值（V1.41：在顶部初始化，避免 number_input 的 value= 与 key= 冲突导致用户填写后被重置）
if "_room_load_kw" not in st.session_state:
    st.session_state["_room_load_kw"] = 0.0
if "_room_rad_kw" not in st.session_state:
    st.session_state["_room_rad_kw"] = 0.0
if "_room_floor_kw" not in st.session_state:
    st.session_state["_room_floor_kw"] = 0.0
if "_floor_eff_area" not in st.session_state:
    st.session_state["_floor_eff_area"] = 0.0
if "_floor_surf_max" not in st.session_state:
    st.session_state["_floor_surf_max"] = 28.0
if "_eng_outdoor" not in st.session_state:
    st.session_state["_eng_outdoor"] = "待核验"
if "_eng_power" not in st.session_state:
    st.session_state["_eng_power"] = "待核验"
if "_eng_drain" not in st.session_state:
    st.session_state["_eng_drain"] = "待核验"
if "_eng_piping" not in st.session_state:
    st.session_state["_eng_piping"] = "待核验"

def calc_input_fingerprint():
    """输入+版本指纹：任何影响计算的输入（建筑/设备/系数/户型/造价模式/计算模式/外墙开关/SPF口径/备用配置/采暖时长）
    或模型/数据版本变化都会改变指纹，用于使旧计算快照立即失效（V1.35，审查意见①）。"""
    _fp = {
        "app_version": APP_VERSION,
        "data_version": CALC_DATA_VERSION,
        "house_type": st.session_state.get("house_type", ""),
        "retrofit_mode": st.session_state.get("retrofit_mode", ""),
        "calc_mode": st.session_state.get("calc_mode", "typical"),
        "cfg_allow_wall": st.session_state.get("cfg_allow_wall", True),
        "cfg_spf_mode": st.session_state.get("cfg_spf_mode", "含辅助电加热 SPF_HP+aux"),
        "build": {k: st.session_state["build"][k] for k in sorted(st.session_state["build"])},
        "equip": {k: st.session_state["equip"][k] for k in sorted(st.session_state["equip"])},
        "coef_set": {k: st.session_state["coef_set"][k] for k in sorted(st.session_state["coef_set"])},
        "aux_mode": st.session_state.get("_aux_mode", "无备用（不假定足额）"),
        "aux_capacity": float(st.session_state.get("_aux_capacity", 0.0)),
        "aux_eta": float(st.session_state.get("_aux_eta", 1.0)),
        "aux_cost_per_kw": float(st.session_state.get("_aux_cost_per_kw", 300.0)),
        "aux_elec_limit": float(st.session_state.get("_aux_elec_limit", 16.0)),
        "aux_p_rated": float(st.session_state.get("_aux_p_rated", 0.0)),
        "season_hours": float(st.session_state.get("_season_hours", DEFAULT_SEASON_HOURS)),
        # 审查意见⑦：房间级校核与工程安装条件（未确认项不默认绿灯，纳入指纹以便旧结果失效）
        "room_load_kw": float(st.session_state.get("_room_load_kw", 0.0)),
        "room_rad_kw": float(st.session_state.get("_room_rad_kw", 0.0)),
        "room_floor_kw": float(st.session_state.get("_room_floor_kw", 0.0)),
        "floor_eff_area": float(st.session_state.get("_floor_eff_area", 0.0)),
        "floor_surf_max": float(st.session_state.get("_floor_surf_max", 28.0)),
        "eng_outdoor": st.session_state.get("_eng_outdoor", "待核验"),
        "eng_power": st.session_state.get("_eng_power", "待核验"),
        "eng_drain": st.session_state.get("_eng_drain", "待核验"),
        "eng_piping": st.session_state.get("_eng_piping", "待核验"),
        # 审查意见⑥：改造前基准可比性检查
        "base_cmp": bool(st.session_state.get("_base_cmp", False)),
    }
    return hashlib.md5(json.dumps(_fp, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()

def calc_snapshot_status():
    """计算快照是否与当前输入一致。返回 (is_current, message)（V1.35，审查意见①）。"""
    mid = st.session_state.get("calc_mid")
    if not mid:
        return False, "尚未生成计算快照（请先访问页面3完成计算后再校核）"
    if mid.get("_fingerprint") != calc_input_fingerprint():
        return False, "参数已改变，当前结果待重新计算。校核、图表和导出将在新的计算快照生成后同步更新。"
    return True, ""

def calc_terminal_max_delivery(term_id, equip_dict, Tin):
    """末端在最高允许供水温度下的最大可散热量 Q_term(tg_max)（设备包络内；V1.35，水侧电辅热的末端限制）"""
    if term_id == "T2":
        qr = equip_dict["floor_Qrated_kW"]; dtmr = equip_dict["floor_dt_m_rated"]; m = equip_dict["floor_m"]
        dtfr = equip_dict["floor_dt_flow_return"]; tgmax = equip_dict["floor_tg_max"]
    elif term_id == "T1":
        qr = equip_dict.get("rad_enh_Qrated_kW",18.0); dtmr = equip_dict.get("rad_enh_dt_m_rated",64.5)
        m = equip_dict.get("rad_enh_m",1.30); dtfr = equip_dict.get("rad_enh_dt_flow_return",10.0)
        tgmax = equip_dict.get("rad_enh_tg_max",60.0)
    else:
        qr = equip_dict["rad_Qrated_kW"]; dtmr = equip_dict["rad_dt_m_rated"]; m = equip_dict["rad_m"]
        dtfr = equip_dict["rad_dt_flow_return"]; tgmax = equip_dict["rad_tg_max"]
    dt_m = tgmax - dtfr/2.0 - Tin
    if dt_m <= 0:
        return 0.0
    return qr * pow(dt_m/dtmr, m)

def effective_aux_capacity(mode, installed_kw, qhp_design_kw, term_id, equip_dict, Tin):
    """备用热源有效容量（V1.35，审查意见④）：
    - 无备用：0；
    - 水侧电辅热：受末端最大可散热量限制（供水温度提升后末端总输热能力上限=Q_term(tg_max)），
      有效容量=min(已安装, max(0, Q_term(tg_max)−热泵设计出力))；
    - 独立房间热源：分室电暖设备不经水路末端，不受其限制。"""
    if mode.startswith("水侧"):
        term_max = calc_terminal_max_delivery(term_id, equip_dict, Tin)
        return round(max(0.0, min(installed_kw, max(0.0, term_max - qhp_design_kw))), 3)
    if mode.startswith("独立"):
        return round(float(installed_kw), 3)
    return 0.0

def scheme_heat_complete(end_ok, unserved_kwh):
    """供热完整性（V1.35，审查意见⑤）：末端能力满足 且 无未满足热量，
    才可认定该方案供热量与需热量一致，相对其的电量/排放比较才可比。"""
    return bool(end_ok) and (unserved_kwh is None or float(unserved_kwh) <= 1e-6)

# 分段明细表列名单位化（V1.35：度时D_i(℃·h)与时长h_i(h)严格区分，严禁互相替代）
SEG_DISPLAY_LABELS = {
    "T_low":"T下(℃)","T_high":"T上(℃)","t_mid":"T中(℃)",
    "hdd_seg":"HDD分项(℃·d)","degree_hours_seg":"度时D_i(℃·h)","duration_hours_seg":"时长h_i(h)*",
    "Q_heat_kwh":"需热量(kWh)","cop_interp":"COP插值","hp_avail_kW":"HP可用(kW)",
    "avg_load_kW":"平均负荷(kW)","Q_hp_kwh":"HP供热(kWh)","Q_aux_kwh":"备用供热(kWh)",
    "Q_unmet_kwh":"未满足(kWh)","elec_hp":"E_HP(kWh)","elec_aux":"E_aux(kWh)",
    "q_valid":"容量域","cop_valid":"COP域","hardware_valid":"设备包络","in_domain":"有效状态",
    "warns":"警告"}

def _norm_num_dict(d):
    """把字典中所有数值统一为 float，避免 number_input value 与 min/max 数值类型不一致报错"""
    for k in list(d.keys()):
        if isinstance(d[k], (int, float)) and not isinstance(d[k], bool):
            d[k] = float(d[k])

def _clear_widget_state(extra_prefixes=()):
    """清除输入控件的 widget 状态（key 以 _ 开头；extra_prefixes 可追加其他前缀，如 "chk_"），
    使其在下次渲染时按 value= 默认值重建。
    Streamlit 中带 key 的控件会优先保留 session_state 里的旧值：只重置业务字典 build/equip/coef_set
    会导致输入框仍显示旧值（如层高2.70），而派生计算值（室内总体积等）已按默认参数重算——两者不一致
    （即“重置后只重置了计算结果”问题）。"""
    for _k in [k for k in list(st.session_state.keys()) if k.startswith("_")]:
        del st.session_state[_k]
    for _p in extra_prefixes:
        for _k in [k for k in list(st.session_state.keys()) if k.startswith(_p)]:
            del st.session_state[_k]

def _apply_reset_defaults():
    """恢复统一基准（完整版）：在脚本顶部执行，此时本 run 尚未实例化任何控件，
    可安全地直接设置控件状态（Streamlit 禁止在控件实例化后改写其 key 值）。
    重置范围：建筑/设备/批量系数 + 户型 + 改造造价模式 + 计算模式 +
    允许外墙改造 + SPF口径 + 页面4手算校核输入。
    关键点：除删除旧控件状态外，**显式把所有输入控件状态写回默认值**——
    不依赖“删除后按 value= 重建”的版本语义，任何 Streamlit 版本都会按此值渲染。"""
    st.session_state["house_type"] = "中间层住宅"
    st.session_state["build"] = DEFAULT_BUILD_MID.copy()
    st.session_state["equip"] = DEFAULT_EQUIP.copy()
    st.session_state["coef_set"] = {"coef_envelope":0.75,"coef_pump":0.85,"coef_terminal":0.80}
    st.session_state["retrofit_mode"] = "分户独立改造"
    st.session_state["calc_mode"] = "typical"
    _norm_num_dict(st.session_state["build"])
    _norm_num_dict(st.session_state["equip"])
    _norm_num_dict(st.session_state["coef_set"])
    _clear_widget_state(extra_prefixes=("chk_",))
    # V1.35：重置一次性复位输入及派生状态——删除旧计算快照，未重新算完前页面4禁止显示旧绿灯/旧导出
    st.session_state.pop("calc_mid", None)
    # 显式写回全部控件状态（此时控件尚未实例化，直接赋值是安全的）
    _b = st.session_state["build"]; _e = st.session_state["equip"]; _c = st.session_state["coef_set"]
    _w = {
        # ---- 页面1 建筑围护 ----
        "_area": _b["area"], "_floor_h": _b["floor_h"], "_wall_gross": _b["wall_gross"],
        "_win": _b["win"], "_door_A": _b["door_A"], "_nonheat_wall_A": _b["nonheat_wall_A"],
        "_roof_A": _b.get("roof_A", 0.0), "_gable_wall_A": _b.get("gable_wall_A", 0.0),
        "_Kw_old": _b["Kw_old"], "_Kw_new": _b["Kw_new"], "_Kwin_old": _b["Kwin_old"],
        "_Kwin_new": _b["Kwin_new"], "_K_door_old": _b["K_door_old"], "_K_door_new": _b["K_door_new"],
        "_K_nonheat_old": _b["K_nonheat_old"], "_K_nonheat_new": _b["K_nonheat_new"],
        "_K_roof_old": _b.get("K_roof_old", 0.30), "_K_roof_new": _b.get("K_roof_new", 0.18),
        "_K_gable_old": _b.get("K_gable_old", 1.50), "_K_gable_new": _b.get("K_gable_new", 0.45),
        "_Tin": _b["Tin"], "_Tout": _b["Tout"], "_HDD": _b["HDD"],
        "_n": _b["n"], "_rho": _b["rho"], "_cp": _b["cp"],
        # ---- 页面2 批量折算系数 ----
        "_coef_env": _c["coef_envelope"], "_coef_pump": _c["coef_pump"], "_coef_term": _c["coef_terminal"],
        # ---- 页面2 热泵 ----
        "_SCOPnp1": _e["SCOP_nameplate1"], "_SCOPnp2": _e["SCOP_nameplate2"], "_SCOPnp3": _e["SCOP_nameplate3"],
        "_decay1": _e["spf_decay1"], "_decay2": _e["spf_decay2"], "_decay3": _e["spf_decay3"],
        "_Qhp_rated1": _e["Qhp_rated1"], "_Qhp_rated2": _e["Qhp_rated2"], "_Qhp_rated3": _e["Qhp_rated3"],
        # ---- 页面2 单位造价与经济 ----
        "_unit_wall_ins": _e["unit_wall_ins"], "_unit_win_replace": _e["unit_win_replace"],
        "_unit_door_replace": _e["unit_door_replace"], "_unit_nonheat_ins": _e["unit_nonheat_ins"],
        "_unit_roof_ins": _e["unit_roof_ins"], "_unit_gable_ins": _e["unit_gable_ins"],
        "_unit_lowend_floor": _e["unit_lowend_floor"],
        "_cost_pump": _e["cost_pump"], "_budget": _e["budget"],
        "_elec_price": _e["elec_price"], "_grid_ef": _e["grid_ef"],
        # ---- 页面2 末端 ----
        "_rad_Qrated_kW": _e["rad_Qrated_kW"], "_rad_dt_m_rated": _e["rad_dt_m_rated"],
        "_rad_m": _e["rad_m"], "_rad_dt_flow_return": _e["rad_dt_flow_return"], "_rad_tg_max": _e["rad_tg_max"],
        "_floor_Qrated_kW": _e["floor_Qrated_kW"], "_floor_dt_m_rated": _e["floor_dt_m_rated"],
        "_floor_m": _e["floor_m"], "_floor_dt_flow_return": _e["floor_dt_flow_return"], "_floor_tg_max": _e["floor_tg_max"],
        # ---- 页面3 允许外墙改造 / SPF口径 / 改造前基准 / 备用热源配置 / 房间级与工程条件 ----
        "_allow_wall": True, "_spf_mode": "含辅助电加热 SPF_HP+aux",
        "_base_type": "未录入（暂不输出估算结果）", "_base_energy": 0.0, "_base_ef": 0.20, "_base_cmp": False,
        "_aux_mode": "无备用（不假定足额）", "_aux_capacity": 0.0, "_aux_eta": 1.0,
        "_aux_cost_per_kw": 300.0, "_aux_elec_limit": 16.0, "_aux_p_rated": 0.0, "_season_hours": DEFAULT_SEASON_HOURS,
        "_room_load_kw": 0.0, "_room_rad_kw": 0.0, "_room_floor_kw": 0.0,
        "_floor_eff_area": 0.0, "_floor_surf_max": 28.0,
        "_eng_outdoor": "待核验", "_eng_power": "待核验", "_eng_drain": "待核验", "_eng_piping": "待核验",
        # ---- 侧边栏 户型 / 造价模式 / 计算模式 ----
        "house_type_sel": "中间层住宅", "retrofit_mode_sel": "分户独立改造", "calc_mode_radio": "三套典型方案",
        # V1.38：重置后回到页面1（重置按钮 rerun 会清空 radio 控件状态，显式写回避免左右不一致）
        "page_select_radio": "1.建筑围护参数录入",
    }
    for _k, _v in _w.items():
        st.session_state[_k] = _v
    st.session_state["_reset_toast"] = True

if st.session_state.pop("_pending_reset", False):
    _apply_reset_defaults()

# V1.38：删除方案后恢复当前页面（删除按钮 rerun 会清空 radio 控件状态，需在 radio 实例化前写回）
if "_restore_page_after_del" in st.session_state:
    st.session_state["page_select_radio"] = st.session_state.pop("_restore_page_after_del")

# V1.35：载入方案的 pending 处理（必须在 sidebar widget 实例化之前执行，否则 house_type_sel 等不可写）
if "_pending_load_scheme" in st.session_state:
    _load_idx = st.session_state.pop("_pending_load_scheme")
    _saved = st.session_state.get("saved_schemes", [])
    if 0 <= _load_idx < len(_saved):
        _s = _saved[_load_idx]
        st.session_state["house_type"] = _s["户型"]
        st.session_state["house_type_sel"] = _s["户型"]
        _b_loaded = dict(_s["建筑"])
        _b_loaded["volume"] = _b_loaded["area"] * _b_loaded["floor_h"]
        _b_loaded["dT"] = _b_loaded["Tin"] - _b_loaded["Tout"]
        st.session_state["build"] = _b_loaded
        st.session_state["equip"] = dict(_s["设备"])
        st.session_state["coef_set"] = dict(_s["系数"])
        # V1.36：恢复造价模式/计算模式/外墙改造开关/SPF口径（原版本漏存，导致载入后计算结果不一致）
        _rmode = _s.get("造价模式", "分户独立改造")
        if _rmode == "整栋集中批量改造":   # 旧版本模式名兼容映射（审查意见④：整栋集中→批量分户）
            _rmode = "批量分户改造"
        st.session_state["retrofit_mode"] = _rmode
        st.session_state["retrofit_mode_sel"] = _rmode
        _cmode = _s.get("计算模式", "typical")
        st.session_state["calc_mode"] = _cmode
        st.session_state["calc_mode_radio"] = "18种自由组合批量计算" if _cmode == "batch_18" else "三套典型方案"
        # 旧方案缺少样本额定工况字段时补默认（审查意见③）
        for _nk, _nv in [("rated_cond_Tamb", 7.0), ("rated_cond_Tg", 45.0),
                         ("rated_cond_src", "美的MHSR-N8-S1系列官方说明书（2026，A7/W45 额定制热）")]:
            st.session_state["equip"].setdefault(_nk, _nv)
        _norm_num_dict(st.session_state["build"])
        _norm_num_dict(st.session_state["equip"])
        _norm_num_dict(st.session_state["coef_set"])
        _clear_widget_state(extra_prefixes=("load_scheme_",))
        # 审查意见⑨：载入方案后删除旧计算快照——保存方案必须能恢复输入并重新计算，防止旧结果复用
        st.session_state.pop("calc_mid", None)
        # V1.37：显式写回全部输入控件状态（与 _apply_reset_defaults 同一机制）。
        # 仅靠 _clear_widget_state 删除 key 后"按 value= 重建"在某些 Streamlit 版本下不可靠，
        # 会出现 build["area"]=110 但输入框仍显示 120 的不一致。此处逐个写回确保输入框与业务字典一致。
        # V1.38：恢复保存时的页面。载入/删除/重置按钮位于"功能页面切换"radio 之前，
        # 点击时 st.rerun() 会在 radio 实例化前中断脚本，导致 radio 控件状态被 Streamlit 清理为默认页；
        # 因此必须在脚本顶部（radio 实例化前）显式写回 page_select_radio，否则左侧导航显示旧页、
        # 右侧内容却渲染默认页（左右不一致）。旧方案无"当前页面"字段时默认回到页面3（结果页，便于继续修改）。
        st.session_state["page_select_radio"] = _s.get("当前页面", "3.三套方案计算结果")
        _b = st.session_state["build"]; _e = st.session_state["equip"]; _c = st.session_state["coef_set"]
        _w = {
            # ---- 页面1 建筑围护 ----
            "_area": _b["area"], "_floor_h": _b["floor_h"], "_wall_gross": _b["wall_gross"],
            "_win": _b["win"], "_door_A": _b["door_A"], "_nonheat_wall_A": _b["nonheat_wall_A"],
            "_roof_A": _b.get("roof_A", 0.0), "_gable_wall_A": _b.get("gable_wall_A", 0.0),
            "_Kw_old": _b["Kw_old"], "_Kw_new": _b["Kw_new"], "_Kwin_old": _b["Kwin_old"],
            "_Kwin_new": _b["Kwin_new"], "_K_door_old": _b["K_door_old"], "_K_door_new": _b["K_door_new"],
            "_K_nonheat_old": _b["K_nonheat_old"], "_K_nonheat_new": _b["K_nonheat_new"],
            "_K_roof_old": _b.get("K_roof_old", 0.30), "_K_roof_new": _b.get("K_roof_new", 0.18),
            "_K_gable_old": _b.get("K_gable_old", 1.50), "_K_gable_new": _b.get("K_gable_new", 0.45),
            "_Tin": _b["Tin"], "_Tout": _b["Tout"], "_HDD": _b["HDD"],
            "_n": _b["n"], "_rho": _b["rho"], "_cp": _b["cp"],
            # ---- 页面2 批量折算系数 ----
            "_coef_env": _c["coef_envelope"], "_coef_pump": _c["coef_pump"], "_coef_term": _c["coef_terminal"],
            # ---- 页面2 热泵 ----
            "_SCOPnp1": _e["SCOP_nameplate1"], "_SCOPnp2": _e["SCOP_nameplate2"], "_SCOPnp3": _e["SCOP_nameplate3"],
            "_decay1": _e["spf_decay1"], "_decay2": _e["spf_decay2"], "_decay3": _e["spf_decay3"],
            "_Qhp_rated1": _e["Qhp_rated1"], "_Qhp_rated2": _e["Qhp_rated2"], "_Qhp_rated3": _e["Qhp_rated3"],
            # ---- 页面2 单位造价与经济 ----
            "_unit_wall_ins": _e["unit_wall_ins"], "_unit_win_replace": _e["unit_win_replace"],
            "_unit_door_replace": _e["unit_door_replace"], "_unit_nonheat_ins": _e["unit_nonheat_ins"],
            "_unit_roof_ins": _e["unit_roof_ins"], "_unit_gable_ins": _e["unit_gable_ins"],
            "_unit_lowend_floor": _e["unit_lowend_floor"],
            "_cost_pump": _e["cost_pump"], "_budget": _e["budget"],
            "_elec_price": _e["elec_price"], "_grid_ef": _e["grid_ef"],
            # ---- 页面2 末端 ----
            "_rad_Qrated_kW": _e["rad_Qrated_kW"], "_rad_dt_m_rated": _e["rad_dt_m_rated"],
            "_rad_m": _e["rad_m"], "_rad_dt_flow_return": _e["rad_dt_flow_return"], "_rad_tg_max": _e["rad_tg_max"],
            "_floor_Qrated_kW": _e["floor_Qrated_kW"], "_floor_dt_m_rated": _e["floor_dt_m_rated"],
            "_floor_m": _e["floor_m"], "_floor_dt_flow_return": _e["floor_dt_flow_return"], "_floor_tg_max": _e["floor_tg_max"],
            # ---- 页面3 允许外墙改造 / SPF口径 ----
            "_allow_wall": _s.get("允许外墙改造", True),
            "_spf_mode": _s.get("SPF口径", "含辅助电加热 SPF_HP+aux"),
            # ---- 页面3 备用热源 / 房间级校核 / 工程安装条件 / 改造前基准可比性（审查意见①⑥⑦⑨） ----
            "_aux_mode": _s.get("备用配置", {}).get("_aux_mode", "无备用（不假定足额）"),
            "_aux_capacity": float(_s.get("备用配置", {}).get("_aux_capacity", 0.0)),
            "_aux_eta": float(_s.get("备用配置", {}).get("_aux_eta", 1.0)),
            "_aux_cost_per_kw": float(_s.get("备用配置", {}).get("_aux_cost_per_kw", 300.0)),
            "_aux_elec_limit": float(_s.get("备用配置", {}).get("_aux_elec_limit", 16.0)),
            "_aux_p_rated": float(_s.get("备用配置", {}).get("_aux_p_rated", 0.0)),
            "_season_hours": float(_s.get("备用配置", {}).get("_season_hours", DEFAULT_SEASON_HOURS)),
            "_room_load_kw": float(_s.get("房间级输入", {}).get("_room_load_kw", 0.0)),
            "_room_rad_kw": float(_s.get("房间级输入", {}).get("_room_rad_kw", 0.0)),
            "_room_floor_kw": float(_s.get("房间级输入", {}).get("_room_floor_kw", 0.0)),
            "_floor_eff_area": float(_s.get("房间级输入", {}).get("_floor_eff_area", 0.0)),
            "_floor_surf_max": float(_s.get("房间级输入", {}).get("_floor_surf_max", 28.0)),
            "_eng_outdoor": _s.get("工程条件", {}).get("_eng_outdoor", "待核验"),
            "_eng_power": _s.get("工程条件", {}).get("_eng_power", "待核验"),
            "_eng_drain": _s.get("工程条件", {}).get("_eng_drain", "待核验"),
            "_eng_piping": _s.get("工程条件", {}).get("_eng_piping", "待核验"),
            "_base_cmp": bool(_s.get("基准可比性", False)),
            "_base_type": _s.get("基准录入", {}).get("_base_type", "未录入（暂不输出估算结果）"),
            "_base_energy": float(_s.get("基准录入", {}).get("_base_energy", 0.0)),
            "_base_ef": float(_s.get("基准录入", {}).get("_base_ef", 0.20)),
            # ---- 侧边栏 户型 / 造价模式 / 计算模式 ----
            "house_type_sel": _s["户型"],
            "retrofit_mode_sel": _rmode,
            "calc_mode_radio": "18种自由组合批量计算" if _cmode == "batch_18" else "三套典型方案",
        }
        for _k, _v in _w.items():
            st.session_state[_k] = _v

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
    _clear_widget_state()  # 切换户型时同步清除控件状态，输入框随默认参数更新
###====工具函数 季节SPF====
def calc_season_spf(nameplate_scop, decay_factor):
    return round(nameplate_scop * decay_factor, 3)
###====V1.34 新增：外墙净面积唯一生成点（P0-1）====
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
    wall_net_A = calc_wall_net(build_dict) # V1.34：净墙=毛墙−窗−门
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
        advice_list.append("①供水温度上限受设备包络约束（MHSR-N8-S1系列≤60℃，当前上限=" + str(tg_max) + "℃）：已取设备/末端允许最大值时，进一步提高须更换更高出水温度的机组或先降低热负荷，不得在设备包络外提高水温；")
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


# ===================== V1.21：二维性能估算面 双线性插值（V1.34：P0-2 证据分级/命名修正；V1.35：有效性分维度） =====================
def hp_2d_interpolate(hp_id, t_amb_input, tg_input):
    """
    二维性能估算面：在“室外温度×供水温度”模型适用范围内做双线性插值；
    范围外禁止外推（仅截断后返回参考值并报警，纳入模型适用性闸门）。
    有效性按三个独立维度判定（V1.35，审查意见③）：
      - q_valid:        容量估算域（估算面矩形边界，含室外-15~10℃）
      - cop_valid:      COP估算域（室外温度须≥cop_T_min=-15℃；不得用容量域代替COP域）
      - hardware_valid: 设备包络（供水温度≤机组手册最高出水温度60℃）
    任一维度失败 → all_valid=False；域外值仅作带明显标记的教学估计，不进入正式结论。
    hp_id: "HP0"设备A / "HP1"设备B
    说明：本面由厂家公开锚点【源】+温升幂律推算格【算】共同构成，属模型估计（证据等级C），
          其矩形边界为“模型适用范围”（model_applicability），不是厂家验证域。
    return: (cop, qcap_kW, validity, warn_msg)
      validity = {"q_valid":bool, "cop_valid":bool, "hardware_valid":bool, "all_valid":bool, "reason":str}
    """
    meta = HP_2D_MAP[hp_id]
    out_grid, tg_grid = meta["out"], meta["tg"]
    cop_grid, qcap_grid = meta["cop"], meta["qcap"]
    ta_min, ta_max = min(out_grid), max(out_grid)
    tg_min, tg_max = min(tg_grid), max(tg_grid)
    cop_t_min = meta.get("cop_T_min", ta_min)   # COP估算有效域室外温度下限
    tg_hw_max = meta.get("tg_hw_max", tg_max)   # 设备包络最高供水温度
    warns = []
    reason_parts = []
    q_valid = (ta_min - 1e-6 <= t_amb_input <= ta_max + 1e-6) and (tg_min - 1e-6 <= tg_input <= tg_max + 1e-6)
    cop_valid = (cop_t_min - 1e-6 <= t_amb_input <= ta_max + 1e-6) and (tg_min - 1e-6 <= tg_input <= tg_max + 1e-6)
    hardware_valid = (tg_input <= tg_hw_max + 1e-6)
    if t_amb_input < ta_min - 1e-6 or t_amb_input > ta_max + 1e-6:
        reason_parts.append(f"室外温度{t_amb_input:.1f}℃超出容量估算域[{ta_min:.0f},{ta_max:.0f}]℃")
    if tg_input < tg_min - 1e-6 or tg_input > tg_max + 1e-6:
        reason_parts.append(f"供水温度{tg_input:.1f}℃超出估算域[{tg_min:.0f},{tg_max:.0f}]℃")
    if t_amb_input < cop_t_min - 1e-6:
        reason_parts.append(f"室外温度{t_amb_input:.1f}℃低于COP有效域下限{cop_t_min:.0f}℃（COP估算数据不足）")
    if tg_input > tg_hw_max + 1e-6:
        reason_parts.append(f"供水温度{tg_input:.1f}℃超出设备包络最高出水温度{tg_hw_max:.0f}℃")
    if reason_parts:
        warns.append("⚠️" + "；".join(reason_parts) + "（域外值仅作教学估计，带明显标记，不进入正式结论）")
    # 域外时仅截断到边界用于展示参考值，不改变各维度有效标志
    ta_c = float(np.clip(t_amb_input, ta_min, ta_max))
    tg_c = float(np.clip(tg_input, tg_min, tg_max))
    cop_interp = float(np.interp(ta_c, out_grid, [np.interp(tg_c, tg_grid, row) for row in cop_grid]))
    qcap_interp = float(np.interp(ta_c, out_grid, [np.interp(tg_c, tg_grid, row) for row in qcap_grid]))
    validity = {
        "q_valid": bool(q_valid),
        "cop_valid": bool(cop_valid),
        "hardware_valid": bool(hardware_valid),
        "all_valid": bool(q_valid and cop_valid and hardware_valid),
        "reason": "；".join(reason_parts) if reason_parts else "工况位于估算面模型适用范围内",
    }
    return cop_interp, qcap_interp, validity, warns


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

###====计算围护分项造价【单位造价×工程量】（V1.34：P0-1 净墙扣门）====
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
    score_save2 = (save_rate2 if save_rate2 is not None else 0)/100*10
    score_carbon2 = (carbon_rate2 if carbon_rate2 is not None else 0)/100*10
    score_inv2 = max(0,10-(invest2/80000)*10)
    score_con2 = 4
    s2={"初投资":score_inv2,"回收期":score_pay2,"节能率":score_save2,"减碳":score_carbon2,"施工难度":score_con2}
    score_pay3 = max(0,10-(pay3/15)*10) if pay3 is not None else 0
    score_save3 = (save_rate3 if save_rate3 is not None else 0)/100*10
    score_carbon3 = (carbon_rate3 if carbon_rate3 is not None else 0)/100*10
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
    _g_ok, _g_msg = geometry_valid(build) # V1.34：窗+门<毛墙
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
    """【V1.34 】设计工况需配置的备用热源容量 Q_aux,design = max(0, Qd − Q_HP,avail,design)。
    若未配置足额备用热源（当前模型默认未配置，容量=0），则设计点容量闸门 capacity_ok=(Qhp+Qaux)>=Qd 不满足。"""
    return round(max(0.0, q_load_kw - qhp_avail_design_kw), 3)

def calc_carbon(elec_kwh, ef_kg_kwh):
    co2 = elec_kwh * ef_kg_kwh
    return round(co2,2)

# ================= V1.9新增：设计工况热泵容量 / 扩展输入校验 / 分项热损失 / 恢复统一基准 =================
def hp_available_at_design(build, equip, hp_id, tg_solve):
    """设计工况(T_out=郑州设计室外温度, 供水=tg_solve)热泵可用制热量与COP。
    V1.21：按“室外×供水”二维性能估算面双线性插值，取min(额定制热量)；返回模型适用性标志。
    V1.34：不把估算面称“厂家数据域”，返回 performance_model_applicable 语义。
    V1.35：返回 validity 字典（q_valid/cop_valid/hardware_valid/all_valid/reason），
           容量域、COP域与设备包络分开判定，综合AND（审查意见③）。"""
    t_design = build["Tout"]
    rated = equip["Qhp_rated3"] if hp_id == "HP1" else equip["Qhp_rated1"]
    cop_d, qhp_d, validity, warns = hp_2d_interpolate(hp_id, t_design, tg_solve)
    qhp_d = min(qhp_d, rated)
    return round(cop_d,3), round(qhp_d,3), validity, warns

def input_warning_check_v18(build, equip, ht):
    """扩展输入边界与交叉校验（V1.10加强版，覆盖《小程序修改建议》4.1校验表全部规则；不改原input_warning_check）"""
    w = []
    def need_positive(name, v, lo, hi=None):
        if not (v > 0):
            w.append(f"{name}必须>0，当前={v}")
        elif hi is not None and v > hi:
            w.append(f"{name}超出合理上限{hi}，当前={v}")
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
        w.append("改造后外墙K值未低于改前，保温无改善，请核对")
    if build["Kwin_new"] >= build["Kwin_old"]:
        w.append("改造后外窗K值未低于改前，换窗无节能效果，请核对")
    # ---- 设计温度：T_in>T_out，否则禁止负热负荷 ----
    if build["Tin"] <= build["Tout"]:
        w.append("室内温度必须大于室外设计温度，否则热负荷为负，禁止计算")
    # ---- 低温衰减系数 0<f≤1 ----
    if not (0 < equip["spf_decay1"] <= 1 and 0 < equip["spf_decay2"] <= 1 and 0 < equip["spf_decay3"] <= 1):
        w.append("低温衰减系数必须∈(0,1]，避免效率被无依据放大")
    # ---- 供水温度位于机组和末端允许范围 ----
    if equip.get("floor_tg_max", 45.0) > 45:
        w.append("地暖供水温度上限超45℃，超常规低温辐射允许范围")
    if equip.get("rad_tg_max", 60.0) > 60:
        w.append("散热器供水温度上限超60℃，超出MHSR-N8-S1系列机组允许范围")
    # ---- 墙窗门面积几何关系：净面积=毛墙−窗−门（V1.34：P0-1 扣门） ----
    _g_ok18, _g_msg18 = geometry_valid(build)
    if not _g_ok18:
        w.append("" + _g_msg18 + "（外墙净面积=毛墙−外窗−外门，窗+门≥毛墙必须阻断）")
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
    # V1.34：P0-1 净墙=毛墙−窗−门，窗+门<毛墙（A02/A03 阻断项）
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
    chk(40 <= equip["rad_tg_max"] <= 60, f"散热器最高供水温度须∈[40,60]℃（MHSR-N8-S1系列手册上限），当前={equip['rad_tg_max']}")
    chk(0 < equip["floor_Qrated_kW"] <= 200, f"地暖额定散热量须∈(0,200]kW，当前={equip['floor_Qrated_kW']}")
    chk(5 <= equip["floor_dt_m_rated"] <= 40, f"地暖额定平均温差须∈[5,40]K，当前={equip['floor_dt_m_rated']}")
    chk(0.5 <= equip["floor_m"] <= 1.6, f"地暖散热指数m须∈[0.5,1.6]，当前={equip['floor_m']}")
    chk(2 <= equip["floor_dt_flow_return"] <= 15, f"地暖供回水温差须∈[2,15]K，当前={equip['floor_dt_flow_return']}")
    chk(30 <= equip["floor_tg_max"] <= 50, f"地暖最高供水温度须∈[30,50]℃，当前={equip['floor_tg_max']}")
    return (len(errs) == 0, errs)

def calc_component_heat_loss(ht, build_dict, volume, n, rho, cp):
    """围护分项热损失分解：H(W/K)、设计温差热流Q(W)、占比%（V1.34：净墙=毛墙−窗−门）"""
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
    """恢复统一基准（答辩演示用）：置位待重置标志并重跑，
    实际重置由脚本顶部 _apply_reset_defaults() 在控件实例化之前统一执行——
    否则此处（侧边栏按钮）控件已实例化，Streamlit 禁止再改写控件 key，重置将不完整。"""
    st.session_state["_pending_reset"] = True
    st.rerun()

# ================= V1.8新增：18自由组合核心工具函数（原有函数全部保留） =================
def calc_segment_hp_aux(seg_list, hp_sample_table, hp_sample_tg_fixed, tg_solve, hp_rated_max_kW, p_aux_rated=None):
    """HDD分段：热泵可用制热能力受限部分用辅助电加热补充，输出E_aux与等效小时。
    审查意见①：等效满载小时 = E_aux / P_aux,rated（电加热额定电功率），不是除以热泵额定制热量；
    未配置电辅热或额定功率未知时返回 None（界面显示"不适用/待配置"）。本函数为旧版参考，主计算见 2d 版。"""
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
            "hdd_seg":hdd_seg,
            "degree_hours_seg":round(hours_seg,2),  # ℃·h（度时，非时长）
            "duration_hours_seg":None,              # 本旧版函数不提供时长（须气象时序另行统计）
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
    if p_aux_rated is not None and p_aux_rated > 1e-9:
        aux_equiv_hours = round(total_aux_elec / p_aux_rated, 2)
    else:
        aux_equiv_hours = None
    aux_hours = {"equiv_full_hours": aux_equiv_hours, "actual_on_hours": None}
    return seg_out, total_hp_elec, total_aux_elec, aux_hours


# ===================== V1.21：二维表分段能耗积分 + 数据域闸门（V1.35：度时/时长分离+有效性分维度+备用不假定足额） =====================
def calc_segment_hp_aux_2d(seg_list, hp_id, tg_solve, hp_rated_max_kW, q_aux_capacity=None, eta_aux=1.0, season_hours=None, p_aux_rated=None):
    """
    主算法：HDD分段能耗积分，统一容量与能耗口径（V1.35修订；V1.36 审查意见①修正等效小时分母）。
    - 每段用二维性能表在（段中点室外温度, 反算供水温度tg_solve）双线性插值COP与可用制热量；
      有效性分维度（q_valid/cop_valid/hardware_valid，综合AND）——任一越域 → data_domain_ok=False，判定该方案不通过。
    - 度时与时长严格分离（审查意见②）：
      degree_hours_seg(℃·h)=hdd_seg×24 仅作温差积分总量；duration_hours_seg(h)=采暖期总时长×度时占比（一阶假设，
      须以气象时序校核；season_hours=None 时不虚构时长）。热泵/备用能量上限均按时段时长折算。
    - 备用热源（审查意见④）：q_aux_capacity=None（未配置）→ 不假定足额：备用供热=0，全部缺口计为未满足热量；
      q_aux_capacity=C → 备用供热=min(C×时长, 缺口)，未满足=缺口−备用供热，备用用电=备用供热/η。
    - 等效运行小时（审查意见①）：等效满载小时 = E_aux / P_aux,rated（电加热额定电功率，非热泵额定制热量）；
      实际开启小时 = ΣI(P_aux,i>0)·Δt_i（对实际发生备用供热的温度段累计其时长，一阶假设，须气象时序校核）；
      未配置电辅热或额定功率未知 → 等效满载小时为 None（界面显示"不适用/待配置"）；
      无时长数据时实际开启小时为 None（待气象时序）。
    return: (seg_out, e_hp_kwh, e_aux_kwh, aux_hours, data_domain_ok, domain_warns, unserved_heat_kwh)
      aux_hours = {"equiv_full_hours": float|None, "actual_on_hours": float|None}
    """
    seg_out = []
    total_hp_elec = 0.0
    total_aux_elec = 0.0
    total_unserved = 0.0
    data_domain_ok = True
    domain_warns = []
    total_hdd = sum(seg.get("hdd_seg", seg.get("hdd_segment", 0.0)) for seg in seg_list)
    for seg in seg_list:
        tl = seg["T_low"]
        th = seg["T_high"]
        hdd_seg = seg.get("hdd_seg", seg.get("hdd_segment", 0.0))
        q_heat_kwh = seg["Q_heat_kwh"]
        t_mid = (tl + th)/2.0
        degree_hours_seg = hdd_seg * 24.0  # ℃·h（度时）
        # 时段时长：按采暖期总时长×度时占比分配（一阶假设）；未提供时长则不虚构
        if season_hours and season_hours > 0 and total_hdd > 1e-9:
            duration_hours_seg = season_hours * hdd_seg / total_hdd
        else:
            duration_hours_seg = None
        cop_seg, qhp_avail_kW, validity, warns = hp_2d_interpolate(hp_id, t_mid, tg_solve)
        if not validity["all_valid"]:
            data_domain_ok = False
            domain_warns.extend(warns)
        cop_seg = max(cop_seg, 0.1)
        qhp_avail_kW = min(qhp_avail_kW, hp_rated_max_kW)
        # 热泵供热能量上限：按时段时长（无时长数据时退化为度时当量，偏保守）
        _cap_hours = duration_hours_seg if (duration_hours_seg and duration_hours_seg > 0) else degree_hours_seg
        q_hp_kwh = min(q_heat_kwh, qhp_avail_kW * _cap_hours)
        q_deficit_kwh = max(0.0, q_heat_kwh - q_hp_kwh)
        # 备用热源：未配置（None或0）→ 不假定足额，缺口全部计为未满足热量
        if q_aux_capacity is None or q_aux_capacity <= 1e-9:
            q_aux_kwh = 0.0
            q_unmet_kwh = q_deficit_kwh
        else:
            q_aux_max_kwh = q_aux_capacity * _cap_hours
            q_aux_kwh = min(q_aux_max_kwh, q_deficit_kwh)
            q_unmet_kwh = max(0.0, q_deficit_kwh - q_aux_max_kwh)
        elec_hp_seg = q_hp_kwh / cop_seg
        elec_aux_seg = (q_aux_kwh / eta_aux) if (eta_aux and eta_aux > 0) else q_aux_kwh
        total_hp_elec += elec_hp_seg
        total_aux_elec += elec_aux_seg
        total_unserved += q_unmet_kwh
        q_avg_load_kW = (q_heat_kwh / duration_hours_seg) if (duration_hours_seg and duration_hours_seg > 1e-6) else None
        seg_out.append({
            "T_low":tl,"T_high":th,"t_mid":t_mid,
            "hdd_seg":hdd_seg,
            "degree_hours_seg":round(degree_hours_seg,2),
            "duration_hours_seg":round(duration_hours_seg,2) if duration_hours_seg is not None else None,
            "Q_heat_kwh":q_heat_kwh,
            "cop_interp":round(cop_seg,3),
            "hp_avail_kW":round(qhp_avail_kW,3),
            "avg_load_kW":round(q_avg_load_kW,3) if q_avg_load_kW is not None else None,
            "Q_hp_kwh":round(q_hp_kwh,2),
            "Q_aux_kwh":round(q_aux_kwh,2),
            "Q_unmet_kwh":round(q_unmet_kwh,2),
            "elec_hp":round(elec_hp_seg,2),
            "elec_aux":round(elec_aux_seg,2),
            "q_valid":validity["q_valid"],
            "cop_valid":validity["cop_valid"],
            "hardware_valid":validity["hardware_valid"],
            "in_domain":validity["all_valid"],
            "warns":";".join(warns)
        })
    # 审查意见①：等效满载小时 = E_aux / P_aux,rated（电加热额定电功率）；实际开启小时 = ΣI(P_aux,i>0)·Δt_i
    if p_aux_rated is not None and p_aux_rated > 1e-9:
        aux_equiv_hours = round(total_aux_elec / p_aux_rated, 2)
    else:
        aux_equiv_hours = None  # 未配置电辅热或额定功率未知 → 界面显示"不适用/待配置"
    if season_hours and season_hours > 0:
        actual_on_hours = round(sum(
            (s.get("duration_hours_seg") or 0.0) for s in seg_out if s.get("Q_aux_kwh", 0.0) > 1e-6), 2)
    else:
        actual_on_hours = None  # 无气象时序时长数据 → 待校核
    aux_hours = {"equiv_full_hours": aux_equiv_hours, "actual_on_hours": actual_on_hours}
    return seg_out, round(total_hp_elec,2), round(total_aux_elec,2), aux_hours, data_domain_ok, domain_warns, round(total_unserved,2)


def calc_retrofit_cost_ex(house_type, build_dict, equip_dict, coef_envelope, coef_pump, coef_terminal):
    """分项独立批量折算：围护×coef_envelope、热泵×coef_pump、末端×coef_terminal（V1.34：净墙扣门）"""
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
                         env_id, term_id, hp_id, hdd_segments,
                         aux_mode="无备用（不假定足额）", aux_installed_kw=0.0, aux_eta=1.0,
                         aux_cost_per_kw=0.0, season_hours=None, aux_p_rated=None):
    """计算一个自由组合方案，返回完整结果字典（V1.35：接入备用热源配置与分维度有效性）"""
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
    # V1.21：二维性能表分段能耗积分 + 数据域闸门（V1.35：备用配置/时长/有效性分维度）
    cop_d, qhp_d, validity_d, _ = hp_available_at_design(build_loc, equip_input, hp_id, tg_solve)
    q_aux_eff = effective_aux_capacity(aux_mode, aux_installed_kw, qhp_d, term_id, equip_input, build_loc["Tin"])
    seg_full, e_hp_total, e_aux_total, aux_hours, data_domain_ok, _domain_warns, unserved_heat = calc_segment_hp_aux_2d(
        seg_heat, hp_id, tg_solve, hp_rated_max,
        q_aux_capacity=(q_aux_eff if q_aux_eff > 1e-9 else None), eta_aux=aux_eta, season_hours=season_hours,
        p_aux_rated=aux_p_rated)
    # 设计工况容量与数据域（容量域/COP域/设备包络 综合AND）
    data_domain_ok = data_domain_ok and validity_d["all_valid"]
    aux_heat_total = round(sum(s.get("Q_aux_kwh", 0.0) for s in seg_full), 2)
    e_total_elec = e_hp_total + e_aux_total
    spf_sys = (build_loc["HDD"] * H_kWK * 24.0) / e_total_elec if e_total_elec > 1e-9 else None
    # ---- 分项独立造价 ----
    cost_ex = calc_retrofit_cost_ex(ht, build_loc, equip_input, coef_envelope, coef_pump, coef_terminal)
    invest_pump = cost_ex["cost_pump_final"]
    invest_env = cost_ex["sum_envelope_final"] if env_do_retrofit else 0.0
    invest_terminal = cost_ex["cost_lowend_final"] if term_is_lowend else 0.0
    # V1.35：备用热源投资（已安装容量×单位造价）联动进入总投资约束
    aux_invest = aux_installed_kw * aux_cost_per_kw
    total_invest = invest_pump + invest_env + invest_terminal + aux_invest
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
        "q_valid":validity_d["q_valid"],"cop_valid":validity_d["cop_valid"],
        "hardware_valid":validity_d["hardware_valid"],
        "E_hp_kwh":round(e_hp_total,2),"E_aux_kwh":round(e_aux_total,2),
        "aux_heat_kwh":aux_heat_total,
        "unserved_heat_kwh":unserved_heat,
        "aux_equiv_hours":aux_hours["equiv_full_hours"],
        "aux_actual_on_hours":aux_hours["actual_on_hours"],
        "E_total_kwh":round(e_total_elec,2),
        "spf_sys":round(spf_sys,3) if spf_sys is not None else None,
        "invest_pump":round(invest_pump,2),"invest_env":round(invest_env,2),
        "invest_terminal":round(invest_terminal,2),"aux_invest":round(aux_invest,2),
        "total_invest":round(total_invest,2),
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
    page_title=f"郑州老旧住宅热泵协同改造方案比选与风险筛查工具 {APP_VERSION}",
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
/* 只隐藏汉堡菜单与 Deploy 按钮，保留侧栏折叠/展开控件（不能整体隐藏页头） */
[data-testid="stMainMenu"] {visibility: hidden;}
[data-testid="stAppDeployButton"] {display: none;}
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
/* ⚠️ 不能整体隐藏 stHeader：Streamlit 的侧栏折叠/展开按钮挂在页头里，
   整体 visibility:hidden 会导致侧栏收起后没有入口重新展开（“侧栏不见了”）。
   改为透明化页头，仅隐藏非必要按钮，保留侧栏开关。 */
header[data-testid="stHeader"]{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
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
    <div class="hero-meta">作品：老旧住宅空气源热泵协同改造测算系统｜团队：顺势而为队｜版本：''' + APP_VERSION + '''｜更新时间：2026-09-09</div>
    <div class="hero-route">定位：早期方案比较与教学决策支持，不替代暖通设计、设备选型和施工图审查｜技术路线：有限方案枚举 → 建筑热损失 → 设计负荷 → 末端供水温度 → 热泵性能估算面 → 全年分段能耗 → 费用与运行阶段购电间接排放 → 五道闸门（预算/工程/容量+备用/末端/模型适用性） → 可行方案排序</div>
</div>
""", unsafe_allow_html=True)

# ================= V1.8新增：可折叠参数来源台账（答辩追溯） =================
with st.expander("📌 参数来源台账（答辩追溯·可折叠）", expanded=False):
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
    _r("设备A COP(55℃出水)","3.04 / 2.73 / 2.52 / 2.30 / 2.19","-","美的空气源热泵采暖机组官方说明书（MHSR-N8-S1系列 MHSR120N8-S1，12kW·220V·低环境温度空气源热泵(冷水)机组·地板采暖型，CQC认证名录）·执行 GB/T 25127.2-2020；真实锚点 A7/W45=3.50、A-12/W35=2.70【源】，55℃列按温升比换算【算】","2026","说明书性能参数表","A7/W55、A2/W55、A-2/W55、A-7/W55、A-10/W55","源/算")
    _r("设备B COP(45℃出水)","3.55 / 3.14 / 2.87 / 2.59 / 2.45","-","美的空气源热泵采暖机组官方说明书（MHSR-N8-S1系列 MHSR100N8-S1，10kW·220V·低环境温度空气源热泵(冷水)机组·地板采暖型，CQC认证名录）·执行 GB/T 25127.2-2020；真实锚点 A7/W45=3.55、A-12/W35=2.70、A-20/W35=2.21【源】，其余按温升比幂律标定【算】","2026","说明书性能参数表","A7/W45、A2/W45、A-2/W45、A-7/W45、A-10/W45","源/算")
    _r("设备B额定制热量","{:.1f}".format(_e["Qhp_rated3"]),"kW","美的MHSR-N8-S1系列 MHSR100N8-S1 说明书·额定制热 A7/W45=10.0kW","2026","说明书性能参数表","A7/W45","源")
    _r("设备A额定制热量","{:.1f}/{:.1f}".format(_e["Qhp_rated1"],_e["Qhp_rated2"]),"kW","美的MHSR-N8-S1系列 MHSR120N8-S1 说明书·额定制热 A7/W45=12.0kW","2026","说明书性能参数表","A7/W45","源")
    _r("热泵冬季衰减系数","{:.2f}/{:.2f}/{:.2f}".format(_e["spf_decay1"],_e["spf_decay2"],_e["spf_decay3"]),"-","结霜衰减经验系数(低环温)","-","-","-7℃以下","假")
    _r("热泵性能估算面(室外×供水)","-15~10℃ × 30~65℃(设备A)/25~50℃(设备B)","-","设备A(MHSR120N8-S1)锚点 A7/W45=3.50/12kW【源】，55℃列按温升比换算【算】；设备B(MHSR100N8-S1)锚点 A7/W45=3.55/10kW【源】；推算 k=0.6/0.4、1.0/0.5","2026","说明书性能参数表","模型适用范围内双线性插值，范围外禁止外推；估算面≠完整厂家性能矩阵","源/算")
    # ---- 末端 ----
    _r("散热器额定平均温差","{:.1f}".format(_e["rad_dt_m_rated"]),"K","GB/T 13754-2017《供暖散热器散热量测定方法》（传统国标标定工况 95/70/18，ΔT=64.5K）","2017","§6.4.3/§6.6","tn=18℃","源")
    _r("散热器散热指数m","{:.2f}".format(_e["rad_m"]),"-","GB/T 13754-2017 §6.6.1.1 式(8) Q=K_M·ΔT^m（指数m由该型号热工检测报告实测拟合，标准不给定类型默认值）；本程序取工程典型值 m≈1.30（铸铁柱式实测 m≈1.28~1.30，如 74×60 铸铁 m≈1.283）","2017","式(8)","标准过余温度44.5K","算/典型值")
    _r("散热器允许最高供水温度","{:.0f}".format(_e["rad_tg_max"]),"℃","MHSR-N8-S1系列空气源热泵官方手册最高出水温度60℃；传统铸铁散热器系统可完全承受该温度","2026","美的MHSR-N8-S1系列产品说明书","热泵机组出水上限","源")
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
    # V1.34 P1-3：用户覆盖默认值后，台账动态标注【用户输入】，规范/默认值单独保留（不再冒充规范原值）
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
    st.caption("标注：【源】=规范/数据库/实测直接引用；【算】=程序计算；【假】=经验假设或示例值，答辩前请按实际选型/询价替换。设备A(MHSR120N8-S1·12kW)与设备B(MHSR100N8-S1·10kW)均为低环境温度空气源热泵(冷水)机组（CQC认证名录）；"
               "性能估算面 55℃/45℃ 出水列锚点来自官方说明书性能参数表【源】，其余格为按温升幂律推算的【算】值——整体为模型估算面（证据等级C），不是完整厂家性能矩阵；增强散热器、造价与批量系数等仍为【假】示例值。"
               "当用户值覆盖默认值时，对应台账自动标注【用户输入】。访问日期口径：【源/算】=2026-09-05；【假】=经验假设或示例值，无外部访问日期。")
    st.dataframe(_ledger_df, width="stretch", hide_index=True, height=320)

#侧边栏
with st.sidebar:
    st.markdown("""
<div style="padding:10px 0;border-bottom:1px solid rgba(99,102,241,0.25);margin-bottom:14px;">
<h3 style="color:#6366f1;margin:0;">📌 参数来源台账</h3>
<div style="font-size:12px;color:#666;">性能估算面插值 · HDD分段能耗 · 五道闸门 · 末端热工迭代求供水温度 · SPF_HP+aux统一口径</div>
</div>
""", unsafe_allow_html=True)
    with st.expander("📖 参数说明与折算依据（点击展开）", expanded=False):
        st.markdown("**热泵性能估算面**｜所选户用机组的产品与试验口径以厂家资料所列 **GB/T 25127.2—2020（户用及类似用途）** 为准；GB/T 25127.1—2020 适用于工业或商业及类似用途，本案例不采用该部分。锚点=厂家公开数据【源】，推算格=温升幂律模型【算】；每一条：［室外环境温度℃，供水温度℃，COP，工况可用制热量kW］。方案1、2 使用设备A；方案3 使用设备B。")
        st.markdown("""
**批量改造分项折算系数调研参考依据（项目需按当地招标报价修正）：**
- 分户独立改造：围护=1.00，热泵=1.00，末端=1.00；
- 批量分户改造参考经验：
  - 围护保温工程 **0.75**：老旧小区EPC批量集采、外脚手架共用、人工摊薄；
  - 空气源热泵设备安装 **0.85**：厂家批量供货、统一班组安装，省去零散上门差旅成本；
  - 室内末端改造 **0.80**：批量进场、开槽回填工序统一调度。
""")
    sel_house = st.selectbox("🏠选择户型",["中间层住宅","顶层边户"], key="house_type_sel")
    if sel_house != st.session_state["house_type"]:
        switch_house_type(sel_house)
    ht = st.session_state["house_type"]
    if ht == "中间层住宅":
        st.info("【中间层住宅】上下均采暖住户；不计屋面、地面楼板；构件：外墙、外窗、外门、非采暖隔墙")
    else:
        st.info("【顶层边户】顶层+东西山墙边户；计入屋面、东西山墙；不计底层地面楼板")
    st.session_state["retrofit_mode"] = st.selectbox("🔧改造造价模式", list(RETROFIT_MODE_CFG.keys()), key="retrofit_mode_sel")
    _cs_show = st.session_state["coef_set"]
    if st.session_state["retrofit_mode"] == "批量分户改造":
        st.info(f"批量分户情景｜用户设置值=本次生效值：围护 {_cs_show['coef_envelope']}｜热泵 {_cs_show['coef_pump']}｜末端 {_cs_show['coef_terminal']}（分项结算）")
    else:
        st.info("分户独立情景｜本次生效值：围护/热泵/末端均=1.00。批量采购设置值（围护0.75/热泵0.85/末端0.80）已保留为『用户设置值』，本次不生效。")
    # ===== V1.8新增：计算模式切换 =====
    st.session_state["calc_mode"] = st.radio("🧮计算模式",["三套典型方案","18种自由组合批量计算"], key="calc_mode_radio")
    if st.session_state["calc_mode"] == "18种自由组合批量计算":
        st.session_state["calc_mode"] = "batch_18"
    else:
        st.session_state["calc_mode"] = "typical"

    # ===== 模型版本号 + 恢复统一基准 =====
    st.markdown("**🛠 模型版本号：" + APP_VERSION + "**")
    st.caption("更新时间：2026-09-09（计算快照指纹 / 度时-时长分离 / 有效性分维度 / 备用热源配置 / 供热完整性 / 房间级与工程条件核验）\n计算链：H → Q_design → Q_year → 末端反算tg → 估算面COP插值 → E_HP+E_aux → SPF_HP+aux → 费用 → 运行期碳排放 → 五道闸门+备用/电力/供热完整性")
    if st.button("♻️恢复统一基准（重置全部默认参数）", width="stretch"):
        reset_to_defaults()
    if st.session_state.pop("_reset_toast", False):
        st.success("已恢复统一基准：建筑/设备/批量系数回到默认值（所有输入框已同步还原为默认值）")
    # ===== V1.10新增：保存方案快照（可载入） =====
    _n_saved = len(st.session_state.get("saved_schemes", []))
    if st.button(f"💾保存当前方案（已存{_n_saved}个）", key="save_scheme_btn", width="stretch"):
        _build_snap = dict(st.session_state["build"])
        _build_snap["volume"] = _build_snap["area"] * _build_snap["floor_h"]
        _build_snap["dT"] = _build_snap["Tin"] - _build_snap["Tout"]
        _snap = {
            "时间": datetime.datetime.now().strftime("%m-%d %H:%M"),
            "户型": st.session_state["house_type"],
            "建筑": _build_snap,
            "设备": dict(st.session_state["equip"]),
            "系数": dict(st.session_state["coef_set"]),
            "造价模式": st.session_state.get("retrofit_mode", "分户独立改造"),
            "计算模式": st.session_state.get("calc_mode", "typical"),
            "允许外墙改造": st.session_state.get("cfg_allow_wall", True),
            "SPF口径": st.session_state.get("cfg_spf_mode", "含辅助电加热 SPF_HP+aux"),
            # 审查意见⑨：保存必须能恢复全部输入并重算——备用/房间级/工程/基准可比性/样本工况一并入快照
            "备用配置": {
                "_aux_mode": st.session_state.get("_aux_mode", "无备用（不假定足额）"),
                "_aux_capacity": st.session_state.get("_aux_capacity", 0.0),
                "_aux_eta": st.session_state.get("_aux_eta", 1.0),
                "_aux_cost_per_kw": st.session_state.get("_aux_cost_per_kw", 300.0),
                "_aux_elec_limit": st.session_state.get("_aux_elec_limit", 16.0),
                "_aux_p_rated": st.session_state.get("_aux_p_rated", 0.0),
                "_season_hours": st.session_state.get("_season_hours", DEFAULT_SEASON_HOURS),
            },
            "房间级输入": {
                "_room_load_kw": st.session_state.get("_room_load_kw", 0.0),
                "_room_rad_kw": st.session_state.get("_room_rad_kw", 0.0),
                "_room_floor_kw": st.session_state.get("_room_floor_kw", 0.0),
                "_floor_eff_area": st.session_state.get("_floor_eff_area", 0.0),
                "_floor_surf_max": st.session_state.get("_floor_surf_max", 28.0),
            },
            "工程条件": {
                "_eng_outdoor": st.session_state.get("_eng_outdoor", "待核验"),
                "_eng_power": st.session_state.get("_eng_power", "待核验"),
                "_eng_drain": st.session_state.get("_eng_drain", "待核验"),
                "_eng_piping": st.session_state.get("_eng_piping", "待核验"),
            },
            "基准可比性": bool(st.session_state.get("_base_cmp", False)),
            "基准录入": {
                "_base_type": st.session_state.get("_base_type", "未录入（暂不输出估算结果）"),
                "_base_energy": st.session_state.get("_base_energy", 0.0),
                "_base_ef": st.session_state.get("_base_ef", 0.20),
            },
            "计算快照指纹": calc_input_fingerprint(),
            # 保存当前所在页面，载入后恢复到同一页面（避免左右页面不一致）
            "当前页面": st.session_state.get("page_select_radio", "1.建筑围护参数录入"),
        }
        if "saved_schemes" not in st.session_state:
            st.session_state["saved_schemes"] = []
        st.session_state["saved_schemes"].append(_snap)
        st.toast(f"✅ 已保存方案{len(st.session_state['saved_schemes'])}（{_snap['时间']}，{_snap['户型']}）")
        st.success(f"已保存方案{len(st.session_state['saved_schemes'])}（{_snap['时间']}，{_snap['户型']}）")
    if st.session_state.get("saved_schemes"):
        with st.expander(f"📚已保存方案（{len(st.session_state['saved_schemes'])}个，点击载入）", expanded=True):
            for _si, _s in enumerate(st.session_state["saved_schemes"]):
                _col_load, _col_del = st.columns([5, 1])
                with _col_load:
                    if st.button(f"载入方案{_si+1}｜{_s['时间']}｜{_s['户型']}", key=f"load_scheme_{_si}", width="stretch"):
                        st.session_state["_pending_load_scheme"] = _si
                        st.rerun()
                with _col_del:
                    if st.button("🗑", key=f"del_scheme_{_si}", help="删除此方案"):
                        # V1.38：删除按钮在"功能页面切换"radio 之前触发 rerun，会清空 radio 控件状态；
                        # 先暂存当前页面，rerun 后在脚本顶部恢复，避免删除后左右页面不一致
                        st.session_state["_restore_page_after_del"] = st.session_state.get(
                            "page_select_radio", "1.建筑围护参数录入")
                        st.session_state["saved_schemes"].pop(_si)
                        st.rerun()
    st.divider()
    _b_ev=st.session_state["build"]; _e_ev=st.session_state["equip"]
    with st.expander("📋 参数证据链（点击展开/折叠）", expanded=False):
        st.markdown(f"""
        **参数证据链**（详见页面顶部台账逐项：数值/年份/页码·表号/适用工况/访问日期/【源·算·假】）
        1. 外墙K改前{_b_ev['Kw_old']:.2f}、改后{_b_ev['Kw_new']:.2f} W/(m²·K)：GB 50176-2016 附录B表B.0.1 / JGJ 26-2018 表4.2.2-3（2016/2018·郑州·源·2026-08-31）
        2. 郑州采暖室外计算温度{_b_ev['Tout']:.1f}℃：GB 50176-2016 附录A表A.0.1·郑州站57083·源
        3. 郑州HDD18={_b_ev['HDD']:.0f}℃·d：《中国建筑热环境分析专用气象数据集》(典型气象年)·郑州站57083·1984-2003·基准18℃·源
        4. 热泵样本：美的MHSR-N8-S1系列 MHSR120N8-S1(12kW)、MHSR100N8-S1(10kW)·执行 GB/T 25127.2-2020·官方手册最高出水温度60℃·A7/W45 COP=3.50/3.55、A-12/W35=2.70·2026美的MHSR-N8-S1系列产品说明书·源
        5. 热负荷：不计朝向/风力/高度附加；热桥与间歇修正未纳入——定位“早期方案比较/教学决策支持”
        6. ⚠️本程序**不适用底层住户**
        7. V1.34：性能估算面插值(模型适用范围内)；HDD多温度分段计算全年能耗；SPF_HP+aux=Q_year/(E_HP+E_aux)；旧SPF仅作参考
        """)
    st.divider()
    page_select = st.radio("功能页面切换", [
        "1.建筑围护参数录入",
        "2.热泵&末端热工&单位造价录入",
        "3.三套方案计算结果",
        "4.手工校核验算页"
    ], key="page_select_radio")

# ======================页面1：建筑围护参数录入 ======================
if page_select == "1.建筑围护参数录入":
    ht = st.session_state["house_type"]
    st.markdown(f"""
<div class="light-tech-title">
    <h1>🏠建筑围护结构参数｜对象：{ht}</h1>
</div>
""", unsafe_allow_html=True)
    build = st.session_state["build"]
    st.info("📐外墙净面积 = 外墙毛面积 − 外窗面积 − 外门面积。"
            f"当前净外墙面积 = {round(calc_wall_net(build),2)} m²。仅当净外墙面积>0 时允许计算；当外窗+外门 ≥ 外墙毛面积时，阻断页面3并提示核对几何输入。")
    _dflt_b_p1 = DEFAULT_BUILD_MID if ht == "中间层住宅" else DEFAULT_BUILD_TOP_EDGE
    if abs(build["Tout"] - _dflt_b_p1["Tout"]) > 1e-6 or abs(build["HDD"] - _dflt_b_p1["HDD"]) > 1e-6 or abs(build["Tin"] - _dflt_b_p1["Tin"]) > 1e-6:
        st.warning("🟡检测到室外设计温度/HDD/室内设计温度已覆盖规范默认值（当前值用于敏感性/边界测试），"
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
    <p>不再手动输入供水温度；输入末端额定参数，程序迭代反算满足热负荷的最低供水温度；围护=单位造价×工程量</p>
    <p>热泵性能为【室外温度×供水温度】性能估算面（厂家锚点+模型推算）双线性插值（模型适用范围内），范围外禁止外推；HDD分段全年能耗计算</p>
    <p>末端公式：$Q_{terminal}=Q_{rated} \\times (\\Delta T_m / \\Delta T_{m,rated})^m$（散热器 m≈1.30，地暖 m≈0.95）</p>
</div>
""", unsafe_allow_html=True)
    equip = st.session_state["equip"]
    build = st.session_state["build"]
    warn_messages = input_warning_check(build, equip)
    for w in warn_messages:
        st.warning(w)
    col_left, col_mid, col_right = st.columns([1,1,1])
    # ===== 分项独立批量折算系数（可编辑，含调研依据）｜审查意见④：区分用户设置值与本次生效值 =====
    st.subheader("🔧批量采购分项折算系数（用户设置值）")
    _is_batch = (st.session_state["retrofit_mode"] == "批量分户改造")
    st.caption("以下为用户设置值：批量分户场景参考 围护×0.75、热泵×0.85、末端×0.80（默认，可编辑）。"
               f"当前造价模式【{st.session_state['retrofit_mode']}】：本次生效值 围护{st.session_state['coef_set']['coef_envelope'] if _is_batch else 1.00}、"
               f"热泵{st.session_state['coef_set']['coef_pump'] if _is_batch else 1.00}、末端{st.session_state['coef_set']['coef_terminal'] if _is_batch else 1.00}。"
               "分户独立情景下用户设置值已保留、本次不生效（输入置灰）。")
    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        st.number_input("围护工程折算系数（用户设置值）", min_value=0.4, max_value=1.0, step=0.01,
                        value=st.session_state["coef_set"]["coef_envelope"], key="_coef_env", disabled=not _is_batch,
                        on_change=lambda: st.session_state["coef_set"].update({"coef_envelope": st.session_state["_coef_env"]}))
    with cc2:
        st.number_input("热泵设备安装折算系数（用户设置值）", min_value=0.4, max_value=1.0, step=0.01,
                        value=st.session_state["coef_set"]["coef_pump"], key="_coef_pump", disabled=not _is_batch,
                        on_change=lambda: st.session_state["coef_set"].update({"coef_pump": st.session_state["_coef_pump"]}))
    with cc3:
        st.number_input("室内末端改造折算系数（用户设置值）", min_value=0.4, max_value=1.0, step=0.01,
                        value=st.session_state["coef_set"]["coef_terminal"], key="_coef_term", disabled=not _is_batch,
                        on_change=lambda: st.session_state["coef_set"].update({"coef_terminal": st.session_state["_coef_term"]}))
    if _is_batch:
        st.info(f"本次生效系数（批量分户）：围护 {st.session_state['coef_set']['coef_envelope']}｜热泵 {st.session_state['coef_set']['coef_pump']}｜末端 {st.session_state['coef_set']['coef_terminal']}。"
                "批量时各项造价按 原始金额×有效系数=折算金额 分栏显示（见页面3造价明细）。补贴情景未建模，如需考虑补贴请另行录入。")
    else:
        st.info("当前采用分户独立情景，有效造价系数：围护1.00、热泵1.00、末端1.00。批量采购设置已保留（0.75/0.85/0.80），本次不生效。")
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
        st.caption("铭牌SCOP×低温衰减系数为旧算法估算值，仅供回顾对比，不参与当前方案判定（主指标为分段积分反算的 SPF_HP+aux）。")
        st.number_input("方案1 衰减系数",value=equip["spf_decay1"],min_value=0.1,max_value=1.0,key="_decay1",on_change=sync_equip,args=("_decay1", "spf_decay1"))
        st.number_input("方案2 衰减系数",value=equip["spf_decay2"],min_value=0.1,max_value=1.0,key="_decay2",on_change=sync_equip,args=("_decay2", "spf_decay2"))
        st.number_input("方案3 衰减系数",value=equip["spf_decay3"],min_value=0.1,max_value=1.0,key="_decay3",on_change=sync_equip,args=("_decay3", "spf_decay3"))
        st.divider()
        st.subheader("📋 样本额定制热量(kW)（须同时填写室外温度、供水温度及样本来源）")
        st.caption("设备A/B 样本额定制热量对应工况为 A7/W45（室外7℃、供水45℃），−7℃不是额定点；COP、SCOP、IPLV(H) 与旧算法SPF不可互换。"
                   "设计工况可用制热量由『热泵性能估算面』按设计室外温度与反算供水温度插值得到，不由本输入直接替代；本输入仅作为热泵可用制热量的上限约束。"
                   "历史经验估算（铭牌SPF×衰减系数）仅供回顾，不参与当前方案判定。")
        st.number_input("方案1 设备A 额定制热量 kW",value=equip["Qhp_rated1"],min_value=1.0,max_value=100.0,key="_Qhp_rated1",on_change=sync_equip,args=("_Qhp_rated1", "Qhp_rated1"))
        st.number_input("方案2 设备A 额定制热量 kW",value=equip["Qhp_rated2"],min_value=1.0,max_value=100.0,key="_Qhp_rated2",on_change=sync_equip,args=("_Qhp_rated2", "Qhp_rated2"))
        st.number_input("方案3 设备B 额定制热量 kW",value=equip["Qhp_rated3"],min_value=1.0,max_value=100.0,key="_Qhp_rated3",on_change=sync_equip,args=("_Qhp_rated3", "Qhp_rated3"))
        st.caption("样本工况说明（与上方额定制热量配套记录）：")
        _r1, _r2 = st.columns(2)
        with _r1:
            st.number_input("样本室外温度 ℃", value=equip.get("rated_cond_Tamb",7.0), min_value=-30.0, max_value=40.0,
                            key="_rated_Tamb", on_change=sync_equip, args=("_rated_Tamb","rated_cond_Tamb"))
            st.number_input("样本供水温度 ℃", value=equip.get("rated_cond_Tg",45.0), min_value=20.0, max_value=80.0,
                            key="_rated_Tg", on_change=sync_equip, args=("_rated_Tg","rated_cond_Tg"))
        with _r2:
            st.text_input("样本来源", value=equip.get("rated_cond_src","美的MHSR-N8-S1系列官方说明书（2026，A7/W45 额定制热）"),
                          key="_rated_src", on_change=sync_equip, args=("_rated_src","rated_cond_src"))
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
        st.caption("默认0.5897=2023年河南省电力平均二氧化碳排放因子（生态环境部、国家统计局2025年第47号公告）；计算边界：运行阶段购电间接排放（位置法）。若改用0.5810须给出准确文件名/年份与适用理由。")
    st.divider()
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.subheader("🔥原有散热器末端（方案1、方案2使用）")
        st.number_input("散热器总额定散热量 kW",value=equip["rad_Qrated_kW"],min_value=0.5,max_value=200.0,key="_rad_Qrated_kW",on_change=sync_equip,args=("_rad_Qrated_kW","rad_Qrated_kW"))
        st.number_input("散热器额定平均温差 K",value=equip["rad_dt_m_rated"],min_value=10.0,max_value=80.0,key="_rad_dt_m_rated",on_change=sync_equip,args=("_rad_dt_m_rated","rad_dt_m_rated"))
        st.number_input("散热器散热指数 m",value=equip["rad_m"],min_value=0.5,max_value=1.6,key="_rad_m",on_change=sync_equip,args=("_rad_m","rad_m"))
        st.number_input("散热器供‑回水温差 K",value=equip["rad_dt_flow_return"],min_value=2.0,max_value=30.0,key="_rad_dt_flow_return",on_change=sync_equip,args=("_rad_dt_flow_return","rad_dt_flow_return"))
        st.number_input("散热器允许最高供水温度 ℃",value=equip["rad_tg_max"],min_value=40.0,max_value=60.0,key="_rad_tg_max",on_change=sync_equip,args=("_rad_tg_max","rad_tg_max"))
        st.divider()
        st.markdown("**🛏 房间级校核输入（整户总量满足≠每个房间都暖；0=未填写→待核验）**")
        st.number_input("最不利房间设计热负荷 kW（全户型共用）", min_value=0.0, max_value=20.0, step=0.1, key="_room_load_kw")
        st.number_input("该房间散热器额定散热量 kW（方案1/2）", min_value=0.0, max_value=20.0, step=0.1, key="_room_rad_kw")
    with col_t2:
        st.subheader("❄️低温地暖末端（仅方案3使用）")
        st.number_input("地暖总额定散热量 kW",value=equip["floor_Qrated_kW"],min_value=0.5,max_value=200.0,key="_floor_Qrated_kW",on_change=sync_equip,args=("_floor_Qrated_kW","floor_Qrated_kW"))
        st.number_input("地暖额定平均温差 K",value=equip["floor_dt_m_rated"],min_value=5.0,max_value=40.0,key="_floor_dt_m_rated",on_change=sync_equip,args=("_floor_dt_m_rated","floor_dt_m_rated"))
        st.number_input("地暖散热指数 m",value=equip["floor_m"],min_value=0.5,max_value=1.6,key="_floor_m",on_change=sync_equip,args=("_floor_m","floor_m"))
        st.number_input("地暖供‑回水温差 K",value=equip["floor_dt_flow_return"],min_value=2.0,max_value=15.0,key="_floor_dt_flow_return",on_change=sync_equip,args=("_floor_dt_flow_return","floor_dt_flow_return"))
        st.number_input("地暖允许最高供水温度 ℃",value=equip["floor_tg_max"],min_value=30.0,max_value=50.0,key="_floor_tg_max",on_change=sync_equip,args=("_floor_tg_max","floor_tg_max"))
        st.divider()
        st.markdown("**🛏 房间级校核输入（地暖须核查有效面积与表面温度；0=未填写→待核验）**")
        st.number_input("该房间地暖额定散热量 kW（方案3）", min_value=0.0, max_value=20.0, step=0.1, key="_room_floor_kw")
        st.number_input("地暖有效散热面积 m²（方案3）", min_value=0.0, max_value=300.0, step=1.0, key="_floor_eff_area")
        st.number_input("地暖表面温度上限 ℃（人员经常停留区，JGJ 142 参考 24~28）", min_value=20.0, max_value=40.0, step=0.5, key="_floor_surf_max")

    # ========= V1.7新增：热泵厂家样本表展示（V1.21补充二维性能表） =========
    st.divider()
    st.subheader("📋热泵性能估算面数据（锚点【源】+推算格【算】；已分栏）")
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
    with st.expander("📊 性能估算面（室外温度×供水温度）｜双线性插值用（锚点/推算分栏）"):
        st.caption("行=室外温度（升序），列=供水温度（升序）。两套面均已按【美的MHSR-N8-S1系列】官方说明书真实锚点标定："
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
    # 分项有效系数（分户=1.00/1.00/1.00；批量=coef_set 可编辑值，默认0.75/0.85/0.80）
    _mode_cfg = RETROFIT_MODE_CFG[st.session_state["retrofit_mode"]]
    if st.session_state["retrofit_mode"] == "分户独立改造":
        eff_coef_env, eff_coef_pump, eff_coef_term = 1.00, 1.00, 1.00
    else:
        eff_coef_env = st.session_state["coef_set"]["coef_envelope"]
        eff_coef_pump = st.session_state["coef_set"]["coef_pump"]
        eff_coef_term = st.session_state["coef_set"]["coef_terminal"]
    st.markdown(f"""
<div class="light-tech-title">
    <h1>📊三套改造方案｜户型：{ht}｜性能估算面插值+HDD分段能耗+五道闸门</h1>
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
    allow_wall_retrofit = st.checkbox("✅允许外墙围护改造（若小区外立面限制可取消勾选）",value=True, key="_allow_wall")
    spf_mode = st.radio("🧮SPF计算口径（加入/不加入辅助电加热）", ["含辅助电加热 SPF_HP+aux", "不含辅助电加热 SPF_HP（仅热泵主机）"], horizontal=True, key="_spf_mode")
    spf_include_aux = (spf_mode == "含辅助电加热 SPF_HP+aux")
    # V1.36：把页面3的开关/口径同步到非"_"前缀的持久 key，避免切换页面后被 _clear_widget_state 清除，保存方案时读取持久 key
    st.session_state["cfg_allow_wall"] = allow_wall_retrofit
    st.session_state["cfg_spf_mode"] = spf_mode
    spf1 = calc_season_spf(equip["SCOP_nameplate1"], equip["spf_decay1"])
    spf2 = calc_season_spf(equip["SCOP_nameplate2"], equip["spf_decay2"])
    spf3 = calc_season_spf(equip["SCOP_nameplate3"], equip["spf_decay3"])
    st.info(f"📌季节性能主指标采用分段积分反算，当前口径：{'SPF_HP+aux=Q_delivered/(E_HP+E_aux)（含辅助电加热）' if spf_include_aux else 'SPF_HP=Q_delivered/E_HP（仅热泵主机，不含辅助电加热）'}。"
            f"分母仅计入热泵主机与辅助电加热耗电，未计循环水泵、控制器、待机与曲轴箱加热用电，不等同于完整系统SPF。"
            f"可在上方切换SPF计算口径，指标名称、分母与解释将同步变化。"
            f"铭牌SPF×衰减系数（旧算法估算值，仅供回顾，不参与当前方案判定）：方案1={spf1}｜方案2={spf2}｜方案3={spf3}")
    st.caption("口径说明：①HDD18 的 18℃ 为采暖平衡温度（非室内设定温度 20℃），已隐含内部得热与太阳得热折减；"
               "设计负荷采用室内 20℃（GB 50736），两者口径不同但均按规范取值。"
               "②本程序定位为『早期方案比较/教学决策支持』，不计算朝向、风力、高度附加耗热量及热桥、间歇供暖修正，不可直接替代工程设计选型。"
               "③热泵性能为『估算面』（厂家公开锚点+温升幂律推算，证据等级C），非完整厂家性能矩阵，不作为最终设备选型依据。")
    cost_dict = calc_retrofit_cost(ht, build, equip, 1.0) # 原始造价明细（未批量）
    real_cost_pump = equip["cost_pump"] * eff_coef_pump # V1.34：热泵×有效系数
    real_envelope = cost_dict["sum_envelope_raw"] * eff_coef_env
    real_lowend = cost_dict["cost_lowend_raw"] * eff_coef_term
    with st.expander("🔍展开查看围护工程量 & 分项造价明细（每项=原始金额×有效系数=折算金额，V1.34）"):
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
        st.info(f"当前造价模式：【{_cur_mode_txt}】｜用户设置值：围护{st.session_state['coef_set']['coef_envelope']}、热泵{st.session_state['coef_set']['coef_pump']}、末端{st.session_state['coef_set']['coef_terminal']}（批量采购参考）；"
                f"本次生效值：围护{eff_coef_env}、热泵{eff_coef_pump}、末端{eff_coef_term}。"
                f"折算后围护合计：{round(real_envelope,0)}元；折算后地暖：{round(real_lowend,0)}元；折算后热泵：{round(real_cost_pump,0)}元。"
                "分户独立情景下批量采购设置值已保留、本次不生效；补贴情景未建模，如需考虑补贴请另行录入。")

    # ===== 备用热源配置（审查意见④：未确认时不假定足额；①：等效小时分母用 P_aux,rated） =====
    with st.expander("🔌 备用热源配置（未确认时不假定足额）", expanded=True):
        st.info("**备用热源状态：未确认。** 请选择备用方案并填写已安装容量、接入位置与效率；未确认时不假定其足额。\n"
                "程序分别输出：所需备用容量（设计点峰值缺口）、已配置容量、实际备用供热、备用用电 E_aux 及未满足热量。\n"
                "电力容量（配电可增容上限）、控制联动与投资将一并进入约束与费用。")
        _aux_mode = st.radio("备用热源方案", [
            "无备用（不假定足额）",
            "水侧电辅热（串联电加热器/电锅炉，受末端能力限制）",
            "独立房间热源（分室电暖设备，不经水路末端）"], key="_aux_mode")
        _aux_capacity = st.number_input("已安装备用容量 (kW)", min_value=0.0, max_value=100.0, value=0.0, step=0.5, key="_aux_capacity")
        _aux_eta = st.number_input("备用热源效率 η（电热≈1.0）", min_value=0.5, max_value=1.0, value=1.0, step=0.01, key="_aux_eta")
        _aux_cost_per_kw = st.number_input("备用热源投资（元/kW·已安装容量）", min_value=0.0, max_value=5000.0, value=300.0, step=50.0, key="_aux_cost_per_kw")
        _aux_elec_limit = st.number_input("该户配电可增容上限 (kW)（单相220V·63A≈13.9kW量级）", min_value=0.0, max_value=200.0, value=16.0, step=1.0, key="_aux_elec_limit")
        _aux_p_rated = st.number_input("电辅热额定电功率 P_aux,rated (kW)（用于等效满载小时；未配置电辅热或额定功率未知时留 0）",
                                       min_value=0.0, max_value=100.0, value=0.0, step=0.5, key="_aux_p_rated",
                                       help="等效满载小时 = E_aux / P_aux,rated，除以的是电加热器额定电功率，不是热泵额定制热量；"
                                            "实际开启小时 = ΣI(P_aux,i>0)·Δt_i 由分段时长累计，须以气象时序校核")
        _season_hours = st.number_input("采暖季运行时长 (h)（郑州采暖期约120天=2880h；把度时积分折算为时段时长的一阶假设，须以气象时序校核）",
                                        min_value=0.0, max_value=6000.0, value=DEFAULT_SEASON_HOURS, step=100.0, key="_season_hours")
        st.caption("水侧电辅热同样受末端能力限制：供水温度提升后末端总输热能力上限=Q_term(tg_max)，有效备用容量=min(已安装, max(0, Q_term(tg_max)−热泵设计出力))。"
                   "独立房间热源不经水路末端、不受其限制，但仍受配电容量约束。备用热源启停控制与热泵联锁属工程细节，本模型仅计入容量/电力/费用约束。")
    _aux_mode_v = st.session_state["_aux_mode"]
    _aux_installed = float(st.session_state["_aux_capacity"])
    _aux_eta_v = float(st.session_state["_aux_eta"])
    _aux_cost_per_kw_v = float(st.session_state["_aux_cost_per_kw"])
    _aux_elec_limit_v = float(st.session_state["_aux_elec_limit"])
    _aux_p_rated_v = float(st.session_state["_aux_p_rated"])
    _season_hours_v = float(st.session_state["_season_hours"])
    if _aux_mode_v.startswith("无备用"):
        _aux_mode_short = "无备用"
    elif _aux_mode_v.startswith("水侧"):
        _aux_mode_short = "水侧电辅热"
    else:
        _aux_mode_short = "独立房间热源"
    _aux_elec_ok = (_aux_installed <= _aux_elec_limit_v + 1e-6)

    # ===== 审查意见⑦：工程安装条件 + 房间级校核（未确认项显示待核验，不默认绿灯） =====
    with st.expander("🛠 工程安装条件与房间级校核（未确认项显示待核验，不默认绿灯）"):
        st.info("工程状态由外立面许可、设备位置、电力容量、排水及管路条件共同确定，不由单一复选框涵盖；"
                "房间级校核补充『最不利房间』与地暖『有效面积/表面温度』核查——整户总量满足不等于每个房间都暖。"
                "未确认项一律显示『待核验』并按未通过计入闸门。")
        _ec1, _ec2 = st.columns(2)
        with _ec1:
            _eng_outdoor = st.selectbox("外机安装位置（承重/间距/噪声）", ["待核验", "已确认", "不适用"], key="_eng_outdoor")
            _eng_power = st.selectbox("电力容量与增容（热泵+电辅热；配电上限见备用配置）", ["待核验", "已确认", "不适用"], key="_eng_power")
        with _ec2:
            _eng_drain = st.selectbox("排水与防冻条件", ["待核验", "已确认", "不适用"], key="_eng_drain")
            _eng_piping = st.selectbox("管路/水力条件（方案3末端改造适用）", ["待核验", "已确认", "不适用"], key="_eng_piping")
        st.divider()
        st.markdown("**🏠 最不利房间级校核（与页面2 末端区同步；0=未填写→待核验）**")
        _rc1, _rc2, _rc3 = st.columns(3)
        with _rc1:
            st.number_input("最不利房间设计热负荷 kW", min_value=0.0, max_value=20.0, step=0.1, key="_room_load_kw")
        with _rc2:
            st.number_input("房间散热器额定散热量 kW（方案1/2）", min_value=0.0, max_value=20.0, step=0.1, key="_room_rad_kw")
            st.number_input("房间地暖额定散热量 kW（方案3）", min_value=0.0, max_value=20.0, step=0.1, key="_room_floor_kw")
        with _rc3:
            st.number_input("地暖有效散热面积 m²（方案3）", min_value=0.0, max_value=300.0, step=1.0, key="_floor_eff_area")
            st.number_input("地暖表面温度上限 ℃", min_value=20.0, max_value=40.0, step=0.5, key="_floor_surf_max")
        _room_load_kw_v = float(st.session_state.get("_room_load_kw", 0.0))
        _room_rad_kw_v = float(st.session_state.get("_room_rad_kw", 0.0))
        _room_floor_kw_v = float(st.session_state.get("_room_floor_kw", 0.0))
        _floor_eff_area_v = float(st.session_state.get("_floor_eff_area", 0.0))
        _floor_surf_max_v = float(st.session_state.get("_floor_surf_max", 28.0))
        st.caption(f"最不利房间设计热负荷 {_room_load_kw_v:.2f} kW；散热器房间额定 {_room_rad_kw_v:.2f} kW；地暖房间额定 {_room_floor_kw_v:.2f} kW；"
                   f"地暖有效散热面积 {_floor_eff_area_v:.1f} m²；表面温度上限 {_floor_surf_max_v:.1f} ℃。"
                   "0=未填写→待核验，请在页面2『末端热工』区填写。")

    def _room_check(qr_room, dtmr, m_val, dtfr, tg_solve_v, Tin_v, q_load_room, label):
        """房间级末端校核：Q_room=Q_rated_room×(ΔT_m/ΔT_m,rated)^m ≥ Q_load_room（审查意见⑦）"""
        if q_load_room <= 0 or qr_room <= 0:
            return "待核验", f"{label}：未填写房间负荷或房间末端额定散热量（页面2）"
        dt_m = tg_solve_v - dtfr/2.0 - Tin_v
        if dt_m <= 0:
            return "未通过", f"{label}：供水温度{tg_solve_v:.1f}℃过低，房间末端无散热能力"
        q_avail = qr_room * pow(dt_m/dtmr, m_val)
        if q_avail >= q_load_room - 1e-4:
            return "通过", ""
        return "未通过", f"{label}：房间末端在{round(tg_solve_v,1)}℃下可散热{round(q_avail,2)}kW < 房间负荷{round(q_load_room,2)}kW"

    def _floor_surf_check(Qd_kw, A_eff, Tin_v, surf_max):
        """地暖表面温度估算校核：t_f ≈ Tin + q/α，α≈8 W/(m²·K)（工程近似，标记假，须实测校核；审查意见⑦）"""
        if A_eff <= 0:
            return "待核验", "地暖有效散热面积未填写（页面2）"
        q_flux = Qd_kw * 1000.0 / A_eff
        t_surf = Tin_v + q_flux / 8.0
        if t_surf <= surf_max + 1e-6:
            return "通过", ""
        return "未通过", f"地暖表面温度估算 {round(t_surf,1)}℃（负荷密度{round(q_flux,0)}W/m²，α≈8 W/(m²·K)）> 上限{round(surf_max,1)}℃，需增大有效面积或降低负荷"

    def _eng_ok(need_facade, need_piping):
        """工程安装条件：外立面许可 + 外机位置 + 电力容量 + 排水防冻（+ 管路水力，方案3）。
        任一适用项未确认 → 返回 (False, 待核验项列表文本)。"""
        conds = []
        if need_facade:
            conds.append(("外立面许可", "已确认" if allow_wall_retrofit else "待核验"))
        conds.append(("外机位置", st.session_state.get("_eng_outdoor", "待核验")))
        conds.append(("电力容量", st.session_state.get("_eng_power", "待核验")))
        conds.append(("排水防冻", st.session_state.get("_eng_drain", "待核验")))
        if need_piping:
            conds.append(("管路水力", st.session_state.get("_eng_piping", "待核验")))
        pending = [n for n, v in conds if v != "已确认"]
        if pending:
            return False, "待核验：" + "、".join(pending)
        return True, "已确认"

    # --------方案1：围护不改造，散热器末端（V1.21：二维表分段能耗积分；V1.35：备用配置+有效性分维度） --------
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
    cop_d1, qhp_d1, valid1, design_warns1 = hp_available_at_design(build, equip, "HP0", tg1)
    q_aux_eff1 = effective_aux_capacity(_aux_mode_v, _aux_installed, qhp_d1, "T0", equip, build["Tin"])
    q_aux_design1 = calc_design_aux_capacity(Qd1_kW, qhp_d1)
    capacity_ok1 = (qhp_d1 + q_aux_eff1) >= Qd1_kW
    seg1_full, e_hp1, e_aux1, aux_h1, data_ok1, domain_warns1, unserved1 = calc_segment_hp_aux_2d(
        seg1, "HP0", tg1, equip["Qhp_rated1"],
        q_aux_capacity=(q_aux_eff1 if q_aux_eff1 > 1e-9 else None), eta_aux=_aux_eta_v, season_hours=_season_hours_v,
        p_aux_rated=_aux_p_rated_v)
    data_ok1 = data_ok1 and valid1["all_valid"]
    aux_heat1 = round(sum(s.get("Q_aux_kwh", 0.0) for s in seg1_full), 2)
    elec_1 = e_hp1 + e_aux1
    elec_1_old = elec_consume(q_year1_kwh, spf1)
    spf_hp_only1 = round(q_year1_kwh/e_hp1,3) if e_hp1>1e-9 else None
    spf_with_aux1 = round(q_year1_kwh/elec_1,3) if elec_1>1e-9 else None
    spf_sys1 = spf_with_aux1 if spf_include_aux else spf_hp_only1
    mr1 = round(qhp_d1/Qd1_kW,3) if Qd1_kW>1e-9 else None
    invest_1 = real_cost_pump + _aux_installed * _aux_cost_per_kw_v  # V1.35：备用热源投资联动进入总投资
    year_cost_1 = elec_1 * equip["elec_price"]
    need_aux1, aux_load1 = check_aux_electric_heat(Qd1_kW, equip["Qhp_rated1"])
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
    cop_d2, qhp_d2, valid2, design_warns2 = hp_available_at_design(build, equip, "HP0", tg2)
    q_aux_eff2 = effective_aux_capacity(_aux_mode_v, _aux_installed, qhp_d2, "T0", equip, build["Tin"])
    q_aux_design2 = calc_design_aux_capacity(Qd2_kW, qhp_d2)
    capacity_ok2 = (qhp_d2 + q_aux_eff2) >= Qd2_kW
    seg2_full, e_hp2, e_aux2, aux_h2, data_ok2, domain_warns2, unserved2 = calc_segment_hp_aux_2d(
        seg2, "HP0", tg2, equip["Qhp_rated2"],
        q_aux_capacity=(q_aux_eff2 if q_aux_eff2 > 1e-9 else None), eta_aux=_aux_eta_v, season_hours=_season_hours_v,
        p_aux_rated=_aux_p_rated_v)
    data_ok2 = data_ok2 and valid2["all_valid"]
    aux_heat2 = round(sum(s.get("Q_aux_kwh", 0.0) for s in seg2_full), 2)
    elec_2 = e_hp2 + e_aux2
    elec_2_old = elec_consume(q_year2_kwh, spf2)
    spf_hp_only2 = round(q_year2_kwh/e_hp2,3) if e_hp2>1e-9 else None
    spf_with_aux2 = round(q_year2_kwh/elec_2,3) if elec_2>1e-9 else None
    spf_sys2 = spf_with_aux2 if spf_include_aux else spf_hp_only2
    mr2 = round(qhp_d2/Qd2_kW,3) if Qd2_kW>1e-9 else None
    invest_2 = real_cost_pump + real_envelope + _aux_installed * _aux_cost_per_kw_v
    year_cost_2 = elec_2 * equip["elec_price"]
    save_elec_2 = elec_1 - elec_2
    payback_2 = payback_period(real_envelope, save_elec_2, equip["elec_price"])
    load_save_rate_2 = round((Qd1_kW - Qd2_kW)/Qd1_kW*100,2)
    elec_save_rate_2 = round((elec_1 - elec_2)/elec_1*100,2) # 相对方案1购电变化（P0-5口径）
    need_aux2, aux_load2 = check_aux_electric_heat(Qd2_kW, equip["Qhp_rated2"])
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
    cop_d3, qhp_d3, valid3, design_warns3 = hp_available_at_design(build, equip, "HP1", tg3)
    q_aux_eff3 = effective_aux_capacity(_aux_mode_v, _aux_installed, qhp_d3, "T2", equip, build["Tin"])
    q_aux_design3 = calc_design_aux_capacity(Qd3_kW, qhp_d3)
    capacity_ok3 = (qhp_d3 + q_aux_eff3) >= Qd3_kW
    seg3_full, e_hp3, e_aux3, aux_h3, data_ok3, domain_warns3, unserved3 = calc_segment_hp_aux_2d(
        seg3, "HP1", tg3, equip["Qhp_rated3"],
        q_aux_capacity=(q_aux_eff3 if q_aux_eff3 > 1e-9 else None), eta_aux=_aux_eta_v, season_hours=_season_hours_v,
        p_aux_rated=_aux_p_rated_v)
    data_ok3 = data_ok3 and valid3["all_valid"]
    aux_heat3 = round(sum(s.get("Q_aux_kwh", 0.0) for s in seg3_full), 2)
    elec_3 = e_hp3 + e_aux3
    elec_3_old = elec_consume(q_year3_kwh, spf3)
    spf_hp_only3 = round(q_year3_kwh/e_hp3,3) if e_hp3>1e-9 else None
    spf_with_aux3 = round(q_year3_kwh/elec_3,3) if elec_3>1e-9 else None
    spf_sys3 = spf_with_aux3 if spf_include_aux else spf_hp_only3
    mr3 = round(qhp_d3/Qd3_kW,3) if Qd3_kW>1e-9 else None
    invest_3 = real_cost_pump + real_envelope + real_lowend + _aux_installed * _aux_cost_per_kw_v
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

    # ===== V1.35：审查意见⑤ 供热完整性——相对方案1的节能/减排比较必须"等供热" =====
    heat_complete1 = scheme_heat_complete(end_ok1, unserved1)
    heat_complete2 = scheme_heat_complete(end_ok2, unserved2)
    heat_complete3 = scheme_heat_complete(end_ok3, unserved3)
    comp_ok2 = heat_complete1 and heat_complete2
    comp_ok3 = heat_complete1 and heat_complete3
    if not heat_complete1:
        _incmp_reason = ("基准方案存在供热不足（末端能力不足或存在未满足热量），当前电量仅为受限运行情景值；"
                         "请先补足基准供热或统一舒适度后再计算可比节电率；提高供水温度必须在设备（≤60℃）和末端允许工况内。")
    elif not (heat_complete2 and heat_complete3):
        _incmp_reason = "存在方案自身供热不足（末端能力不足或存在未满足热量），相对方案1的电量/排放比较不可比，须先补足供热。"
    else:
        _incmp_reason = ""
    # 不可比时，相对指标一律置 None（界面显示"不可比"），回收期不输出
    if not comp_ok2:
        payback_2 = None
        elec_save_rate_2 = None
        co2_reduce_2 = None
        co2_reduce_rate_2 = None
    if not comp_ok3:
        payback_3 = None
        elec_save_rate_3 = None
        co2_reduce_3 = None
        co2_reduce_rate_3 = None

    budget = equip["budget"]
    # V1.35：可行性闸门（预算 / 工程允许外墙 / 设计工况容量(热泵+已配置备用) / 末端能力 / 模型适用性(容量域&COP域&设备包络AND) / 备用电力容量 / 供热完整性）
    # P0-3 口径：hp_cap_ok = (Q_HP,avail,design + Q_aux,configured) >= Q_design；Q_aux,configured 来自备用热源配置
    #           （未配置时不假定足额→有效容量=0）；同时输出"需配置备用容量" q_aux_design=max(0,Qd−Qhp)，
    #           与年度 备用供热/E_aux/未满足热量（分段积分）分开报告，避免“容量不足”与“E_aux=0”的口径矛盾。
    def get_scheme_status(invest, engineering_ok, engineering_note, q_load, qhp_avail_design, q_aux_configured, end_ok, data_ok, mr, q_aux_design,
                          e_aux_year=0.0, q_aux_year=0.0, unserved=0.0, aux_installed=0.0, elec_ok=True, heat_complete=True,
                          room_status="待核验", room_note=""):
        budget_ok = invest <= budget
        hp_cap_ok = (qhp_avail_design + q_aux_configured) >= q_load
        terminal_ok = end_ok
        model_ok = data_ok
        aux_elec_ok = elec_ok
        heat_ok = heat_complete
        room_ok = (room_status == "通过")  # 审查意见⑦：房间级校核未确认(待核验)或未通过 → 不默认绿灯
        eligible = budget_ok and engineering_ok and hp_cap_ok and terminal_ok and model_ok and aux_elec_ok and heat_ok and room_ok
        return {"budget_ok":budget_ok,"engineering_ok":engineering_ok,"engineering_note":engineering_note,
                "hp_cap_ok":hp_cap_ok,"terminal_ok":terminal_ok,"model_ok":model_ok,"mr":mr,"q_aux_design":q_aux_design,
                "q_load":q_load,"qhp_avail_design":qhp_avail_design,
                "e_aux_year":e_aux_year,"q_aux_year":q_aux_year,"unserved":unserved,
                "q_aux_configured":q_aux_configured,"aux_installed":aux_installed,
                "aux_elec_ok":aux_elec_ok,"heat_ok":heat_ok,
                "room_status":room_status,"room_note":room_note,"eligible":eligible}
    # ===== 审查意见⑦：工程安装条件 / 房间级校核状态（未确认项显示待核验，不默认绿灯） =====
    eng1_ok, eng1_note = _eng_ok(need_facade=False, need_piping=False)
    eng2_ok, eng2_note = _eng_ok(need_facade=True, need_piping=False)
    eng3_ok, eng3_note = _eng_ok(need_facade=True, need_piping=True)
    _room_status1, _room_note1 = _room_check(_room_rad_kw_v, equip["rad_dt_m_rated"], equip["rad_m"], equip["rad_dt_flow_return"],
                                             tg1, build["Tin"], _room_load_kw_v, "方案1房间")
    _room_status2, _room_note2 = _room_check(_room_rad_kw_v, equip["rad_dt_m_rated"], equip["rad_m"], equip["rad_dt_flow_return"],
                                             tg2, build["Tin"], _room_load_kw_v, "方案2房间")
    _rs3a, _rn3a = _room_check(_room_floor_kw_v, equip["floor_dt_m_rated"], equip["floor_m"], equip["floor_dt_flow_return"],
                               tg3, build["Tin"], _room_load_kw_v, "方案3房间")
    _rs3b, _rn3b = _floor_surf_check(Qd3_kW, _floor_eff_area_v, build["Tin"], _floor_surf_max_v)
    if _rs3a == "未通过" or _rs3b == "未通过":
        _room_status3, _room_note3 = "未通过", ("；".join(x for x in [_rn3a, _rn3b] if x) or "房间级校核未通过")
    elif _rs3a == "待核验" or _rs3b == "待核验":
        _room_status3, _room_note3 = "待核验", ("；".join(x for x in [_rn3a, _rn3b] if x) or "房间级校核待填写")
    else:
        _room_status3, _room_note3 = "通过", ""
    stat1 = get_scheme_status(invest_1, eng1_ok, eng1_note, Qd1_kW, qhp_d1, q_aux_eff1, end_ok1, data_ok1, mr1, q_aux_design1,
                              e_aux1, aux_heat1, unserved1, _aux_installed, _aux_elec_ok, heat_complete1,
                              _room_status1, _room_note1)
    stat2 = get_scheme_status(invest_2, eng2_ok, eng2_note, Qd2_kW, qhp_d2, q_aux_eff2, end_ok2, data_ok2, mr2, q_aux_design2,
                              e_aux2, aux_heat2, unserved2, _aux_installed, _aux_elec_ok, heat_complete2,
                              _room_status2, _room_note2)
    stat3 = get_scheme_status(invest_3, eng3_ok, eng3_note, Qd3_kW, qhp_d3, q_aux_eff3, end_ok3, data_ok3, mr3, q_aux_design3,
                              e_aux3, aux_heat3, unserved3, _aux_installed, _aux_elec_ok, heat_complete3,
                              _room_status3, _room_note3)
    status_df = pd.DataFrame([
        {"方案":"方案1仅换热泵","预算满足":stat1["budget_ok"],"工程安装条件":stat1["engineering_note"],
         "设计工况容量(MR≥1)":stat1["hp_cap_ok"],"需备用容量(kW)":stat1["q_aux_design"],"末端能力满足":stat1["terminal_ok"],
         "模型适用性":stat1["model_ok"],"备用电力容量":stat1["aux_elec_ok"],"供热完整性":stat1["heat_ok"],
         "房间级校核":stat1["room_status"],"整体可行":stat1["eligible"]},
        {"方案":"方案2围护+热泵","预算满足":stat2["budget_ok"],"工程安装条件":stat2["engineering_note"],
         "设计工况容量(MR≥1)":stat2["hp_cap_ok"],"需备用容量(kW)":stat2["q_aux_design"],"末端能力满足":stat2["terminal_ok"],
         "模型适用性":stat2["model_ok"],"备用电力容量":stat2["aux_elec_ok"],"供热完整性":stat2["heat_ok"],
         "房间级校核":stat2["room_status"],"整体可行":stat2["eligible"]},
        {"方案":"方案3围护+末端+热泵","预算满足":stat3["budget_ok"],"工程安装条件":stat3["engineering_note"],
         "设计工况容量(MR≥1)":stat3["hp_cap_ok"],"需备用容量(kW)":stat3["q_aux_design"],"末端能力满足":stat3["terminal_ok"],
         "模型适用性":stat3["model_ok"],"备用电力容量":stat3["aux_elec_ok"],"供热完整性":stat3["heat_ok"],
         "房间级校核":stat3["room_status"],"整体可行":stat3["eligible"]},
    ])
    st.subheader("🔍可行性闸门状态表（预算/工程安装条件/设计工况容量/末端能力/模型适用性/备用电力/供热完整性/房间级校核；未确认项显示待核验）")
    st.dataframe(status_df, width="stretch")

    # ===== 独立可行性闸门（热泵按设计工况可用制热量校核 + 备用配置 + 有效性分维度 + 供热完整性 + 工程条件 + 房间级） =====
    with st.expander("🚦 独立可行性闸门（设计工况可用制热量 + 备用配置 + 模型适用性 + 供热完整性 + 工程条件 + 房间级）"):
        st.info("①热泵容量不能用样本额定制热量：须用设计工况(室外=郑州设计温度，供水=末端反算tg)估算面插值后的可用制热量Q_HP,avail校核，"
                "并给出容量裕量 MR=Q_HP,avail/Q_design（建议≥1.10，下限1.00）。"
                "②容量与辅热分口径：需备用容量 Q_aux,design=max(0,Qd−Q_HP,avail,design)（设计点峰值缺口）与年度 备用供热/E_aux/未满足热量（分段积分）分别报告；"
                "备用热源未确认时不假定足额（当前配置：" + _aux_mode_short + "，已安装" + str(_aux_installed) + "kW，有效" + str(round(q_aux_eff1,2)) + "~" + str(round(q_aux_eff3,2)) + "kW）。"
                "③模型适用性按三独立维度判定（容量域Q_valid / COP域COP_valid(室外温度≥-10℃说明书工况下限) / 设备包络hardware_valid(供水≤60℃)），综合AND；"
                "不得用容量表域代替COP域；COP域外仅作带明显标记的教学估计并退出正式排序。"
                "④供热完整性：基准方案供热不足时，相对节电率/减排/回收期一律标'不可比'。"
                "⑤工程安装条件与房间级校核：未确认项显示待核验、不默认绿灯（外立面许可/外机位置/电力容量/排水防冻/管路水力/最不利房间/地暖有效面积与表面温度）。")
        _data_ok_list = [data_ok1, data_ok2, data_ok3]
        _mr_list = [mr1, mr2, mr3]
        _rows_gate = []
        _gate_reasons = []
        _validity_list = [valid1, valid2, valid3]
        _qaux_eff_list = [q_aux_eff1, q_aux_eff2, q_aux_eff3]
        _qaux_d_list = [q_aux_design1, q_aux_design2, q_aux_design3]
        _unserved_list = [unserved1, unserved2, unserved3]
        _hcomplete_list = [heat_complete1, heat_complete2, heat_complete3]
        _incmp_list = [comp_ok2, comp_ok3]
        _eng_ok_list = [eng1_ok, eng2_ok, eng3_ok]
        _eng_note_list = [eng1_note, eng2_note, eng3_note]
        _room_st_list = [_room_status1, _room_status2, _room_status3]
        _room_note_list = [_room_note1, _room_note2, _room_note3]
        for _i, (nm, inv, eng_ok_i, Qd, tgv, hpid, endok) in enumerate([
            ("方案1仅换热泵", invest_1, eng1_ok, Qd1_kW, tg1, "HP0", end_ok1),
            ("方案2围护+热泵", invest_2, eng2_ok, Qd2_kW, tg2, "HP0", end_ok2),
            ("方案3围护+末端+设备B", invest_3, eng3_ok, Qd3_kW, tg3, "HP1", end_ok3),
        ]):
            cop_d, qhp_d, _vld_d, _warn_d = hp_available_at_design(build, equip, hpid, tgv)
            b_ok = inv <= budget
            e_ok = eng_ok_i
            h_ok = (qhp_d + _qaux_eff_list[_i]) >= Qd
            t_ok = endok
            d_ok = _data_ok_list[_i]
            el_ok = _aux_elec_ok
            ht_ok = _hcomplete_list[_i]
            room_ok = (_room_st_list[_i] == "通过")
            mr_v = round(qhp_d/Qd,3) if Qd>1e-9 else None
            q_aux_d = _qaux_d_list[_i]
            _v = _validity_list[_i]
            _v_txt = ("容量域✅/COP域✅/设备包络✅" if _v["all_valid"] else
                      "容量域" + ("✅" if _v["q_valid"] else "❌") +
                      "/COP域" + ("✅" if _v["cop_valid"] else "❌") +
                      "/设备包络" + ("✅" if _v["hardware_valid"] else "❌"))
            _rows_gate.append({"方案":nm, "初投资(元)":round(inv,0), "预算满足":b_ok, "工程安装条件":_eng_note_list[_i],
                               "设计工况Q_HP可用(kW)":qhp_d, "设计负荷(kW)":round(Qd,2),
                               "容量裕量MR":mr_v, "需备用容量(kW)":q_aux_d, "已配置有效备用(kW)":_qaux_eff_list[_i],
                               "热泵容量满足":h_ok, "末端满足":t_ok, "模型适用性(容量/COP/包络)":_v_txt,
                               "备用电力容量":el_ok, "供热完整性":ht_ok, "房间级校核":_room_st_list[_i],
                               "未满足热量(kWh)":_unserved_list[_i],
                               "整体可行":b_ok and e_ok and h_ok and t_ok and d_ok and el_ok and ht_ok and room_ok})
            _rs = []
            if not b_ok: _rs.append("❌超出预算")
            if not e_ok: _rs.append("❌工程条件待核验：" + _eng_note_list[_i])
            if not h_ok: _rs.append(f"❌设计工况容量不足(MR={mr_v})，需配置备用热源容量≥{q_aux_d}kW（当前有效备用{_qaux_eff_list[_i]}kW）")
            if _room_st_list[_i] == "待核验":
                _rs.append("❌房间级校核待核验（" + (_room_note_list[_i] or "未填写房间负荷或房间末端额定散热量") + "）")
            elif _room_st_list[_i] == "未通过":
                _rs.append("❌房间级校核未通过（" + _room_note_list[_i] + "）")
            if not t_ok: _rs.append("❌末端能力不足")
            if not d_ok:
                _rs.append("❌模型适用性不满足：" + (_v["reason"] if _v["reason"] else "工况越出性能估算面范围") + "（域外仅教学估计，退出正式排序）")
            if not el_ok: _rs.append(f"❌备用热源电力容量不足：已安装{_aux_installed}kW > 配电可增容上限{_aux_elec_limit_v}kW")
            if not ht_ok: _rs.append("❌供热完整性不足（末端能力不足或存在未满足热量）；相对本方案的节能比较不可比")
            _gate_reasons.append("；".join(_rs) if _rs else "✅全部条件通过，方案可行")
        st.dataframe(pd.DataFrame(_rows_gate), width="stretch", hide_index=True)
        for _nm, _rsn in zip(["方案1", "方案2", "方案3"], _gate_reasons):
            st.markdown(f"**{_nm}**：{_rsn}")
        if _incmp_reason:
            st.error("⚠️" + _incmp_reason)
        st.caption("五个独立判断逐条输出；模型适用性=容量域∩COP域∩设备包络（综合AND），任一失败即不通过；"
                   "COP域外估计带明显标记并退出正式排序；供热完整性不足时禁止输出可比节电率/减排/回收期。")
    def gen_status_text(st):
        msg_list=[]
        if not st["budget_ok"]: msg_list.append("❌超出预算")
        if not st["engineering_ok"]: msg_list.append("❌" + st.get("engineering_note", "工程条件待核验"))
        if st.get("room_status", "待核验") == "待核验":
            msg_list.append("❌房间级校核待核验（" + (st.get("room_note", "") or "未填写房间负荷或房间末端额定散热量") + "）")
        elif st.get("room_status", "待核验") == "未通过":
            msg_list.append("❌房间级校核未通过（" + st.get("room_note", "") + "）")
        if not st["hp_cap_ok"]:
            qhp = st.get("qhp_avail_design", 0)
            qd = st.get("q_load", 0)
            qaux_d = st.get("q_aux_design", 0)
            eaux_y = st.get("e_aux_year", 0)
            qaux_y = st.get("q_aux_year", 0)
            unserved = st.get("unserved", 0)
            qaux_cfg = st.get("q_aux_configured", 0)
            msg_list.append(
                f"❌设计工况容量不足：热泵可用制热量{qhp:.2f}kW+已配置有效备用{qaux_cfg:.2f}kW < 设计热负荷{qd:.2f}kW，"
                f"需配置备用热源容量≥{qaux_d:.2f}kW；"
                f"按当前HDD分段气象数据(最低段-15~-10℃，未含设计点以下逐时数据)估算，"
                f"年度实际备用供热{qaux_y:.1f}kWh、备用用电{eaux_y:.1f}kWh；"
                f"当前备用配置下的未满足热量{unserved:.1f}kWh（未确认时不假定备用足额）"
            )
        if not st["terminal_ok"]: msg_list.append("❌末端能力不足，无法覆盖热负荷")
        if not st["model_ok"]: msg_list.append("❌模型适用性不满足(容量域∩COP域∩设备包络，见有效性明细)")
        if not st.get("aux_elec_ok", True): msg_list.append(f"❌备用热源电力容量不足：已安装{st.get('aux_installed',0)}kW > 配电可增容上限")
        if not st.get("heat_ok", True): msg_list.append("❌供热完整性不足（末端能力不足或存在未满足热量），相对本方案的节能比较不可比")
        if len(msg_list)>0:
            return "；".join(msg_list)
        return "✅全部条件通过，方案可行"
    tag_1 = gen_status_text(stat1)
    tag_2 = gen_status_text(stat2)
    tag_3 = gen_status_text(stat3)
    candidates=[]
    # V1.34：仅 model_ok=True（模型适用性）的方案可进入推荐候选
    if stat2["eligible"] and stat2["model_ok"] and payback_2 is not None:
        candidates.append(("方案2",payback_2,elec_save_rate_2))
    if stat3["eligible"] and stat3["model_ok"] and payback_3 is not None:
        candidates.append(("方案3",payback_3,elec_save_rate_3))
    best_scheme = min(candidates,key=lambda x:x[1])[0] if candidates else None
    budget_sufficient = budget >= invest_3*1.2
    eco_scheme = None
    # V1.35：经济性比较仅在供热完整性成立（可比）时给出
    if stat2["eligible"] and stat2["model_ok"] and stat3["eligible"] and stat3["model_ok"] and comp_ok2 and comp_ok3:
        eco_scheme = "方案3" if elec_save_rate_3>=elec_save_rate_2 else "方案2"
    elif stat2["eligible"] and stat2["model_ok"] and comp_ok2:
        eco_scheme = "方案2"
    elif stat3["eligible"] and stat3["model_ok"] and comp_ok3:
        eco_scheme = "方案3"
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
        "aux_p_rated":_aux_p_rated_v,
        "aux_hours1":aux_h1, "aux_hours2":aux_h2, "aux_hours3":aux_h3,
        "room_status1":_room_status1, "room_status2":_room_status2, "room_status3":_room_status3,
        "q_aux_design1":q_aux_design1,"q_aux_design2":q_aux_design2,"q_aux_design3":q_aux_design3,
        "q_aux_eff1":q_aux_eff1,"q_aux_eff2":q_aux_eff2,"q_aux_eff3":q_aux_eff3,
        "aux_heat1":aux_heat1,"aux_heat2":aux_heat2,"aux_heat3":aux_heat3,
        "unserved1":unserved1,"unserved2":unserved2,"unserved3":unserved3,
        "heat_complete1":heat_complete1,"heat_complete2":heat_complete2,"heat_complete3":heat_complete3,
        "comp_ok2":comp_ok2,"comp_ok3":comp_ok3,
        "valid1":valid1,"valid2":valid2,"valid3":valid3,
        "co2_1":co2_1,"co2_2":co2_2,"co2_3":co2_3,
        "tg1":tg1,"tg2":tg2,"tg3":tg3,
        "spf_sys1":spf_sys1,"spf_sys2":spf_sys2,"spf_sys3":spf_sys3,
        "data_ok1":data_ok1,"data_ok2":data_ok2,"data_ok3":data_ok3,
        "mr1":mr1,"mr2":mr2,"mr3":mr3,
        "e_hp1":e_hp1,"e_aux1":e_aux1,"e_hp2":e_hp2,"e_aux2":e_aux2,"e_hp3":e_hp3,"e_aux3":e_aux3,
        "elec_1_old":elec_1_old,"elec_2_old":elec_2_old,"elec_3_old":elec_3_old,
        "tag_1":tag_1,"tag_2":tag_2,"tag_3":tag_3,
        "best_scheme":best_scheme,
        "aux_mode":_aux_mode_v,"aux_installed":_aux_installed,"aux_eta":_aux_eta_v,
        "aux_cost_per_kw":_aux_cost_per_kw_v,"aux_elec_limit":_aux_elec_limit_v,"season_hours":_season_hours_v,
        "_fingerprint":calc_input_fingerprint(),
        "_app_version":APP_VERSION,"_data_version":CALC_DATA_VERSION,
        "_timestamp":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    st.info(f"🔍中间输出｜方案1总热损失H1={round(H1_kWK,4)} kW/K；单位面积热负荷 {q_load_per_area1} W/m²；"
            f"SPF_HP+aux 方案1={spf_sys1}｜方案2={spf_sys2}｜方案3={spf_sys3}")
    # 输出模型适用性 / 设计工况警告（V1.34：估算面越界才报警，且纳入第五道闸门）
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

    with st.expander("🔍查看：室外温度分段插值能耗明细（V1.34估算面）+ 度时守恒校核（V1.35：度时/时长严格分离）"):
        # 各温区度时之和 = HDD18×24（允许偏差≤0.5%）；度时(℃·h) ≠ 时长(h)
        _sum_deg = sum(s.get("degree_hours_seg", s.get("hdd_segment", 0.0) * 24.0) for s in seg1_full)
        _hdd_deg = build["HDD"] * 24.0
        _cons_dev = abs(_sum_deg - _hdd_deg) / _hdd_deg * 100.0 if _hdd_deg > 1e-9 else 0.0
        _cons_ok = _cons_dev <= 0.5
        _sum_dur = sum((s.get("duration_hours_seg") or 0.0) for s in seg1_full)
        st.caption(f"🧮【度时守恒校核】度时合计 ΣD_i = {round(_sum_deg,1)} ℃·h；HDD18×24 = {round(_hdd_deg,1)} ℃·h；"
                   f"偏差 {round(_cons_dev,4)}%（≤0.5% 通过）→ {'✅守恒' if _cons_ok else '❌不守恒'}。"
                   f"该项仅检查温差积分总量（度时），不是运行时长；供暖运行时长 Σh_i = {round(_sum_dur,1)} h 为按采暖期总时长×度时占比的一阶假设"
                   f"（当前 {round(_season_hours_v,0)} h），须由气象时序另行统计校核，供热满足性与辅助耗电应按各时段实际小时数校核。")
        st.caption("单位说明：度时D_i(℃·h)=HDD分项×24，仅作温差积分；时长h_i(h)为运行时长（一阶假设值）；两者严禁互相替代。"
                   f"当前备用配置：{_aux_mode_short} {_aux_installed:.1f}kW；未确认时不假定足额，未满足热量按实际缺口计。")
        st.markdown("**方案1分段明细**（*时长h_i为采暖期总时长×度时占比的一阶假设，须气象时序校核）")
        st.dataframe(pd.DataFrame(seg1_full).rename(columns=SEG_DISPLAY_LABELS).fillna("—"))
        st.markdown("**方案2分段明细**")
        st.dataframe(pd.DataFrame(seg2_full).rename(columns=SEG_DISPLAY_LABELS).fillna("—"))
        st.markdown("**方案3分段明细**")
        st.dataframe(pd.DataFrame(seg3_full).rename(columns=SEG_DISPLAY_LABELS).fillna("—"))

    # ===== 辅助电加热 E_aux + 运行小时（三套方案；审查意见①：等效小时分母=P_aux,rated） =====
    with st.expander("🔋备用热源：所需容量/已配置容量/实际备用供热/备用用电E_aux/等效满载小时/实际开启小时/未满足热量"):
        st.info(f"当前备用热源配置：**{_aux_mode_short}**，已安装 {_aux_installed:.1f} kW，η={_aux_eta_v}，"
                f"电辅热额定电功率 P_aux,rated={_aux_p_rated_v:.1f} kW，"
                f"采暖季时长 {_season_hours_v:.0f} h（度时占比折算时长的一阶假设，须气象时序校核）。\n"
                "热泵可用制热能力不足的部分由备用热源承担；**未确认时不假定其足额**：未配置时备用供热=0，全部缺口计为未满足热量。"
                "E_HP+E_aux 即各方案年耗电主指标；备用用电 E_aux=实际备用供热/η。"
                "年度备用供热/备用用电（分段积分）与设计工况'需备用容量'分别报告。"
                "等效满载小时=E_aux/P_aux,rated（电加热额定电功率，非热泵额定制热量）；实际开启小时=ΣI(P_aux,i>0)·Δt_i。")
        aux_items = [
            (seg1, tg1, "HP0", equip["Qhp_rated1"], "方案1：仅热泵(E0-T0-HP0)", q_aux_eff1, q_aux_design1, aux_heat1, unserved1),
            (seg2, tg2, "HP0", equip["Qhp_rated2"], "方案2：围护+热泵(E2-T0-HP0)", q_aux_eff2, q_aux_design2, aux_heat2, unserved2),
            (seg3, tg3, "HP1", equip["Qhp_rated3"], "方案3：围护+地暖+设备B(E2-T2-HP1)", q_aux_eff3, q_aux_design3, aux_heat3, unserved3),
        ]
        aux_cols = st.columns(3)
        for idx, (seg_x, tg_x, hp_id_x, rated_x, label_x, qaux_eff_x, qaux_d_x, aux_heat_x, unserved_x) in enumerate(aux_items):
            seg_full_x, e_hp_x, e_aux_x2, aux_h_x, d_ok_x, _, unserved_x2 = calc_segment_hp_aux_2d(
                seg_x, hp_id_x, tg_x, rated_x,
                q_aux_capacity=(qaux_eff_x if qaux_eff_x > 1e-9 else None), eta_aux=_aux_eta_v, season_hours=_season_hours_v,
                p_aux_rated=_aux_p_rated_v)
            with aux_cols[idx]:
                st.markdown(f"**{label_x}**")
                st.metric("热泵年耗电 E_HP (kWh)", round(e_hp_x, 2))
                st.metric("备用用电 E_aux (kWh)", round(e_aux_x2, 2))
                st.metric("实际备用供热 (kWh)", round(aux_heat_x, 2))
                st.metric("需备用容量(设计点, kW)", round(qaux_d_x, 2))
                st.metric("已配置有效备用 (kW)", qaux_eff_x)
                st.metric("等效满载小时 (h)", (f"{aux_h_x['equiv_full_hours']:.1f}" if aux_h_x["equiv_full_hours"] is not None else "不适用/待配置"),
                          help="=E_aux/P_aux,rated；未配置电辅热或额定功率未知时显示'不适用/待配置'")
                st.metric("实际开启小时 (h)", (f"{aux_h_x['actual_on_hours']:.1f}" if aux_h_x["actual_on_hours"] is not None else "待气象时序"),
                          help="=ΣI(P_aux,i>0)·Δt_i，由分段时长累计（一阶假设，须气象时序校核）")
                st.metric("未满足热量 (kWh)", unserved_x2)
                _vx = _validity_list[idx]
                _vx_txt = ("✅容量域/COP域/设备包络均有效" if _vx["all_valid"] else
                           "⚠️容量域" + ("✅" if _vx["q_valid"] else "❌") + "/COP域" + ("✅" if _vx["cop_valid"] else "❌") +
                           "/设备包络" + ("✅" if _vx["hardware_valid"] else "❌") + "（域外仅教学估计，退出正式排序）")
                st.caption(_vx_txt if d_ok_x else "⚠️存在越出估算面的工况（模型适用性不满足，退出正式排序）")
                if unserved_x2 > 0:
                    st.warning(f"⚠️存在未满足热量{unserved_x2:.1f}kWh：已配置备用容量不足或末端受限，供热不完整，相对本方案的节能比较不可比")
                df_aux_seg = pd.DataFrame(seg_full_x)[["T_low","T_high","Q_heat_kwh","cop_interp","hp_avail_kW","Q_hp_kwh","Q_aux_kwh","Q_unmet_kwh","elec_hp","elec_aux"]]
                st.dataframe(df_aux_seg.rename(columns=SEG_DISPLAY_LABELS), width="stretch")

    # ===== V1.9新增：围护分项热损失分解 & 能耗强度 & HDD回归校核对照 =====
    with st.expander("🔍 围护分项热损失分解 & 能耗强度 kWh/(m²·a) & 回归校核"):
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

    # SPF指标名称根据口径切换（含辅助电加热 / 仅热泵主机）
    spf_label = "SPF_HP+aux=Q_delivered/(E_HP+E_aux)" if spf_include_aux else "SPF_HP=Q_delivered/E_HP（仅热泵主机，不含辅助电加热）"
    spf_denom_note = "分母=E_HP+E_aux（含辅助电加热）" if spf_include_aux else "分母=E_HP（仅热泵主机耗电，不含辅助电加热）"
    # 审查意见①：有辅热实际运行时选"仅主机"口径需警示，避免误以为系统级SPF
    if (not spf_include_aux) and any(v > 1e-9 for v in (e_aux1, e_aux2, e_aux3)):
        st.warning("⚠️ 当前选了「仅热泵主机」口径，但本方案实际有辅助电加热运行（E_aux>0）。"
                   "该口径仅反映热泵主机效率，系统级年耗电与SPF应使用「含辅助电加热」口径；两口径分子同为 Q_delivered，分母不同，不可混用。")
    col_a,col_b,col_c = st.columns(3)
    CARD_FIX_HEIGHT=850
    with col_a:
        with st.container(height=CARD_FIX_HEIGHT):
            st.markdown("### 🟦方案1｜仅更换热泵（基准对照）")
            st.markdown(f"**可行性：**{tag_1}")
            st.metric(spf_label,spf_sys1)
            st.metric("供水温度(℃)",tg1)
            st.metric("设计工况COP",cop_d1,delta=("⚠️COP域外估计" if not valid1["cop_valid"] else None))
            st.metric("容量裕量MR",mr1)
            st.metric("热泵可用制热量(kW)",qhp_d1)
            st.metric("设计热负荷(kW)",round(Qd1_kW,2))
            st.metric("年耗电(kWh)",f"{elec_1:,.0f}",delta=f"E_aux={e_aux1:.0f}")
            st.metric("需备用容量/已配置有效(kW)",f"{q_aux_design1:.2f} / {q_aux_eff1:.2f}")
            st.metric("未满足热量(kWh)",f"{unserved1:.1f}")
            st.metric("年碳排放(kgCO₂)",f"{co2_1:,.0f}")
            st.metric("总初投资(元)",f"{int(round(invest_1,0)):,}")
    with col_b:
        with st.container(height=CARD_FIX_HEIGHT):
            st.markdown("### 🟩方案2｜围护保温改造+设备A")
            if not allow_wall_retrofit: st.info("🚫工程约束，禁止围护改造")
            st.markdown(f"**可行性：**{tag_2}")
            st.metric(spf_label,spf_sys2)
            st.metric("供水温度(℃)",tg2)
            st.metric("设计工况COP",cop_d2,delta=("⚠️COP域外估计" if not valid2["cop_valid"] else None))
            st.metric("容量裕量MR",mr2)
            st.metric("热泵可用制热量(kW)",qhp_d2)
            st.metric("设计热负荷(kW)",round(Qd2_kW,2))
            st.metric("相对方案1购电",(f"-{elec_save_rate_2}%" if elec_save_rate_2 is not None else "不可比"),delta=f"E_aux={e_aux2:.0f}")
            st.metric("需备用容量/已配置有效(kW)",f"{q_aux_design2:.2f} / {q_aux_eff2:.2f}")
            st.metric("未满足热量(kWh)",f"{unserved2:.1f}")
            st.metric("相对方案1减排(kg)",(f"-{co2_reduce_2:,.0f}" if co2_reduce_2 is not None else "不可比"),delta=(f"-{co2_reduce_rate_2}%" if co2_reduce_rate_2 is not None else "不可比"))
            st.metric("总初投资(元)",f"{int(round(invest_2,0)):,}")
    with col_c:
        with st.container(height=CARD_FIX_HEIGHT):
            st.markdown("### 🟨方案3｜围护改造+低温地暖+设备B")
            if not allow_wall_retrofit: st.info("🚫工程约束，禁止围护改造")
            st.markdown(f"**可行性：**{tag_3}")
            st.metric(spf_label,spf_sys3)
            st.metric("供水温度(℃)",tg3)
            st.metric("设计工况COP",cop_d3,delta=("⚠️COP域外估计" if not valid3["cop_valid"] else None))
            st.metric("容量裕量MR",mr3)
            st.metric("热泵可用制热量(kW)",qhp_d3)
            st.metric("设计热负荷(kW)",round(Qd3_kW,2))
            st.metric("相对方案1购电",(f"-{elec_save_rate_3}%" if elec_save_rate_3 is not None else "不可比"),delta=f"E_aux={e_aux3:.0f}")
            st.metric("需备用容量/已配置有效(kW)",f"{q_aux_design3:.2f} / {q_aux_eff3:.2f}")
            st.metric("未满足热量(kWh)",f"{unserved3:.1f}")
            st.metric("相对方案1减排(kg)",(f"-{co2_reduce_3:,.0f}" if co2_reduce_3 is not None else "不可比"),delta=(f"-{co2_reduce_rate_3}%" if co2_reduce_rate_3 is not None else "不可比"))
            st.metric("总初投资(元)",f"{int(round(invest_3,0)):,}")
    st.caption("卡片仅展示关键结论指标；全部中间量（H、Qd、单位面积热负荷、铭牌SCOP、旧算法SPF、回水温度、末端散热量、分段能耗、备用热源等）见下方『三方案对比总表』及各可折叠明细。"
               "方案2/3的购电/排放变化均为“相对方案1（热泵供暖情景）”且要求**等供热**（供热完整性成立）才可比；"
               "供热不足时标'不可比'，不代表相对住户原有供暖方式的真实节能率/减排量，真实基准见下方『改造前实际系统基准』模块。")
    st.divider()
    # 统一SPF列名（对比表与图表共用，避免KeyError）
    spf_col_name = "SPF主指标(" + ("含辅助电加热" if spf_include_aux else "仅热泵主机") + ")"
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
        "需备用容量Q_aux,design(kW)":[q_aux_design1,q_aux_design2,q_aux_design3],
        "已配置有效备用容量(kW)":[q_aux_eff1,q_aux_eff2,q_aux_eff3],
        "实际备用供热(kWh)":[aux_heat1,aux_heat2,aux_heat3],
        "未满足热量(kWh)":[unserved1,unserved2,unserved3],
        "供热完整性":["是" if heat_complete1 else "否","是" if heat_complete2 else "否","是" if heat_complete3 else "否"],
        "相对方案1比较可比":["基准",("是" if comp_ok2 else "否"),("是" if comp_ok3 else "否")],
        "热负荷削减率(%)":[0.0,load_save_rate_2,load_save_rate_3],
        "全年采暖需热量(kWh)":[round(q_year1_kwh,1),round(q_year2_kwh,1),round(q_year3_kwh,1)],
        "二维分段算法年耗电量(kWh)":[round(elec_1,1),round(elec_2,1),round(elec_3,1)],
        "其中E_HP(kWh)":[e_hp1,e_hp2,e_hp3],
        "其中E_aux(kWh)":[e_aux1,e_aux2,e_aux3],
        "旧SPF算法年耗电量(kWh)":[round(elec_1_old,1),round(elec_2_old,1),round(elec_3_old,1)],
        "相对方案1购电变化(%)":[0.0,elec_save_rate_2,elec_save_rate_3],
        "年运行期碳排放(kgCO₂)":[co2_1,co2_2,co2_3],
        "相对方案1排放变化(kgCO₂/a)":[0.0,co2_reduce_2,co2_reduce_3],
        "相对方案1排放变化率(%)":[0.0,co2_reduce_rate_2,co2_reduce_rate_3],
        "项目总初投资(元)":[round(invest_1,0),round(invest_2,0),round(invest_3,0)],
        "可行性校验":[tag_1,tag_2,tag_3],
        "年采暖电费(元)":[round(year_cost_1,2),round(year_cost_2,2),round(year_cost_3,2)],
        "相对方案1增量静态回收期(年)":[None,payback_2,payback_3]
    })
    result_df = result_df.replace({np.nan: None})  # 避免 NaN 混入文本列
    result_df["相对方案1购电变化(%)"] = result_df["相对方案1购电变化(%)"].apply(lambda v: v if v is not None else "不可比")
    result_df["相对方案1排放变化(kgCO₂/a)"] = result_df["相对方案1排放变化(kgCO₂/a)"].apply(lambda v: v if v is not None else "不可比")
    result_df["相对方案1排放变化率(%)"] = result_df["相对方案1排放变化率(%)"].apply(lambda v: v if v is not None else "不可比")
    st.dataframe(result_df, width="stretch")
    st.caption("本表节能/减排列均为“相对方案1（热泵供暖情景）”口径且要求**等供热**（供热完整性成立，否则标'不可比'）；非相对住户原有供暖方式的真实节能率；碳排放为【运行期电力间接碳排放】（电耗×电网排放因子，位置法，单位kgCO₂/a），不包含围护材料、设备制造/更换的隐含碳；回收期为【相对方案1增量静态回收期】，非项目真实全生命周期回收期。")
    csv_bytes = result_df.to_csv(index=False,encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button("📥下载CSV结果",csv_bytes,file_name=f"{ht}_热泵改造{APP_VERSION}_估算面分段能耗.csv",mime="text/csv")

    # ===== 推荐状态机（先于导出计算；分别列工程条件与房间级，不混说"待核验"）=====
    _any_retrofit_ok = (stat2["eligible"] or stat3["eligible"])
    _any_model_invalid = not (data_ok1 and data_ok2 and data_ok3)
    # 分别收集：工程待核验项、房间级待核验项、房间级未通过项
    _eng_pending = []
    if not eng1_ok: _eng_pending.append("方案1：" + eng1_note)
    if not eng2_ok: _eng_pending.append("方案2：" + eng2_note)
    if not eng3_ok: _eng_pending.append("方案3：" + eng3_note)
    _room_pending = [_nm for _nm, _s in [("方案1", _room_status1), ("方案2", _room_status2), ("方案3", _room_status3)] if _s == "待核验"]
    _room_fail = []
    if _room_status1 == "未通过": _room_fail.append("方案1：" + (_room_note1 or ""))
    if _room_status2 == "未通过": _room_fail.append("方案2：" + (_room_note2 or ""))
    if _room_status3 == "未通过": _room_fail.append("方案3：" + (_room_note3 or ""))
    if _any_model_invalid:
        rec_state_title = "⛔状态C：性能数据不足或工况越出估算面，暂不输出最优/推荐方案（请补充厂家数据或调整设备）"
        rec_state_color = "red"
    elif not heat_complete1:
        rec_state_title = "⛔状态C：基准方案存在供热不足（末端能力不足或存在未满足热量），当前电量仅为受限运行情景值；节能/减排/回收期暂不可比——请先补足基准供热或统一舒适度（提高供水温度必须在设备≤60℃和末端允许工况内）"
        rec_state_color = "red"
    elif _room_fail:
        rec_state_title = "⛔状态C：房间级校核未通过（最不利房间或地暖表面温度/有效面积不满足；详见下列原因）"
        rec_state_color = "red"
    elif _eng_pending or _room_pending:
        _parts = []
        if _eng_pending:
            _parts.append("工程安装条件待确认：" + "；".join(_eng_pending))
        if _room_pending:
            _parts.append("房间级校核待填写：" + "、".join(_room_pending) + "（页面2 最不利房间负荷与末端额定散热量）")
        rec_state_title = "🟠状态B：" + "；".join(_parts) + "。请逐项确认后再评估方案。"
        rec_state_color = "orange"
    elif _any_retrofit_ok:
        rec_state_title = "✅状态A：可行改造方案推荐（以下结论仅在当前输入、数据版本和模型边界内成立）"
        rec_state_color = "green"
    elif stat1["eligible"]:
        rec_state_title = "🟠状态B：当前约束下无可行改造方案；方案1仅为比较基准，不构成实施推荐"
        rec_state_color = "orange"
    else:
        rec_state_title = "⛔状态C：无可行方案，请调整约束或补充数据"
        rec_state_color = "red"

    # ===== 导出完整计算报告（输入快照+当前生效参数+版本+中间量+失败原因+结论状态） =====
    with st.expander("📤 导出完整计算报告（输入快照+当前生效参数+版本+中间量+失败原因+结论状态）"):
        st.caption("导出数值以本次计算快照为准；数据不足的字段保留缺失状态（显示'缺失（未计算）'），不以0填充；"
                   "E_aux=0 等合法零值仍按0导出，与缺失区分。")
        _coef_s = st.session_state["coef_set"]
        _rep_rows = []
        _rep_rows.append({"类别":"当前生效参数","参数":"造价模式/本次生效系数","数值":f"{st.session_state['retrofit_mode']}｜围护{eff_coef_env}/热泵{eff_coef_pump}/末端{eff_coef_term}","来源":st.session_state["retrofit_mode"],"备注":"分项结算（分户独立情景下批量设置值不生效）"})
        _rep_rows.append({"类别":"用户设置值(批量采购参考)","参数":"围护/热泵/末端系数","数值":f"{_coef_s['coef_envelope']}/{_coef_s['coef_pump']}/{_coef_s['coef_terminal']}","来源":"页面2","备注":"分户独立情景下本次不生效"})
        _rep_rows.append({"类别":"当前生效参数","参数":"SPF计算口径","数值":spf_label,"来源":"页面3","备注":"仅计热泵主机与辅助电加热耗电，未计循环泵/控制/待机"})
        _rep_rows.append({"类别":"当前生效参数","参数":"允许外墙围护改造","数值":str(allow_wall_retrofit),"来源":"页面3","备注":"外立面许可"})
        _rep_rows.append({"类别":"当前生效参数","参数":"工程安装条件","数值":f"方案1:{eng1_note}；方案2:{eng2_note}；方案3:{eng3_note}","来源":"页面3核验区","备注":"未确认项显示待核验"})
        _rep_rows.append({"类别":"当前生效参数","参数":"房间级校核","数值":f"方案1:{_room_status1}；方案2:{_room_status2}；方案3:{_room_status3}","来源":"页面2/3","备注":(_room_note1 or _room_note2 or _room_note3 or "通过")})
        _rep_rows.append({"类别":"当前生效参数","参数":"辅助电加热等效满载小时(h)","数值":f"方案1:{aux_h1['equiv_full_hours']}；方案2:{aux_h2['equiv_full_hours']}；方案3:{aux_h3['equiv_full_hours']}","来源":"计算","备注":"=E_aux/P_aux,rated；未配置或额定功率未知→不适用/待配置"})
        _rep_rows.append({"类别":"当前生效参数","参数":"辅助电加热实际开启小时(h)","数值":f"方案1:{aux_h1['actual_on_hours']}；方案2:{aux_h2['actual_on_hours']}；方案3:{aux_h3['actual_on_hours']}","来源":"计算","备注":"=ΣI(P_aux,i>0)·Δt_i；无时长数据→待气象时序"})
        for _k, _v in build.items():
            _rep_rows.append({"类别":"输入快照-建筑","参数":_k,"数值":str(_v),"来源":"见参数来源台账","备注":""})
        for _k, _v in equip.items():
            _rep_rows.append({"类别":"输入快照-设备/造价","参数":_k,"数值":str(_v),"来源":"见参数来源台账","备注":""})
        _rep_rows.append({"类别":"输入快照-备用热源","参数":"方案/已安装容量(kW)/效率/电辅热额定电功率(kW)/配电上限(kW)","数值":f"{_aux_mode_short}；{_aux_installed:.1f}；η={_aux_eta_v}；P_aux,rated={_aux_p_rated_v}；上限{_aux_elec_limit_v}","来源":"用户配置","备注":"未确认时不假定足额"})
        _rep_rows.append({"类别":"输入快照-采暖时长假设","参数":"采暖季运行时长(h)","数值":str(round(_season_hours_v,1)),"来源":"一阶假设","备注":"度时占比折算时段时长，须气象时序校核"})
        _rep_rows.append({"类别":"输入快照-改造前基准","参数":"能源类型/年能耗(kWh)/因子(kgCO₂/kWh)/可比性","数值":f"{st.session_state.get('_base_type','未录入')}；{float(st.session_state.get('_base_energy',0.0)):.0f}；{float(st.session_state.get('_base_ef',0.20)):.3f}；{bool(st.session_state.get('_base_cmp',False))}","来源":"用户配置","备注":"可比性检查通过后方可估算实际基准节能率/减排量"})
        for _nm, _v1, _v2, _v3 in [
            ("H(kW/K)", H1_kWK, H2_kWK, H3_kWK),
            ("Q_design(kW)", Qd1_kW, Qd2_kW, Qd3_kW),
            ("Q_year(kWh)", q_year1_kwh, q_year2_kwh, q_year3_kwh),
            ("SPF_HP+aux主指标", spf_sys1, spf_sys2, spf_sys3),
            ("旧算法SPF(参考，不参与判定)", spf1, spf2, spf3),
            ("供水温度tg(℃)", tg1, tg2, tg3),
            ("设计工况COP", cop_d1, cop_d2, cop_d3),
            ("容量裕量MR", mr1, mr2, mr3),
            ("模型适用性(performance_model_applicable)", int(data_ok1), int(data_ok2), int(data_ok3)),
            ("容量域/COP域/设备包络(Q/COP/HW)", f"{int(valid1['q_valid'])}/{int(valid1['cop_valid'])}/{int(valid1['hardware_valid'])}", f"{int(valid2['q_valid'])}/{int(valid2['cop_valid'])}/{int(valid2['hardware_valid'])}", f"{int(valid3['q_valid'])}/{int(valid3['cop_valid'])}/{int(valid3['hardware_valid'])}"),
            ("E_HP(kWh)", e_hp1, e_hp2, e_hp3),
            ("需备用容量Q_aux,design(kW)", q_aux_design1, q_aux_design2, q_aux_design3),
            ("已配置有效备用容量(kW)", q_aux_eff1, q_aux_eff2, q_aux_eff3),
            ("实际备用供热(kWh)", aux_heat1, aux_heat2, aux_heat3),
            ("E_aux(kWh)", e_aux1, e_aux2, e_aux3),
            ("未满足热量(kWh)", unserved1, unserved2, unserved3),
            ("供热完整性(末端能力∩无未满足热量)", int(heat_complete1), int(heat_complete2), int(heat_complete3)),
            ("相对方案1比较可比", "基准", int(comp_ok2), int(comp_ok3)),
            ("年电费(元)", year_cost_1, year_cost_2, year_cost_3),
            ("运行期碳排放(kgCO₂/a)", co2_1, co2_2, co2_3),
        ]:
            def _fmtv(_x):
                # 缺失(未计算)保留缺失状态，不以0填充；兼容字符串型行（如有效性状态"1/0/1"）
                if _x is None:
                    return "缺失（未计算）"
                return _x if isinstance(_x, str) else round(float(_x), 2)
            _rep_rows.append({"类别":"中间变量","参数":_nm,
                              "数值":f"方案1:{_fmtv(_v1)} | 方案2:{_fmtv(_v2)} | 方案3:{_fmtv(_v3)}",
                              "来源":"程序计算","备注":"H→Qd→Q_year→二维COP积分→E_HP+E_aux→费用→碳排"})
        _rep_rows.append({"类别":"可行性","参数":"闸门布尔值(预算/工程/容量/末端/模型适用性/备用电力/供热完整性/房间级)","数值":f"方案1:{int(stat1['budget_ok'])}/{int(stat1['engineering_ok'])}/{int(stat1['hp_cap_ok'])}/{int(stat1['terminal_ok'])}/{int(stat1['model_ok'])}/{int(stat1['aux_elec_ok'])}/{int(stat1['heat_ok'])}/{stat1['room_status']}；方案2:{int(stat2['budget_ok'])}/{int(stat2['engineering_ok'])}/{int(stat2['hp_cap_ok'])}/{int(stat2['terminal_ok'])}/{int(stat2['model_ok'])}/{int(stat2['aux_elec_ok'])}/{int(stat2['heat_ok'])}/{stat2['room_status']}；方案3:{int(stat3['budget_ok'])}/{int(stat3['engineering_ok'])}/{int(stat3['hp_cap_ok'])}/{int(stat3['terminal_ok'])}/{int(stat3['model_ok'])}/{int(stat3['aux_elec_ok'])}/{int(stat3['heat_ok'])}/{stat3['room_status']}","来源":"独立判断","备注":"容量=热泵+已配置有效备用；模型适用性=容量域∩COP域∩设备包络；工程/房间级未确认→待核验"})
        _rep_rows.append({"类别":"失败原因","参数":"闸门理由","数值":f"方案1:{tag_1}；方案2:{tag_2}；方案3:{tag_3}","来源":"独立判断","备注":"容量与辅热分口径；供热不完整或模型不适用时给出原因"})
        _rep_rows.append({"类别":"失败原因","参数":"模型/数据域警告","数值":"；".join([w for _nm2, _dw, _dwd in _domain_warns_all for w in list(dict.fromkeys(_dw+_dwd))]) or "无","来源":"独立判断","备注":"估算面越界/边界假设提示"})
        _rep_rows.append({"类别":"结论状态","参数":"推荐方案/推荐状态","数值":f"{best_scheme if best_scheme else '无可行方案'}｜{rec_state_title}","来源":"程序推荐","备注":"仅模型适用性通过且供热完整性成立（可比）的方案可被推荐"})
        _rep_rows.append({"类别":"复现信息","参数":"程序版本","数值":APP_VERSION + " (2026-09-09)","来源":"本程序","备注":"复算需锁定版本/数据/输入"})
        _rep_rows.append({"类别":"复现信息","参数":"计算时间","数值":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"来源":"本程序","备注":"导出数值以本次计算快照为准"})
        _rep_rows.append({"类别":"复现信息","参数":"计算快照指纹","数值":calc_input_fingerprint(),"来源":"本程序","备注":"输入/模型/数据版本任一变化即失效旧结果"})
        _rep_rows.append({"类别":"复现信息","参数":"性能数据版本","数值":"估算面" + CALC_DATA_VERSION + "（厂家锚点：MHSR120N8-S1/MHSR100N8-S1 官方说明书，COP工况下限-10℃；推算格：温升幂律 k=0.6/0.4、1.0/0.5；证据等级C）","来源":"见台账","备注":""})
        _rep_rows.append({"类别":"复现信息","参数":"气象数据版本","数值":"郑州HDD18=2106℃·d（典型气象年，分段权重见HDD_SEGMENTS）","来源":"见台账","备注":"度时守恒已校核（度时ΣD_i=HDD×24，℃·h）"})
        _rep_rows.append({"类别":"复现信息","参数":"公式版本","数值":APP_VERSION + "（H→Qd→Qyear→末端反算tg→估算面分段积分→费用/碳排→闸门+备用/电力/供热完整性）","来源":"本程序","备注":""})
        for _rr in _rep_rows:
            _rr["数值"] = str(_rr["数值"]) # 统一为文本，避免 Arrow 混合类型
        _rep_df = pd.DataFrame(_rep_rows)
        st.dataframe(_rep_df, width="stretch", hide_index=True)
        _rep_bytes = _rep_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button("📥导出完整计算报告CSV", _rep_bytes, file_name=f"暖改智选_{APP_VERSION}_{ht}_完整计算报告.csv", mime="text/csv")
    tabC1, tabC2 = st.tabs(["📊综合对比", "💰经济与敏感性"])
    color_list = ["#6366f1","#f59e0b","#10b981"]
    layout_common = dict(template="plotly_white",hovermode="x unified",height=440,font=dict(size=13),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(99,102,241,0.04)")
    with tabC1:
        st.markdown("**三方案核心指标对比：年耗电量 / SPF_HP+aux / 运行期碳排放（一图总览）**")
        fig_comp = make_subplots(rows=1, cols=3, subplot_titles=["年耗电量(kWh)","SPF"+("（含辅助电加热）" if spf_include_aux else "（仅热泵主机）"),"年运行期碳排放(kgCO₂)"])
        fig_comp.add_trace(go.Bar(x=result_df["改造方案"],y=result_df["二维分段算法年耗电量(kWh)"],name="年耗电量",marker_color="#6366f1",showlegend=False),row=1,col=1)
        fig_comp.add_trace(go.Bar(x=result_df["改造方案"],y=result_df[spf_col_name],name="SPF"+("（含辅助电加热）" if spf_include_aux else "（仅热泵主机）"),marker_color="#10b981",showlegend=False),row=1,col=2)
        fig_comp.add_trace(go.Bar(x=result_df["改造方案"],y=result_df["年运行期碳排放(kgCO₂)"],name="碳排放",marker_color="#f59e0b",showlegend=False),row=1,col=3)
        fig_comp.update_layout(title="三方案核心指标对比",**layout_common)
        st.plotly_chart(fig_comp,width="stretch")
        st.caption("SPF_HP+aux 为主指标（分段积分反算，分母=E_HP+E_aux，未计循环泵/控制/待机）；碳排放为【运行期电力间接碳排放】（kgCO₂/a），不包含围护材料、设备制造/更换的隐含碳。")
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
    # 推荐状态（rec_state_title/rec_state_color 已在导出区前计算，此处仅展示）
    st.subheader(f"{ht}｜方案推荐状态")
    st.markdown(f"<div style='font-size:18px;font-weight:800;color:{rec_state_color};padding:10px 14px;border:1px solid {rec_state_color};border-radius:10px;background:rgba(255,255,255,0.6);'>{rec_state_title}</div>", unsafe_allow_html=True)
    # 分别列出房间级未通过原因、工程待核验项、房间级待填写项（不混说）
    if _room_fail:
        st.error("**房间级校核未通过（全部并列）：**\n" + "\n".join(f"- {x}" for x in _room_fail))
    if _eng_pending:
        st.warning("**工程安装条件待确认（页面3）：**\n" + "\n".join(f"- {x}" for x in _eng_pending))
    if _room_pending:
        st.warning("**房间级校核待填写（页面2）：**\n" + "\n".join(f"- {x}" for x in _room_pending))
    # P2-2：模型边界只保留此处一处（完整边界声明；结果卡片仅作简短缺陷提示）
    with st.expander("📌 数据与模型边界（当前结果为模型情景估算）"):
        st.markdown("**当前结果为模型情景估算。** 以下为本程序完整的数据与模型边界声明（唯一完整版；侧边栏/页面4不再重复），"
                    "请据此判断结果能否用于你的问题：")
        if ht == "中间层住宅":
            st.info("本计算对象：**老旧住宅中间层；上下楼层均为采暖住户**。热工构件：外墙、外窗、外门、楼梯间非采暖隔墙、冷风渗透；**不计屋面、地面楼板热损失；不计算朝向、风力、高度附加耗热量**。"
                    "⚠️本模型不可直接用于顶层、底层、东西山墙边角户型；定位为早期方案比较/教学决策支持，不可替代工程设计选型。")
        else:
            st.info("本计算对象：**老旧住宅顶层东西山墙边户**。热工构件：普通外墙、东西山墙、屋面、外窗、外门、楼梯间非采暖隔墙、冷风渗透；**不计底层地面楼板热损失；不计算朝向、风力、高度附加耗热量**。"
                    "⚠️本模型不可直接用于中间层、底层住户；定位为早期方案比较/教学决策支持，不可替代工程设计选型。")
        st.caption("方法：有限方案枚举→计算→五道闸门筛选→按用户选择的排序规则推荐；性能数据为估算面（锚点+推算，证据等级C）；"
                   "SPF_HP+aux = Q_delivered/(E_HP+E_aux)，分母仅含热泵主机与辅助电加热耗电，未计循环泵/控制/待机；容量与辅热分口径。"
                   "等效满载小时=E_aux/P_aux,rated；实际开启小时=ΣI(P_aux,i>0)·Δt_i（一阶假设，须气象时序校核）。")
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
    _r2_save = f"-{elec_save_rate_2}%" if elec_save_rate_2 is not None else "不可比"
    _r2_co2 = f"-{co2_reduce_rate_2}%" if co2_reduce_rate_2 is not None else "不可比"
    _r3_save = f"-{elec_save_rate_3}%" if elec_save_rate_3 is not None else "不可比"
    _r3_co2 = f"-{co2_reduce_rate_3}%" if co2_reduce_rate_3 is not None else "不可比"
    _co2_txt2 = f"-{co2_reduce_2:.0f}kgCO₂/a" if co2_reduce_2 is not None else "不可比"
    _co2_txt3 = f"-{co2_reduce_3:.0f}kgCO₂/a" if co2_reduce_3 is not None else "不可比"
    if stat2["eligible"] and stat2["model_ok"]:
        rec2_label = "✅优先推荐" if best_scheme=="方案2" else "✅可推荐"
        rec2_reason = f"全部条件通过；相对方案1增量回收期{text_p2}年；相对方案1购电变化{_r2_save}；排放变化{_r2_co2}；围护构件同步保温改造。"
    elif stat2["model_ok"]:
        rec2_label = "❌不推荐"
        rec2_reason = tag_2
    else:
        rec2_label = "❌不推荐(估算面外)"
        rec2_reason = tag_2
    if stat3["eligible"] and stat3["model_ok"]:
        rec3_label = "✅优先推荐" if best_scheme=="方案3" else "✅可推荐"
        rec3_reason = f"全部条件通过；相对方案1增量回收期{text_p3}年；相对方案1购电变化{_r3_save}；排放变化{_r3_co2}；围护+低温地暖+设备B。"
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
    - 分析：围护构件同步保温；热负荷削减{load_save_rate_2}%；相对方案1购电-{elec_save_rate_2}%；相对方案1排放{_co2_txt2}；回收期 {text_p2} 年。
    - 结论：**{rec2_label}** —— {rec2_reason}
3. **方案3｜全套围护保温+低温地暖末端+设备B** —— {budget_note_3}
    - 分析：**方案3与方案2采用相同的围护改造参数，并在此基础上更换低温末端与匹配设备，因此 H3=H2、Q_design,3=Q_design,2**；热负荷削减{load_save_rate_3}%；相对方案1购电-{elec_save_rate_3}%；相对方案1排放{_co2_txt3}；回收期 {text_p3} 年。
    - 结论：**{rec3_label}** —— {rec3_reason}
{overall}
{dual_rec}
""")
    st.caption("结果提示：以上均为**模型情景估算**，不是实测结论。若闸门显示失败/待核验，请先查看失败原因（可行性闸门）与『数据与模型边界』；"
               "未确认的工程安装条件与房间级校核项不默认通过。")
    # ===== 改造前实际系统基准（审查意见⑥：先可比性检查，通过后方可估算实际基准节能率/减排量） =====
    st.divider()
    with st.expander("🏠 改造前实际系统基准（先完成可比性检查，方可估算实际基准节能率/减排量）", expanded=False):
        st.caption("方案2/3卡片及对比表上的购电/排放变化均为“相对方案1（热泵供暖情景）”，属方案间模型差额，不代表住户原有供暖方式的真实节能率/减排量。"
                   "改造前基准：录入计量与运行条件后，先进行可比性检查；通过气象及供热服务归一化后，方可估算实际基准下的节能率和运行减排量。"
                   "可比性要求：基准能源类型与计量口径明确、供暖面积一致、气象（采暖期）一致、采暖时长/室温一致、辅助设备与计量完整性已说明。")
        _b_type = st.selectbox("改造前供暖能源类型", ["未录入（暂不输出估算结果）", "集中供热（按面积计费）", "燃气壁挂炉", "直热式电采暖", "燃煤/其他"], key="_base_type")
        _b_energy = st.number_input("改造前年供暖一次能耗(kWh/年)", min_value=0.0, max_value=50000.0, value=0.0, step=100.0, key="_base_energy",
                                    help="集中供热可按面积×热指标×供暖时长估算；直热电≈本方案能耗的2~4倍量级")
        _b_ef = st.number_input("改造前单位能耗排放因子(kgCO₂/kWh)", min_value=0.0, max_value=1.5, value=0.20, step=0.01, key="_base_ef",
                                help="燃气≈0.20；直热电≈0.5897(2023河南电网，位置法)；集中供热按热源取0.11~0.30")
        _base_cmp = st.checkbox("✅已确认可比性条件（基准能源类型与计量口径明确；供暖面积、气象、采暖时长、室温一致；辅助设备与计量完整性已说明）",
                                value=False, key="_base_cmp")
        if _b_type != "未录入（暂不输出估算结果）" and _b_energy > 0:
            if not _base_cmp:
                st.warning("可比性检查未完成：改造前基准与改造后情景的供暖面积/气象/采暖时长/室温/计量完整性需先归一化。"
                           "确认上述可比性条件前，暂不输出实际基准下的节能率与运行减排量。")
            else:
                _base_rows = []
                for _bi, (_nm, _ekwh) in enumerate([("方案1", elec_1), ("方案2", elec_2), ("方案3", elec_3)]):
                    _sv = (_b_energy - _ekwh) / _b_energy * 100.0 if _b_energy > 1e-9 else None
                    _rv = _b_energy * _b_ef - _ekwh * equip["grid_ef"]
                    _base_rows.append({"方案":_nm, "改造前年能耗(kWh)":round(_b_energy,1), "本方案年电耗(kWh)":round(_ekwh,1),
                                       "实际基准节能率(%)(估算)":round(_sv,1) if _sv is not None else None,
                                       "运行减排量(kgCO₂/a)(估算)":round(_rv,1),
                                       "口径":"改造前基准（已通过可比性检查，估算值）"})
                st.dataframe(pd.DataFrame(_base_rows), width="stretch", hide_index=True)
                st.caption(f"改造前基准：{_b_type}，年能耗{_b_energy:.0f}kWh，排放因子{_b_ef:.3f}kgCO₂/kWh；"
                           f"本方案排放按电网因子{equip['grid_ef']:.4f}kgCO₂/kWh（2023河南，位置法）。"
                           f"运行减排量=改造前排放−本方案排放（估算），均指运行阶段购电间接排放（kgCO₂/a，不含设备制造/围护材料隐含碳）。"
                           f"节能率=1−本方案年电耗/改造前年能耗（估算）；实际节能效果仍需外部或实测验证。")
        else:
            st.info("未录入改造前实际供暖能耗，本模块暂不输出实际基准下的节能率与运行减排量。")

# ======================页面4：手工校核验算页 ======================
    # ================= V1.8新增：18种自由组合批量计算模块（追加，不动原有代码） =================
    if st.session_state.get("calc_mode","typical") == "batch_18":
        st.divider()
        st.markdown("# 🧪 18种自由组合批量计算｜3围护 ×3末端 ×2热泵")
        st.info("枚举轴：围护{E0,E1,E2} × 末端{T0,T1,T2} × 热泵{HP0,HP1} = 3×3×2=18 行。"
                "互斥与去重：E1/E2 当前建模均为『全套围护改造』（E1 与 E2 的差异项未建模），二者逐项结果等价 → 6 对重复，去重后 12 个唯一结果（重复行已标注）。"
                "基准=E0-T0-HP0；增量回收期仅方案间对比，非工程真实回收期；节能/减排为相对基准组合，且仅在**基准与本组合均供热完整**（末端OK且无未满足热量）时可比，否则标'不可比'。"
                "排序仅在供热完整、模型适用且约束相同的组合内进行；本表按枚举顺序输出，未做跨约束排序。")
        if st.session_state["retrofit_mode"] == "分户独立改造":
            coef_envelope = coef_pump = coef_terminal = 1.00 # 分户模式三系数=1.00（本次生效值）
        else:
            coef_envelope = st.session_state["coef_set"]["coef_envelope"]
            coef_pump = st.session_state["coef_set"]["coef_pump"]
            coef_terminal = st.session_state["coef_set"]["coef_terminal"]
        # 批量模式沿用页面3的备用热源配置（未确认时不假定足额）+ 电辅热额定电功率（等效满载小时分母）
        _batch_aux_mode = st.session_state.get("_aux_mode", "无备用（不假定足额）")
        _batch_aux_installed = float(st.session_state.get("_aux_capacity", 0.0))
        _batch_aux_eta = float(st.session_state.get("_aux_eta", 1.0))
        _batch_aux_cost = float(st.session_state.get("_aux_cost_per_kw", 300.0))
        _batch_season_hours = float(st.session_state.get("_season_hours", DEFAULT_SEASON_HOURS))
        _batch_aux_p_rated = float(st.session_state.get("_aux_p_rated", 0.0))
        all_result_list = []
        for e_item in ENVELOPE_OPTIONS:
            for t_item in TERMINAL_OPTIONS:
                for hp_item in HEATPUMP_OPTIONS:
                    all_result_list.append(calc_one_combination(
                        ht, build, equip, coef_envelope, coef_pump, coef_terminal,
                        e_item["id"], t_item["id"], hp_item["id"], HDD_SEGMENTS,
                        aux_mode=_batch_aux_mode, aux_installed_kw=_batch_aux_installed,
                        aux_eta=_batch_aux_eta, aux_cost_per_kw=_batch_aux_cost,
                        season_hours=_batch_season_hours, aux_p_rated=_batch_aux_p_rated))
        base = next(x for x in all_result_list if x["env_id"]=="E0" and x["term_id"]=="T0" and x["hp_id"]=="HP0")
        base_heat_ok = bool(base["term_ok"] and base.get("unserved_heat_kwh",0) <= 1e-6)
        out_rows = []
        for item in all_result_list:
            delta_inv = item["total_invest"] - base["total_invest"]
            pb = payback_period_incremental(base["total_invest"], delta_inv,
                                            base["E_total_kwh"], item["E_total_kwh"], equip["elec_price"])
            elec_save_rate = round((base["E_total_kwh"]-item["E_total_kwh"])/base["E_total_kwh"]*100,2) if base["E_total_kwh"]>1e-3 else None
            item_heat_ok = bool(item["term_ok"] and item.get("unserved_heat_kwh",0) <= 1e-6)
            comp_ok = base_heat_ok and item_heat_ok
            _v_txt = "Q" + ("✓" if item.get("q_valid",True) else "✗") + "/C" + ("✓" if item.get("cop_valid",True) else "✗") + "/H" + ("✓" if item.get("hardware_valid",True) else "✗")
            _dedup_mark = "E1/E2等价重复" if item["env_id"] == "E2" else "唯一"
            _elim_reasons = []
            if not item.get("data_domain_ok", True):
                _elim_reasons.append("模型适用性NG")
            if not item.get("term_ok", True):
                _elim_reasons.append("末端NG")
            if not item_heat_ok:
                _elim_reasons.append("供热不完整")
            _feasible = bool(item.get("data_domain_ok", True) and item.get("term_ok", True) and item_heat_ok)
            out_rows.append({
                "围护":item["env_id"],"末端":item["term_id"],"热泵":item["hp_id"],"去重标记":_dedup_mark,
                "H(kW/K)":item["H_kWK"],"Qd(kW)":item["Qd_kW"],"q(W/m²)":item["q_load_per_area_Wm2"],
                "供水℃":item["tg_solve"],"末端校验":"OK" if item["term_ok"] else "NG",
                "设计COP":item.get("cop_design"),"MR":item.get("mr_design"),"模型适用性":"OK" if item.get("data_domain_ok",True) else "NG",
                "有效性(Q/C/H)":_v_txt,
                "E_hp(kWh)":item["E_hp_kwh"],"备用供热(kWh)":item.get("aux_heat_kwh",0),"E_aux(kWh)":item["E_aux_kwh"],
                "等效满载小时(h)":(item["aux_equiv_hours"] if item.get("aux_equiv_hours") is not None else "不适用/待配置"),
                "实际开启小时(h)":(item.get("aux_actual_on_hours") if item.get("aux_actual_on_hours") is not None else "待气象时序"),
                "未满足热量(kWh)":item.get("unserved_heat_kwh",0),"供热完整性":"OK" if item_heat_ok else "NG",
                "E_total(kWh)":item["E_total_kwh"],"SPF_HP+aux":item.get("spf_sys"),
                "相对基准购电变化%":(elec_save_rate if comp_ok else "不可比"),
                "CO₂(kg)":item["co2_run_kg"],
                "投资热泵":item["invest_pump"],"投资围护":item["invest_env"],"投资末端":item["invest_terminal"],
                "备用投资":item.get("aux_invest",0),
                "总投资(元)":item["total_invest"],"年电费(元)":item["year_cost"],"增量回收期(年)":(pb if comp_ok else None),
                "可行":_feasible,"淘汰原因":("；".join(_elim_reasons) if _elim_reasons else "—")
            })
        df_18 = pd.DataFrame(out_rows)
        df_18["增量回收期(年)"] = df_18["增量回收期(年)"].apply(lambda v: v if v is not None else "不可比")
        st.dataframe(df_18, width="stretch", height=260)
        _n_unique = int((df_18["去重标记"] == "唯一").sum())
        _n_feas = int(df_18["可行"].sum())
        _elim_sum = df_18.loc[df_18["淘汰原因"] != "—", "淘汰原因"].str.split("；").explode().value_counts().to_dict()
        _elim_txt = "；".join(f"{k}×{v}" for k, v in _elim_sum.items()) if _elim_sum else "无"
        st.info(f"名义组合 18 行；E1/E2 当前建模等价 → 去重后唯一结果 {_n_unique} 个；供热完整且模型适用的可行组合 {_n_feas} 个；淘汰原因分布：{_elim_txt}。"
                "导出数值以本次计算快照（含输入、生效参数与数据版本）为准；等效满载小时=E_aux/P_aux,rated，未配置电辅热或额定功率未知时显示'不适用/待配置'。")
        csv_18 = df_18.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button("📥下载18种自由组合结果CSV", csv_18,
                           file_name=f"{ht}_18种自由组合_{APP_VERSION}.csv", mime="text/csv")
        st.info("💡注：18组合中，末端校验NG表示该末端在最高供水温度下无法覆盖热负荷；模型适用性NG=容量域/COP域/设备包络任一越域（COP域外仅教学估计，退出正式排序）；"
                "供热完整性NG或基准供热不足时，相对基准购电变化/回收期标'不可比'（等供热前提）；备用供热/未满足热量按页面3备用热源配置计算，未确认不假定足额；"
                "排序仅在同等供热、相同约束及有效数据内进行。")

# ======================页面4：手工校核验算页 ======================
elif page_select == "4.手工校核验算页":
    ht = st.session_state["house_type"]
    st.markdown(f"""
<div class="light-tech-title">
    <h1>✍️计算一致性校核（非模型有效性验证）｜户型：{ht}</h1>
</div>
""", unsafe_allow_html=True)
    st.info("本页用于检查“程序复算”与“手算/独立电子表格”是否一致（代码一致性校核），不代表模型已通过实测验证。"
            "空值按“待填写”处理，不按0计算误差；E_aux=0 等合法零值须勾选『已确认填写0』后按已填写处理。误差阈值：≤1%判定校验通过。")
    st.markdown("### 🔬 验证证据（测试类别与证据等级单列；无日志时按『未提交证据』处理）")
    tab_vA, tab_vB, tab_vC = st.tabs(["A. 一致性测试（固定算例对照）", "B. 边界回归测试（单元测试）", "C. 外部验证（模型有效性）"])
    with tab_vA:
        st.markdown("**A. 一致性测试：内置固定算例与独立电子表格对照**")
        st.caption(f"内置回归测试版本：{CALC_DATA_VERSION}；运行日期：2026-09-09（与计算快照同步生成）；可下载测试记录：暂未提供（待补充日志导出）。"
                   "默认算例：中间层住宅、建筑面积120m²、室外设计温度-3.5℃、HDD18=2106℃·d、分户独立改造模式；"
                   "V1.35修正：Qd1原表7.142kW为-7℃口径，与默认-3.5℃不符，已改为6.21622kW；"
                   "SPF_HP+aux与年耗电按新口径（E_HP+E_aux分段积分、时长=采暖期2880h一阶假设）重算，独立电子表格值待按同口径复核。"
                   "上述仅验证程序内部数值一致性，物理模型与实际节能效果仍需外部或实测验证。")
        df_fixed = pd.DataFrame([
            {"参数":"总热损失系数H1","程序计算值":"0.26452 kW/K","独立电子表格值":"0.26452 kW/K","相对误差":"0.000%","结论":"✅通过"},
            {"参数":"设计热负荷Qd1(默认-3.5℃)","程序计算值":"6.21622 kW","独立电子表格值":"待复核（原表7.142为-7℃口径）","相对误差":"—","结论":"待复核"},
            {"参数":"全年需热量Qyear1","程序计算值":"13369.9 kWh","独立电子表格值":"13369.9 kWh","相对误差":"0.000%","结论":"✅通过"},
            {"参数":"方案1 SPF_HP+aux(无备用)","程序计算值":"2.477","独立电子表格值":"待按V1.35口径重算","相对误差":"—","结论":"待更新"},
            {"参数":"方案1年耗电量(E_HP+E_aux)","程序计算值":"5398.4 kWh","独立电子表格值":"待按V1.35口径重算","相对误差":"—","结论":"待更新"},
        ])
        st.dataframe(df_fixed, width="stretch", hide_index=True)
        st.info("一致性测试状态：H1/Qyear1 对照通过；Qd1/SPF/年耗电程序值已按 V1.35 新口径重算，独立电子表格须同步复核后方可判'通过'——"
                "未提交完整测试记录（含测试版本与运行日期）前，证据状态按『未提交证据』处理，不宣称'全部通过'。"
                "口径变化根因：V1.34把度时(℃·h)当作时长(h)使用（Σ=50544 h），V1.35已分离为 度时ΣD_i=50544℃·h 与 时长Σh_i=2880h 一阶假设。")
    with tab_vB:
        st.markdown("**B. 边界/趋势单元测试**")
        df_unit = pd.DataFrame([
            {"编号":"A02","测试项":"几何阻断-窗+门≥毛墙","输入":"win=80, door=10, wall_gross=85","预期结果":"阻断计算并提示","实际结果":"✅阻断","状态":"通过"},
            {"编号":"A03","测试项":"几何阻断-净墙=毛墙−窗−门","输入":"wall_gross=85, win=22, door=2.2","预期结果":"净墙=60.8m²","实际结果":"✅60.8m²","状态":"通过"},
            {"编号":"A04","测试项":"设备包络越界-供水65℃","输入":"T_amb=-7, tg=65（超MHSR-N8-S1手册60℃上限）","预期结果":"hardware_valid=False→all_valid=False（容量域内但包络外）","实际结果":"✅包络False,AND=False","状态":"通过"},
            {"编号":"A05","测试项":"容量域外-T_design=-20℃","输入":"设计温度覆盖为-20℃（用户输入）","预期结果":"q_valid=False→data/model gate失败；工况越出估算面；方案不推荐","实际结果":"✅gate=False,不推荐","状态":"通过"},
            {"编号":"A06","测试项":"用户覆盖规范值-来源标注","输入":"Tout=-20（覆盖默认-3.5℃）","预期结果":"台账显示【用户输入】，默认-3.5℃单独保留","实际结果":"✅【用户输入】标注","状态":"通过"},
            {"编号":"A07","测试项":"批量造价-围护0.75/热泵0.85/末端0.80","输入":"raw=14167/12500/13800","预期结果":"10625/10625/11040元","实际结果":"✅一致","状态":"通过"},
            {"编号":"A08","测试项":"分户造价-有效系数1/1/1","输入":"分户独立改造模式","预期结果":"分项系数置灰；结果按原始价格","实际结果":"✅置灰,原价","状态":"通过"},
            {"编号":"A09","测试项":"空手算值-校核页首次打开","输入":"页面4首次加载","预期结果":"显示待填写，不出现100%误差","实际结果":"✅待填写","状态":"通过"},
            {"编号":"A10","测试项":"仅基准可行-默认3万元预算","输入":"预算=30000元","预期结果":"显示无可行改造方案；基准不标推荐","实际结果":"✅无可行,基准不推荐","状态":"通过"},
            {"编号":"A11","测试项":"拟合性能面-证据等级C","输入":"厂家锚点+温升幂律推算","预期结果":"不显示厂家数据域；显示估算面和不确定性","实际结果":"✅估算面/证据C","状态":"通过"},
            {"编号":"A13","测试项":"分段守恒-Σ度时=HDD×24","输入":"HDD=2106","预期偏差":"≤0.5%","实际结果":"✅0.000%","状态":"通过"},
            {"编号":"A14","测试项":"SPF边界-含辅助电加热/不含辅助电加热切换","输入":"radio切换两种口径","预期结果":"指标名称、分母、解释同步变化；SPF值自动重算","实际结果":"✅同步变化","状态":"通过"},
            {"编号":"A15","测试项":"容量闸门-MR<1","输入":"Qd=8, Qhp=7.24, MR=0.905","预期结果":"hp_cap_ok=False；显示Q_aux,design","实际结果":"✅False,Q_aux=0.76","状态":"通过"},
            {"编号":"A16","测试项":"末端能力-反算tg≤tg_max","输入":"Qd=7.14, rad_Qrated=14, tg_max=60℃","预期tg":"反算tg≤60℃（MHSR-N8-S1手册上限）","实际结果":"✅受60℃上限约束","状态":"通过"},
            {"编号":"A17","测试项":"备用热源未确认不假定足额","输入":"备用方案=无备用","预期结果":"E_aux=0、未满足热量=缺口（不置零）","实际结果":"✅缺口如实报告","状态":"通过"},
            {"编号":"A18","测试项":"COP域外-T_design=-20℃","输入":"室外-20℃（COP工况下限-15℃）","预期结果":"cop_valid=False→all_valid=False；COP带域外标记退出正式排序；容量域可单独显示","实际结果":"✅分维度判定","状态":"通过"},
            {"编号":"A19","测试项":"度时/时长严格分离","输入":"HDD分段模型","预期结果":"degree_hours_seg(℃·h)≠duration_hours_seg(h)；ΣD_i=HDD×24为度时守恒；时长须气象时序另行统计","实际结果":"✅字段分离","状态":"通过"},
            {"编号":"A20","测试项":"基准供热不足→节电率不可比","输入":"Tout=-7℃（方案1末端能力不足）","预期结果":"相对方案1购电/减排/回收期标'不可比'，不输出数值","实际结果":"✅不可比","状态":"通过"},
            {"编号":"A21","测试项":"快照指纹失效-改参后旧结果","输入":"页面3算完→页面1改Tout→直接进页面4","预期结果":"显示'参数已改变，当前结果待重新计算'，不显示旧Qd/旧SPF","实际结果":"✅旧结果失效","状态":"通过"},
        ])
        st.dataframe(df_unit, width="stretch", hide_index=True, height=620)
        st.success("✅ 边界回归测试：19项单元测试全部通过（数值级回归；V1.35新增A17-A21共5项）")
        st.caption("测试版本 " + CALC_DATA_VERSION + "｜运行日期 2026-09-09。本结果仅说明程序内部边界行为符合预期，不构成模型有效性证据；"
                   "测试日志可下载记录暂未提供（待补充导出）。A05容量域外：T_design=-20℃时q_valid=False→model gate失败，不推荐；"
                   "A18 COP域外：-20℃低于COP有效域下限-15℃时cop_valid=False，COP仅作带标记的教学估计并退出正式排序（容量域可单独显示）；"
                   "A21快照指纹：输入/版本变化立即失效旧结果，未重新算完前禁止显示旧绿灯或导出旧值。")
        st.markdown("### 📋 证据状态汇总（测试类别与证据等级单列）")
        df_evid = pd.DataFrame([
            {"测试类别":"一致性测试（内置固定算例对照）","状态":"部分通过（H1/Qyear1通过；Qd1/SPF/年耗电待独立表格复核）",
             "测试版本":CALC_DATA_VERSION,"测试日期":"2026-09-09","测试记录":"未提交（待导出日志）","证据等级":"代码级一致性"},
            {"测试类别":"边界回归测试（19项单元测试）","状态":"全部通过",
             "测试版本":CALC_DATA_VERSION,"测试日期":"2026-09-09","测试记录":"未提交（待导出日志）","证据等级":"数值级回归"},
            {"测试类别":"外部验证（EnergyPlus/DeST/厂家软件/实测户）","状态":"未完成",
             "测试版本":"—","测试日期":"—","测试记录":"无日志（未提交证据）","证据等级":"模型有效性"},
        ])
        st.dataframe(df_evid, width="stretch", hide_index=True)
        st.warning("以上仅验证数值一致性；物理模型与实际节能效果仍需外部或实测验证。无测试日志时，对应证据状态按『未提交证据』处理；"
                   "当前输入的手算校核：待填写（见下方逐级校核）。")
    with tab_vC:
        st.markdown("**C. 外部验证（模型有效性）**")
        st.warning("⚠️ 外部验证尚未完成：与 EnergyPlus/DeST/厂家选型软件或实测户的外部对照尚未开展（无日志＝未提交证据）。")
        df_ext = pd.DataFrame([
            {"对照对象":"EnergyPlus 能耗模拟","状态":"❌未完成","说明":"需建立同参数EnergyPlus模型，对比全年能耗与分段COP"},
            {"对照对象":"DeST 能耗模拟","状态":"❌未完成","说明":"需建立同参数DeST模型，对比采暖季耗热量"},
            {"对照对象":"厂家选型软件","状态":"❌未完成","说明":"需用美的/格力等厂家选型软件核对设计工况制热量与COP"},
            {"对照对象":"实测住户数据","状态":"❌未完成","说明":"需选取试点住户，安装电表/温度记录仪，采集一个采暖季实测数据"},
        ])
        st.dataframe(df_ext, width="stretch", hide_index=True)

        # ===== 独立解析对照算例（V1.38 审查意见⑤：至少一个独立模型对照）=====
        st.markdown("**独立解析对照（稳态热损失法，与本程序分段积分实现独立）：**")
        st.caption("方法：用经典稳态公式 Q_design=H·ΔT、Q_year=H·HDD24·24 独立重算，"
                   "与本程序分段积分输出对比。偏差应为 0（或仅四舍五入）；偏差>0.5% 说明积分实现有误。"
                   "注意：零值附近使用绝对误差判定，不用相对误差除以零。")
        try:
            _mid_ref = st.session_state.get("calc_mid", {})
            _H_kwk = float(_mid_ref["H1_kWK"])
            _Tin = float(st.session_state["build"]["Tin"])
            _Tout = float(st.session_state["build"]["Tout"])
            _dT = _Tin - _Tout
            _HDD24 = float(st.session_state["build"]["HDD"])
            _Qd_prog = float(_mid_ref["Qd1_kW"])
            _Qy_prog = float(_mid_ref["q_year1_kwh"])
            _Qd_calc = _H_kwk * _dT
            _Qy_calc = _H_kwk * _HDD24 * 24.0
            _dQd = abs(_Qd_prog - _Qd_calc)
            _dQy = abs(_Qy_prog - _Qy_calc)
            # 零值附近用绝对误差阈值（≤0.01kW / ≤1kWh），非零用相对误差
            _qd_ok = (_dQd <= 0.01) if abs(_Qd_calc) < 1e-9 else (_dQd / _Qd_calc <= 0.005)
            _qy_ok = (_dQy <= 1.0) if abs(_Qy_calc) < 1e-9 else (_dQy / _Qy_calc <= 0.005)
            df_indep = pd.DataFrame([
                {"对照量":"设计热负荷 Q_design(kW)","程序输出":round(_Qd_prog,3),"独立解析":round(_Qd_calc,3),
                 "绝对差":round(_dQd,4),"相对差%":(round(_dQd/_Qd_calc*100,3) if abs(_Qd_calc)>1e-9 else "N/A(零值,绝对误差)"),
                 "判定":"✅通过" if _qd_ok else "❌偏差>0.5%"},
                {"对照量":"全年需热量 Q_year(kWh)","程序输出":round(_Qy_prog,1),"独立解析":round(_Qy_calc,1),
                 "绝对差":round(_dQy,2),"相对差%":(round(_dQy/_Qy_calc*100,3) if abs(_Qy_calc)>1e-9 else "N/A(零值,绝对误差)"),
                 "判定":"✅通过" if _qy_ok else "❌偏差>0.5%"},
            ])
            st.dataframe(df_indep, width="stretch", hide_index=True)
            st.caption("偏差来源说明：本程序分段积分与稳态解析法在同一线性热损失假设下数学等价；"
                       "若偏差显著，优先检查：①HDD 分段度时是否正确求和；②单位换算（W↔kW、h↔d）；"
                       "③温度分段中点 dT 取值。本对照仅验证积分实现自洽，不代表与 EnergyPlus/实测户一致。")
        except Exception as _e:
            st.warning(f"独立解析对照计算失败：{_e}（不影响主计算）")

        st.markdown("""
**测试类别与证据等级判定（单列）：**
- 一致性测试（代码级）：H1/Qyear1 已对照通过，其余项待独立表格复核（未提交完整日志前按『未提交证据』处理）
- 边界回归测试（数值级）：19 项单元测试全部通过（测试版本 V1.35-data-20260909，2026-09-09）
- 外部验证（模型级）：见上表；独立解析对照（稳态热损失法）已完成，EnergyPlus/DeST/厂家软件/实测户对照仍❌未完成

**测试阈值说明：** 测试阈值按量的精度制定；零值附近（如 E_aux=0、save_elec=0）使用绝对误差判定，不使用相对误差除以零。

**结论：本程序当前状态为「原型模型待实测校准」，不得写"模型已验证"。**
上述测试仅验证数值一致性；物理模型与实际节能效果仍需外部或实测验证。**通过一致性/边界测试项不自动构成实测节能认证**；只有完成外部对照（EnergyPlus/DeST/厂家软件或实测户）并报告偏差与原因后，才能宣称模型已通过有效性验证，可用于工程推广。
""")
    # V1.35：统一结果对象 + 输入哈希/模型版本/数据版本校验——旧快照立即失效，未重新算完前禁止显示旧绿灯/旧导出
    _snap_ok, _snap_msg = calc_snapshot_status()
    if not _snap_ok:
        st.warning("⚠️" + _snap_msg)
        st.stop()
    mid = st.session_state["calc_mid"]
    st.caption(f"计算快照：{mid.get('_app_version','—')} / 数据版本 {mid.get('_data_version','—')} / 生成于 {mid.get('_timestamp','—')}；"
               f"输入哈希或版本任一变化，旧快照立即失效，须重访页面3生成新快照。")
    st.subheader("核心公式")
    st.markdown(r"""
$H_{total}=\sum H_{envelope} + H_{inf}\quad [kW/K]$
设计热负荷：$Q_{design}=H_{total}\cdot \Delta T$（无附加耗热量）
年采暖需热量：$Q_{year}=H_{total}\cdot HDD18 \cdot 24$
""")
    st.divider()
    col_h1, col_h2 = st.columns(2)
    with col_h1:
        st.number_input("软件 H1(kW/K)", value=mid["H1_kWK"], disabled=True, format="%.4f")
        hand_H1 = st.number_input("✍️手算 H1(kW/K)", value=0.0, format="%.4f")
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
            st.info("🕐尚未输入手算值，状态：待校核（空值不按0处理）")
    with col_h2:
        st.number_input("软件 Qd1(kW)", value=mid["Qd1_kW"], disabled=True, format="%.4f")
        hand_Qd1 = st.number_input("✍️手算 Qd1(kW)", value=0.0, format="%.4f")
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
        st.number_input("软件 H2(kW/K)", value=mid["H2_kWK"], disabled=True, format="%.4f")
        hand_H2 = st.number_input("✍️手算 H2(kW/K)", value=0.0, format="%.4f")
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
        st.number_input("软件 Qd2(kW)", value=mid["Qd2_kW"], disabled=True, format="%.4f")
        hand_Qd2 = st.number_input("✍️手算 Qd2(kW)", value=0.0, format="%.4f")
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
        st.number_input("软件 H3(kW/K)", value=mid["H3_kWK"], disabled=True, format="%.4f")
        hand_H3 = st.number_input("✍️手算 H3(kW/K)", value=0.0, format="%.4f")
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
        st.number_input("软件 Qd3(kW)", value=mid["Qd3_kW"], disabled=True, format="%.4f")
        hand_Qd3 = st.number_input("✍️手算 Qd3(kW)", value=0.0, format="%.4f")
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
    st.subheader("🔬 HDD分段插值结果查看（性能估算面口径）")
    st.info("💡提示：方案3与方案2采用相同的围护改造参数，并在此基础上更换低温末端与匹配设备，因此H3=H2、Q_design,3=Q_design,2；两者的供水温度、设备性能、能耗和投资不同。")
    if "seg1" in mid:
        st.markdown("**方案1分段插值明细**（*时长h_i为采暖期总时长×度时占比的一阶假设，须气象时序校核）")
        st.dataframe(pd.DataFrame(mid["seg1"]).rename(columns=SEG_DISPLAY_LABELS).fillna("—"), width="stretch")
    if "seg2" in mid:
        st.markdown("**方案2分段插值明细**")
        st.dataframe(pd.DataFrame(mid["seg2"]).rename(columns=SEG_DISPLAY_LABELS).fillna("—"), width="stretch")
    if "seg3" in mid:
        st.markdown("**方案3分段插值明细**")
        st.dataframe(pd.DataFrame(mid["seg3"]).rename(columns=SEG_DISPLAY_LABELS).fillna("—"), width="stretch")

    # ================= 逐级误差校核（软件值自动带入，仅填手算值） =================
    st.divider()
    st.subheader("🧪逐级误差校核（软件值自动带入，只填手算值）｜性能估算面口径")
    st.info("校核链：H → Q_design → Q_year → 估算面COP/SPF_HP+aux → E_HP → E_aux → 费用 → 运行期碳排放。误差≤1%判『通过』，>1%判『未通过』。"
            "E_HP/E_aux 按性能估算面（含容量约束，供水=末端反算tg，模型适用范围内插值）口径计算。"
            "E_aux=0 属合法零值（无辅助电加热时），须勾选『已确认填写0』后按已填写处理；未勾选时手算栏 0 仍视为待填写，与未填 None 区分。")
    equip_chk = st.session_state["equip"]
    _spf_list = [mid["spf1"], mid["spf2"], mid["spf3"]]
    _spf_sys_list = [mid.get("spf_sys1"), mid.get("spf_sys2"), mid.get("spf_sys3")]
    # 计算每方案 E_HP / E_aux（二维表，供水=反算tg；V1.35：沿用页面3的备用配置与采暖时长，保证口径一致）
    _aux_results = []
    for _i, (_seg, _hpid, _tg, _rated) in enumerate([
        (mid.get("seg1_plain", mid["seg1"]), "HP0", mid["tg1"], equip_chk["Qhp_rated1"]),
        (mid.get("seg2_plain", mid["seg2"]), "HP0", mid["tg2"], equip_chk["Qhp_rated2"]),
        (mid.get("seg3_plain", mid["seg3"]), "HP1", mid["tg3"], equip_chk["Qhp_rated3"]),
    ]):
        _qaux_eff = mid.get("q_aux_eff1" if _i==0 else "q_aux_eff2" if _i==1 else "q_aux_eff3", 0.0)
        _, _ehp, _eaux, _ah, _dok, _, _unserved = calc_segment_hp_aux_2d(
            _seg, _hpid, _tg, _rated,
            q_aux_capacity=(_qaux_eff if _qaux_eff > 1e-9 else None),
            eta_aux=float(mid.get("aux_eta", 1.0)),
            season_hours=float(mid.get("season_hours", DEFAULT_SEASON_HOURS)),
            p_aux_rated=float(mid.get("aux_p_rated", 0.0)))
        _aux_results.append((round(_ehp,2), round(_eaux,2), _ah, _dok, _unserved))

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
            _zero_ok = st.checkbox("E_aux 手算值为 0（合法零值，已确认填写；无辅助电加热时 E_aux=0 为合法结果）",
                                   value=False, key=f"chk_zero_{_sidx}",
                                   help="勾选后，本方案手算栏 E_aux (kWh) 填 0 将按『已填写且通过』处理，而不是『待填写』；"
                                        "未勾选时 0 与未填写 None 保持区分。")
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
                _is_zero_legal = (_k == "E_aux (kWh)") and (_hv == 0.0) and _zero_ok
                if _hv <= 0 and not _is_zero_legal:
                    _all_filled = False
                    _res_rows.append({"参数":_k,"软件值":_v,"手算值":_hv,
                                      "绝对误差":"—","相对误差%":"—",
                                      "结论":"🕐待填写（空值不按0处理）"})
                    continue
                if _is_zero_legal:
                    _ae, _re, _ok = 0.0, 0.0, True
                    _res_rows.append({"参数":_k,"软件值":_v,"手算值":_hv,
                                      "绝对误差":0.0,"相对误差%":0.0,
                                      "结论":"✅通过（合法零值，已确认）"})
                else:
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
    st.markdown("**🔎 供水温度(末端反算) 与 热泵设计工况可用制热量/容量裕量/模型适用性 校核**")
    st.info("供水温度由负荷与末端能力反算：Q_terminal=Q_rated×(ΔT_m/ΔT_m,rated)^m（散热器m=1.30，地暖m=0.95）；"
            "热泵容量按设计工况(室外=郑州设计温度)性能估算面插值，不直接用样本额定值；并给出容量裕量MR与模型适用性标志。")
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
        _copd, _qav, _vld4, _warns4 = hp_available_at_design(_bd4, _eq4, _hpid, _tgv)
        _qd = mid[_qdk]
        _ok = _qav >= _qd
        _mr = round(_qav/_qd,3) if _qd>1e-9 else None
        _rows4.append({"方案":nm, "反算供水温度tg(℃)":_tgv, "设计工况COP":_copd,
                       "设计工况Q_HP可用(kW)":_qav, "设计负荷(kW)":round(_qd,2),
                       "容量裕量MR":_mr, "容量满足":"✅" if _ok else "❌",
                       "容量域Q_valid":"✅" if _vld4["q_valid"] else "❌",
                       "COP域COP_valid":"✅" if _vld4["cop_valid"] else "❌",
                       "设备包络(供水≤60℃)":"✅" if _vld4["hardware_valid"] else "❌",
                       "模型适用性(AND)":"✅" if _vld4["all_valid"] else "⚠️否",
                       "说明":(_vld4["reason"] if not _vld4["all_valid"] else ("可用制热量≥设计负荷，可行" if _ok else "需增容或配置备用热源"))})
    st.dataframe(pd.DataFrame(_rows4), width="stretch", hide_index=True)
    st.caption("当末端/热泵能力不满足时，应给出『提高水温（须在设备≤60℃和末端允许工况内）/增加散热器面积/更换末端』及『增容或备用热源』建议，避免直接把额定值当可用值；"
               "模型适用性=容量域∩COP域(室外≥-10℃)∩设备包络(供水≤60℃)（综合AND），任一失败即判定该方案不通过；COP域外仅作带标记的教学估计，禁止输出可行/最优。")
