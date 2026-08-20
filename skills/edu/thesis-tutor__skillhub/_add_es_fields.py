import json

with open(r"d:\Skill Library\Thesis Tutor v4.0\knowledge_base\_shared\disciplines.json", "r", encoding="utf-8") as f:
    data = json.load(f)

disciplines = data["disciplines"]

es_names = {
    "cs": "Informatica",
    "economics": "Economia",
    "education": "Educacion",
    "engineering": "Ingenieria",
    "law": "Derecho",
    "literature": "Literatura",
    "management": "Administracion",
    "medical": "Medicina",
    "psychology": "Psicologia",
    "art": "Arte",
    "science": "Ciencias",
    "agriculture": "Agronomia",
    "library_science": "Biblioteconomia",
    "archaeology": "Arqueologia",
    "sports_science": "Ciencias del Deporte"
}

es_keywords = {
    "cs": ["computadora", "software", "inteligencia artificial", "IA", "grandes datos", "ciberseguridad", "IoT", "ciencia de datos", "aprendizaje automatico", "aprendizaje profundo"],
    "economics": ["economia", "finanzas", "fiscal", "seguros", "banca", "inversion", "economia internacional", "economia industrial"],
    "education": ["educacion", "ensenanza", "pedagogia", "curriculo", "ciencia del aprendizaje", "educacion superior", "educacion vocacional"],
    "engineering": ["mecanica", "electronica", "comunicacion", "automatizacion", "civil", "quimica", "materiales", "energia", "medio ambiente", "aeroespacial"],
    "law": ["derecho", "juridico", "judicial", "legislacion", "cumplimiento", "derecho penal", "derecho civil", "derecho administrativo"],
    "literature": ["literatura", "lengua", "linguistica", "traduccion", "literatura comparada"],
    "management": ["gestion", "marketing", "mercado", "recursos humanos", "MBA", "negocios", "contabilidad", "finanzas"],
    "medical": ["medicina", "clinica", "farmacia", "salud publica", "enfermeria", "biologia", "medicina basica", "medicina preventiva"],
    "psychology": ["psicologia", "cognitivo", "psicologia del desarrollo", "psicologia social", "psicologia clinica"],
    "art": ["arte", "diseno", "visual", "musica", "bellas artes", "patrimonio inmaterial", "teatro", "cine"],
    "science": ["matematicas", "fisica", "quimica", "biologia", "geografia", "astronomia", "estadisticas"],
    "agriculture": ["agronomia", "silvicultura", "ganaderia", "veterinaria", "pesca", "economia agricola"],
    "library_science": ["biblioteca", "archivo", "gestion de la informacion", "gestion del conocimiento", "documentacion"],
    "archaeology": ["arqueologia", "artefacto", "sitio", "excavacion", "preservacion del patrimonio"],
    "sports_science": ["deportes", "ejercicio", "entrenamiento", "educacion fisica", "kinesiologia"]
}

field_order = ["name_zh", "name_en", "name_ja", "name_ko", "name_fr", "name_de", "name_es", "keywords_zh", "keywords_en", "keywords_ja", "keywords_ko", "keywords_fr", "keywords_de", "keywords_es", "subfields"]

new_disciplines = {}
for key, disc in disciplines.items():
    disc["name_es"] = es_names[key]
    disc["keywords_es"] = es_keywords[key]
    ordered = {}
    for field in field_order:
        if field in disc:
            ordered[field] = disc[field]
    for field in disc:
        if field not in ordered:
            ordered[field] = disc[field]
    new_disciplines[key] = ordered

data["disciplines"] = new_disciplines

with open(r"d:\Skill Library\Thesis Tutor v4.0\knowledge_base\_shared\disciplines.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# verify
with open(r"d:\Skill Library\Thesis Tutor v4.0\knowledge_base\_shared\disciplines.json", "r", encoding="utf-8") as f:
    v = json.load(f)
for k in v["disciplines"]:
    d = v["disciplines"][k]
    keys = list(d.keys())
    assert "name_es" in d, f"{k} missing name_es"
    assert "keywords_es" in d, f"{k} missing keywords_es"
    assert keys.index("name_es") == keys.index("name_de") + 1, f"{k}: name_es order wrong"
    assert keys.index("keywords_es") == keys.index("keywords_de") + 1, f"{k}: keywords_es order wrong"
    assert keys.index("keywords_es") < keys.index("subfields"), f"{k}: keywords_es before subfields"
print("OK: All 15 disciplines updated with name_es and keywords_es in correct field order.")
