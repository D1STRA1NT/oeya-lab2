"""Разбор запроса и печать дерева.

Читает фразу слева направо по правилам языка и собирает дерево составляющих.
Если фраза правилам не соответствует, сообщает место ошибки.
Результат использует модуль запуска примеров.
"""

from grammar import word_kind


EXPECTED = {
    "VERB": "глагол (найди, покажи или выведи)",
    "ALL": "«все»",
    "TYPE": "тип документа (книги, статьи или журналы)",
    "NAME": "имя автора",
    "TOPIC": "тема",
    "PO": "«по»",
    "POSLE": "«после»",
    "GODA": "«года»",
    "IZDANNYE": "«изданные»",
    "AND": "«и»",
    "NUMBER": "число",
}


class ParseError(Exception):
    """Ошибка: фраза не соответствует правилам языка."""

    def __init__(self, position, expected, found):
        """Собирает сообщение о месте, где фраза разошлась с правилами.

        Args:
            position: Номер слова в фразе, начиная с единицы.
            expected: Что должно было стоять на этом месте.
            found: Слово, которое там оказалось. Пусто, если фраза кончилась.

        Returns:
            Ничего.
        """
        self.position = position
        self.expected = expected
        self.found = found
        if found is None:
            detail = "а слова кончились"
        else:
            detail = f"получено «{found}»"
        super().__init__(
            f"Ошибка на позиции {position}: ожидалось {expected}, {detail}"
        )


class Token:
    """Слово фразы вместе с его ролью и номером места."""

    def __init__(self, text, kind, position):
        """Запоминает слово, его роль и место во фразе.

        Args:
            text: Слово, как оно написано во фразе.
            kind: Роль слова в запросе.
            position: Номер слова в фразе, начиная с единицы.

        Returns:
            Ничего.
        """
        self.text = text
        self.kind = kind
        self.position = position


class Node:
    """Одна составляющая дерева разбора."""

    def __init__(self, name, children=None, value=None):
        """Создаёт составляющую и вкладывает в неё дочерние части.

        Args:
            name: Название составляющей.
            children: Вложенные составляющие. Можно не передавать.
            value: Уточнение к названию, обычно само слово. Можно не передавать.

        Returns:
            Ничего.
        """
        self.name = name
        self.children = children or []
        self.value = value


def tokenize(text):
    """Делит фразу на слова и определяет роль каждого.

    Args:
        text: Текст запроса.

    Returns:
        Слова фразы по порядку, с ролью и номером места.
    """
    tokens = []
    for position, word in enumerate(text.split(), start=1):
        kind = word_kind(word.lower())
        # слова нет в словаре — дерево дальше не строится
        if kind is None:
            raise ParseError(position, "слово из словаря", word)
        tokens.append(Token(word, kind, position))
    return tokens


