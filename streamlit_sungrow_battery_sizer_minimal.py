
import math
import streamlit as st

# -----------------------------
# System definitions
# -----------------------------
SYSTEMS = {
    "Single-phase • SHRS": {
        "models": {3.6: "SH3.6RS", 4.6: "SH4.6RS", 5.0: "SH5.0RS", 6.0: "SH6.0RS"},
        "inverter_ac_sizes": [3.6, 4.6, 5.0, 6.0],
        "max_dc_ac_ratio": 1.5,
        "mppts": 2,
        "max_strings_total": 2,
        "max_string_current_a": 16,
        "battery_type": "SBS050",
        "battery_options_kwh": [5, 10, 15, 20],  # usable
        "battery_labels": ["SBS050 ×1", "SBS050 ×2", "SBS050 ×3", "SBS050 ×4"],
        "battery_step_display": "≈ 5 kWh blocks (1–4 units)"
    },
    "Three-phase • SHRT": {
        "models": {5.0: "SH5.0RT", 6.0: "SH6.0RT", 8.0: "SH8.0RT", 10.0: "SH10RT"},
        "inverter_ac_sizes": [5.0, 6.0, 8.0, 10.0],
        "max_dc_ac_ratio": 1.5,
        "mppts": 2,
        "max_strings_total": 3,
        "max_string_current_a": 13.5,
        "battery_type": "SBR",
        "battery_options_kwh": [9.6, 12.8, 16.0, 19.2, 22.4, 25.6],
        "battery_labels": ["SBR096", "SBR128", "SBR160", "SBR192", "SBR224", "SBR256"],
        "battery_step_display": "≈ 3.2 kWh steps (9.6–25.6 kWh)"
    },
    "Three-phase • SHT": {
        "models": {10.0: "SH10T", 12.0: "SH12T", 15.0: "SH15T", 20.0: "SH20T"},
        "inverter_ac_sizes": [10.0, 12.0, 15.0, 20.0],
        "max_dc_ac_ratio": 1.5,
        "mppts": 3,
        "max_strings_total": 5,
        "max_string_current_a": 16,
        "battery_type": "SBH",
        "battery_options_kwh": [10, 15, 20, 25, 30, 35, 40],
        "battery_labels": ["SBH100", "SBH150", "SBH200", "SBH250", "SBH300", "SBH350", "SBH400"],
        "battery_step_display": "≈ 5 kWh steps (10–40 kWh)"
    },
}

# Assumptions (defaults; adjustable)
DEFAULT_YIELD_PER_KWP_YR = 1050  # kWh/kWp/year baseline for Central Europe / CH
DEFAULT_RTE = 0.92
DEFAULT_DOD = 0.90
DEFAULT_DEGRADATION_RESERVE = 0.10

# Load profiles -> (label, day_fraction)
LOAD_PROFILES = {
    "Balanced household (40% day / 60% night)": 0.40,
    "Workday away (30% / 70%)": 0.30,
    "Home most of day (55% / 45%)": 0.55,
    "Evening peaky (25% / 75%)": 0.25,   # e.g., EV or cooking/lighting-heavy evenings
    "Heat pump or daytime loads (50% / 50%)": 0.50,
    "Custom…": None,
}


# -----------------------------
# Helper functions
# -----------------------------
def orientation_factor(orientation: str) -> float:
    o = orientation.lower()
    if o in ["south", "s"]:
        return 1.00
    if o in ["southeast", "se", "south-east", "south_east"]:
        return 0.97
    if o in ["southwest", "sw", "south-west", "south_west"]:
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
    if tilt_deg <= 15:
        return 0.95
    if 16 <= tilt_deg <= 45:
        return 1.00
    if 46 <= tilt_deg <= 60:
        return 0.90
    return 0.80  # >60°


def estimate_yearly_pv_yield_kwp(region_yield, orient_factor, tilt_fac):
    return region_yield * orient_factor * tilt_fac


