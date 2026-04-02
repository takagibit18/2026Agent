"""
本地 Qdrant 入门：CRUD、相似向量搜索、带 payload 过滤的查询。

前置：在 embedding_test 目录执行
  docker compose up -d
然后：
  pip install -r requirements.txt
  python qdrant_learn.py
"""

from __future__ import annotations

import sys
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

COLLECTION = "learn_demo"


def vector_search(
    client: QdrantClient,
    collection_name: str,
    query_vector: list[float],
    *,
    limit: int,
    query_filter: rest.Filter | None = None,
    with_payload: bool = True,
):
    """qdrant-client 1.17+ 使用 query_points；旧版仍可能有 search。"""
    if hasattr(client, "search"):
        return client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter=query_filter,
            with_payload=with_payload,
        )
    resp = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=limit,
        query_filter=query_filter,
        with_payload=with_payload,
    )
    return resp.points
VECTOR_SIZE = 8
# Docker Compose 映射 HTTP 6333、gRPC 6334。部分 Windows 环境 REST(httpx) 访问 6333 会 503，gRPC 6334 仍正常。
QDRANT_HOST = "127.0.0.1"
QDRANT_HTTP_PORT = 6333
QDRANT_GRPC_PORT = 6334


def connect_client() -> QdrantClient:
    """先尝试 gRPC，再尝试 REST，避免单一通道在 Win + Docker 下异常。"""
    base_kw = dict(
        host=QDRANT_HOST,
        port=QDRANT_HTTP_PORT,
        grpc_port=QDRANT_GRPC_PORT,
        check_compatibility=False,
    )
    last: Exception | None = None
    for prefer_grpc in (True, False):
        client = QdrantClient(prefer_grpc=prefer_grpc, **base_kw)
        try:
            client.get_collections()
            return client
        except Exception as e:
            last = e
    assert last is not None
    raise last


def ensure_collection(client: QdrantClient) -> None:
    if client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)
    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=rest.VectorParams(size=VECTOR_SIZE, distance=rest.Distance.COSINE),
    )


def demo_crud(client: QdrantClient) -> str:
    """Create / Read / Update / Delete 点（向量 + payload）。"""
    print("\n=== CRUD ===")

    # Create（批量 upsert 即插入）
    pid_str = str(uuid.uuid4())
    points = [
        rest.PointStruct(
            id=1,
            vector=[0.1] * VECTOR_SIZE,
            payload={"kind": "doc", "title": "alpha", "tag": "math"},
        ),
        rest.PointStruct(
            id=pid_str,
            vector=[0.2] * VECTOR_SIZE,
            payload={"kind": "doc", "title": "beta", "tag": "physics"},
        ),
    ]
    client.upsert(collection_name=COLLECTION, points=points)
    print(f"  Create: upsert id=1 与 id={pid_str[:8]}...")

    # Read
    got = client.retrieve(collection_name=COLLECTION, ids=[1], with_payload=True, with_vectors=True)
    print(f"  Read: id=1 payload={got[0].payload}")

    # Update（再次 upsert 同 id 即覆盖向量与 payload）
    client.upsert(
        collection_name=COLLECTION,
        points=[
            rest.PointStruct(
                id=1,
                vector=[0.15] * VECTOR_SIZE,
                payload={"kind": "doc", "title": "alpha-v2", "tag": "math"},
            )
        ],
    )
    got2 = client.retrieve(collection_name=COLLECTION, ids=[1], with_payload=True)
    print(f"  Update: id=1 新 title={got2[0].payload.get('title')}")

    # Delete（按 id）
    client.delete(collection_name=COLLECTION, points_selector=rest.PointIdsList(points=[pid_str]))
    print(f"  Delete: 已删除 id={pid_str[:8]}...")

    return pid_str


def demo_similarity_search(client: QdrantClient) -> None:
    """相似搜索：按查询向量找最近邻（余弦距离）。"""
    print("\n=== 相似搜索（无过滤）===")
    # 与 id=1 的向量 [0.15]*8 最接近的应是 [0.14]*8、[0.5]*8 等，按 cosine 排序
    client.upsert(
        collection_name=COLLECTION,
        points=[
            rest.PointStruct(id=2, vector=[0.14] * VECTOR_SIZE, payload={"title": "near-1"}),
            rest.PointStruct(id=3, vector=[0.9] * VECTOR_SIZE, payload={"title": "far-1"}),
        ],
    )
    query = [0.15] * VECTOR_SIZE
    hits = vector_search(
        client,
        COLLECTION,
        query,
        limit=3,
        with_payload=True,
    )
    for h in hits:
        print(f"  id={h.id} score={h.score:.4f} payload={h.payload}")


def demo_filtered_search(client: QdrantClient) -> None:
    """过滤查询：在相似搜索基础上只保留 payload 满足条件的点。"""
    print("\n=== 相似搜索 + payload 过滤 ===")
    client.upsert(
        collection_name=COLLECTION,
        points=[
            rest.PointStruct(
                id=4,
                vector=[0.16] * VECTOR_SIZE,
                payload={"kind": "note", "topic": "ml", "lang": "zh"},
            ),
            rest.PointStruct(
                id=5,
                vector=[0.16] * VECTOR_SIZE,
                payload={"kind": "note", "topic": "web", "lang": "en"},
            ),
        ],
    )
    query = [0.16] * VECTOR_SIZE
    flt = rest.Filter(
        must=[
            rest.FieldCondition(key="kind", match=rest.MatchValue(value="note")),
            rest.FieldCondition(key="topic", match=rest.MatchValue(value="ml")),
        ]
    )
    hits = vector_search(
        client,
        COLLECTION,
        query,
        limit=5,
        query_filter=flt,
        with_payload=True,
    )
    for h in hits:
        print(f"  id={h.id} score={h.score:.4f} payload={h.payload}")
    if not hits:
        print("  （无命中，检查过滤条件）")


def main() -> None:
    try:
        client = connect_client()
    except Exception as e:
        print(
            f"无法连接 Qdrant ({QDRANT_HOST}，已试 gRPC:{QDRANT_GRPC_PORT} 与 REST:{QDRANT_HTTP_PORT}): {e}",
            file=sys.stderr,
        )
        print("请先在本目录执行: docker compose up -d，并确认 docker ps 中映射了 6333 与 6334。", file=sys.stderr)
        sys.exit(1)

    ensure_collection(client)
    demo_crud(client)
    demo_similarity_search(client)
    demo_filtered_search(client)
    print("\n完成。可在浏览器打开 http://127.0.0.1:6333/dashboard（或 localhost）查看集合与点。")


if __name__ == "__main__":
    main()
