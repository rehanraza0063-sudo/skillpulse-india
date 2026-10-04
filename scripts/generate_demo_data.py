"""
SkillPulse India - DEMO DATA GENERATOR
=======================================
Generates the FICTIONAL / ILLUSTRATIVE dataset used by the prototype.

IMPORTANT: Every number produced here is synthetic demo data.
It is NOT sourced from PLFS, NCS, e-Shram, MSDE, NSQF or any official dataset.
Every row carries source_type = DEMO.

Run:  python scripts/generate_demo_data.py
Output: ../data/*.csv and ../data/*.json  (and a copy in backend/app/data)
"""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data"
OUT.mkdir(exist_ok=True)
rng = np.random.default_rng(42)
YEARS = [2023, 2024, 2025, 2026]
SRC = "DEMO"

# ---------------------------------------------------------------- districts
# Names follow current official naming (Chhatrapati Sambhajinagar, not Aurangabad).
# Navi Mumbai is a municipal-corporation area (not a separate district); the demo
# treats it as a planning zone and says so in the notes column.
DISTRICTS = [
    ("D01", "Mumbai", 19.0760, 72.8777, "Konkan", 0.16, "Demo planning district"),
    ("D02", "Thane", 19.2183, 72.9781, "Konkan", 0.12, "Demo planning district"),
    ("D03", "Navi Mumbai", 19.0330, 73.0297, "Konkan", 0.08, "Urban area treated as a demo planning zone (not a separate district)"),
    ("D04", "Pune", 18.5204, 73.8567, "Western Maharashtra", 0.22, "Demo planning district"),
    ("D05", "Nashik", 19.9975, 73.7898, "North Maharashtra", 0.08, "Demo planning district"),
    ("D06", "Nagpur", 21.1458, 79.0882, "Vidarbha", 0.10, "Demo planning district"),
    ("D07", "Chhatrapati Sambhajinagar", 19.8762, 75.3433, "Marathwada", 0.10, "Demo planning district"),
    ("D08", "Kolhapur", 16.7050, 74.2433, "Western Maharashtra", 0.06, "Demo planning district"),
    ("D09", "Satara", 17.6805, 74.0183, "Western Maharashtra", 0.04, "Demo planning district"),
    ("D10", "Solapur", 17.6599, 75.9064, "Western Maharashtra", 0.04, "Demo planning district"),
]
D_IDS = [d[0] for d in DISTRICTS]
D_NAME = {d[0]: d[1] for d in DISTRICTS}
D_W = {d[0]: d[5] for d in DISTRICTS}

# --------------------------------------------------------------- industries
INDUSTRIES = [
    ("I01", "EV / Battery", "GROWING", "GROWING", 0.85, "Demo signal: rising EV hiring and charging build-out (illustrative)"),
    ("I02", "Electronics", "GROWING", "GROWING", 0.55, "Demo signal: electronics assembly and embedded roles expanding (illustrative)"),
    ("I03", "Renewable Energy", "GROWING", "GROWING", 0.70, "Demo signal: solar and grid roles expanding (illustrative)"),
    ("I04", "Healthcare Technology", "GROWING", "GROWING", 0.60, "Demo signal: diagnostics and health-data roles expanding (illustrative)"),
    ("I05", "Traditional ICE Automotive", "DECLINING", "DECLINING", -0.60, "Demo signal: ICE service demand shrinking as EV share rises (illustrative)"),
    ("I06", "Textiles & Garments", "DECLINING", "DECLINING", -0.45, "Demo signal: manual machine-operator demand shrinking (illustrative)"),
    ("I07", "IT Services", "STABLE", "STABLE", 0.20, "Demo signal: steady hiring with moderate growth (illustrative)"),
    ("I08", "General Manufacturing", "STABLE", "STABLE", 0.10, "Demo signal: flat to slowly rising demand (illustrative)"),
]

