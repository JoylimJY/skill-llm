import os
import random
import textwrap

random.seed(42)

WORKSPACE = "/workspace"

# ─── 1. Create the workspace-level built-in memory artifacts
#        (the agent must NOT modify these)
os.makedirs(WORKSPACE, exist_ok=True)

# Workspace-level MEMORY.md (must not be touched)
with open(os.path.join(WORKSPACE, "MEMORY.md"), "w") as f:
    f.write(textwrap.dedent("""\
        # Agent Memory
        ## Current Context
        - Working with Professor Chen's lab
        - Organizing institutional knowledge
        ## Recent Interactions
        - 2026-01-15: Initial setup discussion
        - 2026-01-14: Reviewed lab inventory spreadsheet
    """))

# Workspace-level memory/ folder (must not be touched)
ws_mem = os.path.join(WORKSPACE, "memory")
os.makedirs(ws_mem, exist_ok=True)
with open(os.path.join(ws_mem, "2026-01-15.md"), "w") as f:
    f.write("# Daily Log 2026-01-15\n- Discussed lab organization needs with Prof. Chen\n")
with open(os.path.join(ws_mem, "2026-01-14.md"), "w") as f:
    f.write("# Daily Log 2026-01-14\n- Received raw data dumps from lab manager\n")

# ─── 2. Raw data dumps (the messy input the agent must process)

# --- People data (8 people) ---
people_raw = """\
NAME: Dr. Sofia Reyes
ROLE: PhD Student (Year 3)
EMAIL: s.reyes@univ.edu
RESEARCH: Computational fluid dynamics, turbulence modeling
ADVISOR: Prof. Chen
PUBLICATIONS: 2 first-author, 4 co-author
JOINED: 2023-09
STATUS: Active
---
NAME: Marcus Webb
ROLE: Postdoctoral Researcher
EMAIL: m.webb@univ.edu
RESEARCH: Machine learning for climate prediction
ADVISOR: Prof. Chen
PUBLICATIONS: 12 first-author
JOINED: 2022-03
STATUS: Active
---
NAME: Priya Nair
ROLE: PhD Student (Year 1)
EMAIL: p.nair@univ.edu
RESEARCH: Remote sensing, satellite data analysis
ADVISOR: Prof. Chen
PUBLICATIONS: 0
JOINED: 2025-09
STATUS: Active
---
NAME: Dr. James Okafor
ROLE: Collaborator (External)
EMAIL: j.okafor@partneruniv.edu
RESEARCH: Oceanographic modeling
AFFILIATION: Pacific Institute of Oceanography
PUBLICATIONS: 35+
STATUS: Active collaborator
---
NAME: Lin Zhang
ROLE: Research Technician
EMAIL: l.zhang@univ.edu
RESEARCH: Lab instrumentation, data pipelines
JOINED: 2021-05
STATUS: Active
---
NAME: Dr. Amara Diallo
ROLE: Former Postdoc (Graduated)
EMAIL: a.diallo@techcorp.com
RESEARCH: Atmospheric chemistry
NEW_ROLE: Senior Scientist at TechCorp Environmental
STATUS: Alumni
---
NAME: Tomás Herrera
ROLE: Masters Student
EMAIL: t.herrera@univ.edu
RESEARCH: Urban heat island effects
ADVISOR: Prof. Chen
PUBLICATIONS: 1 co-author
JOINED: 2024-09
STATUS: Active
---
NAME: Dr. Yuki Tanaka
ROLE: Collaborator (External)
EMAIL: y.tanaka@kyoto-u.jp
RESEARCH: Monsoon dynamics, seasonal forecasting
AFFILIATION: Kyoto University Earth Sciences
PUBLICATIONS: 28
STATUS: Active collaborator
"""

with open(os.path.join(WORKSPACE, "raw_people.txt"), "w") as f:
    f.write(people_raw)

