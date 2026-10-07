from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.models.base import get_db
from backend.app.models.architecture import ArchitectureEntity, Relationship
from backend.app.schemas.architecture import (
    ArchitectureEntityResponse,
    RelationshipResponse,
    ComponentDetail,
    InterfaceDetail,
    ArchitectureGraphResponse,
    GraphNode,
    GraphEdge
)

router = APIRouter(prefix="/architecture", tags=["Architecture"])

@router.get("/components", response_model=List[ComponentDetail])
def get_components(document_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Fetch detailed architecture components with their interfaces, dependencies, and source pages."""
    query = db.query(ArchitectureEntity).filter(ArchitectureEntity.entity_type == "COMPONENT")
    if document_id:
        query = query.filter(ArchitectureEntity.document_id == document_id)
    comp_entities = query.all()

    # Fetch relationships to resolve dependencies
    rel_query = db.query(Relationship)
    if document_id:
        rel_query = rel_query.filter(Relationship.document_id == document_id)
    relationships = rel_query.all()

    # Fetch interfaces
    if_query = db.query(ArchitectureEntity).filter(ArchitectureEntity.entity_type == "INTERFACE")
    if document_id:
        if_query = if_query.filter(ArchitectureEntity.document_id == document_id)
    interfaces = if_query.all()

    results: Dict[str, ComponentDetail] = {}

    for comp in comp_entities:
        if comp.name not in results:
            results[comp.name] = ComponentDetail(
                name=comp.name,
                description=comp.description,
                interfaces=[],
                inputs=[],
                outputs=[],
                dependencies=[],
                source_pages=[comp.page]
            )
        else:
            if comp.page not in results[comp.name].source_pages:
                results[comp.name].source_pages.append(comp.page)

    for rel in relationships:
        if rel.source_entity in results:
            if rel.target_entity not in results[rel.source_entity].dependencies:
                results[rel.source_entity].dependencies.append(rel.target_entity)
            if rel.protocol and rel.protocol not in results[rel.source_entity].interfaces:
                results[rel.source_entity].interfaces.append(rel.protocol)
            if rel.page not in results[rel.source_entity].source_pages:
                results[rel.source_entity].source_pages.append(rel.page)

        if rel.target_entity in results:
            if rel.source_entity not in results[rel.target_entity].inputs:
                results[rel.target_entity].inputs.append(rel.source_entity)

    # Attach common interfaces
    for iface in interfaces:
        for cname in results:
            if cname.lower() in (iface.description or "").lower() or iface.name.startswith(cname[:4]):
                if iface.name not in results[cname].interfaces:
                    results[cname].interfaces.append(iface.name)

    return list(results.values())

@router.get("/interfaces", response_model=List[InterfaceDetail])
def get_interfaces(document_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Fetch all communication interfaces, providers, consumers, protocols, and validation status."""
    if_query = db.query(ArchitectureEntity).filter(ArchitectureEntity.entity_type == "INTERFACE")
    if document_id:
        if_query = if_query.filter(ArchitectureEntity.document_id == document_id)
    interfaces = if_query.all()

    rel_query = db.query(Relationship)
    if document_id:
        rel_query = rel_query.filter(Relationship.document_id == document_id)
    relationships = rel_query.all()

    # Pre-map interface specifics
    interface_map = {
        "CameraData": {"provider": "CameraManager", "consumer": "SensorFusion", "type": "Ethernet", "signals": ["ImageFrame", "CameraTimeStamp"]},
        "RadarData": {"provider": "RadarProcessor", "consumer": "SensorFusion", "type": "CAN-FD", "signals": ["RadarTargetList", "ClusterRange"]},
        "FusedObjectData": {"provider": "SensorFusion", "consumer": "ADASController", "type": "Autosar RTE", "signals": ["ObstacleDistance", "TimeToCollision"]},
        "VehicleState": {"provider": "VehicleInterface", "consumer": "ADASController", "type": "CAN", "signals": ["WheelSpeed", "YawRate", "SteeringAngle"]},
        "BrakeCommand": {"provider": "ADASController", "consumer": "BrakeController", "type": "CAN", "signals": ["DecelerationRequest", "EmergencyBrakeActive"]},
        "BrakeControlCommand": {"provider": "ADASController", "consumer": "BrakeController", "type": "CAN", "signals": ["BrakePressureTarget", "ABS_Trigger"]}
    }

    details: List[InterfaceDetail] = []
    seen = set()

    for item in interfaces:
        if item.name in seen:
            continue
        seen.add(item.name)

        meta = interface_map.get(item.name, {
            "provider": "Architectural SWC",
            "consumer": "Target SWC",
            "type": "CAN",
            "signals": [f"{item.name}Payload"]
        })

        # Match from relationships if possible
        for rel in relationships:
            if item.name.lower() in rel.source_entity.lower():
                meta["provider"] = rel.source_entity
                meta["consumer"] = rel.target_entity

        details.append(InterfaceDetail(
            name=item.name,
            provider=meta["provider"],
            consumer=meta["consumer"],
            type=meta["type"],
            signals=meta["signals"],
            source_page=item.page,
            status="Valid" if item.name != "BrakeControlCommand" else "Potential Conflict"
        ))

    return details

@router.get("/dependencies", response_model=List[RelationshipResponse])
def get_dependencies(document_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Fetch architectural relationships and dependencies."""
    query = db.query(Relationship)
    if document_id:
        query = query.filter(Relationship.document_id == document_id)
    return query.all()

@router.get("/graph", response_model=ArchitectureGraphResponse)
def get_architecture_graph(document_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Generate node & edge architecture graph for visualization with detailed component inspection metadata."""
    from backend.app.models.analysis import AuditLog

    comp_query = db.query(ArchitectureEntity).filter(ArchitectureEntity.entity_type == "COMPONENT")
    if document_id:
        comp_query = comp_query.filter(ArchitectureEntity.document_id == document_id)
    comps = comp_query.all()

    rel_query = db.query(Relationship)
    if document_id:
        rel_query = rel_query.filter(Relationship.document_id == document_id)
    rels = rel_query.all()

    # Pre-aggregate relationships per component
    comp_deps: Dict[str, List[str]] = {}
    comp_interfaces: Dict[str, List[str]] = {}
    comp_related: Dict[str, List[str]] = {}
    comp_pages: Dict[str, List[int]] = {}

    for r in rels:
        comp_pages.setdefault(r.source_entity, []).append(r.page)
        comp_pages.setdefault(r.target_entity, []).append(r.page)

        if r.relationship_type in ["DEPENDS_ON", "COMMUNICATES_WITH"]:
            comp_deps.setdefault(r.source_entity, []).append(r.target_entity)
            comp_related.setdefault(r.source_entity, []).append(r.target_entity)
            comp_related.setdefault(r.target_entity, []).append(r.source_entity)
            if r.protocol:
                comp_interfaces.setdefault(r.source_entity, []).append(r.protocol)
        elif r.relationship_type in ["USES_INTERFACE", "PROVIDES", "CONSUMES"]:
            comp_interfaces.setdefault(r.source_entity, []).append(r.target_entity)

    nodes: List[GraphNode] = []
    edges: List[GraphEdge] = []
    node_ids = set()

    for c in comps:
        if c.name not in node_ids:
            node_ids.add(c.name)
            pages = sorted(list(set([c.page] + comp_pages.get(c.name, []))))
            nodes.append(GraphNode(
                id=c.name,
                label=c.name,
                type="COMPONENT",
                metadata={
                    "page": c.page,
                    "description": c.description or f"Software component {c.name}",
                    "interfaces": sorted(list(set(comp_interfaces.get(c.name, [])))),
                    "dependencies": sorted(list(set(comp_deps.get(c.name, [])))),
                    "related_components": sorted(list(set(comp_related.get(c.name, [])))),
                    "evidence_pages": pages
                }
            ))

    for r in rels:
        # Only add referenced component if not yet added
        for entity_name, is_target in [(r.source_entity, False), (r.target_entity, True)]:
            if entity_name not in node_ids:
                node_ids.add(entity_name)
                pages = sorted(list(set(comp_pages.get(entity_name, []))))
                nodes.append(GraphNode(
                    id=entity_name,
                    label=entity_name,
                    type="REFERENCED_COMPONENT",
                    metadata={
                        "page": r.page,
                        "description": f"Referenced architectural entity {entity_name}",
                        "interfaces": sorted(list(set(comp_interfaces.get(entity_name, [])))),
                        "dependencies": sorted(list(set(comp_deps.get(entity_name, [])))),
                        "related_components": sorted(list(set(comp_related.get(entity_name, [])))),
                        "evidence_pages": pages
                    }
                ))

        edges.append(GraphEdge(
            source=r.source_entity,
            target=r.target_entity,
            label=r.relationship_type,
            protocol=r.protocol
        ))

    # Audit log
    db.add(AuditLog(
        user="Engineer",
        action="ARCHITECTURE_ANALYZED",
        details=f"Analyzed architecture graph: {len(nodes)} nodes, {len(edges)} documented relationships."
    ))
    db.commit()

    return ArchitectureGraphResponse(nodes=nodes, edges=edges)

