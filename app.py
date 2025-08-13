# app.py
import math
import streamlit as st
from systems import SYSTEMS
from translations import TRANSLATIONS, LANG_CHOICES, get_text

# ---- Assumptions ----
DEFAULT_YIELD_PER_KWP_YR = 1050
DEFAULT_RTE = 0.92
DEFAULT_DOD = 0.90
DEFAULT_DEGRADATION_RESERVE = 0.10

LOAD_PROFILES = {
    "p_balanced": 0.40,
    "p_workday": 0.30,
    "p_home": 0.55,
    "p_evening": 0.25,
    "p_heatpump": 0.50,
    "p_custom": None,
}

# ---- Helpers ----
def orientation_factor(orientation: str) -> float:
    o = orientation.lower()
    if o in ["south", "s"]:
        return 1.00
    if o in ["southeast", "se", "south-east"]:
        return 0.97
    if o in ["southwest", "sw", "south-west"]:
        return 0.97
    if o in ["east", "e"]:
        return 0.90
    if o in ["west", "w"]:
        return 0.90
    if o in ["north", "n"]:
        return 0.60
    return 1.00

def opposite_orientation(orientation: str) -> str:
    pairs = {
        "south": "north",
        "southeast": "northwest",
        "southwest": "northeast",
        "east": "west",
        "west": "east",
        "north": "south",
        "northeast": "southwest",
        "northwest": "southeast",
    }
    return pairs.get(orientation.lower(), "north")

def tilt_factor(tilt_deg: float) -> float:
    if tilt_deg <= 15: return 0.95
    if 16 <= tilt_deg <= 45: return 1.00
    if 46 <= tilt_deg <= 60: return 0.90
    return 0.80

def estimate_yearly_pv_yield_kwp(region_yield, orient_factor, tilt_fac):
    return region_yield * orient_factor * tilt_fac

def pick_inverter(dc_kw: float, ac_sizes: list, models_map: dict, max_ratio: float) -> dict:
    choices = []
    for ac in ac_sizes:
        ratio = dc_kw / ac if ac > 0 else float("inf")
        ok = ratio <= max_ratio
        score = abs(1.25 - ratio)
        choices.append((ac, ratio, ok, score))
    valid = [c for c in choices if c[2]]
    best = min(valid, key=lambda x: (x[3], x[0])) if valid else max(choices, key=lambda x: x[0])
    ac_kw = best[0]
    return {"ac_kw": ac_kw, "model": models_map.get(ac_kw, f"{ac_kw:.1f} kW"), "dc_ac_ratio": best[1], "within_cap": best[2]}

def estimate_battery_need_components(annual_kwh: float, pv_kw: float, specific_yield_kwh_per_kwp_yr: float,
                                     day_fraction: float, profile_flatten: float, backup_kw: float, backup_hours: float):
    daily_load = annual_kwh / 365.0
    daily_pv = (pv_kw * specific_yield_kwh_per_kwp_yr) / 365.0
    day_load = daily_load * day_fraction
    night_load = daily_load - day_load
    surplus_day = max(0.0, daily_pv - day_load) * profile_flatten
    shiftable = min(surplus_day, night_load)
    backup_energy = max(0.0, backup_kw) * max(0.0, backup_hours)
    return {
        "daily_load": daily_load, "daily_pv": daily_pv,
        "day_load": day_load, "night_load": night_load,
        "surplus_day": surplus_day, "shiftable": shiftable,
        "backup_energy": backup_energy,
    }

def apply_system_factors(usable_self_kwh: float, usable_backup_kwh: float, rte: float, dod: float, degradation_reserve: float):
    usable_needed = usable_self_kwh + usable_backup_kwh
    nominal_needed = 0.0 if usable_needed <= 0 else (usable_needed / (dod * rte)) * (1.0 + degradation_reserve)
    return usable_needed, nominal_needed

def pick_battery_model(usable_kwh_needed: float, options: list, labels: list) -> tuple:
    if usable_kwh_needed <= 0 or not options: return 0.0, ""
    idx = min(range(len(options)), key=lambda i: abs(options[i] - usable_kwh_needed))
    return options[idx], labels[idx] if idx < len(labels) else f"{options[idx]:.1f} kWh"

