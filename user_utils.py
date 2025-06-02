# user_utils.py

import random

def generate_5_digit():
    """
    5桁のランダムな数字を文字列で返す。
    10000～99999 の範囲で乱数を作っているので
    先頭に0が来ることはありません。
    """
    return str(random.randint(10000, 99999))


if __name__ == "__main__":
    # テスト実行用。5回ほどサンプルを出力してみる
    for _ in range(5):
        print(generate_5_digit())