# ------------------------------------------------------------------- skills
# (id, name, industry, 2026 statewide demand, history 2023-2026, 2026 coverage cap/demand)
SKILLS = [
    ("S01", "EV Technician", "I01", 6300, [2100, 3200, 4800, 6300], 0.952),
    ("S02", "Battery Assembly", "I01", 2600, [900, 1300, 1900, 2600], 0.85),
    ("S03", "ICE Automotive Service", "I05", 8800, [11200, 10600, 9800, 8800], 1.18),
    ("S04", "Electronics Assembly", "I02", 7200, [5100, 5800, 6500, 7200], 0.95),
    ("S05", "Embedded Systems", "I02", 2400, [1300, 1700, 2000, 2400], 0.80),
    ("S06", "Solar PV Installation", "I03", 3900, [1800, 2500, 3200, 3900], 0.85),
    ("S07", "Grid & Substation Electrical", "I03", 2100, [1500, 1700, 1900, 2100], 0.97),
    ("S08", "Medical Imaging", "I04", 2800, [1900, 2200, 2500, 2800], 0.92),
    ("S09", "Health Informatics", "I04", 1700, [700, 1000, 1350, 1700], 0.80),
    ("S10", "Data Analytics", "I07", 5200, [3900, 4300, 4750, 5200], 0.96),
    ("S11", "Cloud Support", "I07", 4600, [3800, 4100, 4350, 4600], 1.02),
    ("S12", "Textile Machine Operation", "I06", 9500, [12200, 11500, 10500, 9500], 1.20),
    ("S13", "Welding & Fabrication", "I08", 6100, [5800, 5900, 6000, 6100], 1.00),
    ("S14", "Industrial Automation (PLC)", "I08", 3300, [2000, 2400, 2850, 3300], 0.88),
    ("S15", "CNC Machining", "I08", 5000, [4400, 4600, 4800, 5000], 1.05),
]
S_BY_ID = {s[0]: s for s in SKILLS}
SKILL_DESC = {
    "S01": "Service, diagnosis and repair of electric vehicles and their high-voltage systems",
    "S02": "Assembly and testing of battery modules and packs",
    "S03": "Service and repair of internal-combustion-engine vehicles",
    "S04": "Assembly and rework of electronic boards and products",
    "S05": "Firmware and hardware bring-up for embedded devices",
    "S06": "Installation and commissioning of solar PV systems",
    "S07": "Installation, testing and protection of grid and substation equipment",
    "S08": "Operation of diagnostic imaging equipment",
    "S09": "Handling and analysis of patient and health-facility data",
    "S10": "Data cleaning, analysis and visualisation",
    "S11": "Cloud platform support and incident handling",
    "S12": "Operation of textile and garment machinery",
    "S13": "Welding and metal fabrication",
    "S14": "PLC / SCADA based industrial automation",
    "S15": "CNC machine setup and operation",
}

# ------------------------------------------------------------- occupations
# (id, name, skill_id)
OCCUPATIONS = [
    ("O01", "EV Technician", "S01"),
    ("O02", "EV Charging Infrastructure Installer", "S01"),
    ("O03", "Battery Pack Assembler", "S02"),
    ("O04", "ICE Technician", "S03"),
    ("O05", "Two-Wheeler Mechanic (ICE)", "S03"),
    ("O06", "Electronics Assembly Technician", "S04"),
    ("O07", "PCB Rework Technician", "S04"),
    ("O08", "Embedded Systems Technician", "S05"),
    ("O09", "Solar PV Installer", "S06"),
    ("O10", "Grid & Substation Electrician", "S07"),
    ("O11", "Medical Imaging Technician", "S08"),
    ("O12", "Health Informatics Assistant", "S09"),
    ("O13", "Data Analyst", "S10"),
    ("O14", "Cloud Support Engineer", "S11"),
    ("O15", "Textile Machine Operator", "S12"),
    ("O16", "Garment Line Operator", "S12"),
    ("O17", "Welding & Fabrication Technician", "S13"),
    ("O18", "Industrial Automation Technician", "S14"),
    ("O19", "CNC Machinist", "S15"),
]

