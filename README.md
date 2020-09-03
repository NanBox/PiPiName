# PiPiName

根据三才五格，从诗经、楚辞、论语、周易、唐诗、宋词给宝宝取名。

# 使用方法

## 1. 安装第三方库

安装繁简体转换库 OpenCC：

```
pip install opencc
```

## 2. 配置参数

打开 config.py，进行参数配置：

```python
# 选择词库
# 0: "默认", 1: "诗经", 2: "楚辞", 3: "论语",
# 4: "周易", 5: "唐诗", 6: "宋诗", 7: "宋词"
name_source = 0

# 姓，仅支持单姓
last_name = "张"

# 不想要的字，结果中不会出现这些字
dislike_words = list("")

# 最小笔画数
min_stroke_count = 3

# 最大笔画数
max_stroke_count = 25

# 允许使用中吉，开启后将生成包含中吉配置的名字，生成的名字会更多
allow_general = False

# 是否筛选名字，仅输出名字库中存在的名字，可以过滤明显不合适的名字
name_validate = True

# 是否筛选性别，男/女，空则不筛选，仅当开启名字筛选时有效
gender = ""

##########################################################################

# 填入姓名，查看三才五格配置，仅支持单姓复名
# 如果要起名，请保持该值为空
check_name = ""

# 是否显示名字来源
check_name_resource = True
```

## 3. 运行查看结果

运行 main.py 后，结果会生成在 name.text 文件，比如：

```
张哲维    男  哲  维  10 14 「哲」人之愚，亦「維」斯戾。無競「維」人，四方其訓之。有覺德行，四國順之。
张家宁    男  家  宁  10 14 有飶其香。邦「家」之光。有椒其馨，胡考之「寧」。匪且有且，匪今斯今，振古如茲。
张怀元    男  怀  元  20 4  翩彼飛鴞，集於泮林。食我桑黮，「懷」我好音。憬彼淮夷，來獻其琛。「元」龜象齒，大賂南金。
张恒寿    男  恒  寿  10 14 如月之「恆」，如日之升。如南山之「壽」，不騫不崩。如松柏之茂，無不爾或承。
```

可以将结果粘贴在 Excel 表格，根据字或笔画进行筛选。

如果是查看名字配置和来源，结果会直接打印出来，比如：

```
周杰伦

周杰倫 8 8 10

天格	9
人格	16	大吉
地格	18	大吉
总格	26	凶
外格	11	大吉

三才	水土金	中吉

唐诗 自蜀奉册命往朔方途中呈韦左相文部房尚书门下崔侍郎 贾至
谁谓三「杰」才，功业独殊「伦」。

宋诗 答赵温甫见谢茶瓯韵 彭汝砺
朅来东江欲学古，喜听英「杰」参吾「伦」。
```

# 感谢

- [OpenCC](https://github.com/BYVoid/OpenCC)
- [chinese-poetry](https://github.com/chinese-poetry/chinese-poetry)
- [chineseStroke](https://github.com/WTree/chineseStroke)
- [Chinese-Names-Corpus]()
- [hanzi_chaizi](https://github.com/howl-anderson/hanzi_chaizi)