def pick_inverter(dc_kw: float, ac_sizes: list, models_map: dict, max_ratio: float) -> dict:
    choices = []
    for ac in ac_sizes:
        ratio = dc_kw / ac if ac > 0 else float("inf")
        ok = ratio <= max_ratio
        score = abs(1.25 - ratio)  # aim near ~1.25
        choices.append((ac, ratio, ok, score))
    valid = [c for c in choices if c[2]]
    if valid:
        best = min(valid, key=lambda x: (x[3], x[0]))
    else:
        best = max(choices, key=lambda x: x[0])
    ac_kw = best[0]
    return {"ac_kw": ac_kw, "model": models_map.get(ac_kw, f"{ac_kw:.1f} kW"), "dc_ac_ratio": best[1], "within_cap": best[2]}


def estimate_battery_need_components(annual_kwh: float,
                                     pv_kw: float,
                                     specific_yield_kwh_per_kwp_yr: float,
                                     day_fraction: float,
                                     profile_flatten: float,
                                     backup_kw: float,
                                     backup_hours: float):
    """Return components before efficiency/reserves: shiftable (kWh), backup_energy (kWh)."""
    daily_load = annual_kwh / 365.0
    daily_pv = (pv_kw * specific_yield_kwh_per_kwp_yr) / 365.0

    day_load = daily_load * day_fraction
    night_load = daily_load - day_load
    surplus_day = max(0.0, daily_pv - day_load) * profile_flatten  # flatten profile reduces midday surplus
    shiftable = min(surplus_day, night_load)

    backup_energy = max(0.0, backup_kw) * max(0.0, backup_hours)
    return {
        "daily_load": daily_load,
        "daily_pv": daily_pv,
        "day_load": day_load,
        "night_load": night_load,
        "surplus_day": surplus_day,
        "shiftable": shiftable,
        "backup_energy": backup_energy,
    }


def apply_system_factors(usable_self_kwh: float,
                         usable_backup_kwh: float,
                         rte: float,
                         dod: float,
                         degradation_reserve: float):
    """Combine self-consumption + backup (additive), then apply DoD/RTE and degradation reserve."""
    usable_needed = usable_self_kwh + usable_backup_kwh
    if usable_needed <= 0:
        nominal_needed = 0.0
    else:
        nominal_needed = usable_needed / (dod * rte)
        nominal_needed *= (1.0 + degradation_reserve)
    return usable_needed, nominal_needed


def pick_battery_model(usable_kwh_needed: float, options: list, labels: list) -> tuple:
    if usable_kwh_needed <= 0 or not options:
        return 0.0, ""
    idx = min(range(len(options)), key=lambda i: abs(options[i] - usable_kwh_needed))
    return options[idx], labels[idx] if idx < len(labels) else f"{options[idx]:.1f} kWh"


# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Sungrow Battery Sizer (v3.3)", layout="centered")

st.title("🔋 Sungrow Battery Sizer — v3.3")
st.caption("Backup capacity is **reserved** on top of self‑consumption. Choose a daily load profile or set a custom split.")

system_key = st.selectbox("System type", list(SYSTEMS.keys()), index=0)
SYS = SYSTEMS[system_key]

