from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

class EntityBase(BaseModel):
    name: str
    entity_type: str
    description: Optional[str] = None
    page: int = 1
    confidence: float = 0.9

class ArchitectureEntityResponse(EntityBase):
    id: int
    document_id: str

    model_config = ConfigDict(from_attributes=True)

class RelationshipBase(BaseModel):
    source_entity: str
    relationship_type: str
    target_entity: str
    protocol: Optional[str] = "CAN"
    page: int = 1
    confidence: float = 0.9

class RelationshipResponse(RelationshipBase):
    id: int
    document_id: str

    model_config = ConfigDict(from_attributes=True)


class ComponentDetail(BaseModel):
    name: str
    description: Optional[str] = None
    interfaces: List[str] = []
    inputs: List[str] = []
    outputs: List[str] = []
    dependencies: List[str] = []
    source_pages: List[int] = []

class InterfaceDetail(BaseModel):
    name: str
    provider: str
    consumer: str
    type: str  # CAN, Ethernet, Autosar RTE, Inter-core
    signals: List[str] = []
    source_page: int
    status: str = "Valid"

class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    metadata: Dict[str, Any] = {}

class GraphEdge(BaseModel):
    source: str
    target: str
    label: str
    protocol: Optional[str] = None

class ArchitectureGraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
