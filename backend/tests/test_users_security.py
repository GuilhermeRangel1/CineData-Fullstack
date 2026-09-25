from app.users.security import gerar_hash_senha, verificar_senha


def test_password_hash_does_not_store_the_original_password() -> None:
    password = "uma-senha-segura-para-teste"

    password_hash = gerar_hash_senha(password)

    assert password_hash != password
    assert verificar_senha(password, password_hash)
    assert not verificar_senha("senha-incorreta", password_hash)
