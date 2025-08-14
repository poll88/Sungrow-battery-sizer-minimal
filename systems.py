# systems.py

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
        "battery_step_display": "≈ 3.2 kWh blocks (9.6–25.6 kWh)"
    },
    "Three-phase • SHT": {
        "models": {10.0: "SH10T", 12.0: "SH12T", 15.0: "SH15T", 20.0: "SH20T"},
        "inverter_ac_sizes": [10.0, 12.0, 15.0, 20.0],
        "max_dc_ac_ratio": 1.5,
        "mppts": 3,
        "max_strings_total": 5,
        "max_string_current_a": 16.0,
        "battery_type": "SBH",
        "battery_options_kwh": [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0],
        "battery_labels": ["SBH100", "SBH150", "SBH200", "SBH250", "SBH300", "SBH350", "SBH400"],
        "battery_step_display": "≈ 5 kWh blocks (10–40 kWh)"
    }
}
