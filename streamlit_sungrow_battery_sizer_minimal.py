
import math
import streamlit as st

# -----------------------------
# Constants (Sungrow single-phase scenario)
# -----------------------------
INVERTER_SIZES_KW = [3.6, 4.6, 5.0, 6.0]  # SHRS AC sizes
MAX_DC_AC_RATIO = 1.5
MPPT_COUNT = 2
MAX_STRING_CURRENT_A = 16  # informational; not validated without module currents

# Battery: SBS050 (usable ≈ 5.0 kWh per unit), up to 4 per SHRS, up to 2 SHRS in parallel
BATTERY_UNIT_KWH = 5.0
MAX_BATTERIES_PER_SHRS = 4
MAX_SHRS_PARALLEL = 2

# Assumptions (tweakable defaults)
DEFAULT_YIELD_PER_KWP_YR = 1050  # kWh/kWp/year for Central Europe / CH baseline
DAY_FRACTION = 0.40              # share of load consumed during daylight hours
RTE = 0.92                       # round trip efficiency (battery + conversion)
DOD = 0.90                       # usable depth of discharge fraction
DEGRADATION_RESERVE = 0.10       # 10% headroom for long-term capacity fade


# -----------------------------
# Helper functions
# -----------------------------
def orientation_factor(orientation: str) -> float:
    """Crude performance factor by azimuth relative to south. South=1.0 baseline."""
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
    """Simple tilt factor relative to ~30-35° optimum for CH/Central EU."""
    if tilt_deg <= 15:
        return 0.95
    if 16 <= tilt_deg <= 45:
        return 1.00
    if 46 <= tilt_deg <= 60:
        return 0.90
    return 0.80  # >60°


def estimate_yearly_pv_yield_kwp(region_yield=DEFAULT_YIELD_PER_KWP_YR,
                                 orient_factor=1.0,
                                 tilt_fac=1.0):
    """Adjusted yearly specific yield (kWh/kWp/yr)."""
    return region_yield * orient_factor * tilt_fac


def pick_inverter_size(dc_kw: float) -> dict:
    """
    Choose SHRS AC size given DC array size, trying to keep DC/AC between ~1.1 and 1.5.
    Prefer the smallest AC size that does not violate the 1.5 cap.
    """
    choices = []
    for ac in INVERTER_SIZES_KW:
        ratio = dc_kw / ac if ac > 0 else float("inf")
        ok = ratio <= MAX_DC_AC_RATIO
        score = abs(1.25 - ratio)  # aim near ~1.25
        choices.append((ac, ratio, ok, score))
    # Filter those under 1.5 cap; if none, take largest AC (still over-capped warning)
    valid = [c for c in choices if c[2]]
    if valid:
        best = min(valid, key=lambda x: (x[3], x[0]))  # closest to 1.25; tie -> smaller AC
    else:
        best = max(choices, key=lambda x: x[0])  # largest AC; will flag ratio>1.5
    return {"ac_kw": best[0], "dc_ac_ratio": best[1], "within_cap": best[2]}


def round_to_battery_steps(usable_kwh_needed: float, shrs_count: int) -> dict:
    """
    Round the usable capacity to SBS050 steps.
    - Each SBS050 ≈ 5 kWh usable
    - Up to 4 per SHRS
    - Up to 2 SHRS in parallel
    """
    max_units = MAX_BATTERIES_PER_SHRS * shrs_count
    max_usable = max_units * BATTERY_UNIT_KWH
    units = min(max_units, max(1, round(usable_kwh_needed / BATTERY_UNIT_KWH)))
    usable = units * BATTERY_UNIT_KWH
    return {"units_total": units, "usable_kwh": usable, "max_usable_kwh": max_usable}