# ---- App ----
st.set_page_config(page_title="Sungrow Battery Sizer", layout="centered")

# Language selector
lang_codes = [c for c, _ in LANG_CHOICES]
lang_names = [n for _, n in LANG_CHOICES]
default_lang = st.session_state.get("lang", "en")
lang_index = lang_codes.index(default_lang) if default_lang in lang_codes else 0
lang_name = st.selectbox("🌐 Language", lang_names, index=lang_index)
lang = lang_codes[lang_names.index(lang_name)]
st.session_state["lang"] = lang
T = lambda key: get_text(lang, key)

st.title(T("title"))
st.caption(T("subtitle"))

system_key = st.selectbox(T("system_type"), list(SYSTEMS.keys()), index=0)
SYS = SYSTEMS[system_key]

with st.form("inputs"):
    st.subheader(T("pv_consumption"))
    colA, colB = st.columns(2)
    total_modules = colA.number_input(T("modules_installed"), min_value=1, max_value=300, value=16, step=1)
    module_wp = colB.number_input(T("module_wattage"), min_value=250, max_value=700, value=430, step=5)
    annual_kwh = st.number_input(T("annual_consumption"), min_value=500, max_value=50000, value=5000, step=100)

    st.markdown(f"**{T('roof_layout')}**")
    layout_opts = ["all_one_side", "split_two_sides"]
    layout_labels = [T(o) for o in layout_opts]
    layout_choice_label = st.radio(T("where_modules"), layout_labels, index=0)
    layout_choice = layout_opts[layout_labels.index(layout_choice_label)]

    if layout_choice == "all_one_side":
        col3, col4 = st.columns(2)
        orient_keys = ["south", "southeast", "southwest", "east", "west", "north"]
        orient_labels = [T(o) for o in orient_keys]
        orient_label = col3.selectbox(T("orientation"), options=orient_labels, index=0)
        orientation_single = orient_keys[orient_labels.index(orient_label)]
        tilt = col4.number_input(T("tilt"), min_value=0, max_value=90, value=30, step=1)
        orient_fac = orientation_factor(orientation_single)
        profile_flatten = 1.0
        orientation_text = T(orientation_single)
    else:
        col3, col4 = st.columns(2)
        orient_keys = ["east", "west", "south", "southeast", "southwest", "north"]
        orient_labels = [T(o) for o in orient_keys]
        orient_label_a = col3.selectbox(T("main_side_orientation"), options=orient_labels, index=0)
        orientation_side_a = orient_keys[orient_labels.index(orient_label_a)]
        tilt = col4.number_input(T("tilt"), min_value=0, max_value=90, value=30, step=1)
        orientation_side_b = opposite_orientation(orientation_side_a)
        orient_fac = 0.5 * (orientation_factor(orientation_side_a) + orientation_factor(orientation_side_b))
        profile_flatten = 0.90
        orientation_text = f"{T(orientation_side_a)} + {T(orientation_side_b)}"

    # Load profiles
    st.markdown(f"**{T('daily_load_profile')}**")
    profile_keys = list(LOAD_PROFILES.keys())
    profile_labels = [T(k) for k in profile_keys]
    profile_choice_label = st.selectbox(T("choose_profile"), profile_labels, index=0)
    profile_choice = profile_keys[profile_labels.index(profile_choice_label)]
    if LOAD_PROFILES[profile_choice] is None:
        day_fraction = st.slider(T("custom_day_pct"), min_value=0.2, max_value=0.8, value=0.40, step=0.05)
    else:
        day_fraction = LOAD_PROFILES[profile_choice]

    # Backup
    st.markdown(T("backup_optional"))
    col5, col6 = st.columns(2)
    backup_kw = col5.number_input(T("backup_kw"), min_value=0.0, max_value=30.0, value=0.0, step=0.5)
    backup_hours = col6.number_input(T("backup_h"), min_value=0.0, max_value=48.0, value=0.0, step=0.5)

    # Advanced
    with st.expander(T("advanced")):
        region_yield = st.number_input(T("specific_yield"), min_value=700, max_value=1500, value=DEFAULT_YIELD_PER_KWP_YR, step=10)
        rte = st.slider(T("rte"), min_value=0.80, max_value=0.98, value=DEFAULT_RTE, step=0.01)
        dod = st.slider(T("dod"), min_value=0.80, max_value=0.98, value=DEFAULT_DOD, step=0.01)
        degradation = st.slider(T("degradation"), min_value=0.05, max_value=0.20, value=DEFAULT_DEGRADATION_RESERVE, step=0.01)

    submitted = st.form_submit_button(T("calculate"))

