curl -X POST "https://10.110.0.105:8443/api/auth" \
-H  "Accept: application/vnd.ceph.api.v1.0+json" \
-H  "Content-Type: application/json" \
-d '{"username": "admin", "password": "fnslt10!"}' --insecure


curl -X GET "https://10.110.0.105:8443/api/health/minimal" \
-H  "Accept: application/vnd.ceph.api.v1.0+json" \
-H  "Authorization: Bearer "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJjZXBoLWRhc2hib2FyZCIsImp0aSI6IjVkNWU1NTMzLThlZmUtNGU3NS04MDIwLTk4NDMwN2VmOWUzZiIsImV4cCI6MTc3NzQ3MDE2MCwiaWF0IjoxNzc3NDQxMzYwLCJ1c2VybmFtZSI6ImFkbWluIn0.BNaIwgfMrlQYffS8qkgy8M9jsQp27kw5H07JswL5Flc"" \
--insecure