"""Запуск примеров и разбор одной фразы.

Печатает короткий запрос, составной запрос и три неверных.
Если фраза передана при запуске, разбирает только её.
"""

import sys

from parser import ParseError, format_tree, parse


QUERIES = [
    "найди все книги",
    "найди все книги Толстого и Достоевского по лингвистике изданные после 2015",
]

BAD = [
    "книги Толстого",
    "найди",
    "найди книги после 2015",
]


def show(query):
    """Печатает фразу и дерево её разбора.

    Args:
        query: Текст запроса.

    Returns:
        Ничего.
    """
    print(query)
    print(format_tree(parse(query)))
    print()


def run_examples():
    """Печатает учебные фразы и проверяет, что неверные отклоняются.

    Args:
        Нет.

    Returns:
        Ноль, если проверка прошла. Единица, если неверная фраза была принята.
    """
    print("Запросы")
    print()
    for query in QUERIES:
        show(query)

    print("Неверные запросы")
    print()
    failed = 0
    # неверные фразы должны останавливать разбор
    for query in BAD:
        print(query)
        try:
            parse(query)
        except ParseError as error:
            print(error)
            failed += 1
        else:
            print("Ошибка: запрос неожиданно разобрался")
        print()

    if failed != len(BAD):
        print("Проверка: не все неверные запросы отклонены")
        return 1

    print("Проверка: запросы разобрались, неверные отклонены")
    return 0


def run_query(query):
    """Печатает дерево одной фразы или сообщение об ошибке.

    Args:
        query: Текст запроса.

    Returns:
        Ноль, если дерево построено. Единица, если фраза неверна.
    """
    try:
        print(format_tree(parse(query)))
    except ParseError as error:
        print(error)
        return 1
    return 0


def main():
    """Запускает примеры или разбирает фразу, переданную при запуске.

    Args:
        Нет.

    Returns:
        Ноль при успешном разборе. Единица, если фраза неверна или проверка не прошла.
    """
    if len(sys.argv) > 1:
        return run_query(" ".join(sys.argv[1:]))
    return run_examples()


if __name__ == "__main__":
    sys.exit(main())
