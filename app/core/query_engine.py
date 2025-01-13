# app/core/query_engine.py

from typing import Dict, List, Any, Optional
from enum import Enum
import openai
from loguru import logger
from .graph_manager import GraphManager
from .config import get_settings

class QueryType(Enum):
    COMPONENT_USAGE = "component_usage"
    PROCESS_IMPACT = "process_impact"
    REGULATORY_IMPACT = "regulatory_impact"
    FULL_IMPACT = "full_impact"
    TIMELINE = "timeline"
    CUSTOM = "custom"

class ImpactQueryEngine:
    def __init__(self, graph_manager: GraphManager):
        self.graph_manager = graph_manager
        self.settings = get_settings()
        openai.api_key = self.settings.OPENAI_API_KEY

    async def execute_query(self, query: str, query_type: Optional[QueryType] = None) -> Dict[str, Any]:
        """Execute an impact analysis query"""
        if query_type is None:
            query_type = await self._classify_query(query)

        # Extract relevant entities from the query
        entities = await self._extract_entities(query)
        
        if query_type == QueryType.COMPONENT_USAGE:
            return await self._handle_component_usage(entities)
        elif query_type == QueryType.PROCESS_IMPACT:
            return await self._handle_process_impact(entities)
        elif query_type == QueryType.REGULATORY_IMPACT:
            return await self._handle_regulatory_impact(entities)
        elif query_type == QueryType.FULL_IMPACT:
            return await self._handle_full_impact(entities)
        elif query_type == QueryType.TIMELINE:
            return await self._handle_timeline_analysis(entities)
        else:
            return await self._handle_custom_query(query, entities)

    # app/core/query_engine.py

