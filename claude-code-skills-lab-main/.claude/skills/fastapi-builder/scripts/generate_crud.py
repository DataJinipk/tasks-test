#!/usr/bin/env python3
"""
FastAPI CRUD Generator

Generates model, schema, and router files for a new resource with full CRUD operations.

Usage:
    python generate_crud.py <resource-name> [--fields field1:type field2:type ...]

Examples:
    python generate_crud.py product
    python generate_crud.py product --fields name:str price:float description:str stock:int
    python generate_crud.py article --fields title:str content:str published:bool author_id:int
"""

import sys
from pathlib import Path
from typing import List, Tuple


FIELD_TYPE_MAPPING = {
    "str": ("String", "str", None),
    "int": ("Integer", "int", None),
    "float": ("Float", "float", None),
    "bool": ("Boolean", "bool", "False"),
    "datetime": ("DateTime", "datetime", "None"),
}


def parse_fields(field_args: List[str]) -> List[Tuple[str, str, str, str]]:
    """
    Parse field arguments into (name, sql_type, python_type, default) tuples

    Returns:
        List of tuples: [(field_name, sql_type, python_type, default), ...]
    """
    fields = []
    for field_arg in field_args:
        if ":" not in field_arg:
            print(f"Warning: Skipping invalid field format: {field_arg}")
            continue

        field_name, field_type = field_arg.split(":", 1)
        field_type = field_type.lower()

        if field_type not in FIELD_TYPE_MAPPING:
            print(f"Warning: Unknown type '{field_type}' for field '{field_name}', using str")
            field_type = "str"

        sql_type, python_type, default = FIELD_TYPE_MAPPING[field_type]
        fields.append((field_name, sql_type, python_type, default))

    return fields


def generate_model(resource_name: str, fields: List[Tuple[str, str, str, str]]) -> str:
    """Generate SQLAlchemy model"""
    class_name = resource_name.capitalize()

    model = f'''from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.sql import func
from ..database import Base


class {class_name}(Base):
    __tablename__ = "{resource_name}s"

    id = Column(Integer, primary_key=True, index=True)
'''

    for field_name, sql_type, _, default in fields:
        nullable = ", nullable=True" if default == "None" else ""
        default_val = f", default={default}" if default and default != "None" else ""
        model += f"    {field_name} = Column({sql_type}{nullable}{default_val})\n"

    model += '''    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
'''

    return model


def generate_schema(resource_name: str, fields: List[Tuple[str, str, str, str]]) -> str:
    """Generate Pydantic schemas"""
    class_name = resource_name.capitalize()

    # Import statements
    schema = "from pydantic import BaseModel, ConfigDict\n"
    schema += "from typing import Optional\n"
    if any(python_type == "datetime" for _, _, python_type, _ in fields):
        schema += "from datetime import datetime\n"
    schema += "\n\n"

    # Base schema
    schema += f"class {class_name}Base(BaseModel):\n"
    for field_name, _, python_type, default in fields:
        optional = "Optional[" + python_type + "] = None" if default == "None" else python_type
        schema += f"    {field_name}: {optional}\n"

    # Create schema
    schema += f"\n\nclass {class_name}Create({class_name}Base):\n"
    schema += "    pass\n"

    # Update schema
    schema += f"\n\nclass {class_name}Update(BaseModel):\n"
    for field_name, _, python_type, _ in fields:
        schema += f"    {field_name}: Optional[{python_type}] = None\n"

    # Response schema
    schema += f"\n\nclass {class_name}({class_name}Base):\n"
    schema += "    id: int\n"
    schema += "    created_at: datetime\n"
    schema += "    updated_at: Optional[datetime] = None\n\n"
    schema += "    model_config = ConfigDict(from_attributes=True)\n"

    return schema


