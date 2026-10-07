import re
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.app.models.architecture import ArchitectureEntity, Relationship
from backend.app.core.logging import logger

class ExtractionService:
    @staticmethod
    def extract_architecture_from_chunks(
        db: Session,
        document_id: str,
        document_name: str,
        chunks: List[Dict[str, Any]]
    ) -> Tuple[List[ArchitectureEntity], List[Relationship]]:
        """
        Parses document chunks to extract automotive architectural entities and relationships:
        COMPONENTS, INTERFACES, PORTS, SIGNALS, DEPENDENCIES, DATA FLOWS, PROTOCOLS, REQUIREMENTS.
        """
        entities: List[ArchitectureEntity] = []
        relationships: List[Relationship] = []

        seen_entities = set()
        seen_relationships = set()

        for chunk in chunks:
            page_num = chunk.get("page_number", 1)
            text = chunk.get("content", "")

            # 1. Component Extraction
            # Patterns: "Component: X", "Software Component: X", "SWC: X", or architectural definitions
            comp_patterns = [
                r'(?:Software Component|Component|SWC)\s*[:\-]\s*([A-Za-z0-9_]+)(?:\s*\(?([^\n\)]*)\)?)?',
                r'(?:The\s+)?([A-Za-z0-9_]+Controller|[A-Za-z0-9_]+Manager|[A-Za-z0-9_]+Processor|[A-Za-z0-9_]+Fusion|[A-Za-z0-9_]+Interface)\b'
            ]

            for pat in comp_patterns:
                for match in re.finditer(pat, text):
                    name = match.group(1).strip()
                    # Skip generic words
                    if name.lower() in ["the", "this", "an", "a", "software", "component", "interface"]:
                        continue
                    
                    key = ("COMPONENT", name)
                    if key not in seen_entities:
                        seen_entities.add(key)
                        desc = f"Software component documented on page {page_num}."
                        # Extract description snippet if available
                        lines = [l for l in text.splitlines() if name in l]
                        if lines:
                            desc = lines[0].strip()[:200]
                        
                        entities.append(ArchitectureEntity(
                            document_id=document_id,
                            entity_type="COMPONENT",
                            name=name,
                            description=desc,
                            page=page_num,
                            confidence=0.92
                        ))

            # 2. Interface Extraction
            # Patterns: "Interface: X", "Port/Interface X", "CameraData", "BrakeCommand"
            if_patterns = [
                r'(?:Interface|Sender-Receiver Interface|Client-Server Interface)\s*[:\-]\s*([A-Za-z0-9_]+)(?:\s*\(?([^\n\)]*)\)?)?',
                r'\b([A-Za-z0-9_]+(?:Data|Command|State|Frame|Request|Signal|Payload))\b'
            ]
            for pat in if_patterns:
                for match in re.finditer(pat, text):
                    name = match.group(1).strip()
                    if name.lower() in ["interface", "command", "data", "state", "signal"]:
                        continue
                    key = ("INTERFACE", name)
                    if key not in seen_entities:
                        seen_entities.add(key)
                        entities.append(ArchitectureEntity(
                            document_id=document_id,
                            entity_type="INTERFACE",
                            name=name,
                            description=f"Communication interface specified on page {page_num}.",
                            page=page_num,
                            confidence=0.89
                        ))

            # 3. Protocols (CAN, Ethernet, Autosar RTE, FlexRay, LIN, SPI)
            protocol_matches = re.findall(r'\b(CAN|CAN-FD|Ethernet|Autosar RTE|FlexRay|LIN|SPI|SOME/IP)\b', text, re.IGNORECASE)
            for proto in protocol_matches:
                proto_map = {
                    "can": "CAN",
                    "can-fd": "CAN-FD",
                    "ethernet": "Ethernet",
                    "autosar rte": "Autosar RTE",
                    "flexray": "FlexRay",
                    "lin": "LIN",
                    "spi": "SPI",
                    "some/ip": "SOME/IP"
                }
                proto_clean = proto_map.get(proto.lower(), proto)
                key = ("PROTOCOL", proto_clean)
                if key not in seen_entities:
                    seen_entities.add(key)
                    entities.append(ArchitectureEntity(
                        document_id=document_id,
                        entity_type="PROTOCOL",
                        name=proto_clean,
                        description=f"Automotive communication protocol referenced on page {page_num}.",
                        page=page_num,
                        confidence=0.95
                    ))

            # 4. Signals (e.g. BrakeRequest, ImageFrame, RadarTargetList, WheelSpeed)
            sig_matches = re.finditer(r'(?:Signal|Payload|Variable)\s*[:\-]\s*([A-Za-z0-9_]+)', text, re.IGNORECASE)
            for sm in sig_matches:
                sname = sm.group(1).strip()
                key = ("SIGNAL", sname)
                if key not in seen_entities:
                    seen_entities.add(key)
                    entities.append(ArchitectureEntity(
                        document_id=document_id,
                        entity_type="SIGNAL",
                        name=sname,
                        description=f"Signal definition extracted from page {page_num}.",
                        page=page_num,
                        confidence=0.88
                    ))

            # 5. Ports (e.g. PPort_BrakeCmd, RPort_RadarData, Port: AccStatus)
            port_matches = re.finditer(r'\b(PPort_[A-Za-z0-9_]+|RPort_[A-Za-z0-9_]+|PRPort_[A-Za-z0-9_]+)\b|(?:Port|RTE Port)\s*[:\-]\s*([A-Za-z0-9_]+)', text, re.IGNORECASE)
            for pm in port_matches:
                pname = (pm.group(1) or pm.group(2)).strip()
                if pname.lower() not in ["port", "the", "an"]:
                    key = ("PORT", pname)
                    if key not in seen_entities:
                        seen_entities.add(key)
                        entities.append(ArchitectureEntity(
                            document_id=document_id,
                            entity_type="PORT",
                            name=pname,
                            description=f"AUTOSAR port interface definition on page {page_num}.",
                            page=page_num,
                            confidence=0.91
                        ))

            # 6. Functions / Runnables
            func_matches = re.finditer(r'(?:Function|Runnable|Runnable Entity|Process)\s*[:\-]\s*([A-Za-z0-9_]+)|\b(Runnable_[A-Za-z0-9_]+|re_[A-Za-z0-9_]+)\b', text, re.IGNORECASE)
            for fm in func_matches:
                fname = (fm.group(1) or fm.group(2)).strip()
                if fname.lower() not in ["function", "runnable", "process", "the"]:
                    key = ("FUNCTION", fname)
                    if key not in seen_entities:
                        seen_entities.add(key)
                        entities.append(ArchitectureEntity(
                            document_id=document_id,
                            entity_type="FUNCTION",
                            name=fname,
                            description=f"Executable function or runnable entity on page {page_num}.",
                            page=page_num,
                            confidence=0.90
                        ))

            # 7. Data Flows
            flow_matches = re.finditer(r'(?:Data Flow|DataFlow|Signal Flow)\s*[:\-]\s*([A-Za-z0-9_\s\->]+)', text, re.IGNORECASE)
            for flm in flow_matches:
                flname = flm.group(1).strip()
                if len(flname) > 3 and len(flname) < 60:
                    key = ("DATA_FLOW", flname)
                    if key not in seen_entities:
                        seen_entities.add(key)
                        entities.append(ArchitectureEntity(
                            document_id=document_id,
                            entity_type="DATA_FLOW",
                            name=flname,
                            description=f"Architecture data flow definition on page {page_num}.",
                            page=page_num,
                            confidence=0.88
                        ))

            # 8. Requirements (e.g. REQ-ADAS-001, REQ_SWC_102)
            req_matches = re.finditer(r'\b(REQ[-_][A-Za-z0-9\-_]+)\b', text)
            for rm in req_matches:
                rname = rm.group(1).strip()
                key = ("REQUIREMENT", rname)
                if key not in seen_entities:
                    seen_entities.add(key)
                    entities.append(ArchitectureEntity(
                        document_id=document_id,
                        entity_type="REQUIREMENT",
                        name=rname,
                        description=f"Automotive architecture requirement referenced on page {page_num}.",
                        page=page_num,
                        confidence=0.95
                    ))

            # 9. Relationships & Dependencies
            for line in text.splitlines():
                # Direct arrow notation: e.g. "CameraManager -> SensorFusion via Ethernet"
                arrow_match = re.search(r'([A-Za-z0-9_]+)\s*->\s*([A-Za-z0-9_]+)(?:\s*(?:via|using)\s*([A-Za-z0-9_\-]+))?', line)
                if arrow_match:
                    src = arrow_match.group(1).strip()
                    tgt = arrow_match.group(2).strip()
                    proto = arrow_match.group(3).strip() if arrow_match.group(3) else "CAN"
                    if src != tgt and len(src) > 2 and len(tgt) > 2 and src.lower() not in ["the", "this"]:
                        rel_key = (src, "DEPENDS_ON", tgt)
                        if rel_key not in seen_relationships:
                            seen_relationships.add(rel_key)
                            relationships.append(Relationship(
                                document_id=document_id,
                                source_entity=src,
                                relationship_type="DEPENDS_ON",
                                target_entity=tgt,
                                protocol=proto,
                                page=page_num,
                                confidence=0.92
                            ))

                # "A provides B to C"
                prov_to_match = re.search(r'([A-Za-z0-9_]+)\s+provides\s+(?:the\s+)?(?:interface\s+)?([A-Za-z0-9_]+)\s+to\s+([A-Za-z0-9_]+)', line, re.IGNORECASE)
                if prov_to_match:
                    src, iface, tgt = prov_to_match.group(1).strip(), prov_to_match.group(2).strip(), prov_to_match.group(3).strip()
                    k1 = (src, "PROVIDES", iface)
                    if k1 not in seen_relationships:
                        seen_relationships.add(k1)
                        relationships.append(Relationship(
                            document_id=document_id, source_entity=src, relationship_type="PROVIDES", target_entity=iface, protocol="Autosar RTE", page=page_num, confidence=0.94
                        ))
                    k2 = (tgt, "CONSUMES", iface)
                    if k2 not in seen_relationships:
                        seen_relationships.add(k2)
                        relationships.append(Relationship(
                            document_id=document_id, source_entity=tgt, relationship_type="CONSUMES", target_entity=iface, protocol="Autosar RTE", page=page_num, confidence=0.94
                        ))
                    k3 = (src, "DEPENDS_ON", tgt)
                    if k3 not in seen_relationships:
                        seen_relationships.add(k3)
                        relationships.append(Relationship(
                            document_id=document_id, source_entity=src, relationship_type="DEPENDS_ON", target_entity=tgt, protocol=iface, page=page_num, confidence=0.90
                        ))

                # "A provides [interface] B"
                prov_match = re.search(r'([A-Za-z0-9_]+)\s+provides\s+(?:the\s+)?(?:interface\s+)?([A-Za-z0-9_]+)', line, re.IGNORECASE)
                if prov_match and not prov_to_match:
                    src, iface = prov_match.group(1).strip(), prov_match.group(2).strip()
                    if iface.lower() not in ["the", "an", "data", "to"]:
                        k = (src, "PROVIDES", iface)
                        if k not in seen_relationships:
                            seen_relationships.add(k)
                            relationships.append(Relationship(
                                document_id=document_id, source_entity=src, relationship_type="PROVIDES", target_entity=iface, protocol="Autosar RTE", page=page_num, confidence=0.91
                            ))

                # "A consumes [interface] B"
                cons_match = re.search(r'([A-Za-z0-9_]+)\s+consumes\s+(?:the\s+)?(?:interface\s+)?([A-Za-z0-9_]+)', line, re.IGNORECASE)
                if cons_match:
                    src, iface = cons_match.group(1).strip(), cons_match.group(2).strip()
                    if iface.lower() not in ["the", "an", "data", "from"]:
                        k = (src, "CONSUMES", iface)
                        if k not in seen_relationships:
                            seen_relationships.add(k)
                            relationships.append(Relationship(
                                document_id=document_id, source_entity=src, relationship_type="CONSUMES", target_entity=iface, protocol="Autosar RTE", page=page_num, confidence=0.91
                            ))

                # "A communicates with B through/using C interface" or "sends C to B"
                comm_if_match = re.search(r'([A-Za-z0-9_]+)\s+(?:communicates with|connects to)\s+([A-Za-z0-9_]+)\s+(?:through|using|via)\s+(?:the\s+)?([A-Za-z0-9_]+)(?:\s+interface)?', line, re.IGNORECASE)
                if comm_if_match:
                    src, tgt, iface = comm_if_match.group(1).strip(), comm_if_match.group(2).strip(), comm_if_match.group(3).strip()
                    k_use = (src, "USES_INTERFACE", iface)
                    if k_use not in seen_relationships:
                        seen_relationships.add(k_use)
                        relationships.append(Relationship(
                            document_id=document_id, source_entity=src, relationship_type="USES_INTERFACE", target_entity=iface, protocol="Autosar RTE", page=page_num, confidence=0.92
                        ))
                    k_comm = (src, "COMMUNICATES_WITH", tgt)
                    if k_comm not in seen_relationships:
                        seen_relationships.add(k_comm)
                        relationships.append(Relationship(
                            document_id=document_id, source_entity=src, relationship_type="COMMUNICATES_WITH", target_entity=tgt, protocol=iface, page=page_num, confidence=0.90
                        ))

                # "A sends B to C"
                send_match = re.search(r'([A-Za-z0-9_]+)\s+sends\s+([A-Za-z0-9_]+)\s+to\s+([A-Za-z0-9_]+)', line, re.IGNORECASE)
                if send_match:
                    src, sig, tgt = send_match.group(1).strip(), send_match.group(2).strip(), send_match.group(3).strip()
                    k_use = (src, "USES_INTERFACE", sig)
                    if k_use not in seen_relationships:
                        seen_relationships.add(k_use)
                        relationships.append(Relationship(
                            document_id=document_id, source_entity=src, relationship_type="USES_INTERFACE", target_entity=sig, protocol="CAN", page=page_num, confidence=0.92
                        ))

                # "X depends on Y"
                dep_match = re.search(r'([A-Za-z0-9_]+)\s+depends\s+on\s+([A-Za-z0-9_]+)', line, re.IGNORECASE)
                if dep_match:
                    src = dep_match.group(1).strip()
                    tgt = dep_match.group(2).strip()
                    if src != tgt and len(src) > 2 and len(tgt) > 2:
                        rel_key = (src, "DEPENDS_ON", tgt)
                        if rel_key not in seen_relationships:
                            seen_relationships.add(rel_key)
                            relationships.append(Relationship(
                                document_id=document_id,
                                source_entity=src,
                                relationship_type="DEPENDS_ON",
                                target_entity=tgt,
                                protocol="Autosar RTE",
                                page=page_num,
                                confidence=0.90
                            ))

                # "X communicates with Y" / "transmits to"
                comm_match = re.search(r'([A-Za-z0-9_]+)\s+(?:transmits|communicates)\s+(?:data\s+)?to\s+([A-Za-z0-9_]+)(?:\s+via\s+([A-Za-z0-9_]+))?', line, re.IGNORECASE)
                if comm_match and not comm_if_match:
                    src = comm_match.group(1).strip()
                    tgt = comm_match.group(2).strip()
                    proto = comm_match.group(3).strip() if comm_match.group(3) else "CAN"
                    if src != tgt and len(src) > 2 and len(tgt) > 2:
                        rel_key = (src, "COMMUNICATES_WITH", tgt)
                        if rel_key not in seen_relationships:
                            seen_relationships.add(rel_key)
                            relationships.append(Relationship(
                                document_id=document_id,
                                source_entity=src,
                                relationship_type="COMMUNICATES_WITH",
                                target_entity=tgt,
                                protocol=proto,
                                page=page_num,
                                confidence=0.88
                            ))

        # Save to DB
        for ent in entities:
            db.add(ent)
        for rel in relationships:
            db.add(rel)
        db.commit()

        logger.info(f"Extracted {len(entities)} architecture entities and {len(relationships)} relationships for document {document_id}")
        return entities, relationships

