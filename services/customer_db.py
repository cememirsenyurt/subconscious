"""
Customer Database Service.

Manages persistent customer data across sessions (within server runtime).
Enables long-term memory - when a customer returns and gives their name,
we can look up their previous reservations and preferences.
"""

from typing import Dict, Optional


class CustomerDatabase:
    """
    Stores customer information persistently across sessions.
    
    When a customer gives their name, we can look up their previous reservations.
    This simulates long-term memory - data persists until server restarts.
    
    In a production environment, this would be backed by a real database.
    """
    
    def __init__(self):
        self.customers: Dict[str, Dict] = {}  # name -> customer info
    
    def normalize_name(self, name: str) -> str:
        """Normalize name for lookup (lowercase, stripped)."""
        return name.lower().strip()
    
    def save_customer(self, name: str, business_id: str, info: Dict):
        """
        Save or update customer information.
        
        Args:
            name: Customer's name (will be normalized for storage)
            info: Dictionary of customer information to save
        """
        if not name:
            return
        
        key = f"{business_id}:{self.normalize_name(name)}"
        if key not in self.customers:
            self.customers[key] = {}
        
        # Merge new info with existing
        for k, v in info.items():
            if v:  # Only save non-empty values
                self.customers[key][k] = v
        
        self.customers[key]["name"] = name  # Keep original case
        self.customers[key]["business_id"] = business_id
        print(f"[CustomerDB] Saved customer: {name} -> {self.customers[key]}")
    
    def find_customer(self, name: str, business_id: str) -> Optional[Dict]:
        """
        Look up a customer by name.
        
        Args:
            name: Customer's name to look up
            
        Returns:
            Dictionary of customer information, or None if not found
        """
        if not name:
            return None
        
        key = f"{business_id}:{self.normalize_name(name)}"
        if key in self.customers:
            print(f"[CustomerDB] Found customer: {name} -> {self.customers[key]}")
            return self.customers[key].copy()
        return None
    
    def get_all_customers(self) -> Dict[str, Dict]:
        """
        Get all stored customers (for debugging).
        
        Returns:
            Dictionary of all customers
        """
        return self.customers.copy()


# Global customer database instance - persists across sessions
customer_db = CustomerDatabase()
