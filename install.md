# Install app on Windows
1. Install make:
```
winget install ezwinports.make
where make
make --version
```
2. Install Visual C++ Redistributable for Visual Studio 2015
- https://www.microsoft.com/en-us/download/details.aspx?id=48145

3. Install Gitbash
4. Install SSH
5. Install Nginx
- Download and install: https://nginx.org/en/download.html

6. Install Redis
- Download and Install: https://github.com/microsoftarchive/redis/releases
- Run Service on folder install
```
redis-server.exe redis.windows-service.conf
sc qc Redis
```
- Run CLI on folder install
```
redis-cli
127.0.0.1:6379> CONFIG GET requirepass # Lấy password hiện tại
127.0.0.1:6379> CONFIG SET requirepass MyStrongPassword123 # Set password
127.0.0.1:6379> AUTH MyStrongPassword123 # Vì có pass rồi nên cần điền pass trước các thao tác khác
127.0.0.1:6379> CONFIG REWRITE # Lưu vào file cấu hình
127.0.0.1:6379> PING # Test PING, nếu trả về PONG là ok
127.0.0.1:6379> set name Duy # Test 
127.0.0.1:6379> get name # Test

# Hoặc có thể gõ luôn trong 1 câu lệnh
redis-cli -a MyStrongPassword123 CONFIG GET requirepass
redis-cli -a MyStrongPassword123 ping
```
- Restart
```
net stop Redis
net start Redis
# OR
sc stop Redis
sc start Redis
```

- Remove Redis
```
redis-server.exe --service-uninstall
net stop Redis
sc delete Redis
```


7. Install uv and app

8. Install Task Scheduler
- Power shell
```
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass 
& "C:\Projects\MT5PubSubFastApi\scripts\start_fastapi.ps1"
```

```
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass 
& "C:\Projects\MT5PubSubFastApi\scripts\start_nginx.ps1"
```