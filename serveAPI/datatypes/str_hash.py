import hashlib


def make_hash(dados: bytes | str) -> str:
    if isinstance(dados, str):
        dados = dados.encode("utf-8")  # Converte str para bytes
    return hashlib.sha256(dados).hexdigest()


def check_hash(dados: bytes | str, hash_recebido: str) -> bool:
    hash_calculado = make_hash(dados)
    return hash_calculado == hash_recebido
