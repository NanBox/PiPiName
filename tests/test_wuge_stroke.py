from pipiname.stroke import get_stroke_number
from pipiname.wuge import check_wuge


def test_check_wuge_zhou_jielun_matches_readme_sample():
    report = check_wuge("周杰伦")

    assert report.complex_name == "周杰倫"
    assert report.strokes == (8, 8, 10)
    assert report.tian.value == 9
    assert report.ren.value == 16
    assert report.ren.kind == "大吉"
    assert report.di.value == 18
    assert report.di.kind == "大吉"
    assert report.zong.value == 26
    assert report.zong.kind == "凶"
    assert report.wai.value == 11
    assert report.wai.kind == "大吉"
    assert report.sancai == "水土金"
    assert report.sancai_kind == "中吉"


def test_radical_stroke_rules_cover_common_cases():
    assert get_stroke_number("清") == 12
    assert get_stroke_number("英") == 11
    assert get_stroke_number("達") == 16
    assert get_stroke_number("陳") == 16
    assert get_stroke_number("珀") == 10
    assert get_stroke_number("祥") == 11
    assert get_stroke_number("裕") == 13
    assert get_stroke_number("猛") == 12
    assert get_stroke_number("三") == 3
    assert get_stroke_number("十") == 10