# ------------------------------------------------------ competency taxonomy
# canonical name -> (category, bridge_hours, [aliases])
COMPETENCIES = {
    "Electrical Systems": ("Electrical", 40, ["electrical systems", "electrical system", "electrical work", "wiring", "electrical maintenance", "electrical fundamentals"]),
    "Vehicle Diagnostics": ("Automotive", 40, ["vehicle diagnostics", "diagnostics", "ev diagnostics", "electric vehicle diagnostics", "fault diagnosis", "vehicle fault finding", "obd diagnostics", "automotive diagnostics"]),
    "Mechanical Maintenance": ("Mechanical", 40, ["mechanical maintenance", "mechanical repair", "preventive maintenance", "mechanical servicing"]),
    "Workplace Safety": ("Safety", 16, ["workplace safety", "safety", "safety procedures", "industrial safety", "occupational safety", "ohs"]),
    "High Voltage Safety": ("Safety", 40, ["high voltage safety", "high-voltage safety", "hv safety", "ev safety", "electric vehicle safety", "high voltage handling"]),
    "Battery Systems": ("Battery", 60, ["battery systems", "battery technology", "battery pack", "lithium-ion batteries", "li-ion batteries", "battery maintenance"]),
    "Battery Management System": ("Battery", 50, ["battery management system", "battery management systems", "battery management", "bms"]),
    "High Voltage Diagnostics": ("Automotive", 50, ["high voltage diagnostics", "high-voltage diagnostics", "hv diagnostics", "hv fault diagnosis"]),
    "Engine Systems": ("Automotive", 60, ["engine systems", "engine repair", "engine overhaul", "ic engine", "internal combustion engine"]),
    "Fuel Injection & Emission Control": ("Automotive", 40, ["fuel injection", "emission control", "exhaust systems", "fuel systems"]),
    "Transmission & Drivetrain": ("Automotive", 40, ["transmission", "drivetrain", "gearbox", "clutch systems"]),
    "Charging Infrastructure": ("Electrical", 50, ["charging infrastructure", "ev charging", "charger installation", "charging stations", "evse"]),
    "Electrical Testing": ("Electrical", 30, ["electrical testing", "insulation testing", "megger testing", "commissioning tests"]),
    "Grid Connection & Protection": ("Electrical", 50, ["grid connection", "grid protection", "relay protection", "substation protection", "net metering"]),
    "Solar PV Installation": ("Renewable", 60, ["solar pv installation", "solar installation", "solar panel installation", "rooftop solar", "photovoltaic installation"]),
    "Soldering & Rework": ("Electronics", 30, ["soldering", "rework", "soldering and rework", "smd rework", "desoldering"]),
    "PCB Assembly": ("Electronics", 40, ["pcb assembly", "smt assembly", "board assembly", "circuit board assembly"]),
    "Embedded C Programming": ("Electronics", 80, ["embedded c", "embedded programming", "firmware development", "c programming for microcontrollers"]),
    "Microcontroller Interfacing": ("Electronics", 60, ["microcontroller interfacing", "microcontrollers", "arduino", "stm32", "sensor interfacing"]),
    "Sensors & Instrumentation": ("Automation", 40, ["sensors", "instrumentation", "sensors and instrumentation", "process instrumentation"]),
    "PLC Programming": ("Automation", 80, ["plc programming", "plc", "ladder logic", "plc ladder programming"]),
    "SCADA & HMI": ("Automation", 50, ["scada", "hmi", "scada and hmi", "scada systems"]),
    "CNC Operation": ("Manufacturing", 60, ["cnc operation", "cnc machining", "cnc programming", "cnc setup"]),
    "CAD/CAM Basics": ("Manufacturing", 40, ["cad", "cam", "cad/cam", "cad cam basics", "computer aided design"]),
    "Blueprint Reading": ("Manufacturing", 20, ["blueprint reading", "drawing interpretation", "engineering drawings", "reading technical drawings"]),
    "Welding Techniques": ("Manufacturing", 60, ["welding", "welding techniques", "mig welding", "tig welding", "arc welding"]),
    "Quality Inspection": ("Manufacturing", 30, ["quality inspection", "quality control", "inspection and testing", "qc checks"]),
    "Medical Imaging Operation": ("Healthcare", 80, ["medical imaging", "x-ray operation", "ct scan operation", "mri operation", "radiography", "imaging equipment operation"]),
    "Radiation Safety": ("Healthcare", 30, ["radiation safety", "radiation protection", "dose management"]),
    "Patient Data Handling": ("Healthcare", 30, ["patient data handling", "health records", "medical records", "electronic health records", "ehr"]),
    "Spreadsheet Analysis": ("Data", 30, ["spreadsheet analysis", "excel", "spreadsheets", "advanced excel"]),
    "SQL": ("Data", 40, ["sql", "database queries", "sql queries", "structured query language"]),
    "Python": ("Data", 60, ["python", "python scripting", "python programming"]),
    "Data Visualization": ("Data", 40, ["data visualization", "data visualisation", "dashboards", "power bi", "tableau"]),
    "Cloud Platforms": ("IT", 60, ["cloud platforms", "cloud computing", "aws", "azure", "gcp", "cloud services"]),
    "Linux Administration": ("IT", 50, ["linux", "linux administration", "shell scripting", "unix"]),
    "Networking Basics": ("IT", 40, ["networking", "networking basics", "tcp/ip", "network troubleshooting"]),
    "Ticketing & Incident Management": ("IT", 20, ["ticketing", "incident management", "service desk", "ticketing and incident management"]),
    "Textile Machine Operation": ("Textile", 40, ["textile machine operation", "loom operation", "spinning machine operation", "knitting machine operation"]),
    "Loom Maintenance": ("Textile", 40, ["loom maintenance", "loom repair", "textile machine maintenance"]),
    "Garment Stitching": ("Textile", 30, ["garment stitching", "sewing machine operation", "stitching", "garment assembly"]),
}

