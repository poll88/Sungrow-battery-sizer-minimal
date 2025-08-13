import math
import streamlit as st

# -----------------------------
# i18n setup
# -----------------------------
LANGUAGES = {
    "English": "en",
    "Italiano": "it",
    "Français": "fr",
    "Deutsch": "de",
    "Español": "es",
}

TRANSLATIONS = {
    "en": {
        "Language": "Language",
        "🔋 Sungrow Battery Sizer — v3.3": "🔋 Sungrow Battery Sizer — v3.3",
        "Backup capacity is **reserved** on top of self‑consumption. Choose a daily load profile or set a custom split.": "Backup capacity is **reserved** on top of self‑consumption. Choose a daily load profile or set a custom split.",
        "System type": "System type",
        "Your PV & Consumption": "Your PV & Consumption",
        "Total PV modules installed": "Total PV modules installed",
        "Module wattage (Wp)": "Module wattage (Wp)",
        "Annual electricity consumption (kWh)": "Annual electricity consumption (kWh)",
        "Roof layout": "Roof layout",
        "Where are the modules placed?": "Where are the modules placed?",
        "All on one side": "All on one side",
        "Split across two opposite sides": "Split across two opposite sides",
        "Orientation": "Orientation",
        "Tilt (degrees)": "Tilt (degrees)",
        "Main side orientation": "Main side orientation",
        "Daily load profile": "Daily load profile",
        "Choose a profile": "Choose a profile",
        "Balanced household (40% day / 60% night)": "Balanced household (40% day / 60% night)",
        "Workday away (30% / 70%)": "Workday away (30% / 70%)",
        "Home most of day (55% / 45%)": "Home most of day (55% / 45%)",
        "Evening peaky (25% / 75%)": "Evening peaky (25% / 75%)",
        "Heat pump or daytime loads (50% / 50%)": "Heat pump or daytime loads (50% / 50%)",
        "Custom…": "Custom…",
        "Custom: % of daily consumption during daylight": "Custom: % of daily consumption during daylight",
        "Backup (optional) — reserve capacity for outage support (added on top of self‑consumption).": "Backup (optional) — reserve capacity for outage support (added on top of self‑consumption).",
        "Critical load power to support during outage (kW)": "Critical load power to support during outage (kW)",
        "Desired backup duration (hours)": "Desired backup duration (hours)",
        "Advanced assumptions": "Advanced assumptions",
        "Specific yield baseline (kWh/kWp/year)": "Specific yield baseline (kWh/kWp/year)",
        "Round-trip efficiency": "Round-trip efficiency",
        "Usable depth of discharge": "Usable depth of discharge",
        "Degradation reserve": "Degradation reserve",
        "Calculate recommendation": "Calculate recommendation",
        "Inverter recommendation": "Inverter recommendation",
        "Estimated PV DC size": "Estimated PV DC size",
        "Suggested inverter": "Suggested inverter",
        "DC/AC ratio ≈ {ratio} (cap ≤ {cap})": "DC/AC ratio ≈ {ratio} (cap ≤ {cap})",
        "Your DC/AC ratio exceeds the {cap} cap. Consider a larger inverter or less PV DC.": "Your DC/AC ratio exceeds the {cap} cap. Consider a larger inverter or less PV DC.",
        "Backup power needs {need} kW, which exceeds the selected inverter's AC rating ({ac} kW). Consider the next larger model.": "Backup power needs {need} kW, which exceeds the selected inverter's AC rating ({ac} kW). Consider the next larger model.",
        "Battery sizing inputs & rationale": "Battery sizing inputs & rationale",
        "- Orientation: **{orientation}**; Tilt: **{tilt}°**": "- Orientation: **{orientation}**; Tilt: **{tilt}°**",
        "- Load profile: **{profile}** → daytime **{day}%**, night **{night}%**": "- Load profile: **{profile}** → daytime **{day}%**, night **{night}%**",
        "- Typical daily load: **{daily_load:.1f} kWh**; Typical daily PV: **{daily_pv:.1f} kWh** (from {dc_kw:.2f} kW @ {specific_yield:.0f} kWh/kWp/yr)": "- Typical daily load: **{daily_load:.1f} kWh**; Typical daily PV: **{daily_pv:.1f} kWh** (from {dc_kw:.2f} kW @ {specific_yield:.0f} kWh/kWp/yr)",
        "- Daytime load: **{day_load:.1f} kWh**; Night load: **{night_load:.1f} kWh**": "- Daytime load: **{day_load:.1f} kWh**; Night load: **{night_load:.1f} kWh**",
        "- Daytime PV surplus: **{surplus:.1f} kWh**; Shiftable to night: **{shiftable:.1f} kWh**": "- Daytime PV surplus: **{surplus:.1f} kWh**; Shiftable to night: **{shiftable:.1f} kWh**",
        "Two-side layout flattens production; surplus reduced by ~10% to reflect less midday clipping and later peaks.": "Two-side layout flattens production; surplus reduced by ~10% to reflect less midday clipping and later peaks.",
        "- Backup requirement: **{kw:.1f} kW** for **{h:.1f} h** → **{energy:.1f} kWh** energy (reserved)": "- Backup requirement: **{kw:.1f} kW** for **{h:.1f} h** → **{energy:.1f} kWh** energy (reserved)",
        "Battery recommendation": "Battery recommendation",
        "Usable capacity (rounded)": "Usable capacity (rounded)",
        "Suggested battery model": "Suggested battery model",
        "No battery recommended": "No battery recommended",
        "(Rounded to nearest available size for **{battery_type}**; {battery_step_display})": "(Rounded to nearest available size for **{battery_type}**; {battery_step_display})",
        "Breakdown: **Self‑consumption** ~{self:.1f} kWh + **Backup reserve** ~{backup:.1f} kWh → **Total usable target** ~{total:.1f} kWh": "Breakdown: **Self‑consumption** ~{self:.1f} kWh + **Backup reserve** ~{backup:.1f} kWh → **Total usable target** ~{total:.1f} kWh",
        "Your shiftable energy is very small and no backup was requested. A battery may have limited benefit for pure self-consumption.": "Your shiftable energy is very small and no backup was requested. A battery may have limited benefit for pure self-consumption.",
        "Sanity checks & notes": "Sanity checks & notes",
        "- **MPPTs / strings:** {mppts} MPPTs and up to **{strings} strings** (info only).": "- **MPPTs / strings:** {mppts} MPPTs and up to **{strings} strings** (info only).",
        "- **Max string current:** ≈ **{current} A** per string (verify with module Imp/Isc).": "- **Max string current:** ≈ **{current} A** per string (verify with module Imp/Isc).",
        "- **DC/AC cap:** ≤ {cap}. Aim near 1.2–1.4 for good utilization.": "- **DC/AC cap:** ≤ {cap}. Aim near 1.2–1.4 for good utilization.",
        "- Quick estimate for self-consumption + backup reserve. Tariffs/feed‑in not yet modeled.": "- Quick estimate for self-consumption + backup reserve. Tariffs/feed‑in not yet modeled.",
        "Select system, roof layout, **daily load profile** (or custom), optional backup, then click **Calculate recommendation**.": "Select system, roof layout, **daily load profile** (or custom), optional backup, then click **Calculate recommendation**.",
        "south": "south",
        "southeast": "southeast",
        "southwest": "southwest",
        "east": "east",
        "west": "west",
        "north": "north",
        "northwest": "northwest",
        "northeast": "northeast",
    },
    "it": {
        "Language": "Lingua",
        "🔋 Sungrow Battery Sizer — v3.3": "🔋 Calcolatore Batteria Sungrow — v3.3",
        "Backup capacity is **reserved** on top of self‑consumption. Choose a daily load profile or set a custom split.": "La capacità di backup è **riservata** oltre all'autoconsumo. Scegli un profilo di carico giornaliero o imposta una suddivisione personalizzata.",
        "System type": "Tipo di sistema",
        "Your PV & Consumption": "Il tuo FV e Consumo",
        "Total PV modules installed": "Numero totale di moduli FV installati",
        "Module wattage (Wp)": "Potenza del modulo (Wp)",
        "Annual electricity consumption (kWh)": "Consumo elettrico annuo (kWh)",
        "Roof layout": "Disposizione del tetto",
        "Where are the modules placed?": "Dove sono posizionati i moduli?",
        "All on one side": "Tutti su un lato",
        "Split across two opposite sides": "Divisi su due lati opposti",
        "Orientation": "Orientamento",
        "Tilt (degrees)": "Inclinazione (gradi)",
        "Main side orientation": "Orientamento lato principale",
        "Daily load profile": "Profilo di carico giornaliero",
        "Choose a profile": "Scegli un profilo",
        "Balanced household (40% day / 60% night)": "Famiglia bilanciata (40% giorno / 60% notte)",
        "Workday away (30% / 70%)": "Giornata lavorativa fuori casa (30% / 70%)",
        "Home most of day (55% / 45%)": "A casa per gran parte della giornata (55% / 45%)",
        "Evening peaky (25% / 75%)": "Picco serale (25% / 75%)",
        "Heat pump or daytime loads (50% / 50%)": "Pompa di calore o carichi diurni (50% / 50%)",
        "Custom…": "Personalizzato…",
        "Custom: % of daily consumption during daylight": "Personalizzato: % di consumo giornaliero durante il giorno",
        "Backup (optional) — reserve capacity for outage support (added on top of self‑consumption).": "Backup (opzionale) — capacità riservata per supporto in caso di blackout (aggiunta oltre all'autoconsumo).",
        "Critical load power to support during outage (kW)": "Potenza del carico critico da supportare durante il blackout (kW)",
        "Desired backup duration (hours)": "Durata del backup desiderata (ore)",
        "Advanced assumptions": "Assunzioni avanzate",
        "Specific yield baseline (kWh/kWp/year)": "Rendimento specifico di base (kWh/kWp/anno)",
        "Round-trip efficiency": "Efficienza di ciclo",
        "Usable depth of discharge": "Profondità di scarica utilizzabile",
        "Degradation reserve": "Riserva per degradazione",
        "Calculate recommendation": "Calcola raccomandazione",
        "Inverter recommendation": "Raccomandazione inverter",
        "Estimated PV DC size": "Potenza FV CC stimata",
        "Suggested inverter": "Inverter suggerito",
        "DC/AC ratio ≈ {ratio} (cap ≤ {cap})": "Rapporto CC/CA ≈ {ratio} (limite ≤ {cap})",
        "Your DC/AC ratio exceeds the {cap} cap. Consider a larger inverter or less PV DC.": "Il tuo rapporto CC/CA supera il limite di {cap}. Considera un inverter più grande o meno FV CC.",
        "Backup power needs {need} kW, which exceeds the selected inverter's AC rating ({ac} kW). Consider the next larger model.": "La potenza di backup richiede {need} kW, che supera la potenza AC dell'inverter selezionato ({ac} kW). Considera il modello più grande.",
        "Battery sizing inputs & rationale": "Input dimensionamento batteria e motivazione",
        "- Orientation: **{orientation}**; Tilt: **{tilt}°**": "- Orientamento: **{orientation}**; Inclinazione: **{tilt}°**",
        "- Load profile: **{profile}** → daytime **{day}%**, night **{night}%**": "- Profilo di carico: **{profile}** → giorno **{day}%**, notte **{night}%**",
        "- Typical daily load: **{daily_load:.1f} kWh**; Typical daily PV: **{daily_pv:.1f} kWh** (from {dc_kw:.2f} kW @ {specific_yield:.0f} kWh/kWp/yr)": "- Carico giornaliero tipico: **{daily_load:.1f} kWh**; FV giornaliero tipico: **{daily_pv:.1f} kWh** (da {dc_kw:.2f} kW @ {specific_yield:.0f} kWh/kWp/anno)",
        "- Daytime load: **{day_load:.1f} kWh**; Night load: **{night_load:.1f} kWh**": "- Carico diurno: **{day_load:.1f} kWh**; Carico notturno: **{night_load:.1f} kWh**",
        "- Daytime PV surplus: **{surplus:.1f} kWh**; Shiftable to night: **{shiftable:.1f} kWh**": "- Surplus FV diurno: **{surplus:.1f} kWh**; Spostabile alla notte: **{shiftable:.1f} kWh**",
        "Two-side layout flattens production; surplus reduced by ~10% to reflect less midday clipping and later peaks.": "La disposizione su due lati appiattisce la produzione; il surplus è ridotto di ~10% per riflettere minori tagli a mezzogiorno e picchi più tardivi.",
        "- Backup requirement: **{kw:.1f} kW** for **{h:.1f} h** → **{energy:.1f} kWh** energy (reserved)": "- Requisito di backup: **{kw:.1f} kW** per **{h:.1f} h** → **{energy:.1f} kWh** di energia (riservata)",
        "Battery recommendation": "Raccomandazione batteria",
        "Usable capacity (rounded)": "Capacità utilizzabile (arrotondata)",
        "Suggested battery model": "Modello di batteria suggerito",
        "No battery recommended": "Nessuna batteria raccomandata",
        "(Rounded to nearest available size for **{battery_type}**; {battery_step_display})": "(Arrotondato alla misura disponibile più vicina per **{battery_type}**; {battery_step_display})",
        "Breakdown: **Self‑consumption** ~{self:.1f} kWh + **Backup reserve** ~{backup:.1f} kWh → **Total usable target** ~{total:.1f} kWh": "Dettaglio: **Autoconsumo** ~{self:.1f} kWh + **Riserva backup** ~{backup:.1f} kWh → **Totale utilizzabile** ~{total:.1f} kWh",
        "Your shiftable energy is very small and no backup was requested. A battery may have limited benefit for pure self-consumption.": "La tua energia spostabile è molto bassa e non è stato richiesto backup. Una batteria potrebbe avere benefici limitati per il solo autoconsumo.",
        "Sanity checks & notes": "Verifiche e note",
        "- **MPPTs / strings:** {mppts} MPPTs and up to **{strings} strings** (info only).": "- **MPPT / stringhe:** {mppts} MPPT e fino a **{strings} stringhe** (solo informativo).",
        "- **Max string current:** ≈ **{current} A** per string (verify with module Imp/Isc).": "- **Corrente massima stringa:** ≈ **{current} A** per stringa (verificare con Imp/Isc del modulo).",
        "- **DC/AC cap:** ≤ {cap}. Aim near 1.2–1.4 for good utilization.": "- **Limite CC/CA:** ≤ {cap}. Puntare tra 1.2–1.4 per una buona utilizzazione.",
        "- Quick estimate for self-consumption + backup reserve. Tariffs/feed‑in not yet modeled.": "- Stima rapida per autoconsumo + riserva di backup. Tariffe/immissione non ancora modellate.",
        "Select system, roof layout, **daily load profile** (or custom), optional backup, then click **Calculate recommendation**.": "Seleziona sistema, disposizione del tetto, **profilo di carico giornaliero** (o personalizzato), backup opzionale, quindi clicca **Calcola raccomandazione**.",
        "south": "sud",
        "southeast": "sud-est",
        "southwest": "sud-ovest",
        "east": "est",
        "west": "ovest",
        "north": "nord",
        "northwest": "nord-ovest",
        "northeast": "nord-est",
    },
    "fr": {
        "Language": "Langue",
        "🔋 Sungrow Battery Sizer — v3.3": "🔋 Dimensionneur de batterie Sungrow — v3.3",
        "Backup capacity is **reserved** on top of self‑consumption. Choose a daily load profile or set a custom split.": "La capacité de secours est **réservée** en plus de l'autoconsommation. Choisissez un profil de charge quotidien ou définissez une répartition personnalisée.",
        "System type": "Type de système",
        "Your PV & Consumption": "Votre PV et consommation",
        "Total PV modules installed": "Nombre total de modules PV installés",
        "Module wattage (Wp)": "Puissance du module (Wp)",
        "Annual electricity consumption (kWh)": "Consommation électrique annuelle (kWh)",
        "Roof layout": "Disposition du toit",
        "Where are the modules placed?": "Où sont placés les modules?",
        "All on one side": "Tous d'un côté",
        "Split across two opposite sides": "Répartis sur deux côtés opposés",
        "Orientation": "Orientation",
        "Tilt (degrees)": "Inclinaison (degrés)",
        "Main side orientation": "Orientation côté principal",
        "Daily load profile": "Profil de charge quotidien",
        "Choose a profile": "Choisissez un profil",
        "Balanced household (40% day / 60% night)": "Ménage équilibré (40% jour / 60% nuit)",
        "Workday away (30% / 70%)": "Journée de travail hors domicile (30% / 70%)",
        "Home most of day (55% / 45%)": "À la maison la plupart de la journée (55% / 45%)",
        "Evening peaky (25% / 75%)": "Pic le soir (25% / 75%)",
        "Heat pump or daytime loads (50% / 50%)": "Pompe à chaleur ou charges diurnes (50% / 50%)",
        "Custom…": "Personnalisé…",
        "Custom: % of daily consumption during daylight": "Personnalisé : % de la consommation quotidienne en journée",
        "Backup (optional) — reserve capacity for outage support (added on top of self‑consumption).": "Secours (optionnel) — capacité réservée pour les coupures (ajoutée à l'autoconsommation).",
        "Critical load power to support during outage (kW)": "Puissance du chargement critique à soutenir lors d'une coupure (kW)",
        "Desired backup duration (hours)": "Durée de secours souhaitée (heures)",
        "Advanced assumptions": "Hypothèses avancées",
        "Specific yield baseline (kWh/kWp/year)": "Productivité spécifique de base (kWh/kWp/an)",
        "Round-trip efficiency": "Rendement aller-retour",
        "Usable depth of discharge": "Profondeur de décharge utilisable",
        "Degradation reserve": "Réserve de dégradation",
        "Calculate recommendation": "Calculer la recommandation",
        "Inverter recommendation": "Recommandation onduleur",
        "Estimated PV DC size": "Puissance CC PV estimée",
        "Suggested inverter": "Onduleur suggéré",
        "DC/AC ratio ≈ {ratio} (cap ≤ {cap})": "Rapport CC/CA ≈ {ratio} (limite ≤ {cap})",
        "Your DC/AC ratio exceeds the {cap} cap. Consider a larger inverter or less PV DC.": "Votre rapport CC/CA dépasse la limite de {cap}. Envisagez un onduleur plus grand ou moins de CC PV.",
        "Backup power needs {need} kW, which exceeds the selected inverter's AC rating ({ac} kW). Consider the next larger model.": "La puissance de secours nécessite {need} kW, ce qui dépasse la puissance AC de l'onduleur sélectionné ({ac} kW). Envisagez le modèle supérieur.",
        "Battery sizing inputs & rationale": "Entrées de dimensionnement de la batterie et justification",
        "- Orientation: **{orientation}**; Tilt: **{tilt}°**": "- Orientation : **{orientation}**; Inclinaison : **{tilt}°**",
        "- Load profile: **{profile}** → daytime **{day}%**, night **{night}%**": "- Profil de charge : **{profile}** → jour **{day}%**, nuit **{night}%**",
        "- Typical daily load: **{daily_load:.1f} kWh**; Typical daily PV: **{daily_pv:.1f} kWh** (from {dc_kw:.2f} kW @ {specific_yield:.0f} kWh/kWp/yr)": "- Charge quotidienne typique : **{daily_load:.1f} kWh**; PV quotidien typique : **{daily_pv:.1f} kWh** (à partir de {dc_kw:.2f} kW @ {specific_yield:.0f} kWh/kWp/an)",
        "- Daytime load: **{day_load:.1f} kWh**; Night load: **{night_load:.1f} kWh**": "- Charge de jour : **{day_load:.1f} kWh**; Charge de nuit : **{night_load:.1f} kWh**",
        "- Daytime PV surplus: **{surplus:.1f} kWh**; Shiftable to night: **{shiftable:.1f} kWh**": "- Surplus PV de jour : **{surplus:.1f} kWh**; Déplaçable la nuit : **{shiftable:.1f} kWh**",
        "Two-side layout flattens production; surplus reduced by ~10% to reflect less midday clipping and later peaks.": "La disposition sur deux côtés aplatit la production; surplus réduit d'environ 10% pour refléter moins de limitation à midi et des pics plus tardifs.",
        "- Backup requirement: **{kw:.1f} kW** for **{h:.1f} h** → **{energy:.1f} kWh** energy (reserved)": "- Besoin de secours : **{kw:.1f} kW** pendant **{h:.1f} h** → **{energy:.1f} kWh** d'énergie (réservée)",
        "Battery recommendation": "Recommandation batterie",
        "Usable capacity (rounded)": "Capacité utilisable (arrondie)",
        "Suggested battery model": "Modèle de batterie suggéré",
        "No battery recommended": "Aucune batterie recommandée",
        "(Rounded to nearest available size for **{battery_type}**; {battery_step_display})": "(Arrondi à la taille disponible la plus proche pour **{battery_type}**; {battery_step_display})",
        "Breakdown: **Self‑consumption** ~{self:.1f} kWh + **Backup reserve** ~{backup:.1f} kWh → **Total usable target** ~{total:.1f} kWh": "Détail : **Autoconsommation** ~{self:.1f} kWh + **Réserve secours** ~{backup:.1f} kWh → **Cible utilisable totale** ~{total:.1f} kWh",
        "Your shiftable energy is very small and no backup was requested. A battery may have limited benefit for pure self-consumption.": "Votre énergie déplaçable est très faible et aucun secours n'a été demandé. Une batterie peut avoir un bénéfice limité pour l'autoconsommation pure.",
        "Sanity checks & notes": "Vérifications et notes",
        "- **MPPTs / strings:** {mppts} MPPTs and up to **{strings} strings** (info only).": "- **MPPT / strings :** {mppts} MPPT et jusqu'à **{strings} strings** (info uniquement).",
        "- **Max string current:** ≈ **{current} A** per string (verify with module Imp/Isc).": "- **Courant max par string :** ≈ **{current} A** par string (vérifier avec Imp/Isc du module).",
        "- **DC/AC cap:** ≤ {cap}. Aim near 1.2–1.4 for good utilization.": "- **Limite CC/CA :** ≤ {cap}. Visez entre 1.2–1.4 pour une bonne utilisation.",
        "- Quick estimate for self-consumption + backup reserve. Tariffs/feed‑in not yet modeled.": "- Estimation rapide pour autoconsommation + réserve de secours. Tarifs/injection non encore modélisés.",
        "Select system, roof layout, **daily load profile** (or custom), optional backup, then click **Calculate recommendation**.": "Sélectionnez le système, la disposition du toit, **profil de charge quotidien** (ou personnalisé), secours optionnel, puis cliquez sur **Calculer la recommandation**.",
        "south": "sud",
        "southeast": "sud-est",
        "southwest": "sud-ouest",
        "east": "est",
        "west": "ouest",
        "north": "nord",
        "northwest": "nord-ouest",
        "northeast": "nord-est",
    },
    "de": {
        "Language": "Sprache",
        "🔋 Sungrow Battery Sizer — v3.3": "🔋 Sungrow Batteriegrößenrechner — v3.3",
        "Backup capacity is **reserved** on top of self‑consumption. Choose a daily load profile or set a custom split.": "Backup-Kapazität wird **zusätzlich** zum Eigenverbrauch reserviert. Wählen Sie ein tägliches Lastprofil oder legen Sie eine eigene Aufteilung fest.",
        "System type": "Systemtyp",
        "Your PV & Consumption": "Ihre PV & Verbrauch",
        "Total PV modules installed": "Anzahl installierter PV-Module",
        "Module wattage (Wp)": "Modul-Leistung (Wp)",
        "Annual electricity consumption (kWh)": "Jährlicher Stromverbrauch (kWh)",
        "Roof layout": "Dachanordnung",
        "Where are the modules placed?": "Wo sind die Module platziert?",
        "All on one side": "Alle auf einer Seite",
        "Split across two opposite sides": "Auf zwei gegenüberliegenden Seiten verteilt",
        "Orientation": "Ausrichtung",
        "Tilt (degrees)": "Neigung (Grad)",
        "Main side orientation": "Ausrichtung der Hauptseite",
        "Daily load profile": "Tägliches Lastprofil",
        "Choose a profile": "Profil wählen",
        "Balanced household (40% day / 60% night)": "Ausgeglichenes Haushalt (40% Tag / 60% Nacht)",
        "Workday away (30% / 70%)": "Arbeitstag außer Haus (30% / 70%)",
        "Home most of day (55% / 45%)": "Meist zuhause (55% / 45%)",
        "Evening peaky (25% / 75%)": "Abendspitzen (25% / 75%)",
        "Heat pump or daytime loads (50% / 50%)": "Wärmepumpe oder Tageslasten (50% / 50%)",
        "Custom…": "Benutzerdefiniert…",
        "Custom: % of daily consumption during daylight": "Benutzerdefiniert: % des Tagesverbrauchs bei Tageslicht",
        "Backup (optional) — reserve capacity for outage support (added on top of self‑consumption).": "Backup (optional) — zusätzliche Kapazität für Stromausfälle (zum Eigenverbrauch addiert).",
        "Critical load power to support during outage (kW)": "Leistung der kritischen Last während des Ausfalls (kW)",
        "Desired backup duration (hours)": "Gewünschte Backup-Dauer (Stunden)",
        "Advanced assumptions": "Erweiterte Annahmen",
        "Specific yield baseline (kWh/kWp/year)": "Spezifischer Ertrag Basis (kWh/kWp/Jahr)",
        "Round-trip efficiency": "Wirkungsgrad (Lade/Entlade)",
        "Usable depth of discharge": "Nutzbare Entladetiefe",
        "Degradation reserve": "Degradationsreserve",
        "Calculate recommendation": "Empfehlung berechnen",
        "Inverter recommendation": "Wechselrichter-Empfehlung",
        "Estimated PV DC size": "Geschätzte PV-DC-Leistung",
        "Suggested inverter": "Vorgeschlagener Wechselrichter",
        "DC/AC ratio ≈ {ratio} (cap ≤ {cap})": "DC/AC-Verhältnis ≈ {ratio} (Grenze ≤ {cap})",
        "Your DC/AC ratio exceeds the {cap} cap. Consider a larger inverter or less PV DC.": "Ihr DC/AC-Verhältnis überschreitet die Grenze von {cap}. Erwägen Sie einen größeren Wechselrichter oder weniger PV-DC.",
        "Backup power needs {need} kW, which exceeds the selected inverter's AC rating ({ac} kW). Consider the next larger model.": "Für die Backup-Leistung werden {need} kW benötigt, was die AC-Leistung des ausgewählten Wechselrichters ({ac} kW) überschreitet. Erwägen Sie das nächstgrößere Modell.",
        "Battery sizing inputs & rationale": "Batterie-Dimensionierung & Begründung",
        "- Orientation: **{orientation}**; Tilt: **{tilt}°**": "- Ausrichtung: **{orientation}**; Neigung: **{tilt}°**",
        "- Load profile: **{profile}** → daytime **{day}%**, night **{night}%**": "- Lastprofil: **{profile}** → Tag **{day}%**, Nacht **{night}%**",
        "- Typical daily load: **{daily_load:.1f} kWh**; Typical daily PV: **{daily_pv:.1f} kWh** (from {dc_kw:.2f} kW @ {specific_yield:.0f} kWh/kWp/yr)": "- Typische tägliche Last: **{daily_load:.1f} kWh**; Typische tägliche PV: **{daily_pv:.1f} kWh** (aus {dc_kw:.2f} kW @ {specific_yield:.0f} kWh/kWp/Jahr)",
        "- Daytime load: **{day_load:.1f} kWh**; Night load: **{night_load:.1f} kWh**": "- Tageslast: **{day_load:.1f} kWh**; Nachtlast: **{night_load:.1f} kWh**",
        "- Daytime PV surplus: **{surplus:.1f} kWh**; Shiftable to night: **{shiftable:.1f} kWh**": "- PV-Überschuss am Tag: **{surplus:.1f} kWh**; Nachts verschiebbar: **{shiftable:.1f} kWh**",
        "Two-side layout flattens production; surplus reduced by ~10% to reflect less midday clipping and later peaks.": "Zweiseitige Anordnung glättet die Produktion; Überschuss um ~10% reduziert, um weniger Mittagsabsenkung und spätere Spitzen zu berücksichtigen.",
        "- Backup requirement: **{kw:.1f} kW** for **{h:.1f} h** → **{energy:.1f} kWh** energy (reserved)": "- Backup-Anforderung: **{kw:.1f} kW** für **{h:.1f} h** → **{energy:.1f} kWh** Energie (reserviert)",
        "Battery recommendation": "Batterie-Empfehlung",
        "Usable capacity (rounded)": "Nutzbare Kapazität (gerundet)",
        "Suggested battery model": "Vorgeschlagenes Batteriemodell",
        "No battery recommended": "Keine Batterie empfohlen",
        "(Rounded to nearest available size for **{battery_type}**; {battery_step_display})": "(Gerundet auf die nächstverfügbare Größe für **{battery_type}**; {battery_step_display})",
        "Breakdown: **Self‑consumption** ~{self:.1f} kWh + **Backup reserve** ~{backup:.1f} kWh → **Total usable target** ~{total:.1f} kWh": "Aufschlüsselung: **Eigenverbrauch** ~{self:.1f} kWh + **Backup-Reserve** ~{backup:.1f} kWh → **Gesamt nutzbares Ziel** ~{total:.1f} kWh",
        "Your shiftable energy is very small and no backup was requested. A battery may have limited benefit for pure self-consumption.": "Ihre verschiebbare Energie ist sehr gering und es wurde kein Backup angefordert. Eine Batterie könnte nur begrenzten Nutzen für reinen Eigenverbrauch haben.",
        "Sanity checks & notes": "Plausibilitätsprüfungen & Hinweise",
        "- **MPPTs / strings:** {mppts} MPPTs and up to **{strings} strings** (info only).": "- **MPPT / Strings:** {mppts} MPPTs und bis zu **{strings} Strings** (nur Info).",
        "- **Max string current:** ≈ **{current} A** per string (verify with module Imp/Isc).": "- **Max. Stringstrom:** ≈ **{current} A** pro String (mit Modul Imp/Isc prüfen).",
        "- **DC/AC cap:** ≤ {cap}. Aim near 1.2–1.4 for good utilization.": "- **DC/AC-Grenze:** ≤ {cap}. Zielwert 1,2–1,4 für gute Ausnutzung.",
        "- Quick estimate for self-consumption + backup reserve. Tariffs/feed‑in not yet modeled.": "- Schnelle Schätzung für Eigenverbrauch + Backup-Reserve. Tarife/Einspeisung noch nicht modelliert.",
        "Select system, roof layout, **daily load profile** (or custom), optional backup, then click **Calculate recommendation**.": "System, Dachanordnung, **tägliches Lastprofil** (oder benutzerdefiniert), optionales Backup auswählen und dann auf **Empfehlung berechnen** klicken.",
        "south": "süd",
        "southeast": "südost",
        "southwest": "südwest",
        "east": "ost",
        "west": "west",
        "north": "nord",
        "northwest": "nordwest",
        "northeast": "nordost",
    },
    "es": {
        "Language": "Idioma",
        "🔋 Sungrow Battery Sizer — v3.3": "🔋 Dimensionador de Baterías Sungrow — v3.3",
        "Backup capacity is **reserved** on top of self‑consumption. Choose a daily load profile or set a custom split.": "La capacidad de respaldo se **reserva** además del autoconsumo. Elige un perfil de carga diario o establece una división personalizada.",
        "System type": "Tipo de sistema",
        "Your PV & Consumption": "Tu FV y Consumo",
        "Total PV modules installed": "Módulos FV totales instalados",
        "Module wattage (Wp)": "Potencia del módulo (Wp)",
        "Annual electricity consumption (kWh)": "Consumo eléctrico anual (kWh)",
        "Roof layout": "Disposición del techo",
        "Where are the modules placed?": "¿Dónde están ubicados los módulos?",
        "All on one side": "Todos en un lado",
        "Split across two opposite sides": "Divididos en dos lados opuestos",
        "Orientation": "Orientación",
        "Tilt (degrees)": "Inclinación (grados)",
        "Main side orientation": "Orientación del lado principal",
        "Daily load profile": "Perfil de carga diario",
        "Choose a profile": "Elige un perfil",
        "Balanced household (40% day / 60% night)": "Hogar equilibrado (40% día / 60% noche)",
        "Workday away (30% / 70%)": "Día laboral fuera (30% / 70%)",
        "Home most of day (55% / 45%)": "En casa la mayor parte del día (55% / 45%)",
        "Evening peaky (25% / 75%)": "Picos por la tarde (25% / 75%)",
        "Heat pump or daytime loads (50% / 50%)": "Bomba de calor o cargas diurnas (50% / 50%)",
        "Custom…": "Personalizado…",
        "Custom: % of daily consumption during daylight": "Personalizado: % del consumo diario durante el día",
        "Backup (optional) — reserve capacity for outage support (added on top of self‑consumption).": "Respaldo (opcional) — capacidad reservada para cortes (añadida al autoconsumo).",
        "Critical load power to support during outage (kW)": "Potencia de la carga crítica a soportar durante el corte (kW)",
        "Desired backup duration (hours)": "Duración de respaldo deseada (horas)",
        "Advanced assumptions": "Supuestos avanzados",
        "Specific yield baseline (kWh/kWp/year)": "Rendimiento específico base (kWh/kWp/año)",
        "Round-trip efficiency": "Eficiencia de ciclo completo",
        "Usable depth of discharge": "Profundidad de descarga utilizable",
        "Degradation reserve": "Reserva por degradación",
        "Calculate recommendation": "Calcular recomendación",
        "Inverter recommendation": "Recomendación de inversor",
        "Estimated PV DC size": "Tamaño CC FV estimado",
        "Suggested inverter": "Inversor sugerido",
        "DC/AC ratio ≈ {ratio} (cap ≤ {cap})": "Relación CC/CA ≈ {ratio} (límite ≤ {cap})",
        "Your DC/AC ratio exceeds the {cap} cap. Consider a larger inverter or less PV DC.": "Tu relación CC/CA supera el límite de {cap}. Considera un inversor mayor o menos CC FV.",
        "Backup power needs {need} kW, which exceeds the selected inverter's AC rating ({ac} kW). Consider the next larger model.": "Se requieren {need} kW de respaldo, lo que supera la potencia CA del inversor seleccionado ({ac} kW). Considera el siguiente modelo más grande.",
        "Battery sizing inputs & rationale": "Entrada para dimensionamiento de batería y justificación",
        "- Orientation: **{orientation}**; Tilt: **{tilt}°**": "- Orientación: **{orientation}**; Inclinación: **{tilt}°**",
        "- Load profile: **{profile}** → daytime **{day}%**, night **{night}%**": "- Perfil de carga: **{profile}** → día **{day}%**, noche **{night}%**",
        "- Typical daily load: **{daily_load:.1f} kWh**; Typical daily PV: **{daily_pv:.1f} kWh** (from {dc_kw:.2f} kW @ {specific_yield:.0f} kWh/kWp/yr)": "- Carga diaria típica: **{daily_load:.1f} kWh**; FV diaria típica: **{daily_pv:.1f} kWh** (de {dc_kw:.2f} kW @ {specific_yield:.0f} kWh/kWp/año)",
        "- Daytime load: **{day_load:.1f} kWh**; Night load: **{night_load:.1f} kWh**": "- Carga diurna: **{day_load:.1f} kWh**; Carga nocturna: **{night_load:.1f} kWh**",
        "- Daytime PV surplus: **{surplus:.1f} kWh**; Shiftable to night: **{shiftable:.1f} kWh**": "- Excedente FV diurno: **{surplus:.1f} kWh**; Transferible a la noche: **{shiftable:.1f} kWh**",
        "Two-side layout flattens production; surplus reduced by ~10% to reflect less midday clipping and later peaks.": "La disposición en dos lados aplana la producción; el excedente se reduce ~10% para reflejar menos recortes al mediodía y picos más tardíos.",
        "- Backup requirement: **{kw:.1f} kW** for **{h:.1f} h** → **{energy:.1f} kWh** energy (reserved)": "- Requisito de respaldo: **{kw:.1f} kW** durante **{h:.1f} h** → **{energy:.1f} kWh** de energía (reservada)",
        "Battery recommendation": "Recomendación de batería",
        "Usable capacity (rounded)": "Capacidad utilizable (redondeada)",
        "Suggested battery model": "Modelo de batería sugerido",
        "No battery recommended": "No se recomienda batería",
        "(Rounded to nearest available size for **{battery_type}**; {battery_step_display})": "(Redondeado al tamaño disponible más cercano para **{battery_type}**; {battery_step_display})",
        "Breakdown: **Self‑consumption** ~{self:.1f} kWh + **Backup reserve** ~{backup:.1f} kWh → **Total usable target** ~{total:.1f} kWh": "Desglose: **Autoconsumo** ~{self:.1f} kWh + **Reserva de respaldo** ~{backup:.1f} kWh → **Objetivo utilizable total** ~{total:.1f} kWh",
        "Your shiftable energy is very small and no backup was requested. A battery may have limited benefit for pure self-consumption.": "Tu energía desplazable es muy pequeña y no se solicitó respaldo. Una batería puede tener beneficio limitado para autoconsumo puro.",
        "Sanity checks & notes": "Comprobaciones y notas",
        "- **MPPTs / strings:** {mppts} MPPTs and up to **{strings} strings** (info only).": "- **MPPT / cadenas:** {mppts} MPPT y hasta **{strings} cadenas** (solo info).",
        "- **Max string current:** ≈ **{current} A** per string (verify with module Imp/Isc).": "- **Corriente máxima de cadena:** ≈ **{current} A** por cadena (verificar con Imp/Isc del módulo).",
        "- **DC/AC cap:** ≤ {cap}. Aim near 1.2–1.4 for good utilization.": "- **Límite CC/CA:** ≤ {cap}. Apunta a 1.2–1.4 para una buena utilización.",
        "- Quick estimate for self-consumption + backup reserve. Tariffs/feed‑in not yet modeled.": "- Estimación rápida para autoconsumo + reserva de respaldo. Tarifas/inyección aún no modeladas.",
        "Select system, roof layout, **daily load profile** (or custom), optional backup, then click **Calculate recommendation**.": "Selecciona sistema, disposición del techo, **perfil de carga diario** (o personalizado), respaldo opcional, luego haz clic en **Calcular recomendación**.",
        "south": "sur",
        "southeast": "sureste",
        "southwest": "suroeste",
        "east": "este",
        "west": "oeste",
        "north": "norte",
        "northwest": "noroeste",
        "northeast": "noreste",
    },
}