# --- Grants data (5 grants) ---
grants_raw = """\
GRANT_ID: NSF-2024-ATM-0042
TITLE: Turbulence Parameterization in Climate Models
AGENCY: National Science Foundation
AMOUNT: $485,000
PERIOD: 2024-01 to 2027-01
PI: Prof. Chen
CO-PI: Dr. James Okafor
STATUS: Active
NOTES: Annual reports due in January. Student support for Reyes and Zhang.

GRANT_ID: DOE-2023-ER-9918
TITLE: Machine Learning Approaches to Renewable Energy Forecasting
AGENCY: Department of Energy
AMOUNT: $320,000
PERIOD: 2023-06 to 2026-06
PI: Prof. Chen
CO-PI: Marcus Webb
STATUS: Active
NOTES: Quarterly progress reports. Webb's primary funding source.

GRANT_ID: NASA-2022-ROSES-0077
TITLE: Satellite-Based Urban Heat Island Detection
AGENCY: NASA
AMOUNT: $210,000
PERIOD: 2022-09 to 2025-09
PI: Prof. Chen
STATUS: Completed
NOTES: Final report submitted 2025-10. Led to Herrera's thesis project.

GRANT_ID: NOAA-2025-CLIMATE-1234
TITLE: Coupled Ocean-Atmosphere Prediction at Seasonal Timescales
AGENCY: NOAA
AMOUNT: $560,000
PERIOD: 2025-03 to 2028-03
PI: Prof. Chen
CO-PI: Dr. Yuki Tanaka, Dr. James Okafor
STATUS: Active
NOTES: Major new grant. Nair's primary support. First milestone Q3 2025.

GRANT_ID: UNIVERSITY-SEED-2026-003
TITLE: Deep Learning for Extreme Weather Event Prediction
AGENCY: University Research Office
AMOUNT: $50,000
PERIOD: 2026-01 to 2026-12
PI: Prof. Chen
STATUS: Active
NOTES: Seed funding to support Herrera's extended research into Year 2 Masters.
"""

with open(os.path.join(WORKSPACE, "raw_grants.txt"), "w") as f:
    f.write(grants_raw)

# --- Publications data (6 publications) ---
publications_raw = """\
ID: PUB-2025-001
TITLE: Adaptive Turbulence Closure Schemes Using Neural Networks
AUTHORS: Reyes S., Webb M., Chen P.
JOURNAL: Journal of Atmospheric Sciences
YEAR: 2025
DOI: 10.1175/JAS-D-24-0182
STATUS: Published
IMPACT_FACTOR: 3.4
NOTES: Cover article for May 2025 issue. NSF-2024-ATM-0042 acknowledged.

ID: PUB-2025-002
TITLE: Seasonal Forecasting Skill of Machine Learning Models vs. ENSO Indices
AUTHORS: Webb M., Tanaka Y., Chen P.
JOURNAL: Geophysical Research Letters
YEAR: 2025
DOI: 10.1029/2025GL108834
STATUS: Published
IMPACT_FACTOR: 5.2
NOTES: Highlighted as GRL Editor's Choice.

ID: PUB-2024-001
TITLE: Urban Heat Island Intensification Under Climate Change Scenarios
AUTHORS: Chen P., Herrera T., Zhang L.
JOURNAL: Urban Climate
YEAR: 2024
DOI: 10.1016/j.uclim.2024.101432
STATUS: Published
IMPACT_FACTOR: 6.1
NOTES: NASA-2022-ROSES-0077 acknowledged. Basis for Herrera's thesis.

ID: PUB-2026-001
TITLE: Remote Sensing Validation of Urban Thermal Models
AUTHORS: Nair P., Reyes S., Chen P.
JOURNAL: Remote Sensing of Environment
YEAR: 2026
STATUS: Under Review
NOTES: Submitted 2026-01-10. DOE and NOAA grants acknowledged.

ID: PUB-2026-002
TITLE: Coupled Ocean-Atmosphere Interactions at Sub-Seasonal Timescales
AUTHORS: Okafor J., Tanaka Y., Webb M., Chen P.
JOURNAL: Climate Dynamics
YEAR: 2026
STATUS: In Preparation
NOTES: Target submission Q2 2026. NOAA-2025-CLIMATE-1234 primary.

ID: PUB-2023-001
TITLE: Atmospheric Chemistry Feedbacks in Coupled Climate Models
AUTHORS: Diallo A., Chen P., Okafor J.
JOURNAL: Atmospheric Chemistry and Physics
YEAR: 2023
DOI: 10.5194/acp-23-8841-2023
STATUS: Published
IMPACT_FACTOR: 7.2
NOTES: Diallo's capstone postdoc paper. Highly cited (42 citations as of 2026-01).
"""

with open(os.path.join(WORKSPACE, "raw_publications.txt"), "w") as f:
    f.write(publications_raw)

