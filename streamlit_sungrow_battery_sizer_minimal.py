
import math
import streamlit as st

# -----------------------------
# System definitions
# -----------------------------
SYSTEMS = {
    "Single-phase • SHRS": {
        "inverter_ac_sizes": [3.6, 4.6, 5.0, 6.0],
        "max_dc_ac_ratio": 1.5,
        "mppts": 2,
        "max_strings_total": 2,
        "max_string_current_a": 16,
        # Battery: SBS050 5 kWh each, 1–4 units (no parallel SHRS)
        "battery_type": "SBS050",
        "battery_options_kwh": [5, 10, 15, 20],  # usable
        "battery_step_display": "≈ 5 kWh blocks (1–4 units)"
    },
    "Three-phase • SHRT": {
        "inverter_ac_sizes": [5.0, 6.0, 8.0, 10.0],
        "max_dc_ac_ratio": 1.5,
        "mppts": 2,
        "max_strings_total": 3,
        "max_string_current_a": 13.5,
        # Battery: SBR096..SBR256 (≈ 9.6 to 25.6 kWh usable, ~3.2 kWh steps)
        "battery_type": "SBR",
        "battery_options_kwh": [9.6, 12.8, 16.0, 19.2, 22.4, 25.6],
        "battery_step_display": "≈ 3.2 kWh steps (9.6–25.6 kWh)"
    },
    "Three-phase • SHT": {
        "inverter_ac_sizes": [10.0, 12.0, 15.0, 20.0],
        "max_dc_ac_ratio": 1.5,
        "mppts": 3,
        "max_strings_total": 5,
        "max_string_current_a": 16,
        # Battery: SBH100..SBH400 (10–40 kWh usable, 5 kWh steps; typical stacks)
        "battery_type": "SBH",
        "battery_options_kwh": [10, 15, 20, 25, 30, 35, 40],
        "battery_step_display": "≈ 5 kWh steps (10–40 kWh)"
    },
}

# Assumptions (defaults; adjustable)
DEFAULT_YIELD_PER_KWP_YR = 1050  # kWh/kWp/year baseline for Central Europe / CH
DEFAULT_DAY_FRACTION = 0.40
DEFAULT_RTE = 0.92
DEFAULT_DOD = 0.90
DEFAULT_DEGRADATION_RESERVE = 0.10


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
    if o in ["east-west", "ew", "e-w", "east_west"]:
        return 0.95
    if o in ["north", "n"]:
        return 0.60
    return 1.00


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


def pick_inverter_size(dc_kw: float, ac_sizes: list, max_ratio: float) -> dict:
    choices = []
    for ac in ac_sizes:
        ratio = dc_kw / ac if ac > 0 else float("inf")
        ok = ratio <= max_ratio
        score = abs(1.25 - ratio)  # aim near ~1.25
        choices.append((ac, ratio, ok, score))
    valid = [c for c in choices if c[2]]
    if valid:
        best = min(valid, key=lambda x: (x[3], x[0]))  # closest to 1.25; tie -> smaller AC
    else:
        best = max(choices, key=lambda x: x[0])  # fallback largest AC
    return {"ac_kw": best[0], "dc_ac_ratio": best[1], "within_cap": best[2]}


def estimate_battery_need_simple(annual_kwh: float,
                                 pv_kw: float,
                                 specific_yield_kwh_per_kwp_yr: float,
                                 day_fraction: float,
                                 rte: float,
                                 dod: float,
                                 degradation_reserve: float) -> dict:
    daily_load = annual_kwh / 365.0
    daily_pv = (pv_kw * specific_yield_kwh_per_kwp_yr) / 365.0

    day_load = daily_load * day_fraction
    night_load = daily_load - day_load
    surplus_day = max(0.0, daily_pv - day_load)
    shiftable = min(surplus_day, night_load)

    usable_needed = shiftable
    if usable_needed <= 0:
        nominal_needed = 0.0
    else:
        nominal_needed = usable_needed / (dod * rte)
        nominal_needed *= (1.0 + degradation_reserve)

    return {
        "daily_load": daily_load,
        "daily_pv": daily_pv,
        "day_load": day_load,
        "night_load": night_load,
        "surplus_day": surplus_day,
        "shiftable": shiftable,
        "usable_needed": usable_needed,
        "nominal_needed": nominal_needed
    }


def round_to_available_sizes(usable_kwh_needed: float, options: list) -> float:
    """Pick the closest available usable size from a list of options; minimum 0 if no need."""
    if usable_kwh_needed <= 0:
        return 0.0
    return min(options, key=lambda s: abs(s - usable_kwh_needed))


# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Sungrow Battery Sizer (v2)", layout="centered")

st.title("🔋 Sungrow Battery Sizer — v2")
st.caption("Single‑phase SHRS • Three‑phase SHRT/SHT • Minimal inputs with PV & consumption")

system_key = st.selectbox("System type", list(SYSTEMS.keys()), index=0)
SYS = SYSTEMS[system_key]