# occupation -> {competency: weight 1..3}
REQ = {
    "EV Technician": {"Electrical Systems": 3, "Vehicle Diagnostics": 3, "Workplace Safety": 2, "High Voltage Safety": 3, "Battery Systems": 3, "Battery Management System": 3, "High Voltage Diagnostics": 3},
    "EV Charging Infrastructure Installer": {"Electrical Systems": 3, "Workplace Safety": 2, "High Voltage Safety": 3, "Charging Infrastructure": 3, "Electrical Testing": 2, "Grid Connection & Protection": 1},
    "Battery Pack Assembler": {"Battery Systems": 3, "Soldering & Rework": 2, "Workplace Safety": 2, "High Voltage Safety": 2, "Quality Inspection": 2, "Electrical Systems": 1},
    "ICE Technician": {"Electrical Systems": 2, "Vehicle Diagnostics": 3, "Mechanical Maintenance": 3, "Workplace Safety": 2, "Engine Systems": 3, "Fuel Injection & Emission Control": 2, "Transmission & Drivetrain": 2},
    "Two-Wheeler Mechanic (ICE)": {"Mechanical Maintenance": 3, "Engine Systems": 3, "Vehicle Diagnostics": 2, "Workplace Safety": 2, "Transmission & Drivetrain": 2, "Electrical Systems": 1},
    "Electronics Assembly Technician": {"Soldering & Rework": 3, "PCB Assembly": 3, "Quality Inspection": 2, "Workplace Safety": 1, "Electrical Systems": 2, "Blueprint Reading": 1},
    "PCB Rework Technician": {"Soldering & Rework": 3, "PCB Assembly": 2, "Quality Inspection": 2, "Electrical Testing": 2},
    "Embedded Systems Technician": {"Embedded C Programming": 3, "Microcontroller Interfacing": 3, "Electrical Systems": 2, "Sensors & Instrumentation": 2, "Soldering & Rework": 1},
    "Solar PV Installer": {"Solar PV Installation": 3, "Electrical Systems": 2, "Workplace Safety": 2, "Electrical Testing": 2, "Grid Connection & Protection": 2},
    "Grid & Substation Electrician": {"Electrical Systems": 3, "Grid Connection & Protection": 3, "Electrical Testing": 3, "High Voltage Safety": 3, "Workplace Safety": 2},
    "Medical Imaging Technician": {"Medical Imaging Operation": 3, "Radiation Safety": 3, "Patient Data Handling": 2, "Workplace Safety": 1},
    "Health Informatics Assistant": {"Patient Data Handling": 3, "Spreadsheet Analysis": 2, "SQL": 2, "Data Visualization": 1},
    "Data Analyst": {"SQL": 3, "Python": 2, "Data Visualization": 3, "Spreadsheet Analysis": 2},
    "Cloud Support Engineer": {"Cloud Platforms": 3, "Linux Administration": 3, "Networking Basics": 2, "Ticketing & Incident Management": 2},
    "Textile Machine Operator": {"Textile Machine Operation": 3, "Loom Maintenance": 2, "Quality Inspection": 2, "Workplace Safety": 1, "Mechanical Maintenance": 1},
    "Garment Line Operator": {"Garment Stitching": 3, "Quality Inspection": 2, "Workplace Safety": 1, "Textile Machine Operation": 1},
    "Welding & Fabrication Technician": {"Welding Techniques": 3, "Blueprint Reading": 2, "Quality Inspection": 2, "Workplace Safety": 2, "Mechanical Maintenance": 1},
    "Industrial Automation Technician": {"PLC Programming": 3, "Sensors & Instrumentation": 3, "Electrical Systems": 2, "SCADA & HMI": 2, "Mechanical Maintenance": 1, "Workplace Safety": 1},
    "CNC Machinist": {"CNC Operation": 3, "Blueprint Reading": 3, "CAD/CAM Basics": 2, "Quality Inspection": 2, "Mechanical Maintenance": 1, "Workplace Safety": 1},
}