# --- Equipment data (150 items — forces a split) ---
# 80 lab items, 70 field items

lab_equipment = [
    ("LAB-001", "Agilent 4156C Semiconductor Parameter Analyzer", "Electrical characterization", "Operational", "Main Lab B-204"),
    ("LAB-002", "Thermo Scientific HAAKE Viscometer RS6000", "Fluid viscosity measurement", "Operational", "Main Lab B-204"),
    ("LAB-003", "Anton Paar DMA 4500M Density Meter", "Liquid density measurement", "Operational", "Main Lab B-204"),
    ("LAB-004", "TA Instruments Q500 Thermogravimetric Analyzer", "TGA analysis", "Operational", "Thermal Suite B-210"),
    ("LAB-005", "Bruker Tensor 27 FTIR Spectrometer", "Infrared spectroscopy", "Operational", "Spectroscopy B-212"),
    ("LAB-006", "Malvern Zetasizer Nano ZS", "Particle size analysis", "Operational", "Spectroscopy B-212"),
    ("LAB-007", "Carl Zeiss Axio Observer 7", "Inverted optical microscopy", "Operational", "Microscopy B-215"),
    ("LAB-008", "Olympus SZX16 Stereo Microscope", "Sample inspection", "Operational", "Microscopy B-215"),
    ("LAB-009", "Keithley 2450 SourceMeter", "Current-voltage measurements", "Operational", "Electronics Bench B-204"),
    ("LAB-010", "Tektronix MDO3054 Mixed Domain Oscilloscope", "Signal analysis", "Operational", "Electronics Bench B-204"),
    ("LAB-011", "Rigol DG4162 Function Generator", "Signal generation", "Operational", "Electronics Bench B-204"),
    ("LAB-012", "Stanford Research SR830 Lock-in Amplifier", "Low-noise measurements", "Operational", "Electronics Bench B-204"),
    ("LAB-013", "Lakeshore 325 Temperature Controller", "Cryogenic temperature control", "Operational", "Cryostat Room B-220"),
    ("LAB-014", "Janis Research ST-100 Cryostat", "Low-temperature experiments", "Operational", "Cryostat Room B-220"),
    ("LAB-015", "Pfeiffer HiPace 300 Turbopump", "Vacuum system", "Operational", "Vacuum Bay B-222"),
    ("LAB-016", "Leybold TRIVAC D16B Rotary Pump", "Roughing vacuum", "Under Maintenance", "Vacuum Bay B-222"),
    ("LAB-017", "MKS Instruments 627B Capacitance Manometer", "Pressure measurement", "Operational", "Vacuum Bay B-222"),
    ("LAB-018", "Horiba Scientific LabRAM HR Evolution Raman", "Raman spectroscopy", "Operational", "Spectroscopy B-212"),
    ("LAB-019", "Shimadzu UV-2600i UV-Vis Spectrophotometer", "Absorbance/transmittance", "Operational", "Spectroscopy B-212"),
    ("LAB-020", "Perkin Elmer Lambda 1050 UV/Vis/NIR", "Broad-spectrum photometry", "Operational", "Spectroscopy B-212"),
    ("LAB-021", "Mettler Toledo XSR205 Analytical Balance", "Precision mass measurement", "Operational", "Prep Room B-208"),
    ("LAB-022", "Mettler Toledo Excellence XS603S Balance", "Large-sample weighing", "Operational", "Prep Room B-208"),
    ("LAB-023", "IKA RCT basic Hot Plate Stirrer", "Sample preparation", "Operational", "Prep Room B-208"),
    ("LAB-024", "Sartorius Arium pro UF Ultrapure Water", "Water purification", "Operational", "Prep Room B-208"),
    ("LAB-025", "Thermo Scientific Sorvall Legend X1R Centrifuge", "Sample separation", "Operational", "Prep Room B-208"),
    ("LAB-026", "Eppendorf 5810R Refrigerated Centrifuge", "Temperature-controlled centrifugation", "Operational", "Prep Room B-208"),
    ("LAB-027", "BioRad MyCycler PCR Thermocycler", "Nucleic acid amplification", "Operational", "Bio Bay B-230"),
    ("LAB-028", "Thermo Scientific NanoDrop 2000", "Micro-volume spectrophotometry", "Operational", "Bio Bay B-230"),
    ("LAB-029", "GE ÄKTA Pure 25 FPLC System", "Protein purification", "Operational", "Bio Bay B-230"),
    ("LAB-030", "Thermo Scientific CO2 Water-Jacketed Incubator", "Cell culture incubation", "Operational", "Bio Bay B-230"),
    ("LAB-031", "Nikon Eclipse Ti2-E Inverted Microscope", "Fluorescence imaging", "Operational", "Imaging Suite B-218"),
    ("LAB-032", "Zeiss LSM 980 Confocal Microscope", "Confocal fluorescence", "Operational", "Imaging Suite B-218"),
    ("LAB-033", "Andor iXon Ultra 897 EMCCD Camera", "Single-molecule imaging", "Operational", "Imaging Suite B-218"),
    ("LAB-034", "Hamamatsu ORCA-Flash4 sCMOS Camera", "High-speed imaging", "Operational", "Imaging Suite B-218"),
    ("LAB-035", "Photometrics Prime BSI sCMOS Camera", "Widefield fluorescence", "Operational", "Imaging Suite B-218"),
    ("LAB-036", "Coherent OBIS 488nm Laser", "Fluorescence excitation", "Operational", "Imaging Suite B-218"),
    ("LAB-037", "Coherent OBIS 561nm Laser", "Fluorescence excitation", "Operational", "Imaging Suite B-218"),
    ("LAB-038", "Thorlabs SCIENTIFIC CMOS DCC3240M", "Wavefront sensing", "Operational", "Optics Bench B-225"),
    ("LAB-039", "Newport XPS-D Controller", "Multi-axis motion control", "Operational", "Optics Bench B-225"),
    ("LAB-040", "Thorlabs BBD302 3-Axis Brushless Controller", "Precision positioning", "Operational", "Optics Bench B-225"),
    ("LAB-041", "National Instruments PXIe-1082 Chassis", "Data acquisition chassis", "Operational", "Server Room B-235"),
    ("LAB-042", "National Instruments PXIe-6674T Timing", "Clock synchronization", "Operational", "Server Room B-235"),
    ("LAB-043", "National Instruments PXIe-5160 Oscilloscope", "PXI-based oscilloscope", "Operational", "Server Room B-235"),
    ("LAB-044", "Dell PowerEdge R750 Server (Node 1)", "HPC compute node", "Operational", "Server Room B-235"),
    ("LAB-045", "Dell PowerEdge R750 Server (Node 2)", "HPC compute node", "Operational", "Server Room B-235"),
    ("LAB-046", "Dell PowerEdge R750 Server (Node 3)", "HPC compute node", "Operational", "Server Room B-235"),
    ("LAB-047", "Supermicro 4U Storage Server", "Research data storage 200TB", "Operational", "Server Room B-235"),
    ("LAB-048", "APC Smart-UPS 3000VA", "Uninterruptible power supply", "Operational", "Server Room B-235"),
    ("LAB-049", "Cisco Catalyst 9300 Switch", "Lab network switch", "Operational", "Server Room B-235"),
    ("LAB-050", "Keyence VHX-7000 Digital Microscope", "Surface topography", "Operational", "Metrology B-240"),
    ("LAB-051", "Bruker Dimension Icon AFM", "Atomic force microscopy", "Operational", "Metrology B-240"),
    ("LAB-052", "Veeco Dektak 150 Surface Profiler", "Thin film step height", "Operational", "Metrology B-240"),
    ("LAB-053", "KLA Tencor P-17 Stylus Profiler", "Surface metrology", "Operational", "Metrology B-240"),
    ("LAB-054", "Zygo NewView 9000 3D Optical Profiler", "Non-contact surface measurement", "Operational", "Metrology B-240"),
    ("LAB-055", "Cascade Microtech EPS150 Probe Station", "Wafer-level probing", "Operational", "Clean Room B-245"),
    ("LAB-056", "Suss MicroTec MJB4 Mask Aligner", "Photolithography", "Operational", "Clean Room B-245"),
    ("LAB-057", "Anatech SCE-106 Oxygen Plasma Cleaner", "Surface treatment", "Operational", "Clean Room B-245"),
    ("LAB-058", "Kurt J. Lesker PVD 75 Sputter Deposition", "Thin film deposition", "Operational", "Clean Room B-245"),
    ("LAB-059", "Oxford Instruments ALD FlexAL", "Atomic layer deposition", "Operational", "Clean Room B-245"),
    ("LAB-060", "Plasmatherm Versaline ICP-CVD", "Plasma-enhanced CVD", "Operational", "Clean Room B-245"),
    ("LAB-061", "Solartron 1260A Impedance Analyzer", "Electrochemical impedance", "Operational", "Electrochemistry B-250"),
    ("LAB-062", "Bio-Logic SP-300 Potentiostat", "Electrochemical testing", "Operational", "Electrochemistry B-250"),
    ("LAB-063", "Gamry Reference 3000 Potentiostat", "Corrosion testing", "Operational", "Electrochemistry B-250"),
    ("LAB-064", "Metrohm Autolab PGSTAT302N", "Electroanalytical chemistry", "Operational", "Electrochemistry B-250"),
    ("LAB-065", "Autoclave Engineers 1L Parr Reactor", "High-pressure reactions", "Operational", "Reaction Bay B-255"),
    ("LAB-066", "Buchi Rotavapor R-300", "Solvent evaporation", "Operational", "Reaction Bay B-255"),
    ("LAB-067", "IKA LR-2000 Lifting Reactor", "Large-scale mixing", "Operational", "Reaction Bay B-255"),
    ("LAB-068", "Mettler Toledo EasyMax 102", "Automated synthesis reactor", "Operational", "Reaction Bay B-255"),
    ("LAB-069", "Waters ACQUITY UPLC H-Class", "Ultra-high performance LC", "Operational", "Chromatography B-260"),
    ("LAB-070", "Agilent 1290 Infinity II UHPLC", "High-speed liquid chromatography", "Operational", "Chromatography B-260"),
    ("LAB-071", "Agilent 7890B GC with 5977B MSD", "Gas chromatography-mass spec", "Operational", "Chromatography B-260"),
    ("LAB-072", "Thermo Scientific Orbitrap Exploris 480", "High-res mass spectrometry", "Operational", "Mass Spec B-265"),
    ("LAB-073", "Bruker timsTOF Pro2 Mass Spectrometer", "Ion mobility mass spectrometry", "Operational", "Mass Spec B-265"),
    ("LAB-074", "JEOL JEM-2100F TEM", "Transmission electron microscopy", "Operational", "Electron Microscopy B-270"),
    ("LAB-075", "FEI Quanta 650 FEG SEM", "Scanning electron microscopy", "Operational", "Electron Microscopy B-270"),
    ("LAB-076", "Oxford Instruments X-MaxN 150 EDS", "Energy dispersive X-ray spectroscopy", "Operational", "Electron Microscopy B-270"),
    ("LAB-077", "Rigaku SmartLab XRD", "X-ray diffraction", "Operational", "X-ray Suite B-275"),
    ("LAB-078", "Bruker D8 Advance XRD", "Powder X-ray diffraction", "Operational", "X-ray Suite B-275"),
    ("LAB-079", "PANalytical Empyrean XRD", "High-res X-ray diffraction", "Under Maintenance", "X-ray Suite B-275"),
    ("LAB-080", "Quantum Design MPMS3 SQUID Magnetometer", "Magnetic property measurement", "Operational", "Magnetics B-280"),
]