with st.form("inputs"):
    st.subheader("Your PV & Consumption")
    colA, colB = st.columns(2)
    total_modules = colA.number_input("Total PV modules installed", min_value=1, max_value=300, value=16, step=1)
    module_wp = colB.number_input("Module wattage (Wp)", min_value=250, max_value=700, value=430, step=5)

    col1, col2 = st.columns(2)
    strings = col1.number_input(f"Number of strings (max {SYS['max_strings_total']})",
                                min_value=1, max_value=SYS['max_strings_total'],
                                value=min(2, SYS['max_strings_total']), step=1)
    annual_kwh = col2.number_input("Annual electricity consumption (kWh)", min_value=500, max_value=50000, value=5000, step=100)

    st.markdown("**Array orientation & tilt** (use the dominant orientation)")
    col3, col4 = st.columns(2)
    orientation = col3.selectbox("Orientation", options=["south", "southeast", "southwest", "east", "west", "east-west", "north"], index=0)
    tilt = col4.number_input("Tilt (degrees)", min_value=0, max_value=90, value=30, step=1)

    # Advanced (optional)
    with st.expander("Advanced assumptions"):
        region_yield = st.number_input("Specific yield baseline (kWh/kWp/year)", min_value=700, max_value=1500, value=DEFAULT_YIELD_PER_KWP_YR, step=10)
        day_fraction = st.slider("Daytime share of your consumption", min_value=0.2, max_value=0.8, value=DEFAULT_DAY_FRACTION, step=0.05)
        rte = st.slider("Round-trip efficiency", min_value=0.80, max_value=0.98, value=DEFAULT_RTE, step=0.01)
        dod = st.slider("Usable depth of discharge", min_value=0.80, max_value=0.98, value=DEFAULT_DOD, step=0.01)
        degradation = st.slider("Degradation reserve", min_value=0.05, max_value=0.20, value=DEFAULT_DEGRADATION_RESERVE, step=0.01)

    submitted = st.form_submit_button("Calculate recommendation")

if submitted:
    # Compute PV DC
    dc_kw = (total_modules * module_wp) / 1000.0

    # Yield factors
    ofac = orientation_factor(orientation)
    tfac = tilt_factor(tilt)
    specific_yield = estimate_yearly_pv_yield_kwp(region_yield, ofac, tfac)
    yearly_pv_kwh = dc_kw * specific_yield

    # Inverter pick per system
    inv_choice = pick_inverter_size(dc_kw, SYS["inverter_ac_sizes"], SYS["max_dc_ac_ratio"])

    # Battery need
    sc = estimate_battery_need_simple(annual_kwh, dc_kw, specific_yield, day_fraction, rte, dod, degradation)
    battery_rec_kwh = round_to_available_sizes(sc["usable_needed"], SYS["battery_options_kwh"])

    # UI results
    st.subheader("Recommendation")
    colr1, colr2 = st.columns(2)
    with colr1:
        st.metric("Estimated PV DC size", f"{dc_kw:.2f} kW")
        st.metric("Suggested inverter (AC)", f'{inv_choice["ac_kw"]:.1f} kW', help=f'DC/AC ratio ≈ {inv_choice["dc_ac_ratio"]:.2f} (cap ≤ {SYS["max_dc_ac_ratio"]})')
        if not inv_choice["within_cap"]:
            st.warning(f"Your DC/AC ratio exceeds the {SYS['max_dc_ac_ratio']} cap. Consider a larger inverter or less PV DC.")
    with colr2:
        st.metric("Specific yield (adj.)", f"{specific_yield:.0f} kWh/kWp/yr")
        st.metric("PV production (est. yearly)", f"{yearly_pv_kwh:.0f} kWh")

    st.markdown("---")
    st.subheader(f"Battery sizing ({SYS['battery_type']})")
    st.write(f"- Typical daily load: **{sc['daily_load']:.1f} kWh**")
    st.write(f"- Typical daily PV: **{sc['daily_pv']:.1f} kWh** (from {dc_kw:.2f} kW @ {specific_yield:.0f} kWh/kWp/yr)")
    st.write(f"- Daytime load (assumed {day_fraction*100:.0f}%): **{sc['day_load']:.1f} kWh**; Night load: **{sc['night_load']:.1f} kWh**")
    st.write(f"- Daytime PV surplus: **{sc['surplus_day']:.1f} kWh**; Shiftable to night: **{sc['shiftable']:.1f} kWh**")

    if battery_rec_kwh == 0:
        st.info("Your typical shiftable energy is very small. A battery may have limited benefit for pure self-consumption.")
    else:
        st.write(f"**Usable storage target**: ~**{sc['usable_needed']:.1f} kWh** → Recommended **{battery_rec_kwh:.1f} kWh** ({SYS['battery_step_display']}).")
        # Model name helper
        if SYS["battery_type"] == "SBR":
            # Convert 9.6 -> 096 etc (rough label)
            label = f"SBR{int(round(battery_rec_kwh*10)):03d}"
            st.write(f"Suggested model capacity label: **{label}**")
        elif SYS["battery_type"] == "SBH":
            label = f"SBH{int(round(battery_rec_kwh*10)):03d}"
            st.write(f"Suggested model capacity label: **{label}**")
        else:  # SBS050 units
            units = int(round(battery_rec_kwh / 5))
            st.write(f"Suggested: **{units}× SBS050** (≈ {battery_rec_kwh:.0f} kWh usable).")

    st.markdown("---")
    st.subheader("Sanity checks & notes")
    st.write(f"- **MPPTs / strings:** {SYS['mppts']} MPPTs and up to **{SYS['max_strings_total']} strings total**.")
    st.write(f"- **Max string current:** ≈ **{SYS['max_string_current_a']} A** per string (verify with module Imp/Isc).")
    st.write(f"- **DC/AC cap:** ≤ {SYS['max_dc_ac_ratio']}. Aim near 1.2–1.4 for good utilization.")
    st.write("- This is a **quick estimate** focused on self-consumption. Tariffs and backup power not included yet.")

else:
    st.info("Fill the form and click **Calculate recommendation** to see the suggested inverter and battery configuration for your selected system.")