# similarity pairs used for partial credit (symmetric, 0..1) - illustrative expert-style weights
SIMILARITY = [
    ("Workplace Safety", "High Voltage Safety", 0.4),
    ("Vehicle Diagnostics", "High Voltage Diagnostics", 0.5),
    ("Electrical Systems", "Battery Systems", 0.3),
    ("Battery Systems", "Battery Management System", 0.4),
    ("Electrical Systems", "Charging Infrastructure", 0.3),
    ("Electrical Systems", "Electrical Testing", 0.5),
    ("Electrical Systems", "Grid Connection & Protection", 0.3),
    ("Solar PV Installation", "Grid Connection & Protection", 0.3),
    ("Soldering & Rework", "PCB Assembly", 0.5),
    ("Sensors & Instrumentation", "PLC Programming", 0.3),
    ("Embedded C Programming", "Microcontroller Interfacing", 0.4),
    ("Spreadsheet Analysis", "SQL", 0.3),
    ("Spreadsheet Analysis", "Data Visualization", 0.4),
    ("SQL", "Python", 0.2),
    ("Textile Machine Operation", "Loom Maintenance", 0.4),
    ("Mechanical Maintenance", "Loom Maintenance", 0.4),
    ("Linux Administration", "Networking Basics", 0.3),
    ("Welding Techniques", "Mechanical Maintenance", 0.2),
    ("PLC Programming", "SCADA & HMI", 0.4),
    ("Garment Stitching", "Textile Machine Operation", 0.4),
]

BRIDGE_PROGRAMMES = [
    {
        "programme_id": "BP01",
        "name": "EV Bridge Training (ICE to EV)",
        "from_occupation": "ICE Technician",
        "to_occupation": "EV Technician",
        "duration_weeks": 8,
        "modules": ["High Voltage Safety", "Battery Systems", "Battery Management System", "High Voltage Diagnostics"],
        "note": "Illustrative programme design for the prototype - not an approved curriculum",
    },
    {
        "programme_id": "BP02",
        "name": "EV Bridge Training (Two-Wheeler to EV)",
        "from_occupation": "Two-Wheeler Mechanic (ICE)",
        "to_occupation": "EV Technician",
        "duration_weeks": 10,
        "modules": ["High Voltage Safety", "Battery Systems", "Battery Management System", "High Voltage Diagnostics", "Electrical Systems"],
        "note": "Illustrative programme design for the prototype - not an approved curriculum",
    },
    {
        "programme_id": "BP03",
        "name": "Textile Operator to Electronics Assembly Bridge",
        "from_occupation": "Textile Machine Operator",
        "to_occupation": "Electronics Assembly Technician",
        "duration_weeks": 8,
        "modules": ["Soldering & Rework", "PCB Assembly", "Electrical Systems"],
        "note": "Illustrative programme design for the prototype - not an approved curriculum",
    },
]