def estimate_battery_need_simple(annual_kwh: float,
                                 pv_kw: float,
                                 specific_yield_kwh_per_kwp_yr: float) -> dict:
    """
    Minimalist 'self-consumption' storage target:
    - Estimate daily load and PV
    - Assume DAY_FRACTION of load occurs while PV is producing
    - Shiftable = min(daytime surplus, night load)
    - Size to cover typical daily shiftable energy (add RTE/DOD/degradation headroom)
    """
    daily_load = annual_kwh / 365.0
    daily_pv = (pv_kw * specific_yield_kwh_per_kwp_yr) / 365.0

    day_load = daily_load * DAY_FRACTION
    night_load = daily_load - day_load
    surplus_day = max(0.0, daily_pv - day_load)
    shiftable = min(surplus_day, night_load)

    # Convert shiftable usable energy into nominal capacity with headrooms
    usable_needed = shiftable  # target usable energy to shift per typical day
    if usable_needed <= 0:
        nominal_needed = 0.0
    else:
        nominal_needed = usable_needed / (DOD * RTE)
        nominal_needed *= (1.0 + DEGRADATION_RESERVE)

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


# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Sungrow Battery Sizer (Minimal Inputs)", layout="centered")

st.title("🔋 Sungrow Battery Sizer — Minimal Inputs")
st.caption("SHRS (3.6/4.6/5.0/6.0 kW) • SBS050 (5 kWh per unit) • Up to 4 batteries per SHRS • Up to 2 SHRS in parallel")

with st.form("inputs"):
    st.subheader("Your PV & Consumption")
    colA, colB = st.columns(2)
    total_modules = colA.number_input("Total PV modules installed", min_value=1, max_value=200, value=16, step=1)
    module_wp = colB.number_input("Module wattage (Wp)", min_value=250, max_value=700, value=430, step=5)

    col1, col2 = st.columns(2)
    strings = col1.selectbox("Number of strings (MPPTs used)", options=[1, 2], index=1)
    annual_kwh = col2.number_input("Annual electricity consumption (kWh)", min_value=500, max_value=30000, value=5000, step=100)

    st.markdown("**Array orientation & tilt** (use the dominant orientation; per-string detail is optional)")
    col3, col4 = st.columns(2)
    orientation = col3.selectbox("Orientation", options=["south", "southeast", "southwest", "east", "west", "east-west", "north"], index=0)
    tilt = col4.number_input("Tilt (degrees)", min_value=0, max_value=90, value=30, step=1)

    # Optional: per-string module split (only visible if 2 strings)
    per_string_counts = [total_modules, 0]
    if strings == 2:
        st.markdown("Optional: **Modules per string** (for 2 strings). Leave equal split if unsure.")
        s1 = st.number_input("String 1: modules", min_value=1, max_value=int(total_modules)-1, value=int(math.ceil(total_modules/2)), step=1)
        s2 = total_modules - s1
        st.write(f"String 2: modules = {s2}")
        per_string_counts = [s1, s2]

    # Advanced (optional)
    with st.expander("Advanced assumptions"):
        region_yield = st.number_input("Specific yield baseline (kWh/kWp/year)", min_value=700, max_value=1500, value=DEFAULT_YIELD_PER_KWP_YR, step=10)
        day_fraction = st.slider("Daytime share of your consumption", min_value=0.2, max_value=0.8, value=DAY_FRACTION, step=0.05)
        rte = st.slider("Round-trip efficiency", min_value=0.80, max_value=0.98, value=RTE, step=0.01)
        dod = st.slider("Usable depth of discharge", min_value=0.80, max_value=0.98, value=DOD, step=0.01)
        degradation = st.slider("Degradation reserve", min_value=0.05, max_value=0.20, value=DEGRADATION_RESERVE, step=0.01)
        two_shrs = st.checkbox("Two SHRS in parallel (doubles max battery units)", value=False)

    submitted = st.form_submit_button("Calculate recommendation")

