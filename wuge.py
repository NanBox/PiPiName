import opencc

from stroke_number import get_stroke_number

stroke_goods = [1, 3, 5, 6, 7, 8, 11, 13, 15, 16, 17, 18, 21, 23, 24, 25, 29, 31, 32, 33, 35, 37, 39, 41, 45, 47, 48,
                52, 57, 61, 63, 65, 67, 68, 81]

stroke_generals = [27, 38, 42, 55, 58, 71, 72, 73, 77, 78]

stroke_bads = [2, 4, 9, 10, 12, 14, 19, 20, 22, 26, 28, 30, 34, 36, 40, 43, 44, 46, 49, 50, 51, 53, 54, 56, 59, 60, 62,
               64, 66, 69, 70, 74, 75, 76, 79, 80]

stroke_list = list()


def get_stroke_list(last_name, allow_general):
    print(">>计算笔画组合...")
    # 姓氏转繁体
    converter = opencc.OpenCC('s2t')
    last_name = converter.convert(last_name)
    n = get_stroke_number(last_name)
    for i in range(1, 81):
        for j in range(1, 81):
            # 天格
            tian = n + 1
            # 人格
            ren = n + i
            # 地格
            di = i + j
            # 总格
            zong = n + i + j
            # 外格
            wai = zong - ren + 1

            if ren in stroke_goods and di in stroke_goods and zong in stroke_goods and wai in stroke_goods:
                if check_sancai_good([tian, ren, di], allow_general):
                    stroke_list.append([i, j])
            elif allow_general and \
                    (ren in stroke_goods or ren in stroke_generals) and \
                    (di in stroke_goods or di in stroke_generals) and \
                    (zong in stroke_goods or zong in stroke_generals) and \
                    (wai in stroke_goods or wai in stroke_generals):
                if check_sancai_good([tian, ren, di], allow_general):
                    stroke_list.append([i, j])
    print(">>" + str(stroke_list))
    return stroke_list


# 大吉
wuxing_goods = ["木木木", "木木火", "木木土", "木火木", "木火土", "木水木", "木水金", "木水水", "火木木", "火木火",
                "火木土", "火火木", "火火土", "火土火", "火土土", "火土金", "土火木", "土火火", "土火土", "土土火",
                "土土土", "土土金", "土金土", "土金金", "土金水", "金土火", "金土土", "金土金", "金金土", "金水木",
                "金水金", "水木木", "水木火", "水木土", "水木水", "水金土", "水金水", "水水木", "水水金"]

# 中吉
wuxing_generals = ["木火火", "木土火", "火木水", "火火火", "土木木", "土木火", "土土木", "金土木", "金金金", "金金水",
                   "金水水", "水火木", "水土火", "水土土", "水土金", "水金金", "水水水"]

# 凶
wuxing_bads = ["木木金", "木火金", "木火水", "木土木", "木土水", "木金木", "木金火", "木金土", "木金金", "木金水",
               "木水火", "木水土", "火木金", "火火金", "火火水", "火金木", "火金火", "火金金", "火金水", "火水木",
               "火水火", "火水土", "火水金", "火水水", "土木土", "土木金", "土木水", "土火水", "土土水", "土金木",
               "土金火", "土水木", "土水火", "土水土", "土水水", "金木木", "金木火", "金木土", "金木金", "金木水",
               "金火木", "金火金", "金火水", "金金木", "金金木", "金水火", "水木金", "水火火", "水火土", "水火金",
               "水火水", "水土木", "水水土", "水金木", "水金火", "水水火", "水水土", "木木水", "木土金", "火土木",
               "火土水", "土火金", "金土水", "火金土", "土水金", "金火火", "金火土", "木土土", "金水土"]


# 检查三才配置吉
def check_sancai_good(counts, allow_general):
    config = get_sancai_config(counts)
    if config in wuxing_goods:
        return True
    elif allow_general and config in wuxing_generals:
        return True
    return False


# 获取对应五行
def get_wuxing(count):
    count = count % 10
    if count == 1 or count == 2:
        return "木"
    elif count == 3 or count == 4:
        return "火"
    elif count == 5 or count == 6:
        return "土"
    elif count == 7 or count == 8:
        return "金"
    elif count == 9 or count == 0:
        return "水"


# 查看三才五格配置
def check_wuge_config(name):
    if len(name) != 3:
        return
    # 姓名转繁体
    converter = opencc.OpenCC('s2t')
    complex_name = converter.convert(name)
    xing = get_stroke_number(complex_name[0])
    ming1 = get_stroke_number(complex_name[1])
    ming2 = get_stroke_number(complex_name[2])
    # 天格
    tian = xing + 1
    # 人格
    ren = xing + ming1
    # 地格
    di = ming1 + ming2
    # 总格
    zong = xing + ming1 + ming2
    # 外格
    wai = zong - ren + 1
    # 三才配置
    sancai_config = get_sancai_config([tian, ren, di])
    # 输出结果
    print("\n")
    print(name + "\n")
    print(complex_name + " " + str(xing) + " " + str(ming1) + " " + str(ming2) + "\n")
    print("天格\t" + str(tian))
    print("人格\t" + str(ren) + "\t" + get_stroke_type(ren))
    print("地格\t" + str(di) + "\t" + get_stroke_type(di))
    print("总格\t" + str(zong) + "\t" + get_stroke_type(zong))
    print("外格\t" + str(wai) + "\t" + get_stroke_type(wai))
    print("\n三才\t" + sancai_config + "\t" + get_sancai_type(sancai_config) + "\n")


# 获取三才配置
def get_sancai_config(counts):
    config = ""
    for count in counts:
        config += get_wuxing(count)
    return config


def get_stroke_type(stroke):
    if stroke in stroke_goods:
        return "大吉"
    elif stroke in stroke_generals:
        return "中吉"
    elif stroke in stroke_bads:
        return "凶"
    else:
        return ""


def get_sancai_type(config):
    if config in wuxing_goods:
        return "大吉"
    elif config in wuxing_generals:
        return "中吉"
    elif config in wuxing_bads:
        return "凶"
    else:
        return ""
