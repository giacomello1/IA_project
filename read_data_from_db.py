import os
from typing import Optional
from supabase import create_client, Client
from beneficiaries import Beneficiary
from products import Product

class DatabaseReader:
    def __init__(self, url: str = None, key: str = None):
        """
        Initializes the Supabase client using direct credentials or environment variables.
        """
        self.url = url or os.environ.get("SUPABASE_URL")
        self.key = key or os.environ.get("SUPABASE_KEY")

        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY are missing. Connection failed.")

        self.client: Client = create_client(self.url, self.key)

    # =========================================================================
    # BENEFICIARIES METHODS
    # =========================================================================

    def get_all_beneficiaries(self) -> list[Beneficiary]:
        """Fetches all beneficiaries and returns them as a list of Beneficiary objects."""
        try:
            response = self.client.table("Beneficiaries").select("*").execute()
            return [Beneficiary.from_dict(row) for row in response.data]
        except Exception as e:
            print(f"Error fetching beneficiaries: {e}")
            return []

    def get_beneficiary_by_tax_code(self, tax_code: str) -> Optional[Beneficiary]:
        """Searches for a specific beneficiary by their tax code (fiscal code)."""
        try:
            response = self.client.table("Beneficiaries").select("*").eq("tax_code", tax_code).execute()
            if response.data:
                return Beneficiary.from_dict(response.data[0])
            return None
        except Exception as e:
            print(f"Error searching for tax code {tax_code}: {e}")
            return None

    # =========================================================================
    # PRODUCTS METHODS
    # =========================================================================

    def get_all_products(self) -> list[Product]:
        """Fetches all products and returns them as a list of Product objects."""
        try:
            response = self.client.table("Products").select("*").execute()
            return [Product.from_dict(row) for row in response.data]
        except Exception as e:
            print(f"Error fetching products: {e}")
            return []

    def get_product_by_name(self, name: str) -> Optional[Product]:
        """Searches for a specific product by its name."""
        try:
            response = self.client.table("Products").select("*").eq("name", name).execute()
            if response.data:
                return Product.from_dict(response.data[0])
            return None
        except Exception as e:
            print(f"Error searching for product {name}: {e}")
            return None
