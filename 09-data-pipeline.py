# AI-generated PR — review this code
# Description: "Added configurable data transformation pipeline with plugin support"

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Type
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TransformationType(Enum):
    FILTER = "filter"
    MAP = "map"
    ENRICH = "enrich"
    VALIDATE = "validate"
    NORMALIZE = "normalize"


@dataclass
class TransformationConfig:
    name: str
    type: TransformationType
    params: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    order: int = 0


class TransformationStrategy(ABC):
    @abstractmethod
    def transform(self, records: List[Dict], config: TransformationConfig) -> List[Dict]:
        pass

    @abstractmethod
    def validate_config(self, config: TransformationConfig) -> bool:
        pass


class FilterStrategy(TransformationStrategy):
    def transform(self, records: List[Dict], config: TransformationConfig) -> List[Dict]:
        field_name = config.params.get("field")
        operator = config.params.get("operator", "eq")
        value = config.params.get("value")

        result = []
        for record in records:
            record_value = record.get(field_name)
            if operator == "eq" and record_value == value:
                result.append(record)
            elif operator == "neq" and record_value != value:
                result.append(record)
            elif operator == "gt" and record_value > value:
                result.append(record)
            elif operator == "lt" and record_value < value:
                result.append(record)
            elif operator == "contains" and value in str(record_value):
                result.append(record)

        return result

    def validate_config(self, config: TransformationConfig) -> bool:
        return "field" in config.params and "value" in config.params


class MapStrategy(TransformationStrategy):
    def transform(self, records: List[Dict], config: TransformationConfig) -> List[Dict]:
        field_mapping = config.params.get("mapping", {})
        result = []
        for record in records:
            new_record = {}
            for old_key, new_key in field_mapping.items():
                if old_key in record:
                    new_record[new_key] = record[old_key]
            result.append(new_record)
        return result

    def validate_config(self, config: TransformationConfig) -> bool:
        return "mapping" in config.params


class NormalizeStrategy(TransformationStrategy):
    def transform(self, records: List[Dict], config: TransformationConfig) -> List[Dict]:
        fields = config.params.get("fields", [])
        result = []
        for record in records:
            new_record = record.copy()
            for f in fields:
                if f in new_record and isinstance(new_record[f], str):
                    new_record[f] = new_record[f].strip().lower()
            result.append(new_record)
        return result

    def validate_config(self, config: TransformationConfig) -> bool:
        return "fields" in config.params


class StrategyRegistry:
    _strategies: Dict[TransformationType, Type[TransformationStrategy]] = {}

    @classmethod
    def register(cls, transformation_type: TransformationType, strategy_class: Type[TransformationStrategy]):
        cls._strategies[transformation_type] = strategy_class

    @classmethod
    def get(cls, transformation_type: TransformationType) -> Optional[TransformationStrategy]:
        strategy_class = cls._strategies.get(transformation_type)
        if strategy_class:
            return strategy_class()
        return None


StrategyRegistry.register(TransformationType.FILTER, FilterStrategy)
StrategyRegistry.register(TransformationType.MAP, MapStrategy)
StrategyRegistry.register(TransformationType.NORMALIZE, NormalizeStrategy)


class TransformationPipeline:
    def __init__(self, configs: List[TransformationConfig]):
        self.configs = sorted(
            [c for c in configs if c.enabled],
            key=lambda c: c.order,
        )

    def execute(self, records: List[Dict]) -> List[Dict]:
        current = records
        for config in self.configs:
            strategy = StrategyRegistry.get(config.type)
            if strategy is None:
                logger.warning(f"No strategy found for {config.type}")
                continue
            if not strategy.validate_config(config):
                logger.warning(f"Invalid config for {config.name}")
                continue
            current = strategy.transform(current, config)
            logger.info(f"Applied {config.name}: {len(current)} records remaining")
        return current


# Usage
def clean_user_data(users: List[Dict]) -> List[Dict]:
    """Clean and normalize user records — filter inactive, normalize names, remap fields."""
    pipeline = TransformationPipeline([
        TransformationConfig(
            name="filter_active",
            type=TransformationType.FILTER,
            params={"field": "status", "operator": "eq", "value": "active"},
            order=1,
        ),
        TransformationConfig(
            name="normalize_names",
            type=TransformationType.NORMALIZE,
            params={"fields": ["name", "email"]},
            order=2,
        ),
        TransformationConfig(
            name="remap_fields",
            type=TransformationType.MAP,
            params={"mapping": {"name": "full_name", "email": "email_address", "status": "account_status"}},
            order=3,
        ),
    ])
    return pipeline.execute(users)
