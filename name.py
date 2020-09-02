from opencc import OpenCC

from stroke_number import get_stroke_number


class Name:
    __slots__ = "first_name", "stroke_number1", "stroke_number2", "count", "source", "gender"

    def __init__(self, first_name, source, gender):
        self.stroke_number1 = get_stroke_number(first_name[0])
        self.stroke_number2 = get_stroke_number(first_name[1])
        self.count = len(first_name)
        self.source = source.replace(first_name[0], "「" + first_name[0] + "」") \
            .replace(first_name[1], "「" + first_name[1] + "」")
        self.gender = gender
        # 转回简体
        cc = OpenCC('t2s')
        self.first_name = cc.convert(first_name)

    def __eq__(self, other):
        return self.first_name == other.first_name

    def __ne__(self, other):
        return not self.first_name == other.first_name

    def __lt__(self, other):
        return self.first_name < other.first_name

    def __str__(self):
        return self.first_name + "\t" + \
               str(self.gender) + "\t" + \
               self.first_name[0] + "\t" + \
               self.first_name[1] + "\t" + \
               str(self.stroke_number1) + "\t" + str(self.stroke_number2) + "\t" + \
               self.source

    def __hash__(self):
        return hash(self.first_name)