def generate_router(resource_name: str) -> str:
    """Generate FastAPI router with CRUD endpoints"""
    class_name = resource_name.capitalize()
    plural_name = resource_name + "s"

    router = f'''from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.{resource_name} import {class_name}
from ..schemas.{resource_name} import (
    {class_name},
    {class_name}Create,
    {class_name}Update
)

router = APIRouter(prefix="/{plural_name}", tags=["{plural_name}"])


@router.get("/", response_model=List[{class_name}])
async def get_{plural_name}(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all {plural_name}"""
    {plural_name} = db.query({class_name}).offset(skip).limit(limit).all()
    return {plural_name}


@router.get("/{{{{item_id}}}}", response_model={class_name})
async def get_{resource_name}(item_id: int, db: Session = Depends(get_db)):
    """Get a specific {resource_name} by ID"""
    {resource_name} = db.query({class_name}).filter({class_name}.id == item_id).first()
    if not {resource_name}:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="{class_name} not found"
        )
    return {resource_name}


@router.post("/", response_model={class_name}, status_code=status.HTTP_201_CREATED)
async def create_{resource_name}(
    {resource_name}: {class_name}Create,
    db: Session = Depends(get_db)
):
    """Create a new {resource_name}"""
    db_{resource_name} = {class_name}(**{resource_name}.dict())
    db.add(db_{resource_name})
    db.commit()
    db.refresh(db_{resource_name})
    return db_{resource_name}


@router.put("/{{{{item_id}}}}", response_model={class_name})
async def update_{resource_name}(
    item_id: int,
    {resource_name}_update: {class_name}Update,
    db: Session = Depends(get_db)
):
    """Update an existing {resource_name}"""
    db_{resource_name} = db.query({class_name}).filter({class_name}.id == item_id).first()
    if not db_{resource_name}:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="{class_name} not found"
        )

    update_data = {resource_name}_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_{resource_name}, key, value)

    db.commit()
    db.refresh(db_{resource_name})
    return db_{resource_name}


@router.delete("/{{{{item_id}}}}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_{resource_name}(item_id: int, db: Session = Depends(get_db)):
    """Delete a {resource_name}"""
    db_{resource_name} = db.query({class_name}).filter({class_name}.id == item_id).first()
    if not db_{resource_name}:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="{class_name} not found"
        )

    db.delete(db_{resource_name})
    db.commit()
'''

    return router


def generate_crud(resource_name: str, fields: List[Tuple[str, str, str, str]]):
    """Generate all CRUD files for a resource"""
    app_path = Path("app")

    if not app_path.exists():
        print("Error: 'app' directory not found. Run this from your project root.")
        return False

    # Create necessary directories
    models_path = app_path / "models"
    schemas_path = app_path / "schemas"
    routers_path = app_path / "routers"

    models_path.mkdir(exist_ok=True)
    schemas_path.mkdir(exist_ok=True)
    routers_path.mkdir(exist_ok=True)

    # Ensure __init__.py files exist
    (models_path / "__init__.py").touch()
    (schemas_path / "__init__.py").touch()
    (routers_path / "__init__.py").touch()

    # Generate files
    print(f"Generating CRUD for resource: {resource_name}")

    # Model
    model_file = models_path / f"{resource_name}.py"
    model_file.write_text(generate_model(resource_name, fields))
    print(f"  ✅ Created {model_file}")

    # Schema
    schema_file = schemas_path / f"{resource_name}.py"
    schema_file.write_text(generate_schema(resource_name, fields))
    print(f"  ✅ Created {schema_file}")

    # Router
    router_file = routers_path / f"{resource_name}.py"
    router_file.write_text(generate_router(resource_name))
    print(f"  ✅ Created {router_file}")

    # Instructions
    print("\n📝 Next steps:")
    print(f"1. Add the router to app/main.py:")
    print(f"   from .routers import {resource_name}")
    print(f"   app.include_router({resource_name}.router)")
    print(f"\n2. Create database migration (if using Alembic):")
    print(f"   alembic revision --autogenerate -m \"Add {resource_name} table\"")
    print(f"   alembic upgrade head")
    print(f"\n3. Test your endpoints at http://localhost:8000/docs")

    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_crud.py <resource-name> [--fields field1:type field2:type ...]")
        print("\nSupported types: str, int, float, bool, datetime")
        print("\nExamples:")
        print("  python generate_crud.py product")
        print("  python generate_crud.py product --fields name:str price:float stock:int")
        print("  python generate_crud.py article --fields title:str content:str published:bool")
        sys.exit(1)

    resource_name = sys.argv[1].lower()

    # Parse fields
    fields = []
    if len(sys.argv) > 2 and sys.argv[2] == "--fields":
        fields = parse_fields(sys.argv[3:])
    else:
        # Default fields
        fields = [
            ("name", "String", "str", None),
            ("description", "String", "str", "None"),
        ]

    success = generate_crud(resource_name, fields)
    sys.exit(0 if success else 1)