field_equipment = [
    ("FIELD-001", "Vaisala HMP155A Temperature/Humidity Probe", "Atmospheric T/RH measurement", "Operational", "Field Cache Alpha"),
    ("FIELD-002", "Vaisala PTB330 Digital Barometer", "Atmospheric pressure", "Operational", "Field Cache Alpha"),
    ("FIELD-003", "Gill Instruments WindSonic Anemometer", "Wind speed and direction", "Operational", "Field Cache Alpha"),
    ("FIELD-004", "Kipp & Zonen CMP22 Pyranometer", "Solar radiation measurement", "Operational", "Field Cache Alpha"),
    ("FIELD-005", "Kipp & Zonen CGR4 Pyrgeometer", "Thermal infrared radiation", "Operational", "Field Cache Alpha"),
    ("FIELD-006", "Campbell Scientific CR6 Datalogger", "Multi-channel data logging", "Operational", "Field Cache Alpha"),
    ("FIELD-007", "Campbell Scientific CR1000X Datalogger", "Field data acquisition", "Operational", "Field Cache Beta"),
    ("FIELD-008", "Campbell Scientific AM16/32B Multiplexer", "Channel expansion for CR6", "Operational", "Field Cache Alpha"),
    ("FIELD-009", "Vaisala WXT536 Weather Transmitter", "All-in-one weather station", "Operational", "Field Cache Beta"),
    ("FIELD-010", "R.M. Young 81000 Ultrasonic Anemometer", "3D turbulence measurements", "Operational", "Tower Site 1"),
    ("FIELD-011", "LI-COR LI-7500DS CO2/H2O Analyzer", "Eddy covariance gas flux", "Operational", "Tower Site 1"),
    ("FIELD-012", "LI-COR LI-7700 Open Path CH4 Analyzer", "Methane flux measurement", "Operational", "Tower Site 1"),
    ("FIELD-013", "Apogee SI-411 Infrared Radiometer", "Surface temperature", "Operational", "Tower Site 1"),
    ("FIELD-014", "Hukseflux HFP01 Heat Flux Plate", "Soil heat flux", "Operational", "Tower Site 1"),
    ("FIELD-015", "Stevens HydraProbe Soil Sensor", "Soil moisture and temperature", "Operational", "Tower Site 1"),
    ("FIELD-016", "Decagon 5TE Soil Sensor", "Soil dielectric properties", "Operational", "Tower Site 2"),
    ("FIELD-017", "ONSET HOBO U30 Station", "Remote micro-climate logging", "Operational", "Tower Site 2"),
    ("FIELD-018", "ONSET HOBO MX2301 Data Logger", "Portable T/RH logging", "Operational", "Field Cache Beta"),
    ("FIELD-019", "Onset HOBO MX2001 Water Level", "Water level and temperature", "Operational", "Wetland Site"),
    ("FIELD-020", "In-Situ Aqua TROLL 500 Sonde", "Multi-parameter water quality", "Operational", "Wetland Site"),
    ("FIELD-021", "YSI ProDSS Water Quality Sonde", "Dissolved oxygen, conductivity", "Operational", "Wetland Site"),
    ("FIELD-022", "Hydrolab DS5X Multi-parameter Sonde", "Aquatic monitoring", "Operational", "Wetland Site"),
    ("FIELD-023", "Nortek Aquadopp Current Profiler", "Water current profiling", "Operational", "Coastal Site"),
    ("FIELD-024", "RBRconcerto3 CTD Logger", "Conductivity-Temperature-Depth", "Operational", "Coastal Site"),
    ("FIELD-025", "Sea-Bird SBE 37-SM MicroCAT CTD", "High-accuracy oceanographic CTD", "Operational", "Coastal Site"),
    ("FIELD-026", "SonTek FlowTracker2 ADV", "Streamflow measurement", "Operational", "River Site"),
    ("FIELD-027", "Teledyne RD Instruments WorkHorse ADCP", "Acoustic Doppler profiler", "Operational", "River Site"),
    ("FIELD-028", "Global Water FP111 Flow Probe", "Open-channel velocity", "Operational", "River Site"),
    ("FIELD-029", "Sutron SatLink3 Satellite Transmitter", "Remote data telemetry", "Operational", "Tower Site 1"),
    ("FIELD-030", "Iridium Edge Solar Data Transmitter", "Satellite IoT data logger", "Operational", "Tower Site 2"),
    ("FIELD-031", "DJI Matrice 300 RTK Drone", "Aerial survey platform", "Operational", "Field Cache Beta"),
    ("FIELD-032", "DJI Zenmuse X7 Camera", "High-res aerial imaging", "Operational", "Field Cache Beta"),
    ("FIELD-033", "DJI Zenmuse L1 LiDAR", "Aerial LiDAR scanning", "Operational", "Field Cache Beta"),
    ("FIELD-034", "Micasense RedEdge-MX Multispectral Camera", "Multispectral aerial imaging", "Operational", "Field Cache Beta"),
    ("FIELD-035", "Headwall Photonics Nano-Hyperspec", "Hyperspectral imaging", "Operational", "Field Cache Beta"),
    ("FIELD-036", "FARO Focus3D X330 Terrestrial LiDAR", "Ground-based 3D scanning", "Operational", "Field Cache Alpha"),
    ("FIELD-037", "Leica BLK360 Imaging Laser Scanner", "Portable 3D scanning", "Operational", "Field Cache Alpha"),
    ("FIELD-038", "Trimble R10 GNSS Receiver", "Centimeter-accurate GPS", "Operational", "Field Cache Alpha"),
    ("FIELD-039", "Leica GS18 T GNSS Rover", "RTK GNSS surveying", "Operational", "Field Cache Alpha"),
    ("FIELD-040", "Topcon GR-5+ GNSS Receiver", "Multi-constellation GNSS", "Operational", "Field Cache Beta"),
    ("FIELD-041", "Garmin inReach Explorer+", "Satellite communicator", "Operational", "Field Cache Alpha"),
    ("FIELD-042", "Garmin inReach Mini 2 (Unit 1)", "Compact satellite messenger", "Operational", "Field Cache Alpha"),
    ("FIELD-043", "Garmin inReach Mini 2 (Unit 2)", "Compact satellite messenger", "Operational", "Field Cache Beta"),
    ("FIELD-044", "Garmin inReach Mini 2 (Unit 3)", "Compact satellite messenger", "Operational", "Field Cache Beta"),
    ("FIELD-045", "Motorola APX 8000 Portable Radio", "Two-way communications", "Operational", "Field Cache Alpha"),
    ("FIELD-046", "Motorola APX 8000 Portable Radio (Spare)", "Two-way communications backup", "Operational", "Field Cache Beta"),
    ("FIELD-047", "Pelican 1650 Case (Large) - Set of 4", "Equipment transport protection", "Operational", "Storage Rack C-101"),
    ("FIELD-048", "Pelican 1550 Case (Medium) - Set of 6", "Instrument transport cases", "Operational", "Storage Rack C-101"),
    ("FIELD-049", "Pelican 1510 Case (Carry-on) - Set of 3", "Air-travel instrument cases", "Operational", "Storage Rack C-101"),
    ("FIELD-050", "Goal Zero Yeti 6000X Power Station", "High-capacity field power", "Operational", "Field Cache Alpha"),
    ("FIELD-051", "Goal Zero Yeti 1500X Power Station (Unit 1)", "Mid-capacity field power", "Operational", "Field Cache Alpha"),
    ("FIELD-052", "Goal Zero Yeti 1500X Power Station (Unit 2)", "Mid-capacity field power", "Operational", "Field Cache Beta"),
    ("FIELD-053", "Renogy 200W Foldable Solar Panel (Set of 3)", "Solar charging for field stations", "Operational", "Field Cache Alpha"),
    ("FIELD-054", "Renogy 100W Foldable Solar Panel (Set of 4)", "Portable solar panels", "Operational", "Field Cache Beta"),
    ("FIELD-055", "Victron Energy SmartSolar MPPT 100/30", "Solar charge controller", "Operational", "Tower Site 1"),
    ("FIELD-056", "Victron Energy SmartSolar MPPT 75/15 (x2)", "Small-station charge controllers", "Operational", "Tower Site 2"),
    ("FIELD-057", "Optima YellowTop D31M Battery (x4)", "Deep-cycle field batteries", "Operational", "Field Cache Alpha"),
    ("FIELD-058", "BattleBorn 100Ah LiFePO4 (x6)", "Lithium field battery bank", "Operational", "Field Cache Beta"),
    ("FIELD-059", "Bosch GLM 400 C Laser Rangefinder", "Distance/area measurement", "Operational", "Field Cache Alpha"),
    ("FIELD-060", "Nikon Forestry Pro II Laser Rangefinder", "Forestry height measurement", "Operational", "Field Cache Alpha"),
    ("FIELD-061", "Suunto A-30 Compass (Set of 5)", "Magnetic field navigation", "Operational", "Field Cache Alpha"),
    ("FIELD-062", "Brunton TruArc 15 Compass (Set of 3)", "Professional-grade compass", "Operational", "Field Cache Beta"),
    ("FIELD-063", "Rite in the Rain 3x5 Notebooks (Box/40)", "All-weather field notebooks", "Consumable", "Storage Rack C-101"),
    ("FIELD-064", "SanDisk Extreme Pro 512GB MicroSDXC (x10)", "High-capacity memory cards", "Operational", "Storage Rack C-101"),
    ("FIELD-065", "Western Digital My Passport 4TB (x5)", "Portable field data backup", "Operational", "Storage Rack C-101"),
    ("FIELD-066", "Peli Storm iM2950 Case (Extra-Large)", "Large equipment transport", "Operational", "Storage Rack C-101"),
    ("FIELD-067", "MSR WaterWorks EX Water Filter (x2)", "Field water purification", "Operational", "Safety Cache C-105"),
    ("FIELD-068", "Adventure Medical Kits Expedition Kit", "Field first aid", "Operational", "Safety Cache C-105"),
    ("FIELD-069", "Black Diamond Spot Headlamp (x6)", "Field lighting", "Operational", "Safety Cache C-105"),
    ("FIELD-070", "Black Diamond Storm 500-R Headlamp (x4)", "Rechargeable field lighting", "Operational", "Safety Cache C-105"),
]

