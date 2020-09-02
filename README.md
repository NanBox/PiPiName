# get_chinese_name
中文起名工具，支持古诗文取名。内置诗经，论语，唐诗，宋词，楚辞，周易。支持自定义文章取词。
# 简介
只关注名字好不好听，不关注八字吉凶。
# 使用方法
**1.安装所有第三方库**
```
pip install opencc-python-reimplemented
```
**2.调整main.py中的参数**
```
# 长辈姓名--删掉所有读音相同的字--例：加入“伟”，则结果中不会出现任何读音为we的字（为伟位微卫...）
banned_list = lazy_pinyin("可悦思平笑华世永念沁建宏中人春山雨国清溪瑞峰")

# 名字开头字母--删掉所有以此字母开头的字--例：加入“w”，则结果中不会出现任何拼音以w开头的字（卫瓦望卧...）
bad_init = list("eqrsxy")

# 不想要的名字--删掉所有相同的字--例：加入“贵”，则结果中不会出现“贵”字
bad_words = list("富贵民国军卫义二三四"
                 "介少大毛伟帅攻立生田"
                 "水火金木土才花凤龙春"
                 "艳芳淑杰俊志强昌银婷"
                 "丽芬发梅蛋铁铜娜宝春"
                 "夏秋冬武力天地圣神佛"
                 "老乾坤云")
                 
# 笔画数--名字的笔画总数的范围--例：王伟，名字笔画总数为6（不计姓氏）
stroke_number = [0, 200]

# 字数--名字的字数--例：王伟，字数为1
character_number = 2

# 姓--不会影响名字的生成，仅仅影响输出
last_name = "王"

# 允许叠字--例：欢欢，西西
replicate = False

# 选择词库
# 0: "默认", 1: "诗经", 2: "楚辞", 3: "论语",
# 4: "周易", 5: "唐诗", 6: "宋诗", 7: "宋词"
# 8: 自定义
name_source = 1

# 是否筛选名字--仅输出默认库中存在的名字，可以删除明显不合适的名字
name_validate = True

# 是否筛选性别--仅输出与默认库中对应名字性别相同的名字--仅当开启名字筛选时有效
filter_gender = True

# 性别--男/女--仅当开启名字筛选时有效
gender = "女"
```

**3.运行后结果会输出到“names.txt”文件中**
```
例：
姓名    性别  名字笔画数               取词来源
王琼瑶   女	    26	       投我以木桃，报之以琼瑶。匪报也，永以为好也！
王琼莹   女	    22	       俟我于庭乎而，充耳以青乎而，尚之以琼莹乎而。
```
# 数据来源
* [chinese-poetry](https://github.com/chinese-poetry/chinese-poetry)
* [chineseStroke](https://github.com/WTree/chineseStroke)
* [Chinese-Names-Corpus](https://github.com/wainshine/Chinese-Names-Corpus)
# 第三方库
* [OpenCC](https://github.com/BYVoid/OpenCC)
* json
* re
