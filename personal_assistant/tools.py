import ast
import operator
import re

_OPERATIONS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _calculate_node(node):
    # Numbers such as 10, 25.5
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value

    # Operations such as addition, multiplication and division
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATIONS:
        left = _calculate_node(node.left)
        right = _calculate_node(node.right)

        # Prevent extremely large exponent calculations
        if isinstance(node.op, ast.Pow) and abs(right) > 100:
            raise ValueError("Exponent is too large")

        return _OPERATIONS[type(node.op)](left, right)

    # Negative and positive numbers
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATIONS:
        return _OPERATIONS[type(node.op)](_calculate_node(node.operand))

    raise ValueError("Only basic arithmetic expressions are allowed")


def calculator(expression: str) -> dict:
    """Calculate a mathematical expression such as '25000 * 18 / 100'.

    Args:
        expression: Arithmetic expression using +, -, *, /, %, **.

    Returns:
        A dictionary containing the calculation result.
    """
    try:
        if len(expression) > 200:
            raise ValueError("Expression is too long")

        tree = ast.parse(expression, mode="eval")
        result = _calculate_node(tree.body)

        if isinstance(result, (int, float)) and abs(result) > 1e100:
            raise ValueError("Result is too large")

        return {"status": "success", "expression": expression, "result": result}

    except (ValueError, SyntaxError, ZeroDivisionError, OverflowError) as e:
        return {"status": "error", "message": str(e)}


def text_analyzer(text: str) -> dict:
    """Count characters, words and sentences in the supplied text.

    Args:
        text: The exact paragraph or text to analyze.

    Returns:
        Character count, word count and sentence count.
    """

    # Counts characters, including spaces and punctuation
    character_count = len(text)

    # Counts words separated by whitespace
    word_count = len(text.split())

    # Counts groups of sentence-ending punctuation
    sentences = re.findall(r"[^.!?]+[.!?]+|[^.!?]+$", text.strip())
    sentence_count = sum(1 for s in sentences if s.strip())

    return {
        "status": "success",
        "characters": character_count,
        "words": word_count,
        "sentences": sentence_count,
    }
