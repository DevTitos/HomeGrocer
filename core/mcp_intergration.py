# core/mcp_integration.py (fixed version)
import logging
from typing import Dict, List, Any, Optional
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MCPIntegration:
    """Model Context Protocol Integration for HomeGrocer - Fixed Version"""
    
    def __init__(self):
        self.is_available = True  # Always available for now
        self.available_tools = self._discover_tools()
        
    def _discover_tools(self):
        """Discover available MCP tools"""
        return {
            'predict_consumption': {
                'description': 'Predict product consumption patterns',
                'parameters': ['product_id', 'historical_data', 'user_context']
            },
            'generate_recommendations': {
                'description': 'Generate personalized shopping recommendations',
                'parameters': ['user_id', 'inventory', 'budget', 'preferences']
            },
            'optimize_cart': {
                'description': 'Optimize shopping cart for price and delivery',
                'parameters': ['cart_items', 'vendors', 'constraints']
            }
        }
    
    def generate_recommendations(self, user_id: str, inventory: List[Dict], 
                                 budget: Optional[float] = None, 
                                 preferences: Optional[Dict] = None) -> List[Dict]:
        """Generate personalized recommendations using MCP - FIXED VERSION"""
        try:
            if self.is_available and 'generate_recommendations' in self.available_tools:
                # Simulated MCP call with proper error handling
                recommendations = self._simulate_mcp_recommendations(user_id, inventory, budget, preferences)
            else:
                # Fallback recommendations
                recommendations = self._fallback_recommendations(inventory, budget)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error in generate_recommendations: {e}")
            # Return safe default recommendations
            return self._fallback_recommendations(inventory, budget)
    
    def _simulate_mcp_recommendations(self, user_id: str, inventory: List[Dict], 
                                      budget: Optional[float], preferences: Optional[Dict]) -> List[Dict]:
        """Simulate MCP recommendations with proper error handling"""
        recommendations = []
        
        # Safely process inventory items
        for item in inventory:
            try:
                # Get values with defaults to prevent KeyError
                quantity = float(item.get('quantity', 0))
                min_threshold = float(item.get('min_threshold', 1))
                product_id = str(item.get('product_id', ''))
                product_name = str(item.get('product_name', 'Unknown Product'))
                
                # Calculate urgency score safely
                if min_threshold > 0:
                    urgency_score = max(0, 1 - (quantity / min_threshold))
                else:
                    urgency_score = 0.5  # Default if no threshold
                
                # Only recommend if quantity is low
                if quantity <= min_threshold:
                    recommendation = {
                        'product_id': product_id,
                        'product_name': product_name,
                        'current_quantity': quantity,
                        'min_threshold': min_threshold,
                        'urgency_score': round(urgency_score, 2),
                        'recommended_quantity': max(1, int(min_threshold * 2)),
                        'reason': f'Stock level at {quantity} units, below threshold of {min_threshold}',
                        'estimated_cost': 4.99,  # Simulated price
                        'priority': 'high' if urgency_score > 0.7 else 'medium' if urgency_score > 0.3 else 'low'
                    }
                    
                    # Add personalization based on preferences
                    if preferences:
                        if preferences.get('prefer_organic', False) and 'organic' in product_name.lower():
                            recommendation['personalized_note'] = 'Matches your preference for organic products'
                    
                    recommendations.append(recommendation)
                    
            except (KeyError, ValueError, TypeError) as e:
                logger.warning(f"Skipping inventory item due to error: {e}")
                continue
        
        # Add seasonal recommendations
        current_month = datetime.now().month
        seasonal_items = self._get_seasonal_recommendations(current_month)
        recommendations.extend(seasonal_items)
        
        # Sort by priority and urgency
        try:
            recommendations.sort(key=lambda x: (
                0 if x.get('priority') == 'high' else 
                1 if x.get('priority') == 'medium' else 2, 
                -x.get('urgency_score', 0)
            ))
        except (KeyError, TypeError):
            # If sorting fails, just return as-is
            pass
        
        return recommendations[:10]  # Return top 10 recommendations
    
    def _fallback_recommendations(self, inventory: List[Dict], budget: Optional[float]) -> List[Dict]:
        """Fallback recommendations with safe defaults"""
        recommendations = []
        
        try:
            for item in inventory[:3]:  # Limit to 3 items
                # Safely get values with defaults
                quantity = float(item.get('quantity', 0))
                min_threshold = float(item.get('min_threshold', 1))
                product_id = str(item.get('product_id', ''))
                product_name = str(item.get('product_name', 'Product'))
                
                if quantity <= min_threshold:
                    recommendations.append({
                        'product_id': product_id,
                        'product_name': product_name,
                        'recommended_quantity': max(1, int(min_threshold * 2)),
                        'reason': 'Low stock level',
                        'priority': 'medium',
                        'urgency_score': 0.5,  # Default urgency
                        'estimated_cost': 3.99  # Default price
                    })
        except Exception as e:
            logger.error(f"Error in fallback recommendations: {e}")
        
        return recommendations
    
    def _get_seasonal_recommendations(self, month: int) -> List[Dict]:
        """Get seasonal product recommendations with safe defaults"""
        seasonal_map = {
            1: [('Vitamin C Supplements', 'Cold & flu season', 'medium')],
            2: [('Chocolate', 'Valentine\'s Day', 'low')],
            3: [('Cleaning Supplies', 'Spring cleaning', 'medium')],
            6: [('Sunscreen', 'Summer begins', 'high')],
            12: [('Baking Supplies', 'Holiday baking', 'high')]
        }
        
        items = seasonal_map.get(month, [])
        recommendations = []
        
        for name, reason, priority in items:
            recommendations.append({
                'product_id': f'seasonal_{name.lower().replace(" ", "_")}',
                'product_name': name,
                'reason': reason,
                'priority': priority,
                'seasonal': True,
                'estimated_cost': 4.99,
                'recommended_quantity': 1,
                'urgency_score': 0.3  # Lower urgency for seasonal items
            })
        
        return recommendations

# Global MCP instance
mcp_client = MCPIntegration()