import aioredis
import time
from ..util import get_dependency
from ..errors import ConfigurationError
from .base import AsyncStorage


class AsyncRedisInteractor(object):
    SCRIPT_MOVING_WINDOW = """
            local items = redis.call('lrange', KEYS[1], 0, tonumber(ARGV[2]))
            local expiry = tonumber(ARGV[1])
            local a = 0
            local oldest = nil
            for idx=1,#items do
                if tonumber(items[idx]) >= expiry then
                    a = a + 1
                    if oldest == nil then
                        oldest = tonumber(items[idx])
                    end
                else
                    break
                end
            end
            return {oldest, a}
            """

    SCRIPT_ACQUIRE_MOVING_WINDOW = """
            local entry = redis.call('lindex', KEYS[1], tonumber(ARGV[2]) - 1)
            local timestamp = tonumber(ARGV[1])
            local expiry = tonumber(ARGV[3])
            if entry and tonumber(entry) >= timestamp - expiry then
                return false
            end
            local limit = tonumber(ARGV[2])
            local no_add = tonumber(ARGV[4])
            if 0 == no_add then
                redis.call('lpush', KEYS[1], timestamp)
                redis.call('ltrim', KEYS[1], 0, limit - 1)
                redis.call('expire', KEYS[1], expiry)
            end
            return true
            """

    SCRIPT_CLEAR_KEYS = """
            local keys = redis.call('keys', KEYS[1])
            local res = 0
            for i=1,#keys,5000 do
                res = res + redis.call(
                    'del', unpack(keys, i, math.min(i+4999, #keys))
                )
            end
            return res
            """

    SCRIPT_INCR_EXPIRE = """
            local current
            current = redis.call("incrby",KEYS[1], KEYS[2])
            if tonumber(current) == tonumber(KEYS[2]) then
                redis.call("expire",KEYS[1],ARGV[1])
            end
            return current
        """

    async def incr(self, key, expiry, connection: aioredis.Redis, elastic_expiry=False, incr_by=1):
        """
        increments the counter for a given rate limit key

        :param connection: Redis connection
        :param str key: the key to increment
        :param int expiry: amount in seconds for the key to expire in
        """
        value = await connection.incrby(key, incr_by)

        if elastic_expiry:
            await connection.expire(key, expiry)
        return value

    async def get(self, key, connection: aioredis.Redis):
        """
        :param connection: Redis connection
        :param str key: the key to get the counter value for
        """
        key_val = await connection.get(key)
        return int( key_val or 0)

    async def clear(self, key, connection: aioredis.Redis):
        """
        :param str key: the key to clear rate async_limits for
        :param connection: Redis connection
        """
        await connection.delete(key)


    async def get_expiry(self, key, connection: aioredis.Redis=None):
        """
        :param str key: the key to get the expiry for
        :param connection: Redis connection
        """
        key_ttl = await connection.ttl(key)
        return int(max(key_ttl, 0) + time.time())

    async def check(self, connection: aioredis.Redis):
        """
        :param connection: Redis connection
        check if storage is healthy
        """
        try:
            return await connection.ping()
        except:  # noqa
            return False


class AsyncRedisStorage(AsyncRedisInteractor, AsyncStorage):
    """
    Rate limit storage with redis as backend.

    Depends on the `redis-py` library.
    """

    STORAGE_SCHEME = ["redis", "rediss", "redis+unix"]

    def __init__(self, scripts_sha_mapping, redis_conn: aioredis.Redis):
        """
        :param str uri: uri of the form `redis://[:password]@host:port`,
         `redis://[:password]@host:port/db`,
         `rediss://[:password]@host:port`, `redis+unix:///path/to/sock` etc.
         This uri is passed directly to :func:`redis.from_url` except for the
         case of `redis+unix` where it is replaced with `unix`.
        :param options: all remaining keyword arguments are passed
         directly to the constructor of :class:`redis.Redis`
        :raise ConfigurationError: when the redis library is not available
        """
        self.storage = redis_conn
        # self.script_incr_expire_sha = '0d23cf1ccf81ad1452ccf307e1938d99997a6073'
        self.script_incr_expire_sha = scripts_sha_mapping['script_incr_expire']
        # self.script_clear_keys_sha = '73c9b8f504c33418c74f79a3ac7be749c54004f4'
        self.script_clear_keys_sha = scripts_sha_mapping['script_clear_keys']
        super(AsyncRedisStorage, self).__init__()

    async def lua_incr_expire(self, keys, args):
        return await self.storage.evalsha(self.script_incr_expire_sha, keys=keys, args=args)

    async def lua_clear_keys(self, keys):
        return await self.storage.evalsha(self.script_clear_keys_sha, keys)

    async def incr(self, key, expiry, elastic_expiry=False, incr_by=1):
        """
        increments the counter for a given rate limit key

        :param str key: the key to increment
        :param int expiry: amount in seconds for the key to expire in
        """
        if elastic_expiry:
            return await super(AsyncRedisStorage, self).incr(key, expiry, self.storage, elastic_expiry, incr_by)
        else:
            return await self.lua_incr_expire([key, incr_by], [expiry])

    async def get(self, key):
        """
        :param str key: the key to get the counter value for
        """
        return await super(AsyncRedisStorage, self).get(key, self.storage)

    async def clear(self, key):
        """
        :param str key: the key to clear rate async_limits for
        """
        return await super(AsyncRedisStorage, self).clear(key, self.storage)

    async def get_expiry(self, key):
        """
        :param str key: the key to get the expiry for
        """
        return await super(AsyncRedisStorage, self).get_expiry(key, self.storage)

    async def check(self):
        """
        check if storage is healthy
        """
        return await super(AsyncRedisStorage, self).check(self.storage)

    async def reset(self):
        """
        This function calls a Lua Script to delete keys prefixed with 'LIMITER'
        in block of 5000.

        .. warning::
           This operation was designed to be fast, but was not tested
           on a large production based system. Be careful with its usage as it
           could be slow on very large data sets.

        """

        cleared = await self.lua_clear_keys(['LIMITER*'])
        return cleared