def t(key: str) -> str:
    return TRANSLATIONS.get(st.session_state.get("lang", "en"), {}).get(key, key)

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



# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Sungrow Battery Sizer (v3.3)", layout="centered")

# Language selection
default_lang = st.session_state.get("lang", "en")
st.title(t("🔋 Sungrow Battery Sizer — v3.3"))
lang_choice = st.selectbox(t("Language"), list(LANGUAGES.keys()), index=list(LANGUAGES.values()).index(default_lang))
st.session_state["lang"] = LANGUAGES[lang_choice]

st.caption(t("Backup capacity is **reserved** on top of self‑consumption. Choose a daily load profile or set a custom split."))

system_key = st.selectbox(t("System type"), list(SYSTEMS.keys()), index=0)
SYS = SYSTEMS[system_key]

with st.form("inputs"):
    st.subheader(t("Your PV & Consumption"))
    colA, colB = st.columns(2)
    total_modules = colA.number_input(t("Total PV modules installed"), min_value=1, max_value=300, value=16, step=1)
    module_wp = colB.number_input(t("Module wattage (Wp)"), min_value=250, max_value=700, value=430, step=5)

    annual_kwh = st.number_input(t("Annual electricity consumption (kWh)"), min_value=500, max_value=50000, value=5000, step=100)

    st.markdown(f"**{t('Roof layout')}**")
    layout_opts = ["All on one side", "Split across two opposite sides"]
    layout_labels = [t(o) for o in layout_opts]
    layout_choice_label = st.radio(t("Where are the modules placed?"), layout_labels, index=0, horizontal=False)
    layout_choice = layout_opts[layout_labels.index(layout_choice_label)]

    if layout_choice == "All on one side":
        col3, col4 = st.columns(2)
        orient_keys = ["south", "southeast", "southwest", "east", "west", "north"]
        orient_labels = [t(o) for o in orient_keys]
        orient_label = col3.selectbox(t("Orientation"), options=orient_labels, index=0)
        orientation_single = orient_keys[orient_labels.index(orient_label)]
        tilt = col4.number_input(t("Tilt (degrees)"), min_value=0, max_value=90, value=30, step=1)
        orient_fac = orientation_factor(orientation_single)
        profile_flatten = 1.0
        orientation_text = t(orientation_single)
    else:
        col3, col4 = st.columns(2)
        orient_keys = ["east", "west", "south", "southeast", "southwest", "north"]
        orient_labels = [t(o) for o in orient_keys]
        orient_label_a = col3.selectbox(t("Main side orientation"), options=orient_labels, index=0)
        orientation_side_a = orient_keys[orient_labels.index(orient_label_a)]
        tilt = col4.number_input(t("Tilt (degrees)"), min_value=0, max_value=90, value=30, step=1)
        orientation_side_b = opposite_orientation(orientation_side_a)
        orient_fac = 0.5 * (orientation_factor(orientation_side_a) + orientation_factor(orientation_side_b))
        profile_flatten = 0.90  # flatter production curve
        orientation_text = f"{t(orientation_side_a)} + {t(orientation_side_b)}"

    # Load profile selection
    st.markdown(f"**{t('Daily load profile')}**")
    profile_keys = list(LOAD_PROFILES.keys())
    profile_labels = [t(p) for p in profile_keys]
    profile_choice_label = st.selectbox(t("Choose a profile"), profile_labels, index=0)
    profile_choice = profile_keys[profile_labels.index(profile_choice_label)]
    if LOAD_PROFILES[profile_choice] is None:
        day_fraction = st.slider(t("Custom: % of daily consumption during daylight"), min_value=0.2, max_value=0.8, value=0.40, step=0.05)
    else:
        day_fraction = LOAD_PROFILES[profile_choice]

    # Backup (optional)
    st.markdown(t("Backup (optional) — reserve capacity for outage support (added on top of self‑consumption)."))
    col5, col6 = st.columns(2)
    backup_kw = col5.number_input(t("Critical load power to support during outage (kW)"), min_value=0.0, max_value=30.0, value=0.0, step=0.5)
    backup_hours = col6.number_input(t("Desired backup duration (hours)"), min_value=0.0, max_value=48.0, value=0.0, step=0.5)

    # Advanced (optional)
    with st.expander(t("Advanced assumptions")):
        region_yield = st.number_input(t("Specific yield baseline (kWh/kWp/year)"), min_value=700, max_value=1500, value=DEFAULT_YIELD_PER_KWP_YR, step=10)
        rte = st.slider(t("Round-trip efficiency"), min_value=0.80, max_value=0.98, value=DEFAULT_RTE, step=0.01)
        dod = st.slider(t("Usable depth of discharge"), min_value=0.80, max_value=0.98, value=DEFAULT_DOD, step=0.01)
        degradation = st.slider(t("Degradation reserve"), min_value=0.05, max_value=0.20, value=DEFAULT_DEGRADATION_RESERVE, step=0.01)

    submitted = st.form_submit_button(t("Calculate recommendation"))

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
    st.subheader(t("Inverter recommendation"))
    colr1, colr2 = st.columns(2)
    with colr1:
        st.metric(t("Estimated PV DC size"), f"{dc_kw:.2f} kW")
    with colr2:
        st.metric(t("Suggested inverter"), inv_choice["model"], help=t("DC/AC ratio ≈ {ratio} (cap ≤ {cap})").format(ratio=inv_choice["dc_ac_ratio"], cap=SYS["max_dc_ac_ratio"]))
    if not inv_choice["within_cap"]:
        st.warning(t("Your DC/AC ratio exceeds the {cap} cap. Consider a larger inverter or less PV DC.").format(cap=SYS['max_dc_ac_ratio']))
    if backup_kw > 0 and inv_choice["ac_kw"] < backup_kw:
        st.warning(t("Backup power needs {need} kW, which exceeds the selected inverter's AC rating ({ac} kW). Consider the next larger model.").format(need=backup_kw, ac=inv_choice['ac_kw']))

    st.markdown("---")
    st.subheader(t("Battery sizing inputs & rationale"))
    st.write(t("- Orientation: **{orientation}**; Tilt: **{tilt}°**").format(orientation=orientation_text, tilt=tilt))
    st.write(t("- Load profile: **{profile}** → daytime **{day}%**, night **{night}%**").format(profile=t(profile_choice), day=day_fraction*100, night=(1-day_fraction)*100))
    st.write(t("- Typical daily load: **{daily_load:.1f} kWh**; Typical daily PV: **{daily_pv:.1f} kWh** (from {dc_kw:.2f} kW @ {specific_yield:.0f} kWh/kWp/yr)").format(daily_load=comp['daily_load'], daily_pv=comp['daily_pv'], dc_kw=dc_kw, specific_yield=specific_yield))
    st.write(t("- Daytime load: **{day_load:.1f} kWh**; Night load: **{night_load:.1f} kWh**").format(day_load=comp['day_load'], night_load=comp['night_load']))
    st.write(t("- Daytime PV surplus: **{surplus:.1f} kWh**; Shiftable to night: **{shiftable:.1f} kWh**").format(surplus=comp['surplus_day'], shiftable=comp['shiftable']))
    if layout_choice == "Split across two opposite sides":
        st.caption(t("Two-side layout flattens production; surplus reduced by ~10% to reflect less midday clipping and later peaks."))
    if backup_kw > 0 and backup_hours > 0:
        st.write(t("- Backup requirement: **{kw:.1f} kW** for **{h:.1f} h** → **{energy:.1f} kWh** energy (reserved)").format(kw=backup_kw, h=backup_hours, energy=comp['backup_energy']))

    # Battery section styled like inverter (metrics) + breakdown
    st.markdown("---")
    st.subheader(t("Battery recommendation"))
    colb1, colb2 = st.columns(2)
    with colb1:
        if rec_kwh == 0:
            st.metric(t("Usable capacity (rounded)"), "—")
        else:
            st.metric(t("Usable capacity (rounded)"), f"{rec_kwh:.1f} kWh")
    with colb2:
        if rec_kwh == 0:
            st.metric(t("Suggested battery model"), t("No battery recommended"))
        else:
            st.metric(t("Suggested battery model"), rec_label)

    if rec_kwh > 0:
        st.caption(t("(Rounded to nearest available size for **{battery_type}**; {battery_step_display})").format(battery_type=SYS['battery_type'], battery_step_display=SYS['battery_step_display']))
        st.write(t("Breakdown: **Self‑consumption** ~{self:.1f} kWh + **Backup reserve** ~{backup:.1f} kWh → **Total usable target** ~{total:.1f} kWh").format(self=comp['shiftable'], backup=comp['backup_energy'], total=usable_needed))
    else:
        st.info(t("Your shiftable energy is very small and no backup was requested. A battery may have limited benefit for pure self-consumption."))

    st.markdown("---")
    st.subheader(t("Sanity checks & notes"))
    st.write(t("- **MPPTs / strings:** {mppts} MPPTs and up to **{strings} strings** (info only)." ).format(mppts=SYS['mppts'], strings=SYS['max_strings_total']))
    st.write(t("- **Max string current:** ≈ **{current} A** per string (verify with module Imp/Isc)." ).format(current=SYS['max_string_current_a']))
    st.write(t("- **DC/AC cap:** ≤ {cap}. Aim near 1.2–1.4 for good utilization.").format(cap=SYS['max_dc_ac_ratio']))
    st.write(t("- Quick estimate for self-consumption + backup reserve. Tariffs/feed‑in not yet modeled."))

else:
    st.info(t("Select system, roof layout, **daily load profile** (or custom), optional backup, then click **Calculate recommendation**."))