class ImpactQueryEngine:
    # ... (existing initialization code) ...

    async def _find_relevant_context(
        self,
        query: str,
        component_id: Optional[str] = None,
        use_multi_hop: bool = False
    ) -> List[Dict[str, Any]]:
        """Find relevant context using hybrid search"""
        if use_multi_hop and component_id:
            # Use multi-hop search for deeper relationship exploration
            results = await self.graph_manager.multi_hop_search(
                start_component_id=component_id,
                query_text=query,
                max_hops=3
            )
            # Extract relevant context from paths
            context = []
            for path in results['paths']:
                context.append({
                    'text': path['supporting_text'],
                    'similarity': path['similarity_score'],
                    'path': [node['properties'].get('name', node['properties'].get('id')) 
                            for node in path['nodes']]
                })
            return context
        else:
            # Use hybrid search for direct context
            return await self.graph_manager.hybrid_search(
                query_text=query,
                component_id=component_id,
                limit=5
            )

    async def _handle_component_usage(self, entities: Dict[str, List[str]]) -> Dict[str, Any]:
        """Enhanced component usage query handling"""
        results = {}
        
        for component_id in entities.get('component_ids', []):
            # Get direct impacts through graph relationships
            impact_data = await self.graph_manager.find_component_impacts(component_id)
            
            # Get relevant context through hybrid search
            relevant_context = await self._find_relevant_context(
                query=f"usage and dependencies of component {component_id}",
                component_id=component_id,
                use_multi_hop=True
            )
            
            results[component_id] = {
                'direct_impacts': impact_data,
                'relevant_context': relevant_context,
                'relationship_paths': [
                    context['path'] for context in relevant_context 
                    if 'path' in context
                ]
            }
        
        return {
            'query_type': 'component_usage',
            'results': results
        }

    async def _handle_full_impact(self, entities: Dict[str, List[str]]) -> Dict[str, Any]:
        """Enhanced full impact analysis"""
        # Get component impacts with multi-hop exploration
        component_results = await self._handle_component_usage(entities)
        
        # Get process impacts
        process_results = await self._handle_process_impact(entities)
        
        # Get regulatory impacts
        regulatory_results = await self._handle_regulatory_impact(entities)
        
        # Get broader context through hybrid search
        broader_context = []
        for component_id in entities.get('component_ids', []):
            context = await self._find_relevant_context(
                query="impact analysis considerations and requirements",
                component_id=component_id
            )
            broader_context.extend(context)
        
        return {
            'query_type': 'full_impact',
            'component_impacts': component_results['results'],
            'process_impacts': process_results['results'],
            'regulatory_impacts': regulatory_results['results'],
            'relationship_paths': [
                path for result in component_results['results'].values()
                for path in result.get('relationship_paths', [])
            ],
            'relevant_context': broader_context
        }
        
    async def _classify_query(self, query: str) -> QueryType:
        """Classify the type of query using OpenAI"""
        prompt = f"""Classify the following impact analysis query into one of these categories:
        - component_usage: Queries about where components are used
        - process_impact: Queries about manufacturing process impacts
        - regulatory_impact: Queries about regulatory implications
        - full_impact: Queries requiring comprehensive impact analysis
        - timeline: Queries about implementation timelines
        - custom: Other types of queries

        Query: {query}

        Return only the category name.
        """

        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        
        category = response.choices[0].message.content.strip().lower()
        return QueryType(category)

    async def _extract_entities(self, query: str) -> Dict[str, List[str]]:
        """Extract relevant entities from the query"""
        prompt = f"""Extract relevant entities from the following impact analysis query.
        Focus on:
        - component_ids (format: CMP-XXXX)
        - process_ids (format: Assembly Line #X)
        - regulatory_ids (format: YYYY-KXXXX)
        - device_names

        Query: {query}

        Return a JSON object with lists of found entities.
        """

        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        
        return response.choices[0].message.content

    async def _handle_component_usage(self, entities: Dict[str, List[str]]) -> Dict[str, Any]:
        """Handle component usage queries"""
        results = {}
        
        for component_id in entities.get('component_ids', []):
            # Get direct impacts
            impact_data = await self.graph_manager.find_component_impacts(component_id)
            
            # Get similar documents for context
            relevant_chunks = await self._find_relevant_chunks(component_id)
            
            results[component_id] = {
                'direct_impacts': impact_data,
                'relevant_context': relevant_chunks
            }
            
        return {
            'query_type': 'component_usage',
            'results': results
        }

    async def _handle_process_impact(self, entities: Dict[str, List[str]]) -> Dict[str, Any]:
        """Handle process impact queries"""
        with self.graph_manager.driver.session() as session:
            # Get process impacts
            result = session.run("""
                MATCH (p:Process)
                WHERE p.id IN $process_ids
                OPTIONAL MATCH (p)-[:VALIDATES]->(c:Component)
                OPTIONAL MATCH (c)-[:USED_IN]->(d:Device)
                RETURN {
                    process: properties(p),
                    components: collect(DISTINCT properties(c)),
                    affected_devices: collect(DISTINCT properties(d))
                } as impact
            """, {'process_ids': entities.get('process_ids', [])})
            
            return {
                'query_type': 'process_impact',
                'results': [record['impact'] for record in result]
            }

    async def _handle_regulatory_impact(self, entities: Dict[str, List[str]]) -> Dict[str, Any]:
        """Handle regulatory impact queries"""
        with self.graph_manager.driver.session() as session:
            # Get regulatory impacts
            result = session.run("""
                MATCH (r:RegulatorySubmission)
                WHERE r.id IN $regulatory_ids
                OPTIONAL MATCH (r)-[:REGULATES]->(c:Component)
                OPTIONAL MATCH (c)-[:USED_IN]->(d:Device)
                RETURN {
                    submission: properties(r),
                    regulated_components: collect(DISTINCT properties(c)),
                    affected_devices: collect(DISTINCT properties(d))
                } as impact
            """, {'regulatory_ids': entities.get('regulatory_ids', [])})
            
            return {
                'query_type': 'regulatory_impact',
                'results': [record['impact'] for record in result]
            }

    async def _handle_full_impact(self, entities: Dict[str, List[str]]) -> Dict[str, Any]:
        """Handle comprehensive impact analysis queries"""
        # Get component impacts
        component_results = await self._handle_component_usage(entities)
        
        # Get process impacts
        process_results = await self._handle_process_impact(entities)
        
        # Get regulatory impacts
        regulatory_results = await self._handle_regulatory_impact(entities)
        
        # Get relevant document chunks for context
        context_chunks = []
        for component_id in entities.get('component_ids', []):
            chunks = await self._find_relevant_chunks(component_id)
            context_chunks.extend(chunks)
        
        return {
            'query_type': 'full_impact',
            'component_impacts': component_results['results'],
            'process_impacts': process_results['results'],
            'regulatory_impacts': regulatory_results['results'],
            'relevant_context': context_chunks
        }

    async def _handle_timeline_analysis(self, entities: Dict[str, List[str]]) -> Dict[str, Any]:
        """Handle timeline analysis queries"""
        with self.graph_manager.driver.session() as session:
            # Get timeline-related data
            result = session.run("""
                MATCH (c:Component)
                WHERE c.id IN $component_ids
                OPTIONAL MATCH (e:ECO)-[:AFFECTS]->(c)
                OPTIONAL MATCH (p:Process)-[:VALIDATES]->(c)
                RETURN {
                    component: properties(c),
                    changes: collect(DISTINCT properties(e)),
                    validations: collect(DISTINCT properties(p))
                } as timeline
            """, {'component_ids': entities.get('component_ids', [])})
            
            return {
                'query_type': 'timeline',
                'results': [record['timeline'] for record in result]
            }

    async def _handle_custom_query(self, query: str, entities: Dict[str, List[str]]) -> Dict[str, Any]:
        """Handle custom/complex queries"""
        # First get comprehensive data
        full_impact = await self._handle_full_impact(entities)
        
        # Use OpenAI to analyze and structure the response
        prompt = f"""Analyze the following impact analysis data and answer the specific query.
        
        Query: {query}
        
        Impact Data: {full_impact}
        
        Provide a structured analysis focusing on the specific aspects asked in the query.
        """

        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        
        return {
            'query_type': 'custom',
            'original_query': query,
            'analysis': response.choices[0].message.content,
            'supporting_data': full_impact
        }

    async def _find_relevant_chunks(self, search_term: str) -> List[Dict[str, Any]]:
        """Find relevant document chunks for context"""
        # Generate embedding for search term
        response = await openai.Embedding.acreate(
            input=search_term,
            model="text-embedding-ada-002"
        )
        query_embedding = response.data[0].embedding
        
        # Find similar chunks
        return await self.graph_manager.find_similar_chunks(query_embedding, limit=5)