import os
import logging
import requests
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class SearchService:
    """
    搜索服务类，负责处理各类搜索功能
    """
    
    def __init__(self):
        # 从环境变量初始化配置
        self.search_config = {
            "gugudata": {
                "enabled": os.environ.get("GUGUDATA_ENABLED", "False").lower() == "true",
                "api_key": os.environ.get("GUGUDATA_API_KEY", ""),
                "endpoint": "https://api.gugudata.com/metadata/ceemajor",
                "timeout": 30
            },
            "custom_search": {
                "enabled": True,
                "search_engine": "mock"
            },
            "serpapi": {
                "enabled": os.environ.get("SERPAPI_ENABLED", "False").lower() == "true",
                "api_key": os.environ.get("SERPAPI_API_KEY", ""),
                "timeout": 30
            }
        }
    
    def optimize_search_query(self, query: str) -> str:
        """
        优化搜索查询，提取核心关键词
        
        Args:
            query: 原始查询字符串
            
        Returns:
            优化后的查询字符串
        """
        # 去除常见的停用词和冗余表达
        stopwords = ["请问", "请问一下", "想请问", "想知道", "我想知道", "能否", "能否告诉我", 
                    "可以告诉我", "告诉我", "关于", "有关", "是", "的", "吗", "呢", "？", "。", "，"]
        
        optimized = query
        for word in stopwords:
            optimized = optimized.replace(word, "")
        
        # 确保查询中包含学校名称（增强相关性）
        if "江西工业工程职业技术学院" not in optimized and "江西工业职院" not in optimized:
            optimized = f"江西工业工程职业技术学院 {optimized}"
        
        return optimized.strip()
    
    def generate_precise_search_results(self, optimized_query: str, original_query: str, is_realtime: bool = False) -> List[Dict]:
        """
        根据查询类型生成更精准的模拟搜索结果
        
        Args:
            optimized_query: 优化后的查询
            original_query: 原始查询
            is_realtime: 是否需要实时数据
            
        Returns:
            精准的搜索结果列表
        """
        # 根据查询内容的关键词分类，生成更相关的结果
        query_lower = original_query.lower()
        current_year = 2025
        recent_years = [str(current_year - i) for i in range(4)]  # 获取最近4年
        
        # 专业相关查询
        if any(keyword in query_lower for keyword in ["专业", "系", "学院", "课程", "学科"]):
            if is_realtime:
                # 实时数据：最新的专业设置和调整信息
                return [
                    {"content": f"{recent_years[0]}年江西工业工程职业技术学院专业设置: 根据{recent_years[0]}年最新数据，学校设有机械工程学院、电气工程学院、建筑工程学院、信息工程学院、经济管理学院等多个二级学院，开设50多个专业，包括近年来新增的人工智能技术应用、大数据技术等专业。", 
                     "metadata": {"source": "搜索API-最新专业信息", "type": "实时数据"}},
                    {"content": f"{recent_years[0]}-{recent_years[1]}学年专业介绍: 针对'{optimized_query}'，学校在{recent_years[0]}-{recent_years[1]}学年对该专业进行了课程体系优化，更加注重实践能力培养，增加了企业真实项目实训环节。具体课程设置可登录学校官网查看最新的培养方案。", 
                     "metadata": {"source": "搜索API-最新专业详情", "type": "实时数据"}},
                    {"content": f"最新专业发展动态: 近年来学校积极推进专业建设，多个专业被评为省级特色专业。{recent_years[1]}-{recent_years[0]}学年，学校新增了多个校企合作订单班，为学生提供更好的就业保障。学校定期更新专业建设动态，建议关注学校教务处官网。", 
                     "metadata": {"source": "搜索API-专业动态", "type": "近年数据"}}
                ]
            else:
                # 非实时数据：近几年的专业情况参考
                return [
                    {"content": f"江西工业工程职业技术学院专业设置(近年情况): 学校设有机械工程学院、电气工程学院、建筑工程学院、信息工程学院、经济管理学院等多个二级学院，{recent_years[2]}-{recent_years[0]}年间开设了50多个专业，涵盖工、管、文、经、艺等多个学科门类。每个专业都有完善的课程体系和实训条件。", 
                     "metadata": {"source": "搜索API-专业信息", "type": "近年数据"}},
                    {"content": f"专业介绍详情(近年参考): 针对'{optimized_query}'，近三年来学校该专业主要培养具备相关领域基础理论和专业技能的高素质技术技能人才。核心课程包括专业基础课、专业核心课和专业实践课，学生毕业后可在相关行业就业或继续深造。具体课程设置可能会根据教学需要进行调整。", 
                     "metadata": {"source": "搜索API-专业详情", "type": "近年数据"}},
                    {"content": f"专业发展前景(近年统计): {recent_years[3]}-{recent_years[0]}年间，该专业就业前景广阔，毕业生主要面向相关行业企业，从事技术应用、管理服务等工作。就业率保持在较高水平，深受用人单位欢迎。学校还与多家企业建立了校企合作关系，为学生提供实习和就业机会。", 
                     "metadata": {"source": "搜索API-就业信息", "type": "近年数据"}}
                ]
        
        # 招生相关查询
        elif any(keyword in query_lower for keyword in ["招生", "录取", "分数", "分数线", "报考"]):
            # 可以根据需要继续实现其他类型的查询处理
            pass
        
        # 默认搜索结果
        if is_realtime:
            return [
                {"content": f"江西工业工程职业技术学院最新信息: 根据{recent_years[0]}年最新数据，学校位于江西省萍乡市，是一所公办全日制普通高等职业院校。学校占地约800亩，建筑面积30余万平方米，教职工近700人，在校生1万余人。近年来，学校积极推进教育教学改革，不断提升人才培养质量。", 
                 "metadata": {"source": "搜索API-最新校情", "type": "实时数据"}},
                {"content": f"最新校园动态: {recent_years[0]}年上半年，学校举办了多场重要活动，包括校园招聘会、技能竞赛、学术讲座等。学校还与多家企业签署了战略合作协议，进一步深化产教融合。学校官网定期发布最新校园新闻和通知，建议关注。", 
                 "metadata": {"source": "搜索API-校园动态", "type": "实时数据"}},
                {"content": f"学校最新政策: 近期，学校出台了多项新政策，涵盖学生管理、教学改革、科研奖励等多个方面。这些政策旨在进一步规范学校管理，提升教学质量，促进学校内涵发展。具体政策内容可登录学校官网查阅相关文件。", 
                 "metadata": {"source": "搜索API-政策信息", "type": "实时数据"}}
            ]
        else:
            return [
                {"content": f"江西工业工程职业技术学院概况(近年情况): 学校位于江西省萍乡市，是一所公办全日制普通高等职业院校。{recent_years[2]}-{recent_years[0]}年间，学校不断完善办学条件，提升办学水平。学校占地约800亩，建筑面积30余万平方米，教学科研仪器设备总值近2亿元。", 
                 "metadata": {"source": "搜索API-校情信息", "type": "近年数据"}},
                {"content": f"学校发展成就(近年统计): 近三年来，学校在教学科研、人才培养、社会服务等方面取得了显著成就。多个专业被评为省级高水平专业群，教师主持或参与多项省级以上科研项目，学生在各类技能竞赛中屡获佳绩，就业率保持在较高水平。", 
                 "metadata": {"source": "搜索API-成就信息", "type": "近年数据"}},
                {"content": f"校园环境与设施(近年情况): 学校环境优美，设施完善，拥有现代化的教学楼、实验楼、图书馆、体育馆等教学设施，以及学生公寓、食堂等生活设施。近年来，学校不断加大校园建设投入，为学生提供良好的学习和生活环境。", 
                 "metadata": {"source": "搜索API-校园信息", "type": "近年数据"}},
                {"content": f"师资力量(近年情况): 学校拥有一支结构合理、素质优良的师资队伍。近三年来，学校引进和培养了一批具有博士、硕士学位的高层次人才，现有教授、副教授等高级职称教师100余人，'双师型'教师占比达到70%以上。", 
                 "metadata": {"source": "搜索API-师资信息", "type": "近年数据"}}
            ]

