import json
import os
from abc import ABC, abstractmethod


class BaseTransformer(ABC):
    """
    Abstract Base Class for all supplier data transformers.
    Enforces a strict contract for data harmonisation across different vendors.
    """

    def __init__(self, supplier_key: str):
        self.supplier_key = supplier_key
        self.field_mappings = self._load_mappings()

    def _load_mappings(self) -> dict:
        """Loads the central field mapping JSON layer dynamically."""
        # Moving up to backend/ root from transformers/ folder to find mappings
        mapping_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "mappings",
            "field_mapping.json",
        )

        if not os.path.exists(mapping_path):
            raise FileNotFoundError(
                f"Critical Error: Field mapping file missing at {mapping_path}"
            )

        with open(mapping_path, "r", encoding="utf-8") as f:
            all_mappings = json.load(f)

        supplier_map = all_mappings.get(self.supplier_key)
        if not supplier_map:
            raise KeyError(
                f"Mapping configuration missing for supplier key: '{self.supplier_key}'"
            )

        return supplier_map

    @abstractmethod
    def transform(self, raw_data: list) -> list:
        """
        Abstract method that each supplier subclass MUST implement.
        Should return a list of standard canonical dictionaries.
        """
        pass