# --------------------------------------------------------------- generators
def write(df, name):
    df.to_csv(OUT / name, index=False)
    print(f"  {name}: {len(df)} rows")


def build_districts():
    df = pd.DataFrame(DISTRICTS, columns=["district_id", "district_name", "latitude", "longitude", "region", "base_weight", "notes"])
    df["source_type"] = SRC
    return df


def build_industries():
    df = pd.DataFrame(INDUSTRIES, columns=["industry_id", "industry_name", "current_outlook", "future_outlook", "signal_score", "signal_note"])
    df["source_type"] = SRC
    return df


def build_skills():
    df = pd.DataFrame([(s[0], s[1], s[2], SKILL_DESC[s[0]]) for s in SKILLS], columns=["skill_id", "skill_name", "industry_id", "description"])
    df["source_type"] = SRC
    return df


def build_occupations():
    rows = []
    for oid, name, sid in OCCUPATIONS:
        rows.append((oid, name, sid, S_BY_ID[sid][2], "PENDING - to be mapped to NCO-2015"))
    df = pd.DataFrame(rows, columns=["occupation_id", "occupation_name", "skill_id", "industry_id", "nco_mapping"])
    df["source_type"] = SRC
    return df


# hand-tuned district multipliers (relative to base weight) to make the geography plausible
AFFINITY = {
    "S03": {"D04": 1.3, "D07": 1.3, "D05": 1.2},
    "S04": {"D02": 1.4, "D03": 1.3, "D04": 1.2},
    "S05": {"D04": 1.8, "D01": 1.2},
    "S06": {"D05": 1.5, "D07": 1.5, "D06": 1.2, "D10": 2.0},
    "S07": {"D06": 1.5, "D01": 1.2},
    "S08": {"D01": 1.6, "D06": 1.5, "D04": 1.2},
    "S09": {"D01": 1.5, "D06": 1.5, "D04": 1.3},
    "S10": {"D04": 1.8, "D01": 1.4, "D06": 0.8, "D08": 0.5, "D09": 0.5, "D10": 0.5},
    "S11": {"D04": 1.9, "D01": 1.4, "D03": 1.3, "D08": 0.4, "D09": 0.4, "D10": 0.4},
    "S12": {"D10": 3.5, "D08": 3.0, "D02": 1.5, "D07": 1.2, "D04": 0.5, "D01": 0.4},
    "S13": {"D07": 1.4, "D04": 1.3, "D05": 1.3},
    "S14": {"D04": 1.4, "D05": 1.3, "D07": 1.3},
    "S15": {"D07": 1.5, "D04": 1.4, "D05": 1.2},
}

# EV Technician (S01) is hand-specified so the demo storyline is exact:
# Pune demand 1000 vs capacity 700 (shortage); Nashik demand 380 vs capacity 620 (surplus).
EV_2026 = {
    "D01": (900, 800), "D02": (700, 650), "D03": (650, 500), "D04": (1000, 700), "D05": (380, 620),
    "D06": (650, 700), "D07": (800, 750), "D08": (400, 520), "D09": (370, 380), "D10": (450, 380),
}