with st.form("inputs"):
    st.subheader("Your PV & Consumption")
    colA, colB = st.columns(2)
    total_modules = colA.number_input("Total PV modules installed", min_value=1, max_value=300, value=16, step=1)
    module_wp = colB.number_input("Module wattage (Wp)", min_value=250, max_value=700, value=430, step=5)

    annual_kwh = st.number_input("Annual electricity consumption (kWh)", min_value=500, max_value=50000, value=5000, step=100)

    st.markdown("**Roof layout**")
    layout_choice = st.radio("Where are the modules placed?", ["All on one side", "Split across two opposite sides"], index=0, horizontal=False)

    if layout_choice == "All on one side":
        col3, col4 = st.columns(2)
        orientation_single = col3.selectbox("Orientation", options=["south", "southeast", "southwest", "east", "west", "north"], index=0)
        tilt = col4.number_input("Tilt (degrees)", min_value=0, max_value=90, value=30, step=1)
        orient_fac = orientation_factor(orientation_single)
        profile_flatten = 1.0
        orientation_text = orientation_single
    else:
        col3, col4 = st.columns(2)
        orientation_side_a = col3.selectbox("Main side orientation", options=["east", "west", "south", "southeast", "southwest", "north"], index=0)
        tilt = col4.number_input("Tilt (degrees)", min_value=0, max_value=90, value=30, step=1)
        orientation_side_b = opposite_orientation(orientation_side_a)
        orient_fac = 0.5 * (orientation_factor(orientation_side_a) + orientation_factor(orientation_side_b))
        profile_flatten = 0.90  # flatter production curve
        orientation_text = f"{orientation_side_a} + {orientation_side_b}"

    # Load profile selection
    st.markdown("**Daily load profile**")
    profile_choice = st.selectbox("Choose a profile", list(LOAD_PROFILES.keys()), index=0)
    if LOAD_PROFILES[profile_choice] is None:
        day_fraction = st.slider("Custom: % of daily consumption during daylight", min_value=0.2, max_value=0.8, value=0.40, step=0.05)
    else:
        day_fraction = LOAD_PROFILES[profile_choice]

    # Backup (optional)
    st.markdown("**Backup (optional)** — reserve capacity for outage support (added on top of self‑consumption).")
    col5, col6 = st.columns(2)
    backup_kw = col5.number_input("Critical load power to support during outage (kW)", min_value=0.0, max_value=30.0, value=0.0, step=0.5)
    backup_hours = col6.number_input("Desired backup duration (hours)", min_value=0.0, max_value=48.0, value=0.0, step=0.5)

    # Advanced (optional)
    with st.expander("Advanced assumptions"):
        region_yield = st.number_input("Specific yield baseline (kWh/kWp/year)", min_value=700, max_value=1500, value=DEFAULT_YIELD_PER_KWP_YR, step=10)
        rte = st.slider("Round-trip efficiency", min_value=0.80, max_value=0.98, value=DEFAULT_RTE, step=0.01)
        dod = st.slider("Usable depth of discharge", min_value=0.80, max_value=0.98, value=DEFAULT_DOD, step=0.01)
        degradation = st.slider("Degradation reserve", min_value=0.05, max_value=0.20, value=DEFAULT_DEGRADATION_RESERVE, step=0.01)

    submitted = st.form_submit_button("Calculate recommendation")

