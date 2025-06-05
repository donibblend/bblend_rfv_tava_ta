# Em core/rfv_rules.py

"""
Este arquivo centraliza todas as regras de negócio para o cálculo de RFV.
Qualquer mudança nas regras de pontuação ou categorização deve ser feita aqui.
"""

# ==============================================================================
# REGRAS DO MODELO ANTIGO
# ==============================================================================

RFV_RULES_ANTIGO = {
    "Insumos": {
        "R": {(0, 90): 3, (91, 180): 2, (181, 365): 1},
        "F": {(5, float('inf')): 3, (3, 4): 2, (1, 2): 1},
        "V": {(6, float('inf')): 3, (4, 5): 2, (1, 3): 1},
    },
    "Cápsulas": {
        "R": {(0, 90): 3, (91, 180): 2, (181, 365): 1},
        "F": {(8, float('inf')): 3, (3, 7): 2, (1, 2): 1},
        "V": {(360, float('inf')): 3, (120, 359): 2, (1, 119): 1},
    }
}

CATEGORIAS_ANTIGO = {
    9: "ELITE",
    8: "POTENCIAL ELITE",
    7: "CLIENTE LEAL",
    6: "PROMISSOR",
    5: "PEGANDO NO SONO",
    4: "EM RISCO",
    3: "ADORMECIDO",
    # Scores menores que 3 serão tratados como CHURN
}

# ==============================================================================
# REGRAS DO MODELO NOVO
# ==============================================================================

RFV_RULES_NOVO = {
    "Filtro": {
        "R": {(0, 120): 3, (121, 180): 2, (181, 365): 1},
        "F": {(3, float('inf')): 3, (2, 2): 2, (1, 1): 1},
        "V": {(3, float('inf')): 3, (2, 2): 2, (1, 1): 1},
    },
    "Cilindros": {
        "R": {(0, 60): 3, (61, 180): 2, (181, 365): 1},
        "F": {(5, float('inf')): 3, (4, 4): 2, (1, 3): 1},
        "V": {(6, float('inf')): 3, (4, 5): 2, (1, 3): 1},
    },
    "Cápsulas": {
        # Mantém as mesmas regras do modelo antigo, mas podemos definir aqui
        # para manter a consistência.
        "R": {(0, 90): 3, (91, 180): 2, (181, 365): 1},
        "F": {(8, float('inf')): 3, (3, 7): 2, (1, 2): 1},
        "V": {(360, float('inf')): 3, (120, 359): 2, (1, 119): 1},
    }
}

CATEGORIAS_NOVO = {
    (9, 9): "DIAMANTE",
    (7, 8): "OURO",
    (5, 6): "PRATA",
    (3, 4): "BRONZE",
    # Scores menores que 3 serão tratados como CHURN
}