def build_demand_and_capacity():
    dem_rows, cap_rows = [], []
    for sid, name, ind, d26, hist, cov in SKILLS:
        # district shares
        if sid == "S01":
            shares = {d: EV_2026[d][0] / sum(v[0] for v in EV_2026.values()) for d in D_IDS}
        else:
            raw = {d: D_W[d] * AFFINITY.get(sid, {}).get(d, 1.0) for d in D_IDS}
            tot = sum(raw.values())
            shares = {d: raw[d] / tot for d in D_IDS}
        for d in D_IDS:
            noise_free = sid == "S01"
            # demand history
            for yi, y in enumerate(YEARS):
                val = hist[yi] * shares[d]
                if not noise_free and y != 2026:
                    val *= 1 + rng.normal(0, 0.02)
                dem_rows.append((d, sid, y, int(round(val)), SRC))
            # 2026 anchor
            if sid == "S01":
                d26_d = EV_2026[d][0]
                c26_d = EV_2026[d][1]
            else:
                d26_d = int(round(hist[3] * shares[d]))
                c26_d = int(round(d26_d * cov * rng.uniform(0.78, 1.22)))
            # make the 2026 row exactly the anchor
            for i, r in enumerate(dem_rows):
                if r[0] == d and r[1] == sid and r[2] == 2026:
                    dem_rows[i] = (d, sid, 2026, d26_d, SRC)
            cap_factors = [0.60, 0.72, 0.86, 1.0] if sid == "S01" else (
                [1.04, 1.03, 1.01, 1.0] if cov > 1.1 else [0.88, 0.92, 0.96, 1.0])
            for yi, y in enumerate(YEARS):
                c = c26_d * cap_factors[yi]
                if y != 2026 and sid != "S01":
                    c *= 1 + rng.normal(0, 0.015)
                cap_rows.append((d, sid, y, int(round(c)), SRC))
    dem = pd.DataFrame(dem_rows, columns=["district_id", "skill_id", "year", "demand", "source_type"])
    cap = pd.DataFrame(cap_rows, columns=["district_id", "skill_id", "year", "capacity", "source_type"])
    return dem, cap


def build_centres(dem, cap):
    """Training centres: 4 per district, each offering a subset of skills.
    Per-skill seats split the district's 2026 capacity; utilisation derives from demand/capacity."""
    c26 = cap[cap.year == 2026].set_index(["district_id", "skill_id"]).capacity
    d26 = dem[dem.year == 2026].set_index(["district_id", "skill_id"]).demand
    rows = []
    cid = 0
    for d in D_IDS:
        n_centres = 4
        letters = "ABCD"
        assign = {k: [] for k in range(n_centres)}
        for si, s in enumerate(SKILLS):
            sid = s[0]
            first = si % n_centres
            second = (si + 2) % n_centres
            assign[first].append(sid)
            if second != first:
                assign[second].append(sid)
        # share of each skill's capacity per centre
        count = {s[0]: sum(1 for k in assign if s[0] in assign[k]) for s in SKILLS}
        for k in range(n_centres):
            cid += 1
            dlat = DISTRICTS[D_IDS.index(d)][2]
            dlon = DISTRICTS[D_IDS.index(d)][3]
            lat = round(dlat + rng.uniform(-0.12, 0.12), 4)
            lon = round(dlon + rng.uniform(-0.12, 0.12), 4)
            seats, avail = [], []
            for sid in assign[k]:
                cap_ds = int(c26[(d, sid)])
                share = int(round(cap_ds / count[sid]))
                util = min(0.98, 0.97 * d26[(d, sid)] / max(cap_ds, 1))
                util = max(util, 0.25)
                seats.append((sid, share))
                avail.append((sid, int(round(share * (1 - util)))))
            total = sum(v for _, v in seats)
            total_avail = sum(v for _, v in avail)
            util_total = round(1 - total_avail / total, 3) if total else 0
            rows.append((
                f"TC{cid:03d}", f"Demo Skill Centre {D_NAME[d]} {letters[k]}", d, D_NAME[d], lat, lon,
                "|".join(sid for sid, _ in seats),
                ";".join(f"{sid}={v}" for sid, v in seats),
                ";".join(f"{sid}={v}" for sid, v in avail),
                total, total_avail, util_total,
                "Illustrative Level-4 certificate (demo, no official NSQF mapping)", SRC,
            ))
    return pd.DataFrame(rows, columns=[
        "centre_id", "name", "district_id", "district_name", "latitude", "longitude", "skills_offered",
        "seats_by_skill", "available_by_skill", "total_capacity", "available_seats", "utilization",
        "certification", "source_type"])


