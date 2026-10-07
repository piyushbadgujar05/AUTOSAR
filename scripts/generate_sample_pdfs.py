import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def create_hld_pdf(filename: str, version: str, is_v2: bool = False):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=22, textColor=colors.HexColor('#0F172A'), spaceAfter=8)
    subtitle_style = ParagraphStyle('SubStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor('#2563EB'), spaceAfter=15)
    disclaimer_style = ParagraphStyle('DiscStyle', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=9, textColor=colors.HexColor('#DC2626'), spaceAfter=15)
    h1_style = ParagraphStyle('H1Style', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=15, textColor=colors.HexColor('#1E293B'), spaceBefore=12, spaceAfter=8)
    h2_style = ParagraphStyle('H2Style', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor('#334155'), spaceBefore=10, spaceAfter=6)
    body_style = ParagraphStyle('BodyCustom', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=colors.HexColor('#1E293B'), leading=14, spaceAfter=8)
    table_cell = ParagraphStyle('TableCell', parent=styles['Normal'], fontName='Helvetica', fontSize=9, textColor=colors.HexColor('#1E293B'), leading=11)
    table_hdr = ParagraphStyle('TableHdr', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, textColor=colors.white, leading=11)

    elements = []

    # ================= PAGE 1: TITLE & COVER =================
    elements.append(Paragraph("AUTOSAR High-Level Design (HLD) Document", title_style))
    elements.append(Paragraph("SYNTHETIC DEMONSTRATION DOCUMENT — NOT OFFICIAL AUTOSAR DOCUMENTATION", disclaimer_style))
    elements.append(Spacer(1, 15))
    elements.append(Paragraph("<b>Document Identifier:</b> HLD-ADAS-2026-X89<br/><b>Classification:</b> Confidential / Engineering Baseline<br/><b>Author:</b> Systems Architecture Engineering Team<br/><b>ECU Target:</b> ADAS Domain Controller (TriCore AURIX / ARM Cortex-R52)", body_style))
    elements.append(Spacer(1, 15))
    elements.append(Paragraph("1.0 Document Revision History", h1_style))
    
    rev_data = [
        [Paragraph("Version", table_hdr), Paragraph("Date", table_hdr), Paragraph("Author", table_hdr), Paragraph("Description", table_hdr)],
        [Paragraph("1.0", table_cell), Paragraph("2026-01-15", table_cell), Paragraph("Arch Team", table_cell), Paragraph("Initial baseline release of ADAS controller architecture.", table_cell)]
    ]
    if is_v2:
        rev_data.append([
            Paragraph("2.0", table_cell),
            Paragraph("2026-06-20", table_cell),
            Paragraph("Lead Architect", table_cell),
            Paragraph("Upgraded sensor fusion pipeline to SensorFusionV2. Updated brake interface contracts and protocols.", table_cell)
        ])
    t_rev = Table(rev_data, colWidths=[60, 80, 100, 290])
    t_rev.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
    ]))
    elements.append(t_rev)
    elements.append(PageBreak())

    # ================= PAGE 2: SYSTEM ARCHITECTURE OVERVIEW =================
    elements.append(Paragraph("2.0 System Architecture Overview", h1_style))
    elements.append(Paragraph(
        "The ADAS Control System provides Level 2+ automated driving capabilities including Autonomous Emergency Braking (AEB), "
        "Adaptive Cruise Control (ACC), and Lane Centering Assist (LCA). The architectural model follows AUTOSAR Classic and Adaptive "
        "methodologies with strictly delineated software component (SWC) boundaries, standardized RTE communication ports, and ISO 26262 ASIL-D safety integrity.",
        body_style
    ))
    elements.append(Paragraph(
        "The system executes across a multi-core automotive microcontroller. Real-time sensor perception data is ingested from external "
        "radar and optical front-camera sensors, synchronized, and processed to calculate safety trajectories and deceleration commands.",
        body_style
    ))
    elements.append(Paragraph("Primary Architecture Goals:", h2_style))
    elements.append(Paragraph("• Deterministic execution with maximum 20ms end-to-end latency from optical perception to brake actuation.<br/>• Full fault isolation between perception layers and actuator execution.<br/>• Compliance with automotive bus protocols (CAN-FD and Automotive Ethernet 100BASE-T1).", body_style))
    elements.append(PageBreak())

    # ================= PAGE 3: SOFTWARE COMPONENTS CATALOG =================
    elements.append(Paragraph("3.0 Software Component (SWC) Specifications", h1_style))
    elements.append(Paragraph(
        "The application layer decomposes functionality into modular AUTOSAR software components. Each component exposes standardized "
        "Sender-Receiver and Client-Server ports configured via the Runtime Environment (RTE).",
        body_style
    ))
    elements.append(Paragraph("3.1 Component: CameraManager", h2_style))
    elements.append(Paragraph(
        "Software Component: CameraManager is responsible for deserializing raw video streams from the front-facing monocular camera module. "
        "It performs object boundary detection, optical flow estimation, and lane boundary classification. "
        "It provides the interface CameraData and transmits high-bandwidth visual object frames over Automotive Ethernet.",
        body_style
    ))
    elements.append(Paragraph("3.2 Component: RadarProcessor", h2_style))
    elements.append(Paragraph(
        "Software Component: RadarProcessor connects to long-range and medium-range radar transceivers. It filters raw radar reflections, "
        "performs Doppler velocity resolution, and clusters target point clouds. It provides the interface RadarData to downstream fusion SWCs.",
        body_style
    ))
    elements.append(PageBreak())

    # ================= PAGE 4: SENSOR FUSION & PROCESSING =================
    elements.append(Paragraph("3.3 Component: SensorFusion", h1_style))
    fusion_name = "SensorFusionV2" if is_v2 else "SensorFusion"
    elements.append(Paragraph(
        f"Software Component: {fusion_name} performs spatial and temporal alignment of optical objects from CameraManager and radar clusters from RadarProcessor. "
        f"Using an Extended Kalman Filter (EKF) and Hungarian association algorithm, {fusion_name} synthesizes a unified environmental model. "
        f"It consumes CameraData from CameraManager and RadarData from RadarProcessor. It outputs the interface FusedObjectData.",
        body_style
    ))
    if is_v2:
        # Deliberate inconsistency introduction in v2: references ObjectFusionStatus without formal definition
        elements.append(Paragraph(
            "<b>Architectural Reference:</b> For functional safety diagnostics, SensorFusionV2 periodically outputs interface ObjectFusionStatus "
            "to monitor Kalman covariance convergence. (Note: Port configuration pending review).",
            body_style
        ))
    elements.append(Paragraph("Data Flow Description:", h2_style))
    elements.append(Paragraph(
        "CameraManager -> SensorFusion via Ethernet<br/>"
        "RadarProcessor -> SensorFusion via CAN-FD<br/>"
        "SensorFusion -> ADASController via Autosar RTE",
        body_style
    ))
    elements.append(PageBreak())

    # ================= PAGE 5: ADAS DECISION CONTROLLER =================
    elements.append(Paragraph("3.4 Component: ADASController", h1_style))
    elements.append(Paragraph(
        "Software Component: ADASController implements high-level supervisory decision logic, situation assessment, and motion planning. "
        "It evaluates target vehicle trajectories against host vehicle dynamics and assesses time-to-collision (TTC). "
        "ADASController consumes FusedObjectData from SensorFusion and VehicleState from VehicleInterface.",
        body_style
    ))
    elements.append(Paragraph(
        "When collision hazards exceed safety thresholds, ADASController generates autonomous deceleration and torque commands. "
        "It transmits commands to the braking subsystem.",
        body_style
    ))
    elements.append(Paragraph("Documented Architectural Dependencies:", h2_style))
    elements.append(Paragraph(
        "• ADASController depends on SensorFusion<br/>"
        "• ADASController depends on BrakeController<br/>"
        "• ADASController depends on VehicleInterface",
        body_style
    ))
    elements.append(PageBreak())

    # ================= PAGE 6: BRAKE CONTROLLER & ACTUATION =================
    elements.append(Paragraph("3.5 Component: BrakeController", h1_style))
    elements.append(Paragraph(
        "Software Component: BrakeController operates on the chassis safety partition. It coordinates electronic stability control (ESC) "
        "and electro-hydraulic braking actuators to achieve requested vehicle deceleration.",
        body_style
    ))
    if not is_v2:
        elements.append(Paragraph(
            "BrakeController consumes the interface BrakeCommand from ADASController over the dedicated Chassis CAN bus. "
            "Upon receipt of active braking flags, it builds hydraulic pressure in primary brake circuits within 120ms.",
            body_style
        ))
    else:
        # Deliberate inconsistency introduction: v2 refers to BrakeControlCommand on this page while page 18/catalog references BrakeCommand!
        elements.append(Paragraph(
            "BrakeController consumes the interface BrakeControlCommand from ADASController over Chassis CAN. "
            "Signal payload specifies target deceleration rate in m/s^2 and prefill pressure targets.",
            body_style
        ))
    elements.append(Paragraph("3.6 Component: VehicleInterface", h2_style))
    elements.append(Paragraph(
        "Software Component: VehicleInterface connects to the central vehicle CAN gateway. It samples vehicle dynamics sensors including "
        "wheel speed sensors, inertial measurement unit (IMU) yaw rates, and steering wheel angles. "
        "It provides the interface VehicleState to ADASController.",
        body_style
    ))
    elements.append(PageBreak())

    # ================= PAGE 7: COMMUNICATION INTERFACE CATALOG =================
    elements.append(Paragraph("4.0 Communication Interfaces & Port Catalog", h1_style))
    elements.append(Paragraph(
        "All inter-component communication is mediated by AUTOSAR Software Component Ports. Below is the formal interface specification matrix.",
        body_style
    ))
    
    if_rows = [
        [Paragraph("Interface Name", table_hdr), Paragraph("Provider", table_hdr), Paragraph("Consumer", table_hdr), Paragraph("Protocol", table_hdr), Paragraph("Signals", table_hdr)],
        [Paragraph("CameraData", table_cell), Paragraph("CameraManager", table_cell), Paragraph("SensorFusion", table_cell), Paragraph("Ethernet", table_cell), Paragraph("ImageFrame, TimeStamp", table_cell)],
        [Paragraph("RadarData", table_cell), Paragraph("RadarProcessor", table_cell), Paragraph("SensorFusion", table_cell), Paragraph("CAN-FD", table_cell), Paragraph("RadarTargetList, ClusterRange", table_cell)],
        [Paragraph("FusedObjectData", table_cell), Paragraph("SensorFusion", table_cell), Paragraph("ADASController", table_cell), Paragraph("Autosar RTE", table_cell), Paragraph("ObstacleDistance, TTC", table_cell)],
        [Paragraph("VehicleState", table_cell), Paragraph("VehicleInterface", table_cell), Paragraph("ADASController", table_cell), Paragraph("CAN", table_cell), Paragraph("WheelSpeed, YawRate", table_cell)],
        [Paragraph("BrakeCommand", table_cell), Paragraph("ADASController", table_cell), Paragraph("BrakeController", table_cell), Paragraph("CAN", table_cell), Paragraph("DecelerationRequest, BrakeActive", table_cell)]
    ]
    t_if = Table(if_rows, colWidths=[95, 95, 95, 75, 170])
    t_if.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
    ]))
    elements.append(t_if)
    elements.append(Spacer(1, 15))
    elements.append(Paragraph("Interface Protocol Mapping Details:", h2_style))
    elements.append(Paragraph(
        "• Ethernet 100BASE-T1: High bandwidth video transport between CameraManager and SensorFusion.<br/>"
        "• CAN-FD: High-integrity radar point clusters between RadarProcessor and SensorFusion.<br/>"
        "• Autosar RTE: Inter-core shared memory communication within ADAS Domain Controller.<br/>"
        "• Classic CAN 2.0B: Deterministic 500kbps communication to chassis ECUs for BrakeCommand and VehicleState.",
        body_style
    ))
    elements.append(PageBreak())

    # ================= PAGE 8: FUNCTIONAL FLOW - EMERGENCY BRAKING =================
    elements.append(Paragraph("5.0 Functional Flow: Autonomous Emergency Braking (AEB)", h1_style))
    elements.append(Paragraph(
        "The AEB feature execution sequence is defined as follows:",
        body_style
    ))
    elements.append(Paragraph(
        "Step 1: Front camera detects obstacle and produces CameraData.<br/>"
        "Step 2: Radar transceiver detects target range and produces RadarData.<br/>"
        "Step 3: SensorFusion combines signals and transmits FusedObjectData to ADASController.<br/>"
        "Step 4: ADASController evaluates vehicle speed from VehicleState and calculates TTC < 1.2s.<br/>"
        "Step 5: ADASController issues emergency BrakeCommand.<br/>"
        "Step 6: BrakeController actuates hydraulic calipers, achieving vehicle standstill.",
        body_style
    ))
    elements.append(Paragraph("Latency & Timing Budget:", h2_style))
    elements.append(Paragraph(
        "Total cycle budget is 50ms. Perception pipeline contributes 25ms, Decision logic contributes 10ms, and Actuator ramp-up contributes 15ms.",
        body_style
    ))
    elements.append(PageBreak())

    # ================= PAGE 9: SAFETY & ASIL TRACEABILITY =================
    elements.append(Paragraph("6.0 Functional Safety & Requirements Traceability", h1_style))
    elements.append(Paragraph(
        "In accordance with ISO 26262, the emergency braking function is allocated ASIL-D safety integrity. Software components must adhere to freedom from interference (FFI) memory partitioning.",
        body_style
    ))
    req_rows = [
        [Paragraph("Req ID", table_hdr), Paragraph("Component", table_hdr), Paragraph("ASIL", table_hdr), Paragraph("Safety Requirement Statement", table_hdr)],
        [Paragraph("REQ-ADAS-001", table_cell), Paragraph("ADASController", table_cell), Paragraph("ASIL-D", table_cell), Paragraph("The ADASController shall command maximum emergency deceleration when TTC drops below 0.8s.", table_cell)],
        [Paragraph("REQ-ADAS-002", table_cell), Paragraph("SensorFusion", table_cell), Paragraph("ASIL-B", table_cell), Paragraph("SensorFusion shall provide fused object tracks with 99.5% confidence within 35ms of sensor acquisition.", table_cell)],
        [Paragraph("REQ-ADAS-003", table_cell), Paragraph("BrakeController", table_cell), Paragraph("ASIL-D", table_cell), Paragraph("BrakeController shall achieve 8.5 m/s^2 deceleration within 180ms of receiving BrakeCommand.", table_cell)]
    ]
    t_req = Table(req_rows, colWidths=[90, 95, 55, 290])
    t_req.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
    ]))
    elements.append(t_req)
    elements.append(PageBreak())

    # ================= PAGE 10: ARCHITECTURAL DEPENDENCIES SUMMARY =================
    elements.append(Paragraph("7.0 Architectural Dependency & Coupling Analysis", h1_style))
    elements.append(Paragraph(
        "The software architecture enforces hierarchical, unidirectional dependencies to prevent circular deadlocks and ensure deterministic schedulability.",
        body_style
    ))
    elements.append(Paragraph("Documented Relationships & Communication Flows:", h2_style))
    elements.append(Paragraph(
        "1. CameraManager -> SensorFusion via Ethernet<br/>"
        "2. RadarProcessor -> SensorFusion via CAN-FD<br/>"
        "3. SensorFusion -> ADASController via Autosar RTE<br/>"
        "4. ADASController -> BrakeController via CAN<br/>"
        "5. ADASController -> VehicleInterface via CAN<br/>"
        "6. ADASController transmits data to BrakeController<br/>"
        "7. VehicleInterface transmits data to ADASController",
        body_style
    ))
    elements.append(Paragraph(
        "Component ADASController is identified as the central integration hub. Any changes to interfaces FusedObjectData, VehicleState, or BrakeCommand directly affect system schedulability.",
        body_style
    ))
    elements.append(PageBreak())

    # ================= PAGE 11: DIAGNOSTICS & AUDIT =================
    elements.append(Paragraph("8.0 Diagnostic & Audit Considerations", h1_style))
    elements.append(Paragraph(
        "Diagnostic services follow Unified Diagnostic Services (UDS) ISO 14229 over CAN. Component health monitors report internal plausibility errors to the Dem (Diagnostic Event Manager) module.",
        body_style
    ))
    elements.append(Paragraph(
        "Engineers reviewing this document must verify signal data types in AUTOSAR ARXML files against this High-Level Design baseline. "
        "All inconsistencies require human engineering evaluation.",
        body_style
    ))

    doc.build(elements)
    print(f"Generated synthetic demo HLD: {filename}")

if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "..", "data", "sample_documents")
    create_hld_pdf(os.path.join(out_dir, "ADAS_HLD_v1.0.pdf"), version="1.0", is_v2=False)
    create_hld_pdf(os.path.join(out_dir, "ADAS_HLD_v2.0.pdf"), version="2.0", is_v2=True)