if submitted:
    # Compute PV DC
    dc_kw = (total_modules * module_wp) / 1000.0

    # Yield factors
    tfac = tilt_factor(tilt)
    specific_yield = estimate_yearly_pv_yield_kwp(region_yield, orient_fac, tfac)
    yearly_pv_kwh = dc_kw * specific_yield

    # Inverter pick per system
    inv_choice = pick_inverter(dc_kw, SYS["inverter_ac_sizes"], SYS["models"], SYS["max_dc_ac_ratio"])

    # Battery need (components + additive backup)
    comp = estimate_battery_need_components(annual_kwh, dc_kw, specific_yield, day_fraction, profile_flatten, backup_kw, backup_hours)
    usable_needed, nominal_needed = apply_system_factors(comp["shiftable"], comp["backup_energy"], rte, dod, degradation)
    rec_kwh, rec_label = pick_battery_model(usable_needed, SYS["battery_options_kwh"], SYS["battery_labels"])

    # -----------------------------
    # Results
    # -----------------------------
    # Inverter section
    st.subheader("Inverter recommendation")
    colr1, colr2 = st.columns(2)
    with colr1:
        st.metric("Estimated PV DC size", f"{dc_kw:.2f} kW")
    with colr2:
        st.metric("Suggested inverter", inv_choice["model"], help=f'DC/AC ratio ≈ {inv_choice["dc_ac_ratio"]:.2f} (cap ≤ {SYS["max_dc_ac_ratio"]})')
    if not inv_choice["within_cap"]:
        st.warning(f"Your DC/AC ratio exceeds the {SYS['max_dc_ac_ratio']} cap. Consider a larger inverter or less PV DC.")
    if backup_kw > 0 and inv_choice["ac_kw"] < backup_kw:
        st.warning(f"Backup power needs {backup_kw:.1f} kW, which exceeds the selected inverter's AC rating ({inv_choice['ac_kw']:.1f} kW). Consider the next larger model.")

    st.markdown("---")
    st.subheader("Battery sizing inputs & rationale")
    st.write(f"- Orientation: **{orientation_text}**; Tilt: **{tilt}°**")
    st.write(f"- Load profile: **{profile_choice}** → daytime **{day_fraction*100:.0f}%**, night **{(1-day_fraction)*100:.0f}%**")
    st.write(f"- Typical daily load: **{comp['daily_load']:.1f} kWh**; Typical daily PV: **{comp['daily_pv']:.1f} kWh** (from {dc_kw:.2f} kW @ {specific_yield:.0f} kWh/kWp/yr)")
    st.write(f"- Daytime load: **{comp['day_load']:.1f} kWh**; Night load: **{comp['night_load']:.1f} kWh**")
    st.write(f"- Daytime PV surplus: **{comp['surplus_day']:.1f} kWh**; Shiftable to night: **{comp['shiftable']:.1f} kWh**")
    if layout_choice == "Split across two opposite sides":
        st.caption("Two-side layout flattens production; surplus reduced by ~10% to reflect less midday clipping and later peaks.")
    if backup_kw > 0 and backup_hours > 0:
        st.write(f"- Backup requirement: **{backup_kw:.1f} kW** for **{backup_hours:.1f} h** → **{comp['backup_energy']:.1f} kWh** energy (reserved)")

    # Battery section styled like inverter (metrics) + breakdown
    st.markdown("---")
    st.subheader("Battery recommendation")
    colb1, colb2 = st.columns(2)
    with colb1:
        if rec_kwh == 0:
            st.metric("Usable capacity (rounded)", "—")
        else:
            st.metric("Usable capacity (rounded)", f"{rec_kwh:.1f} kWh")
    with colb2:
        if rec_kwh == 0:
            st.metric("Suggested battery model", "No battery recommended")
        else:
            st.metric("Suggested battery model", rec_label)

    if rec_kwh > 0:
        st.caption(f"(Rounded to nearest available size for **{SYS['battery_type']}**; {SYS['battery_step_display']})")
        st.write(f"Breakdown: **Self‑consumption** ~{comp['shiftable']:.1f} kWh + **Backup reserve** ~{comp['backup_energy']:.1f} kWh → **Total usable target** ~{usable_needed:.1f} kWh")
    else:
        st.info("Your shiftable energy is very small and no backup was requested. A battery may have limited benefit for pure self-consumption.")

    st.markdown("---")
    st.subheader("Sanity checks & notes")
    st.write(f"- **MPPTs / strings:** {SYS['mppts']} MPPTs and up to **{SYS['max_strings_total']} strings** (info only).")
    st.write(f"- **Max string current:** ≈ **{SYS['max_string_current_a']} A** per string (verify with module Imp/Isc).")
    st.write(f"- **DC/AC cap:** ≤ {SYS['max_dc_ac_ratio']}. Aim near 1.2–1.4 for good utilization.")
    st.write("- Quick estimate for self-consumption + backup reserve. Tariffs/feed‑in not yet modeled.")

else:
    st.info("Select system, roof layout, **daily load profile** (or custom), optional backup, then click **Calculate recommendation**.")