if submitted:
    # Update globals from advanced
    global DAY_FRACTION, RTE, DOD, DEGRADATION_RESERVE
    DAY_FRACTION = day_fraction
    RTE = rte
    DOD = dod
    DEGRADATION_RESERVE = degradation

    # Compute DC size
    dc_kw = (total_modules * module_wp) / 1000.0

    # Orientation/tilt factors and specific yield
    ofac = orientation_factor(orientation)
    tfac = tilt_factor(tilt)
    specific_yield = estimate_yearly_pv_yield_kwp(region_yield, ofac, tfac)

    # Estimated yearly & daily PV
    yearly_pv_kwh = dc_kw * specific_yield

    # Inverter pick
    inv_choice = pick_inverter_size(dc_kw)

    # Battery need (minimal self-consumption approach)
    sc = estimate_battery_need_simple(annual_kwh, dc_kw, specific_yield)

    # Round to SBS050 steps
    shrs_count = 2 if two_shrs else 1
    rounding = round_to_battery_steps(sc["usable_needed"], shrs_count)

    # -----------------------------
    # Results
    # -----------------------------
    st.subheader("Recommendation")
    colr1, colr2 = st.columns(2)
    with colr1:
        st.metric("Estimated PV DC size", f"{dc_kw:.2f} kW")
        st.metric("Suggested SHRS AC size", f'{inv_choice["ac_kw"]:.1f} kW', help=f'DC/AC ratio ≈ {inv_choice["dc_ac_ratio"]:.2f} (cap ≤ {MAX_DC_AC_RATIO})')
        if not inv_choice["within_cap"]:
            st.warning("Your DC/AC ratio exceeds the 1.5 cap. Consider a larger SHRS or reducing PV DC.")
    with colr2:
        st.metric("Specific yield (adj.)", f"{specific_yield:.0f} kWh/kWp/yr")
        st.metric("PV production (est. yearly)", f"{yearly_pv_kwh:.0f} kWh")

    st.markdown("---")
    st.subheader("Battery sizing (SBS050)")
    st.write(f"- Typical daily load: **{sc['daily_load']:.1f} kWh** (from {annual_kwh} kWh/yr)")
    st.write(f"- Typical daily PV: **{sc['daily_pv']:.1f} kWh** (from {dc_kw:.2f} kW @ {specific_yield:.0f} kWh/kWp/yr)")
    st.write(f"- Daytime load (assumed {DAY_FRACTION*100:.0f}%): **{sc['day_load']:.1f} kWh**; Night load: **{sc['night_load']:.1f} kWh**")
    st.write(f"- Daytime PV surplus: **{sc['surplus_day']:.1f} kWh**; Shiftable to night: **{sc['shiftable']:.1f} kWh**")

    if sc["usable_needed"] <= 0.1:
        st.info("Based on your inputs, there may be little to no surplus to shift at typical days. A battery may offer limited benefit for pure self-consumption.")
    else:
        st.write(f"**Usable storage target** (per typical day): **{sc['usable_needed']:.1f} kWh**")
        st.write(f"Rounded to SBS050 steps (≈ {BATTERY_UNIT_KWH:.1f} kWh each): **{rounding['units_total']} unit(s)** → **{rounding['usable_kwh']:.1f} kWh usable**")
        st.write(f"Max usable capacity allowed by your setup: **{rounding['max_usable_kwh']:.0f} kWh**" + (" (two SHRS)" if two_shrs else " (one SHRS)"))

    # Quick heuristic nudge if feed-in is likely low (no tariff inputs here; informational only)
    if sc["shiftable"] > 0 and sc["usable_needed"] < (2 * BATTERY_UNIT_KWH):
        st.caption("Tip: If feed-in price is much lower than your purchase tariff, consider going one step larger to capture more surplus on sunny days.")

    st.markdown("---")
    st.subheader("Sanity checks & notes")
    st.write("- **Strings vs MPPTs:** You selected **{} string(s)**; SHRS has **{} MPPTs**. This is fine. For two strings, try to keep similar orientations or use separate MPPTs.".format(strings, MPPT_COUNT))
    st.write(f"- **String current:** Max recommended ≈ {MAX_STRING_CURRENT_A} A per string (needs module Imp/Isc to verify; not checked here).")
    st.write(f"- **DC/AC ratio cap:** ≤ {MAX_DC_AC_RATIO}. We aim near 1.2–1.4 for good clipping vs utilization balance.")
    st.write("- This tool is a **quick estimate** for self-consumption sizing. Backup power and tariffs are not considered in this minimal version.")

else:
    st.info("Fill the form and click **Calculate recommendation** to see the suggested SHRS size and SBS050 battery configuration.")
