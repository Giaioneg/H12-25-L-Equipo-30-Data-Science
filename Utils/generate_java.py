import os
from pydantic import BaseModel
from typing import get_type_hints

ARTIFACTS_DIR = 'artifacts'
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

# Definimos el mapeo de tipos Python -> Java
TYPE_MAPPING = {
    int: "Integer",
    float: "Double",
    str: "String",
    bool: "Boolean"
}

def generate_java_dto(model: BaseModel, class_name: str, package_name: str = "com.hackathon.model"):
    """Genera una clase Java (POJO) basada en un modelo Pydantic."""
    
    java_code = f"package {package_name};\n\n"
    java_code += "import com.fasterxml.jackson.annotation.JsonProperty;\n"
    java_code += "import lombok.Data;\n"
    java_code += "import lombok.AllArgsConstructor;\n"
    java_code += "import lombok.NoArgsConstructor;\n\n"
    
    # Usamos Lombok para ahorrar código repetitivo (Getters/Setters)
    java_code += "@Data\n@AllArgsConstructor\n@NoArgsConstructor\n"
    java_code += f"public class {class_name} {{\n\n"

    type_hints = get_type_hints(model)
    
    for field, python_type in type_hints.items():
        java_type = TYPE_MAPPING.get(python_type, "String") # Default a String si falla
        java_code += f"    @JsonProperty(\"{field}\")\n"
        java_code += f"    private {java_type} {field};\n\n"

    java_code += "}"
    
    return java_code

if __name__ == "__main__":
    # Importamos tu modelo real desde main.py
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from main import FlightRequest  

    # Generar código
    java_class = generate_java_dto(FlightRequest, "FlightRequestDTO")
    
    # Guardar archivo
    with open(f'{ARTIFACTS_DIR}/FlightRequestDTO.java', "w") as f:
        f.write(java_class)

    print(f'✅ Archivo Java generado en {ARTIFACTS_DIR}/FlightRequestDTO.java')