JOB_TEMPLATES = [
    "Looking for a {occ} with experience in {a}, {b} and {c}.",
    "Hiring {occ}. Required: {a}, {b}. Good to have: {c}.",
    "{occ} needed - hands-on with {a} and {b}; knowledge of {c} preferred.",
]


def build_jobs():
    rows = []
    jid = 0
    d_ids = np.array(D_IDS)
    for oid, oname, sid in OCCUPATIONS:
        skills = list(REQ[oname].keys())
        n_posts = int(rng.integers(10, 16))
        for _ in range(n_posts):
            jid += 1
            pick = rng.choice(len(skills), size=min(3, len(skills)), replace=False)
            chosen = [skills[i] for i in pick]
            alias_choice = []
            for comp in chosen:
                aliases = COMPETENCIES[comp][2]
                alias_choice.append(aliases[int(rng.integers(0, len(aliases)))])
            while len(alias_choice) < 3:
                alias_choice.append(alias_choice[-1])
            tpl = JOB_TEMPLATES[int(rng.integers(0, len(JOB_TEMPLATES)))]
            desc = tpl.format(occ=oname, a=alias_choice[0], b=alias_choice[1], c=alias_choice[2])
            d = str(rng.choice(d_ids))
            rows.append((
                f"J{jid:04d}", oname, oid, sid, S_BY_ID[sid][2], d, D_NAME[d],
                f"Demo Employer {int(rng.integers(1, 60)):03d}", int(rng.integers(2, 40)),
                int(rng.choice([2025, 2026])), desc, "|".join(chosen), SRC))
    return pd.DataFrame(rows, columns=[
        "job_id", "title", "occupation_id", "skill_id", "industry_id", "district_id", "district_name",
        "employer", "openings", "posted_year", "description", "competencies", "source_type"])


def build_json():
    taxonomy = {
        "_comment": "Illustrative competency taxonomy for the prototype. Future work: map to NCO-2015 occupations and NSQF qualifications.",
        "source_type": SRC,
        "competencies": [
            {"name": n, "category": v[0], "bridge_hours": v[1], "aliases": v[2]} for n, v in COMPETENCIES.items()
        ],
    }
    transition = {
        "_comment": "Prototype transition data (demo / illustrative). Weights are expert-style placeholders requiring validation.",
        "source_type": SRC,
        "occupation_requirements": {
            occ: [{"competency": c, "weight": w} for c, w in reqs.items()] for occ, reqs in REQ.items()
        },
        "similarity": [{"a": a, "b": b, "similarity": s} for a, b, s in SIMILARITY],
        "bridge_programmes": BRIDGE_PROGRAMMES,
    }
    (OUT / "taxonomy.json").write_text(json.dumps(taxonomy, indent=2))
    (OUT / "transition_skills.json").write_text(json.dumps(transition, indent=2))
    print("  taxonomy.json, transition_skills.json")


def main():
    print("Generating DEMO dataset ->", OUT)
    write(build_districts(), "districts.csv")
    write(build_industries(), "industries.csv")
    write(build_skills(), "skills.csv")
    write(build_occupations(), "occupations.csv")
    dem, cap = build_demand_and_capacity()
    write(dem, "historical_demand.csv")
    write(cap, "training_capacity.csv")
    write(build_centres(dem, cap), "training_centres.csv")
    write(build_jobs(), "jobs.csv")
    build_json()
    # sanity: EV story
    ev = dem[(dem.skill_id == "S01") & (dem.year == 2026)].merge(
        cap[(cap.skill_id == "S01") & (cap.year == 2026)], on=["district_id", "skill_id", "year"])
    print("\nEV 2026 check (demand/capacity):")
    for _, r in ev.iterrows():
        print(f"  {D_NAME[r.district_id]:28s} {r.demand_x if 'demand_x' in r else r.demand:5d} / {r.capacity:5d}")


if __name__ == "__main__":
    main()
