-- ===========================================================================
-- 混合检索：多路召回 + RRF 融合
--
-- 这是 src/l2_recall.py + src/l3_fusion.py 实际执行的 SQL 的可读版本。
-- 参数由 L1（query 理解）解析出来后绑定。
-- ===========================================================================


-- ###########################################################################
-- 先看反面教材 —— 原方案的写法，以及它的四个问题
-- ###########################################################################
--
--   WITH semantic AS (
--       SELECT id, 1 - (embedding <=> $qv) AS semantic_score
--       FROM products
--       WHERE price <= 500 AND stock > 0 AND category = '运动鞋'
--       ORDER BY embedding <=> $qv
--       LIMIT 200
--   )
--   SELECT id,
--          ts_rank(to_tsvector('chinese', description),
--                  plainto_tsquery('chinese', '扁平足 跑步鞋 轻量')) AS keyword_score,
--          semantic_score,
--          (0.4 * semantic_score + 0.6 * keyword_score) AS final_score
--   FROM semantic
--   WHERE to_tsvector('chinese', description)
--         @@ plainto_tsquery('chinese', '扁平足 跑步鞋 轻量')
--   ORDER BY final_score DESC LIMIT 20;
--
-- ① 'chinese' 这个文本搜索配置在原生 PG 里不存在，第一行就报错。
--
-- ② ts_rank 不是 BM25。它没有 IDF，「扁平足」这种低频词拿不到应有的高权重。
--
-- ③ 量纲不统一，声明的权重是假的：
--       semantic_score ∈ [0,1]，命中时普遍 0.7~0.9
--       ts_rank        典型值 0.01~0.1，无上界
--    代入 0.4×0.85 + 0.6×0.06 = 0.34 + 0.036 —— 语义项贡献了 90%。
--    注释说「0.6 权重给关键词因为精确匹配更重要」，代码做的正好相反。
--
-- ④ 最致命的：外层那个 WHERE ... @@ ... 是**交集**，不是融合。
--    plainto_tsquery 对多个词是 AND 语义，商品描述必须同时包含
--    「扁平足」「跑步鞋」「轻量」三个词才能留下。
--    可真正适合扁平足的鞋，描述里写的是「TPU 稳定片」「抗过度内旋」，
--    根本没有「扁平足」三个字——全被这个 WHERE 砍掉了。
--    而少数把「扁平足」写进标题的商品（鞋垫、超预算的鞋、纯缓震鞋），
--    反而被排到了最前面。
--
-- 混合检索的价值在于**取并集再融合**，原方案取了交集，把价值取反了。
-- ###########################################################################


-- ###########################################################################
-- 正确的写法
-- ###########################################################################

-- 会话级参数。iterative_scan 是 pgvector >= 0.8.0 才有的，
-- 它决定了带过滤的向量召回会不会悄悄丢结果。详见 src/db.py。
SET hnsw.iterative_scan = relaxed_order;
SET hnsw.ef_search = 100;

WITH params AS (
    SELECT
        $1::vector(512) AS qv,           -- 查询向量（只编码语义残余部分）
        $2::text        AS qtext,        -- 扩展后的检索词，OR 语义
        $3::text        AS f_category,   -- 以下是 L1 解析出的硬过滤
        $4::numeric     AS f_price_max,
        $5::text        AS f_support,    -- 「适合扁平足」翻译成的属性
        $6::integer     AS f_weight_max  -- 「轻量」翻译成的数值上界
),

-- ---------------------------------------------------------------------------
-- 第一路：向量召回
--
-- 硬过滤下推到这一路里面，不是「预过滤加速」——HNSW 是后过滤，
-- 加了 WHERE 只会让召回变难，不会变快。下推的真正目的是保证
-- 三路召回看到的是同一个候选空间，融合出来的排名才有意义。
-- ---------------------------------------------------------------------------
semantic AS (
    SELECT p.id,
           row_number() OVER (ORDER BY p.embedding <=> pa.qv) AS rnk
    FROM products p CROSS JOIN params pa
    WHERE p.stock > 0
      AND (pa.f_category  IS NULL OR p.category = pa.f_category)
      AND (pa.f_price_max IS NULL OR p.price   <= pa.f_price_max)
    ORDER BY p.embedding <=> pa.qv
    LIMIT 100
),

