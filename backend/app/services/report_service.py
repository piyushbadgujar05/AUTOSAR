import os
import json
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from backend.app.models.document import Document
from backend.app.models.architecture import ArchitectureEntity, Relationship
from backend.app.models.analysis import Finding, Review
from backend.app.core.config import settings
from backend.app.core.logging import logger

class ReportService:
    @staticmethod
    def generate_report_data(db: Session, document_id: str) -> Dict[str, Any]:
        """Aggregate all architecture knowledge, findings, and review statuses into a structured dictionary with all 10 required sections."""
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise ValueError(f"Document with ID {document_id} not found.")

        entities = db.query(ArchitectureEntity).filter(ArchitectureEntity.document_id == document_id).all()
        relationships = db.query(Relationship).filter(Relationship.document_id == document_id).all()
        findings = db.query(Finding).filter(Finding.document_id == document_id).all()

        components = [
            {"name": e.name, "description": e.description, "page": e.page, "confidence": e.confidence}
            for e in entities if e.entity_type == "COMPONENT"
        ]

        interfaces = [
            {"name": e.name, "description": e.description, "page": e.page, "confidence": e.confidence}
            for e in entities if e.entity_type == "INTERFACE"
        ]

        dependencies = [
            {"source": r.source_entity, "relationship": r.relationship_type, "target": r.target_entity, "protocol": r.protocol or "CAN", "page": r.page}
            for r in relationships
        ]

        findings_list = []
        review_statuses = []
        evidence_items = []

        for f in findings:
            f_reviews = [
                {"reviewer": r.reviewer, "status": r.status, "comment": r.comment or "", "timestamp": r.timestamp.isoformat()}
                for r in f.reviews
            ]
            findings_list.append({
                "id": f.id,
                "title": f.title,
                "type": f.finding_type,
                "severity": f.severity,
                "confidence": f.confidence,
                "status": f.status,
                "source_page": f.source_page,
                "description": f.description,
                "evidence": f.evidence or f"Document evidence cited on page {f.source_page}"
            })

            if f.evidence:
                evidence_items.append({
                    "finding_id": f.id,
                    "finding_title": f.title,
                    "page": f.source_page,
                    "evidence": f.evidence
                })

            review_statuses.append({
                "finding_id": f.id,
                "title": f.title,
                "current_status": f.status,
                "review_count": len(f_reviews),
                "latest_comment": f_reviews[-1]["comment"] if f_reviews else "Awaiting human review"
            })

        # Check for revision changes against prior revisions in same project
        prior_docs = db.query(Document).filter(
            Document.project == doc.project,
            Document.id != doc.id
        ).all()
        revision_changes = []
        for pdoc in prior_docs:
            p_entities = db.query(ArchitectureEntity).filter(ArchitectureEntity.document_id == pdoc.id).all()
            p_comp_names = set(e.name for e in p_entities if e.entity_type == "COMPONENT")
            curr_comp_names = set(c["name"] for c in components)
            added_c = curr_comp_names - p_comp_names
            removed_c = p_comp_names - curr_comp_names

            if added_c or removed_c:
                revision_changes.append({
                    "compared_with": f"{pdoc.name} (v{pdoc.version})",
                    "added_components": list(added_c),
                    "removed_components": list(removed_c),
                    "note": f"Revision {doc.version} delta versus baseline {pdoc.version}"
                })

        return {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "system": "AUTOSAR HLD Document Analysis Assistant",
                "disclaimer": "This is an AI-assisted engineering report. Not an autonomous formal architecture sign-off."
            },
            "1_project": {
                "project_name": doc.project,
                "target_platform": "AUTOSAR Domain Controller"
            },
            "2_document": {
                "document_name": doc.name,
                "version": doc.version,
                "document_type": doc.document_type,
                "total_pages": doc.total_pages,
                "indexed_chunks": doc.chunk_count,
                "status": doc.status
            },
            "3_architecture_summary": {
                "components_count": len(components),
                "interfaces_count": len(interfaces),
                "dependencies_count": len(dependencies),
                "findings_count": len(findings_list)
            },
            "4_components": components,
            "5_interfaces": interfaces,
            "6_dependencies": dependencies,
            "7_consistency_findings": findings_list,
            "8_revision_changes": revision_changes,
            "9_evidence": evidence_items,
            "10_review_status": review_statuses
        }

    @staticmethod
    def generate_pdf_report(report_data: Dict[str, Any], output_path: str) -> str:
        """Generate a complete 10-section formal PDF engineering report using ReportLab."""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('RptTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, textColor=colors.HexColor('#0F172A'), spaceAfter=4)
        subtitle_style = ParagraphStyle('RptSub', parent=styles['Normal'], fontName='Helvetica', fontSize=9, textColor=colors.HexColor('#475569'), spaceAfter=12)
        h2_style = ParagraphStyle('RptH2', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor('#1E293B'), spaceBefore=10, spaceAfter=4)
        body_style = ParagraphStyle('RptBody', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=colors.HexColor('#334155'), leading=11)
        th_style = ParagraphStyle('RptTH', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, textColor=colors.white, leading=10)
        td_style = ParagraphStyle('RptTD', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=colors.HexColor('#1E293B'), leading=10)

        elements = []

        # Header
        elements.append(Paragraph("AUTOSAR Architecture Analysis & Verification Report", title_style))
        elements.append(Paragraph(
            f"Generated: {report_data['metadata']['generated_at']} | Tool: {report_data['metadata']['system']}<br/>"
            f"<b>Notice:</b> {report_data['metadata']['disclaimer']}",
            subtitle_style
        ))
        elements.append(Spacer(1, 6))

        # 1. Project & 2. Document Information
        elements.append(Paragraph("1. Project & 2. Document Specification", h2_style))
        proj = report_data.get("1_project", {})
        doc_inf = report_data.get("2_document", {})
        info_data = [
            [Paragraph("<b>Project:</b>", td_style), Paragraph(proj.get("project_name", "N/A"), td_style),
             Paragraph("<b>Document:</b>", td_style), Paragraph(doc_inf.get("document_name", "N/A"), td_style)],
            [Paragraph("<b>Version:</b>", td_style), Paragraph(doc_inf.get("version", "N/A"), td_style),
             Paragraph("<b>Type:</b>", td_style), Paragraph(doc_inf.get("document_type", "N/A"), td_style)],
            [Paragraph("<b>Pages:</b>", td_style), Paragraph(str(doc_inf.get("total_pages", 0)), td_style),
             Paragraph("<b>Status:</b>", td_style), Paragraph(doc_inf.get("status", "N/A"), td_style)]
        ]
        t_info = Table(info_data, colWidths=[65, 195, 65, 215])
        t_info.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
        ]))
        elements.append(t_info)
        elements.append(Spacer(1, 8))

        # 3. Architecture Summary
        elements.append(Paragraph("3. Architecture Summary Metrics", h2_style))
        summ = report_data.get("3_architecture_summary", {})
        sum_data = [
            [Paragraph("Components", th_style), Paragraph("Interfaces", th_style), Paragraph("Dependencies", th_style), Paragraph("Findings", th_style)],
            [Paragraph(str(summ.get("components_count", 0)), td_style),
             Paragraph(str(summ.get("interfaces_count", 0)), td_style),
             Paragraph(str(summ.get("dependencies_count", 0)), td_style),
             Paragraph(str(summ.get("findings_count", 0)), td_style)]
        ]
        t_sum = Table(sum_data, colWidths=[135, 135, 135, 135])
        t_sum.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E293B')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('ALIGN', (0,0), (-1,-1), 'CENTER')
        ]))
        elements.append(t_sum)
        elements.append(Spacer(1, 8))

        # 4. Components
        elements.append(Paragraph("4. Software Components (SWCs)", h2_style))
        comp_rows = [[Paragraph("Component Name", th_style), Paragraph("Page", th_style), Paragraph("Confidence", th_style), Paragraph("Description", th_style)]]
        for c in report_data.get("4_components", []):
            comp_rows.append([
                Paragraph(c["name"], td_style),
                Paragraph(f"Page {c['page']}", td_style),
                Paragraph(f"{int(c['confidence']*100)}%", td_style),
                Paragraph((c.get("description") or "")[:70], td_style)
            ])
        if len(comp_rows) > 1:
            t_comp = Table(comp_rows, colWidths=[140, 50, 60, 290])
            t_comp.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1'))
            ]))
            elements.append(t_comp)
        elements.append(Spacer(1, 8))

        # 5. Interfaces
        elements.append(Paragraph("5. Communication Interfaces & Ports", h2_style))
        if_rows = [[Paragraph("Interface Name", th_style), Paragraph("Source Page", th_style), Paragraph("Confidence", th_style), Paragraph("Description", th_style)]]
        for i in report_data.get("5_interfaces", []):
            if_rows.append([
                Paragraph(i["name"], td_style),
                Paragraph(f"Page {i['page']}", td_style),
                Paragraph(f"{int(i['confidence']*100)}%", td_style),
                Paragraph((i.get("description") or "")[:70], td_style)
            ])
        if len(if_rows) > 1:
            t_if = Table(if_rows, colWidths=[140, 60, 60, 280])
            t_if.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E293B')),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1'))
            ]))
            elements.append(t_if)
        elements.append(Spacer(1, 8))

        # 6. Dependencies
        elements.append(Paragraph("6. Architectural Dependencies & Flow", h2_style))
        dep_rows = [[Paragraph("Source Entity", th_style), Paragraph("Relation / Protocol", th_style), Paragraph("Target Entity", th_style), Paragraph("Page", th_style)]]
        for d in report_data.get("6_dependencies", []):
            dep_rows.append([
                Paragraph(d["source"], td_style),
                Paragraph(f"{d.get('relationship', 'CONNECTS')} ({d.get('protocol', 'CAN')})", td_style),
                Paragraph(d["target"], td_style),
                Paragraph(f"Page {d['page']}", td_style)
            ])
        if len(dep_rows) > 1:
            t_dep = Table(dep_rows, colWidths=[150, 150, 160, 80])
            t_dep.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1'))
            ]))
            elements.append(t_dep)
        elements.append(Spacer(1, 8))

        # 7. Consistency Findings
        elements.append(Paragraph("7. Consistency Findings (Requires Human Review)", h2_style))
        find_rows = [[Paragraph("Title", th_style), Paragraph("Type", th_style), Paragraph("Severity", th_style), Paragraph("Page", th_style), Paragraph("Status", th_style)]]
        for f in report_data.get("7_consistency_findings", []):
            find_rows.append([
                Paragraph(f["title"][:38], td_style),
                Paragraph(f["type"], td_style),
                Paragraph(f["severity"], td_style),
                Paragraph(f"Page {f['source_page']}", td_style),
                Paragraph(f["status"], td_style)
            ])
        if len(find_rows) > 1:
            t_find = Table(find_rows, colWidths=[180, 110, 70, 60, 120])
            t_find.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#991B1B')),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1'))
            ]))
            elements.append(t_find)
        elements.append(Spacer(1, 8))

        # 8. Revision Changes
        elements.append(Paragraph("8. Revision Changes & Evolution", h2_style))
        rev_rows = [[Paragraph("Baseline Document", th_style), Paragraph("Added Components", th_style), Paragraph("Removed Components", th_style)]]
        for r in report_data.get("8_revision_changes", []):
            rev_rows.append([
                Paragraph(r.get("compared_with", "Baseline"), td_style),
                Paragraph(", ".join(r.get("added_components", [])) or "None", td_style),
                Paragraph(", ".join(r.get("removed_components", [])) or "None", td_style)
            ])
        if len(rev_rows) > 1:
            t_rev = Table(rev_rows, colWidths=[180, 180, 180])
            t_rev.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E293B')),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1'))
            ]))
            elements.append(t_rev)
        else:
            elements.append(Paragraph("Initial baseline release or single revision indexed.", body_style))
        elements.append(Spacer(1, 8))

        # 9. Evidence
        elements.append(Paragraph("9. Document Evidence Citations", h2_style))
        ev_rows = [[Paragraph("Finding / Claim", th_style), Paragraph("Page", th_style), Paragraph("Document Evidence", th_style)]]
        for ev in report_data.get("9_evidence", []):
            ev_rows.append([
                Paragraph(ev["finding_title"][:35], td_style),
                Paragraph(f"Page {ev['page']}", td_style),
                Paragraph(ev["evidence"][:85], td_style)
            ])
        if len(ev_rows) > 1:
            t_ev = Table(ev_rows, colWidths=[170, 50, 320])
            t_ev.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1'))
            ]))
            elements.append(t_ev)
        elements.append(Spacer(1, 8))

        # 10. Review Status
        elements.append(Paragraph("10. Engineering Review Status & Dispositions", h2_style))
        rst_rows = [[Paragraph("Finding ID", th_style), Paragraph("Current Disposition", th_style), Paragraph("Latest Engineering Rationale", th_style)]]
        for rs in report_data.get("10_review_status", []):
            rst_rows.append([
                Paragraph(f"Finding #{rs['finding_id']}: {rs['title'][:30]}", td_style),
                Paragraph(rs["current_status"], td_style),
                Paragraph(rs["latest_comment"][:60], td_style)
            ])
        if len(rst_rows) > 1:
            t_rst = Table(rst_rows, colWidths=[200, 100, 240])
            t_rst.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E293B')),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1'))
            ]))
            elements.append(t_rst)

        elements.append(Spacer(1, 14))
        elements.append(Paragraph(
            "<b>Engineering Sign-off Notice:</b> This report was compiled by the AUTOSAR HLD Document Analysis Assistant. "
            "In compliance with ISO 26262 functional safety processes, all architectural modifications require formal human engineering approval.",
            body_style
        ))

        doc.build(elements)
        logger.info(f"Generated complete 10-section PDF report at {output_path}")
        return output_path
