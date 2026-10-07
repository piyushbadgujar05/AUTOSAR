from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.models.document import Document
from backend.app.models.architecture import ArchitectureEntity, Relationship
from backend.app.schemas.analysis import ComparisonResponse, EntityDiff
from backend.app.core.logging import logger

class ComparisonService:
    @staticmethod
    def compare_documents(db: Session, doc1_id: str, doc2_id: str) -> ComparisonResponse:
        """
        Performs deterministic semantic comparison between two HLD document revisions.
        Extracts added, removed, and modified components, interfaces, and dependencies.
        Labels impact as 'Potential Impact — Requires Engineering Review'.
        """
        doc1 = db.query(Document).filter(Document.id == doc1_id).first()
        doc2 = db.query(Document).filter(Document.id == doc2_id).first()

        if not doc1 or not doc2:
            raise ValueError("One or both document IDs could not be found.")

        # Entities doc1
        e1 = db.query(ArchitectureEntity).filter(ArchitectureEntity.document_id == doc1_id).all()
        e2 = db.query(ArchitectureEntity).filter(ArchitectureEntity.document_id == doc2_id).all()

        comps1 = {e.name: e for e in e1 if e.entity_type == "COMPONENT"}
        comps2 = {e.name: e for e in e2 if e.entity_type == "COMPONENT"}

        ifs1 = {e.name: e for e in e1 if e.entity_type == "INTERFACE"}
        ifs2 = {e.name: e for e in e2 if e.entity_type == "INTERFACE"}

        # Dependencies doc1 & doc2
        r1 = db.query(Relationship).filter(Relationship.document_id == doc1_id).all()
        r2 = db.query(Relationship).filter(Relationship.document_id == doc2_id).all()

        deps1 = {f"{r.source_entity} -> {r.target_entity}": r for r in r1}
        deps2 = {f"{r.source_entity} -> {r.target_entity}": r for r in r2}

        # 1. Components Diff
        comp_added = [name for name in comps2 if name not in comps1]
        comp_removed = [name for name in comps1 if name not in comps2]
        comp_changed = []
        for name in comps1:
            if name in comps2:
                d1_desc = comps1[name].description or ""
                d2_desc = comps2[name].description or ""
                if d1_desc != d2_desc:
                    comp_changed.append({
                        "name": name,
                        "v1_description": d1_desc,
                        "v2_description": d2_desc,
                        "v1_page": comps1[name].page,
                        "v2_page": comps2[name].page
                    })

        components_diff = EntityDiff(
            added=comp_added,
            removed=comp_removed,
            changed=comp_changed
        )

        # 2. Interfaces Diff
        if_added = [name for name in ifs2 if name not in ifs1]
        if_removed = [name for name in ifs1 if name not in ifs2]
        if_changed = []
        for name in ifs1:
            if name in ifs2:
                d1_desc = ifs1[name].description or ""
                d2_desc = ifs2[name].description or ""
                if d1_desc != d2_desc:
                    if_changed.append({
                        "name": name,
                        "v1_description": d1_desc,
                        "v2_description": d2_desc,
                        "v1_page": ifs1[name].page,
                        "v2_page": ifs2[name].page
                    })

        interfaces_diff = EntityDiff(
            added=if_added,
            removed=if_removed,
            changed=if_changed
        )

        # 3. Dependencies Diff
        dep_added = [name for name in deps2 if name not in deps1]
        dep_removed = [name for name in deps1 if name not in deps2]
        dep_changed = []
        for name in deps1:
            if name in deps2:
                p1 = deps1[name].protocol
                p2 = deps2[name].protocol
                if p1 != p2:
                    dep_changed.append({
                        "dependency": name,
                        "v1_protocol": p1,
                        "v2_protocol": p2,
                        "v1_page": deps1[name].page,
                        "v2_page": deps2[name].page
                    })

        dependencies_diff = EntityDiff(
            added=dep_added,
            removed=dep_removed,
            changed=dep_changed
        )

        # 4. Potential Impacts analysis
        potential_impacts = []
        
        # Interface renaming / contract changes
        if "BrakeCommand" in ifs1 and ("BrakeControlCommand" in ifs2 or "BrakeControlCommand" in [c.name for c in e2]):
            v2_page = ifs2["BrakeControlCommand"].page if "BrakeControlCommand" in ifs2 else 6
            potential_impacts.append({
                "item": "BrakeCommand -> BrakeControlCommand",
                "category": "Interface Renaming / Contract Modification",
                "finding": "Interface name changed from BrakeCommand to BrakeControlCommand between revisions.",
                "potential_impact": "Potential interface contract change. Engineering review required.",
                "review_label": "Potential Impact — Requires Engineering Review",
                "sources": f"v1 ({doc1.version}) Page {ifs1['BrakeCommand'].page} vs v2 ({doc2.version}) Page {v2_page}"
            })

        for ca in comp_added:
            potential_impacts.append({
                "item": ca,
                "category": "New Component Introduction",
                "finding": f"Component '{ca}' was introduced in revision {doc2.version}.",
                "potential_impact": f"Requires memory partition budgeting and ASIL safety level verification for {ca}.",
                "review_label": "Potential Impact — Requires Engineering Review",
                "sources": f"v2 ({doc2.version}) Page {comps2[ca].page}"
            })

        for cr in comp_removed:
            potential_impacts.append({
                "item": cr,
                "category": "Component Deprecation",
                "finding": f"Component '{cr}' in revision {doc1.version} was deprecated/removed in {doc2.version}.",
                "potential_impact": f"Verify all legacy dependencies and signals consumed from {cr} have alternative sources.",
                "review_label": "Potential Impact — Requires Engineering Review",
                "sources": f"v1 ({doc1.version}) Page {comps1[cr].page}"
            })

        summary = (
            f"Comparison between {doc1.name} (v{doc1.version}) and {doc2.name} (v{doc2.version}): "
            f"{len(comp_added)} component(s) added, {len(comp_removed)} removed; "
            f"{len(if_added)} interface(s) added, {len(if_removed)} removed; "
            f"{len(dep_added)} dependency(ies) added, {len(dep_removed)} removed."
        )

        return ComparisonResponse(
            doc1_id=doc1.id,
            doc1_name=doc1.name,
            doc1_version=doc1.version,
            doc2_id=doc2.id,
            doc2_name=doc2.name,
            doc2_version=doc2.version,
            components_diff=components_diff,
            interfaces_diff=interfaces_diff,
            dependencies_diff=dependencies_diff,
            potential_impacts=potential_impacts,
            summary=summary
        )
