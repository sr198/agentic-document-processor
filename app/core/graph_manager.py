# app/core/graph_manager.py

from typing import Dict, List, Any, Optional
from neo4j import GraphDatabase, Driver
from neo4j.exceptions import Neo4jError
from loguru import logger
from datetime import datetime
import json
from .config import get_settings

class GraphManager:
    def __init__(self):
        self.settings = get_settings()
        self.driver = GraphDatabase.driver(
            self.settings.NEO4J_URI,
            auth=(self.settings.NEO4J_USER, self.settings.NEO4J_PASSWORD)
        )
        self._init_database()
    
    def _init_database(self):
        """Initialize database with necessary indexes and constraints"""
        with self.driver.session() as session:
            # Create constraints
            session.run("""
                CREATE CONSTRAINT IF NOT EXISTS FOR (c:Component) 
                REQUIRE c.id IS UNIQUE
            """)
            session.run("""
                CREATE CONSTRAINT IF NOT EXISTS FOR (d:Device) 
                REQUIRE d.name IS UNIQUE
            """)
            session.run("""
                CREATE CONSTRAINT IF NOT EXISTS FOR (p:Process) 
                REQUIRE p.id IS UNIQUE
            """)
            
            # Create vector index for embeddings
            session.run("""
                CALL db.index.vector.createNodeIndex(
                    'document_embeddings',
                    'DocumentChunk',
                    'embedding',
                    1536,
                    'cosine'
                )
            """)

    async def store_processed_document(self, processed_data: Dict[str, Any]):
        """Store processed document data in Neo4j"""
        try:
            with self.driver.session() as session:
                if processed_data['family'] == 'bom':
                    await self._store_bom_document(session, processed_data)
                elif processed_data['family'] == 'eco':
                    await self._store_eco_document(session, processed_data)
                elif processed_data['family'] == 'process_validation':
                    await self._store_process_document(session, processed_data)
                elif processed_data['family'] == 'regulatory':
                    await self._store_regulatory_document(session, processed_data)
                
                # Store document chunks with embeddings
                await self._store_document_chunks(session, processed_data)
                
        except Neo4jError as e:
            logger.error(f"Error storing document in Neo4j: {e}")
            raise

    async def hybrid_search(
        self,
        query_text: str,
        component_id: Optional[str] = None,
        limit: int = 5,
        min_similarity: float = 0.7
    ) -> Dict[str, Any]:
        """
        Perform hybrid search combining vector similarity and graph relationships
        """
        with self.driver.session() as session:
            # Generate embedding for the query
            response = await openai.Embedding.acreate(
                input=query_text,
                model="text-embedding-ada-002"
            )
            query_embedding = response.data[0].embedding

            # If component_id is provided, use it to contextualize the search
            if component_id:
                result = session.run("""
                    // First find related nodes through graph relationships
                    MATCH (c:Component {id: $component_id})
                    MATCH (c)-[r*1..2]-(related)
                    WITH collect(related) as related_nodes
                    
                    // Then find semantically similar chunks
                    CALL db.index.vector.queryNodes(
                        'document_embeddings',
                        $query_embedding,
                        $limit,
                        $min_similarity
                    ) YIELD node, score
                    
                    // Boost scores for chunks related to our component
                    WITH node, score,
                         CASE WHEN node IN related_nodes THEN score * 1.2 ELSE score END as adjusted_score
                    
                    RETURN node.text as text,
                           node.document_family as family,
                           node.filename as filename,
                           adjusted_score as similarity,
                           [(node)-[r]->(t) | type(r) + ' -> ' + labels(t)[0]] as relationships
                    ORDER BY adjusted_score DESC
                    LIMIT $limit
                """, {
                    'component_id': component_id,
                    'query_embedding': query_embedding,
                    'limit': limit,
                    'min_similarity': min_similarity
                })
            else:
                # Pure vector search without graph context
                result = session.run("""
                    CALL db.index.vector.queryNodes(
                        'document_embeddings',
                        $query_embedding,
                        $limit,
                        $min_similarity
                    ) YIELD node, score
                    
                    RETURN node.text as text,
                           node.document_family as family,
                           node.filename as filename,
                           score as similarity,
                           [(node)-[r]->(t) | type(r) + ' -> ' + labels(t)[0]] as relationships
                    ORDER BY score DESC
                """, {
                    'query_embedding': query_embedding,
                    'limit': limit,
                    'min_similarity': min_similarity
                })

            return [dict(record) for record in result]

    async def multi_hop_search(
        self,
        start_component_id: str,
        query_text: str,
        max_hops: int = 3
    ) -> Dict[str, Any]:
        """
        Perform a multi-hop search combining graph traversal with semantic search
        """
        with self.driver.session() as session:
            # Generate embedding for the query
            response = await openai.Embedding.acreate(
                input=query_text,
                model="text-embedding-ada-002"
            )
            query_embedding = response.data[0].embedding

            result = session.run("""
                // Start from our component
                MATCH (start:Component {id: $component_id})
                
                // Find paths up to max_hops
                MATCH path = (start)-[*1..$max_hops]-(target)
                WHERE NOT target:DocumentChunk
                
                // For each path, find relevant document chunks
                WITH path, nodes(path) as path_nodes
                MATCH (chunk:DocumentChunk)
                WHERE any(node IN path_nodes WHERE 
                    chunk.text CONTAINS node.id OR 
                    chunk.text CONTAINS node.name)
                
                // Calculate vector similarity
                CALL db.index.vector.queryNodes(
                    'document_embeddings',
                    $query_embedding,
                    1,  // Get closest match per path
                    0.0  // No minimum similarity
                ) YIELD node, score
                WHERE node = chunk
                
                RETURN path,
                       [node IN path_nodes | 
                           {type: labels(node)[0], 
                            properties: properties(node)}] as path_nodes,
                       node.text as supporting_text,
                       score as similarity
                ORDER BY score DESC
            """, {
                'component_id': start_component_id,
                'query_embedding': query_embedding,
                'max_hops': max_hops
            })

            # Process results
            paths = []
            for record in result:
                path_data = {
                    'nodes': record['path_nodes'],
                    'supporting_text': record['supporting_text'],
                    'similarity_score': record['similarity']
                }
                paths.append(path_data)

            return {
                'start_component': start_component_id,
                'paths': paths
            }
            
    async def _store_bom_document(self, session: Driver.session, data: Dict[str, Any]):
        """Store BOM document data"""
        # Create components and devices
        for entry in data['content']['structured_data']:
            # Create/merge component
            session.run("""
                MERGE (c:Component {id: $component_id})
                SET c.name = $component_name,
                    c.version = $version,
                    c.supplier = $supplier_name
            """, entry)
            
            # Create/merge device
            session.run("""
                MERGE (d:Device {name: $device_name})
            """, entry)
            
            # Create relationship
            session.run("""
                MATCH (c:Component {id: $component_id})
                MATCH (d:Device {name: $device_name})
                MERGE (c)-[r:USED_IN]->(d)
                SET r.version = $version
            """, entry)

    async def _store_eco_document(self, session: Driver.session, data: Dict[str, Any]):
        """Store ECO document data"""
        eco_data = data['content']
        
        # Create ECO node
        session.run("""
            CREATE (e:ECO {
                id: $eco_id,
                date: datetime($date),
                description: $description
            })
        """, {
            'eco_id': eco_data['entities'].get('eco_number', [None])[0],
            'date': str(datetime.now()),
            'description': eco_data['sections'].get('Change Details', '')
        })
        
        # Link to affected components
        for component_id in eco_data['entities'].get('component', []):
            session.run("""
                MATCH (e:ECO {id: $eco_id})
                MATCH (c:Component {id: $component_id})
                CREATE (e)-[r:AFFECTS]->(c)
            """, {'eco_id': eco_data['entities']['eco_number'][0], 'component_id': component_id})

    async def _store_process_document(self, session: Driver.session, data: Dict[str, Any]):
        """Store process validation document data"""
        process_data = data['content']
        
        # Create process node
        session.run("""
            MERGE (p:Process {id: $process_id})
            SET p.metrics = $metrics,
                p.lastValidation = datetime($validation_date)
        """, {
            'process_id': process_data['entities'].get('process', [None])[0],
            'metrics': json.dumps(process_data['metrics']),
            'validation_date': str(datetime.now())
        })
        
        # Link to components
        for component_id in process_data['entities'].get('component', []):
            session.run("""
                MATCH (p:Process {id: $process_id})
                MATCH (c:Component {id: $component_id})
                MERGE (p)-[r:VALIDATES]->(c)
            """, {'process_id': process_data['entities']['process'][0], 'component_id': component_id})

    async def _store_regulatory_document(self, session: Driver.session, data: Dict[str, Any]):
        """Store regulatory document data"""
        reg_data = data['content']
        
        # Create regulatory submission node
        session.run("""
            CREATE (r:RegulatorySubmission {
                id: $submission_id,
                type: $submission_type,
                date: datetime($date)
            })
        """, {
            'submission_id': reg_data['entities'].get('submission_id', [None])[0],
            'submission_type': reg_data['sections'].get('Device Description', '').split('\n')[0],
            'date': str(datetime.now())
        })
        
        # Link to components
        for component_id in reg_data['entities'].get('component', []):
            session.run("""
                MATCH (r:RegulatorySubmission {id: $submission_id})
                MATCH (c:Component {id: $component_id})
                CREATE (r)-[rel:REGULATES]->(c)
            """, {
                'submission_id': reg_data['entities']['submission_id'][0],
                'component_id': component_id
            })

    async def _store_document_chunks(self, session: Driver.session, data: Dict[str, Any]):
        """Store document chunks with embeddings"""
        for chunk, embedding in zip(data['content']['text_chunks'], data['embeddings']):
            session.run("""
                CREATE (c:DocumentChunk {
                    text: $text,
                    embedding: $embedding,
                    document_family: $family,
                    filename: $filename,
                    created_at: datetime($created_at)
                })
            """, {
                'text': chunk,
                'embedding': embedding,
                'family': data['family'],
                'filename': data['metadata']['filename'],
                'created_at': str(datetime.now())
            })

    async def find_similar_chunks(self, query_embedding: List[float], limit: int = 5) -> List[Dict]:
        """Find similar document chunks using vector similarity"""
        with self.driver.session() as session:
            result = session.run("""
                CALL db.index.vector.queryNodes(
                    'document_embeddings',
                    $query_embedding,
                    $limit
                ) YIELD node, score
                RETURN node.text as text, node.document_family as family,
                       node.filename as filename, score
                ORDER BY score DESC
            """, {'query_embedding': query_embedding, 'limit': limit})
            
            return [dict(record) for record in result]

    async def find_component_impacts(self, component_id: str) -> Dict[str, Any]:
        """Find all impacts for a given component"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Component {id: $component_id})
                OPTIONAL MATCH (c)-[:USED_IN]->(d:Device)
                OPTIONAL MATCH (p:Process)-[:VALIDATES]->(c)
                OPTIONAL MATCH (r:RegulatorySubmission)-[:REGULATES]->(c)
                OPTIONAL MATCH (e:ECO)-[:AFFECTS]->(c)
                RETURN {
                    component: properties(c),
                    devices: collect(DISTINCT properties(d)),
                    processes: collect(DISTINCT properties(p)),
                    regulatory: collect(DISTINCT properties(r)),
                    changes: collect(DISTINCT properties(e))
                } as impact
            """, {'component_id': component_id})
            
            return result.single()['impact']

    def close(self):
        """Close the database driver"""
        self.driver.close()
