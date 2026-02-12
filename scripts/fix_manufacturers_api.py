#!/usr/bin/env python3
"""
修复后的完整 /supply/manufacturers API 函数
替换 api/main.py 中的 list_supply_manufacturers 函数
"""

import re

# 读取原文件
with open('/root/autodl-tmp/pj-pharmaKG/api/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 找到函数开始和结束位置
pattern = r'(@app\.get\("/supply/manufacturers".*?\nasync def list_supply_manufacturers\()(.+?)\{[\\s\\S]*?)(.*?)(?=\\n@app\.get\("/supply/manufacturers/geographic-distribution")'
match = re.search(pattern, content)

if not match:
    print("错误：找不到 list_supply_manufacturers 函数！")
    exit(1)

start_pos = match.start()
end_pos = match.end()
old_function = content[start_pos:end_pos]

# 新函数 - 处理所有筛选参数
new_function = '''@app.get("/supply/manufacturers", tags=["Supply Chain"])
async def list_supply_manufacturers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    country: str = Query(None, description="Filter by country"),
    manufacturer_type: str = Query(None, alias="manufacturer_type", description="Filter by manufacturer type (innovator, generic, biotech, cdmo)"),
    quality_score_min: int = Query(None, alias="quality_score_min", ge=0, le=100, description="Minimum quality score"),
    status: str = Query(None, description="Filter by status (active, inactive)")
):
    """获取制造商/公司列表（使用 /supply 路径）"""
    try:
        db = get_db()
        skip = (page - 1) * page_size

        # 构建WHERE条件
        where_conditions = []
        params = {}

        # 类型过滤映射
        if manufacturer_type:
            type_map = {
                "innovator": "Innovator",
                "generic": "Generic",
                "biotech": "Biotech",
                "cdmo": "CDMO"
            }
            where_conditions.append(f"m.type = '{type_map.get(manufacturer_type.lower(), manufacturer_type)}'")

        # 质量分数过滤
        if quality_score_min is not None:
            where_conditions.append(f"m.quality_score >= {quality_score_min}")

        # 状态过滤
        if status:
            where_conditions.append(f"m.status = '{status}'")

        # 国家过滤
        if country:
            where_conditions.append(f"m.country = '{country}'")

        # 搜索过滤
        if search:
            where_conditions.append(f"m.name CONTAINS '{search}'")

        # 组合WHERE条件
        where_clause = " AND ".join(where_conditions) if where_conditions else "true"

        # 先查询 Manufacturer 节点
        count_query = f"MATCH (m:Manufacturer) WHERE {where_clause} RETURN count(m) as count"
        count_result = db.execute_query(count_query, params=params)
        mfg_count = count_result.records[0]["count"] if count_result and count_result.records else 0

        if mfg_count > 0:
            # 有 Manufacturer 节点 - 应用筛选
            list_query = f"""
                MATCH (m:Manufacturer)
                WHERE {where_clause}
                RETURN m.manufacturer_id as id, m.name as name, m.country as location, m.type as type, m.status as status, COALESCE(m.quality_score, 70) as qualityScore
                ORDER BY m.name
                SKIP {skip}
                LIMIT {page_size}
            """
            total = mfg_count
        else:
            # 使用 Company 节点作为制造商 - 应用筛选
            list_query = f"""
                MATCH (c:Company)
                WHERE {where_clause}
                RETURN c.name as id, c.name as name, c.address as location, 'Pharmaceutical' as type, 'active' as status, COALESCE(c.quality_score, 70) as qualityScore
                ORDER BY c.name
                SKIP {skip}
                LIMIT {page_size}
            """
            count_query = f"MATCH (c:Company) WHERE {where_clause} RETURN count(c) as count"
            count_result = db.execute_query(count_query, params=params)
            total = count_result.records[0]["count"] if count_result and count.result.records else 0

        result = db.execute_query(list_query, params=params)
        data = []
        for record in result.records:
            data.append({
                "id": record.get("id"),
                "name": record.get("name"),
                "location": record.get("location"),
                "type": record.get("type"),
                "status": record.get("status"),
                "qualityScore": record.get("qualityScore", 70)
            })

        return {
            "data": data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total > 0 else 0
        }
    except Exception as e:
        logger.error(f"Error listing manufacturers: {e}")
        return {
            "data": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0
        }
'''

# 替换函数
replacement = f"{{old_function}}\n\n"

# 执行替换
new_content = re.sub(pattern, replacement, content)

# 写回文件
with open('/root/autodl-tmp/pj-pharmaKG/api/main.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ 已修复 /supply/manufacturers API 函数")
print("   添加了完整的筛选参数处理:")
print("   - country (国家)")
print("   - manufacturer_type (类型)")
print("   - quality_score_min (质量分数)")
print("   - status (状态)")
print("   - search (搜索)")
print()
print("=" * 50)
print("下一步：重启API服务器并测试筛选功能")