# Write equipment as raw CSV
equipment_lines = ["ID,NAME,PURPOSE,STATUS,LOCATION"]
for item in lab_equipment:
    equipment_lines.append(",".join(item))
for item in field_equipment:
    equipment_lines.append(",".join(item))

with open(os.path.join(WORKSPACE, "raw_equipment.csv"), "w") as f:
    f.write("\n".join(equipment_lines))

# ─── 3. Distractor files to increase complexity

# Fake project notes (not structured data for memory, just context noise)
os.makedirs(os.path.join(WORKSPACE, "notes"), exist_ok=True)
with open(os.path.join(WORKSPACE, "notes", "meeting_2026-01-10.txt"), "w") as f:
    f.write("Meeting notes: discussed grant reporting deadlines, lab expansions, new student Priya orientation.\n")

with open(os.path.join(WORKSPACE, "notes", "todo.txt"), "w") as f:
    f.write("TODO:\n- Organize lab inventory\n- Update collaborator contacts\n- File NSF annual report\n- Archive old grant files\n")

os.makedirs(os.path.join(WORKSPACE, "admin"), exist_ok=True)
with open(os.path.join(WORKSPACE, "admin", "budget_2026.txt"), "w") as f:
    f.write("Operating budget 2026: $120,000\nPersonnel: $340,000\nEquipment maintenance: $45,000\n")