-- ---------------------------------------------------------------------------
-- 第二路：词汇召回（BM25，pg_search）
--
-- qtext 是 OR 语义（同义词扩展后的词表），不是 AND。
-- 命中一个词就够进候选集，排名交给 BM25 和后面的融合去做。
--
-- ⚠️ @@@ 和 paradedb.score() 的具体形态随 pg_search 版本变化，
--    以你那个镜像的 \df paradedb.* 为准。
-- ---------------------------------------------------------------------------
lexical AS (
    SELECT p.id,
           row_number() OVER (ORDER BY paradedb.score(p.id) DESC) AS rnk
    FROM products p CROSS JOIN params pa
    WHERE p.search_text @@@ pa.qtext
      AND p.stock > 0
      AND (pa.f_category  IS NULL OR p.category = pa.f_category)
      AND (pa.f_price_max IS NULL OR p.price   <= pa.f_price_max)
    LIMIT 100
),

-- 没有 pg_search 时的降级路径。效果明显更差，因为 ts_rank_cd 没有 IDF。
-- lexical AS (
--     SELECT p.id,
--            row_number() OVER (
--                ORDER BY ts_rank_cd(p.seg_tsv, to_tsquery('simple', pa.qtext)) DESC
--            ) AS rnk
--     FROM products p CROSS JOIN params pa
--     WHERE p.seg_tsv @@ to_tsquery('simple', pa.qtext)
--       AND p.stock > 0
--     LIMIT 100
-- ),

-- ---------------------------------------------------------------------------
-- 第三路：结构化召回
--
-- 这一路专门捞「L1 已经解析出了明确属性约束」的商品。
-- 它是前两路的兜底：一双鞋文案写得极简、embedding 又不突出，
-- 但 support_type 抽对了，就能靠这一路进来。
-- ---------------------------------------------------------------------------
structured AS (
    SELECT p.id,
           row_number() OVER (ORDER BY p.sales_30d DESC, p.rating DESC) AS rnk
    FROM products p CROSS JOIN params pa
    WHERE p.stock > 0
      AND (pa.f_category   IS NULL OR p.category      = pa.f_category)
      AND (pa.f_price_max  IS NULL OR p.price        <= pa.f_price_max)
      AND (pa.f_support    IS NULL OR p.support_type  = pa.f_support)
      AND (pa.f_weight_max IS NULL OR p.weight_grams <= pa.f_weight_max)
    LIMIT 100
),

-- ---------------------------------------------------------------------------
-- 融合：RRF (Reciprocal Rank Fusion)
--
--     score = Σ  w_i / (k + rank_i)        k = 60
--
-- 为什么用 RRF 而不是加权和：
--   RRF 只看**名次**，不看分数。余弦相似度和 BM25 分数量纲天差地别，
--   加权和必须先做归一化，而归一化又依赖当前 query 的分数分布，
--   换个 query 就要重调。RRF 天生无量纲，权重才真正代表你的意图。
--
-- FULL OUTER JOIN 是关键：取**并集**。
--   只被一路召回到的商品，另外两路的 COALESCE 补 0，
--   它拿的分数低但仍然在候选集里，能不能进 Top-20 交给后面的重排决定。
--   原方案用 WHERE 取交集，等于让任何一路都有一票否决权。
-- ---------------------------------------------------------------------------
fused AS (
    SELECT
        id,
        0.35 * COALESCE(1.0 / (60 + s.rnk), 0) +   -- 语义
        0.40 * COALESCE(1.0 / (60 + l.rnk), 0) +   -- 词汇：电商里精确匹配权重最高
        0.25 * COALESCE(1.0 / (60 + t.rnk), 0)     -- 结构化
            AS rrf_score,
        s.rnk AS semantic_rank,
        l.rnk AS lexical_rank,
        t.rnk AS structured_rank
    FROM semantic s
    FULL OUTER JOIN lexical    l USING (id)
    FULL OUTER JOIN structured t USING (id)
)

SELECT p.id, p.product_name, p.brand, p.price, p.stock,
       p.support_type, p.weight_grams, p.image_url,
       f.rrf_score, f.semantic_rank, f.lexical_rank, f.structured_rank
FROM fused f
JOIN products p ON p.id = f.id
ORDER BY f.rrf_score DESC
LIMIT 50;   -- 这 50 条送去 L4 做 cross-encoder 重排，再由 L5 决定最终 20 条
