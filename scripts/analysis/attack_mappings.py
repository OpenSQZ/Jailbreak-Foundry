#!/usr/bin/env python3
"""
Mappings between attack names and their corresponding arXiv paper IDs.
This file provides bidirectional lookup between attack method names and paper IDs.
"""

ATTACK_NAME_TO_ARXIV_ID = {
    "abj": "2407.16205",
    "advprefix": "2412.10321",
    "aim": "2506.12685",
    "air": "2410.03857",
    "arr_attack": "2505.17598",
    "autodanturbo": "2410.05295",
    "bon": "2412.03556",
    "deep_inception": "2311.03191",
    "equacode": "2512.23173",
    "fitd": "2502.19820",
    "flip_attack": "2410.02832",
    "gta": "2511.16278",
    "hill": "2509.14297",
    "hpm": "2512.18244",
    "ice": "2505.14316",
    "infoflood": "2506.12274",
    "isa": "2511.00556",
    "jailcon_cit": "2510.21189",
    "jailcon_cvt": "2510.21189",
    "jailexpert": "2508.19292",
    "majic": "2508.13048",
    "mousetrap": "2502.15806",
    "overfitting_gen": "2510.02833",
    "pair": "2310.08419",
    "pap": "2401.06373",
    "past_tense": "2407.11969",
    "pe_coa": "2510.08859",
    "persona_gen": "2507.22171",
    "prefill": "2504.21038",
    "puzzled": "2508.01306",
    "queryattack": "2502.09723",
    "renellm": "2311.08268",
    "RA_DRI": "2507.05248",
    "RA_SRI": "2507.05248",
    "rts": "2510.01223",
    "sata_elp": "2412.15289",
    "sata_mlm": "2412.15289",
    "scp": "2504.05652",
    "seqar": "2407.01902",
    "tap": "2312.02119",
    "tombraider": "2501.18628",
    "trial": "2509.05367",
    "trojfill": "2510.21190",
    "wordgame": "2405.14023",
    "wordgame_plus": "2405.14023",
}

ATTACK_NAME_TO_ATTACK = {
    "abj": "ABJ",
    "aim": "AIM",
    "air": "AIR",
    "arr_attack": "ArrAttack",
    "bon": "BoN",
    "deep_inception": "DeepInception",
    "equacode": "EquaCode",
    "flip_attack": "FlipAttack",
    "gta": "GTA",
    "hill": "HILL",
    "isa": "ISA",
    "jailcon_cit": "JailCon-CIT",
    "jailcon_cvt": "JailCon-CVT",
    "jailexpert": "JailExpert",
    "majic": "Majic",
    "mousetrap": "Mousetrap",
    "pair": "PAIR",
    "pap": "PAP",
    "past_tense": "Past-Tense",
    "pe_coa": "PE-COA",
    "prefill": "Prefill",
    "puzzled": "Puzzled",
    "queryattack": "QueryAttack",
    "renellm": "Renellm",
    "RA_DRI": "RA-DRI",
    "RA_SRI": "RA-SRI",
    "rts": "RTS",
    "sata_elp": "SATA-ELP",
    "sata_mlm": "SATA-MLM",
    "scp": "SCP",
    "seqar": "SeqAR",
    "tap": "TAP",
    "tombraider": "Tombraider",
    "trial": "Trial",
    "trojfill": "Trojfill",
    "wordgame": "Wordgame",
    "wordgame_plus": "Wordgame+",
}


def get_arxiv_id(attack_name: str) -> str | None:
    """
    Get arXiv ID for a given attack name.

    Args:
        attack_name: Name of the attack method

    Returns:
        arXiv ID string or None if not found
    """
    return ATTACK_NAME_TO_ARXIV_ID.get(attack_name)


def get_attack_name(attack_name: str) -> str | None:
    """
    Get attack name for a given arXiv ID.

    Args:
        attack_name: Name of the attack method

    Returns:
        Attack name string or None if not found
    """
    return ATTACK_NAME_TO_ATTACK.get(attack_name)