class Parser:
    """Чтение фразы слева направо и сбор дерева."""

    def __init__(self, tokens):
        """Готовит чтение с первого слова.

        Args:
            tokens: Слова фразы по порядку.

        Returns:
            Ничего.
        """
        self.tokens = tokens
        self.index = 0

    def peek(self):
        """Показывает текущее слово, не сдвигая чтение.

        Args:
            Нет.

        Returns:
            Текущее слово. Пустое значение, если фраза уже кончилась.
        """
        if self.index < len(self.tokens):
            return self.tokens[self.index]
        return None

    def position(self):
        """Сообщает номер слова, на котором сейчас стоит чтение.

        Args:
            Нет.

        Returns:
            Номер слова, начиная с единицы. Если слова кончились — номер следующего места.
        """
        current = self.peek()
        if current is not None:
            return current.position
        if self.tokens:
            return self.tokens[-1].position + 1
        return 1

    def eat(self, kind):
        """Читает текущее слово, если у него ожидаемая роль, и сдвигает чтение на следующее слово.

        Если роль другая или слова кончились, разбор останавливается.

        Args:
            kind: Ожидаемая роль слова.

        Returns:
            Прочитанное слово.
        """
        current = self.peek()
        if current is None or current.kind != kind:
            found = None if current is None else current.text
            raise ParseError(self.position(), EXPECTED[kind], found)
        self.index += 1
        return current

    def parse_query(self):
        """Разбирает всю фразу: сначала глагол, затем объект.

        Args:
            Нет.

        Returns:
            Корень дерева разбора.
        """
        if not self.tokens:
            raise ParseError(1, EXPECTED["VERB"], None)
        verb = self.eat("VERB")
        # корень «запрос»: лист «глагол» и узел «объект»
        return Node("запрос", [
            # лист «глагол»
            Node("глагол", value=verb.text),
            # узел «объект»
            self.parse_object(),
        ])

    def parse_object(self):
        """Разбирает объект: необязательное «все», тип документа и фильтры.

        Args:
            Нет.

        Returns:
            Составляющая объекта со вложенными частями.
        """
        children = []
        current = self.peek()
        # «все» необязательно и стоит только перед типом
        if current is not None and current.kind == "ALL":
            # лист «все»
            children.append(Node(self.eat("ALL").text))
        document_type = self.eat("TYPE")
        # лист «тип»
        children.append(Node("тип", value=document_type.text))
        # листья «год», «тема», «издание» или узел «авторы»
        children.extend(self.parse_filters())
        return Node("объект", children)

    def parse_filters(self):
        """Читает фильтры один за другим, пока фраза не кончится.

        Слово, которое не начинает фильтр, останавливает разбор.

        Args:
            Нет.

        Returns:
            Список составляющих фильтров. Список пуст, если фильтров нет.
        """
        filters = []
        while self.peek() is not None:
            filters.append(self.parse_filter())
        return filters

    def parse_filter(self):
        """Определяет вид фильтра по первому ещё не прочитанному слову.

        Args:
            Нет.

        Returns:
            Составляющая одного фильтра.
        """
        current = self.peek()
        # число начинает год
        if current.kind == "NUMBER":
            # лист «год»
            return self.parse_year()
        # имя — авторов
        if current.kind == "NAME":
            # узел «авторы», внутри листья с именами
            return self.parse_authors()
        # «по» — тему
        if current.kind == "PO":
            # лист «тема»
            return self.parse_topic()
        # «изданные» — издание
        if current.kind == "IZDANNYE":
            # лист «издание»
            return self.parse_published()
        raise ParseError(
            current.position,
            "фильтр (год, имя автора, «по» или «изданные»)",
            current.text,
        )

    def parse_year(self):
        """Читает фильтр года: число и следующее за ним слово «года».

        Args:
            Нет.

        Returns:
            Составляющая года.
        """
        number = self.eat("NUMBER")
        self.eat("GODA")
        return Node("год", value=number.text)

    def parse_authors(self):
        """Читает одно или несколько имён, соединённых союзом «и».

        Args:
            Нет.

        Returns:
            Составляющая со списком имён.
        """
        names = [self.eat("NAME")]
        # каждое «и» присоединяет ещё одно имя к той же группе
        while self.peek() is not None and self.peek().kind == "AND":
            self.eat("AND")
            names.append(self.eat("NAME"))
        # узел «авторы», дети — листья с именами
        return Node("авторы", [Node(name.text) for name in names])

    def parse_topic(self):
        """Читает фильтр темы: слово «по» и название темы.

        Args:
            Нет.

        Returns:
            Составляющая темы.
        """
        self.eat("PO")
        topic = self.eat("TOPIC")
        return Node("тема", value=topic.text)

    def parse_published(self):
        """Читает фильтр издания: слова «изданные после» и число.

        Args:
            Нет.

        Returns:
            Составляющая издания.
        """
        self.eat("IZDANNYE")
        self.eat("POSLE")
        number = self.eat("NUMBER")
        return Node("издание", value=f"после {number.text}")


def parse(text):
    """Строит дерево разбора для одной фразы.

    Args:
        text: Текст запроса.

    Returns:
        Корень дерева разбора.
    """
    return Parser(tokenize(text)).parse_query()


def format_tree(node):
    """Собирает текст дерева: каждая составляющая на своей строке.

    Args:
        node: Корень дерева или любая его составляющая.

    Returns:
        Текст дерева, готовый к выводу.
    """
    lines = []

    def walk(current, prefix, is_last, is_root):
        """Дописывает одну составляющую и обходит вложенные в неё части.

        Args:
            current: Текущая составляющая.
            prefix: Отступ слева от ветки.
            is_last: Признак последней ветки среди соседних.
            is_root: Признак корня дерева.

        Returns:
            Ничего.
        """
        if current.value is None:
            label = current.name
        else:
            label = f"{current.name}: {current.value}"
        if is_root:
            lines.append(label)
            child_prefix = ""
        else:
            # последняя ветка закрывается углом, остальные остаются открытыми
            branch = "└── " if is_last else "├── "
            lines.append(prefix + branch + label)
            child_prefix = prefix + ("    " if is_last else "│   ")
        for number, child in enumerate(current.children):
            last = number == len(current.children) - 1
            walk(child, child_prefix, last, False)

    walk(node, "", True, True)
    return "\n".join(lines)