# 创建搜索服务实例
_search_service = SearchService()

# 模块级别导出，用于方便导入和使用
SEARCH_CONFIG = _search_service.search_config

def should_use_realtime_search(query: str) -> bool:
    """
    判断是否应该使用实时搜索
    
    Args:
        query: 用户查询字符串
        
    Returns:
        是否使用实时搜索
    """
    # 包含这些关键词时优先使用实时搜索
    realtime_keywords = ["最新", "现在", "当前", "今天", "明天", "今年", "最近", 
                        "正在", "即将", "报名", "截止", "活动", "通知"]
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in realtime_keywords)

def search_api_integration(query: str, is_realtime: bool = False) -> list:
    """
    搜索API集成函数
    
    Args:
        query: 用户查询字符串
        is_realtime: 是否使用实时搜索
        
    Returns:
        搜索结果列表
    """
    # 这里使用模拟实现，返回generate_precise_search_results的结果
    optimized_query = optimize_search_query(query)
    return generate_precise_search_results(optimized_query, query, is_realtime)

def optimize_search_query(query: str) -> str:
    """
    优化搜索查询的模块级函数
    """
    return _search_service.optimize_search_query(query)

def generate_precise_search_results(optimized_query: str, original_query: str, is_realtime: bool = False) -> list:
    """
    生成精准搜索结果的模块级函数
    """
    return _search_service.generate_precise_search_results(optimized_query, original_query, is_realtime)