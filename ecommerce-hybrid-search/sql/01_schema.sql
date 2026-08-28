-- ===========================================================================
-- 电商混合检索 —— 表结构与索引
--
-- 这个文件是文章里几处结论的落地。逐条对应：
--   1. tsvector 必须是 STORED 生成列，不能在查询里现算
--   2. HNSW 建部分索引，把最高频的过滤条件塞进索引本身
--   3. BM25 走 pg_search，不是 ts_rank（ts_rank 没有 IDF）
--   4. L0 抽出来的属性是**普通列**，让它们能被 B-tree 索引
--
-- 由 src/l0_ingest.py 自动执行；也可以单独跑：
--   docker compose exec -T db psql -U postgres -d ehs < sql/01_schema.sql
-- ===========================================================================

CREATE EXTENSION IF NOT EXISTS vector;

-- pg_search 提供真正的 BM25（Tantivy 实现，带 IDF 和文档长度归一化）。
-- 官方 PG 镜像里没有这个扩展，需要 ParadeDB 镜像。
-- 如果这一行失败，src/l0_ingest.py 会自动降级到 tsvector + ts_rank_cd 路径。
CREATE EXTENSION IF NOT EXISTS pg_search;

DROP TABLE IF EXISTS products CASCADE;

CREATE TABLE products (
    id               integer PRIMARY KEY,
    product_name     text    NOT NULL,
    brand            text,
    category         text    NOT NULL,
    description      text    NOT NULL,
    price            numeric(10, 2) NOT NULL,
    stock            integer NOT NULL DEFAULT 0,
    shop_id          text,
    shop_name        text,
    rating           numeric(3, 2),
    sales_30d        integer DEFAULT 0,
    image_url        text,

    -- -----------------------------------------------------------------------
    -- L0 离线抽取出来的结构化属性
    --
    -- 这几列是整套架构里最值钱的东西。「适合扁平足」这个查不到的语义诉求，
    -- 一旦变成 support_type = '稳定支撑'，就退化成一次 B-tree 查找。
    --
    -- 它们**允许为 NULL**：抽取一定有失败的时候（文案没写、写得含糊）。
    -- 正因为会失败，才必须保留词汇召回和向量召回这两路来兜底。
    -- -----------------------------------------------------------------------
    support_type     text,          -- 缓震 | 稳定支撑 | 竞速 | 越野
    weight_grams     integer,       -- 「轻量」这个形容词的真身
    width            text,          -- 标准 | 2E | 4E
    pronation_fit    text,          -- 中性 | 过度内旋 | 内旋不足
    has_carbon_plate boolean,
    cushion_level    integer,       -- 0-10

    -- -----------------------------------------------------------------------
    -- 检索列
    -- -----------------------------------------------------------------------
    -- 词汇检索的输入：标题 + 品牌 + 描述 + 抽出来的属性词拼在一起。
    -- 把属性词也拼进去，是为了让 BM25 也能命中「稳定支撑」这类结构化信息。
    search_text      text NOT NULL DEFAULT '',

    -- jieba 预分词后的文本（空格分隔）。只有降级路径用得上。
    seg_text         text NOT NULL DEFAULT '',

    embedding        vector(512)
);

-- ---------------------------------------------------------------------------
-- 生成列：tsvector 必须落库，不能在查询里现算
--
-- 原方案在 SELECT 和 WHERE 里各写了一次 to_tsvector(description)，
-- 结果是每行实时分词、GIN 索引完全用不上。
--
-- 注意用两参数的 to_tsvector(regconfig, text)：它是 IMMUTABLE，
-- 单参数版本是 STABLE，不能用在生成列和索引里。
-- 这里用 'simple' 配置，因为中文分词已经在 Python 侧用 jieba 做完了——
-- 这样可以绕开 zhparser / pg_jieba 的编译安装。
-- ---------------------------------------------------------------------------
ALTER TABLE products
    ADD COLUMN seg_tsv tsvector
    GENERATED ALWAYS AS (to_tsvector('simple', seg_text)) STORED;

CREATE INDEX products_seg_tsv_gin ON products USING gin (seg_tsv);

-- ---------------------------------------------------------------------------
-- 结构化过滤索引
--
-- 部分索引 WHERE stock > 0：缺货商品永远不该出现在搜索结果里，
-- 把这个条件写进索引，索引本身就变小了，也不用每次都判断。
-- ---------------------------------------------------------------------------
CREATE INDEX products_filter_idx
    ON products (category, price, support_type)
    WHERE stock > 0;

CREATE INDEX products_attrs_idx
    ON products (support_type, weight_grams, width)
    WHERE stock > 0;

-- ---------------------------------------------------------------------------
-- HNSW 向量索引 —— 关键在那个 WHERE
--
-- pgvector 的 HNSW 对带 WHERE 的 kNN 查询是**后过滤**：
-- 先在图里走出 ef_search 个候选，再把不满足条件的行丢掉。
-- 过滤越严，剩下的越少，可能连 LIMIT 都凑不满——而且不报错，只是悄悄少。
--
-- 两个缓解手段：
--   1. 把最高频、选择性最强的过滤条件做成**部分索引**（这里是 stock > 0），
--      索引里就没有不合格的行，后过滤自然不会丢东西。
--   2. 会话里开 hnsw.iterative_scan（pgvector >= 0.8.0），
--      候选不够时继续往图里走。见 src/db.py:apply_session_tuning。
--
-- m / ef_construction 越大，召回越高，建索引越慢、索引越大。
-- ---------------------------------------------------------------------------
CREATE INDEX products_embedding_hnsw
    ON products USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64)
    WHERE stock > 0;

-- ---------------------------------------------------------------------------
-- BM25 索引（pg_search / Tantivy）
--
-- ⚠️ 版本敏感：pg_search 的 WITH 选项和分词器名字在小版本之间改过。
--    如果这条 DDL 报错，先确认当前版本的语法：
--        \dx
--        SELECT extversion FROM pg_extension WHERE extname = 'pg_search';
--    中文分词器候选名（按版本不同）：
--        chinese_compatible   —— Tantivy 内置的 CJK 切分，兼容性最好
--        chinese_lindera      —— Lindera + CC-CEDICT 词典，切分质量更好
--        jieba                —— 较新版本才有
--    src/l0_ingest.py 会依次尝试这几个名字，全失败就降级到 tsvector 路径。
--
-- 和 ts_rank 的区别：BM25 有 IDF（罕见词权重更高）和文档长度归一化。
-- 「扁平足」这种低频词在 BM25 里权重很高，在 ts_rank 里则不然。
-- ---------------------------------------------------------------------------
CREATE INDEX products_bm25_idx ON products
USING bm25 (id, product_name, description, search_text)
WITH (
    key_field = 'id',
    text_fields = '{
        "product_name": {"tokenizer": {"type": "chinese_compatible"}},
        "description":  {"tokenizer": {"type": "chinese_compatible"}},
        "search_text":  {"tokenizer": {"type": "chinese_compatible"}}
    }'
);

ANALYZE products;
