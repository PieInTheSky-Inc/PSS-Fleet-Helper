from src.tests import reaction_roles


def test_reaction_roles() -> bool:
    try:
        reaction_roles.test()
        success = True
    except Exception as e:
        print(e)
        success = False
    print(f'Reaction Roles model test: {"success" if success else "fail"}')
    return success


def test_all() -> None:
    test_reaction_roles()


if __name__ == '__main__':
    test_all()