with open(os.path.join(WORKSPACE, "admin", "lab_policies.txt"), "w") as f:
    f.write("Lab safety policy v3.2\nAll field work requires 2-person minimum team.\nEquipment checkout requires 48hr notice.\n")

os.makedirs(os.path.join(WORKSPACE, "data"), exist_ok=True)
with open(os.path.join(WORKSPACE, "data", "sensor_log_2026-01-14.csv"), "w") as f:
    f.write("timestamp,temperature,humidity,pressure\n2026-01-14T00:00:00Z,22.4,55.2,1013.2\n2026-01-14T01:00:00Z,22.1,56.0,1013.1\n")

with open(os.path.join(WORKSPACE, "data", "README_data.txt"), "w") as f:
    f.write("Raw sensor data from Tower Site 1. Do not modify original files.\n")

os.makedirs(os.path.join(WORKSPACE, "scripts"), exist_ok=True)
with open(os.path.join(WORKSPACE, "scripts", "sync_data.sh"), "w") as f:
    f.write("#!/bin/bash\n# Placeholder: syncs field data to server\necho 'Sync script not yet implemented'\n")

with open(os.path.join(WORKSPACE, "scripts", "process_eddy.py"), "w") as f:
    f.write("# Eddy covariance processing script\n# Requires raw LI-7500 data files\nimport sys\nprint('EddyPro wrapper - not yet complete')\n")

with open(os.path.join(WORKSPACE, "instructions.txt"), "w") as f:
    f.write("""\
Lab Knowledge Vault Setup Instructions
========================================
Please use the attached data files to set up our lab's institutional memory system.
The raw data files are:
  - raw_people.txt      (8 lab members and collaborators)
  - raw_grants.txt      (5 funding sources)
  - raw_publications.txt (6 publications)
  - raw_equipment.csv   (150 equipment items: 80 lab-based, 70 field-based)

We need to be able to quickly find any piece of information about our lab.
The equipment list is especially large, so it needs to be subdivided sensibly.
""")

print("Workspace generated successfully.")
print(f"Lab equipment: {len(lab_equipment)} items")
print(f"Field equipment: {len(field_equipment)} items")
print(f"Total equipment: {len(lab_equipment) + len(field_equipment)} items")