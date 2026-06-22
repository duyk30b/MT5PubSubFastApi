from typing import Any, Awaitable, Set, cast

from redis.asyncio.client import Pipeline

from app.redis.redis_connection import RedisConnection


class RedisBase:
    def __init__(self) -> None:
        pass

    @property
    def _redis(self):
        return RedisConnection.get_client()

    # ── String operations ────────────────────────────────────────────────

    async def _get(self, key: str) -> str | None:
        """Return the string value of a key, or None if it does not exist."""
        return await cast(Awaitable[str | None], self._redis.get(key))

    async def _set(
        self,
        key: str,
        value: str | int | float,
        ttl: int | None = None,
    ):
        """Set the string value of a key with optional TTL (seconds)."""
        if ttl is not None:
            await cast(Awaitable[Any], self._redis.setex(key, ttl, value))
        else:
            await cast(Awaitable[Any], self._redis.set(key, value, ex=ttl))

    async def _incr(self, key: str, amount: int = 1) -> int:
        """Increment the integer value of a key by amount."""
        return await self._redis.incrby(key, amount)

    async def _decr(self, key: str, amount: int = 1) -> int:
        """Decrement the integer value of a key by amount."""
        return await self._redis.decrby(key, amount)

    # ── Key management ──────────────────────────────────────────────────

    async def _delete(self, *keys: str) -> int:
        """Delete one or more keys. Returns the number of keys removed."""
        return await self._redis.delete(*keys)

    async def _exists(self, *keys: str) -> int:
        """Return the number of keys that exist from the provided list."""
        return await self._redis.exists(*keys)

    async def _expire(self, key: str, ttl: int) -> bool:
        """Set TTL (seconds) on an existing key. Returns True if key exists."""
        return await self._redis.expire(key, ttl)

    async def _persist(self, key: str) -> bool:
        """Remove the TTL from a key, making it persistent."""
        return await self._redis.persist(key)

    async def _ttl(self, key: str) -> int:
        """Return remaining TTL in seconds. -1 = no expiry, -2 = not found."""
        return await self._redis.ttl(key)

    async def _keys(self, pattern: str = "*") -> list[str]:
        """Return all key names matching pattern. Avoid in production on large datasets."""
        """Example: keys("user:*") returns all keys starting with "user:"."""
        result = await cast(Awaitable[list[Any]], self._redis.keys(pattern))  # type: ignore[misc]
        return list(result)

    # ── Hash operations ─────────────────────────────────────────────────

    async def _hash_get(self, name: str, field: str) -> str | None:
        """Return the value of field in the hash stored at name."""
        return await cast(Awaitable[str | None], self._redis.hget(name, field))

    async def _hash_set(self, name: str, mapping: dict[str, Any]) -> int:
        """Set multiple fields in hash at name. Returns number of new fields added."""
        """Example: hash_set("user:1", {"name": "Alice", "age": "30"}) sets two fields in hash "user:1"."""
        return await cast(Awaitable[int], self._redis.hset(name, mapping=mapping))  # type: ignore[misc]

    async def _hash_delete(self, name: str, *fields: str) -> int:
        """Delete fields from the hash at name."""
        return await self._redis.hdel(name, *fields)

    async def _hash_get_all(self, name: str) -> dict[str, str]:
        """Return all field-value pairs in the hash at name."""
        result = await cast(Awaitable[dict[Any, Any]], self._redis.hgetall(name))  # type: ignore[misc]
        return {str(k): str(v) for k, v in result.items()}

    async def _hash_exists(self, name: str, field: str) -> bool:
        """Return True if field exists in the hash at name."""
        return await self._redis.hexists(name, field)

    async def _hash_keys(self, name: str) -> list[str]:
        """Return all field names in the hash at name."""
        result = await cast(Awaitable[list[Any]], self._redis.hkeys(name))  # type: ignore[misc]
        return [str(k) for k in result]

    async def _hash_values(self, name: str) -> list[str]:
        """Return all values in the hash at name."""
        result = await cast(Awaitable[list[Any]], self._redis.hvals(name))  # type: ignore[misc]
        return [str(v) for v in result]

    # ── Set operations ──────────────────────────────────────────────────

    async def _set_add(self, name: str, *values: str) -> int:
        """Add values to the set at name. Returns number of elements added."""
        """Example: set_add("tags", "python", "redis") adds "python" and "redis" to set "tags"."""
        if not values:
            return 0
        return await self._redis.sadd(name, *values)

    async def _set_remove(self, name: str, *values: str) -> int:
        """Remove values from the set at name."""
        """Example: set_remove("tags", "python") removes "python" from set "tags"."""
        return await self._redis.srem(name, *values)

    async def _set_get_member_list(self, name: str) -> Set[str]:
        """Return all members of the set at name."""
        """Example: set_get_member_list("tags") returns all members of set "tags". Returns a set of strings."""
        result = await cast(Awaitable[Set[Any]], self._redis.smembers(name))  # type: ignore[misc]
        return {str(m) for m in result}

    async def _set_remove_all(self, name: str) -> int:
        """Remove all members from the set at name."""
        """Example: set_remove_all("tags") removes all members from set "tags"."""
        members = await self._set_get_member_list(name)
        if members:
            return await self._set_remove(name, *members)
        return 0

    async def _set_is_member(self, name: str, value: str) -> bool:
        """Return True if value is a member of the set at name."""
        """Example: set_is_member("tags", "python") returns True if "python" is in set "tags"."""
        result = await cast(Awaitable[Any], self._redis.sismember(name, value))
        return bool(result)

    # ── List operations ─────────────────────────────────────────────────

    async def _list_push_head(self, name: str, *values: str) -> int:
        """Push values to the head of the list at name."""
        """Example: list_push("mylist", "value1", "value2") pushes "value1" and "value2" to the head of list "mylist"."""
        return await self._redis.lpush(name, *values)

    async def _list_push_tail(self, name: str, *values: str) -> int:
        """Push values to the tail of the list at name."""
        """Example: list_push_tail("mylist", "value1", "value2") pushes "value1" and "value2" to the tail of list "mylist"."""
        return await self._redis.rpush(name, *values)

    async def _list_range(self, name: str, start: int, end: int) -> list[str]:
        """Return a slice of the list at name from start to end (inclusive)."""
        """Example: list_range("mylist", 0, -1) returns all elements of list "mylist"."""
        result = await cast(Awaitable[list[Any]], self._redis.lrange(name, start, end))  # type: ignore[misc]
        return [str(item) for item in result]

    async def _list_length(self, name: str) -> int:
        """Return the length of the list at name."""
        """Example: list_length("mylist") returns the number of elements in list "mylist"."""
        return await self._redis.llen(name)

    async def _list_lpop(self, name: str) -> str | None:
        """Remove and return the first element of the list at name."""
        """Example: list_lpop("mylist") removes and returns the head element of list "mylist". Returns None if list is empty."""
        result = await cast(Awaitable[Any], self._redis.lpop(name))  # type: ignore[misc]
        return str(result) if result is not None else None

    async def _list_rpop(self, name: str) -> str | None:
        """Remove and return the last element of the list at name."""
        """Example: list_rpop("mylist") removes and returns the tail element of list "mylist". Returns None if list is empty."""
        result = await cast(Awaitable[Any], self._redis.rpop(name))  # type: ignore[misc]
        return str(result) if result is not None else None

    async def _list_trim(self, name: str, start: int, end: int) -> None:
        """Trim the list at name to only include elements from start to end (inclusive)."""
        """Example: list_trim("mylist", 0, 9) keeps only the first 10 elements of list "mylist"."""
        await cast(Awaitable[Any], self._redis.ltrim(name, start, end))

    # ── Pub/Sub helpers ─────────────────────────────────────────────────

    async def _publish(self, channel: str, message: str) -> int:
        """Publish message to channel. Returns number of subscribers that received it."""
        return await cast(Awaitable[int], self._redis.publish(channel, message))  # type: ignore[misc]

    # ── Pipeline ────────────────────────────────────────────────────────

    def _pipeline(self, transaction: bool = True) -> Pipeline:
        """Return a pipeline context for batching commands."""
        return self._redis.pipeline(transaction=transaction)
        # Example:
        # async with self._redis.pipeline() as pipe:
        #     pipe.set("key1", "value1")
        #     pipe.set("key2", "value2")
        #     await pipe.execute()