if submitted:
    # PV & yield
    dc_kw = (total_modules * module_wp) / 1000.0
    tfac = tilt_factor(tilt)
    specific_yield = estimate_yearly_pv_yield_kwp(region_yield, orient_fac, tfac)

    # Inverter
    inv_choice = pick_inverter(dc_kw, SYS["inverter_ac_sizes"], SYS["models"], SYS["max_dc_ac_ratio"])

    # Battery components and sizing
    comp = estimate_battery_need_components(annual_kwh, dc_kw, specific_yield, day_fraction, profile_flatten, backup_kw, backup_hours)
    usable_needed, nominal_needed = apply_system_factors(comp["shiftable"], comp["backup_energy"], rte, dod, degradation)
    rec_kwh, rec_label = pick_battery_model(usable_needed, SYS["battery_options_kwh"], SYS["battery_labels"])

    # Inverter recommendation
    st.subheader(T("inv_reco"))
    colr1, colr2 = st.columns(2)
    with colr1:
        st.metric(T("pv_dc_size"), f"{dc_kw:.2f} kW")
    with colr2:
        st.metric(T("suggested_inverter"), inv_choice["model"], help=T("dcac_help").format(ratio=f"{inv_choice['dc_ac_ratio']:.2f}", cap=SYS["max_dc_ac_ratio"]))
    if not inv_choice["within_cap"]:
        st.warning(T("dcac_warn").format(cap=SYS['max_dc_ac_ratio']))
    if backup_kw > 0 and inv_choice["ac_kw"] < backup_kw:
        st.warning(T("backup_power_warn").format(need=backup_kw, ac=inv_choice['ac_kw']))

    # Battery rationale
    st.markdown("---")
    st.subheader(T("battery_inputs"))
    st.write(T("orientation_tilt_line").format(orientation=orientation_text, tilt=tilt))
    day_pct = int(round(day_fraction * 100))
    st.write(T("profile_line").format(profile=T(profile_choice), day=day_pct, night=100 - day_pct))
    st.write(T("daily_load_line").format(daily_load=comp['daily_load'], daily_pv=comp['daily_pv'], dc_kw=dc_kw, specific_yield=specific_yield))
    st.write(T("day_night_line").format(day_load=comp['day_load'], night_load=comp['night_load']))
    st.write(T("surplus_shift_line").format(surplus=comp['surplus_day'], shiftable=comp['shiftable']))
    if layout_choice == "split_two_sides":
        st.caption(T("two_side_caption"))
    if backup_kw > 0 and backup_hours > 0:
        st.write(T("backup_req_line").format(kw=backup_kw, h=backup_hours, energy=comp['backup_energy']))

    # Battery recommendation
    st.markdown("---")
    st.subheader(T("batt_reco"))
    colb1, colb2 = st.columns(2)
    with colb1:
        st.metric(T("usable_capacity"), "—" if rec_kwh == 0 else f"{rec_kwh:.1f} kWh")
    with colb2:
        st.metric(T("suggested_battery"), T("no_battery") if rec_kwh == 0 else rec_label)
    if rec_kwh > 0:
        st.caption(T("rounded_caption").format(battery_type=SYS['battery_type'], battery_step_display=SYS['battery_step_display']))
        st.write(T("breakdown_line").format(self=comp['shiftable'], backup=comp['backup_energy'], total=usable_needed))
    else:
        st.info(T("small_benefit"))

    # Notes
    st.markdown("---")
    st.subheader(T("sanity"))
    st.write(T("mppt_strings").format(mppts=SYS['mppts'], strings=SYS['max_strings_total']))
    st.write(T("string_current").format(current=SYS['max_string_current_a']))
    st.write(T("dcac_cap").format(cap=SYS['max_dc_ac_ratio']))
    st.write(T("quick_estimate"))
else:
    st.info(T("landing_hint"))
