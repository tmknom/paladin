"""ロギングデコレータ"""

import functools
import logging
from collections.abc import Callable
from typing import Any, cast

# データ要約表示の閾値
_LIST_TRUNCATE_THRESHOLD = 10  # リスト/タプルの要素数閾値
_DICT_TRUNCATE_THRESHOLD = 10  # dictのキー数閾値
_STR_TRUNCATE_LENGTH = 100  # 文字列の文字数閾値


def _format_value(value: Any) -> str:
    """ログ出力用に値を整形

    大量データを要約表示し、デバッグに必要な最小限の情報を残します。

    Args:
        value: 整形対象の値

    Returns:
        整形済みの文字列
    """
    # リスト・タプル: 要素数が閾値以上なら最初の1要素 + 総数
    if isinstance(value, list | tuple):
        typed_value = cast("list[Any] | tuple[Any, ...]", value)
        if len(typed_value) >= _LIST_TRUNCATE_THRESHOLD:
            first_item = repr(typed_value[0]) if typed_value else ""
            return (
                f"[{first_item}, ... ({len(typed_value)} items)]"
                if typed_value
                else "[... (0 items)]"
            )
        return repr(typed_value)

    # dict: キー数が閾値以上なら最初の1キー・値ペア + 総数
    if isinstance(value, dict):
        typed_dict = cast("dict[Any, Any]", value)
        if len(typed_dict) >= _DICT_TRUNCATE_THRESHOLD:
            if typed_dict:
                first_key: Any = next(iter(typed_dict))
                first_value = repr(typed_dict[first_key])
                return f"{{{first_key!r}: {first_value}, ... ({len(typed_dict)} keys)}}"
            return "{... (0 keys)}"
        return repr(typed_dict)

    # 文字列: 長さが閾値以上なら最初の100文字 + 総数
    if isinstance(value, str):
        typed_str: str = value
        if len(typed_str) >= _STR_TRUNCATE_LENGTH:
            return f'"{typed_str[:_STR_TRUNCATE_LENGTH]}... ({len(typed_str)} chars)"'
        return repr(typed_str)

    # その他: そのまま
    return repr(value)


def log[F: Callable[..., Any]](func: F) -> F:
    """関数/メソッドの呼び出しと戻り値をログ出力するデコレータ

    - メソッド開始時: INFO レベルで関数名と引数をログ出力
    - メソッド終了時: INFO レベルで戻り値をログ出力
    - 例外発生時: ログ出力せず、例外をそのまま再送出（ErrorHandlerが担当）

    Usage:
        @log
        def my_function(x: int, y: int) -> int:
            return x + y

    Args:
        func: デコレート対象の関数/メソッド

    Returns:
        ラップされた関数/メソッド
    """
    logger = logging.getLogger(func.__module__)

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # クラス名の取得とselfの除外
        if args and hasattr(args[0].__class__, func.__name__):
            # メソッドの場合、クラス名を付加してselfを除外
            class_name = args[0].__class__.__name__
            qualifier = f"{class_name}.{func.__name__}"
            log_args = args[1:]
        else:
            # 関数の場合、すべての引数を含める
            qualifier = func.__name__
            log_args = args

        # 引数をfunc(arg1, arg2, key=val)形式に整形
        parts = [_format_value(arg) for arg in log_args]
        parts += [f"{k}={_format_value(v)}" for k, v in kwargs.items()]
        args_str = ", ".join(parts)
        logger.info("%s(%s)", qualifier, args_str, stacklevel=2)

        result = func(*args, **kwargs)

        # 戻り値を整形
        formatted_result = _format_value(result)
        logger.info("%s returned: %s", qualifier, formatted_result, stacklevel=2)

        return result

    return cast(F, wrapper)
