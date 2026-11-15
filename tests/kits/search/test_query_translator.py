from scholar_search.query_translator import (
    BooleanQueryTranslator,
    QueryField,
    QueryParser,
)


def test_query_parser_basic():
    parser = QueryParser()
    tokens = parser.parse("machine learning")
    assert len(tokens) == 2
    assert tokens[0].value == "machine"
    assert tokens[1].value == "learning"


def test_query_parser_boolean():
    parser = QueryParser()
    tokens = parser.parse("machine AND learning OR deep")
    assert len(tokens) == 5
    assert tokens[1].is_operator and tokens[1].value == "AND"
    assert tokens[3].is_operator and tokens[3].value == "OR"


def test_query_parser_phrases():
    parser = QueryParser()
    tokens = parser.parse('"machine learning"')
    assert len(tokens) == 1
    assert tokens[0].value == "machine learning"
    assert tokens[0].is_phrase


def test_query_parser_fields():
    parser = QueryParser()
    tokens = parser.parse('title:"machine learning" AND author:smith')

    assert tokens[0].field == QueryField.TITLE
    assert tokens[0].value == "machine learning"
    assert tokens[0].is_phrase

    assert tokens[2].field == QueryField.AUTHOR
    assert tokens[2].value == "smith"


def test_boolean_translator():
    from scholar_search.models import Query

    translator = BooleanQueryTranslator(
        field_map={QueryField.TITLE: "ti"}, operator_map={"AND": "+"}
    )

    q = Query(text='title:"machine learning" AND deep')
    result = translator.translate(q)
    assert result == 'ti:"machine learning" + deep'


def test_adjacent_terms_unchanged_without_implicit_operator():
    from scholar_search.models import Query

    translator = BooleanQueryTranslator(field_map={QueryField.ANY: "all"})
    assert translator.translate(Query(text="a b")) == "all:a all:b"
    assert translator.translate(Query(text='(a OR b) "c d" e')) == '( all:a OR all:b ) all:"c d" all:e'


def test_implicit_operator_joins_adjacent_operands_only():
    from scholar_search.models import Query

    translator = BooleanQueryTranslator(
        field_map={QueryField.ANY: "all"},
        operator_map={"AND": "AND", "OR": "OR", "NOT": "ANDNOT"},
        implicit_operator="AND",
    )
    assert translator.translate(Query(text="a b")) == "all:a AND all:b"
    assert translator.translate(Query(text='(a OR b) "c d" (e)')) == (
        '( all:a OR all:b ) AND all:"c d" AND ( all:e )'
    )
    assert translator.translate(Query(text="a NOT b")) == "all:a ANDNOT all:b"
    assert translator.translate(Query(text="a OR b")) == "all:a OR all:b"
