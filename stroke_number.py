import re

stroke_dic = dict()
with open('data/stoke.dat', encoding='utf-8') as f:
    data = f.readlines()
    for string in data:
        temp = string.split("|")
        temp[2] = temp[2].replace("\n", "")
        stroke_dic[temp[1]] = int(temp[2])

split_dic = dict()
with open('data/chaizi-ft.dat', encoding='utf-8') as f:
    data = f.readlines()
    for string in data:
        temp = re.split("\s", string)
        if len(temp) < 2:
            continue
        split_list = list()
        for index in range(1, len(temp) - 1):
            split_list.append(temp[index])
        split_dic[temp[0]] = split_list


def get_stroke_number(word):
    total = 0
    for i in word:
        if "一" in i:
            total += 1
        elif "二" in i:
            total += 2
        elif "三" in i:
            total += 3
        elif "四" in i:
            total += 4
        elif "五" in i:
            total += 5
        elif "六" in i:
            total += 6
        elif "七" in i:
            total += 7
        elif "八" in i:
            total += 8
        elif "九" in i:
            total += 9
        elif "十" in i:
            total += 10
        else:
            total += stroke_dic[i]
    return get_final_number(word, total)


# 检查特殊部首笔画
def get_final_number(word, number):
    for i in word:
        if i in split_dic:
            splits = split_dic[i]
            if "氵" in splits:
                # 水
                number += 1
            if "扌" in splits:
                # 手
                number += 1
            if splits[0] == "月":
                # 肉
                number += 2
            if "艹" in splits:
                # 艸
                number += 3
            if "辶" in splits:
                # 辵
                number += 4
            if splits[0] == "阜":
                # 左阝 阜
                number += 6
            if "邑" in splits and "阝" in splits:
                # 右阝 邑
                number += 5
            if splits[0] == "玉":
                # 王字旁 玉
                number += 1
            if splits[0] == "示":
                # 礻 示
                number += 1
            if splits[0] == "衣":
                # 衤 衣
                number += 1
            if splits[0] == "衣":
                # 犭 犬
                number += 1
            if splits[0] == "心":
                # 忄 心
                number += 1
    return number
