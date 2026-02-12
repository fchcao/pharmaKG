@app.get("/supply/manufacturers", tags=["Supply Chain"])
async def list_supply_manufacturers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    country: str = Query(None, description="Filter by country"),
    manufacturer_type: str = Query(None, alias="manufacturer_type", description="Filter by manufacturer type (innovator, generic, biotech, cdmo)"),
    quality_score_min: int = Query(None, alias="quality_score_min", ge=0, le=100, description="Minimum quality score"),
    status: str = Query(None, description="Filter by status (active, inactive)"),
    search: str = Query(None, description="Search by name")
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
        mfg_count = count_result.records[0]["count"] if count_result.records else 0

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
            # 使用 Company 节点作为制造商 - 应用相同的筛选
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
            total = count_result.records[0]["count"] if count_result.records else 0

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

        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return {
            "data": data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
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
