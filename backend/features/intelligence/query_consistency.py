"""
Query Consistency Engine
Ensures consistent responses to similar/rephrased questions and prevents contradictory advice
"""

import json
import hashlib
from typing import List, Dict, Optional, Tuple, Set
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer
import numpy as np
from collections import defaultdict
import re

try:
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    print("Warning: sklearn not available. Installing...")
    import subprocess
    subprocess.check_call(["pip", "install", "scikit-learn"])
    from sklearn.metrics.pairwise import cosine_similarity

class QueryConsistencyEngine:
    """
    Ensures consistent responses to similar/rephrased questions and maintains conversation coherence
    """
    
    def __init__(self):
        # Initialize embedding model for semantic similarity
        try:
            print("Loading BAAI/bge-large-en-v1.5 for query consistency...")
            self.model = SentenceTransformer("BAAI/bge-large-en-v1.5")
            print("Successfully loaded BAAI/bge-large-en-v1.5")
        except Exception as e:
            print(f"Warning: Failed to load BAAI/bge-large-en-v1.5: {e}")
            print("Falling back to BAAI/bge-small-en")
            try:
                self.model = SentenceTransformer("BAAI/bge-small-en")
            except Exception as e2:
                print(f"Warning: Failed to load BAAI/bge-small-en: {e2}")
                print("Falling back to all-MiniLM-L6-v2")
                self.model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Similarity thresholds for different consistency levels
        self.similarity_thresholds = {
            "identical": 0.95,      # Nearly identical questions
            "very_similar": 0.85,   # Very similar questions requiring consistent answers
            "similar": 0.70,        # Similar questions that should reference each other
            "related": 0.50         # Related questions that might need context
        }
        
        # Academic domain patterns for enhanced similarity detection
        self.academic_patterns = {
            "course_codes": r'\b([A-Z]{2,5})\s*(\d{3,4})\b',
            "degree_terms": r'\b(bachelor|master|doctorate|phd|bs|ba|ms|ma|degree|major|minor)\b',
            "academic_actions": r'\b(take|enroll|register|complete|finish|graduate|transfer)\b',
            "requirement_terms": r'\b(prerequisite|corequisite|requirement|credit|hour|gpa)\b',
            "time_terms": r'\b(semester|quarter|year|fall|spring|summer|winter|before|after|during)\b'
        }
        
        # Query canonicalization rules for academic questions
        self.canonicalization_rules = {
            "prerequisite_variations": [
                "what are the prerequisites for",
                "what do i need before taking", 
                "what courses do i need before",
                "requirements before taking",
                "what should i take before"
            ],
            "course_info_variations": [
                "tell me about",
                "information about",
                "what is",
                "describe",
                "explain"
            ],
            "planning_variations": [
                "should i take",
                "when should i take",
                "is it good to take",
                "recommend taking"
            ]
        }
    
    def check_query_similarity(self, current_query: str, conversation_history: List[Dict], 
                             session_id: str = None) -> Dict:
        """
        Check if current query is similar to previous ones and determine consistency requirements
        """
        previous_queries = self._extract_previous_queries(conversation_history)
        if not previous_queries:
            return {"is_similar": False, "similarity_level": "none"}
        
        # Normalize and canonicalize current query
        normalized_current = self._normalize_query(current_query)
        canonical_current = self._canonicalize_query(normalized_current)
        
        # Calculate similarities with previous queries
        similarity_results = []
        
        for prev_query in previous_queries:
            # Normalize and canonicalize previous query
            normalized_prev = self._normalize_query(prev_query["query"])
            canonical_prev = self._canonicalize_query(normalized_prev)
            
            # Calculate multiple similarity scores
            similarities = self._calculate_comprehensive_similarity(
                canonical_current, canonical_prev, current_query, prev_query["query"]
            )
            
            similarity_results.append({
                **prev_query,
                **similarities,
                "normalized_query": normalized_prev,
                "canonical_query": canonical_prev
            })
        
        # Find the most similar query
        if similarity_results:
            # Sort by combined similarity score
            similarity_results.sort(key=lambda x: x["combined_score"], reverse=True)
            best_match = similarity_results[0]
            
            # Determine similarity level
            similarity_level = self._determine_similarity_level(best_match["combined_score"])
            
            if similarity_level != "none":
                return {
                    "is_similar": True,
                    "similarity_level": similarity_level,
                    "similarity_score": best_match["combined_score"],
                    "semantic_score": best_match["semantic_score"],
                    "pattern_score": best_match["pattern_score"],
                    "entity_score": best_match["entity_score"],
                    "similar_query": best_match["query"],
                    "previous_response": best_match["response"],
                    "turn_number": best_match["turn"],
                    "consistency_requirement": self._determine_consistency_requirement(similarity_level),
                    "all_similarities": similarity_results[:3]  # Top 3 similar queries
                }
        
        return {"is_similar": False, "similarity_level": "none"}
    
    def _extract_previous_queries(self, history: List[Dict]) -> List[Dict]:
        """Extract user queries and corresponding responses from conversation history"""
        queries = []
        
        for i in range(0, len(history) - 1, 2):  # Process user-assistant pairs
            if i + 1 < len(history):
                user_msg = history[i]
                assistant_msg = history[i + 1]
                
                if (user_msg.get("sender") == "user" and 
                    assistant_msg.get("sender") == "assistant"):
                    queries.append({
                        "query": user_msg["text"],
                        "response": assistant_msg["text"],
                        "turn": i // 2 + 1,
                        "timestamp": user_msg.get("timestamp", datetime.now().isoformat())
                    })
        
        return queries
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for better comparison"""
        # Convert to lowercase
        normalized = query.lower().strip()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove common punctuation that doesn't affect meaning
        normalized = re.sub(r'[?!.,;:]', '', normalized)
        
        # Normalize common academic abbreviations
        replacements = {
            "pre-req": "prerequisite",
            "prereq": "prerequisite", 
            "pre req": "prerequisite",
            "co-req": "corequisite",
            "coreq": "corequisite",
            "gened": "general education",
            "gen ed": "general education",
            "comp sci": "computer science",
            "cs": "computer science"
        }
        
        for abbrev, full_form in replacements.items():
            normalized = re.sub(r'\b' + re.escape(abbrev) + r'\b', full_form, normalized)
        
        return normalized
    
    def _canonicalize_query(self, query: str) -> str:
        """Convert query to canonical form for better similarity detection"""
        canonical = query
        
        # Apply canonicalization rules
        for category, variations in self.canonicalization_rules.items():
            for variation in variations:
                if variation in canonical:
                    # Replace with the first (canonical) variation
                    canonical_form = variations[0]
                    canonical = canonical.replace(variation, canonical_form)
                    break
        
        return canonical
    
    def _calculate_comprehensive_similarity(self, query1: str, query2: str, 
                                         original1: str, original2: str) -> Dict:
        """Calculate multiple types of similarity for comprehensive comparison"""
        
        # 1. Semantic similarity using embeddings
        try:
            embeddings = self.model.encode([query1, query2])
            semantic_score = float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0])
        except Exception as e:
            print(f"Warning: Semantic similarity calculation failed: {e}")
            semantic_score = 0.0
        
        # 2. Pattern-based similarity (academic patterns)
        pattern_score = self._calculate_pattern_similarity(original1, original2)
        
        # 3. Entity overlap similarity
        entity_score = self._calculate_entity_similarity(original1, original2)
        
        # 4. Structural similarity (question structure)
        structural_score = self._calculate_structural_similarity(query1, query2)
        
        # 5. Combined weighted score
        weights = {
            "semantic": 0.4,
            "pattern": 0.25,
            "entity": 0.2,
            "structural": 0.15
        }
        
        combined_score = (
            semantic_score * weights["semantic"] +
            pattern_score * weights["pattern"] +
            entity_score * weights["entity"] +
            structural_score * weights["structural"]
        )
        
        return {
            "semantic_score": semantic_score,
            "pattern_score": pattern_score,
            "entity_score": entity_score,
            "structural_score": structural_score,
            "combined_score": combined_score
        }
    
    def _calculate_pattern_similarity(self, query1: str, query2: str) -> float:
        """Calculate similarity based on academic patterns"""
        score = 0.0
        total_patterns = len(self.academic_patterns)
        
        for pattern_name, pattern in self.academic_patterns.items():
            matches1 = set(re.findall(pattern, query1, re.IGNORECASE))
            matches2 = set(re.findall(pattern, query2, re.IGNORECASE))
            
            if matches1 or matches2:
                # Calculate Jaccard similarity for this pattern
                intersection = len(matches1.intersection(matches2))
                union = len(matches1.union(matches2))
                pattern_sim = intersection / union if union > 0 else 0
                score += pattern_sim
        
        return score / total_patterns if total_patterns > 0 else 0.0
    
    def _calculate_entity_similarity(self, query1: str, query2: str) -> float:
        """Calculate similarity based on academic entities (courses, majors, etc.)"""
        
        # Extract entities from both queries
        entities1 = self._extract_query_entities(query1)
        entities2 = self._extract_query_entities(query2)
        
        # Calculate similarity for each entity type
        entity_similarities = []
        
        for entity_type in set(entities1.keys()).union(set(entities2.keys())):
            set1 = set(entities1.get(entity_type, []))
            set2 = set(entities2.get(entity_type, []))
            
            if set1 or set2:
                intersection = len(set1.intersection(set2))
                union = len(set1.union(set2))
                similarity = intersection / union if union > 0 else 0
                entity_similarities.append(similarity)
        
        return np.mean(entity_similarities) if entity_similarities else 0.0
    
    def _extract_query_entities(self, query: str) -> Dict[str, List[str]]:
        """Extract academic entities from a query"""
        entities = defaultdict(list)
        
        # Extract course codes
        course_matches = re.findall(self.academic_patterns["course_codes"], query, re.IGNORECASE)
        for dept, num in course_matches:
            entities["courses"].append(f"{dept.upper()} {num}")
        
        # Extract degree terms
        degree_matches = re.findall(self.academic_patterns["degree_terms"], query, re.IGNORECASE)
        entities["degrees"].extend([degree.lower() for degree in degree_matches])
        
        # Extract requirement terms
        req_matches = re.findall(self.academic_patterns["requirement_terms"], query, re.IGNORECASE)
        entities["requirements"].extend([req.lower() for req in req_matches])
        
        # Extract time terms
        time_matches = re.findall(self.academic_patterns["time_terms"], query, re.IGNORECASE)
        entities["time_references"].extend([time.lower() for time in time_matches])
        
        return dict(entities)
    
    def _calculate_structural_similarity(self, query1: str, query2: str) -> float:
        """Calculate similarity based on question structure and intent"""
        
        # Question type indicators
        question_types = {
            "what": ["what", "which"],
            "how": ["how"],
            "when": ["when"],
            "where": ["where"], 
            "why": ["why"],
            "can": ["can", "could", "am i able", "is it possible"],
            "should": ["should", "ought", "recommend", "suggest"],
            "is": ["is", "are", "does", "do"]
        }
        
        # Determine question types for both queries
        type1 = self._determine_question_type(query1, question_types)
        type2 = self._determine_question_type(query2, question_types)
        
        # Structure similarity based on question type match
        if type1 == type2 and type1 != "unknown":
            return 1.0
        elif type1 != "unknown" and type2 != "unknown":
            return 0.3  # Different but recognizable question types
        else:
            return 0.0
    
    def _determine_question_type(self, query: str, question_types: Dict) -> str:
        """Determine the type of question being asked"""
        query_lower = query.lower()
        
        for q_type, indicators in question_types.items():
            if any(indicator in query_lower for indicator in indicators):
                return q_type
        
        return "unknown"
    
    def _determine_similarity_level(self, score: float) -> str:
        """Determine similarity level based on combined score"""
        if score >= self.similarity_thresholds["identical"]:
            return "identical"
        elif score >= self.similarity_thresholds["very_similar"]:
            return "very_similar"
        elif score >= self.similarity_thresholds["similar"]:
            return "similar"
        elif score >= self.similarity_thresholds["related"]:
            return "related"
        else:
            return "none"
    
    def _determine_consistency_requirement(self, similarity_level: str) -> str:
        """Determine what type of consistency is required"""
        consistency_map = {
            "identical": "return_previous",      # Return cached response
            "very_similar": "maintain_consistency", # Ensure consistent advice
            "similar": "reference_previous",     # Reference previous discussion
            "related": "acknowledge_context",    # Acknowledge related context
            "none": "no_requirement"
        }
        
        return consistency_map.get(similarity_level, "no_requirement")
    
    def validate_response_consistency(self, new_response: str, similar_query_data: Dict, 
                                    current_query: str) -> Dict:
        """Validate that new response is consistent with previous similar responses"""
        
        if not similar_query_data.get("is_similar"):
            return {
                "is_consistent": True,
                "confidence": 1.0,
                "validation_type": "no_comparison_needed"
            }
        
        previous_response = similar_query_data["previous_response"]
        similarity_level = similar_query_data["similarity_level"]
        
        # For identical/very similar queries, check response consistency
        if similarity_level in ["identical", "very_similar"]:
            consistency_check = self._check_response_consistency(new_response, previous_response)
            
            return {
                "is_consistent": consistency_check["is_consistent"],
                "confidence": consistency_check["confidence"],
                "validation_type": "strict_consistency",
                "previous_response": previous_response,
                "consistency_score": consistency_check["similarity_score"],
                "recommendation": self._generate_consistency_recommendation(
                    consistency_check, similarity_level
                )
            }
        
        # For similar/related queries, check for contradictions
        else:
            contradiction_check = self._check_for_contradictions(new_response, previous_response)
            
            return {
                "is_consistent": not contradiction_check["has_contradiction"],
                "confidence": contradiction_check["confidence"],
                "validation_type": "contradiction_check",
                "contradiction_details": contradiction_check.get("details", []),
                "recommendation": "acknowledge_previous" if not contradiction_check["has_contradiction"] else "explain_difference"
            }
    
    def _check_response_consistency(self, response1: str, response2: str) -> Dict:
        """Check consistency between two responses"""
        try:
            # Calculate semantic similarity between responses
            embeddings = self.model.encode([response1, response2])
            similarity_score = float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0])
            
            # High similarity indicates consistency
            consistency_threshold = 0.7
            is_consistent = similarity_score > consistency_threshold
            
            return {
                "is_consistent": is_consistent,
                "similarity_score": similarity_score,
                "confidence": similarity_score
            }
            
        except Exception as e:
            print(f"Warning: Response consistency check failed: {e}")
            return {
                "is_consistent": True,  # Default to consistent if check fails
                "similarity_score": 0.5,
                "confidence": 0.5
            }
    
    def _check_for_contradictions(self, response1: str, response2: str) -> Dict:
        """Check for contradictions between responses"""
        
        # Simple contradiction detection patterns
        contradiction_patterns = [
            (r'\byes\b.*\bno\b', r'\bno\b.*\byes\b'),
            (r'\brequired\b', r'\bnot required\b'),
            (r'\bmust\b', r'\boptional\b'),
            (r'\ballowed\b', r'\bnot allowed\b'),
            (r'\bcan\b', r'\bcannot\b'),
            (r'\b\d+\s*credits?\b', r'\b\d+\s*credits?\b')  # Different credit counts
        ]
        
        contradictions = []
        response1_lower = response1.lower()
        response2_lower = response2.lower()
        
        for pattern1, pattern2 in contradiction_patterns:
            if (re.search(pattern1, response1_lower) and re.search(pattern2, response2_lower)) or \
               (re.search(pattern2, response1_lower) and re.search(pattern1, response2_lower)):
                contradictions.append({
                    "type": "pattern_contradiction",
                    "pattern": f"{pattern1} vs {pattern2}"
                })
        
        return {
            "has_contradiction": len(contradictions) > 0,
            "confidence": 0.8 if contradictions else 0.9,
            "details": contradictions
        }
    
    def _generate_consistency_recommendation(self, consistency_check: Dict, similarity_level: str) -> str:
        """Generate recommendation for handling consistency"""
        
        if consistency_check["is_consistent"]:
            return "proceed_with_new_response"
        else:
            if similarity_level == "identical":
                return "use_previous_response"
            else:
                return "acknowledge_and_clarify"
    
    def generate_consistency_aware_response(self, query_similarity: Dict, new_response: Dict,
                                          current_query: str) -> Dict:
        """Generate response that maintains consistency with previous interactions"""
        
        if not query_similarity.get("is_similar"):
            return new_response
        
        similarity_level = query_similarity["similarity_level"]
        consistency_requirement = query_similarity["consistency_requirement"]
        
        # Handle different consistency requirements
        if consistency_requirement == "return_previous":
            # For identical questions, return enhanced previous response
            return self._create_cached_response(query_similarity, current_query)
        
        elif consistency_requirement == "maintain_consistency":
            # Ensure new response is consistent with previous advice
            return self._create_consistent_response(query_similarity, new_response, current_query)
        
        elif consistency_requirement == "reference_previous":
            # Reference previous discussion while providing new information
            return self._create_referential_response(query_similarity, new_response, current_query)
        
        elif consistency_requirement == "acknowledge_context":
            # Acknowledge related previous context
            return self._create_contextual_response(query_similarity, new_response, current_query)
        
        else:
            return new_response
    
    def _create_cached_response(self, query_similarity: Dict, current_query: str) -> Dict:
        """Create response that references cached/previous answer"""
        
        similar_query = query_similarity["similar_query"]
        previous_response = query_similarity["previous_response"]
        
        enhanced_response = {
            "answer": f"As I mentioned when you asked about '{similar_query}': {previous_response}\n\nIs there a specific aspect you'd like me to elaborate on?",
            "confidence": 4,
            "suggested_questions": [
                "Could you clarify what specific information you need?",
                "Is there a particular detail you'd like me to expand on?",
                "Would you like me to explain any part in more detail?"
            ],
            "context_references": [similar_query],
            "consistency_applied": {
                "type": "cached_response",
                "similarity_score": query_similarity["similarity_score"],
                "original_query": similar_query
            }
        }
        
        return enhanced_response
    
    def _create_consistent_response(self, query_similarity: Dict, new_response: Dict, 
                                  current_query: str) -> Dict:
        """Create response that maintains consistency with previous advice"""
        
        similar_query = query_similarity["similar_query"]
        consistency_note = f"\n\n*This aligns with what I mentioned earlier about '{similar_query}'. My advice remains consistent.*"
        
        enhanced_response = new_response.copy()
        enhanced_response["answer"] = new_response["answer"] + consistency_note
        enhanced_response["context_references"] = enhanced_response.get("context_references", []) + [similar_query]
        enhanced_response["consistency_applied"] = {
            "type": "maintained_consistency",
            "similarity_score": query_similarity["similarity_score"],
            "referenced_query": similar_query
        }
        
        return enhanced_response
    
    def _create_referential_response(self, query_similarity: Dict, new_response: Dict, 
                                   current_query: str) -> Dict:
        """Create response that references previous discussion"""
        
        similar_query = query_similarity["similar_query"]
        reference_note = f"\n\nThis relates to your earlier question about '{similar_query}'. "
        
        enhanced_response = new_response.copy()
        enhanced_response["answer"] = reference_note + new_response["answer"]
        enhanced_response["context_references"] = enhanced_response.get("context_references", []) + [similar_query]
        enhanced_response["consistency_applied"] = {
            "type": "referenced_previous",
            "similarity_score": query_similarity["similarity_score"],
            "referenced_query": similar_query
        }
        
        return enhanced_response
    
    def _create_contextual_response(self, query_similarity: Dict, new_response: Dict, 
                                  current_query: str) -> Dict:
        """Create response that acknowledges related context"""
        
        similar_query = query_similarity["similar_query"]
        # DISABLED: Robotic meta-commentary removed
        # context_note = f"\n\n*Note: This question is related to our earlier discussion about '{similar_query}'.*"
        
        enhanced_response = new_response.copy()
        # DISABLED: No meta-commentary added
        # enhanced_response["answer"] = new_response["answer"] + context_note
        enhanced_response["context_references"] = enhanced_response.get("context_references", []) + [similar_query]
        enhanced_response["consistency_applied"] = {
            "type": "acknowledged_context",
            "similarity_score": query_similarity["similarity_score"],
            "related_query": similar_query
        }
        
        return enhanced_response
    
    def get_consistency_analytics(self, query_similarity: Dict) -> Dict:
        """Generate analytics about query consistency for monitoring and improvement"""
        
        if not query_similarity.get("is_similar"):
            return {"consistency_detected": False}
        
        return {
            "consistency_detected": True,
            "similarity_level": query_similarity["similarity_level"],
            "similarity_score": query_similarity["similarity_score"],
            "consistency_requirement": query_similarity["consistency_requirement"],
            "semantic_score": query_similarity.get("semantic_score", 0),
            "pattern_score": query_similarity.get("pattern_score", 0),
            "entity_score": query_similarity.get("entity_score", 0),
            "recommendation": "Monitor for consistent application of advice",
            "quality_indicator": "high" if query_similarity["similarity_score"] > 0.8 else "medium"
        }