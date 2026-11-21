#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
保研星途 - 推免招生信息筛选系统同步脚本
读取 baoyan_data/raw_*.csv，自动标签、解析，生成 baoyan_all.json 和 baoyan_filter.html
"""

import csv
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# ============================================================
# 1. 配置文件
# ============================================================

# 985 高校列表（含分校/校区）
SCHOOLS_985 = {
    "北京大学", "清华大学", "中国人民大学", "北京航空航天大学", "北京理工大学",
    "中国农业大学", "北京师范大学", "中央民族大学", "南开大学", "天津大学",
    "大连理工大学", "东北大学", "吉林大学", "哈尔滨工业大学", "复旦大学",
    "同济大学", "上海交通大学", "华东师范大学", "南京大学", "东南大学",
    "浙江大学", "中国科学技术大学", "厦门大学", "山东大学", "中国海洋大学",
    "武汉大学", "华中科技大学", "湖南大学", "中南大学", "中山大学",
    "华南理工大学", "四川大学", "重庆大学", "电子科技大学", "西安交通大学",
    "西北工业大学", "西北农林科技大学", "兰州大学", "国防科技大学",
    "北京协和医学院",  # 虽然不是985但属于顶尖
    "哈尔滨工业大学（深圳）", "哈尔滨工业大学(深圳)",
}

# 211 高校列表（不含985）
SCHOOLS_211 = {
    "北京交通大学", "北京工业大学", "北京科技大学", "北京化工大学", "北京邮电大学",
    "北京林业大学", "北京中医药大学", "北京外国语大学", "中国传媒大学",
    "中央财经大学", "对外经济贸易大学", "中国政法大学", "华北电力大学",
    "北京体育大学", "中国地质大学", "中国矿业大学", "中国石油大学",
    "上海财经大学", "上海外国语大学", "上海大学", "华东理工大学", "东华大学",
    "天津医科大学", "河北工业大学", "太原理工大学", "内蒙古大学",
    "辽宁大学", "大连海事大学", "延边大学", "东北师范大学", "哈尔滨工程大学",
    "东北农业大学", "东北林业大学", "苏州大学", "南京航空航天大学",
    "南京理工大学", "中国药科大学", "河海大学", "江南大学", "南京农业大学",
    "南京师范大学", "安徽大学", "合肥工业大学", "福州大学", "南昌大学",
    "郑州大学", "中国地质大学（武汉）", "武汉理工大学", "华中农业大学",
    "华中师范大学", "中南财经政法大学", "湖南师范大学", "暨南大学",
    "华南师范大学", "广西大学", "海南大学", "西南交通大学", "四川农业大学",
    "西南大学", "西南财经大学", "贵州大学", "云南大学", "西藏大学",
    "西北大学", "西安电子科技大学", "长安大学", "陕西师范大学", "青海大学",
    "宁夏大学", "新疆大学", "石河子大学", "第二军医大学", "第四军医大学",
    "中国地质大学（北京）", "中国矿业大学（北京）", "中国石油大学（北京）",
    "中国石油大学（华东）", "华北电力大学（保定）",
}

# 科研院所
RESEARCH_INSTITUTES = {
    "中国科学院", "中国工程院", "中国社科院", "中国社会科学院",
    "中国农业科学院", "中国医学科学院", "中国林业科学研究院",
    "中国地质科学院", "中国环境科学研究院", "中国气象科学研究院",
    "中国水利水电科学研究院", "中国电力科学研究院",
    "自然资源部", "中国航天", "中国兵器", "中国电子科技",
    "中国船舶", "国家海洋局", "中国地震局",
    "中国科学技术信息研究所", "中国艺术研究院", "故宫博物院",
    "军事科学院", "国防大学", "国防科技大学",
    "怀柔国家实验室", "启元实验室", "上海人工智能实验室",
    "崖州湾国家实验室", "呼吸疾病全国重点实验室",
    "深圳医学科学院", "粤港澳大湾区",
}

# 军校
MILITARY_SCHOOLS = {
    "国防科技大学", "海军工程大学", "空军工程大学", "陆军工程大学",
    "火箭军工程大学", "航天工程大学", "信息工程大学", "武警工程大学",
    "海军军医大学", "陆军军医大学", "空军军医大学",
}

# 港澳台/境外
HK_MACAO_TAIWAN = {
    "香港大学", "香港中文大学", "香港科技大学", "香港城市大学",
    "香港理工大学", "香港浸会大学", "香港岭南大学", "香港教育大学",
    "澳门大学", "澳門大學", "澳门科技大学", "澳门城市大学",
}

# 双一流高校（第二轮，部分）
DOUBLE_FIRST_CLASS = {
    "北京大学", "清华大学", "中国人民大学", "北京航空航天大学", "北京理工大学",
    "中国农业大学", "北京师范大学", "中央民族大学", "南开大学", "天津大学",
    "大连理工大学", "东北大学", "吉林大学", "哈尔滨工业大学", "复旦大学",
    "同济大学", "上海交通大学", "华东师范大学", "南京大学", "东南大学",
    "浙江大学", "中国科学技术大学", "厦门大学", "山东大学", "中国海洋大学",
    "武汉大学", "华中科技大学", "湖南大学", "中南大学", "中山大学",
    "华南理工大学", "四川大学", "重庆大学", "电子科技大学", "西安交通大学",
    "西北工业大学", "西北农林科技大学", "兰州大学",
    "北京交通大学", "北京工业大学", "北京科技大学", "北京化工大学", "北京邮电大学",
    "北京林业大学", "北京协和医学院", "北京中医药大学", "北京外国语大学",
    "中国传媒大学", "中央财经大学", "对外经济贸易大学", "中国政法大学",
    "华北电力大学", "中国地质大学", "中国矿业大学", "中国石油大学",
    "上海财经大学", "上海外国语大学", "上海大学", "华东理工大学",
    "天津医科大学", "河北工业大学", "太原理工大学",
    "南京航空航天大学", "南京理工大学", "中国药科大学", "河海大学",
    "南京农业大学", "南京师范大学", "苏州大学",
    "安徽大学", "合肥工业大学", "福州大学", "南昌大学",
    "郑州大学", "武汉理工大学", "华中农业大学", "华中师范大学",
    "中南财经政法大学", "暨南大学", "华南师范大学",
    "西南交通大学", "四川农业大学", "西南大学", "西南财经大学",
    "西安电子科技大学", "长安大学", "西北大学", "陕西师范大学",
    "南方科技大学", "上海科技大学", "中国科学院大学", "中国社会科学院大学",
    "南京医科大学", "湘潭大学", "山西大学", "华南农业大学",
    "广州医科大学", "南方医科大学",
}

# 城市映射
CITY_MAP = {
    "北京大学": "北京", "清华大学": "北京", "中国人民大学": "北京",
    "北京航空航天大学": "北京", "北京理工大学": "北京", "中国农业大学": "北京",
    "北京师范大学": "北京", "中央民族大学": "北京", "北京交通大学": "北京",
    "北京工业大学": "北京", "北京科技大学": "北京", "北京化工大学": "北京",
    "北京邮电大学": "北京", "北京林业大学": "北京", "北京中医药大学": "北京",
    "北京外国语大学": "北京", "中国传媒大学": "北京", "中央财经大学": "北京",
    "对外经济贸易大学": "北京", "中国政法大学": "北京", "华北电力大学": "北京",
    "北京体育大学": "北京", "北京协和医学院": "北京",
    "中国科学院大学": "北京", "中国科学院": "北京", "中国社会科学院大学": "北京",
    "南开大学": "天津", "天津大学": "天津", "天津医科大学": "天津",
    "河北工业大学": "天津",
    "大连理工大学": "大连", "东北大学": "沈阳", "大连海事大学": "大连",
    "辽宁大学": "沈阳", "东北财经大学": "大连",
    "吉林大学": "长春", "东北师范大学": "长春", "延边大学": "延吉",
    "哈尔滨工业大学": "哈尔滨", "哈尔滨工程大学": "哈尔滨",
    "东北农业大学": "哈尔滨", "东北林业大学": "哈尔滨",
    "复旦大学": "上海", "同济大学": "上海", "上海交通大学": "上海",
    "华东师范大学": "上海", "上海财经大学": "上海", "上海外国语大学": "上海",
    "上海大学": "上海", "华东理工大学": "上海", "东华大学": "上海",
    "上海科技大学": "上海", "上海创智学院": "上海",
    "南京大学": "南京", "东南大学": "南京", "南京航空航天大学": "南京",
    "南京理工大学": "南京", "河海大学": "南京", "南京农业大学": "南京",
    "南京师范大学": "南京", "中国药科大学": "南京", "苏州大学": "苏州",
    "江南大学": "无锡", "中国矿业大学": "徐州",
    "浙江大学": "杭州", "杭州电子科技大学": "杭州", "浙江工业大学": "杭州",
    "中国美术学院": "杭州", "西湖大学": "杭州",
    "中国科学技术大学": "合肥", "合肥工业大学": "合肥", "安徽大学": "合肥",
    "厦门大学": "厦门", "福州大学": "福州",
    "山东大学": "济南", "中国海洋大学": "青岛", "中国石油大学（华东）": "青岛",
    "武汉大学": "武汉", "华中科技大学": "武汉", "武汉理工大学": "武汉",
    "华中农业大学": "武汉", "华中师范大学": "武汉", "中南财经政法大学": "武汉",
    "中国地质大学（武汉）": "武汉",
    "湖南大学": "长沙", "中南大学": "长沙", "湖南师范大学": "长沙",
    "中山大学": "广州", "华南理工大学": "广州", "暨南大学": "广州",
    "华南师范大学": "广州", "南方科技大学": "深圳", "深圳大学": "深圳",
    "香港中文大学（深圳）": "深圳", "南方医科大学": "广州",
    "广州医科大学": "广州", "华南农业大学": "广州",
    "四川大学": "成都", "电子科技大学": "成都", "西南交通大学": "成都",
    "西南财经大学": "成都", "四川农业大学": "雅安",
    "重庆大学": "重庆", "西南大学": "重庆",
    "西安交通大学": "西安", "西北工业大学": "西安", "西安电子科技大学": "西安",
    "长安大学": "西安", "西北大学": "西安", "陕西师范大学": "西安",
    "兰州大学": "兰州",
    "郑州大学": "郑州", "河南大学": "开封",
    "云南大学": "昆明",
    "贵州大学": "贵阳",
    "广西大学": "南宁",
    "海南大学": "海口",
    "内蒙古大学": "呼和浩特",
    "新疆大学": "乌鲁木齐", "石河子大学": "石河子",
    "宁夏大学": "银川", "青海大学": "西宁", "西藏大学": "拉萨",
    "南昌大学": "南昌",
    "山西大学": "太原", "太原理工大学": "太原",
    "香港大学": "香港", "香港中文大学": "香港", "香港科技大学": "香港",
    "香港城市大学": "香港", "香港理工大学": "香港", "香港浸会大学": "香港",
    "香港岭南大学": "香港", "香港教育大学": "香港",
    "香港中文大学（深圳）": "深圳",
    "澳门大学": "澳门", "澳門大學": "澳门", "澳门科技大学": "澳门",
    "湘潭大学": "湘潭",
    "北京中关村学院": "北京", "启元实验室": "北京",
    "北京脑科学与类脑研究所": "北京",
    "上海人工智能实验室": "上海", "深圳医学科学院": "深圳",
    "粤港澳大湾区（广东）量子科学中心": "深圳",
    "崖州湾国家实验室": "三亚", "怀柔国家实验室": "北京",
    "自然资源部第一海洋研究所": "青岛",
    "中国医学科学院": "北京",
    "海军工程大学": "武汉", "空军工程大学": "西安",
    "北京协和医学院": "北京",
}

# 专业类别映射 (从学院名和通知名称推断)
MAJOR_CATEGORIES = {
    # 经管法
    "经济": "经管法", "金融": "经管法", "管理": "经管法", "商": "经管法",
    "会计": "经管法", "工商": "经管法", "MBA": "经管法", "EMBA": "经管法",
    "国贸": "经管法", "财政": "经管法", "税务": "经管法", "保险": "经管法",
    "统计": "经管法", "审计": "经管法", "市场": "经管法", "人力": "经管法",
    "法学": "经管法", "法律": "经管法", "国际法": "经管法",
    "知识产权": "经管法", "政治学": "经管法",
    # 理工农医
    "数学": "理工农医", "物理": "理工农医", "化学": "理工农医",
    "生物": "理工农医", "医学": "理工农医", "药": "理工农医", "临床": "理工农医",
    "公共卫生": "理工农医", "护理": "理工农医", "口腔": "理工农医",
    "生命科学": "理工农医", "农": "理工农医", "兽医": "理工农医",
    "计算机": "理工农医", "软件": "理工农医", "人工智能": "理工农医",
    "数据科学": "理工农医", "信息": "理工农医", "电子": "理工农医",
    "通信": "理工农医", "自动化": "理工农医", "电气": "理工农医",
    "机械": "理工农医", "能源": "理工农医", "动力": "理工农医",
    "材料": "理工农医", "化工": "理工农医", "环境": "理工农医",
    "地理": "理工农医", "地质": "理工农医", "地球": "理工农医",
    "海洋": "理工农医", "大气": "理工农医", "天文": "理工农医",
    "土木": "理工农医", "建筑": "理工农医", "交通": "理工农医",
    "水利": "理工农医", "测绘": "理工农医", "矿业": "理工农医",
    "核科学": "理工农医", "航天": "理工农医", "航空": "理工农医",
    "船舶": "理工农医", "兵器": "理工农医",
    "纳米": "理工农医", "量子": "理工农医", "光学": "理工农医",
    "声学": "理工农医", "力学": "理工农医",
    "工程": "理工农医", "科学": "理工农医",
    "脑科学": "理工农医", "类脑": "理工农医",
    "碳中和": "理工农医", "可持续": "理工农医",
    # 人文社科艺术
    "哲学": "人文社科艺术", "历史": "人文社科艺术", "考古": "人文社科艺术",
    "文学": "人文社科艺术", "语言": "人文社科艺术", "外语": "人文社科艺术",
    "新闻": "人文社科艺术", "传播": "人文社科艺术", "传媒": "人文社科艺术",
    "艺术": "人文社科艺术", "美术": "人文社科艺术", "音乐": "人文社科艺术",
    "设计": "人文社科艺术", "戏剧": "人文社科艺术", "电影": "人文社科艺术",
    "教育": "人文社科艺术", "体育": "人文社科艺术",
    "社会": "人文社科艺术", "人口": "人文社科艺术", "人类学": "人文社科艺术",
    "心理": "人文社科艺术", "马克思": "人文社科艺术",
    "国际关系": "人文社科艺术", "外交": "人文社科艺术",
    "公共管理": "人文社科艺术", "图书": "人文社科艺术", "档案": "人文社科艺术",
    "人文": "人文社科艺术", "社科": "人文社科艺术",
    "文化": "人文社科艺术", "国学": "人文社科艺术",
    "汉语言": "人文社科艺术", "中文": "人文社科艺术",
    "民族": "人文社科艺术", "宗教": "人文社科艺术",
}

# 具体专业（从学院名和通知名称中提取）
SPECIFIC_MAJOR_PATTERNS = [
    (r"金融|金融学|金融工程|金融科技", "金融"),
    (r"经济|经济学|国民经济|世界经济", "经济学"),
    (r"管理|工商管理|公共管理|行政管理|企业管理|项目管理|旅游管理|酒店管理", "管理学"),
    (r"会计|审计|财务管理", "会计/审计"),
    (r"法学|法律|国际法|知识产权|诉讼法学|宪法|刑法|民商法", "法学"),
    (r"政治学|国际政治|国际关系|外交学", "政治学"),
    (r"数学|计算数学|应用数学|基础数学|概率论|运筹", "数学"),
    (r"物理|物理学|理论物理|粒子物理|凝聚态|光学", "物理学"),
    (r"化学|化学工程|应用化学|分析化学|有机化学|高分子", "化学"),
    (r"生物|生命科学|生物学|生物技术|生物信息|生物医学|生物工程|细胞|分子生物", "生物学"),
    (r"医学|临床|基础医学|预防医学|公共卫生|药学|护理|口腔|中医|中西医", "医学/药学"),
    (r"计算机|计算机科学|软件|软件工程|人工智能|AI|机器学习|深度学习|模式识别", "计算机/AI"),
    (r"数据科学|大数据|数据挖掘", "数据科学"),
    (r"电子|电子信息|电子工程|微电子|集成电路|半导体|芯片", "电子信息"),
    (r"通信|信息与通信|信号处理|网络|物联网|5G|6G", "通信/网络"),
    (r"自动化|控制科学|控制工程|机器人|智能制造", "自动化/控制"),
    (r"电气|电力|能源动力|电机|电工", "电气/能源"),
    (r"机械|机械工程|车辆工程|航空航天|飞行器|航空宇航", "机械/航空航天"),
    (r"材料|材料科学|材料工程|冶金|高分子材料", "材料科学"),
    (r"环境|环境科学|环境工程|生态|碳中和|可持续", "环境/生态"),
    (r"土木|建筑|城市规划|建筑学|风景园林|景观|城乡规划", "土木/建筑"),
    (r"交通|交通运输|轨道交通|道路|桥梁|隧道", "交通运输"),
    (r"海洋|海洋科学|船舶|水利|水产", "海洋/水利"),
    (r"地质|地球科学|地球物理|地理|遥感|测绘|GIS", "地球/地理"),
    (r"天文|空间科学|空间物理", "天文学"),
    (r"农学|农业|植保|园艺|畜牧|兽医|林学|作物", "农学/兽医"),
    (r"统计|统计学|应用统计|数理统计", "统计学"),
    (r"哲学|伦理学|逻辑学|美学|宗教学", "哲学"),
    (r"历史|历史学|考古|文物|博物馆|文化遗产", "历史/考古"),
    (r"文学|中文|汉语言|比较文学|文艺学|古典文献", "中国语言文学"),
    (r"外语|英语|日语|法语|德语|俄语|翻译|语言学|外国语言", "外国语言文学"),
    (r"新闻|传播|传媒|新媒体|广播电视|广告|出版", "新闻传播"),
    (r"艺术|美术|设计|音乐|舞蹈|戏剧|电影|影视|动画|书法|雕塑", "艺术学"),
    (r"教育|教育学|高等教育|基础教育|特殊教育|教师教育|课程", "教育学"),
    (r"体育|运动|体育学|竞技", "体育学"),
    (r"社会学|社会|人口|人类学|民俗|社工|社会保障", "社会学"),
    (r"心理|心理学|认知科学|神经科学", "心理学"),
    (r"马克思主义|思想政治教育|中共党史|科学社会主义", "马克思主义理论"),
    (r"信息资源管理|图书|档案|情报|图书馆", "信息资源管理"),
    (r"核科学|核工程|核技术|辐射", "核科学"),
    (r"力学|工程力学|流体力学|固体力学", "力学"),
    (r"纳米|纳米科学|纳米技术", "纳米科学"),
    (r"量子|量子信息|量子计算|量子物理", "量子科技"),
    (r"脑科学|脑科学|类脑|神经", "脑科学"),
    (r"兽医|动物医学", "兽医"),
    (r"信息与计算|信息科学|信息管理", "信息科学"),
]

# 招生阶段关键词
STAGE_PATTERNS = [
    (r"夏令营|Summer Camp|Mini.?营|科学营|暑期学校|暑期研习|暑期学院|开放日|招募营", "夏令营"),
    (r"预推免|预报名|预选|推免预|预报|提前批|提前招生|推荐免试", "预推免"),
    (r"正式推免|九推|推免系统|国家系统|正式报名|十推|研招网", "正式推免"),
    (r"冬令营|Winter Camp|春令营", "夏令营"),  # 冬令营春令营归入夏令营
    (r"招生简章|招生|硕士项目|博士项目|研招|申请", None),  # 通用，不特定阶段
]


# ============================================================
# 2. 数据读取和清洗
# ============================================================

def parse_csv_file(filepath, category):
    """读取单个 raw CSV，返回清洗后的记录列表"""
    records = []
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 第一行是多行公告（用引号包裹的），跳过
    # 找到真正的表头行
    lines = content.strip().split('\n')

    # 跳过第一行（公告banner，引号包裹多行内容）
    # 用 csv.reader 重新处理
    reader = csv.reader(content.splitlines())
    rows = list(reader)

    # 跳过 banner 行（第一行第一个字段包含换行符的公告文本）
    header_row = None
    data_start = 0
    for i, row in enumerate(rows):
        if len(row) >= 2:
            # 检测真正的表头
            first_cell = row[0].strip()
            if first_cell == '序号':
                header_row = row
                data_start = i + 1
                break

    if header_row is None:
        print(f"  WARNING: Could not find header in {filepath}")
        return records

    # 判断列结构
    has_college = len(header_row) >= 6 and '学院' in (header_row[2] if len(header_row) > 2 else '')

    for row in rows[data_start:]:
        if len(row) < 2:
            continue
        school = row[1].strip() if len(row) > 1 else ""
        if not school:
            continue  # 空行

        if has_college and len(header_row) >= 6:
            college = row[2].strip() if len(row) > 2 else ""
            name = row[3].strip() if len(row) > 3 else ""
            link = row[4].strip() if len(row) > 4 else ""
            ddl = row[5].strip() if len(row) > 5 else ""
        else:
            # cir38h 格式: 序号,学校,通知名称,通知链接,DDL
            college = ""
            name = row[2].strip() if len(row) > 2 else ""
            link = row[3].strip() if len(row) > 3 else ""
            ddl = row[4].strip() if len(row) > 4 else ""

        # 跳过公告行
        if '保研星途' in school or '保研er' in school:
            continue
        # 跳过看起来不像通知的行
        if not name or len(name) < 4:
            continue

        records.append({
            "school": school,
            "college": college,
            "name": name,
            "link": link,
            "ddl": ddl,
            "category": category,
        })

    return records


# ============================================================
# 3. 自动标签逻辑
# ============================================================

def tag_school_level(school):
    """判断院校层次"""
    # 精确匹配
    if school in SCHOOLS_985 or any(s in school for s in ["清华大学", "北京大学", "复旦大学", "上海交通大学", "浙江大学", "南京大学", "中国科学技术大学", "哈尔滨工业大学"]):
        # 检查是否是985
        for s985 in SCHOOLS_985:
            if s985 in school or school in s985:
                return "985"
    if school in SCHOOLS_985:
        return "985"
    if school in SCHOOLS_211:
        return "211"
    if school in MILITARY_SCHOOLS:
        return "军校"
    if school in HK_MACAO_TAIWAN:
        return "境外港澳"
    if school in RESEARCH_INSTITUTES or any(kw in school for kw in ["中国科学院", "实验室", "研究所", "研究院", "科学院", "医学科学院"]):
        return "科研院所"
    # 其他双非
    return "双非"


def tag_double_first_class(school):
    """判断是否双一流"""
    for s in DOUBLE_FIRST_CLASS:
        if s in school or school in s:
            return "是"
    # 科研院所中的双一流
    if "中国科学院大学" in school:
        return "是"
    if "南方科技大学" in school:
        return "是"
    if "上海科技大学" in school:
        return "是"
    return "否"


def tag_city(school):
    """根据学校名推断城市"""
    # 精确匹配
    if school in CITY_MAP:
        return CITY_MAP[school]
    # 模糊匹配
    for key, city in CITY_MAP.items():
        if key in school or school in key:
            return city
    # 从学校名推断
    city_hints = {
        "北京": "北京", "上海": "上海", "广州": "广州", "深圳": "深圳",
        "杭州": "杭州", "南京": "南京", "武汉": "武汉", "成都": "成都",
        "西安": "西安", "天津": "天津", "重庆": "重庆", "长沙": "长沙",
        "大连": "大连", "青岛": "青岛", "厦门": "厦门", "苏州": "苏州",
        "合肥": "合肥", "济南": "济南", "沈阳": "沈阳", "长春": "长春",
        "哈尔滨": "哈尔滨", "兰州": "兰州", "郑州": "郑州", "昆明": "昆明",
        "香港": "香港", "澳门": "澳门",
    }
    for kw, city in city_hints.items():
        if kw in school:
            return city
    return "其他"


def tag_major_category(college, name):
    """根据学院名和通知名称推断专业类别"""
    text = f"{college} {name}"
    for kw, cat in MAJOR_CATEGORIES.items():
        if kw in text:
            return cat
    return "理工农医"  # 默认


def tag_specific_majors(college, name):
    """根据学院名和通知名称提取具体专业标签（可多个）"""
    text = f"{college} {name}"
    majors = set()
    for pattern, tag in SPECIFIC_MAJOR_PATTERNS:
        if re.search(pattern, text):
            majors.add(tag)
    return sorted(majors) if majors else ["其他"]


def tag_stage(name, ddl):
    """根据通知名称和截止日期推断招生阶段"""
    text = name
    # 优先从名称判断
    for pattern, stage in STAGE_PATTERNS:
        if stage and re.search(pattern, text):
            return stage
    # 从DDL时间推断
    return "夏令营"  # 默认


def parse_ddl(ddl_str):
    """解析截止日期，返回 (date_obj, display_str, status)"""
    if not ddl_str or ddl_str.strip() in ("暂无", "待定", "未定", ""):
        return None, ddl_str or "暂无", "未知"

    ddl_str = ddl_str.strip()

    # 取第一行（多轮次的情况）
    first_line = ddl_str.split('\n')[0].strip()

    # 尝试多种日期格式
    patterns = [
        (r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})日?', '%Y-%m-%d'),  # 2026年5月20日
        (r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})', '%Y-%m-%d'),
        (r'(\d{4})-(\d{1,2})-(\d{1,2})', '%Y-%m-%d'),
        (r'(\d{4})/(\d{1,2})/(\d{1,2})', '%Y-%m-%d'),
    ]

    for pattern, fmt in patterns:
        m = re.search(pattern, first_line)
        if m:
            try:
                y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
                date_obj = datetime(y, mo, d)
                return date_obj, ddl_str, get_ddl_status(date_obj)
            except ValueError:
                pass

    return None, ddl_str, "未知"


def get_ddl_status(date_obj):
    """判断截止日期状态"""
    now = datetime.now()
    if date_obj < now:
        return "已过期"
    if date_obj <= now + timedelta(days=7):
        return "近7天"
    if date_obj <= now + timedelta(days=30):
        return "近30天"
    if date_obj.month == now.month and date_obj.year == now.year:
        return "本月"
    return "后续"


def get_province(city):
    """根据城市获取省份"""
    province_map = {
        "北京": "北京", "天津": "天津", "上海": "上海", "重庆": "重庆",
        "杭州": "浙江", "宁波": "浙江", "温州": "浙江",
        "南京": "江苏", "苏州": "江苏", "无锡": "江苏", "徐州": "江苏",
        "广州": "广东", "深圳": "广东", "珠海": "广东", "东莞": "广东",
        "武汉": "湖北", "宜昌": "湖北",
        "成都": "四川", "雅安": "四川",
        "西安": "陕西", "咸阳": "陕西",
        "长沙": "湖南", "湘潭": "湖南",
        "郑州": "河南", "开封": "河南",
        "济南": "山东", "青岛": "山东", "威海": "山东",
        "大连": "辽宁", "沈阳": "辽宁",
        "长春": "吉林", "延吉": "吉林",
        "哈尔滨": "黑龙江",
        "合肥": "安徽",
        "南昌": "江西",
        "福州": "福建", "厦门": "福建",
        "昆明": "云南",
        "贵阳": "贵州",
        "南宁": "广西",
        "海口": "海南", "三亚": "海南",
        "兰州": "甘肃",
        "太原": "山西",
        "呼和浩特": "内蒙古",
        "乌鲁木齐": "新疆", "石河子": "新疆",
        "银川": "宁夏", "西宁": "青海", "拉萨": "西藏",
        "香港": "香港", "澳门": "澳门",
    }
    return province_map.get(city, city)


# ============================================================
# 4. 主流程
# ============================================================

def main():
    print("=" * 60)
    print("保研星途 - 数据同步脚本")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 读取4个子表
    config = [
        ("data/raw_BB08J2.csv", "经管法"),
        ("data/raw_xnhylx.csv", "理工农医"),
        ("data/raw_v8tlr8.csv", "人文社科艺术"),
        ("data/raw_cir38h.csv", "单校通知"),
    ]

    all_records = []
    category_counts = {}

    for fname, cat in config:
        fpath = BASE_DIR / fname
        if not fpath.exists():
            print(f"  WARNING: {fname} not found, skipping")
            continue
        records = parse_csv_file(fpath, cat)
        category_counts[cat] = len(records)
        print(f"  {fname} ({cat}): {len(records)} 条有效记录")
        all_records.extend(records)

    print(f"\n  总计: {len(all_records)} 条记录")

    # 为每条记录打标签
    print("\n正在打标签...")
    for i, rec in enumerate(all_records):
        school = rec["school"]
        college = rec.get("college", "")
        name = rec["name"]
        ddl = rec["ddl"]

        rec["school_level"] = tag_school_level(school)
        rec["double_first_class"] = tag_double_first_class(school)
        rec["city"] = tag_city(school)
        rec["province"] = get_province(rec["city"])
        rec["major_category"] = rec["category"]  # 使用子表分类
        rec["specific_majors"] = tag_specific_majors(college, name)
        rec["stage"] = tag_stage(name, ddl)

        # 解析截止日期
        date_obj, display_ddl, status = parse_ddl(ddl)
        rec["ddl_date"] = date_obj.strftime("%Y-%m-%d") if date_obj else None
        rec["ddl_display"] = display_ddl
        rec["ddl_status"] = status
        rec["ddl_timestamp"] = date_obj.isoformat() if date_obj else None

    # 生成 JSON
    json_path = BASE_DIR / "baoyan_all.json"
    output = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_count": len(all_records),
            "category_counts": category_counts,
        },
        "records": all_records,
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n  JSON 已生成: {json_path} ({json_path.stat().st_size:,} bytes)")

    # 生成 HTML
    html_path = BASE_DIR / "baoyan_filter.html"
    generate_html(all_records, category_counts, html_path)
    print(f"  HTML 已生成: {html_path} ({html_path.stat().st_size:,} bytes)")

    print("\n同步完成！")
    return all_records, category_counts


# ============================================================
# 5. HTML 生成
# ============================================================

def generate_html(records, category_counts, output_path):
    """生成带筛选面板的 HTML 页面"""

    # 收集所有筛选选项
    all_categories = sorted(set(r["major_category"] for r in records))
    all_levels = sorted(set(r["school_level"] for r in records))
    all_double_first = sorted(set(r["double_first_class"] for r in records))
    all_stages = sorted(set(r["stage"] for r in records))
    all_ddl_statuses = sorted(set(r["ddl_status"] for r in records))
    all_provinces = sorted(set(r["province"] for r in records))
    all_cities = sorted(set(r["city"] for r in records))

    # 收集具体专业
    all_specific_majors = set()
    for r in records:
        for m in r["specific_majors"]:
            all_specific_majors.add(m)
    all_specific_majors = sorted(all_specific_majors)

    # 将记录转为 JSON
    records_json = json.dumps(records, ensure_ascii=False)

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>保研星途 - 推免招生信息筛选系统</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; background: #f5f7fa; color: #333; }}

.header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); color: white; padding: 24px 32px; text-align: center; }}
.header h1 {{ font-size: 28px; font-weight: 700; letter-spacing: 2px; }}
.header .subtitle {{ font-size: 14px; opacity: 0.8; margin-top: 4px; }}
.header .stats {{ display: flex; justify-content: center; gap: 32px; margin-top: 16px; }}
.header .stat-item {{ text-align: center; }}
.header .stat-num {{ font-size: 32px; font-weight: 700; color: #e94560; }}
.header .stat-label {{ font-size: 12px; opacity: 0.7; }}

.container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
.filter-panel {{ background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }}
.filter-panel h3 {{ font-size: 16px; margin-bottom: 12px; color: #1a1a2e; }}
.filter-row {{ display: flex; flex-wrap: wrap; gap: 16px; margin-bottom: 16px; }}
.filter-group {{ flex: 1; min-width: 200px; }}
.filter-group label {{ display: block; font-size: 13px; font-weight: 600; color: #555; margin-bottom: 6px; }}
.filter-group select, .filter-group input {{ width: 100%; padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; }}
.filter-group select:focus, .filter-group input:focus {{ border-color: #0f3460; outline: none; box-shadow: 0 0 0 2px rgba(15,52,96,0.1); }}

.checkbox-group {{ display: flex; flex-wrap: wrap; gap: 6px; }}
.checkbox-group label {{ display: inline-flex; align-items: center; gap: 4px; font-size: 12px; padding: 4px 10px; border: 1px solid #e0e0e0; border-radius: 16px; cursor: pointer; transition: all 0.2s; background: #fafafa; }}
.checkbox-group label:hover {{ border-color: #0f3460; background: #e8f0fe; }}
.checkbox-group label.active {{ background: #0f3460; color: white; border-color: #0f3460; }}
.checkbox-group input[type=checkbox] {{ display: none; }}

.btn-row {{ display: flex; gap: 8px; margin-top: 12px; }}
.btn {{ padding: 8px 20px; border: none; border-radius: 6px; font-size: 13px; cursor: pointer; font-weight: 600; transition: all 0.2s; }}
.btn-primary {{ background: #0f3460; color: white; }}
.btn-primary:hover {{ background: #1a4a7a; }}
.btn-outline {{ background: white; color: #0f3460; border: 1px solid #0f3460; }}
.btn-outline:hover {{ background: #f0f4ff; }}
.btn-export {{ background: #28a745; color: white; }}
.btn-export:hover {{ background: #218838; }}

.sort-row {{ display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }}
.sort-row span {{ font-size: 13px; color: #666; }}
.sort-btn {{ padding: 4px 12px; font-size: 12px; border: 1px solid #ddd; border-radius: 4px; background: white; cursor: pointer; }}
.sort-btn.active {{ background: #0f3460; color: white; border-color: #0f3460; }}

.result-info {{ font-size: 13px; color: #888; margin-bottom: 12px; }}

.table-container {{ background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
thead {{ background: #f8f9fa; }}
th {{ padding: 12px 10px; text-align: left; font-weight: 600; color: #555; border-bottom: 2px solid #e0e0e0; white-space: nowrap; }}
td {{ padding: 10px; border-bottom: 1px solid #f0f0f0; vertical-align: top; }}
tr:hover {{ background: #f8f9ff; }}
.school-col {{ font-weight: 600; color: #1a1a2e; }}
.name-col {{ max-width: 300px; }}
.name-col a {{ color: #0f3460; text-decoration: none; }}
.name-col a:hover {{ text-decoration: underline; }}
.tag {{ display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 500; margin: 1px 2px; }}
.tag-level-985 {{ background: #ffe0e0; color: #c0392b; }}
.tag-level-211 {{ background: #fff3cd; color: #856404; }}
.tag-level-military {{ background: #d4edda; color: #155724; }}
.tag-level-abroad {{ background: #cce5ff; color: #004085; }}
.tag-level-research {{ background: #e8daef; color: #6c3483; }}
.tag-level-other {{ background: #f0f0f0; color: #666; }}
.tag-ddl-expired {{ background: #f8d7da; color: #721c24; }}
.tag-ddl-urgent {{ background: #fff3cd; color: #856404; }}
.tag-ddl-normal {{ background: #d4edda; color: #155724; }}
.tag-stage {{ background: #e8f0fe; color: #1a4a7a; }}
.tag-major {{ background: #f0e6ff; color: #5b2c6f; }}

.footer {{ text-align: center; padding: 24px; color: #aaa; font-size: 12px; }}
.no-results {{ text-align: center; padding: 48px; color: #999; font-size: 16px; }}

/* Mobile responsive */
@media (max-width: 768px) {{
    .header h1 {{ font-size: 22px; }}
    .header .stats {{ gap: 16px; }}
    .filter-row {{ flex-direction: column; }}
    .table-container {{ overflow-x: auto; }}
}}

/* Collapsible section */
.collapsible {{ cursor: pointer; user-select: none; }}
.collapsible::after {{ content: ' ▼'; font-size: 10px; }}
.collapsible.collapsed::after {{ content: ' ▶'; }}
.collapsible-content {{ max-height: 300px; overflow-y: auto; transition: max-height 0.3s; }}
.collapsible-content.hidden {{ max-height: 0; overflow: hidden; }}
</style>
</head>
<body>

<div class="header">
    <h1>⭐ 保研星途</h1>
    <div class="subtitle">推免招生信息智能筛选系统</div>
    <div class="stats">
        <div class="stat-item"><div class="stat-num" id="totalCount">{len(records)}</div><div class="stat-label">总通知数</div></div>
        <div class="stat-item"><div class="stat-num">{category_counts.get("经管法", 0)}</div><div class="stat-label">经管法</div></div>
        <div class="stat-item"><div class="stat-num">{category_counts.get("理工农医", 0)}</div><div class="stat-label">理工农医</div></div>
        <div class="stat-item"><div class="stat-num">{category_counts.get("人文社科艺术", 0)}</div><div class="stat-label">人文社科艺术</div></div>
        <div class="stat-item"><div class="stat-num">{category_counts.get("单校通知", 0)}</div><div class="stat-label">单校通知</div></div>
    </div>
</div>

<div class="container">

<!-- Filter Panel -->
<div class="filter-panel">
    <h3>🔍 筛选条件</h3>

    <div class="filter-row">
        <div class="filter-group">
            <label>专业类别</label>
            <select id="filterCategory">
                <option value="">全部</option>
                {''.join(f'<option value="{c}">{c}</option>' for c in all_categories)}
            </select>
        </div>
        <div class="filter-group">
            <label>院校层次</label>
            <select id="filterLevel">
                <option value="">全部</option>
                {''.join(f'<option value="{l}">{l}</option>' for l in all_levels)}
            </select>
        </div>
        <div class="filter-group">
            <label>双一流</label>
            <select id="filterDoubleFirst">
                <option value="">全部</option>
                {''.join(f'<option value="{d}">{d}</option>' for d in all_double_first)}
            </select>
        </div>
        <div class="filter-group">
            <label>招生阶段</label>
            <select id="filterStage">
                <option value="">全部</option>
                {''.join(f'<option value="{s}">{s}</option>' for s in all_stages)}
            </select>
        </div>
    </div>

    <div class="filter-row">
        <div class="filter-group">
            <label>省份/地区</label>
            <select id="filterProvince">
                <option value="">全部</option>
                {''.join(f'<option value="{p}">{p}</option>' for p in all_provinces)}
            </select>
        </div>
        <div class="filter-group">
            <label>城市</label>
            <select id="filterCity">
                <option value="">全部</option>
                {''.join(f'<option value="{c}">{c}</option>' for c in all_cities)}
            </select>
        </div>
        <div class="filter-group">
            <label>截止日期状态</label>
            <select id="filterDdlStatus">
                <option value="">全部</option>
                {''.join(f'<option value="{s}">{s}</option>' for s in all_ddl_statuses)}
            </select>
        </div>
        <div class="filter-group">
            <label>关键词搜索</label>
            <input type="text" id="filterKeyword" placeholder="输入学校/专业/关键词...">
        </div>
    </div>

    <div class="filter-row">
        <div class="filter-group" style="flex: 3;">
            <label class="collapsible" onclick="toggleCollapsible(this)">具体专业（点击展开/收起）</label>
            <div class="collapsible-content" id="majorCheckboxes">
                <div class="checkbox-group" id="majorGroup">
                    {''.join(f'<label><input type="checkbox" value="{m}" onchange="applyFilters()">{m}</label>' for m in all_specific_majors)}
                </div>
            </div>
        </div>
    </div>

    <div class="btn-row">
        <button class="btn btn-primary" onclick="applyFilters()">🔍 筛选</button>
        <button class="btn btn-outline" onclick="resetFilters()">🔄 重置</button>
        <button class="btn btn-export" onclick="exportCSV()">📥 导出CSV</button>
    </div>
</div>

<!-- Sort -->
<div class="sort-row">
    <span>排序：</span>
    <button class="sort-btn active" onclick="setSort('ddl')" id="sortDdl">按截止日期 ↑</button>
    <button class="sort-btn" onclick="setSort('school')" id="sortSchool">按学校</button>
    <button class="sort-btn" onclick="setSort('date_added')" id="sortDate">按发布时间 ↓</button>
</div>

<div class="result-info" id="resultInfo"></div>

<!-- Table -->
<div class="table-container">
    <table>
        <thead>
            <tr>
                <th>学校</th>
                <th>学院/研究所</th>
                <th>通知名称</th>
                <th>专业类别</th>
                <th>具体专业</th>
                <th>院校层次</th>
                <th>双一流</th>
                <th>地区</th>
                <th>招生阶段</th>
                <th>截止日期</th>
                <th>状态</th>
            </tr>
        </thead>
        <tbody id="tableBody">
        </tbody>
    </table>
</div>

<div class="no-results" id="noResults" style="display:none;">没有匹配的结果，请调整筛选条件。</div>

<div class="footer">
    保研星途 © 2025-2026 | 数据来源：保研星途推免招生信息分享 | 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</div>

</div>

<script>
// 全部数据
const allRecords = {records_json};

let currentSort = "ddl";
let filteredRecords = [...allRecords];

// 初始化
document.addEventListener("DOMContentLoaded", () => {{
    applyFilters();
}});

function toggleCollapsible(el) {{
    el.classList.toggle("collapsed");
    el.nextElementSibling.classList.toggle("hidden");
}}

function getFilterValues() {{
    const category = document.getElementById("filterCategory").value;
    const level = document.getElementById("filterLevel").value;
    const doubleFirst = document.getElementById("filterDoubleFirst").value;
    const stage = document.getElementById("filterStage").value;
    const province = document.getElementById("filterProvince").value;
    const city = document.getElementById("filterCity").value;
    const ddlStatus = document.getElementById("filterDdlStatus").value;
    const keyword = document.getElementById("filterKeyword").value.toLowerCase().trim();

    // 收集选中的具体专业
    const checkedMajors = [];
    document.querySelectorAll("#majorGroup input:checked").forEach(cb => {{
        checkedMajors.push(cb.value);
    }});

    return {{ category, level, doubleFirst, stage, province, city, ddlStatus, keyword, checkedMajors }};
}}

function applyFilters() {{
    const f = getFilterValues();

    // 更新 checkbox 样式
    document.querySelectorAll("#majorGroup label").forEach(lbl => {{
        const cb = lbl.querySelector("input");
        lbl.classList.toggle("active", cb.checked);
    }});

    filteredRecords = allRecords.filter(r => {{
        if (f.category && r.major_category !== f.category) return false;
        if (f.level && r.school_level !== f.level) return false;
        if (f.doubleFirst && r.double_first_class !== f.doubleFirst) return false;
        if (f.stage && r.stage !== f.stage) return false;
        if (f.province && r.province !== f.province) return false;
        if (f.city && r.city !== f.city) return false;
        if (f.ddlStatus && r.ddl_status !== f.ddlStatus) return false;
        if (f.keyword) {{
            const text = (r.school + " " + r.college + " " + r.name + " " + r.specific_majors.join(" ")).toLowerCase();
            if (!text.includes(f.keyword)) return false;
        }}
        if (f.checkedMajors.length > 0) {{
            const hasMajor = f.checkedMajors.some(m => r.specific_majors.includes(m));
            if (!hasMajor) return false;
        }}
        return true;
    }});

    sortRecords();
    renderTable();
}}

function sortRecords() {{
    if (currentSort === "ddl") {{
        filteredRecords.sort((a, b) => {{
            if (!a.ddl_timestamp && !b.ddl_timestamp) return 0;
            if (!a.ddl_timestamp) return 1;
            if (!b.ddl_timestamp) return -1;
            return a.ddl_timestamp.localeCompare(b.ddl_timestamp);
        }});
    }} else if (currentSort === "school") {{
        filteredRecords.sort((a, b) => a.school.localeCompare(b.school, "zh"));
    }} else if (currentSort === "date_added") {{
        filteredRecords.reverse();
    }}
}}

function setSort(type) {{
    currentSort = type;
    document.querySelectorAll(".sort-btn").forEach(b => b.classList.remove("active"));
    document.getElementById("sort" + type.charAt(0).toUpperCase() + type.slice(1)).classList.add("active");
    sortRecords();
    renderTable();
}}

function resetFilters() {{
    document.getElementById("filterCategory").value = "";
    document.getElementById("filterLevel").value = "";
    document.getElementById("filterDoubleFirst").value = "";
    document.getElementById("filterStage").value = "";
    document.getElementById("filterProvince").value = "";
    document.getElementById("filterCity").value = "";
    document.getElementById("filterDdlStatus").value = "";
    document.getElementById("filterKeyword").value = "";
    document.querySelectorAll("#majorGroup input").forEach(cb => cb.checked = false);
    document.querySelectorAll("#majorGroup label").forEach(lbl => lbl.classList.remove("active"));
    applyFilters();
}}

function getLevelTagClass(level) {{
    const map = {{"985": "tag-level-985", "211": "tag-level-211", "军校": "tag-level-military", "境外港澳": "tag-level-abroad", "科研院所": "tag-level-research", "双非": "tag-level-other"}};
    return map[level] || "tag-level-other";
}}

function getDdlTagClass(status) {{
    const map = {{"已过期": "tag-ddl-expired", "近7天": "tag-ddl-urgent", "近30天": "tag-ddl-normal", "本月": "tag-ddl-normal"}};
    return map[status] || "";
}}

function renderTable() {{
    const tbody = document.getElementById("tableBody");
    const noResults = document.getElementById("noResults");
    const resultInfo = document.getElementById("resultInfo");
    const totalCount = document.getElementById("totalCount");

    resultInfo.textContent = `共 ${{filteredRecords.length}} 条结果`;
    totalCount.textContent = allRecords.length;

    if (filteredRecords.length === 0) {{
        tbody.innerHTML = "";
        noResults.style.display = "block";
        return;
    }}

    noResults.style.display = "none";

    tbody.innerHTML = filteredRecords.map(r => {{
        const levelTag = `<span class="tag ${{getLevelTagClass(r.school_level)}}">${{r.school_level}}</span>`;
        const ddlTag = r.ddl_status !== "未知" ? `<span class="tag ${{getDdlTagClass(r.ddl_status)}}">${{r.ddl_status}}</span>` : "";
        const stageTag = `<span class="tag tag-stage">${{r.stage}}</span>`;
        const majorTags = r.specific_majors.slice(0, 3).map(m => `<span class="tag tag-major">${{m}}</span>`).join("");
        const ddlDisplay = r.ddl_display.length > 30 ? r.ddl_display.substring(0, 30) + "..." : r.ddl_display;

        return `<tr>
            <td class="school-col">${{r.school}}</td>
            <td>${{r.college || "-"}}</td>
            <td class="name-col"><a href="${{r.link}}" target="_blank" title="${{r.name}}">${{r.name.length > 50 ? r.name.substring(0, 50) + "..." : r.name}}</a></td>
            <td>${{r.major_category}}</td>
            <td>${{majorTags}}</td>
            <td>${{levelTag}}</td>
            <td>${{r.double_first_class}}</td>
            <td>${{r.city}}</td>
            <td>${{stageTag}}</td>
            <td title="${{r.ddl_display}}">${{ddlDisplay}}</td>
            <td>${{ddlTag}}</td>
        </tr>`;
    }}).join("");
}}

function exportCSV() {{
    const headers = ["学校", "学院", "通知名称", "通知链接", "专业类别", "具体专业", "院校层次", "双一流", "城市", "省份", "招生阶段", "截止日期", "截止状态"];
    const rows = filteredRecords.map(r => [
        r.school, r.college, r.name, r.link, r.major_category,
        r.specific_majors.join(";"), r.school_level, r.double_first_class,
        r.city, r.province, r.stage, r.ddl_display, r.ddl_status
    ]);

    // BOM for Excel UTF-8
    let csvContent = "\\uFEFF" + headers.join(",") + "\\n";
    rows.forEach(row => {{
        csvContent += row.map(cell => `"${{(cell || "").replace(/"/g, '""')}}"`).join(",") + "\\n";
    }});

    const blob = new Blob([csvContent], {{ type: "text/csv;charset=utf-8" }});
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `保研星途_${{new Date().toISOString().slice(0,10)}}.csv`;
    a.click();
    URL.revokeObjectURL(url);
}}
</script>

</body>
</html>'''

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)


if __name__ == "__main__":
    main()
